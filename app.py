import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import time

# --- MODÜL IMPORT ---
try:
    from streamlit_option_menu import option_menu
    from streamlit_google_auth import Authenticate
except ImportError:
    st.error("Kütüphaneler eksik! Lütfen 'pip install streamlit-option-menu streamlit-google-auth' komutunu çalıştırın.")
    st.stop()

# --- 1. AYARLAR ---
st.set_page_config(page_title="Robotik Akıllı Terminal", page_icon="🤖", layout="wide")

def get_turkiye_saati():
    return datetime.utcnow() + timedelta(hours=3)

def get_remote_ip():
    try:
        return st.context.headers.get("X-Forwarded-For", "127.0.0.1").split(",")[0].strip()
    except:
        return "127.0.0.1"

# --- 2. GOOGLE AUTH AYARLARI ---
if "google_auth" not in st.secrets:
    st.error("Secrets.toml bulunamadı! Google Client ID ve Secret bilgilerini ekleyin.")
    st.stop()

authenticator = Authenticate(
    secret_key=st.secrets["google_auth"]["cookie_key"],
    client_id=st.secrets["google_auth"]["client_id"],
    client_secret=st.secrets["google_auth"]["client_secret"],
    redirect_uri="http://localhost:8501", # Cloud'da isen gerçek URL ile değiştir!
    cookie_name="robotik_auth_cookie",
)

# --- 3. DOSYA YÖNETİMİ ---
FILES = {"data": "robotik_log.csv", "users": "ogrenciler.csv", "ban": "yarisma_ban.csv", "duyuru": "duyuru.txt"}

def db_check():
    for f, path in FILES.items():
        if not os.path.exists(path) or (f != "duyuru" and os.stat(path).st_size == 0):
            if f == "data": cols = ["Zaman", "İsim", "İşlem", "Lehim", "Tip", "IP", "Puan"]
            elif f == "users": cols = ["Isim", "Sinif", "Email", "IP"]
            elif f == "ban": cols = ["IP", "Isim", "Sebep"]
            if f != "duyuru": pd.DataFrame(columns=cols).to_csv(path, index=False)
            else:
                with open(path, "w", encoding="utf-8") as d: d.write("Robotik Atölyesi Hoş Geldiniz!")

db_check()

# --- 4. VERİ YÜKLEME ---
current_ip = get_remote_ip()
df_users = pd.read_csv(FILES["users"])
df_logs = pd.read_csv(FILES["data"])

# --- 5. TASARIM ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #c9d1d9; }
    .stButton button { background: linear-gradient(45deg, #ff8c00, #d35400); color: white; border-radius: 8px; font-weight: bold; }
    .main-card { background: #161b22; padding: 40px; border-radius: 20px; border: 1px solid #30363d; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- 6. SAYFALAR ---
with st.sidebar:
    secim = option_menu("Robotik Lab", ["Giriş Ekranı", "Duyurular", "Liderlik", "Yönetici"], 
        icons=['cpu', 'megaphone', 'trophy', 'gear'], default_index=0)

if secim == "Giriş Ekranı":
    st.title("📟 Akıllı Terminal")

    # Google Durum Kontrolü
    authenticator.check_authenticity()
    
    if not st.session_state.get('connected'):
        # 1. DURUM: HİÇ GİRİŞ YAPILMAMIŞ
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        st.subheader("Atölye Sistemine Hoş Geldiniz")
        st.write("İşlem yapmak için lütfen Google hesabınızla oturum açın.")
        
        # Google Login Butonu
        authenticator.login()
        st.markdown('</div>', unsafe_allow_html=True)
        
    else:
        # 2. DURUM: GOOGLE İLE BAĞLANILMIŞ
        user_info = st.session_state.get('user_info', {})
        g_email = user_info.get('email')
        g_name = user_info.get('name')

        # Bu mail veritabanında var mı?
        user_record = df_users[df_users["Email"] == g_email]
        
        if user_record.empty:
            # 2.A: GOOGLE GİRDİ AMA KAYDI YOK (YENİ ÜYE)
            st.warning(f"Merhaba {g_name}! Henüz kaydın tamamlanmamış.")
            with st.form("yeni_kayit_formu"):
                st.info("Lütfen sınıfını seçerek kaydını tamamla:")
                u_class = st.selectbox("Sınıfın:", ["9", "10", "11", "12"])
                if st.form_submit_button("Kaydı Onayla"):
                    new_user = pd.DataFrame([[g_name, u_class, g_email, current_ip]], columns=df_users.columns)
                    new_user.to_csv(FILES["users"], mode='a', index=False, header=False)
                    st.success("Kaydın yapıldı! Şimdi sistemi kullanabilirsin.")
                    time.sleep(1)
                    st.rerun()
        else:
            # 2.B: GOOGLE GİRDİ VE ZATEN KAYITLI (ESKİ ÜYE)
            u_name = user_record["Isim"].values[0]
            st.success(f"🤖 Sistem Hazır: **{u_name}**")
            
            # IP Güncelleme (Cihaz değişmiş olabilir)
            if user_record["IP"].values[0] != current_ip:
                df_users.loc[df_users["Email"] == g_email, "IP"] = current_ip
                df_users.to_csv(FILES["users"], index=False)

            # İşlem Formu
            col1, col2 = st.columns([2, 1])
            with col1:
                islem = st.text_area("Ne üzerinde çalışıyorsun?", placeholder="Örn: Python ile veri analizi...")
            with col2:
                tr_simdi = get_turkiye_saati()
                tip = st.radio("İşlem Tipi:", ["GİRİŞ", "ÇIKIŞ"], horizontal=True)
                lehim = st.toggle("🔥 Lehim Masası")

            if st.button("🚀 GÜNLÜĞE KAYDET"):
                zaman_str = f"{tr_simdi.strftime('%H:%M')} | {tr_simdi.strftime('%d-%m')}"
                pd.DataFrame([[zaman_str, u_name, islem, ("EVET" if lehim else "HAYIR"), tip, current_ip, 10 if tip=="GİRİŞ" else 0]], 
                            columns=df_logs.columns).to_csv(FILES["data"], mode='a', index=False, header=False)
                st.balloons()
                st.success("Başarıyla kaydedildi!")
                time.sleep(1)
                st.rerun()
            
            # Çıkış Yap butonu (Oturumu kapatmak istersen)
            if st.button("Çıkış Yap (Google Oturumunu Kapat)"):
                authenticator.logout()
                st.rerun()

# --- DİĞER SAYFALAR ---
elif secim == "Duyurular":
    st.title("📢 Duyuru Panosu")
    with open(FILES["duyuru"], "r", encoding="utf-8") as f: content = f.read()
    st.markdown(f"<div style='background:#1c2128; padding:20px; border-radius:10px; border:1px solid #ff8c00;'>{content}</div>", unsafe_allow_html=True)

elif secim == "Liderlik":
    st.title("🏆 Sıralama")
    liderler = df_logs.groupby("İsim")["Puan"].sum().reset_index().sort_values("Puan", ascending=False)
    st.dataframe(liderler, use_container_width=True, hide_index=True)

elif secim == "Yönetici":
    sifre = st.text_input("Şifre:", type="password")
    if sifre == "15531552":
        st.subheader("Öğrenci Veritabanı")
        st.dataframe(df_users, use_container_width=True)
