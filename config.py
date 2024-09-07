# config.py
CORS_ORIGINS = [
    "https://wafra-pos.soultech.ae",
    # Add other allowed origins here
]

FRAPPE_SOCKET_URL = "https://wafra-pos.soultech.ae"
LOGIN_URL = "https://wafra-pos.soultech.ae/api/method/login"
# Authentication credentials
AUTH_DATA = {
    'usr': 'Administrator',  # Replace with your username
    'pwd': '4321actioon',  # Replace with your password
}

API_KEY = "f2f213e09e8018b"
API_SECRET = "d0258ab0ca308ed"

WKHTMLTOPDF = 'C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe'