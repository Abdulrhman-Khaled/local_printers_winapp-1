import subprocess
import win32print
from flask import Flask, request, jsonify, render_template, current_app
import pdfkit
import tempfile


def get_printers():
    """Return a list of available printer names."""
    return [printer[2] for printer in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL)]

def print_pdf_silent(pdf_path, printer_name):
    """Print the PDF silently using the Windows print command."""
    try:
        # Use the Windows 'print' command to send the PDF to the printer
        # The `/d:` option specifies the target printer
        command = f'print /d:"{printer_name}" "{pdf_path}"'
        print(command)
        # Run the command using subprocess
        subprocess.run(command, shell=True, check=True)
        print(f"Sent {pdf_path} to printer {printer_name} successfully.")
        
    except subprocess.CalledProcessError as e:
        print(f"Failed to print {pdf_path} on {printer_name}: {e}")
    except Exception as ex:
        print(f"An error occurred while printing the PDF: {ex}")
def print_html(invoices_data, config_data):
    """Render HTML template to PDF and print to specified printers."""
    with current_app.app_context():
        path_wkhtmltopdf = config_data["WKHTMLTOPDF"]  # Path to wkhtmltopdf executable
        letterhead_image = config_data.get("LETTERHEAD_IMAGE")  # Get the letterhead image path
        frappe_socket_url = config_data.get("FRAPPE_SOCKET_URL")
        config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
        printer_names = []
        for invoice in invoices_data:
            print(invoice.get("ksa_einv_qr"))
            # Pass the letterhead image path to the template
            rendered_html = render_template('print_ui.html', frappe_socket_url=frappe_socket_url, letterhead_image=letterhead_image, **invoice)
            pdf_path = tempfile.mktemp(suffix='.pdf')
            
            try:
                options = {
                    'no-outline': None,
                    'encoding': 'utf-8',
                    'enable-local-file-access': None  # Enable local file access for the image
                }
                pdfkit.from_string(rendered_html, pdf_path, configuration=config, options=options)
                print(f"Generated PDF at: {pdf_path}")
                
                printer = invoice.get("printer")
                if printer:
                    print_pdf_silent(pdf_path, printer)
                    printer_names.append(printer)
                else:
                    print("Printer name not specified, skipping print.")
                
            except Exception as e:
                print(f"Failed to generate or print PDF: {e}")
            finally:
                pass
                # Uncomment the following lines if you want to delete the PDF after printing
                # if os.path.exists(pdf_path):
                #     os.remove(pdf_path)
                #     print(f"Deleted temporary PDF file: {pdf_path}")
        
        return printer_names
