"""
main.py - Student AI Analyzer Entry Point
Starts the Flask development server.
"""
from app import app

if __name__ == "__main__":
    print("=" * 50)
    print("  Student AI Analyzer — Backend Server")
    print("  http://localhost:5000")
    print("=" * 50)
    app.run(debug=True, port=5000, host="0.0.0.0")
