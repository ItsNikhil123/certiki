import os
import logging
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from werkzeug.utils import secure_filename
import tempfile
import shutil
from certificate_generator import process_excel, generate_certificates
from utils import allowed_file, generate_preview, get_excel_headers

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Create Flask application
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")

# Configure upload folder
UPLOAD_FOLDER = os.path.join(tempfile.gettempdir(), 'certificate_uploads')
PREVIEW_FOLDER = os.path.join(tempfile.gettempdir(), 'certificate_previews')
ALLOWED_EXTENSIONS_EXCEL = {'xlsx', 'xls'}
ALLOWED_EXTENSIONS_DOCX = {'docx'}

# Create necessary directories if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PREVIEW_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PREVIEW_FOLDER'] = PREVIEW_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit file uploads to 16MB

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload_excel', methods=['POST'])
def upload_excel():
    if 'excel_file' not in request.files:
        flash('No file part', 'error')
        return redirect(request.url)
    
    file = request.files['excel_file']
    
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(request.url)
    
    if file and allowed_file(file.filename, ALLOWED_EXTENSIONS_EXCEL):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Get Excel headers
        try:
            headers = get_excel_headers(filepath)
            return jsonify({
                'success': True,
                'filename': filename,
                'headers': headers
            })
        except Exception as e:
            logger.error(f"Error processing Excel file: {str(e)}")
            return jsonify({
                'success': False,
                'error': f"Error processing Excel file: {str(e)}"
            }), 400
    else:
        return jsonify({
            'success': False,
            'error': 'Invalid file format. Please upload an Excel file (.xlsx, .xls)'
        }), 400

@app.route('/upload_template', methods=['POST'])
def upload_template():
    if 'template_file' not in request.files:
        flash('No file part', 'error')
        return redirect(request.url)
    
    file = request.files['template_file']
    
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(request.url)
    
    if file and allowed_file(file.filename, ALLOWED_EXTENSIONS_DOCX):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        return jsonify({
            'success': True,
            'filename': filename
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Invalid file format. Please upload a Word document (.docx)'
        }), 400

@app.route('/preview', methods=['POST'])
def preview():
    # Get the field mappings and filenames from the request
    data = request.get_json()
    
    excel_filename = data.get('excel_filename')
    template_filename = data.get('template_filename')
    mappings = data.get('mappings', {})
    row_index = int(data.get('row_index', 0))  # Row to use for preview (default to first row)
    
    excel_path = os.path.join(app.config['UPLOAD_FOLDER'], excel_filename)
    template_path = os.path.join(app.config['UPLOAD_FOLDER'], template_filename)
    
    if not os.path.exists(excel_path) or not os.path.exists(template_path):
        return jsonify({
            'success': False,
            'error': 'Files not found. Please upload again.'
        }), 404
    
    try:
        # Generate preview for specified row
        preview_path = generate_preview(excel_path, template_path, mappings, row_index, app.config['PREVIEW_FOLDER'])
        
        # Return the preview file path or ID
        return jsonify({
            'success': True,
            'preview_file': os.path.basename(preview_path)
        })
    except Exception as e:
        logger.error(f"Error generating preview: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"Error generating preview: {str(e)}"
        }), 500

@app.route('/get_preview/<filename>')
def get_preview(filename):
    filepath = os.path.join(app.config['PREVIEW_FOLDER'], filename)
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    else:
        flash('Preview file not found', 'error')
        return redirect(url_for('index'))

@app.route('/generate', methods=['POST'])
def generate():
    # Get the field mappings and filenames from the request
    data = request.get_json()
    
    excel_filename = data.get('excel_filename')
    template_filename = data.get('template_filename')
    mappings = data.get('mappings', {})
    
    excel_path = os.path.join(app.config['UPLOAD_FOLDER'], excel_filename)
    template_path = os.path.join(app.config['UPLOAD_FOLDER'], template_filename)
    
    if not os.path.exists(excel_path) or not os.path.exists(template_path):
        return jsonify({
            'success': False,
            'error': 'Files not found. Please upload again.'
        }), 404
    
    try:
        # Process Excel file
        data = process_excel(excel_path)
        
        # Generate certificates
        output_dir = os.path.join(tempfile.gettempdir(), 'generated_certificates')
        os.makedirs(output_dir, exist_ok=True)
        
        # Clean previous certificates
        for file in os.listdir(output_dir):
            os.remove(os.path.join(output_dir, file))
        
        # Generate certificates
        output_zip = generate_certificates(data, template_path, mappings, output_dir)
        
        # Return the zip file
        return jsonify({
            'success': True,
            'zip_file': os.path.basename(output_zip)
        })
    except Exception as e:
        logger.error(f"Error generating certificates: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"Error generating certificates: {str(e)}"
        }), 500

@app.route('/download/<filename>')
def download_file(filename):
    output_dir = os.path.join(tempfile.gettempdir(), 'generated_certificates')
    filepath = os.path.join(output_dir, filename)
    
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    else:
        flash('File not found', 'error')
        return redirect(url_for('index'))

@app.errorhandler(413)
def too_large(e):
    flash('File is too large. Maximum size is 16MB', 'error')
    return redirect(url_for('index'))

@app.errorhandler(500)
def server_error(e):
    flash('An unexpected error occurred. Please try again.', 'error')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)