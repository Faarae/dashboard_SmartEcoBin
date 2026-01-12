import streamlit as st
import pandas as pd
import time
import base64
import joblib
import numpy as np
import paho.mqtt.client as mqtt

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
    st.error("❌ ERROR: File 'model_rinoya_fix.pkl' tidak ditemukan.")
    st.stop()

# --- KONFIGURASI MQTT ---
BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC = "rinoya/sic7/data"

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
if 'mqtt_connected' not in st.session_state:
    st.session_state.mqtt_connected = False

# ==========================================
# 3. MQTT & SIDEBAR SETUP
# ==========================================
def on_message(client, userdata, message):
    try:
        payload = str(message.payload.decode("utf-8"))
        data = payload.split(',')
        st.session_state.gas_val = int(data[0])
        st.session_state.dist_val = int(data[1])
        st.session_state.mqtt_connected = True
    except: pass

if 'client' not in st.session_state:
    client = mqtt.Client()
    client.on_message = on_message
    try:
        client.connect(BROKER, PORT)
        client.subscribe(TOPIC)
        client.loop_start()
        st.session_state.client = client
    except: pass

# --- SIDEBAR KONTROL ---
with st.sidebar:
    # A. STATUS KONEKSI (VISUAL)
    st.header("📡 Status Perangkat")
    
    # Logic: Jika tidak ada data > 10 detik, anggap Offline
    time_diff = time.time() - st.session_state.last_update
    is_online = st.session_state.mqtt_connected and (time_diff < 15)
    
    if is_online:
        st.success("🟢 ONLINE (Terhubung)")
        st.caption(f"Update terakhir: {int(time_diff)} detik lalu")
    else:
        st.error("🔴 OFFLINE (Terputus)")
        st.caption("Cek daya ESP32 atau WiFi")

    st.markdown("---")
    
    # B. KALIBRASI SISTEM (FITUR TAMBAHAN)
    st.header("⚙️ Kalibrasi Sistem")
    st.info("Atur sensitivitas sensor sesuai kondisi lapangan.")
    
    # Slider 1: Batas Penuh
    set_batas_penuh = st.slider("📏 Batas Jarak Penuh (cm)", 
                                min_value=2, max_value=15, value=5, 
                                help="Jika jarak sensor < nilai ini, maka dianggap PENUH.")
    
    # Slider 2: Batas Gas
    set_batas_gas = st.slider("🌫️ Ambang Batas Bau (PPM)", 
                              min_value=300, max_value=1500, value=800, step=50,
                              help="Jika gas > nilai ini, maka peringatan MEMBUSUK aktif.")

    st.markdown("---")
    
    # C. TOMBOL RESET
    if st.button("🗑️ Reset Grafik Data", use_container_width=True):
        st.session_state.data_log = pd.DataFrame(columns=['Gas', 'Jarak'])
        st.rerun()

    st.caption("Rinoya Project © 2026")

