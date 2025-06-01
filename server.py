import socket
import threading
from datetime import datetime
import os
import sqlite3

# Defaults
max_temp = 30.0
min_temp = 15.0
max_hum = 80.0
min_hum = 30.0

lock = threading.Lock()

def init_db():
    try:
        conn = sqlite3.connect('mock_database.db')
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS temperatureinfo (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                Temp REAL NOT NULL,
                Hum REAL NOT NULL,
                Time TEXT NOT NULL
            )
        ''')
        conn.commit()
        conn.close()
        print("✅ Base de dados inicializada com sucesso.")
    except Exception as e:
        print(f"❌ Erro a inicializar a base de dados: {e}")

def handle_client(client_sock, addr):
    global max_temp, min_temp, max_hum, min_hum
    print(f"📡 Ligação de {addr}")

    try:
        while True:
            data = client_sock.recv(1024)
            if not data:
                break

            received = data.decode().strip()
            print(f"📥 Recebido de {addr}: {received}")

            if "ALERTA" in received:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                filename = os.path.join(os.path.dirname(__file__), "warning.txt")
                try:
                    with open(filename, "a") as f:
                        f.write(f"[{timestamp}] {received}\n")
                    print(f"⚠️  Ficheiro '{filename}' atualizado com sucesso.")
                except Exception as e:
                    print(f"❌ Erro ao escrever no ficheiro '{filename}': {e}")
                received = received.replace("ALERTA;", "")

            try:
                temp_str, hum_str = received.split(";")
                temp = float(temp_str)
                hum = float(hum_str)

                # Guardar na base de dados
                try:
                    conn = sqlite3.connect('mock_database.db')
                    c = conn.cursor()
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    c.execute("INSERT INTO temperatureinfo (Temp, Hum, Time) VALUES (?, ?, ?)", (temp, hum, timestamp))
                    conn.commit()
                    conn.close()
                    print(f"✅ Dados guardados: Temp={temp}, Hum={hum}, Time={timestamp}")
                except Exception as e:
                    print(f"❌ Erro a guardar na base de dados: {e}")

                with lock:
                    max_temp_i = max_temp
                    min_temp_i = min_temp
                    max_hum_i = max_hum
                    min_hum_i = min_hum
                    try:
                        with open("max_min.txt", "r") as f:
                            linha = f.readline().strip()
                            partes = linha.split(",")
                            if len(partes) == 4:
                                min_temp_i = float(partes[0])
                                max_temp_i = float(partes[1])
                                min_hum_i = float(partes[2])
                                max_hum_i = float(partes[3])
                            else:
                                print("⚠️ Formato inválido no ficheiro max_min.txt.")
                    except FileNotFoundError:
                        print("⚠️ Ficheiro 'max_min.txt' não encontrado. Usar valores padrão.")
                    except Exception as e:
                        print(f"❌ Erro a ler limites de ficheiro: {e}")

                    response = f"{max_temp_i:.2f};{min_temp_i:.2f};{max_hum_i:.2f};{min_hum_i:.2f}"
                    client_sock.sendall(response.encode())

            except ValueError:
                print("❌ Dados mal formatados.")
                continue

    except Exception as e:
        print(f"❌ Erro com cliente {addr}: {e}")
    finally:
        client_sock.close()
        print(f"🔌 Ligação com {addr} terminada.")

def main():
    HOST = '192.168.242.147'
    PORT = 12346

    init_db()

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    print(f"🚀 Servidor à escuta em {HOST}:{PORT}")

    while True:
        client_sock, addr = server_socket.accept()
        threading.Thread(target=handle_client, args=(client_sock, addr), daemon=True).start()

if __name__ == "__main__":
    main()
