from flask import Flask, jsonify
import sqlite3

app = Flask(__name__)

@app.route('/data', methods=['GET'])
def get_data():
    conn = sqlite3.connect('mock_database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM temperatureinfo")
    rows = c.fetchall()
    conn.close()
    data = [{"ID": row[0], "Temp": row[1], "Time": row[2]} for row in rows]
    return jsonify(data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
