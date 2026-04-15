"""Flask application for Transaction Categorizer."""

import os
import uuid
from datetime import datetime
from decimal import Decimal

from flask import Flask, render_template, request, jsonify, session, send_file
from werkzeug.utils import secure_filename

from config import Config, BUDGET_CATEGORIES
from src.parser import MHTMLParser
from src.categorizer import CategorizationEngine
from src.exporter import BudgetExporter

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
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Validate file extension
    if not file.filename.endswith('.mhtml'):
        return jsonify({'error': 'Only .mhtml files are supported'}), 400
    
    try:
        # Read and parse file
        content = file.read()
        transactions = parser.extract_transactions(content)
        
        # Auto-categorize
        engine.auto_categorize_all(transactions)
        
        # Store in session
        session['transactions'] = [tx.to_dict() for tx in transactions]
        session['upload_id'] = str(uuid.uuid4())
        
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
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/review')
def review_page():
    """Review and categorize transactions."""
    if 'transactions' not in session:
        return render_template('review.html', transactions=[], categories=get_flat_categories())
    
    transactions = session['transactions']
    return render_template('review.html', transactions=transactions, categories=get_flat_categories())


@app.route('/api/transactions')
def api_get_transactions():
    """API endpoint to get transactions."""
    if 'transactions' not in session:
        return jsonify({'transactions': []})
    
    transactions = session['transactions']
    
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
    
    if 'transactions' not in session:
        return jsonify({'error': 'No transactions in session'}), 400
    
    transactions = session['transactions']
    updated_count = 0
    
    for tx in transactions:
        if tx['id'] in transaction_ids:
            tx['budget_category'] = category
            tx['confidence'] = 1.0  # Manual categorization = 100% confidence
            updated_count += 1
            
            # Learn from manual categorization
            # Create a temporary Transaction object for learning
            from src.models import Transaction as TxModel
            from decimal import Decimal
            tx_obj = TxModel(
                id=tx['id'],
                date=datetime.fromisoformat(tx['date']) if tx['date'] else datetime.now(),
                counter_party=tx['counter_party'],
                description=tx['description'],
                amount=Decimal(tx['amount']),
                bank_category=tx['bank_category'],
                budget_category=category,
                confidence=1.0
            )
            engine.learn_from_manual(tx_obj, category)
    
    session['transactions'] = transactions
    
    return jsonify({
        'success': True,
        'updated_count': updated_count
    })


@app.route('/api/transactions/auto-categorize', methods=['POST'])
def api_auto_categorize():
    """API endpoint to run auto-categorization on all transactions."""
    if 'transactions' not in session:
        return jsonify({'error': 'No transactions in session'}), 400
    
    transactions = session['transactions']
    
    # Convert dicts back to Transaction objects
    from src.models import Transaction as TxModel
    tx_objects = []
    for tx_dict in transactions:
        tx = TxModel(
            id=tx_dict['id'],
            date=datetime.fromisoformat(tx_dict['date']) if tx_dict['date'] else datetime.now(),
            counter_party=tx_dict['counter_party'],
            description=tx_dict['description'],
            amount=Decimal(tx_dict['amount']),
            bank_category=tx_dict['bank_category'],
            budget_category=tx_dict.get('budget_category'),
            confidence=tx_dict.get('confidence', 0.0)
        )
        tx_objects.append(tx)
    
    # Run auto-categorization
    engine.auto_categorize_all(tx_objects)
    
    # Convert back to dicts and store
    session['transactions'] = [tx.to_dict() for tx in tx_objects]
    
    categorized = sum(1 for tx in tx_objects if tx.budget_category)
    
    return jsonify({
        'success': True,
        'categorized_count': categorized,
        'total_count': len(tx_objects)
    })


@app.route('/export')
def export_page():
    """Export page."""
    if 'transactions' not in session:
        return render_template('export.html', summary={}, tsv='')
    
    transactions_data = session['transactions']
    
    # Convert dicts to Transaction objects
    from src.models import Transaction as TxModel
    transactions = []
    for tx_dict in transactions_data:
        tx = TxModel(
            id=tx_dict['id'],
            date=datetime.fromisoformat(tx_dict['date']) if tx_dict['date'] else datetime.now(),
            counter_party=tx_dict['counter_party'],
            description=tx_dict['description'],
            amount=Decimal(tx_dict['amount']),
            bank_category=tx_dict['bank_category'],
            budget_category=tx_dict.get('budget_category'),
            confidence=tx_dict.get('confidence', 0.0)
        )
        transactions.append(tx)
    
    summary = exporter.get_summary(transactions)
    tsv = exporter.export_to_tsv(transactions)
    
    return render_template('export.html', summary=summary, tsv=tsv)


@app.route('/api/export/tsv')
def api_export_tsv():
    """API endpoint to download TSV file."""
    if 'transactions' not in session:
        return jsonify({'error': 'No transactions in session'}), 400
    
    transactions_data = session['transactions']
    
    # Convert dicts to Transaction objects
    from src.models import Transaction as TxModel
    transactions = []
    for tx_dict in transactions_data:
        tx = TxModel(
            id=tx_dict['id'],
            date=datetime.fromisoformat(tx_dict['date']) if tx_dict['date'] else datetime.now(),
            counter_party=tx_dict['counter_party'],
            description=tx_dict['description'],
            amount=Decimal(tx_dict['amount']),
            bank_category=tx_dict['bank_category'],
            budget_category=tx_dict.get('budget_category'),
            confidence=tx_dict.get('confidence', 0.0)
        )
        transactions.append(tx)
    
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
    if 'transactions' not in session:
        return jsonify({'summary': {}})
    
    transactions_data = session['transactions']
    
    # Convert dicts to Transaction objects
    from src.models import Transaction as TxModel
    transactions = []
    for tx_dict in transactions_data:
        tx = TxModel(
            id=tx_dict['id'],
            date=datetime.fromisoformat(tx_dict['date']) if tx_dict['date'] else datetime.now(),
            counter_party=tx_dict['counter_party'],
            description=tx_dict['description'],
            amount=Decimal(tx_dict['amount']),
            bank_category=tx_dict['bank_category'],
            budget_category=tx_dict.get('budget_category'),
            confidence=tx_dict.get('confidence', 0.0)
        )
        transactions.append(tx)
    
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
    app.run(host='127.0.0.1', port=5000, debug=True)
