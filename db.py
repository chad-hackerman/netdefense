#!/usr/bin/env python3
"""
db.py — Database models and initialization for netdefense
Author: Chad Hackerman
"""

import click
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Event(db.Model):
    """A security event ingested from a SIEM source."""
    __tablename__ = "events"

    id          = db.Column(db.Integer, primary_key=True)
    source      = db.Column(db.String(50), nullable=False)   # splunk, elk, security_onion
    severity    = db.Column(db.String(20), nullable=False)   # CRITICAL, HIGH, MEDIUM, LOW
    category    = db.Column(db.String(100))                  # e.g. "Brute Force", "Port Scan"
    src_ip      = db.Column(db.String(45))
    dst_ip      = db.Column(db.String(45))
    description = db.Column(db.Text)
    raw         = db.Column(db.Text)                         # original raw log line
    timestamp   = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            "id":          self.id,
            "source":      self.source,
            "severity":    self.severity,
            "category":    self.category,
            "src_ip":      self.src_ip,
            "dst_ip":      self.dst_ip,
            "description": self.description,
            "timestamp":   self.timestamp.isoformat()
        }


class AlertRule(db.Model):
    """A user-defined alerting rule."""
    __tablename__ = "alert_rules"

    id        = db.Column(db.Integer, primary_key=True)
    name      = db.Column(db.String(100), nullable=False)
    condition = db.Column(db.Text, nullable=False)  # e.g. "severity == CRITICAL"
    channel   = db.Column(db.String(50), default="slack")
    enabled   = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id":        self.id,
            "name":      self.name,
            "condition": self.condition,
            "channel":   self.channel,
            "enabled":   self.enabled,
            "created_at": self.created_at.isoformat()
        }


@click.command("init-db")
def init_db_command():
    """Initialize the database tables."""
    from app import app
    with app.app_context():
        db.create_all()
    click.echo("Database initialized.")
