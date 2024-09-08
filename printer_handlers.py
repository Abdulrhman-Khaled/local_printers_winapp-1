import subprocess
import win32print
from flask import Flask, request, jsonify, render_template, current_app
import pdfkit
import tempfile
import requests
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def get_printers():
    """Return a list of available printer names."""
    return [printer[2] for printer in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL)]


def print_pdf_silent(pdf_path, printer_name, sumatra_pdf_path):
    """Print the PDF silently using SumatraPDF."""
    try:
        # Use SumatraPDF's -print-to command to print the PDF to the specified printer
        command = (
            f'"{sumatra_pdf_path}" -print-to "{printer_name}" '
            f'-print-settings "noscale" "{pdf_path}"'
        )
        logging.info(f"Executing command: {command}")

        # Run the command using subprocess
        subprocess.run(command, shell=True, check=True)
        logging.info(f"Sent {pdf_path} to printer {printer_name} successfully.")
        
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to print {pdf_path} on {printer_name}: {e}")
    except Exception as ex:
        logging.error(f"An error occurred while printing the PDF: {ex}")


def print_html(invoices_data, config_data):
    """Render HTML template to PDF and print to specified printers."""
    with current_app.app_context():
        path_wkhtmltopdf = config_data["WKHTMLTOPDF"]  # Path to wkhtmltopdf executable
        sumatra_pdf_path = config_data.get("SUMATRA_PDF_PATH", r"C:\Program Files\SumatraPDF\SumatraPDF.exe")  # Path to SumatraPDF
        letterhead_image = config_data.get("LETTERHEAD_IMAGE")  # Get the letterhead image path
        frappe_socket_url = config_data.get("FRAPPE_SOCKET_URL")

        # Get current order number from external API
        order_no = get_order_no(config_data)
        print(order_no)
        config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
        printer_names = []
        
        for invoice in invoices_data:
            logging.info(f"Processing invoice: {invoice.get('ksa_einv_qr')}")

            # Render the invoice HTML to PDF
            rendered_html = render_template(
                'print_ui.html',
                frappe_socket_url=frappe_socket_url,
                letterhead_image=letterhead_image,
                order_no=order_no.get("order_no"),
                **invoice
            )
            pdf_path = tempfile.mktemp(suffix='.pdf')
            
            try:
                options = {
                    'no-outline': None,
                    'encoding': 'utf-8',
                    'enable-local-file-access': None  # Enable local file access for images
                }
                pdfkit.from_string(rendered_html, pdf_path, configuration=config, options=options)
                logging.info(f"Generated PDF at: {pdf_path}")
                
                printer = invoice.get("printer")
                if printer:
                    print_pdf_silent(pdf_path, printer, sumatra_pdf_path)
                    printer_names.append(printer)
                else:
                    logging.warning("Printer name not specified, skipping print.")
                
            except Exception as e:
                logging.error(f"Failed to generate or print PDF: {e}")
            finally:
                pass
                # Optionally delete the PDF after printing
                # if os.path.exists(pdf_path):
                #     os.remove(pdf_path)
                #     logging.info(f"Deleted temporary PDF file: {pdf_path}")
        
        return printer_names


def get_order_no(config_data):
    """Get the current order number from an external API."""
    headers = {
        "Authorization": f"token {config_data['API_KEY']}:{config_data['API_SECRET']}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            f"{config_data['FRAPPE_SOCKET_URL']}/api/method/local_printers.utils.get_order_no",
            headers=headers
        )

        if response.status_code == 200:
            response_data = response.json()
            order_no = response_data.get('message')
            if order_no:
                logging.info(f"Order number received: {order_no}")
                return order_no
            else:
                logging.error("Order number missing in the response.")
                return None
        else:
            logging.error(f"Failed to get order number. Status code: {response.status_code}, Response: {response.text}")
            return None

    except requests.RequestException as e:
        logging.error(f"Error while fetching order number: {e}")
        return None
