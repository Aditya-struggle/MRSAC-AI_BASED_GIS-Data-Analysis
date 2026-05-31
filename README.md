# MRSAC Automated Satellite Imagery & GeoTIFF Extractor

An advanced geospatial application developed during my technical internship at the **Maharashtra Remote Sensing Applications Centre (MRSAC), Nagpur**. This portal automates the workflow of locating specific administrative regions in Maharashtra, allowing users to draw custom boundaries and download geo-referenced satellite imagery (.tif) ready for advanced GIS software like QGIS.

---

## 🧭 How It Works (The Logic)
1. **Administrative Filtering:** Users select a specific **District** and **Taluka** through a dynamic cascading dropdown menu.
2. **Automated Geolocation:** The backend queries open spatial APIs to instantly locate the geographic coordinates (Latitude/Longitude) of the selected region and auto-centers the interactive map.
3. **Custom AOI (Area of Interest) Selection:** Using built-in vector drawing tools (Leaflet Draw), users can draw custom Rectangles or Polygons over the satellite layer to isolate their exact area of interest.
4. **Satellite Tile Stitching & Cropping:** The Flask server communicates with remote satellite servers, fetches high-resolution map tiles for the selected bounds, and stitches them into a single high-quality canvas before cropping it to the user's exact boundary.
5. **Spatial Metadata Embedding (GeoTIFF):** Leveraging Python's `rasterio` engine, the system embeds standard **WGS84 (EPSG:4326)** Coordinate Reference System (CRS) data and affine transformations into the image pixels. This outputs a professional `.tif` file instead of a flat graphic.
6. **QGIS/ArcGIS Ready:** The downloaded file can be directly dropped into QGIS, where it accurately aligns with global geographic grids for spatial analysis and measurement.

---

## 🛠️ Tech Stack
* **Backend:** Python, Flask (Micro-framework)
* **GIS & Data Processing:** Rasterio, Pandas, NumPy, Requests
* **Frontend Dashboard:** HTML5, CSS3, JavaScript, Leaflet.js, Leaflet Draw API
* **Dataset:** Localized Maharashtra spatial index (`data.csv`)

---

## 📂 Core Project Files
* `app.py` — Core Python server handling tile calculations, stitching, and raster geo-referencing.
* `data.csv` — Contains internal geospatial markers for Maharashtra's administrative circles.
* `index (1).html` — Interactive UI hosting the custom bounding tools and response states.
* `style.css` — Custom interface layout and mapping container aesthetics.

---

## 💻 Running the System Locally

1. **Clone the Repo:**
```bash
   git clone [https://github.com/YOUR_USERNAME/MRSAC-AI_BASED_GIS-Data-Analysis.git](https://github.com/YOUR_USERNAME/MRSAC-AI_BASED_GIS-Data-Analysis.git)
   cd MRSAC-AI_BASED_GIS-Data-Analysis