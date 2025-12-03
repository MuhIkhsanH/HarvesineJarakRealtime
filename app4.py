from flask import Flask, render_template_string, request, jsonify, redirect, url_for
import math
import sqlite3
from flask_cors import CORS

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
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }

    body {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        min-height: 100vh;
        padding: 20px;
        color: #333;
    }

    .container {
        max-width: 1200px;
        margin: 0 auto;
    }

    header {
        text-align: center;
        margin-bottom: 30px;
    }

    h1 {
        color: white;
        font-size: 2.5em;
        font-weight: 700;
        margin-bottom: 10px;
        text-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }

    .subtitle {
        color: rgba(255,255,255,0.9);
        font-size: 1.1em;
        font-weight: 400;
    }

    .main-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 20px;
        margin-bottom: 30px;
    }

    @media (max-width: 768px) {
        .main-grid {
            grid-template-columns: 1fr;
        }
    }

    .card {
        background: white;
        border-radius: 20px;
        padding: 30px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.1);
    }

    .compass-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-height: 400px;
    }

    .location-selector {
        width: 100%;
        margin-bottom: 20px;
    }

    .search-box {
        width: 100%;
        padding: 12px 20px;
        border: 2px solid #e0e0e0;
        border-radius: 12px;
        font-size: 1em;
        transition: all 0.3s;
        margin-bottom: 15px;
    }

    .search-box:focus {
        outline: none;
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102,126,234,0.1);
    }

    select {
        width: 100%;
        padding: 12px 20px;
        border: 2px solid #e0e0e0;
        border-radius: 12px;
        font-size: 1em;
        background: white;
        cursor: pointer;
        transition: all 0.3s;
    }

    select:focus {
        outline: none;
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102,126,234,0.1);
    }

    #compass {
        width: 280px;
        height: 280px;
        position: relative;
        margin: 30px 0;
    }

    #compassSvg {
        width: 100%;
        height: 100%;
        filter: drop-shadow(0 4px 20px rgba(0,0,0,0.15));
    }

    .distance-display {
        text-align: center;
        margin-top: 20px;
    }

    .distance-value {
        font-size: 3em;
        font-weight: 700;
        color: #667eea;
        margin-bottom: 5px;
    }

    .distance-label {
        font-size: 1.1em;
        color: #666;
        font-weight: 500;
    }

    .bearing-info {
        display: flex;
        justify-content: space-around;
        margin-top: 20px;
        padding-top: 20px;
        border-top: 2px solid #f0f0f0;
    }

    .bearing-item {
        text-align: center;
    }

    .bearing-item-label {
        font-size: 0.9em;
        color: #999;
        margin-bottom: 5px;
    }

    .bearing-item-value {
        font-size: 1.4em;
        font-weight: 600;
        color: #333;
    }

    .section-title {
        font-size: 1.5em;
        font-weight: 600;
        margin-bottom: 20px;
        color: #333;
    }

    .form-group {
        margin-bottom: 15px;
    }

    input[type="text"],
    input[type="number"] {
        width: 100%;
        padding: 12px 20px;
        border: 2px solid #e0e0e0;
        border-radius: 12px;
        font-size: 1em;
        transition: all 0.3s;
    }

    input[type="text"]:focus,
    input[type="number"]:focus {
        outline: none;
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102,126,234,0.1);
    }

    .button-group {
        display: flex;
        gap: 10px;
        margin-top: 15px;
    }

    button {
        flex: 1;
        padding: 12px 24px;
        border: none;
        border-radius: 12px;
        font-size: 1em;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s;
    }

    .btn-primary {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }

    .btn-primary:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 20px rgba(102,126,234,0.4);
    }

    .btn-secondary {
        background: #f5f5f5;
        color: #333;
    }

    .btn-secondary:hover {
        background: #e0e0e0;
    }

    .btn-danger {
        background: #ff4757;
        color: white;
    }

    .btn-danger:hover {
        background: #ee5a6f;
    }

    .btn-success {
        background: #2ed573;
        color: white;
    }

    .btn-success:hover {
        background: #26de81;
    }

    /* Location Cards for Mobile */
    .locations-grid {
        display: grid;
        gap: 15px;
        margin-top: 20px;
    }

    .location-card {
        background: #f8f9fa;
        border-radius: 12px;
        padding: 20px;
        border: 2px solid #e0e0e0;
        transition: all 0.3s;
    }

    .location-card:hover {
        border-color: #667eea;
        box-shadow: 0 4px 12px rgba(102,126,234,0.15);
    }

    .location-card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 15px;
        padding-bottom: 15px;
        border-bottom: 2px solid #e0e0e0;
    }

    .location-name {
        font-size: 1.3em;
        font-weight: 700;
        color: #333;
    }

    .location-id {
        background: #667eea;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.9em;
        font-weight: 600;
    }

    .location-coords {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 10px;
        margin-bottom: 15px;
    }

    .coord-item {
        background: white;
        padding: 10px;
        border-radius: 8px;
    }

    .coord-label {
        font-size: 0.8em;
        color: #999;
        margin-bottom: 5px;
    }

    .coord-value {
        font-size: 1em;
        font-weight: 600;
        color: #333;
        font-family: 'Courier New', monospace;
    }

    .location-actions {
        display: flex;
        gap: 10px;
    }

    .location-actions button {
        flex: 1;
        padding: 10px;
        font-size: 0.95em;
    }

    /* Edit Mode Styles */
    .location-card.edit-mode {
        background: #fff;
        border-color: #667eea;
    }

    .edit-form {
        display: none;
    }

    .edit-mode .edit-form {
        display: block;
    }

    .edit-mode .view-content {
        display: none;
    }

    .edit-input-group {
        margin-bottom: 12px;
    }

    .edit-input-group label {
        display: block;
        font-size: 0.9em;
        color: #666;
        margin-bottom: 5px;
        font-weight: 600;
    }

    .edit-input-group input {
        width: 100%;
        padding: 10px;
        border: 2px solid #e0e0e0;
        border-radius: 8px;
    }

    /* Desktop table view (hidden on mobile) */
    table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        margin-top: 20px;
        display: none;
    }

    @media (min-width: 1024px) {
        table {
            display: table;
        }

        .locations-grid {
            display: none;
        }

        th {
            background: #f8f9fa;
            padding: 15px;
            text-align: left;
            font-weight: 600;
            color: #666;
            border-bottom: 2px solid #e0e0e0;
        }

        th:first-child {
            border-top-left-radius: 12px;
        }

        th:last-child {
            border-top-right-radius: 12px;
        }

        td {
            padding: 15px;
            border-bottom: 1px solid #f0f0f0;
        }

        tr:last-child td:first-child {
            border-bottom-left-radius: 12px;
        }

        tr:last-child td:last-child {
            border-bottom-right-radius: 12px;
        }

        tr:hover {
            background: #f8f9fa;
        }

        .table-input {
            padding: 8px 12px;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            font-size: 0.9em;
            width: 100%;
        }

        .table-button {
            padding: 8px 16px;
            font-size: 0.9em;
            margin-right: 5px;
        }
    }

    .status-badge {
        display: inline-block;
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 0.85em;
        font-weight: 600;
    }

    .status-active {
        background: #d4edda;
        color: #155724;
    }

    .status-inactive {
        background: #f8d7da;
        color: #721c24;
    }

    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }

    .loading {
        animation: pulse 1.5s ease-in-out infinite;
    }
