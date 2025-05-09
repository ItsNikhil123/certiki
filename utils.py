import os
import logging
import tempfile
import openpyxl
from docxtpl import DocxTemplate
from datetime import datetime
from certificate_generator import format_date

logger = logging.getLogger(__name__)

def allowed_file(filename, allowed_extensions):
    """
    Check if the file has an allowed extension.
    
    Args:
        filename (str): The filename to check
        allowed_extensions (set): Set of allowed file extensions
        
    Returns:
        bool: True if the file is allowed, False otherwise
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def get_excel_headers(excel_path):
    """
    Get the headers (column names) from an Excel file.
    
    Args:
        excel_path (str): Path to the Excel file
        
    Returns:
        list: List of header names
    """
    try:
        # Load the workbook
        workbook = openpyxl.load_workbook(excel_path, read_only=True, data_only=True)
        sheet = workbook.active
        
        # Get headers from first row
        headers = []
        for cell in sheet[1]:
            if cell.value is not None:
                headers.append(cell.value)
        
        return headers
    except Exception as e:
        logger.error(f"Error reading Excel headers: {str(e)}")
        raise

def get_template_variables(template_path):
    """
    Extract template variables from a Word template.
    
    Args:
        template_path (str): Path to the Word template
        
    Returns:
        list: List of variable names in the template
    """
    try:
        doc = DocxTemplate(template_path)
        variables = doc.get_undeclared_template_variables()
        return list(variables)
    except Exception as e:
        logger.error(f"Error extracting template variables: {str(e)}")
        raise

def generate_preview(excel_path, template_path, mappings, row_index, output_folder):
    """
    Generate a preview certificate using data from a specific row.
    
    Args:
        excel_path (str): Path to the Excel file
        template_path (str): Path to the Word template
        mappings (dict): Mappings between template variables and Excel headers
        row_index (int): Row index to use for preview (0-based, excluding header row)
        output_folder (str): Folder to save the preview
        
    Returns:
        str: Path to the generated preview file
    """
    try:
        logger.debug(f"Generating preview using row index: {row_index}")
        
        # Load Excel data
        workbook = openpyxl.load_workbook(excel_path, data_only=True)
        sheet = workbook.active
        
        # Get headers from first row
        headers = [cell.value for cell in sheet[1] if cell.value is not None]
        
        # Calculate actual Excel row (add 2: +1 for header, +1 for 0-indexing)
        excel_row_index = row_index + 2
        row_values = list(sheet[excel_row_index])
        
        # Prepare data dictionary from the selected row
        data = {}
        for i, cell in enumerate(row_values):
            if i < len(headers) and headers[i]:
                header_name = headers[i]
                cell_value = cell.value
                
                # Handle cell value based on type
                if cell_value is None:
                    data[header_name] = ""
                elif isinstance(cell_value, datetime):
                    data[header_name] = cell_value.strftime("%B %d, %Y")
                else:
                    data[header_name] = str(cell_value)
        
        # Create preview filename
        preview_filename = f"preview_{os.path.basename(template_path)}"
        preview_path = os.path.join(output_folder, preview_filename)
        
        # Load template
        doc = DocxTemplate(template_path)
        template_vars = doc.get_undeclared_template_variables()
        
        # Create context data from mappings
        context = {}
        for template_var, excel_header in mappings.items():
            if excel_header in data:
                context[template_var] = data[excel_header]
                logger.debug(f"Preview mapped {template_var} = {data[excel_header]}")
            else:
                context[template_var] = ""
                logger.debug(f"Preview empty mapping for {template_var}")
        
        # Force add current date in multiple common formats
        current_date = datetime.now().strftime("%B %d, %Y")
        context['date'] = current_date
        context['current_date'] = current_date
        context['completion_date'] = current_date
        context['issue_date'] = current_date
        
        # Add any template variable with "date" in the name
        for var in template_vars:
            if 'date' in var.lower() and var not in context:
                context[var] = current_date
                logger.debug(f"Preview added date field {var} = {current_date}")
                
        logger.debug(f"Preview final context: {context}")
                
        # Render and save the document
        doc.render(context)
        doc.save(preview_path)
        
        return preview_path
    except Exception as e:
        logger.error(f"Error generating preview: {str(e)}")
        raise
