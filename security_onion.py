#!/usr/bin/env python3
"""
connectors/security_onion.py — Security Onion connector for netdefense
Author: Chad Hackerman
"""

import os
import time
import threading
import requests
from datetime import datetime


class SecurityOnionConnector:
    """
    Pulls alerts from the Security Onion REST API and forwards
    them to the dashboard via the provided callback.
    """

    def __init__(self, callback, poll_interval=15):
        self.host     = os.getenv("SECURITY_ONION_HOST", "localhost")
        self.api_key  = os.getenv("SECURITY_ONION_API_KEY", "")
        self.callback = callback
        self.poll_interval = poll_interval
        self.base_url = f"https://{self.host}/api"
        self._running = False
        self._last_seen_id = None

    def _get_headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def _fetch_alerts(self):
        """Fetch new alerts since the last seen ID."""
        url = f"{self.base_url}/alerts"
        params = {"limit": 50}
        if self._last_seen_id:
            params["after_id"] = self._last_seen_id
        try:
            resp = requests.get(url, headers=self._get_headers(), params=params, verify=False, timeout=10)
            resp.raise_for_status()
            return resp.json().get("alerts", [])
        except requests.RequestException as e:
            print(f"[security_onion] Connection error: {e}")
            return []

    def _normalize(self, raw_alert):
        """Map a raw Security Onion alert to the common netdefense event format."""
        severity_map = {1: "CRITICAL", 2: "HIGH", 3: "MEDIUM", 4: "LOW"}
        priority = raw_alert.get("priority", 4)
        return {
            "source":      "security_onion",
            "severity":    severity_map.get(priority, "UNKNOWN"),
            "category":    raw_alert.get("signature", "Unknown"),
            "src_ip":      raw_alert.get("src_ip", ""),
            "dst_ip":      raw_alert.get("dst_ip", ""),
            "description": raw_alert.get("message", ""),
            "timestamp":   raw_alert.get("timestamp", datetime.utcnow().isoformat())
        }

    def _poll(self):
        while self._running:
            alerts = self._fetch_alerts()
            for alert in alerts:
                self.callback(self._normalize(alert))
                self._last_seen_id = alert.get("id", self._last_seen_id)
            time.sleep(self.poll_interval)

    def start(self):
        self._running = True
        t = threading.Thread(target=self._poll, daemon=True)
        t.start()
        print("[security_onion] Connector started.")

    def stop(self):
        self._running = False
