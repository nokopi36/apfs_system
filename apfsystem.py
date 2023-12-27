from ultralytics import YOLO
import torch
import os
import setting
import pyproj
from math import atan2, degrees, sqrt, radians, tan
import re
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import datetime
import time


def main():
    start_time = time.perf_counter()
    now = datetime.datetime.now()
    current_time = now.strftime("%Y-%m-%d-%H-%M")
    remove_non_matching_image(setting.detect_img_path)
    rename_files(setting.detect_img_path, 1)
    get_and_save_all_images_exif(setting.detect_img_path)
    split_result_dir = os.path.join(setting.split_img_path, current_time)
    split_all_images(setting.detect_img_path, split_result_dir)

    model = YOLO(model=setting.detect_model)
    object_detection(model, split_result_dir, setting.detect_result_path, current_time)
    detection_resulr_dir = os.path.join(setting.detect_result_path, current_time)
    combine_images_and_txt(detection_resulr_dir, setting.detect_img_path)
    detected_object_location(setting.detect_img_path)
    end_time = time.perf_counter()
    diff_time = end_time - start_time
    print(f"実行時間: {diff_time}")


# 指定した解像度の画像でなければ削除する
def remove_non_matching_image(
    directory,
    target_resolution=(setting.img_width, setting.img_height),
):
    for filename in os.listdir(directory):
        if filename.lower().endswith((".png", ".jpg", ".jpeg")):
            image_path = os.path.join(directory, filename)
            with Image.open(image_path) as img:  # 画像の解像度をチェック
                if img.size != target_resolution:
                    img.close()  # 解像度が一致しない場合、画像を削除
                    os.remove(image_path)
                    print(f"Deleted {filename}")


# フォルダ内のすべてのファイルの名前を1からの連番に変更
def rename_files(directory, start_number):
    # フォルダ内のすべてのファイルを取得
    files = os.listdir(directory)
    # PNGとTXTファイルのみをフィルタリング
    jpg_files = sorted([f for f in files if f.endswith(".jpg")])

    # ファイルをリネーム
    new_number = start_number
    for jpg in jpg_files:
        # 新しいファイル名を生成
        new_jpg_name = f"{new_number}.jpg"

        # ファイル名を変更
        os.rename(os.path.join(directory, jpg), os.path.join(directory, new_jpg_name))

        new_number += 1


# 度分秒から10進数表記の緯度経度に変換
def get_decimal_from_dms(dms, ref):
    degrees = dms[0]
    minutes = dms[1] / 60.0
    seconds = dms[2] / 3600.0

    if ref in ["S", "W"]:
        degrees = -degrees
        minutes = -minutes
        seconds = -seconds

    return degrees + minutes + seconds


def get_and_save_all_images_exif(folder):
    for filename in os.listdir(folder):
        if filename.lower().endswith((".png", ".jpg", ".jpeg")):
            full_path = os.path.join(folder, filename)
            try:
                image = Image.open(full_path)
                image.verify()
                exif = image._getexif()

                if not exif:
                    print(f"No EXIF metadata found for {filename}")
                    continue

                geotags = {}
                for idx, tag in TAGS.items():
                    if tag == "GPSInfo":
                        if idx not in exif:
                            print(f"No EXIF geotagging found for {filename}")
                            continue

                        for key, val in GPSTAGS.items():
                            if key in exif[idx]:
                                geotags[val] = exif[idx][key]

                lat = get_decimal_from_dms(
                    geotags["GPSLatitude"], geotags["GPSLatitudeRef"]
                )
                lon = get_decimal_from_dms(
                    geotags["GPSLongitude"], geotags["GPSLongitudeRef"]
                )
                formatted_lat = "{:.6f}".format(lat)
                formatted_lon = "{:.6f}".format(lon)

                txt_filename = os.path.splitext(full_path)[0] + ".txt"
                with open(txt_filename, "w") as f:
                    f.write(f"{formatted_lat} {formatted_lon}\n")
            except Exception as e:
                print(f"Error processing {filename}: {e}")


# 画像を任意の数に分割
def split_all_images(
    directory,
    output_dir,
    target_resolution=(setting.img_width, setting.img_height),
    grid_size=(setting.grid_size_width, setting.grid_size_height),
):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for file_name in os.listdir(directory):
        if file_name.lower().endswith((".png", ".jpg", ".jpeg")):
            image_path = os.path.join(directory, file_name)
            with Image.open(image_path) as img:
                # 画像の解像度をチェック
                if img.size == target_resolution:
                    img_width, img_height = img.size
                    tile_width = img_width // grid_size[0]
                    tile_height = img_height // grid_size[1]

                    for i in range(grid_size[0]):  # 横の分割数
                        for j in range(grid_size[1]):  # 縦の分割数
                            left = i * tile_width
                            upper = j * tile_height
                            right = left + tile_width
                            lower = upper + tile_height
                            cropped_img = img.crop((left, upper, right, lower))

                            base_name = os.path.basename(image_path)
                            file_name, file_ext = os.path.splitext(base_name)
                            cropped_img.save(
                                os.path.join(
                                    output_dir,
                                    f"{file_name}_{i * grid_size[1] + j + 1}{file_ext}",
                                )
                            )


