#!/usr/bin/env python3
from flask import Flask, render_template, request, jsonify
import os
from proxmox_nli.core import ProxmoxNLI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Initialize the ProxmoxNLI instance (will be properly configured on app start)
proxmox_nli = None

@app.route('/')
def home():
    """Render the home page"""
    return render_template('index.html')

@app.route('/query', methods=['POST'])
def process_query():
    """Process a natural language query"""
    query = request.json.get('query', '')
    if not query:
        return jsonify({'error': 'No query provided'})
    
    response = proxmox_nli.process_query(query)
    return jsonify({'response': response})

@app.route('/tts', methods=['POST'])
def text_to_speech():
    """Convert text to speech"""
    text = request.json.get('text', '')
    if not text:
        return jsonify({'error': 'No text provided'})
    
    # In a real implementation, you would use a TTS service here
    # For now, we'll just return the text
    return jsonify({'audio': 'data:audio/wav;base64,', 'text': text})

@app.route('/stt', methods=['POST'])
def speech_to_text():
    """Convert speech to text"""
    # In a real implementation, you would process audio data here
    # For now, we'll just return an empty string
    return jsonify({'text': ''})

def start_app(host, user, password, realm='pam', verify_ssl=False, debug=False):
    """Start the Flask application with the given Proxmox credentials"""
    global proxmox_nli
    
    # Initialize ProxmoxNLI with the provided credentials
    proxmox_nli = ProxmoxNLI(host, user, password, realm, verify_ssl)
    
    # Create templates directory if it doesn't exist
    templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
    if not os.path.exists(templates_dir):
        os.makedirs(templates_dir)
    
    # Start the Flask application
    app.run(host='0.0.0.0', port=5000, debug=debug)

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Proxmox NLI Web Server')
    parser.add_argument('--host', required=True, help='Proxmox host')
    parser.add_argument('--user', required=True, help='Proxmox user')
    parser.add_argument('--password', required=True, help='Proxmox password')
    parser.add_argument('--realm', default='pam', help='Proxmox realm')
    parser.add_argument('--verify-ssl', action='store_true', help='Verify SSL certificate')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    start_app(
        host=args.host,
        user=args.user,
        password=args.password,
        realm=args.realm,
        verify_ssl=args.verify_ssl,
        debug=args.debug
    )