</style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🧭 GPS Distance Tracker</h1>
            <p class="subtitle">Track your distance and direction in real-time</p>
        </header>

        <div class="main-grid">
            <!-- Compass Section -->
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

                    <div id="compass">
                        <svg id="compassSvg" viewBox="0 0 200 200">
                            <!-- Outer circle -->
                            <circle cx="100" cy="100" r="95" fill="white" stroke="#e0e0e0" stroke-width="2"/>

                            <!-- Cardinal directions background -->
                            <circle cx="100" cy="100" r="85" fill="none" stroke="#f0f0f0" stroke-width="1"/>

                            <!-- Direction markers -->
                            <g id="directions">
                                <!-- N -->
                                <text x="100" y="25" text-anchor="middle" font-size="16" font-weight="bold" fill="#667eea">N</text>
                                <!-- E -->
                                <text x="175" y="105" text-anchor="middle" font-size="14" font-weight="600" fill="#999">E</text>
                                <!-- S -->
                                <text x="100" y="180" text-anchor="middle" font-size="14" font-weight="600" fill="#999">S</text>
                                <!-- W -->
                                <text x="25" y="105" text-anchor="middle" font-size="14" font-weight="600" fill="#999">W</text>
                            </g>

                            <!-- Degree markers -->
                            <g id="degreeMarkers">
                                <line x1="100" y1="10" x2="100" y2="20" stroke="#ccc" stroke-width="2"/>
                                <line x1="100" y1="180" x2="100" y2="190" stroke="#ccc" stroke-width="2"/>
                                <line x1="10" y1="100" x2="20" y2="100" stroke="#ccc" stroke-width="2"/>
                                <line x1="180" y1="100" x2="190" y2="100" stroke="#ccc" stroke-width="2"/>
                            </g>

                            <!-- Center circle -->
                            <circle cx="100" cy="100" r="8" fill="#667eea"/>

                            <!-- Arrow (will rotate) -->
                            <g id="arrow" transform-origin="100 100">
                                <!-- North pointer (red) -->
                                <path d="M 100 30 L 110 90 L 100 85 L 90 90 Z" fill="#ff4757" stroke="#cc1f2f" stroke-width="1"/>
                                <!-- South pointer (white) -->
                                <path d="M 100 170 L 110 110 L 100 115 L 90 110 Z" fill="white" stroke="#ccc" stroke-width="1"/>
                            </g>
                        </svg>
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
                </div>
            </div>

            <!-- Add Location Section -->
            <div class="card">
                <h2 class="section-title">➕ Add New Location</h2>
                <form action="/add_location" method="POST">
                    <div class="form-group">
                        <input type="text" name="name" placeholder="Location Name" required>
                    </div>
                    <div class="form-group">
                        <input type="number" step="any" name="latitude" placeholder="Latitude" required>
                    </div>
                    <div class="form-group">
                        <input type="number" step="any" name="longitude" placeholder="Longitude" required>
                    </div>
                    <div class="button-group">
                        <button type="submit" class="btn-primary">Add Manually</button>
                        <button type="button" class="btn-success" onclick="getLocationAndAdd()">Use Current Location</button>
                    </div>
                </form>
            </div>
        </div>

        <!-- Manage Locations Section -->
        <div class="card">
            <h2 class="section-title">📍 Manage Locations</h2>

            <!-- Mobile Card View -->
            <div class="locations-grid" id="locationsGrid">
                {% for loc in locations %}
                <div class="location-card" id="card-{{ loc[0] }}">
                    <div class="view-content">
                        <div class="location-card-header">
                            <div class="location-name">{{ loc[1] }}</div>
                            <div class="location-id">#{{ loc[0] }}</div>
                        </div>

                        <div class="location-coords">
                            <div class="coord-item">
                                <div class="coord-label">Latitude</div>
                                <div class="coord-value">{{ "%.6f"|format(loc[2]) }}</div>
                            </div>
                            <div class="coord-item">
                                <div class="coord-label">Longitude</div>
                                <div class="coord-value">{{ "%.6f"|format(loc[3]) }}</div>
                            </div>
                        </div>

                        <div class="location-actions">
                            <button class="btn-primary" onclick="toggleEdit({{ loc[0] }})">✏️ Edit</button>
                            <form action="/delete_location/{{ loc[0] }}" method="POST" style="flex: 1;">
                                <button type="submit" class="btn-danger" style="width: 100%;" onclick="return confirm('Delete {{ loc[1] }}?')">🗑️ Delete</button>
                            </form>
                        </div>
                    </div>

                    <form action="/edit_location/{{ loc[0] }}" method="POST" class="edit-form">
                        <div class="edit-input-group">
                            <label>Location Name</label>
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
                            <button type="submit" class="btn-success">💾 Save</button>
                            <button type="button" class="btn-secondary" onclick="toggleEdit({{ loc[0] }})">✖️ Cancel</button>
                        </div>
                    </form>
                </div>
                {% endfor %}
            </div>

            <!-- Desktop Table View -->
            <table id="locationsTable">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Name</th>
                        <th>Latitude</th>
                        <th>Longitude</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                {% for loc in locations %}
                <tr>
                    <td>{{ loc[0] }}</td>
                    <td><strong>{{ loc[1] }}</strong></td>
                    <td>{{ "%.6f"|format(loc[2]) }}</td>
                    <td>{{ "%.6f"|format(loc[3]) }}</td>
                    <td>
                        <form action="/edit_location/{{ loc[0] }}" method="POST" style="display:inline;">
                            <input type="text" name="name" value="{{ loc[1] }}" class="table-input" required>
                            <input type="number" step="any" name="latitude" value="{{ loc[2] }}" class="table-input" required>
                            <input type="number" step="any" name="longitude" value="{{ loc[3] }}" class="table-input" required>
                            <button type="submit" class="btn-primary table-button">Save</button>
                        </form>
                        <form action="/delete_location/{{ loc[0] }}" method="POST" style="display:inline;">
                            <button type="submit" class="btn-danger table-button" onclick="return confirm('Delete this location?')">Delete</button>
                        </form>
                    </td>
                </tr>
                {% endfor %}
                </tbody>
            </table>
        </div>
    </div>

<script>
let currentHeading = 0;
let lastBearing = 0;
let currentRotation = 0; // Track current rotation angle

// Device orientation for compass heading
window.addEventListener('deviceorientationabsolute', e => {
    if (e.alpha != null) {
        currentHeading = 360 - e.alpha;
        updateCompassRotation();
    }
});

// Fallback for devices without absolute orientation
window.addEventListener('deviceorientation', e => {
    if (e.alpha != null && currentHeading === 0) {
        currentHeading = 360 - e.alpha;
        updateCompassRotation();
    }
});

function normalizeAngle(angle) {
    // Normalize angle to 0-360 range
    return ((angle % 360) + 360) % 360;
}

function getShortestRotation(from, to) {
    // Calculate the shortest rotation direction
    let diff = normalizeAngle(to - from);
    if (diff > 180) {
        diff = diff - 360;
    }
    return from + diff;
}

function updateCompassRotation() {
    const arrow = document.getElementById('arrow');
    const targetAngle = normalizeAngle(lastBearing - currentHeading);

    // Calculate shortest path to target angle
    const newRotation = getShortestRotation(currentRotation, targetAngle);
    currentRotation = newRotation;

    arrow.style.transform = `rotate(${currentRotation}deg)`;
    arrow.style.transition = 'transform 0.3s ease-out';
}

