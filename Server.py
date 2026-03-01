import sys
import json
import socket
import threading
import GeometryHandle.Plot as Plot

# -----------------------------
# Helper functions
# -----------------------------
def keyboard_listener():
    """
    Listen for keyboard input in a separate thread.
    Allows the user to stop the server by typing 'quit'.
    """
    global running
    print("Press 'quit' + Enter to stop the server.")
    for line in sys.stdin:
        if line.strip().lower() == "quit":
            print("Shutdown command received.")
            running = False
            break


def recv_exact(conn, n):
    """
    Receive exactly n bytes from a socket connection.

    Parameters:
        conn (socket): The socket connection to read from.
        n (int): The exact number of bytes to read.

    Returns:
        data (bytes): The received bytes.

    Raises:
        ConnectionError: If the connection is closed before n bytes are received.
    """
    data = b""
    while len(data) < n:
        chunk = conn.recv(n - len(data))
        if not chunk:
            raise ConnectionError("Connection closed before receiving full message")
        data += chunk
    return data


def handle_plot(polygons):
    """
    Run plot_data in a dedicated thread so the server loop stays alive
    while the 3D window is open. Using a thread also prevents the Qt
    window from blocking the server from accepting new connections.

    Parameters:
        polygons (list): A list of polygon data structures to plot.
    """
    Plot.plot_data(polygons)


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

            # Read 4-byte length prefix
            length_bytes = recv_exact(conn, 4)
            msg_len = int.from_bytes(length_bytes, "big")

            # Read the full JSON payload
            data = recv_exact(conn, msg_len).decode()
            conn.close()

            if not data:
                continue

            # Parse JSON
            payload = json.loads(data)
            polygons = payload.get("polygons", [])
            if not polygons:
                continue

            # Ensure all polygons are closed by repeating the first point at the end if needed
            for polygon in polygons:
                points = polygon["points"]
                if points[0] != points[-1]:
                    polygon["points"].append(points[0])

            # Launch the plot in a separate thread so the server keeps running while the 3D window is open
            plot_thread = threading.Thread(
                target=handle_plot,
                args=(polygons,),
                daemon=True
            )
            plot_thread.start()
            print("Data plotted.")

        except socket.timeout:
            continue
        except Exception as e:
            print("Error:", e)

finally:
    sock.close()
    print("Server stopped.")


# TODO: Add proper legend
# TODO: Add Requirements, .gitignore and README files