# --- CSS CUSTOM ---
st.markdown("""
    <style>
    .block-container { padding-top: 3rem !important; padding-bottom: 2rem; }
    div[data-testid="stMetric"] { background-color: rgba(38, 39, 48, 0.85); border: 1px solid rgba(255, 255, 255, 0.1); padding: 15px; border-radius: 10px; backdrop-filter: blur(5px); }
    .status-card { padding: 25px; border-radius: 15px; color: white; text-align: left; display: flex; align-items: center; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.1); }
    .status-icon { font-size: 50px; margin-right: 25px; }
    .status-text { font-size: 32px; font-weight: 800; margin: 0; line-height: 1.2; }
    .status-sub { font-size: 16px; opacity: 0.9; margin-top: 5px; font-weight: 400; }
    text { fill: white !important; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 4. LOGIKA AI & NOTIFIKASI
# ==========================================
live_gas = st.session_state.gas_val
live_dist = st.session_state.dist_val
delta_gas = live_gas - st.session_state.last_gas
st.session_state.last_gas = live_gas

input_data = np.array([[live_gas, live_dist, delta_gas]])
prediksi_label = model_ai.predict(input_data)[0]

if prediksi_label == 3: # ANOMALI
    s_label, s_icon = "ANOMALI TERDETEKSI", "⚡"
    s_bg = "linear-gradient(135deg, #4b4b4b, #2e2e2e)"
    s_desc = "AI mendeteksi lonjakan data tidak wajar."
    
elif prediksi_label == 2: # MEMBUSUK
    s_label, s_icon = "BAHAYA: MEMBUSUK", "☣️"
    s_bg = "linear-gradient(135deg, #D90429, #8D0801)"
    s_desc = "Segera tangani! Proses dekomposisi aktif."
    st.toast("🚨 PERINGATAN: Sampah Membusuk Terdeteksi!", icon="☣️")
    
elif prediksi_label == 1: # PENUH (KERING)
    s_label, s_icon = "STATUS: PENUH", "🗑️"
    s_bg = "linear-gradient(135deg, #FF9F1C, #E07A5F)"
    s_desc = "Tong penuh (Sampah Kering). Segera angkut."
    st.toast("⚠️ INFO: Tong Sampah PENUH! Silakan Angkut.", icon="🗑️")
    
else: # AMAN
    s_label, s_icon = "STATUS: NORMAL", "🌱"
    s_bg = "linear-gradient(135deg, #2EC4B6, #218380)"
    s_desc = "Kapasitas tersedia. Udara aman."

# ==========================================
# 5. UI DASHBOARD
# ==========================================

# --- REVISI 1: KOLOM HEADER LEBIH RAPAT ---
# Logo dipersempit (0.2), Judul dilebarkan (3) agar jaraknya dekat
col_logo, col_title, col_time = st.columns([0.25, 3, 1], gap="small", vertical_alignment="center")

with col_logo:
    st.image("logo.png", width=160)

with col_title:
    st.markdown("""
        <div style="text-align: left;">
            <h1 style="margin:0; font-size: 3rem; text-shadow: 2px 2px 4px black;">RINOYA Smart Eco-Bin</h1>
            <h5 style="margin:0px 0 0 0; color: #e0e0e0;">AI-Powered Decomposition Monitoring</h5>
        </div>
    """, unsafe_allow_html=True)

with col_time:
    st.metric("System Time", time.strftime("%H:%M:%S"))

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

# --- REVISI 2: LABEL INDIKATOR DI SEMUA KOLOM ---

with col1:
    st.markdown("##### 📦 Kapasitas Ruang")
    st.metric("Jarak Sensor", f"{live_dist} cm")
    st.progress(persen_isi / 100)
    
    # Label Status Kapasitas (Baru)
    if persen_isi > 90:
        st.error("Overload (Penuh)")
    elif persen_isi > 70:
        st.warning("Hampir Penuh")
    else:
        st.success("Tersedia (Aman)")
    
with col2:
    st.markdown("##### 🌫️ Kualitas Udara")
    st.metric("Gas (MQ135)", f"{live_gas} PPM", delta=f"{delta_gas}")
    st.progress(min(1.0, live_gas / 1500))
    
    # Label Status Gas (Baru)
    if live_gas > 1000:
        st.error("Udara Beracun")
    elif live_gas > 400:
        st.warning("Mulai Berbau")
    else:
        st.success("Udara Segar")

with col3:
    st.markdown("##### 🧠 AI Confidence")
    decay_score = min(100, int((live_gas - 300) / 800 * 100)) if live_gas > 300 else 0
    st.metric("Decay Risk", f"{decay_score}%")
    
    # Label Status Pembusukan (Sudah ada)
    if decay_score > 70: st.error("Critical")
    elif decay_score > 30: st.warning("Warning")
    else: st.success("Safe")

# Grafik
st.markdown("### 📈 Real-time Trend")
new_data = pd.DataFrame({'Gas': [live_gas], 'Jarak': [live_dist]})
st.session_state.data_log = pd.concat([st.session_state.data_log, new_data], ignore_index=True)
if len(st.session_state.data_log) > 50: 
    st.session_state.data_log = st.session_state.data_log.iloc[1:]

c1, c2 = st.columns(2)
with c1: st.area_chart(st.session_state.data_log[['Gas']], color="#FF4B4B", height=250)
with c2: st.area_chart(st.session_state.data_log[['Jarak']], color="#2EC4B6", height=250)

time.sleep(1)
st.rerun()