function getLocationAndAdd() {
    navigator.geolocation.getCurrentPosition(pos => {
        const name = prompt('Enter location name:');
        if (!name) return;
        fetch('/add_location', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                name: name,
                latitude: pos.coords.latitude,
                longitude: pos.coords.longitude
            })
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
    const id = document.getElementById('locationSelect').value;

    fetch('/update_location', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ latitude: lat, longitude: lon, location_id: id })
    })
    .then(r => r.json()).then(data => {
        if (data.distance !== undefined) {
            const distanceEl = document.getElementById('distanceValue');
            distanceEl.innerText = data.distance.toFixed(2);
            distanceEl.classList.remove('loading');

            fetch('/get_location_coords/' + id).then(r => r.json()).then(dest => {
                const bearing = calculate_bearing(lat, lon, dest.latitude, dest.longitude);

                // Smooth transition for bearing changes
                const bearingDiff = Math.abs(bearing - lastBearing);
                if (bearingDiff > 180) {
                    // Large jump, adjust gradually
                    lastBearing = bearing;
                } else {
                    // Small change, update directly
                    lastBearing = bearing;
                }

                updateCompassRotation();

                document.getElementById('bearingValue').innerText = Math.round(bearing) + '°';
                document.getElementById('directionValue').innerText = getCardinalDirection(bearing);
            });
        }
    });
}

function calculate_bearing(lat1, lon1, lat2, lon2) {
    const toRad = deg => deg * Math.PI / 180;
    const toDeg = rad => rad * 180 / Math.PI;
    let dLon = toRad(lon2 - lon1);
    let φ1 = toRad(lat1), φ2 = toRad(lat2);
    let y = Math.sin(dLon) * Math.cos(φ2);
    let x = Math.cos(φ1) * Math.sin(φ2) - Math.sin(φ1) * Math.cos(φ2) * Math.cos(dLon);
    return (toDeg(Math.atan2(y, x)) + 360) % 360;
}

function getCardinalDirection(bearing) {
    const directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];
    const index = Math.round(bearing / 45) % 8;
    return directions[index];
}

function filterLocations() {
    const input = document.getElementById('searchInput').value.toLowerCase();
    const select = document.getElementById('locationSelect');
    const table = document.getElementById('locationsTable');
    const grid = document.getElementById('locationsGrid');

    // Filter dropdown
    for (let i = 0; i < select.options.length; i++) {
        let text = select.options[i].text.toLowerCase();
        select.options[i].style.display = text.includes(input) ? '' : 'none';
    }

    // Filter table (desktop)
    if (table && table.getElementsByTagName('tbody')[0]) {
        const tbody = table.getElementsByTagName('tbody')[0];
        for (let row of tbody.rows) {
            let nameCell = row.cells[1].textContent.toLowerCase();
            row.style.display = nameCell.includes(input) ? '' : 'none';
        }
    }

    // Filter cards (mobile)
    if (grid) {
        const cards = grid.getElementsByClassName('location-card');
        for (let card of cards) {
            const name = card.querySelector('.location-name').textContent.toLowerCase();
            card.style.display = name.includes(input) ? '' : 'none';
        }
    }
}

function toggleEdit(id) {
    const card = document.getElementById('card-' + id);
    if (card) {
        card.classList.toggle('edit-mode');
    }
}

window.onload = () => {
    updateLocation();

    // Request device orientation permission for iOS
    if (typeof DeviceOrientationEvent !== 'undefined' && typeof DeviceOrientationEvent.requestPermission === 'function') {
        DeviceOrientationEvent.requestPermission()
            .then(response => {
                if (response === 'granted') {
                    console.log('Device orientation permission granted');
                }
            })
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
        c.execute('UPDATE locations SET name=?, latitude=?, longitude=? WHERE id=?',
                  (name, lat, lon, id))
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
    app.run(debug=True, host='127.0.0.1', port=5000)
