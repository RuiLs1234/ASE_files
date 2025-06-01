from flask import Flask, jsonify, render_template_string
import sqlite3

app = Flask(__name__)

HTML_PAGE = """
<!DOCTYPE html>
<html lang="pt-PT">
<head>
    <meta charset="UTF-8">
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

        .table-container {
            max-width: 900px;
            margin: 0 auto;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            border-radius: 10px;
            overflow: hidden;
            background-color: #fff;
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

        th:first-child {
            border-top-left-radius: 10px;
        }

        th:last-child {
            border-top-right-radius: 10px;
        }
    </style>
</head>
<body>
    <h1>Temperaturas Recebidas</h1>
    <div class="table-container">
        <table id="dataTable">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Temperatura (°C)</th>
                    <th>Data e Hora</th>
                </tr>
            </thead>
            <tbody></tbody>
        </table>
    </div>

    <script>
        async function loadData() {
            try {
                const response = await fetch('/data');
                const data = await response.json();
                const tableBody = document.querySelector('#dataTable tbody');
                tableBody.innerHTML = '';

                data.forEach(row => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td>${row.ID}</td>
                        <td>${row.Temp}</td>
                        <td>${row.Time}</td>
                    `;
                    tableBody.appendChild(tr);
                });
            } catch (error) {
                console.error('Erro ao carregar dados:', error);
            }
        }

        window.onload = () => {
            loadData();
            setInterval(loadData, 5000); // Atualizar a cada 5 segundos
        };
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
    c.execute("SELECT * FROM temperatureinfo")
    rows = c.fetchall()
    conn.close()
    data = [{"ID": row[0], "Temp": row[1], "Time": row[2]} for row in rows]
    return jsonify(data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
