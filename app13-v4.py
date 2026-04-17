from flask import Flask, render_template_string, request, jsonify, redirect, url_for, send_file
import math
import sqlite3
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

def init_db():
    with sqlite3.connect('locations.db') as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL
            )
        ''')
        c.execute('SELECT COUNT(*) FROM locations')
        if c.fetchone()[0] == 0:
            c.execute('INSERT INTO locations (name, latitude, longitude) VALUES (?, ?, ?)',
                      ('Default Location', 0, 0))
        conn.commit()

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>GPS Distance Tracker</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
    * { margin: 0; padding: 0; box-sizing: border-box; }

    body {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        background: #f0ece4;
        min-height: 100vh;
        padding: 20px;
        color: #2c2c2c;
    }

    .container { max-width: 1200px; margin: 0 auto; }

    header {
        text-align: center;
        margin-bottom: 30px;
        padding: 24px 0 10px;
    }

    h1 {
        color: #2c2c2c;
        font-size: 2em;
        font-weight: 700;
        margin-bottom: 6px;
        letter-spacing: 0.5px;
    }

    .subtitle {
        color: #7a6e5f;
        font-size: 0.95em;
    }

    .main-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 20px;
        margin-bottom: 20px;
    }

    @media (max-width: 768px) {
        .main-grid { grid-template-columns: 1fr; }
    }

    .card {
        background: #fff;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.07);
        border: 1px solid #e0d9cf;
    }

    /* === COMPASS === */
    .compass-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-height: 400px;
    }

    .location-selector { width: 100%; margin-bottom: 16px; }

    .search-box {
        width: 100%;
        padding: 10px 16px;
        border: 1.5px solid #d4cdc3;
        border-radius: 8px;
        font-size: 0.95em;
        background: #faf8f5;
        transition: all 0.2s;
        margin-bottom: 10px;
        color: #2c2c2c;
    }

    .search-box:focus {
        outline: none;
        border-color: #7a6e5f;
        background: #fff;
    }

    select {
        width: 100%;
        padding: 10px 16px;
        border: 1.5px solid #d4cdc3;
        border-radius: 8px;
        font-size: 0.95em;
        background: #faf8f5;
        cursor: pointer;
        color: #2c2c2c;
        transition: all 0.2s;
    }

    select:focus {
        outline: none;
        border-color: #7a6e5f;
    }

    .kompas-wrapper {
        image-rendering: pixelated;
        image-rendering: crisp-edges;
        width: 240px;
        height: 240px;
        overflow: hidden;
        border: 3px solid #5a4e3f;
        border-radius: 6px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.2);
        margin: 16px 0;
    }

    #mcCompass {
        width: 240px;
        height: 7680px;
        background-image: url('/kompas.png');
        background-size: 240px 7680px;
        background-repeat: no-repeat;
        background-position: 0px 0px;
    }

    .distance-display { text-align: center; margin-top: 10px; }

    .distance-value {
        font-size: 2.6em;
        font-weight: 700;
        color: #3d3228;
        margin-bottom: 4px;
        letter-spacing: 1px;
    }

    .distance-label {
        font-size: 0.9em;
        color: #9a8e7f;
        font-weight: 500;
    }

    .bearing-info {
        display: flex;
        justify-content: space-around;
        margin-top: 16px;
        padding-top: 16px;
        border-top: 1.5px solid #ede8e0;
        width: 100%;
    }

    .bearing-item { text-align: center; }

    .bearing-item-label {
        font-size: 0.8em;
        color: #9a8e7f;
        margin-bottom: 4px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .bearing-item-value {
        font-size: 1.3em;
        font-weight: 600;
        color: #3d3228;
    }

    /* === SECTION === */
    .section-title {
        font-size: 1.1em;
        font-weight: 700;
        margin-bottom: 16px;
        color: #3d3228;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .form-group { margin-bottom: 12px; }

    input[type="text"],
    input[type="number"] {
        width: 100%;
        padding: 10px 16px;
        border: 1.5px solid #d4cdc3;
        border-radius: 8px;
        font-size: 0.95em;
        background: #faf8f5;
        color: #2c2c2c;
        transition: all 0.2s;
    }

    input[type="text"]:focus,
    input[type="number"]:focus {
        outline: none;
        border-color: #7a6e5f;
        background: #fff;
    }

    .button-group {
        display: flex;
        gap: 8px;
        margin-top: 12px;
    }

    /* === BUTTONS === */
    button {
        flex: 1;
        padding: 8px 14px;
        border: none;
        border-radius: 7px;
        font-size: 0.85em;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s;
        letter-spacing: 0.2px;
    }

    .btn-primary {
        background: #4a3f35;
        color: #fff;
    }
    .btn-primary:hover {
        background: #3a3028;
        box-shadow: 0 2px 8px rgba(74,63,53,0.3);
    }

    .btn-secondary {
        background: #ede8e0;
        color: #4a3f35;
        border: 1px solid #d4cdc3;
    }
    .btn-secondary:hover { background: #e0d9cf; }

    .btn-danger {
        background: #c0392b;
        color: #fff;
    }
    .btn-danger:hover { background: #a93226; }

    .btn-success {
        background: #2e7d52;
        color: #fff;
    }
    .btn-success:hover { background: #256342; }

    .btn-maps {
        background: #2c5f8a;
        color: #fff;
    }
    .btn-maps:hover {
        background: #1e4d73;
        box-shadow: 0 2px 8px rgba(44,95,138,0.3);
    }

    .btn-reveal {
        background: #f0ece4;
        color: #4a3f35;
        border: 1.5px solid #c4bdb3;
        width: 100%;
        margin-top: 10px;
        padding: 7px 14px;
        font-size: 0.82em;
    }
    .btn-reveal:hover { background: #e5dfd6; }

    /* === LOCATION CARDS === */
    .locations-grid {
        display: grid;
        gap: 12px;
        margin-top: 16px;
    }

    .location-card {
        background: #faf8f5;
        border-radius: 10px;
        padding: 16px;
        border: 1.5px solid #e0d9cf;
        transition: all 0.2s;
    }

    .location-card:hover {
        border-color: #7a6e5f;
        box-shadow: 0 2px 10px rgba(0,0,0,0.07);
    }

    .location-card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
        padding-bottom: 12px;
        border-bottom: 1.5px solid #e0d9cf;
    }

    .location-name {
        font-size: 1.1em;
        font-weight: 700;
        color: #2c2c2c;
    }

    .location-index {
        background: #4a3f35;
        color: #fff;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.8em;
        font-weight: 600;
    }

    .location-coords {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 8px;
        margin-bottom: 12px;
    }

    .coord-item {
        background: #fff;
        padding: 8px 10px;
        border-radius: 7px;
        border: 1px solid #ede8e0;
    }

    .coord-label {
        font-size: 0.75em;
        color: #9a8e7f;
        margin-bottom: 3px;
        text-transform: uppercase;
        letter-spacing: 0.3px;
    }

    .coord-value {
        font-size: 0.9em;
        font-weight: 600;
        color: #2c2c2c;
        font-family: 'Courier New', monospace;
        filter: blur(5px);
        user-select: none;
        transition: filter 0.3s;
    }

    .coord-value.revealed { filter: blur(0px); user-select: text; }

    .location-actions {
        display: flex;
        gap: 8px;
    }

    .location-actions button {
        flex: 1;
        padding: 7px 10px;
        font-size: 0.82em;
    }

    /* === EDIT MODE === */
    .location-card.edit-mode {
        background: #fff;
        border-color: #7a6e5f;
    }

    .edit-form { display: none; }
    .edit-mode .edit-form { display: block; }
    .edit-mode .view-content { display: none; }

    .edit-input-group { margin-bottom: 10px; }

    .edit-input-group label {
        display: block;
        font-size: 0.82em;
        color: #7a6e5f;
        margin-bottom: 4px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.3px;
    }

    .edit-input-group input {
        width: 100%;
        padding: 8px 12px;
        border: 1.5px solid #d4cdc3;
        border-radius: 7px;
        font-size: 0.9em;
        background: #faf8f5;
    }

    /* === DESKTOP TABLE === */
    table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        margin-top: 16px;
        display: none;
    }

    @media (min-width: 1024px) {
        table { display: table; }
        .locations-grid { display: none; }

        th {
            background: #f5f0e8;
            padding: 12px 14px;
            text-align: left;
            font-weight: 600;
            font-size: 0.8em;
            color: #7a6e5f;
            border-bottom: 1.5px solid #e0d9cf;
            text-transform: uppercase;
            letter-spacing: 0.4px;
        }

        th:first-child { border-top-left-radius: 8px; }
        th:last-child  { border-top-right-radius: 8px; }

        td {
            padding: 12px 14px;
            border-bottom: 1px solid #f0ece4;
            font-size: 0.9em;
        }

        tr:last-child td:first-child { border-bottom-left-radius: 8px; }
        tr:last-child td:last-child  { border-bottom-right-radius: 8px; }
        tr:hover { background: #faf8f5; }

        .table-coord {
            font-family: 'Courier New', monospace;
            font-size: 0.85em;
            filter: blur(5px);
            user-select: none;
            transition: filter 0.3s;
            display: inline-block;
        }
        .table-coord.revealed { filter: blur(0px); user-select: text; }

        .table-input {
            padding: 7px 10px;
            border: 1px solid #d4cdc3;
            border-radius: 6px;
            font-size: 0.85em;
            width: 100%;
            background: #faf8f5;
        }

        .table-button {
            padding: 6px 12px;
            font-size: 0.82em;
            margin-right: 4px;
        }
    }

    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50%       { opacity: 0.4; }
    }
    .loading { animation: pulse 1.5s ease-in-out infinite; }
</style>
</head>
<body>
<div class="container">
    <header>
        <h1>🧭 GPS Distance Tracker</h1>
        <p class="subtitle">Track your distance and direction in real-time</p>
    </header>

    <div class="main-grid">
        <!-- Compass -->
        <div class="card">
            <div class="compass-container">
                <div class="location-selector">
                    <input type="text" id="searchInput" class="search-box" placeholder="🔍 Search location..." onkeyup="filterLocations()" />
                    <select id="locationSelect" onchange="updateLocation()">
                        {% for loc in locations %}
                        <option value="{{ loc[0] }}">{{ loc[1] }}</option>
                        {% endfor %}
                    </select>
                </div>

                <div class="kompas-wrapper">
                    <div id="mcCompass"></div>
                </div>

                <div class="distance-display">
                    <div id="distanceValue" class="distance-value loading">---</div>
                    <div class="distance-label">meters away</div>
                </div>

                <div class="bearing-info">
                    <div class="bearing-item">
                        <div class="bearing-item-label">Bearing</div>
                        <div id="bearingValue" class="bearing-item-value">---°</div>
                    </div>
                    <div class="bearing-item">
                        <div class="bearing-item-label">Direction</div>
                        <div id="directionValue" class="bearing-item-value">---</div>
                    </div>
                </div>

                <div style="margin-top: 16px; width: 100%;">
                    <button class="btn-maps" style="width: 100%;" onclick="openGoogleMapsFromCompass()">
                        🗺️ Buka di Google Maps
                    </button>
                </div>
            </div>
        </div>

        <!-- Add Location -->
        <div class="card">
            <h2 class="section-title">➕ Tambah Lokasi</h2>
            <form action="/add_location" method="POST">
                <div class="form-group">
                    <input type="text" name="name" placeholder="Nama Lokasi" required>
                </div>
                <div class="form-group">
                    <input type="number" step="any" name="latitude" placeholder="Latitude" required>
                </div>
                <div class="form-group">
                    <input type="number" step="any" name="longitude" placeholder="Longitude" required>
                </div>
                <div class="button-group">
                    <button type="submit" class="btn-primary">Tambah Manual</button>
                    <button type="button" class="btn-success" onclick="getLocationAndAdd()">📍 Lokasi Saat Ini</button>
                </div>
            </form>
        </div>
    </div>

    <!-- Manage Locations -->
    <div class="card">
        <h2 class="section-title">📍 Kelola Lokasi</h2>

        <!-- Mobile -->
        <div class="locations-grid" id="locationsGrid">
            {% for loc in locations %}
            <div class="location-card" id="card-{{ loc[0] }}">
                <div class="view-content">
                    <div class="location-card-header">
                        <div class="location-name">{{ loc[1] }}</div>
                        <div class="location-index">#{{ loop.index }}</div>
                    </div>
                    <div class="location-coords">
                        <div class="coord-item">
                            <div class="coord-label">Latitude</div>
                            <div class="coord-value" id="lat-{{ loc[0] }}">{{ "%.6f"|format(loc[2]) }}</div>
                        </div>
                        <div class="coord-item">
                            <div class="coord-label">Longitude</div>
                            <div class="coord-value" id="lon-{{ loc[0] }}">{{ "%.6f"|format(loc[3]) }}</div>
                        </div>
                    </div>
                    <button class="btn-reveal" onclick="toggleReveal({{ loc[0] }})" id="revealBtn-{{ loc[0] }}">
                        👁️ Perlihatkan Koordinat
                    </button>
                    <div class="location-actions" style="margin-top: 10px;">
                        <button class="btn-primary" onclick="toggleEdit({{ loc[0] }})">✏️ Edit</button>
                        <button class="btn-maps" onclick="openGoogleMaps({{ loc[2] }}, {{ loc[3] }})">🗺️ Maps</button>
                        <form action="/delete_location/{{ loc[0] }}" method="POST" style="flex: 1;">
                            <button type="submit" class="btn-danger" style="width:100%;" onclick="return confirm('Hapus {{ loc[1] }}?')">🗑️ Hapus</button>
                        </form>
                    </div>
                </div>

                <form action="/edit_location/{{ loc[0] }}" method="POST" class="edit-form">
                    <div class="edit-input-group">
                        <label>Nama Lokasi</label>
                        <input type="text" name="name" value="{{ loc[1] }}" required>
                    </div>
                    <div class="edit-input-group">
                        <label>Latitude</label>
                        <input type="number" step="any" name="latitude" value="{{ loc[2] }}" required>
                    </div>
                    <div class="edit-input-group">
                        <label>Longitude</label>
                        <input type="number" step="any" name="longitude" value="{{ loc[3] }}" required>
                    </div>
                    <div class="location-actions">
                        <button type="submit" class="btn-success">💾 Simpan</button>
                        <button type="button" class="btn-secondary" onclick="toggleEdit({{ loc[0] }})">✖️ Batal</button>
                    </div>
                </form>
            </div>
            {% endfor %}
        </div>

        <!-- Desktop Table -->
        <table id="locationsTable">
            <thead>
                <tr>
                    <th>#</th>
                    <th>Nama</th>
                    <th>Latitude</th>
                    <th>Longitude</th>
                    <th>Aksi</th>
                </tr>
            </thead>
            <tbody>
            {% for loc in locations %}
            <tr>
                <td>{{ loop.index }}</td>
                <td><strong>{{ loc[1] }}</strong></td>
                <td><span class="table-coord" id="tlat-{{ loc[0] }}">{{ "%.6f"|format(loc[2]) }}</span></td>
                <td><span class="table-coord" id="tlon-{{ loc[0] }}">{{ "%.6f"|format(loc[3]) }}</span></td>
                <td>
                    <button class="btn-secondary table-button" onclick="toggleTableReveal({{ loc[0] }})" id="treveal-{{ loc[0] }}">👁️</button>
                    <form action="/edit_location/{{ loc[0] }}" method="POST" style="display:inline;">
                        <input type="text" name="name" value="{{ loc[1] }}" class="table-input" required>
                        <input type="number" step="any" name="latitude" value="{{ loc[2] }}" class="table-input" required>
                        <input type="number" step="any" name="longitude" value="{{ loc[3] }}" class="table-input" required>
                        <button type="submit" class="btn-primary table-button">Simpan</button>
                    </form>
                    <button class="btn-maps table-button" onclick="openGoogleMaps({{ loc[2] }}, {{ loc[3] }})">🗺️ Maps</button>
                    <form action="/delete_location/{{ loc[0] }}" method="POST" style="display:inline;">
                        <button type="submit" class="btn-danger table-button" onclick="return confirm('Hapus lokasi ini?')">Hapus</button>
                    </form>
                </td>
            </tr>
            {% endfor %}
            </tbody>
        </table>
    </div>
</div>

<script>
// ── Minecraft Compass ────────────────────────────────────────
const TOTAL_FRAMES = 32;
const FRAME_H      = 240;

function bearingToFrame(bearing) {
    const adjusted = (540 - bearing) % 360;
    return Math.round((adjusted / 360) * TOTAL_FRAMES) % TOTAL_FRAMES;
}

function setCompassFrame(frame) {
    const offsetY = -((TOTAL_FRAMES - 1 - frame) * FRAME_H);
    document.getElementById('mcCompass').style.backgroundPosition = `0px ${offsetY}px`;
}

setCompassFrame(0);

// ── Device Orientation ───────────────────────────────────────
let currentHeading = 0;
let lastBearing    = 0;

window.addEventListener('deviceorientationabsolute', e => {
    if (e.alpha != null) { currentHeading = 360 - e.alpha; updateCompassFrame(); }
});
window.addEventListener('deviceorientation', e => {
    if (e.alpha != null && currentHeading === 0) { currentHeading = 360 - e.alpha; updateCompassFrame(); }
});

function updateCompassFrame() {
    const rel = (lastBearing - currentHeading + 360) % 360;
    setCompassFrame(bearingToFrame(rel));
    document.getElementById('bearingValue').innerText   = Math.round(lastBearing) + '°';
    document.getElementById('directionValue').innerText = getCardinalDirection(lastBearing);
}

// ── GPS ──────────────────────────────────────────────────────
function getLocationAndAdd() {
    navigator.geolocation.getCurrentPosition(pos => {
        const name = prompt('Nama lokasi:');
        if (!name) return;
        fetch('/add_location', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ name, latitude: pos.coords.latitude, longitude: pos.coords.longitude })
        }).then(() => location.reload());
    }, err => alert('GPS Error: ' + err.message), { enableHighAccuracy: true });
}

function updateLocation() {
    navigator.geolocation.watchPosition(sendLocation, err => {
        console.warn('GPS Error:', err);
        document.getElementById('distanceValue').innerText = 'Error';
        document.getElementById('distanceValue').classList.remove('loading');
    }, { enableHighAccuracy: true, maximumAge: 0, timeout: 5000 });
}

function sendLocation(pos) {
    const lat = pos.coords.latitude;
    const lon = pos.coords.longitude;
    const id  = document.getElementById('locationSelect').value;

    fetch('/update_location', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ latitude: lat, longitude: lon, location_id: id })
    })
    .then(r => r.json()).then(data => {
        if (data.distance !== undefined) {
            const el = document.getElementById('distanceValue');
            el.innerText = formatDistance(data.distance);
            el.classList.remove('loading');
            fetch('/get_location_coords/' + id).then(r => r.json()).then(dest => {
                lastBearing = calculate_bearing(lat, lon, dest.latitude, dest.longitude);
                updateCompassFrame();
            });
        }
    });
}

function formatDistance(m) {
    return Math.round(m).toLocaleString('id-ID');
}

function calculate_bearing(lat1, lon1, lat2, lon2) {
    const toRad = d => d * Math.PI / 180;
    const toDeg = r => r * 180 / Math.PI;
    const dLon  = toRad(lon2 - lon1);
    const φ1 = toRad(lat1), φ2 = toRad(lat2);
    const y = Math.sin(dLon) * Math.cos(φ2);
    const x = Math.cos(φ1) * Math.sin(φ2) - Math.sin(φ1) * Math.cos(φ2) * Math.cos(dLon);
    return (toDeg(Math.atan2(y, x)) + 360) % 360;
}

function getCardinalDirection(b) {
    return ['N','NE','E','SE','S','SW','W','NW'][Math.round(b / 45) % 8];
}

// ── Google Maps ──────────────────────────────────────────────
function openGoogleMaps(lat, lon) {
    window.open(`https://www.google.com/maps/dir/?api=1&destination=${lat},${lon}&travelmode=driving`, '_blank');
}

function openGoogleMapsFromCompass() {
    const id = document.getElementById('locationSelect').value;
    fetch('/get_location_coords/' + id).then(r => r.json()).then(dest => {
        window.open(`https://www.google.com/maps/dir/?api=1&destination=${dest.latitude},${dest.longitude}&travelmode=driving`, '_blank');
    });
}

// ── Reveal Koordinat (Mobile) ────────────────────────────────
function toggleReveal(id) {
    const lat = document.getElementById('lat-' + id);
    const lon = document.getElementById('lon-' + id);
    const btn = document.getElementById('revealBtn-' + id);
    const shown = lat.classList.toggle('revealed');
    lon.classList.toggle('revealed');
    btn.textContent = shown ? '🙈 Sembunyikan Koordinat' : '👁️ Perlihatkan Koordinat';
}

// ── Reveal Koordinat (Desktop Table) ────────────────────────
function toggleTableReveal(id) {
    const tlat = document.getElementById('tlat-' + id);
    const tlon = document.getElementById('tlon-' + id);
    const btn  = document.getElementById('treveal-' + id);
    const shown = tlat.classList.toggle('revealed');
    tlon.classList.toggle('revealed');
    btn.textContent = shown ? '🙈' : '👁️';
}

// ── Filter ───────────────────────────────────────────────────
function filterLocations() {
    const input  = document.getElementById('searchInput').value.toLowerCase();
    const select = document.getElementById('locationSelect');
    const table  = document.getElementById('locationsTable');
    const grid   = document.getElementById('locationsGrid');

    for (let i = 0; i < select.options.length; i++) {
        select.options[i].style.display = select.options[i].text.toLowerCase().includes(input) ? '' : 'none';
    }
    if (table && table.getElementsByTagName('tbody')[0]) {
        for (let row of table.getElementsByTagName('tbody')[0].rows) {
            row.style.display = row.cells[1].textContent.toLowerCase().includes(input) ? '' : 'none';
        }
    }
    if (grid) {
        for (let card of grid.getElementsByClassName('location-card')) {
            card.style.display = card.querySelector('.location-name').textContent.toLowerCase().includes(input) ? '' : 'none';
        }
    }
}

// ── Edit Toggle ──────────────────────────────────────────────
function toggleEdit(id) {
    const card = document.getElementById('card-' + id);
    if (card) card.classList.toggle('edit-mode');
}

// ── Init ─────────────────────────────────────────────────────
window.onload = () => {
    updateLocation();
    if (typeof DeviceOrientationEvent !== 'undefined' && typeof DeviceOrientationEvent.requestPermission === 'function') {
        DeviceOrientationEvent.requestPermission()
            .then(r => { if (r === 'granted') console.log('Orientation granted'); })
            .catch(console.error);
    }
};
</script>
</body>
</html>
"""

@app.route('/')
def index():
    init_db()
    with sqlite3.connect('locations.db') as conn:
        c = conn.cursor()
        c.execute('SELECT id, name, latitude, longitude FROM locations')
        locations = c.fetchall()
    return render_template_string(HTML_TEMPLATE, locations=locations)

@app.route('/kompas.png')
def kompas_img():
    return send_file('kompas.png', mimetype='image/png')

@app.route('/update_location', methods=['POST'])
def update_location():
    data = request.get_json()
    location_id = int(data.get('location_id', 1))
    with sqlite3.connect('locations.db') as conn:
        c = conn.cursor()
        c.execute('SELECT latitude, longitude FROM locations WHERE id = ?', (location_id,))
        row = c.fetchone()
    if not row:
        return jsonify(error="Location not found"), 404
    lat2, lon2 = row
    dist = haversine(data['latitude'], data['longitude'], lat2, lon2)
    return jsonify(distance=dist)

@app.route('/get_location_coords/<int:id>')
def get_location_coords(id):
    with sqlite3.connect('locations.db') as conn:
        c = conn.cursor()
        c.execute('SELECT latitude, longitude FROM locations WHERE id = ?', (id,))
        row = c.fetchone()
    if not row:
        return jsonify(error="Location not found"), 404
    lat, lon = row
    return jsonify(latitude=lat, longitude=lon)

@app.route('/add_location', methods=['POST'])
def add_location():
    if request.is_json:
        d = request.get_json()
        name, lat, lon = d['name'], d['latitude'], d['longitude']
    else:
        f = request.form
        name, lat, lon = f['name'], float(f['latitude']), float(f['longitude'])
    with sqlite3.connect('locations.db') as conn:
        c = conn.cursor()
        c.execute('INSERT INTO locations(name, latitude, longitude) VALUES(?, ?, ?)', (name, lat, lon))
        conn.commit()
    return redirect(url_for('index'))

@app.route('/edit_location/<int:id>', methods=['POST'])
def edit_location(id):
    f = request.form
    name, lat, lon = f['name'], float(f['latitude']), float(f['longitude'])
    with sqlite3.connect('locations.db') as conn:
        c = conn.cursor()
        c.execute('UPDATE locations SET name=?, latitude=?, longitude=? WHERE id=?', (name, lat, lon, id))
        conn.commit()
    return redirect(url_for('index'))

@app.route('/delete_location/<int:id>', methods=['POST'])
def delete_location(id):
    with sqlite3.connect('locations.db') as conn:
        c = conn.cursor()
        c.execute('DELETE FROM locations WHERE id=?', (id,))
        conn.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    os.system("termux-open-url http://127.0.0.1:5000")
    app.run(debug=True, host='127.0.0.1', port=5000)
