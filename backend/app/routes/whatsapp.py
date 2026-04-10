from flask import Blueprint, jsonify, request
import requests
import logging
from app.utils.auth import login_required

whatsapp_bp = Blueprint('whatsapp', __name__)
NODE_SERVICE_URL = "http://localhost:3001"

@whatsapp_bp.route('/status', methods=['GET'])
@login_required
def get_status():
    """Get the connection status of the WhatsApp microservice."""
    try:
        response = requests.get(f"{NODE_SERVICE_URL}/status", timeout=5)
        return jsonify(response.json()), 200
    except requests.exceptions.RequestException as e:
        logging.error(f"WhatsApp service unreachable: {str(e)}")
        return jsonify({"status": "OFFLINE", "error": "Microservice not running"}), 503

@whatsapp_bp.route('/qr', methods=['GET'])
@login_required
def get_qr():
    """Get the QR code from the WhatsApp microservice to scan and login."""
    try:
        response = requests.get(f"{NODE_SERVICE_URL}/qr", timeout=10)
        return jsonify(response.json()), 200
    except requests.exceptions.RequestException as e:
        logging.error(f"WhatsApp service unreachable for QR: {str(e)}")
        return jsonify({"status": "OFFLINE", "error": "Microservice not running"}), 503

@whatsapp_bp.route('/logout', methods=['POST'])
@login_required
def logout_whatsapp():
    """Logout the connected WhatsApp session."""
    try:
        response = requests.post(f"{NODE_SERVICE_URL}/logout", timeout=5)
        return jsonify(response.json()), 200
    except requests.exceptions.RequestException as e:
        logging.error(f"WhatsApp service unreachable for logout: {str(e)}")
        return jsonify({"success": False, "error": "Microservice not running"}), 503

@whatsapp_bp.route('/send', methods=['POST'])
@login_required
def send_message():
    """Send a manual test message via WhatsApp."""
    data = request.get_json()
    if not data or 'number' not in data or 'message' not in data:
        return jsonify({"error": "Missing number or message"}), 400
        
    try:
        response = requests.post(f"{NODE_SERVICE_URL}/send", json=data, timeout=15)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        logging.error(f"WhatsApp service unreachable for send: {str(e)}")
        return jsonify({"success": False, "error": "Microservice not running"}), 503
