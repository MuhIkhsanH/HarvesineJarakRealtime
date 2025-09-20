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
        c.execute('SELECT COUNT(*) FROM locations')                                                         if c.fetchone()[0] == 0:
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
<title>REAL-TIME GPS - FUTURISTIC</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@500&display=swap" rel="stylesheet">
<style>
    body {
        margin: 0;
        font-family: 'Orbitron', sans-serif;
        background: radial-gradient(circle at center, #0a0a0a 0%, #000000 100%);
        color: #00ffea;
        text-align: center;
    }
    h1 {
        color: #ff004c;
        margin-top: 20px;
        font-size: 2.2em;
        text-shadow: 0 0 15px #ff004c;
    }
    #location {
        font-size: 2em;
        margin: 15px 0;
        color: #00ffea;
        text-shadow: 0 0 10px #00fff2;
    }
    select, input, button {
        font-size: 1em;
        padding: 10px;
        margin: 5px;
        border: none;
        border-radius: 6px;
        background: #111;
        color: #fff;
        box-shadow: 0 0 10px #00ffea;
    }
    input#searchInput {
        width: 300px;
        margin: 10px auto;
        display: block;
        box-sizing: border-box;
    }
    table {
        width: 90%;
        margin: 20px auto;
        border-collapse: collapse;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        overflow: hidden;
    }
    th, td {
        padding: 8px;
        border: 1px solid rgba(255,255,255,0.2);
        font-size: 0.9em;
    }
    #compass {
        width: 150px;
        height: 150px;
        margin: 30px auto;
        position: relative;
    }
    #arrow {
        width: 100%;
        height: 100%;
        transition: transform 0.5s ease-out;
    }
</style>
</head>
<body>
    <h1>📡 Distance & Direction Tracker</h1>

    <input type="text" id="searchInput" placeholder="Cari lokasi..." onkeyup="filterLocations()" />

    <select id="locationSelect" onchange="updateLocation()">
        {% for loc in locations %}
        <option value="{{ loc[0] }}">{{ loc[1] }}</option>
        {% endfor %}
    </select>

    <p id="location">🔄 Mengambil lokasi...</p>

    <div id="compass">
        <svg id="arrow" viewBox="0 0 100 100">
            <circle cx="50" cy="50" r="48" stroke="#00ffea" stroke-width="2" fill="none" />
            <polygon points="50,5 60,40 50,30 40,40" fill="#ff004c" />
            <polygon points="50,95 60,60 50,70 40,60" fill="#00ffea" />
        </svg>
    </div>

    <h2>Tambah Lokasi</h2>
    <form action="/add_location" method="POST">
        <input type="text" name="name" placeholder="Nama Lokasi" required>
        <input type="number" step="any" name="latitude" placeholder="Latitude" required>
        <input type="number" step="any" name="longitude" placeholder="Longitude" required>
        <button type="submit">Tambah Manual</button>
        <button type="button" onclick="getLocationAndAdd()">Tambah Lokasi Saat Ini</button>
    </form>

    <h2>Kelola Lokasi</h2>
    <table id="locationsTable">
        <thead>
        <tr><th>ID</th><th>Nama</th><th>Lat</th><th>Lon</th><th>Aksi</th></tr>
        </thead>
        <tbody>
        {% for loc in locations %}
        <tr>
            <td>{{ loc[0] }}</td>
            <td>{{ loc[1] }}</td>
            <td>{{ loc[2] }}</td>
            <td>{{ loc[3] }}</td>
            <td>
                <form action="/edit_location/{{ loc[0] }}" method="POST" style="display:inline;">
                    <input type="text" name="name" value="{{ loc[1] }}" required>
                    <input type="number" step="any" name="latitude" value="{{ loc[2] }}" required>
                    <input type="number" step="any" name="longitude" value="{{ loc[3] }}" required>
                    <button type="submit">Edit</button>
                </form>
                <form action="/delete_location/{{ loc[0] }}" method="POST" style="display:inline;">
                    <button type="submit" onclick="return confirm('Hapus lokasi ini?')">Hapus</button>
                </form>
            </td>
        </tr>
        {% endfor %}
        </tbody>
    </table>

<script>
let currentHeading = 0;
window.addEventListener('deviceorientationabsolute', e => {
    if (e.alpha != null) currentHeading = 360 - e.alpha;
});

function getLocationAndAdd() {
    navigator.geolocation.getCurrentPosition(pos => {
        const name = prompt('Nama lokasi:');
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
    navigator.geolocation.watchPosition(sendLocation, err => console.warn(err), { enableHighAccuracy: true });
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
            document.getElementById('location').innerText = '🚀 ' + data.distance.toFixed(2) + ' m';
            fetch('/get_location_coords/' + id).then(r => r.json()).then(dest => {
                const bearing = calculate_bearing(lat, lon, dest.latitude, dest.longitude);
                rotateArrow(bearing, currentHeading);
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
    let x = Math.cos(φ1) * Math.sin(φ2) -
            Math.sin(φ1) * Math.cos(φ2) * Math.cos(dLon);
    return (toDeg(Math.atan2(y, x)) + 360) % 360;
}

function rotateArrow(bearing, heading) {
    let angle = (bearing - heading + 360) % 360;
    document.getElementById('arrow').style.transform = 'rotate(' + angle + 'deg)';
}

// Filter lokasi di dropdown dan tabel
function filterLocations() {
    const input = document.getElementById('searchInput').value.toLowerCase();
    const select = document.getElementById('locationSelect');
    const table = document.getElementById('locationsTable').getElementsByTagName('tbody')[0];

    // Filter dropdown options
    for (let i = 0; i < select.options.length; i++) {
        let text = select.options[i].text.toLowerCase();
        select.options[i].style.display = text.includes(input) ? '' : 'none';
    }

    // Filter table rows
    for (let row of table.rows) {
        let nameCell = row.cells[1].textContent.toLowerCase();
        row.style.display = nameCell.includes(input) ? '' : 'none';
    }

    // Jika lokasi yang sedang dipilih tidak ada di dropdown yang terlihat, reset pilihan
    if (select.selectedOptions.length > 0 && select.selectedOptions[0].style.display === 'none') {
        select.selectedIndex = -1;
        document.getElementById('location').innerText = '🔄 Pilih lokasi...';
    }
}

window.onload = () => {
    updateLocation();
    filterLocations();  // Apply filter initially empty
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
        return jsonify(error="Lokasi tidak ditemukan"), 404
    lat2, lon2 = row
    dist = haversine(data['latitude'], data['longitude'], lat2, lon2)
    return jsonify(distance=dist)

@app.route('/get_location_coords/<int:id>')
def get_location_coords(id):
    with sqlite3.connect('locations.db') as conn:
        c = conn.cursor()
        c.execute('SELECT latitude, longitude FROM locations WHERE id = ?', (id,))
        lat, lon = c.fetchone()
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
