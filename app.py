import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Otomol Kör Sayım Sistemi", page_icon="📝", layout="wide")

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
    
    # 3. Personel Sayım Sonuçları Tablosu (YENİ)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sayim_sonuclari (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tarih TEXT NOT NULL,
            personel_adi TEXT NOT NULL,
            sube TEXT NOT NULL,
            marka TEXT NOT NULL,
            parca_kodu TEXT NOT NULL,
            sayilan_adet INTEGER NOT NULL
        )
    """)
    conn.commit()
    conn.close()

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

# --- GÜVENLİ ÇIKIŞ ---
st.sidebar.markdown(f"👤 **Aktif Kullanıcı:** {st.session_state.aktif_kullanici.upper()}")
if st.sidebar.button("Güvenli Çıkış"):
    del st.session_state.giris_basarili
    st.rerun()

# ==============================================================================
# 1. RAMAZAN'IN EKRANI (ADMİN / YÖNETİM & RAPORLAMA SAYFASI)
# ==============================================================================
if st.session_state.aktif_kullanici == "ramazan":
    st.title("⚙️ Merkezi Yönetim & Sayım Raporları")
    st.caption("Bu sayfaya sadece RAMAZAN erişim sağlayabilir.")
    st.write("---")
    
    sekme1, sekme2, sekme3 = st.tabs(["👤 Personel Yetkilendirme", "📦 Marka & Parça Tanımlama", "📊 Canlı Sayım Sonuçları"])
    
    with sekme1:
        st.subheader("Yeni Personel Tanımla")
        p_adi = st.text_input("Personel Adı Soyadı (Sistem giriş adıyla aynı olmalı. Örn: kerim):").lower().strip()
        p_sube = st.selectbox("Görev Yapacağı Şube:", ["Antalya", "İstanbul", "İzmir"])
        p_marka = st.selectbox("Yetkili Olacağı Marka:", ["Volkswagen", "Audi", "Seat", "Skoda", "BMW"])
        
        if st.button("Personeli Kaydet", use_container_width=True):
            if p_adi:
                conn = vt_baglan()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO personel (personel_adi, sube, yetkili_marka) VALUES (?, ?, ?)", (p_adi, p_sube, p_marka))
                conn.commit()
                conn.close()
                st.success(f"✓ {p_adi.upper()} isimli personel başarıyla yetkilendirildi!")
                st.rerun()
            else:
                st.error("Lütfen personel adını boş bırakmayın.")
        
        st.write("---")
        st.subheader("📋 Yetkili Personel Listesi")
        conn = vt_baglan()
        df_personel = pd.read_sql_query("SELECT * FROM personel", conn)
        conn.close()
        if not df_personel.empty:
            df_personel.columns = ["ID", "Sistem Adı", "Şube", "Yetkili Marka"]
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
                    st.success("✓ Parça master listeye eklendi!")
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

    with sekme3:
        st.subheader("📥 Sahadan Gelen Canlı Sayım Verileri")
        conn = vt_baglan()
        df_sonuclar = pd.read_sql_query("SELECT * FROM sayim_sonuclari ORDER BY id DESC", conn)
        conn.close()
        
        if not df_sonuclar.empty:
            df_sonuclar.columns = ["Kayıt ID", "Tarih/Saat", "Sayımı Yapan", "Şube", "Marka", "Parça Kodu", "Sayılan Adet"]
            st.dataframe(df_sonuclar, use_container_width=True)
        else:
            st.info("Henüz sahada yapılmış bir sayım girişi bulunmuyor.")

# ==============================================================================
# 2. KERİM VEYA DİĞER PERSONELLERİN SORGULI SAYIM GİRİŞ EKRANI
# ==============================================================================
else:
    mevcut_kullanici = st.session_state.aktif_kullanici
    st.title("📝 Kurumsal Kör Sayım Giriş Ekranı")
    st.caption(f"Sayım Operatörü: {mevcut_kullanici.upper()}")
    st.write("---")
    
    # Personelin yetkilerini SQL'den sorguluyoruz
    conn = vt_baglan()
    cursor = conn.cursor()
    cursor.execute("SELECT sube, yetkili_marka FROM personel WHERE personel_adi = ?", (mevcut_kullanici,))
    yetki = cursor.fetchone()
    conn.close()
    
    if yetki:
        personel_sube, personel_marka = yetki[0], yetki[1]
        
        # Dinamik Bilgilendirme Kartları
        c1, c2 = st.columns(2)
        c1.metric("Atandığınız Şube", personel_sube)
        c2.metric("Sorgulama Yetkili Marka", personel_marka)
        st.write("---")
        
        # Sadece personelin yetkili olduğu markaya ait parçaları SQL'den çekiyoruz
        conn = vt_baglan()
        df_yetkili_parcalar = pd.read_sql_query(
            "SELECT parca_kodu, parca_adi FROM parca_master WHERE marka = ?", conn, params=(personel_marka,)
        )
        conn.close()
        
        if not df_yetkili_parcalar.empty:
            # Personel parça kodunu listeden seçer veya arar
            parca_secenekleri = df_yetkili_parcalar["parca_kodu"].tolist()
            secilen_kod = st.selectbox("Sayımı Yapılan Parça Kodunu Seçin:", parca_secenekleri)
            
            # Seçilen parçanın adını otomatik ekrana basıyoruz (Hata payını sıfırlamak için)
            parca_adi_otomatik = df_yetkili_parcalar[df_yetkili_parcalar["parca_kodu"] == secilen_kod]["parca_adi"].values[0]
            st.info(f"📋 **Seçilen Parça Tanımı:** {parca_adi_otomatik}")
            
            # Sayım Adedi Girişi
            sayilan_adet = st.number_input("Fiziki Sayılan Stok Adedi:", min_value=0, value=0, step=1)
            
            if st.button("Sayımı Onayla ve Sisteme Gönder", use_container_width=True):
                su_an = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                conn = vt_baglan()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO sayim_sonuclari (tarih, personel_adi, sube, marka, parca_kodu, sayilan_adet)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (su_an, mevcut_kullanici, personel_sube, personel_marka, secilen_kod, sayilan_adet))
                conn.commit()
                conn.close()
                
                st.success(f"✓ {secilen_kod} parçası için {sayilan_adet} adetlik sayım kaydı merkeze iletildi!")
        else:
            st.warning(f"Sistemde yetkili olduğunuz **{personel_marka}** markasına ait tanımlanmış parça bulunamadı. Lütfen Ramazan Bey ile görüşün.")
            
    else:
        st.error("🚨 Sistemde tanımlı bir yetkilendirmeniz bulunamadı! Lütfen Ramazan Bey'in sizi 'Personel Yetkilendirme' ekranından eklediğinden emin olun.")