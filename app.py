import streamlit as st
import sqlite3
import pandas as pd

st.set_page_config(page_title="Otomol Yönetim Paneli", page_icon="⚙️", layout="wide")

# --- KULLANICI GİRİŞ KONTROLÜ ---
def giris_ekrani():
    st.markdown("<style>.stApp { max-width: 450px; margin: 0 auto; padding-top: 50px; }</style>", unsafe_allow_html=True)
    st.title("🔐 Kurumsal Giriş")
    st.caption("Otomol Merkezi Stok Yönetim Sistemi")
    st.write("---")
    
    kullanici = st.text_input("Kullanıcı Adı:")
    sifre = st.text_input("Şifre:", type="password")
    
    if st.button("Giriş Yap", use_container_width=True):
        yetkili_kullanicilar = {
            "ramazan": "otomol123",
            "alibey": "otomol2026",
            "kerim": "stok456"
        }
        
        if kullanici in yetkili_kullanicilar and yetkili_kullanicilar[kullanici] == sifre:
            st.session_state.giris_basarili = True
            st.session_state.aktif_kullanici = kullanici
            st.success("Giriş başarılı!")
            st.rerun()
        else:
            st.error("❌ Hatalı kullanıcı adı veya şifre!")

if 'giris_basarili' not in st.session_state:
    giris_ekrani()
    st.stop()
# ---------------------------------

# --- GÜVENLİ ÇIKIŞ ---
st.sidebar.markdown(f"👤 **Kullanıcı:** {st.session_state.aktif_kullanici.upper()}")
if st.sidebar.button("Güvenli Çıkış"):
    del st.session_state.giris_basarili
    st.rerun()

st.title("📦 Gelişmiş Stok Yönetim Paneli")
st.caption("Otomol Otomotiv - Tam Fonksiyonlu SQL Yönetimi")
st.write("---")

DB_NAME = "stok.db"

def vt_baglan():
    return sqlite3.connect(DB_NAME)

def vt_alta_yapi_kur():
    conn = vt_baglan()
    cursor = conn.cursor()
    # Stok tablosu
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

vt_alta_yapi_kur()

def veriyi_yukle_sql():
    conn = vt_baglan()
    df = pd.read_sql_query("SELECT * FROM stoklar", conn)
    conn.close()
    return df

df = veriyi_yukle_sql()

sol_kolon, sag_kolon = st.columns([1, 2])

with sol_kolon:
    st.subheader("🛠️ SQL Stok İşlemleri")
    islem = st.radio("Yapmak istediğiniz işlem:", ["Parça Sorgula", "Yeni Parça Ekle", "Stok Adedi Güncelle", "Parça Kartı Sil"])
    
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
                    cursor.execute("INSERT INTO stoklar VALUES (?, ?, ?, ?, ?)", (yeni_kod, yeni_ad, yeni_marka, yeni_adet, yeni_raf))
                    conn.commit()
                    conn.close()
                    st.success("✓ Yeni parça başarıyla eklendi!")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.warning("Bu parça kodu zaten mevcut!")
            else:
                st.error("Lütfen gerekli alanları doldurun.")

    elif islem == "Stok Adedi Güncelle":
        guncellenecek_kod = st.text_input("Stok Adedi Güncellenecek Parça Kodu:")
        yeni_stok_adedi = st.number_input("Yeni Stok Adedi:", min_value=0, value=0, step=1)
        
        if st.button("SQL Stoğunu Güncelle", use_container_width=True):
            conn = vt_baglan()
            cursor = conn.cursor()
            cursor.execute("UPDATE stoklar SET stok_adedi = ? WHERE parca_kodu = ?", (yeni_stok_adedi, guncellenecek_kod))
            conn.commit()
            if cursor.rowcount > 0:
                st.success("✓ Stok adedi başarıyla güncellendi!")
                conn.close()
                st.rerun()
            else:
                st.error("Parça kodu bulunamadı.")
                conn.close()

    elif islem == "Parça Kartı Sil":
        silinecek_kod = st.text_input("Sistemden Tamamen Silinecek Parça Kodu:")
        
        # Yanlışlıkla silmeyi önlemek için onay kutusu (Kurumsal kontrol)
        onay = st.checkbox("Bu parçayı sistemden kalıcı olarak silmek istediğime eminim.")
        
        if st.button("Parçayı SQL'den Sil", use_container_width=True):
            if onay:
                if silinecek_kod:
                    conn = vt_baglan()
                    cursor = conn.cursor()
                    # Gerçek SQL DELETE sorgusu
                    cursor.execute("DELETE FROM stoklar WHERE parca_kodu = ?", (silinecek_kod,))
                    conn.commit()
                    
                    if cursor.rowcount > 0:
                        st.success(f"✓ {silinecek_kod} kodlu parça veri tabanından kalıcı olarak silindi!")
                        conn.close()
                        st.rerun()
                    else:
                        st.error("Silinmek istenen parça kodu veri tabanında bulunamadı.")
                        conn.close()
                else:
                    st.error("Lütfen silinecek parça kodunu girin.")
            else:
                st.warning("🚨 Lütfen önce yukarıdaki onay kutusunu işaretleyin!")

with sag_kolon:
    st.subheader("📋 SQL Güncel Stok Listesi")
    if not df.empty:
        df.columns = ["Parça Kodu", "Parça Adı", "Marka", "Stok Adedi", "Raf No"]
        st.dataframe(df, use_container_width=True, height=500)
    else:
        st.info("SQL veri tabanı şu an boş. Sol taraftan ilk parçayı ekleyerek başlayabilirsiniz.")
