#!/usr/bin/env python3
import json
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

DB_PATH = Path(__file__).with_name('budget.db')

FIELDS = [
    "Resource ID","cTool ID","Resource Name","Contract Type","City","Pod","2026 GPDM Rate($)","Allocate Month","Allocate budget($)","Gap($)",
    "Project code","Project Name","BP ID","BP Name","Clarity ID","Clarity Name","Role End date","SVS","Supplier Code","Billable Service Code",
    "Total FTE($)","FTE","BP Status","BP Total Budget(K)","Suggested BP"
]


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = connect()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS rows_data (
            row_key TEXT PRIMARY KEY,
            data_json TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def row_key(d):
    return f"{d.get('Resource ID','')}|{d.get('Allocate Month','')}|{d.get('Clarity ID','')}"


def load_rows():
    conn = connect()
    rows = [json.loads(r['data_json']) for r in conn.execute("SELECT data_json FROM rows_data").fetchall()]
    conn.close()
    return rows


def upsert_rows(items):
    conn = connect()
    for item in items:
        key = row_key(item)
        if not key.strip('||'):
            continue
        conn.execute(
            "INSERT INTO rows_data(row_key, data_json) VALUES (?, ?) ON CONFLICT(row_key) DO UPDATE SET data_json=excluded.data_json",
            (key, json.dumps(item, ensure_ascii=False)),
        )
    conn.commit()
    conn.close()


def clear_rows():
    conn = connect()
    conn.execute("DELETE FROM rows_data")
    conn.commit()
    conn.close()


def to_num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def compute_dashboard(rows):
    total_alloc = sum(to_num(r.get('Allocate budget($)')) for r in rows)
    total_gap = sum(to_num(r.get('Gap($)')) for r in rows)
    bp = {}
    for r in rows:
        bpid = r.get('BP ID', '')
        if not bpid:
            continue
        bp.setdefault(bpid, {
            'status': r.get('BP Status', 'TBC'),
            'total': to_num(r.get('BP Total Budget(K)')),
            'allocated': 0.0,
        })
        bp[bpid]['allocated'] += to_num(r.get('Allocate budget($)'))
    overrun = sum(1 for v in bp.values() if v['total'] - v['allocated'] < 0)
    received = sum(1 for v in bp.values() if v['status'] == 'Received')
    return {
        'totalAllocatedK': round(total_alloc, 1),
        'totalGapK': round(total_gap, 1),
        'overrunBpCount': overrun,
        'receivedBpCount': received,
        'totalBpCount': len(bp),
        'rowsCount': len(rows),
    }


def compute_resource(rows):
    grouped = {}
    for r in rows:
        rid = r.get('Resource ID', '')
        if not rid:
            continue
        grouped.setdefault(rid, dict(r))
        grouped[rid]['Gap($)'] = to_num(grouped[rid].get('Gap($)')) + to_num(r.get('Gap($)'))
    return list(grouped.values())


def compute_allocation(rows):
    month_sum = {}
    for r in rows:
        k = (r.get('Resource ID', ''), r.get('Allocate Month', ''))
        month_sum[k] = month_sum.get(k, 0.0) + to_num(r.get('FTE'))
    out = []
    for r in rows:
        k = (r.get('Resource ID', ''), r.get('Allocate Month', ''))
        out.append({
            **r,
            'isFteValid': month_sum.get(k, 0.0) <= 1.0,
            'isBpStatusValid': r.get('BP Status') == 'Received',
        })
    return out


def compute_gap(rows):
    grouped = {}
    for r in rows:
        rid = r.get('Resource ID', '')
        if not rid:
            continue
        grouped.setdefault(rid, {
            'Resource ID': rid,
            'Resource Name': r.get('Resource Name', ''),
            'City': r.get('City', ''),
            'Annual Gap($)': 0.0,
            'Gap Months': set(),
            'Suggested BP': set(),
        })
        g = to_num(r.get('Gap($)'))
        grouped[rid]['Annual Gap($)'] += g
        if g > 0:
            grouped[rid]['Gap Months'].add(r.get('Allocate Month', ''))
        if r.get('Suggested BP'):
            grouped[rid]['Suggested BP'].add(r.get('Suggested BP'))
    out = []
    for v in grouped.values():
        out.append({
            **v,
            'Annual Gap($)': round(v['Annual Gap($)'], 1),
            'Gap Months': sorted(x for x in v['Gap Months'] if x),
            'Suggested BP': sorted(v['Suggested BP']),
        })
    return out


def compute_bp(rows):
    grouped = {}
    for r in rows:
        bpid = r.get('BP ID', '')
        if not bpid:
            continue
        grouped.setdefault(bpid, {
            'BP ID': bpid,
            'Project code': r.get('Project code', ''),
            'Status': r.get('BP Status', 'TBC'),
            'Total Budget(K)': to_num(r.get('BP Total Budget(K)')),
            'Allocated(K)': 0.0,
        })
        grouped[bpid]['Allocated(K)'] += to_num(r.get('Allocate budget($)'))
    out = []
    for v in grouped.values():
        rem = v['Total Budget(K)'] - v['Allocated(K)']
        out.append({**v, 'Remaining(K)': round(rem, 1), 'Overrun': rem < 0})
    return out


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, payload):
        body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET,POST,DELETE,OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self._send(200, {'ok': True})

    def do_GET(self):
        path = urlparse(self.path).path
        rows = load_rows()
        if path == '/health':
            return self._send(200, {'status': 'ok'})
        if path == '/api/fields':
            return self._send(200, {'fields': FIELDS})
        if path == '/api/rows':
            return self._send(200, {'rows': rows})
        if path == '/api/dashboard':
            return self._send(200, compute_dashboard(rows))
        if path == '/api/resource':
            return self._send(200, {'rows': compute_resource(rows)})
        if path == '/api/allocation':
            return self._send(200, {'rows': compute_allocation(rows)})
        if path == '/api/gap':
            return self._send(200, {'rows': compute_gap(rows)})
        if path == '/api/bp':
            return self._send(200, {'rows': compute_bp(rows)})
        self._send(404, {'error': 'not found'})

    def do_POST(self):
        path = urlparse(self.path).path
        if path != '/api/rows':
            return self._send(404, {'error': 'not found'})
        length = int(self.headers.get('Content-Length', '0'))
        payload = json.loads(self.rfile.read(length) or b'{}')
        items = payload.get('rows', [])
        if isinstance(items, dict):
            items = [items]
        upsert_rows(items)
        self._send(200, {'ok': True, 'count': len(items)})

    def do_DELETE(self):
        path = urlparse(self.path).path
        if path != '/api/rows':
            return self._send(404, {'error': 'not found'})
        clear_rows()
        self._send(200, {'ok': True})


def run():
    init_db()
    server = ThreadingHTTPServer(('0.0.0.0', 8000), Handler)
    print('Budget backend running on http://0.0.0.0:8000')
    server.serve_forever()


if __name__ == '__main__':
    run()
