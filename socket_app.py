import json
from flask import Flask, request, jsonify, render_template, current_app
from threading import Thread
import socketio
import requests
import win32print
from printer_handlers import print_html
import sys
import os
import glob
import time

app = Flask(__name__)

# Create a Socket.IO client instance
sio = socketio.Client()

def load_config_from_file(config_path):
    """Load configuration data from a JSON file."""
    try:
        with open(config_path, 'r') as file:
            config_data = json.load(file)
        print("Configuration loaded successfully from file.")
        return config_data
    except FileNotFoundError:
        print(f"Configuration file {config_path} not found.")
        sys.exit("Exiting due to missing configuration file.")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from config file: {e}")
        sys.exit("Exiting due to invalid configuration format.")

def get_printers():
    """Return a list of available printer names."""
    return [printer[2] for printer in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL)]

def send_printers_data(printers, config_data):
    """Send the list of printers to the Frappe server."""
    headers = {
        "Authorization": f"token {config_data['API_KEY']}:{config_data['API_SECRET']}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        f"{config_data['FRAPPE_SOCKET_URL']}/api/method/local_printers.utils.save_printers_data",
        json={"printers": printers}, headers=headers
    )

    if response.status_code == 200:
        print("Printers data successfully sent to ERP.")
    else:
        print(f"Failed to send printers data. Status code: {response.status_code}, Response: {response.text}")




@sio.event
def connect():
    """Handle successful connection to the server."""
    print("Connected to the server")
    printers = get_printers()
    print("Available printers:", printers)
    send_printers_data(printers, config_data)

@sio.event
def connect_error(data):
    """Handle connection errors."""
    print(f"Connection failed: {data}")

@sio.event
def disconnect():
    """Handle disconnection from the server."""
    print("Disconnected from the server")

@sio.on('sales_invoice_submitted')
def handle_sales_invoice_submitted(data):
    """Handle the 'sales_invoice_submitted' event and print the invoice."""
    with app.app_context():
        invoice_name = data[0].get('name')
        print(f"Received Sales Invoice: <<{invoice_name}>> Submitted event. Number of invoices: {len(data)}")
        print_html(data, config_data)

def fetch_session_cookies(config_data):
    """Log in to the server and fetch session cookies."""
    try:
        response = requests.post(config_data["LOGIN_URL"], data=config_data["AUTH_DATA"])
        response.raise_for_status()
        cookies = response.cookies
        cookie_header = "; ".join([f"{key}={value}" for key, value in cookies.items()])
        print("Login successful, cookies fetched:", cookie_header)
        return cookie_header
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch session cookies: {str(e)}")
        return None

def run_socketio_client(config_data):
    """Connect the Socket.IO client to the server using session cookies."""
    cookie_header = fetch_session_cookies(config_data)
    if not cookie_header:
        print("Cannot connect without valid session cookies.")
        return

    headers = {'Cookie': cookie_header}
    try:
        # Validate the domain via an API call
        response = requests.get(
            "https://localprinters.psc-s.com/api/method/validate_local_printers.validate_users.validate_domain",
            json={"config_data": config_data}
        )
        response_data = response.json()

        if response_data.get("message", {}).get("status") == "valid":
            print(f" '{config_data['FRAPPE_SOCKET_URL']}' is valid. Proceeding with the connection...")
            try:
                sio.connect(config_data["FRAPPE_SOCKET_URL"], headers=headers, transports=['websocket'])
                sio.wait()  # Keep the connection open
            except Exception as e:
                print(f"Failed to connect or error during connection: {str(e)}")
        else:
            print(f"Validation failed: {response_data}")
    
    except requests.exceptions.RequestException as e:
        print(f"Error during domain validation: {str(e)}")

def disconnect_socketio_client():
    """Disconnect the Socket.IO client."""
    try:
        sio.disconnect()
        print("Client has been disconnected.")
    except Exception as e:
        print(f"Error during disconnection: {str(e)}")




def validate_domain(config_data):
    """Validate domain periodically and exit script forcefully if invalid."""
    try:
        while True:
            response = requests.get(
                "https://localprinters.psc-s.com/api/method/validate_local_printers.validate_users.validate_domain",
                json={"config_data": config_data}
            )
            response_data = response.json()

            if response_data.get("message", {}).get("status") == "valid":
                print(f"'{config_data['FRAPPE_SOCKET_URL']}' is valid. Proceeding with the connection...")
            else:
                print(response_data)
                print(f"'{config_data['FRAPPE_SOCKET_URL']}' is invalid. Exiting the script.")
                os._exit(1)  # Forcefully exit the script

            # Sleep for 36 seconds before checking again (you can adjust this to your needs)
            time.sleep(3600)

    except Exception as e:
        print(f"An error occurred while validating the domain: {e}")
        os._exit(1)  # Forcefully exit on error

if __name__ == "__main__":
    # Load configuration from file
    config_path = "config.json"
    config_data = load_config_from_file(config_path)

    # Start the Socket.IO client in a separate thread
    Thread(target=run_socketio_client, args=(config_data,)).start()
    # Start another thread to validate the domain
    Thread(target=validate_domain, args=(config_data,)).start()
