# 捜索範囲を指定するためのmapの設定
map_start_latitude = 34.439946888534195
map_start_longtitude = 132.4169722549677
rows = 2
cols = 2
original_map_path = "original_map.html"
new_map_path = "map.html"

# システムを動かすための設定
# 使うモデルの場所
detect_model = "weight/1280_33Y20_0.3best.pt"
# 物体検出を行いたい画像の保存場所
detect_img_path = "systemtest"
# 物体検出の結果を保存する場所
detect_result_path = "detection"
# detect_img_pathの画像を分割した結果を保存する場所
split_img_path = "split"
server_ip = ""
sercer_port = 12345
# Androidに送信するファイル名
send_file_name = "shotPoint.txt"
# ドローンの高度
drone_altitude = 50
# 横、縦それぞれ何分割するか(例：width=3,height=3だと3x3の9枚)
grid_size_width = 3
grid_size_height = 3
# 物体検出後、androidに送信したいlocationのファイル
result_location_file = f"{detect_img_path}/1_location.txt"

# DJI Mavic2 Enterprise DUALのカメラスペック
sensor_width_mm = 6.287  # センサーサイズの幅（ミリメートル）
sensor_height_mm = 4.712  # センサーサイズの高さ（ミリメートル）
focal_length_mm = 4.3  # 焦点距離（ミリメートル）
fov_degrees = 85  # 視野角（度）
img_width = 4056  # 解像度：横
img_height = 3040  # 解像度：縦
