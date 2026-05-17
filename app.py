"""Flask application for Transaction Categorizer."""

import os
import uuid
from decimal import Decimal

from flask import Flask, render_template, request, jsonify, session, send_file
from werkzeug.utils import secure_filename

from config import Config, BUDGET_CATEGORIES, normalize_budget_category
from src.parser import MHTMLParser
from src.categorizer import CategorizationEngine
from src.exporter import BudgetExporter
from src.models import Transaction

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.dirname(app.config['CONFIG_PATH']), exist_ok=True)

# Initialize components
parser = MHTMLParser()
engine = CategorizationEngine(app.config['CONFIG_PATH'])
exporter = BudgetExporter()

# Server-side transaction store (avoids 4KB cookie limit)
transaction_store = {}


def get_stored_transactions():
    """Retrieve transactions from server-side store."""
    upload_id = session.get('upload_id')
    if not upload_id:
        return None
    transactions = transaction_store.get(upload_id)
    if transactions is not None:
        normalize_stored_categories(transactions)
    return transactions


def set_stored_transactions(data):
    """Store transactions in server-side store."""
    upload_id = session.get('upload_id')
    if upload_id:
        normalize_stored_categories(data)
        transaction_store[upload_id] = data


def normalize_stored_categories(transactions):
    """Normalize older stored category labels to the current template labels."""
    for tx in transactions:
        tx['budget_category'] = normalize_budget_category(tx.get('budget_category'))


def dict_amount(tx_data):
    """Get a transaction dictionary amount as Decimal."""
    return Decimal(str(tx_data.get('amount', '0')))


def transaction_objects(transactions_data, include_income=True):
    """Convert stored transaction dictionaries to Transaction objects."""
    transactions = []
    for tx_data in transactions_data:
        tx = Transaction.from_dict(tx_data)
        if include_income or not tx.is_income:
            transactions.append(tx)
    return transactions


def get_flat_categories():
    """Get flat list of all budget categories."""
    categories = []
    for main_cat, subcats in BUDGET_CATEGORIES.items():
        for subcat in subcats:
            categories.append(f"{main_cat}/{subcat}")
    categories.append("Uncategorized/Needs Review")
    return categories


@app.route('/')
def index():
    """Redirect to upload page."""
    return render_template('upload.html')


@app.route('/upload')
def upload_page():
    """Upload page."""
    return render_template('upload.html')


@app.route('/api/upload', methods=['POST'])
def api_upload():
    """API endpoint for file upload."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    filename = secure_filename(file.filename or '')
    if filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Validate file extension
    if not filename.lower().endswith('.mhtml'):
        return jsonify({'error': 'Only .mhtml files are supported'}), 400
    
    try:
        # Read and parse file
        content = file.read()
        transactions = parser.extract_transactions(content)
        
        # Auto-categorize
        engine.auto_categorize_all(transactions)
        
        # Store server-side (avoids 4KB cookie limit)
        upload_id = str(uuid.uuid4())
        session['upload_id'] = upload_id
        transaction_store[upload_id] = [tx.to_dict() for tx in transactions]
        
        # Calculate stats
        categorized = sum(1 for tx in transactions if tx.budget_category)
        uncategorized = len(transactions) - categorized
        
        return jsonify({
            'success': True,
            'transaction_count': len(transactions),
            'categorized_count': categorized,
            'uncategorized_count': uncategorized,
            'redirect': '/review'
        })
    
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/review')
def review_page():
    """Review and categorize transactions."""
    transactions = get_stored_transactions()
    if transactions is None:
        return render_template('review.html', income=[], expenses=[], excluded=[], categories=get_flat_categories())

    income = [tx for tx in transactions if dict_amount(tx) > 0]
    expenses = [tx for tx in transactions if dict_amount(tx) <= 0 and not tx.get('excluded')]
    excluded = [tx for tx in transactions if dict_amount(tx) <= 0 and tx.get('excluded')]

    return render_template('review.html', income=income, expenses=expenses, excluded=excluded, categories=get_flat_categories())


@app.route('/api/transactions')
def api_get_transactions():
    """API endpoint to get transactions."""
    transactions = get_stored_transactions()
    if transactions is None:
        return jsonify({'transactions': []})
    
    # Filter by type (income/expense)
    tx_type = request.args.get('type', 'all')
    if tx_type == 'income':
        transactions = [tx for tx in transactions if dict_amount(tx) > 0]
    elif tx_type == 'expense':
        transactions = [tx for tx in transactions if dict_amount(tx) <= 0]
    
    # Filter by category if specified
    filter_cat = request.args.get('category', 'all')
    if filter_cat == 'uncategorized':
        transactions = [tx for tx in transactions if not tx.get('budget_category')]
    elif filter_cat != 'all':
        transactions = [tx for tx in transactions if tx.get('budget_category') == filter_cat]
    
    # Search filter
    search = request.args.get('search', '').lower()
    if search:
        transactions = [tx for tx in transactions if search in tx.get('description', '').lower()]
    
    return jsonify({'transactions': transactions})


@app.route('/api/transactions/categorize', methods=['POST'])
def api_categorize():
    """API endpoint to categorize transactions."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    transaction_ids = data.get('transaction_ids', [])
    category = data.get('category')
    
    if not transaction_ids or not category:
        return jsonify({'error': 'Missing transaction_ids or category'}), 400
    
    transactions = get_stored_transactions()
    if transactions is None:
        return jsonify({'error': 'No transactions in session'}), 400
    
    updated_count = 0
    
    for tx in transactions:
        if tx['id'] in transaction_ids:
            tx['budget_category'] = category
            tx['confidence'] = 1.0  # Manual categorization = 100% confidence
            updated_count += 1
            
            # Learn from manual categorization
            tx_obj = Transaction.from_dict(tx)
            engine.learn_from_manual(tx_obj, category)
    
    set_stored_transactions(transactions)
    
    return jsonify({
        'success': True,
        'updated_count': updated_count
    })


