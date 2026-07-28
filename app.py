import streamlit as st
import sqlite3
import pandas as pd

st.set_page_config(page_title="Otomol SQL Stok", page_icon="🗄️", layout="wide")

st.title("🗄️ SQL Veri Tabanı Bağlantılı Stok Paneli")
st.caption("Veriler tamamen ücretsiz SQLite SQL veri tabanından anlık çekilmektedir.")
st.write("---")

# --- SQL VERİ TABANI AYARLARI ---
DB_NAME = "stok.db"

def vt_baglan():
    """SQL veri tabanına bağlanır."""
    return sqlite3.connect(DB_NAME)

def vt_altyapi_kur():
    """Eğer yoksa stok tablosunu SQL içinde otomatik oluşturur."""
    conn = vt_baglan()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stoklar (
            parca_kodu TEXT PRIMARY KEY,
            parca_adi TEXT NOT NULL,
            marka TEXT,
            stok_adedi INTEGER DEFAULT 0,
            raf_no TEXT
        )
    """)
    conn.commit()
    conn.close()

# Altyapıyı çalıştır (Uygulama açılırken kontrol eder)
vt_altyapi_kur()
# --------------------------------

# SQL'deki tüm verileri çekip Pandas DataFrame'e dönüştürme fonksiyonu
def veriyi_yukle_sql():
    conn = vt_baglan()
    df = pd.read_sql_query("SELECT * FROM stoklar", conn)
    conn.close()
    return df

df = veriyi_yukle_sql()

sol_kolon, sag_kolon = st.columns([1, 2])

with sol_kolon:
    st.subheader("🛠️ SQL Stok İşlemleri")
    islem = st.radio("Yapmak istediğiniz işlem:", ["Parça Sorgula", "Yeni Parça Ekle", "Stok Adedi Güncelle"])
    
    if islem == "Parça Sorgula":
        aranan_kod = st.text_input("Orijinal Parça Kodu:")
        if st.button("SQL'de Sorgula", use_container_width=True):
            if aranan_kod:
                conn = vt_baglan()
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM stoklar WHERE parca_kodu = ?", (aranan_kod,))
                parca = cursor.fetchone()
                conn.close()
                
                if parca:
                    st.info(f"**{parca[1]}** ({parca[2]}) - Raf: {parca[4]}")
                    st.metric(label="Mevcut Stok", value=f"{parca[3]} Adet")
                else:
                    st.error("Parça kodu SQL'de bulunamadı.")
            else:
                st.error("Lütfen bir parça kodu girin.")
                
    elif islem == "Yeni Parça Ekle":
        yeni_kod = st.text_input("Parça Kodu (Örn: 8W0915105B):")
        yeni_ad = st.text_input("Parça Adı:")
        yeni_marka = st.selectbox("Marka:", ["Volkswagen", "Audi", "Seat", "Skoda", "BMW"])
        yeni_adet = st.number_input("Başlangıç Stoğu:", min_value=0, value=0, step=1)
        yeni_raf = st.text_input("Raf Konumu (Örn: A-01):")
        
        if st.button("SQL Veri Tabanına Yaz", use_container_width=True):
            if yeni_kod and yeni_ad:
                try:
                    conn = vt_baglan()
                    cursor = conn.cursor()
                    # Gerçek SQL INSERT sorgusu
                    cursor.execute("""
                        INSERT INTO stoklar (parca_kodu, parca_adi, marka, stok_adedi, raf_no)
                        VALUES (?, ?, ?, ?, ?)
                    """, (yeni_kod, yeni_ad, yeni_marka, yeni_adet, yeni_raf))
                    conn.commit()
                    conn.close()
                    st.success("✓ Yeni parça SQL veri tabanına başarıyla eklendi!")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.warning("Bu parça kodu SQL veri tabanında zaten mevcut!")
            else:
                st.error("Lütfen gerekli alanları doldurun.")

    elif islem == "Stok Adedi Güncelle":
        guncellenecek_kod = st.text_input("Stok Adedi Güncellenecek Parça Kodu:")
        yeni_stok_adedi = st.number_input("Yeni Stok Adedi:", min_value=0, value=0, step=1)
        
        if st.button("SQL Stoğunu Güncelle", use_container_width=True):
            conn = vt_baglan()
            cursor = conn.cursor()
            # Gerçek SQL UPDATE sorgusu
            cursor.execute("UPDATE stoklar SET stok_adedi = ? WHERE parca_kodu = ?", (yeni_stok_adedi, guncellenecek_kod))
            conn.commit()
            
            if cursor.rowcount > 0:
                st.success("✓ SQL üzerindeki stok adedi başarıyla güncellendi!")
                conn.close()
                st.rerun()
            else:
                st.error("Girdiğiniz parça kodu SQL listesinde bulunamadı.")
                conn.close()

with sag_kolon:
    st.subheader("📋 SQL Güncel Stok Listesi")
    if not df.empty:
        # Sütun isimlerini şık gösterelim
        df.columns = ["Parça Kodu", "Parça Adı", "Marka", "Stok Adedi", "Raf No"]
        st.dataframe(df, use_container_width=True, height=500)
    else:
        st.info("SQL veri tabanı şu an boş. Sol taraftan ilk parçayı ekleyerek başlayabilirsiniz.")