import socket
import threading
import sqlite3
from datetime import datetime

# Função para tratar cada cliente
def handle_client(client_sock, addr):
    print(f"Got connection from {addr}")

    try:
        db = sqlite3.connect("mock_database.db", check_same_thread=False)
        c = db.cursor()

        # Criar tabela se não existir
        c.execute("""
            CREATE TABLE IF NOT EXISTS temperatureinfo (
                ID TEXT,
                Temp TEXT,
                Time TEXT
            )
        """)

        while True:
            client_sock.send("Send Temp".encode())

            data = client_sock.recv(1024)
            if not data:
                print(f"Client {addr} disconnected.")
                break

            temp = data.decode().strip()
            print(f"Received from {addr}: {temp}")

            # Inserir na base de dados com timestamp atual
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute("INSERT INTO temperatureinfo (ID, Temp, Time) VALUES (?, ?, ?)", ('1', temp, current_time))
            db.commit()

    except Exception as e:
        print(f"Error handling client {addr}: {e}")

    finally:
        client_sock.close()
        db.close()
        print(f"Connection with {addr} closed.")

# Main server loop
def main():
    HOST = '192.168.242.147'  # IP do servidor
    PORT = 12346              # Porta

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    print(f"Server listening on {HOST}:{PORT}")

    while True:
        client_sock, addr = server_socket.accept()
        threading.Thread(target=handle_client, args=(client_sock, addr), daemon=True).start()

if __name__ == "__main__":
    main()

