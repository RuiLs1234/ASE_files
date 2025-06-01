from flask import Flask, jsonify, render_template_string, request
import sqlite3
import os

app = Flask(__name__)

HTML_PAGE = """
<!DOCTYPE html>
<html lang="pt-PT">
<head>
    <meta charset="UTF-8" />
    <title>Temperaturas Recebidas</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f7f9fc;
            color: #333;
            padding: 40px;
        }
        h1 {
            text-align: center;
            margin-bottom: 30px;
            color: #2c3e50;
        }
        .table-container, .form-container {
            max-width: 1000px;
            margin: 0 auto 30px auto;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            border-radius: 10px;
            background-color: #fff;
            padding: 20px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        thead {
            background-color: #2980b9;
            color: white;
        }
        th, td {
            padding: 14px 16px;
            text-align: center;
            border-bottom: 1px solid #ddd;
        }
        tbody tr:hover {
            background-color: #f1f1f1;
        }
        #alertBox {
            background-color: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
            padding: 20px;
            max-width: 500px;
            margin: 20px auto;
            border-radius: 5px;
            text-align: center;
            font-weight: bold;
        }
        #alertBox button {
            margin-top: 15px;
            padding: 8px 16px;
            background-color: #721c24;
            border: none;
            color: white;
            font-weight: bold;
            cursor: pointer;
            border-radius: 4px;
        }
        #alertBox button:hover {
            background-color: #a71d2a;
        }
        input[type=number] {
            width: 120px;
            padding: 10px;
            margin: 5px;
        }
        button.submit-btn {
            padding: 10px 20px;
            background-color: #2980b9;
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
        }
        button.submit-btn:hover {
            background-color: #1f6391;
        }
    </style>
</head>
<body>
    <h1>Temperaturas Recebidas</h1>

    <div id="alertBox" style="display:none;">
        <div id="alertText"></div>
        <button onclick="dismissAlert()">OK</button>
    </div>

    <div class="form-container">
        <h2>Definir Limites</h2>
        <form id="limitForm" onsubmit="submitLimits(event)">
            <label>Temp Mín:
                <input type="number" step="0.01" id="minTemp" name="minTemp">
            </label>
            <label>Temp Máx:
                <input type="number" step="0.01" id="maxTemp" name="maxTemp">
            </label><br>
            <label>Hum Mín:
                <input type="number" step="0.01" id="minHum" name="minHum">
            </label>
            <label>Hum Máx:
                <input type="number" step="0.01" id="maxHum" name="maxHum">
            </label><br>
            <button type="submit" class="submit-btn">Guardar</button>
        </form>
    </div>

    <div class="table-container">
        <table id="dataTable">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Temperatura (°C)</th>
                    <th>Humidade (%)</th>
                    <th>Data e Hora</th>
                </tr>
            </thead>
            <tbody></tbody>
        </table>
    </div>

<script>
    async function loadData() {
        const response = await fetch('/data');
        const data = await response.json();
        const tableBody = document.querySelector('#dataTable tbody');
        tableBody.innerHTML = '';

        data.forEach(row => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${row.ID}</td>
                <td>${parseFloat(row.Temp).toFixed(2)}</td>
                <td>${parseFloat(row.Hum).toFixed(2)}</td>
                <td>${row.Time}</td>
            `;
            tableBody.appendChild(tr);
        });
    }

    async function checkAlert() {
        const response = await fetch('/alert');
        const alertData = await response.json();
        if(alertData.showAlert) {
            document.getElementById('alertText').textContent = alertData.message;
            document.getElementById('alertBox').style.display = 'block';
        }
    }

    async function dismissAlert() {
        await fetch('/alert', { method: 'DELETE' });
        document.getElementById('alertBox').style.display = 'none';
    }

    async function submitLimits(event) {
        event.preventDefault();
        const limits = {
            min: document.getElementById('minTemp').value,
            max: document.getElementById('maxTemp').value,
            minHum: document.getElementById('minHum').value,
            maxHum: document.getElementById('maxHum').value
        };

        const res = await fetch('/set_limits', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(limits)
        });

        if (res.ok) alert('Limites guardados com sucesso!');
        else alert('Erro ao guardar limites.');
    }

    async function loadLimits() {
        const res = await fetch('/get_limits');
        if (!res.ok) return;

        const data = await res.json();
        document.getElementById('minTemp').value = data.min || '';
        document.getElementById('maxTemp').value = data.max || '';
        document.getElementById('minHum').value = data.minHum || '';
        document.getElementById('maxHum').value = data.maxHum || '';
    }

    window.onload = () => {
        loadData();
        loadLimits();
        checkAlert();
        setInterval(() => {
            loadData();
            checkAlert();
        }, 5000);
    }
</script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

@app.route('/data')
def get_data():
    conn = sqlite3.connect('mock_database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM temperatureinfo ORDER BY ID DESC")
    rows = c.fetchall()
    conn.close()
    data = [{"ID": row[0], "Temp": row[1], "Hum": row[2], "Time": row[3]} for row in rows]
    return jsonify(data)

@app.route('/alert', methods=['GET', 'DELETE'])
def alert():
    warning_file = os.path.join(os.path.dirname(__file__), 'warning.txt')
    if request.method == 'GET':
        if os.path.exists(warning_file):
            with open(warning_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            return jsonify({"showAlert": True, "message": content})
        else:
            return jsonify({"showAlert": False, "message": ""})
    elif request.method == 'DELETE':
        if os.path.exists(warning_file):
            os.remove(warning_file)
        return jsonify({"success": True})

@app.route('/set_limits', methods=['POST'])
def set_limits():
    data = request.json
    minT = data.get("min", "")
    maxT = data.get("max", "")
    minH = data.get("minHum", "")
    maxH = data.get("maxHum", "")
    filepath = os.path.join(os.path.dirname(__file__), 'max_min.txt')
    with open(filepath, 'w') as f:
        f.write(f"{minT},{maxT},{minH},{maxH}")
    return jsonify({"success": True})

@app.route('/get_limits')
def get_limits():
    filepath = os.path.join(os.path.dirname(__file__), 'max_min.txt')
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            parts = f.read().strip().split(',')
            return jsonify({
                "min": parts[0] if len(parts) > 0 else "",
                "max": parts[1] if len(parts) > 1 else "",
                "minHum": parts[2] if len(parts) > 2 else "",
                "maxHum": parts[3] if len(parts) > 3 else ""
            })
    return jsonify({})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
