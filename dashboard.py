import streamlit as st
import pandas as pd
import requests # Library untuk request HTTP
import time

# ==========================================
# 1. KONFIGURASI
# ==========================================
st.set_page_config(page_title="Rinoya HTTP Mode", layout="wide")

# !!! GANTI INI DENGAN IP DARI SERIAL MONITOR ARDUINO !!!
# Contoh: "http://192.168.43.145/" (Jangan lupa http:// di depannya)
ESP_URL = "http://192.168.225.68/" 

# ==========================================
# 2. STATE MANAGEMENT
# ==========================================
if 'data_log' not in st.session_state:
    st.session_state['data_log'] = pd.DataFrame(columns=['Gas', 'Jarak'])
if 'last_gas' not in st.session_state:
    st.session_state['last_gas'] = 0
if 'last_jarak' not in st.session_state:
    st.session_state['last_jarak'] = 0
if 'status_koneksi' not in st.session_state:
    st.session_state['status_koneksi'] = "Mencari..."

# ==========================================
# 3. FUNGSI AMBIL DATA (HTTP GET)
# ==========================================
def ambil_data_dari_esp32():
    try:
        # Minta data ke ESP32 (Timeout 2 detik biar gak nge-hang lama)
        response = requests.get(ESP_URL, timeout=2)
        
        if response.status_code == 200:
            data = response.json() # Ubah teks JSON jadi Dictionary Python
            return data['gas'], data['jarak'], "Terhubung ✅"
        else:
            return None, None, f"Error Code: {response.status_code}"
            
    except requests.exceptions.ConnectionError:
        return None, None, "Gagal Konek (Cek IP & WiFi) ❌"
    except Exception as e:
        return None, None, f"Error: {e}"

# ==========================================
# 4. LOGIKA UTAMA
# ==========================================
# Ambil data terbaru
gas_baru, jarak_baru, status = ambil_data_dari_esp32()

# Jika data berhasil diambil
if gas_baru is not None:
    st.session_state['last_gas'] = gas_baru
    st.session_state['last_jarak'] = jarak_baru
    st.session_state['status_koneksi'] = status
    
    # Update Grafik
    new_data = pd.DataFrame({'Gas': [gas_baru], 'Jarak': [jarak_baru]})
    st.session_state['data_log'] = pd.concat([st.session_state['data_log'], new_data], ignore_index=True)
    
    if len(st.session_state['data_log']) > 50:
        st.session_state['data_log'] = st.session_state['data_log'].iloc[-50:]
else:
    # Jika gagal, tampilkan status error terakhir tapi pertahankan angka lama
    st.session_state['status_koneksi'] = status

# ==========================================
# 5. TAMPILAN DASHBOARD
# ==========================================
st.title("🌐 Rinoya Monitor (HTTP Mode)")
st.caption(f"Mengambil data dari: {ESP_URL}")

# Indikator Status
warna_status = "green" if "Terhubung" in st.session_state['status_koneksi'] else "red"
st.markdown(f"**Status Koneksi:** :{warna_status}[{st.session_state['status_koneksi']}]")

col1, col2 = st.columns(2)
col1.metric("Kadar Gas", f"{st.session_state['last_gas']} PPM")
col2.metric("Jarak Sampah", f"{st.session_state['last_jarak']} cm")

# Logic Penuh
curr_jarak = st.session_state['last_jarak']
if curr_jarak > 0 and curr_jarak < 10:
    st.error("⚠️ STATUS: PENUH (Segera Buang!)")
else:
    st.success("✅ STATUS: AMAN")

st.line_chart(st.session_state['data_log'])

# Auto Refresh halaman setiap 1 detik
time.sleep(1)
st.rerun()