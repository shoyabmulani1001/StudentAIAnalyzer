"""
main.py — Student AI Analyzer Entry Point
Run this to start the Flask development server at http://localhost:5000
"""
from app import app

if __name__ == "__main__":
    print("=" * 52)
    print("  Student AI Analyzer — Backend Server")
    print("  http://localhost:5000")
    print("=" * 52)
    app.run(debug=True, port=5000, host="0.0.0.0")
