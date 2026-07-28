import streamlit as st
import sqlite3
import pandas as pd

st.set_page_config(page_title="Otomol Sayım Sistemi", page_icon="📝", layout="wide")

DB_NAME = "stok_sayim.db"

def vt_baglan():
    return sqlite3.connect(DB_NAME)

def vt_altyapi_kur():
    conn = vt_baglan()
    cursor = conn.cursor()
    
    # 1. Personel Tanımlama Tablosu
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS personel (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            personel_adi TEXT NOT NULL,
            sube TEXT NOT NULL,
            yetkili_marka TEXT NOT NULL
        )
    """)
    
    # 2. Marka Bağlantılı Parça Master Tablosu
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS parca_master (
            parca_kodu TEXT PRIMARY KEY,
            parca_adi TEXT NOT NULL,
            marka TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# Altyapıyı oluştur
vt_altyapi_kur()

# --- KULLANICI GİRİŞ KONTROLÜ ---
def giris_ekrani():
    st.markdown("<style>.stApp { max-width: 450px; margin: 0 auto; padding-top: 50px; }</style>", unsafe_allow_html=True)
    st.title("🔐 Sayım Sistemi Giriş")
    st.caption("Otomol Otomotiv Yetkili Servis")
    st.write("---")
    
    kullanici = st.text_input("Kullanıcı Adı:").lower().strip()
    sifre = st.text_input("Şifre:", type="password")
    
    if st.button("Sistem Girişi", use_container_width=True):
        yetkili_kullanicilar = {
            "ramazan": "otomol123",
            "kerim": "stok456"
        }
        
        if kullanici in yetkili_kullanicilar and yetkili_kullanicilar[kullanici] == sifre:
            st.session_state.giris_basarili = True
            st.session_state.aktif_kullanici = kullanici
            st.success("Giriş başarılı!")
            st.rerun()
        else:
            st.error("❌ Yetkisiz kullanıcı veya hatalı şifre!")

if 'giris_basarili' not in st.session_state:
    giris_ekrani()
    st.stop()
# ---------------------------------

# --- GÜVENLİ ÇIKŞ ---
st.sidebar.markdown(f"👤 **Aktif Kullanıcı:** {st.session_state.aktif_kullanici.upper()}")
if st.sidebar.button("Güvenli Çıkış"):
    del st.session_state.giris_basarili
    st.rerun()

# --- ROL KONTROLÜ VE EKRANLAR ---

# 1. RAMAZAN'IN EKRANI (ADMİN / YÖNETİM SAYFASI)
if st.session_state.aktif_kullanici == "ramazan":
    st.title("⚙️ Merkezi Yönetim & Tanımlama Paneli")
    st.caption("Bu sayfaya sadece RAMAZAN erişim sağlayabilir.")
    st.write("---")
    
    sekme1, sekme2 = st.tabs(["👤 Personel Yetkilendirme", "📦 Marka & Parça Tanımlama"])
    
    with sekme1:
        st.subheader("Yeni Personel Tanımla")
        p_adi = st.text_input("Personel Adı Soyadı (Örn: Kerim):")
        p_sube = st.selectbox("Görev Yapacağı Şube:", ["Antalya", "İstanbul", "İzmir"])
        p_marka = st.selectbox("Yetkili Olacağı Marka:", ["Volkswagen", "Audi", "Seat", "Skoda", "BMW"])
        
        if st.button("Personeli Kaydet", use_container_width=True):
            if p_adi:
                conn = vt_baglan()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO personel (personel_adi, sube, yetkili_marka) VALUES (?, ?, ?)", (p_adi, p_sube, p_marka))
                conn.commit()
                conn.close()
                st.success(f"✓ {p_adi} isimli personel {p_sube} şubesi {p_marka} markası için yetkilendirildi!")
                st.rerun()
            else:
                st.error("Lütfen personel adını boş bırakmayın.")
        
        st.write("---")
        st.subheader("📋 Yetkili Personel Listesi")
        conn = vt_baglan()
        df_personel = pd.read_sql_query("SELECT * FROM personel", conn)
        conn.close()
        if not df_personel.empty:
            df_personel.columns = ["ID", "Personel Adı", "Şube", "Yetkili Marka"]
            st.dataframe(df_personel, use_container_width=True)
            
    with sekme2:
        st.subheader("Marka Bağlantılı Yeni Parça Ekle")
        secilen_marka = st.selectbox("Parçanın Markası:", ["Volkswagen", "Audi", "Seat", "Skoda", "BMW"], key="parca_marka")
        p_kodu = st.text_input("Orijinal Parça Kodu:")
        p_adi_master = st.text_input("Parça Tanımı / Adı:")
        
        if st.button("Parçayı Master Listeye Ekle", use_container_width=True):
            if p_kodu and p_adi_master:
                try:
                    conn = vt_baglan()
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO parca_master VALUES (?, ?, ?)", (p_kodu, p_adi_master, secilen_marka))
                    conn.commit()
                    conn.close()
                    st.success("✓ Parça marka bağlantılı olarak master listeye eklendi!")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.warning("Bu parça kodu master listede zaten mevcut!")
            else:
                st.error("Lütfen parça kodu ve adını doldurun.")
                
        st.write("---")
        st.subheader("📋 Master Parça Listesi")
        conn = vt_baglan()
        df_parca = pd.read_sql_query("SELECT * FROM parca_master", conn)
        conn.close()
        if not df_parca.empty:
            df_parca.columns = ["Parça Kodu", "Parça Adı", "Bağlı Olduğu Marka"]
            st.dataframe(df_parca, use_container_width=True)

# 2. KERİM'İN EKRANI (ŞİMDİLİK BOŞ)
elif st.session_state.aktif_kullanici == "kerim":
    st.title("📝 Sayım Giriş Ekranı")
    st.caption("Sayım Personeli Operasyon Sayfası")
    st.write("---")
    st.info("Ramazan Bey personel ve parça tanımlamalarını yaptıktan sonra bu ekranda sayım girişleriniz listelenecektir.")
