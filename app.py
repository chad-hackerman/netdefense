#!/usr/bin/env python3
"""
app.py — Flask entry point for netdefense dashboard
Author: Chad Hackerman
"""

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import redis
import json
import os
from db import db, Event, AlertRule
from alerts import AlertEngine
from connectors.splunk import SplunkConnector
from connectors.elk import ELKConnector
from connectors.security_onion import SecurityOnionConnector


app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "change-me-in-production")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "postgresql://localhost/netdefense")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
socketio = SocketIO(app, cors_allowed_origins="*")
redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
alert_engine = AlertEngine(redis_client)


# ---------------------------------------------------------------------------
# Page routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


# ---------------------------------------------------------------------------
# API routes
# ---------------------------------------------------------------------------

@app.route("/api/events", methods=["GET"])
def get_events():
    """Return recent security events, with optional filters."""
    limit = request.args.get("limit", 100, type=int)
    severity = request.args.get("severity")
    source = request.args.get("source")

    query = Event.query.order_by(Event.timestamp.desc())
    if severity:
        query = query.filter_by(severity=severity.upper())
    if source:
        query = query.filter_by(source=source)

    events = query.limit(limit).all()
    return jsonify([e.to_dict() for e in events])


@app.route("/api/events/<int:event_id>", methods=["GET"])
def get_event(event_id):
    event = Event.query.get_or_404(event_id)
    return jsonify(event.to_dict())


@app.route("/api/alerts/rules", methods=["GET"])
def list_alert_rules():
    rules = AlertRule.query.all()
    return jsonify([r.to_dict() for r in rules])


@app.route("/api/alerts/rules", methods=["POST"])
def create_alert_rule():
    data = request.get_json()
    if not data or "name" not in data or "condition" not in data:
        return jsonify({"error": "Missing required fields: name, condition"}), 400
    rule = AlertRule(
        name=data["name"],
        condition=data["condition"],
        channel=data.get("channel", "slack"),
        enabled=data.get("enabled", True)
    )
    db.session.add(rule)
    db.session.commit()
    return jsonify(rule.to_dict()), 201


@app.route("/api/stats", methods=["GET"])
def get_stats():
    """Return summary statistics for the dashboard header."""
    total = Event.query.count()
    critical = Event.query.filter_by(severity="CRITICAL").count()
    high = Event.query.filter_by(severity="HIGH").count()
    sources = db.session.query(Event.source, db.func.count(Event.id)) \
                        .group_by(Event.source).all()
    return jsonify({
        "total_events": total,
        "critical": critical,
        "high": high,
        "sources": {s: c for s, c in sources}
    })


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


# ---------------------------------------------------------------------------
# WebSocket — real-time event push
# ---------------------------------------------------------------------------

@socketio.on("connect")
def on_connect():
    emit("status", {"message": "Connected to netdefense dashboard"})


def push_event(event_dict):
    """Called by SIEM connectors when a new event arrives."""
    socketio.emit("new_event", event_dict)
    alert_engine.evaluate(event_dict)


# ---------------------------------------------------------------------------
# SIEM ingestion (runs in background threads)
# ---------------------------------------------------------------------------

def start_connectors():
    connectors = [
        SplunkConnector(callback=push_event),
        ELKConnector(callback=push_event),
        SecurityOnionConnector(callback=push_event),
    ]
    for c in connectors:
        c.start()


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    start_connectors()
    socketio.run(app, host="0.0.0.0", port=5000, debug=False)
