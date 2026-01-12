import pandas as pd
import numpy as np
import joblib  # Library untuk menyimpan otak AI
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix

# ==========================================
# 1. PERSIAPAN DATA (LOAD DATASET)
# ==========================================
print("📂 Sedang membaca file 'dataset_training_final.csv'...")

try:
    df = pd.read_csv('dataset_training_final.csv')
except FileNotFoundError:
    print("❌ ERROR: File dataset tidak ditemukan!")
    print("   Pastikan Anda sudah menjalankan kode pembuat dataset sebelumnya.")
    exit()

# Cek apakah kolomnya benar
required_columns = ['Gas', 'Jarak', 'Delta_Gas', 'Label']
if not all(col in df.columns for col in required_columns):
    print(f"❌ ERROR: Kolom dataset salah! Harus ada: {required_columns}")
    exit()

print(f"✅ Dataset berhasil dimuat: {len(df)} baris data.")

# ==========================================
# 2. MEMISAHKAN FITUR & KUNCI JAWABAN
# ==========================================
# X = Data yang dipelajari (Soal)
# y = Label/Status (Kunci Jawaban)
X = df[['Gas', 'Jarak', 'Delta_Gas']]
y = df['Label']

# Bagi data: 80% untuk Latihan (Training), 20% untuk Ujian (Testing)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

print(f"📊 Data Latih: {len(X_train)} baris | Data Uji: {len(X_test)} baris")

# ==========================================
# 3. PROSES LATIHAN (TRAINING)
# ==========================================
print("\n🧠 Sedang melatih model AI (Random Forest)...")

# Kita gunakan Random Forest karena bagus untuk data sensor yang 'berisik'
# n_estimators=100 artinya kita pakai 100 'pohon keputusan' agar akurat
model = RandomForestClassifier(n_estimators=100, random_state=42)

# Inilah proses 'belajar' yang sebenarnya
model.fit(X_train, y_train)

print("✅ Proses latihan selesai!")

# ==========================================
# 4. EVALUASI (UJIAN)
# ==========================================
print("\n📝 Sedang melakukan evaluasi akurasi...")

# Minta AI memprediksi data ujian (yang belum pernah dia lihat)
y_pred = model.predict(X_test)

# Hitung nilainya
akurasi = accuracy_score(y_test, y_pred)
laporan = classification_report(y_test, y_pred, target_names=['Aman', 'Penuh', 'Membusuk', 'Anomali'])

print(f"🏆 Akurasi Model: {akurasi * 100:.2f}%")
print("\nDetail Laporan Kinerja:")
print(laporan)

# ==========================================
# 5. SIMPAN OTAK AI (SAVE MODEL)
# ==========================================
print("💾 Menyimpan model ke file 'model_sampah.pkl'...")
joblib.dump(model, 'model_sampah.pkl')

print("\n🎉 SUKSES! File 'model_sampah.pkl' sudah jadi.")
print("   Sekarang Anda bisa menghubungkannya ke Dashboard Streamlit.")