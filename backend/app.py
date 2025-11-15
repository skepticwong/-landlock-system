# backend/app.py
from flask import Flask, request, jsonify
from datetime import datetime
import requests
import os

app = Flask(__name__)

# 🔢 Supabase Config – REPLACE with your own!
SUPABASE_URL = "https://cisgwziqcfyjbohpxeyo.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNpc2d3emlxY2Z5amJvaHB4ZXlvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjMyMjgwMDUsImV4cCI6MjA3ODgwNDAwNX0.EBG7-qXymyOuDF-h6lZp_a4ekTaqft0qeZ6zC1YQSQ0"
HEADERS = {
    "apikey": SUPABASE_KEY,
    "Content-Type": "application/json"
}

# 🌐 Health Check
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "db": "supabase"})

# 📥 Register a new plot
@app.route("/plots", methods=["POST"])
def register_plot():
    data = request.json
    required = ["owner_phone", "points", "plot_name"]
    if not all(k in data for k in required):
        return jsonify({"error": "Missing required fields"}), 400

    # Generate ID
    res = requests.get(
        f"{SUPABASE_URL}/rest/v1/plots?select=id",
        headers=HEADERS
    )
    plot_count = len(res.json()) if res.status_code == 200 else 0
    plot_id = f"PL{plot_count + 1:04d}"

    # Prepare record
    new_plot = {
        "id": plot_id,
        "owner_phone": data["owner_phone"],
        "plot_name": data["plot_name"],
        "points": data["points"],
        "area_acres": data.get("area_acres", "0"),
        "status": "pending",
        "registered_at": datetime.now().isoformat()
    }

    # Save to Supabase
    response = requests.post(
        f"{SUPABASE_URL}/rest/v1/plots",
        json=new_plot,
        headers=HEADERS
    )

    if response.status_code in [200, 201]:
        return jsonify(new_plot), 201
    else:
        return jsonify({"error": "Failed to save", "details": response.text}), 500

# 📤 Get all plots
@app.route("/plots", methods=["GET"])
def get_plots():
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/plots",
        headers=HEADERS
    )
    if response.status_code == 200:
        return jsonify(response.json())
    else:
        return jsonify({"error": "Could not fetch plots"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)