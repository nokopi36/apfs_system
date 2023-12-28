import socket
import setting

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(("", 12345))  # 任意のポート
server_socket.listen(1)

client_socket, address = server_socket.accept()
print(f"Connection from {address} has been established.")

with open(setting.result_location_file, "rb") as file:
    data = file.read(4096)
    while data:
        client_socket.send(data)
        data = file.read(4096)
print("File sent")

client_socket.close()
server_socket.close()
