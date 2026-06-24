#!/usr/bin/env python3
"""
connectors/elk.py — ELK Stack connector for netdefense
Author: Chad Hackerman
"""

import os
import time
import threading
import requests
from datetime import datetime, timedelta


class ELKConnector:
    """
    Queries Elasticsearch for new security events and forwards
    them to the dashboard via the provided callback.
    """

    def __init__(self, callback, poll_interval=10):
        self.host     = os.getenv("ELK_HOST", "localhost")
        self.port     = os.getenv("ELK_PORT", "9200")
        self.callback = callback
        self.poll_interval = poll_interval
        self.base_url = f"http://{self.host}:{self.port}"
        self._running = False

    def _query(self):
        """Fetch events from the last poll window."""
        since = (datetime.utcnow() - timedelta(seconds=self.poll_interval)).isoformat()
        url = f"{self.base_url}/security-events-*/_search"
        body = {
            "query": {
                "range": {
                    "@timestamp": {"gte": since}
                }
            },
            "sort": [{"@timestamp": "desc"}],
            "size": 100
        }
        try:
            resp = requests.post(url, json=body, timeout=10)
            resp.raise_for_status()
            hits = resp.json().get("hits", {}).get("hits", [])
            return [h["_source"] for h in hits]
        except requests.RequestException as e:
            print(f"[elk] Connection error: {e}")
            return []

    def _normalize(self, raw_event):
        """Map a raw Elasticsearch document to the common netdefense event format."""
        return {
            "source":      "elk",
            "severity":    raw_event.get("event", {}).get("severity", "UNKNOWN").upper(),
            "category":    raw_event.get("rule", {}).get("name", "Unknown"),
            "src_ip":      raw_event.get("source", {}).get("ip", ""),
            "dst_ip":      raw_event.get("destination", {}).get("ip", ""),
            "description": raw_event.get("message", ""),
            "timestamp":   raw_event.get("@timestamp", datetime.utcnow().isoformat())
        }

    def _poll(self):
        while self._running:
            events = self._query()
            for raw in events:
                self.callback(self._normalize(raw))
            time.sleep(self.poll_interval)

    def start(self):
        self._running = True
        t = threading.Thread(target=self._poll, daemon=True)
        t.start()
        print("[elk] Connector started.")

    def stop(self):
        self._running = False
