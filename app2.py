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

def calculate_bearing(lat1, lon1, lat2, lon2):
    dLon = math.radians(lon2 - lon1)
    φ1 = math.radians(lat1)
    φ2 = math.radians(lat2)
    y = math.sin(dLon) * math.cos(φ2)
    x = math.cos(φ1) * math.sin(φ2) - math.sin(φ1) * math.cos(φ2) * math.cos(dLon)
    brng = math.degrees(math.atan2(y, x))
    return (brng + 360) % 360

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>REAL-TIME GPS LOCATION METAVERSE</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        html, body {
            margin: 0;
            padding: 0;
            background: black;
            color: white;
            font-family: sans-serif;
        }
        .container {
            padding: 10px;
            max-width: 100%;
            box-sizing: border-box;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        h1 {
            font-size: 40px;
            color: red;
            margin: 20px 0;
        }
        p#location {
            font-size: 32px;
            font-weight: bold;
            color: #00ff00;
        }
        select, input, button {
            font-size: 20px;
            padding: 10px;
            margin: 5px;
            max-width: 90vw;
            box-sizing: border-box;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }
        th, td {
            border: 1px solid white;
            padding: 8px;
            font-size: 14px;
        }
        #arrow-container {
            margin: 30px auto;
            width: 60px;
            height: 100px;
            position: relative;
        }
        #arrow {
            width: 0;
            height: 0;
            border-left: 15px solid transparent;
            border-right: 15px solid transparent;
            border-bottom: 40px solid yellow;
            position: absolute;
            top: 0;
            left: 15px;
            transform-origin: bottom center;
        }
        #arrow-shaft {
            width: 4px;
            height: 60px;
            background: yellow;
            position: absolute;
            top: 40px;
            left: 28px;
        }
        form {
            margin: 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>JARAK KE TUJUAN</h1>
        <select id="locationSelect" onchange="updateLocation()">
            {% for loc in locations %}
            <option value="{{ loc[0] }}">{{ loc[1] }}</option>
            {% endfor %}
        </select>
        <p id="location">🔄 Mengambil lokasi...</p>

        <div id="arrow-container">
            <div id="arrow"></div>
            <div id="arrow-shaft"></div>
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
        <table>
            <tr><th>ID</th><th>Nama</th><th>Lat</th><th>Lon</th><th>Aksi</th></tr>
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
        </table>
    </div>

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
            document.getElementById('arrow-container').style.transform = 'rotate(' + angle + 'deg)';
        }

        window.onload = updateLocation;
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
