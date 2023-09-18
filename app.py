from flask import Flask, render_template, request, redirect, url_for
import os
import pyrebase
import uuid
import datetime

app = Flask(__name__)

config = {
    "apiKey": "AIzaSyCGCrFViSsursoizS3Dgssbsr70Kd3zOYw",
    "authDomain": "onwords-master-api-db.firebaseapp.com",
    "projectId": "onwords-master-api-db",
    "storageBucket": "onwords-master-api-db.appspot.com",
    "messagingSenderId": "812641457896",
    "appId": "1:812641457896:web:5226da7ccadaad50009b5d",
    "measurementId": "G-4TW59PDLHQ",
    "databaseURL":"https://onwords-master-api-db-default-rtdb.asia-southeast1.firebasedatabase.app"
    }

firebase = pyrebase.initialize_app(config)
db = firebase.database()
auth = firebase.auth()

firmware_directory = '/firmware/3chfb'

app.jinja_env.globals['cache'] = False

@app.route('/', methods=['GET', 'POST'])
def home():
    error_message = None
    device_data = {}
    online_status = "Online"

    if request.method == 'POST':
        product_id = request.form.get('product_id')

        if not product_id:
            error_message = "Product ID is required."
        else:
            device_data = db.child("Devices").child(product_id).get().val()

            if not device_data:
                error_message = "Product ID not found."
            else:
                disconnected_time = device_data.get('disconnected_time', {})
                if disconnected_time:
                    if any(info.get('date') and info.get('time') and info.get('date') != '' and info.get('time') != '' for info in disconnected_time.values()):
                        online_status = "Offline"

    return render_template('home.html', device_data=device_data, error_message=error_message, online_status=online_status)

@app.route('/upload_firmware', methods=['POST'])
def upload_firmware():
    product_id = request.form.get('product_id')

    if not product_id:
        return redirect(url_for('home'))

    firmware_file = request.files['firmware_file']

    if firmware_file:
        os.makedirs(firmware_directory, exist_ok=True)
        
        new_firmware_ref = db.child("Devices").child(product_id).child("firmware").push({
            "filename": firmware_file.filename,
            "upload_date": datetime.date.today().strftime("%Y-%m-%d"),
            "version": "1.1.1"
        })
        
        firmware_uid = new_firmware_ref["name"]
        firmware_file.save(os.path.join(firmware_directory, firmware_uid))
        print(f"Firmware file '{firmware_uid}' saved to {firmware_directory}")

    return redirect(url_for('home'))

@app.route('/filter_devices', methods=['POST', 'GET'])
def filter_devices():
    product_id_prefix = request.form.get('product_id_prefix')

    if not product_id_prefix:
        return render_template('home.html', error_message="Invalid request")
    
    devices = db.child("Devices").get().val()
    filtered_devices = {}

    if devices:
        for device_id, device_data in devices.items():
            if device_id.startswith(product_id_prefix):
                filtered_devices[device_id] = device_data

    if filtered_devices:
        if product_id_prefix == '3chfb':
            return render_template('threechannel.html', device_data=filtered_devices)
        elif product_id_prefix == '4chfb':
            return render_template('fourchannel.html', device_data=filtered_devices)
        elif product_id_prefix == 'wta':
            return render_template('wta.html', device_data=filtered_devices)
        else:
            return render_template('home.html', error_message="Unknown product ID prefix")
    else:
        return render_template('home.html', error_message="No devices found for the selected module")

if __name__ == '__main__':
    app.run(debug=True, host="192.168.1.8", port=8000)