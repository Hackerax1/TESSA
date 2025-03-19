#!/usr/bin/env python3
"""
Test script to verify the new template structure works correctly.
"""
import os
import sys
from flask import Flask, render_template

app = Flask(__name__, 
           static_folder='static',
           static_url_path='/static',
           template_folder='templates')

@app.route('/')
def home():
    """Render the home page using the new base.html template"""
    return render_template('base.html')

@app.route('/old')
def old_home():
    """Render the home page using the original index.html template"""
    return render_template('index.html')

if __name__ == '__main__':
    print("Starting test server to verify template structure...")
    print("Access the new template at: http://localhost:5000/")
    print("Access the old template at: http://localhost:5000/old")
    print("Press Ctrl+C to stop the server")
    app.run(debug=True)
