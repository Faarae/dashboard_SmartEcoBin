def on_message(client, userdata, message):
    try:
        payload = str(message.payload.decode("utf-8"))
        print(f"🔵 MQTT Received: {payload}")  # ← TAMBAHKAN INI
        
        data = payload.split(',')
        st.session_state.gas_val = int(data[0])
        st.session_state.dist_val = int(data[1])
        st.session_state.mqtt_connected = True
        st.session_state.last_update = time.time()
        
        print(f"✓ Parsed: Gas={data[0]}, Jarak={data[1]}")  # ← TAMBAHKAN INI
    except Exception as e:
        print(f"❌ MQTT Error: {e}")  # ← TAMBAHKAN INI