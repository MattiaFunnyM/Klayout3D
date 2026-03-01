import sys
import json
import GeometryHandle.Plot as Plot
import socket
import threading

# -----------------------------
# Helper functions
# -----------------------------
def keyboard_listener():
    global running
    print("Press 'quit' + Enter to stop the server.")
    for line in sys.stdin:
        if line.strip().lower() == "quit":
            print("Shutdown command received.")
            running = False
            break

def recv_exact(conn, n):
    data = b""
    while len(data) < n:
        chunk = conn.recv(n - len(data))
        if not chunk:
            raise ConnectionError("Connection closed before receiving full message")
        data += chunk
    return data

# -----------------------------
# Server setup
# -----------------------------
running = True
threading.Thread(target=keyboard_listener, daemon=True).start()

HOST = "127.0.0.1"
PORT = 50007

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind((HOST, PORT))
sock.listen(1)
print("Server ready")

# -----------------------------
# Main server loop
# -----------------------------
try:
    while running:
        try:
            sock.settimeout(1.0)
            conn, addr = sock.accept()

            # ---- Read 4‑byte length prefix ----
            length_bytes = recv_exact(conn, 4)
            msg_len = int.from_bytes(length_bytes, "big")

            # ---- Read the full JSON payload ----
            data = recv_exact(conn, msg_len).decode()
            conn.close()

            if not data:
                continue

            # Parse JSON
            payload = json.loads(data)
            polygons = payload.get("polygons", [])
            if not polygons:
                continue

            # Plot
            Plot.plot_data(polygons)
            print("Data plotted.")

        except socket.timeout:
            continue
        except Exception as e:
            print("Error:", e)

finally:
    sock.close()
    print("Server stopped.")


#TODO Add dynamic z position depending on bottom
#TODO Add option to Save 3d file in the plotter 
#TODO ADD example file
#TODO Add proper legend
#TODO Not closing every time
#TODO Add Requirement, Ignore and Readme files