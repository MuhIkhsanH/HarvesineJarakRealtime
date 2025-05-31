from flask import Flask, render_template_string, request, jsonify, redirect, url_for
import math
import sqlite3
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def init_db():
    with sqlite3.connect('locations.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL
            )
        ''')
        cursor.execute('SELECT COUNT(*) FROM locations')
        if cursor.fetchone()[0] == 0:
            cursor.execute('INSERT INTO locations (name, latitude, longitude) VALUES (?, ?, ?)',
                           ('Default Location', 0, 0))
        conn.commit()

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>REAL-TIME GPS LOCATION METAVERSE</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; background-color: black; color: white; margin: 0; padding: 20px; }
        h1 { font-size: 100px; font-weight: bold; color: #ff0000; margin-top: 50px; text-shadow: 5px 5px 10px rgba(255,0,0,0.8); }
        p { font-size: 80px; font-weight: bold; text-shadow: 3px 3px 8px rgba(255,255,255,0.8); }
        #location { font-size: 120px; font-weight: bold; color: #00ff00; text-shadow: 4px 4px 10px rgba(0,255,0,0.8); margin-top: 20px; }
        .container { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 100vh; }
        select, input, button { font-size: 28px; padding: 12px; margin: 10px; }
        table { width: 80%; margin: 20px auto; border-collapse: collapse; }
        th, td { border: 1px solid white; padding: 10px; text-align: center; }
        th { background-color: #333; }
        button { background-color: #ff0000; color: white; border: none; cursor: pointer; }
        button:hover { background-color: #cc0000; }
        input { background-color: #222; color: white; border: 1px solid #555; }
    </style>
    <script>
        function getLocationAndAdd() {
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(function(position) {
                    const name = prompt("Masukkan nama lokasi:");
                    if (name) {
                        fetch('/add_location', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({
                                name: name,
                                latitude: position.coords.latitude,
                                longitude: position.coords.longitude
                            })
                        }).then(() => location.reload());
                    }
                }, showError, { enableHighAccuracy: true });
            } else {
                alert("Geolocation tidak didukung browser ini.");
            }
        }

        function getLocation() {
            if (navigator.geolocation) {
                navigator.geolocation.watchPosition(sendLocation, showError, { enableHighAccuracy: true });
            } else {
                alert("Geolocation tidak didukung.");
            }
        }

        function sendLocation(position) {
            const selectedLocationId = document.getElementById("locationSelect").value;
            fetch('/update_location', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    latitude: position.coords.latitude,
                    longitude: position.coords.longitude,
                    location_id: selectedLocationId
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.distance !== undefined) {
                    document.getElementById("location").innerHTML =
                        "🚀 " + data.distance.toFixed(2) + " METER";
                } else {
                    document.getElementById("location").innerHTML =
                        "⚠️ Lokasi tidak ditemukan.";
                }
            })
            .catch(error => {
                console.error("Gagal menghitung jarak:", error);
                document.getElementById("location").innerHTML = "❌ Error.";
            });
        }

        function showError(error) {
            let msg = "";
            switch(error.code) {
                case error.PERMISSION_DENIED:
                    msg = "⛔ Akses lokasi ditolak.";
                    break;
                case error.POSITION_UNAVAILABLE:
                    msg = "❌ Lokasi tidak tersedia.";
                    break;
                case error.TIMEOUT:
                    msg = "⌛ Timeout.";
                    break;
                case error.UNKNOWN_ERROR:
                    msg = "⚠ Kesalahan tidak diketahui.";
                    break;
            }
            alert(msg);
        }

        function updateLocation() {
            getLocation();
        }

        window.onload = () => {
            getLocation();
        };
    </script>
</head>
<body>
    <div class="container">
        <h1>JARAK KE TUJUAN</h1>
        <select id="locationSelect" onchange="updateLocation()">
            {% for location in locations %}
            <option value="{{ location[0] }}">{{ location[1] }}</option>
            {% endfor %}
        </select>
        <p id="location">🔄 Mengambil lokasi...</p>

        <h2>Tambah Lokasi Baru</h2>
        <form action="/add_location" method="POST">
            <input type="text" name="name" placeholder="Nama Lokasi" required>
            <input type="number" step="any" name="latitude" placeholder="Latitude" required>
            <input type="number" step="any" name="longitude" placeholder="Longitude" required>
            <button type="submit">Tambah Manual</button>
            <button type="button" onclick="getLocationAndAdd()">Tambah Lokasi Saat Ini</button>
        </form>

        <h2>Kelola Lokasi</h2>
        <table>
            <tr>
                <th>ID</th>
                <th>Nama</th>
                <th>Latitude</th>
                <th>Longitude</th>
                <th>Aksi</th>
            </tr>
            {% for location in locations %}
            <tr>
                <td>{{ location[0] }}</td>
                <td>{{ location[1] }}</td>
                <td>{{ location[2] }}</td>
                <td>{{ location[3] }}</td>
                <td>
                    <form action="/edit_location/{{ location[0] }}" method="POST" style="display:inline;">
                        <input type="text" name="name" value="{{ location[1] }}" required>
                        <input type="number" step="any" name="latitude" value="{{ location[2] }}" required>
                        <input type="number" step="any" name="longitude" value="{{ location[3] }}" required>
                        <button type="submit">Edit</button>
                    </form>
                    <form action="/delete_location/{{ location[0] }}" method="POST" style="display:inline;">
                        <button type="submit" onclick="return confirm('Hapus lokasi ini?')">Hapus</button>
                    </form>
                </td>
            </tr>
            {% endfor %}
        </table>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    with sqlite3.connect('locations.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, latitude, longitude FROM locations')
        locations = cursor.fetchall()
    return render_template_string(HTML_TEMPLATE, locations=locations)

@app.route('/update_location', methods=['POST'])
def update_location():
    data = request.get_json()
    location_id = int(data.get('location_id', 1))
    with sqlite3.connect('locations.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT latitude, longitude FROM locations WHERE id = ?', (location_id,))
        result = cursor.fetchone()
        if result:
            target_lat, target_lon = result
            distance = haversine(target_lat, target_lon, data['latitude'], data['longitude'])
            return jsonify({"distance": distance})
        else:
            return jsonify({"error": "Lokasi tidak ditemukan"}), 404

@app.route('/add_location', methods=['POST'])
def add_location():
    if request.is_json:
        data = request.get_json()
        name = data['name']
        latitude = float(data['latitude'])
        longitude = float(data['longitude'])
    else:
        name = request.form.get('name')
        latitude = float(request.form.get('latitude'))
        longitude = float(request.form.get('longitude'))

    with sqlite3.connect('locations.db') as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO locations (name, latitude, longitude) VALUES (?, ?, ?)',
                       (name, latitude, longitude))
        conn.commit()
    return redirect(url_for('index'))

@app.route('/edit_location/<int:id>', methods=['POST'])
def edit_location(id):
    name = request.form.get('name')
    latitude = float(request.form.get('latitude'))
    longitude = float(request.form.get('longitude'))
    with sqlite3.connect('locations.db') as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE locations SET name = ?, latitude = ?, longitude = ? WHERE id = ?',
                       (name, latitude, longitude, id))
        conn.commit()
    return redirect(url_for('index'))

@app.route('/delete_location/<int:id>', methods=['POST'])
def delete_location(id):
    with sqlite3.connect('locations.db') as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM locations WHERE id = ?', (id,))
        conn.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
