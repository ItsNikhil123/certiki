import os
import zipfile
import logging
from docxtpl import DocxTemplate
import openpyxl
from datetime import datetime
from dateutil import parser

logger = logging.getLogger(__name__)

def format_date(value):
    """
    Formats a date value into a standardized string format.
    
    Args:
        value: The date value (datetime object, string, or None)
        
    Returns:
        str: A formatted date string in the format 'Month DD, YYYY'
    """
    try:
        # Handle None or empty string
        if value is None or (isinstance(value, str) and not value.strip()):
            return datetime.now().strftime("%B %d, %Y")
        
        # Handle datetime objects directly
        if isinstance(value, datetime):
            return value.strftime("%B %d, %Y")
            
        # Try to parse string as date
        if isinstance(value, str):
            try:
                parsed_date = parser.parse(value)
                return parsed_date.strftime("%B %d, %Y")
            except Exception as e:
                logger.debug(f"Could not parse '{value}' as date: {str(e)}")
                
        # Default to current date if all else fails
        return datetime.now().strftime("%B %d, %Y")
    except Exception as e:
        logger.error(f"Error in date formatting: {str(e)}")
        return datetime.now().strftime("%B %d, %Y")

def process_excel(excel_path):
    """
    Process Excel file and extract data for certificate generation.
    
    Args:
        excel_path (str): Path to the Excel file
        
    Returns:
        list: List of dictionaries containing the data from each row
    """
    try:
        # Load the workbook
        workbook = openpyxl.load_workbook(excel_path, data_only=True)
        sheet = workbook.active
        
        # Get headers (first row)
        headers = [cell.value for cell in sheet[1] if cell.value is not None]
        logger.debug(f"Found Excel headers: {headers}")
        
        # Extract data
        data = []
        for row in sheet.iter_rows(min_row=2, values_only=True):
            # Skip completely empty rows
            if not any(row):
                continue
                
            row_data = {}
            for i, value in enumerate(row):
                if i < len(headers) and headers[i]:
                    header_name = headers[i]
                    
                    # Handle None values
                    if value is None:
                        row_data[header_name] = ""
                    # Format date values
                    elif isinstance(value, datetime):
                        row_data[header_name] = value.strftime("%B %d, %Y")
                    # Handle everything else as strings
                    else:
                        row_data[header_name] = str(value)
            
            # Add non-empty rows to the data list
            if row_data:
                data.append(row_data)
        
        logger.debug(f"Processed {len(data)} rows from Excel file")
        return data
    except Exception as e:
        logger.error(f"Error processing Excel file: {str(e)}")
        raise

def generate_certificate(template_path, data, mappings, output_path):
    """
    Generate a single certificate using the provided template and data.
    
    Args:
        template_path (str): Path to the Word template file
        data (dict): Data to fill in the template
        mappings (dict): Field mappings between Excel headers and template variables
        output_path (str): Path where the generated certificate will be saved
        
    Returns:
        str: Path to the generated certificate
    """
    try:
        logger.debug(f"Generating certificate to: {output_path}")
        
        # Load the template
        doc = DocxTemplate(template_path)
        
        # Get template variables
        template_vars = doc.get_undeclared_template_variables()
        logger.debug(f"Template variables: {template_vars}")
        
        # Map data according to field mappings
        context = {}
        for template_var, excel_header in mappings.items():
            if excel_header in data:
                context[template_var] = data[excel_header]
                logger.debug(f"Mapped {template_var} = {data[excel_header]}")
            else:
                context[template_var] = ""
                logger.debug(f"Empty mapping for {template_var}")
        
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
                logger.debug(f"Added date field {var} = {current_date}")
        
        logger.debug(f"Final context: {context}")
        
        # Render the document with the context data
        doc.render(context)
        
        # Save the document
        doc.save(output_path)
        
        return output_path
    except Exception as e:
        logger.error(f"Error generating certificate: {str(e)}")
        raise

def generate_certificates(data, template_path, mappings, output_dir):
    """
    Generate certificates for all entries in the data list.
    
    Args:
        data (list): List of dictionaries containing data for each certificate
        template_path (str): Path to the Word template file
        mappings (dict): Field mappings between Excel headers and template variables
        output_dir (str): Directory where certificates will be saved
        
    Returns:
        str: Path to the generated ZIP file containing all certificates
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        generated_files = []
        
        # Generate a certificate for each data entry
        for i, entry in enumerate(data):
            # Create a filename based on name field or index
            if 'Name' in entry and entry['Name']:
                # Sanitize name for filename
                safe_name = "".join(c if c.isalnum() else "_" for c in entry['Name'])
                filename = f"certificate_{safe_name}.docx"
            else:
                filename = f"certificate_{i+1}.docx"
            
            # Generate and save the certificate
            output_path = os.path.join(output_dir, filename)
            generate_certificate(template_path, entry, mappings, output_path)
            generated_files.append(output_path)
        
        # Package all certificates into a single ZIP file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"certificates_{timestamp}.zip"
        zip_path = os.path.join(output_dir, zip_filename)
        
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for file in generated_files:
                zipf.write(file, arcname=os.path.basename(file))
        
        return zip_path
    except Exception as e:
        logger.error(f"Error generating certificates: {str(e)}")
        raise
