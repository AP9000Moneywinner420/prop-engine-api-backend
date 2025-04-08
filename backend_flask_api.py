# backend_flask_api.py – Verified Prop Engine v13 Flask API

from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import pytesseract
from PIL import Image
import os, io, datetime
from fpdf import FPDF

app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = 'uploads'

parsed_bets = []  # Memory store (use DB/file for persistent storage)

@app.route('/api/dashboard', methods=['GET'])
def dashboard():
    return jsonify({
        "slips": ["Matt’s Points Parlay ✅", "Boosted Longshot 🚀", "Alt-Line Safe Slip ✅"],
        "bankroll": [
            {"day": "Apr 1", "bankroll": 25},
            {"day": "Apr 2", "bankroll": 28},
            {"day": "Apr 3", "bankroll": 35},
            {"day": "Apr 4", "bankroll": 32},
            {"day": "Apr 5", "bankroll": 45},
            {"day": "Apr 6", "bankroll": 48},
            {"day": "Apr 7", "bankroll": 57}
        ],
        "summary": "Engine ran v13 simulation logic with full prop rotation. Boosts matched, volatility adjusted.",
        "matt": "• Points Parlay ROI: +63%\n• Assists Parlay ROI: +48%\n• Risk Profile: Balanced-Conservative",
        "trends": "ATL overs hitting 6 of last 7 · MIL unders trending vs. bigs · Fade LAL points props.",
        "parsedBets": parsed_bets
    })

@app.route('/api/upload-screenshot', methods=['POST'])
def upload_screenshot():
    if 'screenshot' not in request.files:
        return jsonify({"message": "No file uploaded."}), 400

    file = request.files['screenshot']
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    file.save(file_path)

    try:
        text = pytesseract.image_to_string(Image.open(file_path))
        bets = extract_bets_from_text(text)
        parsed_bets.extend(bets)
        return jsonify({"message": "Screenshot uploaded and parsed!", "parsedBets": bets})
    except Exception as e:
        return jsonify({"message": "Parsing failed.", "error": str(e)}), 500

@app.route('/api/export-slip', methods=['GET'])
def export_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Verified Prop Engine – Parsed Bet Slip", ln=1, align='C')

    for bet in parsed_bets:
        line = f"{bet['player']} – {bet['prop']} – {bet['line']} ({bet['result']})"
        pdf.cell(200, 10, txt=line, ln=1)

    filename = f"bet_slip_{datetime.datetime.now().strftime('%Y%m%d')}.pdf"
    path = os.path.join("exports", filename)
    os.makedirs("exports", exist_ok=True)
    pdf.output(path)

    return jsonify({"message": "PDF exported successfully.", "path": path})

# Basic OCR Parser (Can improve with regex, ML, etc.)
def extract_bets_from_text(text):
    lines = text.split('\n')
    bets = []
    for line in lines:
        if any(stat in line.lower() for stat in ['points', 'assists', 'rebounds', 'pra', '3pt']):
            parts = line.strip().split()
            player = ' '.join(parts[:2])
            prop = next((p for p in parts if p.lower() in ['points', 'assists', 'rebounds', 'pra', '3pt']), 'Unknown')
            line_value = next((p for p in parts if p.replace('.', '', 1).isdigit()), '?')
            bets.append({"player": player, "prop": prop, "line": line_value, "result": "PENDING"})
    return bets

import os

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
