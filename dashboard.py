import streamlit as st
import pandas as pd
import time
import joblib
import numpy as np
import requests # Library HTTP
import datetime
import warnings


# 0. KONFIGURASI HALAMAN
warnings.filterwarnings("ignore")

st.set_page_config(
    page_title="Rinoya Smart Eco-Bin",
    page_icon="logo.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 1. KONFIGURASI KONEKSI (HTTP)
# GANTI IP INI SESUAI ARDUINO ANDA
ESP_IP = "172.20.10.3" 
API_URL = f"http://{ESP_IP}/data" 

# BATAS AMAN
LIMIT_JARAK_PENUH = 5   # cm
LIMIT_GAS_BAU = 2500    # Analog Value

# 2. LOAD MODEL AI
try:
    model_ai = joblib.load('model_rinoya_fix.pkl')
except:
    model_ai = None

# 3. SESSION STATE
if 'data_log' not in st.session_state:
    st.session_state.data_log = pd.DataFrame(columns=['Waktu', 'Gas', 'Jarak', 'Status'])
if 'start_time' not in st.session_state:
    st.session_state.start_time = time.time()
if 'last_gas' not in st.session_state:
    st.session_state.last_gas = 0
if 'gas_val' not in st.session_state:
    st.session_state.gas_val = 0
if 'dist_val' not in st.session_state:
    st.session_state.dist_val = 0
if 'is_online' not in st.session_state:
    st.session_state.is_online = False
if 'last_alert_status' not in st.session_state:
    st.session_state.last_alert_status = "" 

# 4. FUNGSI AMBIL DATA
def get_sensor_data():
    try:
        response = requests.get(API_URL, timeout=1.5)
        if response.status_code == 200:
            data = response.json()
            st.session_state.gas_val = int(data.get('gas', 0))
            st.session_state.dist_val = int(data.get('distance', 0))
            st.session_state.is_online = True
            return True
    except: pass
    st.session_state.is_online = False
    return False

get_sensor_data()

# 5. SIDEBAR (TEMA & DATA)
with st.sidebar:
    
    # --- FITUR TEMA (TERANG/GELAP) ---
    st.header("Tampilan")
    theme_mode = st.toggle("🌙 Mode Gelap", value=True) # Default ON
    
    st.markdown("---")
    st.header("Status Koneksi")
    
    # Cek dulu status koneksinya (Online/Offline)
    if st.session_state.is_online:
    # === BAGIAN JIKA ONLINE ===
        st.success("🟢 ONLINE")
        st.caption(f"IP: {ESP_IP}")
    
    # Fitur Tambahan: Cek Status OLED (Hanya jalan kalau Online)
        try:
            response = requests.get(API_URL, timeout=1.5)
            if response.status_code == 200:
                data = response.json()
            # Ambil status oled, default 'unknown' jika tidak ada
                oled_status = data.get('status', 'unknown')
            
                if oled_status == 'full':
                    st.warning("🖥️ OLED: FULL Display")
                else:
                    st.info("🖥️ OLED: IDLE Display")
        except:
            pass # Jika gagal ambil data OLED, diam saja (jangan bikin error)

    else:
    # === BAGIAN JIKA OFFLINE ===
        st.error("🔴 OFFLINE")
        st.caption("Cek koneksi WiFi dan IP Address")

    st.markdown("---")
    st.header("Statistik Sesi")
    uptime_seconds = int(time.time() - st.session_state.start_time)
    uptime_str = str(datetime.timedelta(seconds=uptime_seconds))
    st.info(f"⏱️ **Uptime:**\n{uptime_str}")

    total_data = len(st.session_state.data_log)
    peak_gas = st.session_state.data_log['Gas'].max() if total_data > 0 else 0
    st.write(f"📝 Data: **{total_data}**")
    st.write(f"🔥 Peak Gas: **{peak_gas}**")

    st.markdown("---")
    st.header("Download")
    if not st.session_state.data_log.empty:
        csv = st.session_state.data_log.to_csv(index=False).encode('utf-8')
        curr_date = datetime.datetime.now().strftime("%Y-%m-%d")
        st.download_button("📄 Unduh CSV", csv, f"Log_{curr_date}.csv", "text/csv")

    if st.button("🗑️ Hapus Cache"):
        st.session_state.data_log = pd.DataFrame(columns=['Waktu', 'Gas', 'Jarak', 'Status'])
        st.session_state.start_time = time.time()
        st.rerun()

    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: grey; font-size: 12px;'>
            <b>Rinoya Smart Eco-Bin</b><br>
            © 2025 Rinoya Team.<br>All Rights Reserved.
        </div>
        """, unsafe_allow_html=True
    )

# 6. PENGATURAN CSS (WARNA SOLID)

if theme_mode:
    # --- WARNA GELAP (SOLID) ---
    main_bg = "#0E1117" # Warna background gelap default Streamlit
    metric_bg = "#262730"
    metric_border = "#41444C"
    text_color = "white"
    chart_text_color = "white"
    sub_color = "#e0e0e0"
else:
    # --- WARNA TERANG (SOLID) ---
    main_bg = "#FFFFFF"
    metric_bg = "#F0F2F6"
    metric_border = "#D3D3D3"
    text_color = "#31333F"
    chart_text_color = "#31333F"
    sub_color = "#666666"

# INJECT CSS
st.markdown(f"""
    <style>
    /* Mengubah warna background utama */
    .stApp {{
        background-color: {main_bg};
    }}
    
    .block-container {{ padding-top: 2rem !important; padding-bottom: 2rem; }}
    
    /* Style Kotak Metric (Angka) */
    div[data-testid="stMetric"] {{ 
        background-color: {metric_bg}; 
        border: 1px solid {metric_border}; 
        padding: 15px; 
        border-radius: 10px; 
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }}
    
    /* Paksa warna text di dalam metric */
    div[data-testid="stMetric"] label {{ color: {text_color} !important; }}
    div[data-testid="stMetric"] div {{ color: {text_color} !important; }}

    /* Style Kartu Status Utama */
    .status-card {{ 
        padding: 25px; 
        border-radius: 15px; 
        color: white; 
        text-align: left; 
        display: flex; 
        align-items: center; 
        margin-bottom: 25px; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.2); 
    }}
    .status-icon {{ font-size: 50px; margin-right: 25px; }}
    .status-text {{ font-size: 32px; font-weight: 800; margin: 0; line-height: 1.2; color: white !important; }}
    .status-sub {{ font-size: 16px; opacity: 0.9; margin-top: 5px; font-weight: 400; color: white !important; }}
    
    /* Warna Text Chart */
    text {{ fill: {chart_text_color} !important; }}
    </style>
    """, unsafe_allow_html=True)

# 7. LOGIKA AI & STATUS
live_gas = st.session_state.gas_val
live_dist = st.session_state.dist_val
delta_gas = live_gas - st.session_state.last_gas
st.session_state.last_gas = live_gas

# Prediksi AI
prediksi_label = 0
if model_ai:
    try:
        input_data = np.array([[live_gas, live_dist, delta_gas]])
        prediksi_label = model_ai.predict(input_data)[0]
    except: pass

# Logic Status
if prediksi_label == 3: 
    s_label, s_icon = "ANOMALI TERDETEKSI", "⚡"
    s_bg = "linear-gradient(135deg, #4b4b4b, #2e2e2e)"
    s_desc = "AI mendeteksi lonjakan data tidak wajar."
    current_status = "anomali"
elif prediksi_label == 2 or live_gas > LIMIT_GAS_BAU: 
    s_label, s_icon = "BAHAYA: MEMBUSUK", "☣️"
    s_bg = "linear-gradient(135deg, #D90429, #8D0801)"
    s_desc = "Segera tangani! Proses dekomposisi aktif."
    current_status = "membusuk"
elif prediksi_label == 1 or live_dist < LIMIT_JARAK_PENUH: 
    s_label, s_icon = "STATUS: PENUH", "🗑️"
    s_bg = "linear-gradient(135deg, #FF9F1C, #E07A5F)"
    s_desc = "Tong penuh. Segera angkut."
    current_status = "penuh"
else: 
    s_label, s_icon = "STATUS: NORMAL", "🌱"
    s_bg = "linear-gradient(135deg, #2EC4B6, #218380)"
    s_desc = "Kapasitas tersedia. Udara aman."
    current_status = "normal"

if current_status != st.session_state.last_alert_status:
    if current_status == "membusuk": st.toast("🚨 Sampah Membusuk!", icon="☣️")
    elif current_status == "penuh": st.toast("⚠️ Tong Penuh!", icon="🗑️")
    st.session_state.last_alert_status = current_status

# 8. DASHBOARD HEADER
col_logo, col_title, col_time = st.columns([0.25, 3, 1], gap="small", vertical_alignment="center")

with col_logo:
    try: st.image("logo.png", width=120)
    except: st.header("🖼️")

with col_title:
    st.markdown(f"""
        <div style="text-align: left;">
            <h1 style="margin:0; font-size: 3rem; text-shadow: none; color: {text_color};">RINOYA Smart Eco-Bin</h1>
            <h5 style="margin:5px 0 0 0; color: {sub_color};">AI-Powered Decomposition Monitoring</h5>
        </div>
    """, unsafe_allow_html=True)

with col_time:
    st.metric("System Time", time.strftime("%H:%M:%S"))

# 9. BANNER & METRIK
st.markdown(f"""
    <div class="status-card" style="background: {s_bg};">
        <div class="status-icon">{s_icon}</div>
        <div>
            <p class="status-text">{s_label}</p>
            <p class="status-sub">{s_desc}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
