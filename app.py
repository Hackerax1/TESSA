#!/usr/bin/env python3
from flask import Flask, render_template, request, jsonify
import os
import json
from proxmox_nli import ProxmoxNLI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Initialize the ProxmoxNLI instance (will be properly configured on app start)
proxmox_nli = None

@app.route('/')
def index():
    """Render the main web interface page"""
    app.logger.info('Rendering index page')
    return render_template('index.html')

@app.route('/api/process', methods=['POST'])
def process():
    """Process a text query from the web interface"""
    try:
        data = request.get_json()
        app.logger.info(f'Received data: {data}')
        
        if not data or 'query' not in data:
            return jsonify({'error': 'No query provided'}), 400
        
        # Process the query using the proxmox_nli instance
        response = proxmox_nli.process_query(data['query'])
        
        return jsonify({
            'query': data['query'],
            'response': response
        })
    except Exception as e:
        app.logger.error(f"Error processing request: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/process-voice', methods=['POST'])
def process_voice():
    """Process a voice recording from the web interface"""
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400
    
    audio_file = request.files['audio']
    
    # Save the audio file temporarily
    temp_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp_audio.wav')
    audio_file.save(temp_path)
    
    # Process the audio with speech recognition
    try:
        import speech_recognition as sr
        recognizer = sr.Recognizer()
        
        with sr.AudioFile(temp_path) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data)
            
        # Remove the temporary file
        os.remove(temp_path)
        
        # Process the recognized text using the proxmox_nli instance
        response = proxmox_nli.process_query(text)
        
        return jsonify({
            'query': text,
            'response': response
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def start_app(host, user, password, realm='pam', verify_ssl=False, debug=False):
    """Start the Flask application with the given Proxmox credentials"""
    global proxmox_nli
    
    # Initialize ProxmoxNLI with the provided credentials
    proxmox_nli = ProxmoxNLI(host, user, password, realm, verify_ssl)
    
    # Create templates directory if it doesn't exist
    templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
    if not os.path.exists(templates_dir):
        os.makedirs(templates_dir)
    
    # Create static directory if it doesn't exist
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
    
    # Start the Flask application
    app.run(host='0.0.0.0', port=5000, debug=debug)

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Proxmox NLI Web Interface')
    parser.add_argument('--host', default=os.getenv('PROXMOX_API_URL'), help='Proxmox host')
    parser.add_argument('--user', default=os.getenv('PROXMOX_USER'), help='Proxmox user')
    parser.add_argument('--password', default=os.getenv('PROXMOX_PASSWORD'), help='Proxmox password')
    parser.add_argument('--realm', default=os.getenv('PROXMOX_REALM', 'pam'), help='Proxmox realm')
    parser.add_argument('--verify-ssl', action='store_true', help='Verify SSL certificate')
    parser.add_argument('--debug', action='store_true', help='Enable Flask debug mode')
    parser.add_argument('--web', action='store_true', help='Start as web server with voice recognition')
    
    args = parser.parse_args()
    
    start_app(
        host=args.host,
        user=args.user,
        password=args.password,
        realm=args.realm,
        verify_ssl=args.verify_ssl,
        debug=args.debug
    )