import os
import json
import requests
import onnxruntime as ort
import numpy as np
import joblib
import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import adafruit_dht
import minimalmodbus

# --- CONFIG & FIREBASE ---
FIREBASE_URL = "https://soil-ai-monitor-default-rtdb.asia-southeast1.firebasedatabase.app/.json"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ONNX_PATH = os.path.join(BASE_DIR, 'stacked_model.onnx')
ENCODINGS_PATH = os.path.join(BASE_DIR, 'encodings_final.pkl')

# --- SENSOR CALIBRATION ---
PH_OFFSET = -3.5
MOIST_DRY = 22000
MOIST_WET = 10000

print("Initializing AI Brain...")
session = ort.InferenceSession(ONNX_PATH)
input_name = session.get_inputs()[0].name
encodings = joblib.load(ENCODINGS_PATH)

# --- INITIALIZE SENSOR INTERFACES ---
try:
    i2c = busio.I2C(board.SCL, board.SDA)
    ads = ADS.ADS1115(i2c)
    moisture_chan = AnalogIn(ads, 0)
    ph_chan = AnalogIn(ads, 1)
    dht_device = adafruit_dht.DHT22(board.D4, use_pulseio=False)
    npk_sensor = minimalmodbus.Instrument('/dev/ttyUSB0', 1)
    npk_sensor.serial.baudrate = 4800
    npk_sensor.serial.timeout = 0.5
    print("✅ All Sensors Online & Connected.")
except Exception as e:
    print(f"⚠️ Sensor Hardware Setup Error: {e}")

# --- ROBUST LIVE READING FUNCTIONS ---
def read_dht22():
    global dht_device
    for i in range(5):
        try:
            t, h = dht_device.temperature, dht_device.humidity
            if t is not None: return float(t), float(h)
        except:
            try:
                dht_device.exit()
                time.sleep(0.5)
                dht_device = adafruit_dht.DHT22(board.D4, use_pulseio=False)
            except: pass
            time.sleep(0.5)
    return 25.0, 60.0

def read_moisture():
    try:
        raw = moisture_chan.value
        m = (MOIST_DRY - raw) / (MOIST_DRY - MOIST_WET) * 100
        return round(max(0, min(100, m)), 1)
    except: return 50.0

def read_ph():
    try:
        v = ph_chan.voltage
        ph_val = (3.5 * v) + PH_OFFSET
        return round(max(0, min(14, ph_val)), 2)
    except: return 7.0

def read_npk():
    try:
        n = npk_sensor.read_register(30, 0)
        if n == 0: n = npk_sensor.read_register(0, 0)
        p = npk_sensor.read_register(31, 0)
        k = npk_sensor.read_register(32, 0)
        return float(n), float(p), float(k)
    except: return 45.0, 50.0, 48.0  # Safe dataset averages if hardware defaults

# --- EXECUTE INFERENCE FROM CLOUD COMMAND ---
def process_on_demand(crop, stage):
    print(f"\n[AI GATEWAY] Waking Up. Querying live parameters for {crop} ({stage})...")
    
    # Read active hardware sensors
    n, p, k = read_npk()
    ph = read_ph()
    temp, hum = read_dht22()
    moist = read_moisture()
    
    print(f" -> Hardware Telemetry: NPK:{n},{p},{k} | pH:{ph} | Temp:{temp}°C | Moist:{moist}%")
    
    c_enc = float(encodings['Crop_Type'][crop])
    s_enc = float(encodings['Growth_Stage'][stage])
    
    features = [n, p, k, ph, temp, hum, moist, c_enc, s_enc]
    onnx_input = np.array([features], dtype=np.float32)
    
    prediction = session.run(None, {input_name: onnx_input})[0][0]
    
    return {
        "N": max(0, round(float(prediction[0]), 2)),
        "P": max(0, round(float(prediction[1]), 2)),
        "K": max(0, round(float(prediction[2]), 2))
    }

print("📡 Pi Node is active and listening to cloud ecosystem...")

while True:
    try:
        db_state = requests.get(FIREBASE_URL).json()
        
        if db_state.get('status') == 'requesting':
            target_crop = db_state.get('crop', 'Tomato')
            target_stage = db_state.get('stage', 'Vegetative')
            
            # Fetch sensor data and process model
            recs = process_on_demand(target_crop, target_stage)
            
            # Send results back and reset dashboard trigger status
            payload = {
                "recommendations": {"N": recs['N'], "P": recs['P'], "K": recs['K']},
                "status": "idle",
                "timestamp": time.strftime("%H:%M:%S")
            }
            requests.patch(FIREBASE_URL, data=json.dumps(payload))
            print("✅ Telemetry processed and synced to dashboard context.")
            
    except Exception as e:
        print(f"Error handling network state: {e}")
        
    time.sleep(1.5)