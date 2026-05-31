from flask import Flask, render_template, request, jsonify, send_file
from datetime import datetime
import pandas as pd
import numpy as np
import requests
import io
import math
from PIL import Image
import rasterio
from rasterio.transform import from_bounds
from rasterio.crs import CRS

app = Flask(__name__)

# Read CSV
df = pd.read_csv("data.csv")

# Districts
districts = df['district'].unique()


# ─── Helper: Convert tile coords to lat/lng ───────────────────────────────────
def tile_to_latlon(x, y, z):
    n = 2 ** z
    lon = x / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * y / n)))
    lat = math.degrees(lat_rad)
    return lat, lon


# ─── Helper: Convert lat/lng to tile coords ───────────────────────────────────
def latlon_to_tile(lat, lon, z):
    n = 2 ** z
    x = int((lon + 180.0) / 360.0 * n)
    lat_rad = math.radians(lat)
    y = int((1.0 - math.log(math.tan(lat_rad) + 1.0 / math.cos(lat_rad)) / math.pi) / 2.0 * n)
    return x, y


# ─── Helper: Fetch satellite tiles and stitch ─────────────────────────────────
def fetch_satellite_image(north, south, east, west, zoom=14):
    # Get tile range
    x_min, y_min = latlon_to_tile(north, west, zoom)
    x_max, y_max = latlon_to_tile(south, east, zoom)

    tile_size = 256
    cols = x_max - x_min + 1
    rows = y_max - y_min + 1

    # Stitch tiles into one image
    full_image = Image.new('RGB', (cols * tile_size, rows * tile_size))

    headers = {'User-Agent': 'MRSAC-Dashboard/1.0'}

    for tx in range(x_min, x_max + 1):
        for ty in range(y_min, y_max + 1):
            url = f"https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{zoom}/{ty}/{tx}"
            try:
                resp = requests.get(url, headers=headers, timeout=10)
                tile_img = Image.open(io.BytesIO(resp.content)).convert('RGB')
                px = (tx - x_min) * tile_size
                py = (ty - y_min) * tile_size
                full_image.paste(tile_img, (px, py))
            except Exception as e:
                print(f"Tile fetch error: {e}")

    # Exact bounds of the stitched tile grid
    nw_lat, nw_lon = tile_to_latlon(x_min, y_min, zoom)
    se_lat, se_lon = tile_to_latlon(x_max + 1, y_max + 1, zoom)

    return full_image, nw_lat, nw_lon, se_lat, se_lon


# ─── Dynamic Taluka Route ─────────────────────────────────────────────────────
@app.route('/get_talukas/<district>')
def get_talukas(district):
    talukas = df[df['district'] == district]['taluka'].unique()
    return jsonify(list(talukas))


# ─── GeoTIFF Download Route ───────────────────────────────────────────────────
@app.route('/download_geotiff', methods=['POST'])
def download_geotiff():
    data = request.get_json()

    north = float(data['north'])
    south = float(data['south'])
    east  = float(data['east'])
    west  = float(data['west'])
    taluka   = data.get('taluka', 'area')
    district = data.get('district', 'maharashtra')
    zoom  = int(data.get('zoom', 14))

    # Clamp zoom for reasonable tile count
    zoom = min(zoom, 16)

    # Fetch and stitch satellite tiles
    image, nw_lat, nw_lon, se_lat, se_lon = fetch_satellite_image(north, south, east, west, zoom)

    # Crop image to exact user-drawn bounds
    img_w, img_h = image.size
    tile_extent_lon = se_lon - nw_lon
    tile_extent_lat = nw_lat - se_lat

    crop_left   = int((west  - nw_lon) / tile_extent_lon * img_w)
    crop_right  = int((east  - nw_lon) / tile_extent_lon * img_w)
    crop_top    = int((nw_lat - north) / tile_extent_lat * img_h)
    crop_bottom = int((nw_lat - south) / tile_extent_lat * img_h)

    crop_left   = max(0, crop_left)
    crop_top    = max(0, crop_top)
    crop_right  = min(img_w, crop_right)
    crop_bottom = min(img_h, crop_bottom)

    cropped = image.crop((crop_left, crop_top, crop_right, crop_bottom))

    # Convert to numpy array (bands)
    img_array = np.array(cropped)
    r = img_array[:, :, 0]
    g = img_array[:, :, 1]
    b = img_array[:, :, 2]

    height, width = r.shape

    # GeoTIFF transform — maps pixel to geographic coordinates
    transform = from_bounds(west, south, east, north, width, height)

    # Write GeoTIFF to memory buffer
    buffer = io.BytesIO()
    with rasterio.open(
        buffer,
        'w',
        driver='GTiff',
        height=height,
        width=width,
        count=3,        # RGB
        dtype=np.uint8,
        crs=CRS.from_epsg(4326),   # WGS84 — standard GPS coordinates
        transform=transform
    ) as dst:
        dst.write(r, 1)
        dst.write(g, 2)
        dst.write(b, 3)

    buffer.seek(0)

    filename = f"{taluka}_{district}_satellite.tif"

    return send_file(
        buffer,
        mimetype='image/tiff',
        as_attachment=True,
        download_name=filename
    )


# ─── Main Route ───────────────────────────────────────────────────────────────
@app.route('/', methods=['GET', 'POST'])
def home():

    if request.method == 'POST':

        district = request.form['district']
        taluka   = request.form['taluka']

        row = df[
            (df['district'] == district) &
            (df['taluka'] == taluka)
        ]

        if not row.empty:
            total_circles = row.iloc[0]['circles']
            total_villages = row.iloc[0]['villages']
            map_link = row.iloc[0]['map']
        else:
            total_circles = 0
            total_villages = 0
            map_link = ""

        current_date = datetime.now().strftime('%d-%m-%Y %H:%M:%S')

        return render_template(
            'index.html',
            show_table=True,
            district=district,
            taluka=taluka,
            circles=total_circles,
            villages=total_villages,
            date=current_date,
            districts=districts,
            map_link=map_link
        )

    return render_template(
        'index.html',
        show_table=False,
        districts=districts
    )


if __name__ == '__main__':
    app.run(debug=True)
