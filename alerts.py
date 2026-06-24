#!/usr/bin/env python3
"""
alerts.py — Alerting engine for netdefense
Evaluates incoming events against user-defined rules and sends
notifications via Slack, Microsoft Teams, or email.
Author: Chad Hackerman
"""

import os
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


SLACK_WEBHOOK   = os.getenv("SLACK_WEBHOOK_URL", "")
TEAMS_WEBHOOK   = os.getenv("TEAMS_WEBHOOK_URL", "")
ALERT_EMAIL     = os.getenv("ALERT_EMAIL", "")
SMTP_HOST       = os.getenv("SMTP_HOST", "localhost")
SMTP_PORT       = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER       = os.getenv("SMTP_USER", "")
SMTP_PASSWORD   = os.getenv("SMTP_PASSWORD", "")


class AlertEngine:
    def __init__(self, redis_client=None):
        self.redis = redis_client
        # Simple built-in rules (supplement with DB rules from AlertRule model)
        self.default_rules = [
            {"name": "Critical Event",  "condition": lambda e: e.get("severity") == "CRITICAL", "channel": "slack"},
            {"name": "High Severity",   "condition": lambda e: e.get("severity") == "HIGH",     "channel": "teams"},
        ]

    def evaluate(self, event: dict):
        """Check an event against all active rules and fire alerts."""
        for rule in self.default_rules:
            if rule["condition"](event):
                self._fire(rule["name"], event, rule["channel"])

    def _fire(self, rule_name: str, event: dict, channel: str):
        """Send an alert to the appropriate channel."""
        message = self._format_message(rule_name, event)
        if channel == "slack":
            self._send_slack(message)
        elif channel == "teams":
            self._send_teams(message)
        elif channel == "email":
            self._send_email(rule_name, message)
        else:
            print(f"[alerts] Unknown channel: {channel}")

    def _format_message(self, rule_name: str, event: dict) -> str:
        return (
            f"🚨 *netdefense Alert — {rule_name}*\n"
            f"Severity : {event.get('severity', 'UNKNOWN')}\n"
            f"Source   : {event.get('source', 'unknown')}\n"
            f"Category : {event.get('category', 'unknown')}\n"
            f"Src IP   : {event.get('src_ip', 'N/A')}\n"
            f"Dst IP   : {event.get('dst_ip', 'N/A')}\n"
            f"Details  : {event.get('description', '')[:200]}"
        )

    def _send_slack(self, message: str):
        if not SLACK_WEBHOOK:
            print("[alerts] SLACK_WEBHOOK_URL not configured.")
            return
        try:
            resp = requests.post(SLACK_WEBHOOK, json={"text": message}, timeout=5)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"[alerts] Slack error: {e}")

    def _send_teams(self, message: str):
        if not TEAMS_WEBHOOK:
            print("[alerts] TEAMS_WEBHOOK_URL not configured.")
            return
        try:
            payload = {
                "@type": "MessageCard",
                "@context": "http://schema.org/extensions",
                "text": message
            }
            resp = requests.post(TEAMS_WEBHOOK, json=payload, timeout=5)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"[alerts] Teams error: {e}")

    def _send_email(self, subject: str, body: str):
        if not ALERT_EMAIL:
            print("[alerts] ALERT_EMAIL not configured.")
            return
        try:
            msg = MIMEMultipart()
            msg["From"]    = SMTP_USER
            msg["To"]      = ALERT_EMAIL
            msg["Subject"] = f"[netdefense] {subject}"
            msg.attach(MIMEText(body, "plain"))
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.sendmail(SMTP_USER, ALERT_EMAIL, msg.as_string())
        except Exception as e:
            print(f"[alerts] Email error: {e}")
