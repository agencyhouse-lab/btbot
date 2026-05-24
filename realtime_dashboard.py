#!/usr/bin/env python3
"""REALTIME DASHBOARD"""
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from datetime import datetime

class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            html = """
            <html><head><title>Trading Dashboard</title></head>
            <body><h1>🤖 Trading Bot Dashboard</h1>
            <p>All bots online</p></body></html>
            """
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(html.encode())
    
    def log_message(self, format, *args):
        pass  # Suppress logging

if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', 8888), DashboardHandler)
    print("Dashboard running on http://maxhive.cloud:8888")
    server.serve_forever()

