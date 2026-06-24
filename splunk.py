#!/usr/bin/env python3
"""
connectors/splunk.py — Splunk API connector for netdefense
Author: Chad Hackerman
"""

import os
import time
import threading
import requests
from datetime import datetime


class SplunkConnector:
    """
    Polls the Splunk REST API for new security events and forwards
    them to the dashboard via the provided callback.
    """

    def __init__(self, callback, poll_interval=10):
        self.host     = os.getenv("SPLUNK_HOST", "localhost")
        self.port     = os.getenv("SPLUNK_PORT", "8089")
        self.token    = os.getenv("SPLUNK_TOKEN", "")
        self.callback = callback
        self.poll_interval = poll_interval
        self.base_url = f"https://{self.host}:{self.port}"
        self._running = False

    def _get_headers(self):
        return {
            "Authorization": f"Splunk {self.token}",
            "Content-Type": "application/json"
        }

    def _search(self, query):
        """Run a Splunk search and return results."""
        url = f"{self.base_url}/services/search/jobs"
        payload = {
            "search": f"search {query}",
            "output_mode": "json",
            "earliest_time": "-1m"
        }
        try:
            resp = requests.post(url, headers=self._get_headers(), data=payload, verify=False, timeout=10)
            resp.raise_for_status()
            return resp.json().get("results", [])
        except requests.RequestException as e:
            print(f"[splunk] Connection error: {e}")
            return []

    def _normalize(self, raw_event):
        """Map a raw Splunk event to the common netdefense event format."""
        return {
            "source":      "splunk",
            "severity":    raw_event.get("severity", "UNKNOWN").upper(),
            "category":    raw_event.get("signature", "Unknown"),
            "src_ip":      raw_event.get("src_ip", ""),
            "dst_ip":      raw_event.get("dest_ip", ""),
            "description": raw_event.get("_raw", ""),
            "timestamp":   datetime.utcnow().isoformat()
        }

    def _poll(self):
        while self._running:
            events = self._search("index=security sourcetype=alert")
            for raw in events:
                self.callback(self._normalize(raw))
            time.sleep(self.poll_interval)

    def start(self):
        """Start the polling thread."""
        self._running = True
        t = threading.Thread(target=self._poll, daemon=True)
        t.start()
        print("[splunk] Connector started.")

    def stop(self):
        self._running = False