def object_detection(model, resource, project, name):
    # 画像ファイルのリストを取得
    images = os.listdir(resource)

    for image in images:
        image_path = os.path.join(resource, image)

        # 物体検出を実行
        results = model.predict(
            image_path,
            save=True,
            project=project,
            name=name,
            exist_ok=True,
        )

        for result in results:
            boxes = result.boxes.xyxy.to("cpu").numpy()
            output_boxes = boxes.astype(int).tolist()

            # 中心座標を計算
            centers = []
            for bbox in output_boxes:
                x_center = (bbox[0] + bbox[2]) // 2
                y_center = (bbox[1] + bbox[3]) // 2
                centers.append([x_center, y_center])

            # 画像の名前から拡張子を除いてファイル名を生成
            file_name_without_ext = os.path.splitext(image)[0]
            file_path = os.path.join(
                f"{project}/{name}", f"{file_name_without_ext}.txt"
            )

            # 中心座標をファイルに書き込む
            with open(file_path, "w") as file:
                for center in centers:
                    file.write(f"{center[0]} {center[1]}\n")


def combine_images_and_txt(
    input_dir,
    output_dir,
    original_size=(setting.img_width, setting.img_height),
    grid_size=(setting.grid_size_width, setting.grid_size_height),
):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 正規表現パターンを定義（'数字_数字.jpg'の形式）
    pattern = re.compile(r"\d+_\d+\.jpg")

    for file in os.listdir(input_dir):
        if pattern.match(file):
            base_name = file.split("_")[0]

            # 新しい画像を作成
            new_image = Image.new("RGB", original_size)
            tile_width = original_size[0] // grid_size[0]
            tile_height = original_size[1] // grid_size[1]

            # 合成した物体の位置を記録するためのリスト
            combined_objects = []

            # 画像とテキストファイルの組み合わせを処理
            for i in range(grid_size[0] * grid_size[1]):
                img_path = os.path.join(input_dir, f"{base_name}_{i + 1}.jpg")
                txt_path = os.path.join(input_dir, f"{base_name}_{i + 1}.txt")

                if os.path.exists(img_path):
                    with Image.open(img_path) as tile:
                        x = (i // grid_size[1]) * tile_width  # 列のインデックスに基づくX座標
                        y = (i % grid_size[1]) * tile_height  # 行のインデックスに基づくY座標
                        new_image.paste(tile, (x, y))
                        # テキストファイルがあれば、物体の位置を読み取る
                        if os.path.exists(txt_path):
                            with open(txt_path, "r") as f:
                                for line in f:
                                    obj_x, obj_y = map(int, line.split())
                                    combined_objects.append((obj_x + x, obj_y + y))

            # 画像を保存
            new_image.save(os.path.join(output_dir, f"{base_name}_combine.jpg"))

            # 物体の位置を含むテキストファイルを保存
            if combined_objects:
                with open(
                    os.path.join(output_dir, f"{base_name}_combine.txt"), "w"
                ) as f:
                    for obj_x, obj_y in combined_objects:
                        f.write(f"{obj_x} {obj_y}\n")


def detected_object_location(directory):
    for file_name in os.listdir(directory):
        if file_name.endswith(".txt") and not file_name.endswith("_combine.txt"):
            base_name = file_name.split(".")[0]

            # 緯度経度ファイルの読み込み
            with open(os.path.join(directory, file_name), "r") as file:
                center_latitude, center_longitude = map(float, file.readline().split())

            # 対応する物体位置ファイルの存在確認
            combine_file_name = f"{base_name}_combine.txt"
            if combine_file_name in os.listdir(directory):
                with open(os.path.join(directory, combine_file_name), "r") as file:
                    # 新しい緯度経度をファイルに保存
                    location_file_name = os.path.join(
                        directory, f"{base_name}_location.txt"
                    )
                    with open(location_file_name, "w") as location_file:
                        for line in file:
                            object_x_px, object_y_px = map(int, line.split())
                            new_latitude, new_longitude = calculate_location(
                                center_latitude,
                                center_longitude,
                                object_x_px,
                                object_y_px,
                            )
                            location_file.write(f"{new_latitude} {new_longitude}\n")


def calculate_location(center_latitude, center_longitude, object_x_px, object_y_px):
    fov_radians = radians(setting.fov_degrees)
    shooting_area_width = 2 * setting.drone_altitude * tan(fov_radians / 2)
    shooting_area_height = shooting_area_width * (
        setting.sensor_height_mm / setting.sensor_width_mm
    )
    meter_per_pixel_x = shooting_area_width / setting.img_width
    meter_per_pixel_y = shooting_area_height / setting.img_height

    # 物体の中心からのオフセットを計算（メートル単位）
    offset_x_m = (object_x_px - setting.img_width / 2) * meter_per_pixel_x
    offset_y_m = (setting.img_height / 2 - object_y_px) * meter_per_pixel_y

    # 方位角を計算（度単位）
    bearing = degrees(atan2(offset_y_m, offset_x_m))

    # 距離を計算（メートル単位）
    distance = sqrt(offset_x_m**2 + offset_y_m**2)

    # Geodオブジェクトを作成（WGS84楕円体を使用）
    geod = pyproj.Geod(ellps="WGS84")

    # 新しい緯度経度を計算
    new_longitude, new_latitude, _ = geod.fwd(
        center_longitude, center_latitude, bearing, distance
    )

    return new_latitude, new_longitude


if __name__ == "__main__":
    main()
