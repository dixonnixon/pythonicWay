import json
import logging
import re
from http.server import BaseHTTPRequestHandler, HTTPServer
import csv
from io import StringIO
import sqlite3
from datetime import datetime

DB_NAME = "db.sqlite"

def select_report():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""WITH A as (SELECT SUM(Amount) as expenses  from logs where Type = 'Expense'), 
                b as (SELECT SUM(Amount) as incomes  from logs where Type = 'Income')  
                
                Select b.incomes as gross_revenue, (b.incomes - a.expenses) as net_revenue,
                    a.expenses 
                from a, b ; 
    """)
    rows = cur.fetchone()
    conn.close()
    print(rows)
    return { "gross_revenue" : rows[0], "net_revenue": rows[1], "expenses": rows[2]}

def insert_record(parsed):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    args = parsed
    # print(args)
    # cur.execute('INSERT INTO logs VALUES (?,?,?,?,?)', args)
    print(args + args)
    cur.execute("""INSERT INTO logs(Date,Type,Amount,Memo) 
                SELECT ?, ?, ?, ?
                WHERE NOT EXISTS (
                    SELECT 1 FROM logs 
                    WHERE Date = ?
                    AND Type = ?
                    AND Amount = ?
                    AND Memo = ?
                )
    """, args + args)
    conn.commit()
    conn.close()

"""
    SELECT SUM(Amount) as gross_revenue
    WHERE Type = 'Expense'
"""



def delete_table():
    conn = sqlite3.connect(DB_NAME)
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("DROP TABLE logs")
            conn.commit()
    except sqlite3.Error as e:
        print(e)


def create_table():
    conn = sqlite3.connect(DB_NAME)

    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS logs (
                Date TEXT, 
                Type TEXT, 
                Amount FLOAT,
                Memo TEXT
                );""")
            #                 --created DATETIME DEFAULT CURRENT_TIMESTAMP

            conn.commit()
    except sqlite3.Error as e:
        print(e)

def parse_csv_line(line):
  """Parses a CSV line into a tuple.

  Args:
      line: The CSV line as a string.

  Returns:
      A tuple containing the parsed data (date, type, amount, description).
  """

  reader = csv.reader([line])
  row = next(reader)
  return tuple(row)

def parse_line(line):
    parsed = [l.strip() for l in line.split(", ")]
    print(parsed)
    return [
        parsed[0],
        parsed[1],
        parsed[2],
        parsed[3]
    ]

def decomment(csvfile):
    for row in csvfile:
        raw = row.split('#')[0].strip()
        parsed = parse_csv_line(raw)
        field_num = len(parsed)
                
        if raw and field_num > 1: yield ', '.join(parse_csv_line(raw))


class LocalData(object):
    records = {"1": "record"}


class HTTPRequestHandler(BaseHTTPRequestHandler):
    

    def do_POST(self):
        if re.search('/transactions', self.path):
            content_type = self.headers['Content-Type']
            length = int(self.headers.get('content-length'))
            request_data = self.rfile.read(length)
            csv_file = StringIO(request_data.decode('utf-8'))

            data = []
            for line in decomment(csv_file):
                record = parse_line(line)
                # record.append(datetime.now().strftime("%Y-%m-%dT%H:%M:%S"))
                data.append(record)


            for line in data:
                insert_record(line)
            # LocalData.records[] = data
            

            self.send_response(200)
            
        else:
            self.send_response(403)
        self.end_headers()

    def do_GET(self):
        if re.search('/report', self.path):
            record_id = self.path.split('/')[-1]
            print(record_id)
            # print()
            # if record_id in LocalData.records:
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()

            #     # Return json, even though it came in as POST URL params
            # data = json.dumps(LocalData.records[record_id]).encode('utf-8')
            #     logging.info("get record %s: %s", record_id, data)
            self.wfile.write(json.dumps(select_report()).encode('utf-8'))

            # else:
            #     self.send_response(404, 'Not Found: record does not exist')
        else:
            self.send_response(403)
        self.end_headers()

        
if __name__ == '__main__':
    create_table()
    server = HTTPServer(('localhost', 8000), HTTPRequestHandler)
    logging.info('Starting httpd...\n')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
    logging.info('Stopping httpd...\n')