@app.route('/api/transactions/exclude', methods=['POST'])
def api_exclude():
    """API endpoint to exclude/unexclude transactions."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    transaction_ids = data.get('transaction_ids', [])
    excluded = data.get('excluded', True)

    if not transaction_ids:
        return jsonify({'error': 'Missing transaction_ids'}), 400

    transactions = get_stored_transactions()
    if transactions is None:
        return jsonify({'error': 'No transactions in session'}), 400

    updated_count = 0
    for tx in transactions:
        if tx['id'] in transaction_ids:
            tx['excluded'] = excluded
            updated_count += 1

    set_stored_transactions(transactions)

    return jsonify({
        'success': True,
        'updated_count': updated_count,
        'excluded': excluded
    })


@app.route('/api/transactions/auto-categorize', methods=['POST'])
def api_auto_categorize():
    """API endpoint to run auto-categorization on all transactions."""
    transactions = get_stored_transactions()
    if transactions is None:
        return jsonify({'error': 'No transactions in session'}), 400
    
    # Convert dicts back to Transaction objects
    tx_objects = transaction_objects(transactions)

    # Run auto-categorization
    engine.auto_categorize_all(tx_objects)
    
    # Convert back to dicts and store
    set_stored_transactions([tx.to_dict() for tx in tx_objects])
    
    categorized = sum(1 for tx in tx_objects if tx.budget_category)
    
    return jsonify({
        'success': True,
        'categorized_count': categorized,
        'total_count': len(tx_objects)
    })


@app.route('/export')
def export_page():
    """Export page."""
    transactions_data = get_stored_transactions()
    if transactions_data is None:
        return render_template('export.html', summary={}, tsv='')
    
    # Convert dicts to Transaction objects and filter out income
    transactions = transaction_objects(transactions_data, include_income=False)

    summary = exporter.get_summary(transactions)
    tsv = exporter.export_to_tsv(transactions)
    
    return render_template('export.html', summary=summary, tsv=tsv)


@app.route('/api/export/tsv')
def api_export_tsv():
    """API endpoint to download TSV file."""
    transactions_data = get_stored_transactions()
    if transactions_data is None:
        return jsonify({'error': 'No transactions in session'}), 400
    
    # Convert dicts to Transaction objects, filter out income
    transactions = transaction_objects(transactions_data, include_income=False)

    tsv = exporter.export_to_tsv(transactions)
    
    # Create response with file download
    from io import BytesIO
    output = BytesIO()
    output.write(tsv.encode('utf-8'))
    output.seek(0)
    
    return send_file(
        output,
        mimetype='text/tab-separated-values',
        as_attachment=True,
        download_name='budget_export.tsv'
    )


@app.route('/api/export/summary')
def api_export_summary():
    """API endpoint to get export summary."""
    transactions_data = get_stored_transactions()
    if transactions_data is None:
        return jsonify({'summary': {}})
    
    # Convert dicts to Transaction objects, filter out income
    transactions = transaction_objects(transactions_data, include_income=False)

    summary = exporter.get_summary(transactions)
    
    # Convert Decimal to string for JSON serialization
    summary_json = {
        'total_transactions': summary['total_transactions'],
        'categorized_count': summary['categorized_count'],
        'uncategorized_count': summary['uncategorized_count'],
        'total_income': str(summary['total_income']),
        'total_expenses': str(summary['total_expenses']),
        'net': str(summary['net'])
    }
    
    return jsonify({'summary': summary_json})


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5500, debug=True)