persen_isi = max(0, min(100, int(((30 - live_dist) / 30) * 100)))

with col1:
    st.markdown(f"##### 📦 Kapasitas Ruang") 
    st.metric("Jarak Sensor", f"{live_dist} cm")
    st.progress(persen_isi / 100)
    if persen_isi > 90 or live_dist < LIMIT_JARAK_PENUH: st.error("Overload (Penuh)")
    elif persen_isi > 70: st.warning("Hampir Penuh")
    else: st.success("Tersedia (Aman)")

with col2:
    st.markdown(f"##### 🌫️ Kualitas Udara")
    st.metric("Gas (Analog)", f"{live_gas}", delta=f"{delta_gas}")
    st.progress(min(1.0, live_gas / 4095))
    if live_gas > LIMIT_GAS_BAU: st.error("Udara Beracun")
    elif live_gas > (LIMIT_GAS_BAU * 0.7): st.warning("Mulai Berbau")
    else: st.success("Udara Segar")

with col3:
    st.markdown(f"##### 🧠 AI Confidence")
    decay_score = min(100, int((live_gas / LIMIT_GAS_BAU) * 100)) if live_gas > 300 else 0
    st.metric("Decay Risk", f"{decay_score}%")
    if decay_score > 80: st.error("Critical")
    elif decay_score > 40: st.warning("Warning")
    else: st.success("Safe")

# 10. GRAFIK & LOOP
st.markdown(f"### 📈 Real-time Trend")

timestamp_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
new_data = pd.DataFrame({
    'Waktu': [timestamp_str],
    'Gas': [live_gas], 
    'Jarak': [live_dist],
    'Status': [s_label]
})

st.session_state.data_log = pd.concat([st.session_state.data_log, new_data], ignore_index=True)
chart_data = st.session_state.data_log.tail(50)

c1, c2 = st.columns(2)
with c1: st.area_chart(chart_data[['Gas']], color="#FF4B4B", height=250)
with c2: st.area_chart(chart_data[['Jarak']], color="#2EC4B6", height=250)

time.sleep(1)
st.rerun()