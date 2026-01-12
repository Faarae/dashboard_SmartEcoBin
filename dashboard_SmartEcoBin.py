import streamlit as st
import pandas as pd
import time
import base64
import joblib
import numpy as np
import requests # Library untuk HTTP Request
import datetime

# ==========================================
# 1. KONFIGURASI HALAMAN
# ==========================================
st.set_page_config(
    page_title="Rinoya Smart Eco-Bin",
    page_icon="logo.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- FUNGSI BACKGROUND IMAGE ---
def add_bg_from_local(image_file):
    try:
        with open(image_file, "rb") as f:
            encoded_string = base64.b64encode(f.read())
        st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url(data:image/jpeg;base64,{encoded_string.decode()});
            background-size: cover; background-repeat: no-repeat; background-attachment: fixed;
        }}
        </style>
        """, unsafe_allow_html=True)
    except: pass

add_bg_from_local('background.jpg') 

# --- LOAD OTAK AI (.PKL) ---
try:
    model_ai = joblib.load('model_rinoya_fix.pkl')
except:
    # Dummy jika file tidak ada, agar error tidak mematikan app
    model_ai = None

# --- KONFIGURASI HTTP TARGET (SESUAI ARDUINO) ---
ESP_IP = "192.168.225.68"
API_URL = f"http://{ESP_IP}/" # Endpoint sesuai kode Arduino Anda

# ==========================================
# 2. INISIALISASI SESSION STATE
# ==========================================
if 'data_log' not in st.session_state:
    st.session_state.data_log = pd.DataFrame(columns=['Gas', 'Jarak'])
if 'last_gas' not in st.session_state:
    st.session_state.last_gas = 0
if 'gas_val' not in st.session_state:
    st.session_state.gas_val = 0
if 'dist_val' not in st.session_state:
    st.session_state.dist_val = 0
if 'is_online' not in st.session_state:
    st.session_state.is_online = False
if 'last_update' not in st.session_state:
    st.session_state.last_update = time.time()
if 'last_alert_status' not in st.session_state:
    st.session_state.last_alert_status = "" 

# ==========================================
# 3. FUNGSI AMBIL DATA DARI ARDUINO
# ==========================================
def get_sensor_data():
    try:
        # Request ke http://192.168.225.68/data
        # Timeout 1 detik agar UI tidak hang jika ESP mati
        response = requests.get(API_URL, timeout=1)
        
        if response.status_code == 200:
            # Parsing JSON dari Arduino: {"gas":xxx, "distance":xxx}
            data = response.json()
            
            gas_in = int(data['gas'])
            dist_in = int(data['jarak'])
            
            st.session_state.gas_val = gas_in
            st.session_state.dist_val = dist_in
            st.session_state.is_online = True
            st.session_state.last_update = time.time()
        else:
            st.session_state.is_online = False
            
    except Exception as e:
        # Jika gagal connect (ESP mati / beda network)
        st.session_state.is_online = False
        # Debugging (bisa dihapus nanti)
        # print(f"Error connecting: {e}")

# JALANKAN FUNGSI PENGAMBILAN DATA
get_sensor_data()

# ==========================================
# 4. SIDEBAR KONTROL
# ==========================================
with st.sidebar:
    st.header("📡 Status Perangkat")
    
    # Indikator Online/Offline
    if st.session_state.is_online:
        st.success(f"🟢 ONLINE")
        st.caption(f"Terhubung ke: {ESP_IP}")
        st.caption(f"Last ping: {datetime.datetime.now().strftime('%H:%M:%S')}")
    else:
        st.error("🔴 OFFLINE")
        st.caption(f"Gagal menghubungi {ESP_IP}")
        st.caption("Pastikan Laptop & ESP di WiFi yang sama")

    st.markdown("---")
    
    st.header("⚙️ Kalibrasi Sistem")
    set_batas_penuh = st.slider("📏 Batas Jarak Penuh (cm)", 2, 15, 5)
    set_batas_gas = st.slider("🌫️ Ambang Batas Bau (PPM)", 300, 3000, 2500) # Default disesuaikan dgn kode arduino

    st.markdown("---")
    if st.button("🗑️ Reset Grafik Data", use_container_width=True):
        st.session_state.data_log = pd.DataFrame(columns=['Gas', 'Jarak'])
        st.rerun()

# --- CSS CUSTOM ---
st.markdown("""
    <style>
    .block-container { padding-top: 2rem !important; padding-bottom: 2rem; }
    div[data-testid="stMetric"] { background-color: rgba(38, 39, 48, 0.85); border: 1px solid rgba(255, 255, 255, 0.1); padding: 15px; border-radius: 10px; backdrop-filter: blur(5px); }
    .status-card { padding: 25px; border-radius: 15px; color: white; text-align: left; display: flex; align-items: center; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.1); }
    .status-icon { font-size: 50px; margin-right: 25px; }
    .status-text { font-size: 32px; font-weight: 800; margin: 0; line-height: 1.2; }
    .status-sub { font-size: 16px; opacity: 0.9; margin-top: 5px; font-weight: 400; }
    text { fill: white !important; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 5. LOGIKA AI & NOTIFIKASI
# ==========================================
live_gas = st.session_state.gas_val
live_dist = st.session_state.dist_val
delta_gas = live_gas - st.session_state.last_gas
st.session_state.last_gas = live_gas

input_data = np.array([[live_gas, live_dist, delta_gas]])

# Prediksi AI (Handling jika model tidak ada)
prediksi_label = 0
if model_ai:
    try:
        prediksi_label = model_ai.predict(input_data)[0]
    except:
        pass

# Logika Status
if prediksi_label == 3: 
    s_label, s_icon = "ANOMALI TERDETEKSI", "⚡"
    s_bg = "linear-gradient(135deg, #4b4b4b, #2e2e2e)"
    s_desc = "AI mendeteksi lonjakan data tidak wajar."
    current_status = "anomali"
    
elif prediksi_label == 2 or live_gas > set_batas_gas: 
    s_label, s_icon = "BAHAYA: MEMBUSUK", "☣️"
    s_bg = "linear-gradient(135deg, #D90429, #8D0801)"
    s_desc = "Segera tangani! Proses dekomposisi aktif."
    current_status = "membusuk"
    
elif prediksi_label == 1 or live_dist < set_batas_penuh: 
    s_label, s_icon = "STATUS: PENUH", "🗑️"
    s_bg = "linear-gradient(135deg, #FF9F1C, #E07A5F)"
    s_desc = "Tong penuh. Segera angkut."
    current_status = "penuh"
    
else: 
    s_label, s_icon = "STATUS: NORMAL", "🌱"
    s_bg = "linear-gradient(135deg, #2EC4B6, #218380)"
    s_desc = "Kapasitas tersedia. Udara aman."
    current_status = "normal"

# Notifikasi Toast
if current_status != st.session_state.last_alert_status:
    if current_status == "membusuk":
        st.toast("🚨 PERINGATAN: Sampah Membusuk Terdeteksi!", icon="☣️")
    elif current_status == "penuh":
        st.toast("⚠️ INFO: Tong Sampah PENUH! Silakan Angkut.", icon="🗑️")
    st.session_state.last_alert_status = current_status

# ==========================================
# 6. UI DASHBOARD
# ==========================================

# Header
col_logo, col_title, col_time = st.columns([0.25, 3, 1], gap="small", vertical_alignment="center")

with col_logo:
    try: st.image("logo.png", width=160)
    except: st.header("🖼️")

with col_title:
    st.markdown("""
        <div style="text-align: left;">
            <h1 style="margin:0; font-size: 3rem; text-shadow: 2px 2px 4px black;">RINOYA Smart Eco-Bin</h1>
            <h5 style="margin:0px 0 0 0; color: #e0e0e0;">AI-Powered Decomposition Monitoring (HTTP Mode)</h5>
        </div>
    """, unsafe_allow_html=True)

with col_time:
    st.metric("System Clock", datetime.datetime.now().strftime("%H:%M:%S"))

# Banner Status
st.markdown(f"""
    <div class="status-card" style="background: {s_bg};">
        <div class="status-icon">{s_icon}</div>
        <div>
            <p class="status-text">{s_label}</p>
            <p class="status-sub">{s_desc}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Grid Metrik
col1, col2, col3 = st.columns(3)
persen_isi = max(0, min(100, int(((28 - live_dist) / 28) * 100)))

with col1:
    st.markdown("##### 📦 Kapasitas Ruang")
    st.metric("Jarak Sensor", f"{live_dist} cm")
    st.progress(persen_isi / 100)
    if persen_isi > 90 or live_dist < set_batas_penuh:
        st.error("Overload (Penuh)")
    elif persen_isi > 70:
        st.warning("Hampir Penuh")
    else:
        st.success("Tersedia (Aman)")
    
with col2:
    st.markdown("##### 🌫️ Kualitas Udara")
    st.metric("Gas (Analog)", f"{live_gas}", delta=f"{delta_gas}")
    # Normalisasi progress bar gas (misal max 4095 untuk ESP32)
    prog_gas = min(1.0, live_gas / 4095)
    st.progress(prog_gas)
    if live_gas > set_batas_gas:
        st.error("Udara Beracun")
    elif live_gas > 1500: # Angka tengah-tengah
        st.warning("Mulai Berbau")
    else:
        st.success("Udara Segar")

with col3:
    st.markdown("##### 🧠 AI Confidence")
    # Logika dummy untuk decay score berdasarkan gas
    decay_score = min(100, int((live_gas / 3000) * 100))
    st.metric("Decay Risk", f"{decay_score}%")
    if decay_score > 70: st.error("Critical")
    elif decay_score > 30: st.warning("Warning")
    else: st.success("Safe")

# ==========================================
# 7. UPDATE GRAFIK & AUTO-REFRESH
# ==========================================
st.markdown("### 📈 Real-time Trend")

# Update Data Log untuk Grafik
new_data = pd.DataFrame({'Gas': [live_gas], 'Jarak': [live_dist]})
st.session_state.data_log = pd.concat([st.session_state.data_log, new_data], ignore_index=True)

# Batasi agar grafik tidak berat (Max 50 data terakhir)
if len(st.session_state.data_log) > 50: 
    st.session_state.data_log = st.session_state.data_log.iloc[1:]

c1, c2 = st.columns(2)
with c1: 
    st.area_chart(st.session_state.data_log[['Gas']], color="#FF4B4B", height=250)
with c2: 
    st.area_chart(st.session_state.data_log[['Jarak']], color="#2EC4B6", height=250)

# --- TOMBOL REFRESH MANUAL ---
if st.button("🔄 Paksa Refresh"):
    st.rerun()

# --- AUTO REFRESH LOGIC ---
# Menggunakan sleep dan rerun untuk melakukan polling data setiap 1 detik
time.sleep(1)
st.rerun()
