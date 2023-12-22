from flask import Flask, request, render_template_string
import socket
import threading
import setting
from math import radians, tan

app = Flask(__name__)


# setting.pyに書いてある変数をもとに新しくmapを作る
def init_map():
    with open(setting.original_map_path, "r", encoding="utf-8") as original_file:
        content = original_file.read()

    fov_radians = radians(setting.fov_degrees)
    shooting_area_width = 2 * setting.drone_altitude * tan(fov_radians / 2)
    shooting_area_height = shooting_area_width * (
        setting.sensor_height_mm / setting.sensor_width_mm
    )
    content = (
        content.replace("34.439946888534195", str(setting.map_start_latitude))
        .replace("132.4169722549677", str(setting.map_start_longtitude))
        .replace(
            "drawGrid(e.latlng, 3, 3, 20, 30);",
            f"drawGrid(e.latlng, {setting.rows}, {setting.cols}, {int(shooting_area_height)}, {int(shooting_area_width)});",
        )
        .replace(
            "previewGrid(e.latlng, 3, 3, 20, 30);",
            f"previewGrid(e.latlng, {setting.rows}, {setting.cols}, {int(shooting_area_height)}, {int(shooting_area_width)});",
        )
    )

    with open(setting.new_map_path, "w", encoding="utf-8") as new_file:
        new_file.write(content)


def send_file():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((setting.server_ip, setting.sercer_port))  # 任意のポート
    server_socket.listen(1)

    client_socket, address = server_socket.accept()
    print(f"Connection from {address} has been established.")

    with open(setting.send_file_name, "rb") as file:
        data = file.read(4096)
        while data:
            client_socket.send(data)
            data = file.read(4096)
    print("File sent")

    client_socket.close()
    server_socket.close()


@app.route("/")
def index():
    init_map()
    with open(setting.new_map_path, encoding="utf-8") as file:
        html_content = file.read()
    return render_template_string(html_content)


@app.route("/post_coordinates_list", methods=["POST"])
def post_coordinates():
    data = request.json
    with open(setting.send_file_name, "w", encoding="utf-8") as file:
        for coordinate in data:
            lat = coordinate["lat"]
            lng = coordinate["lng"]
            print(f"{lat} {lng}")
            file.write(f"{lat} {lng}\n")
    threading.Thread(target=send_file).start()

    return "Coordinates received!"


if __name__ == "__main__":
    app.run(debug=True)
