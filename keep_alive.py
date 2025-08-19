# keep_alive.py
# Egyszerű Flask webszerver, hogy az UptimeRobot 5 percenként pingelhesse
# és ébren tartsa a Replitet.

import os
import threading
from flask import Flask, jsonify

app = Flask(__name__)

@app.get("/")
def root():
    return "OK", 200

@app.get("/health")
def health():
    return jsonify(status="up"), 200

def keep_alive():
    # Replit a PORT környezeti változót adja meg
    port = int(os.environ.get("PORT", "8080"))
    thread = threading.Thread(target=lambda: app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
        use_reloader=False
    ))
    thread.daemon = True
    thread.start()