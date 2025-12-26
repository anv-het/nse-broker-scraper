"""
Server Startup Script
=====================
Run this file to start the NSE Broker Management System backend server.

Usage:
    python run_server.py
"""

import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import run_server

if __name__ == '__main__':
    run_server()
