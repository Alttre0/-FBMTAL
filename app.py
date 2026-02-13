import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
from streamlit_option_menu import option_menu
import time
from streamlit_google_auth import Authenticate

# --- 1. AYARLAR ---
st.set_page_config(page_title="Robotik Akıllı Terminal", page_icon="🤖", layout="wide")

def get_turkiye_saati():
    return datetime.utcnow() + timedelta(hours=3)

def get_remote_ip():
    try:
        return st.context.headers.get("X-Forwarded-For", "127.0.0.1").split(",")[0].strip()
    except:
        return "127.0.0.1"

# --- 2. GOOGLE AUTH (Secrets Kullanımı) ---
# Bilgiler artık .streamlit/secrets.toml dosyasından okunuyor
authenticator = Authenticate(
    secret_key=st.secrets["google_auth"]["cookie_key"],
    client_id=st.secrets["google_auth"]["client_id"],
    client_secret=st.secrets["google_auth"]["client_secret"],
    redirect_uri="http://localhost:8501",
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

# --- 4. VERİLERİ ÇEK ---
current_ip = get_remote_ip()
df_users = pd.read_csv(FILES["users"])
df_logs = pd.read_csv(FILES["data"])

# IP Tanıma
user_by_ip = df_users[df_users["IP"] == current_ip]
ip_remembered = not user_by_ip.empty

# --- 5. TASARIM ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #c9d1d9; }
    .stButton button { background: linear-gradient(45deg, #ff8c00, #d35400); color: white; border-radius: 8px; font-weight: bold; }
    .reg-box { background: #161b22; padding: 30px; border-radius: 15px; border: 1px solid #30363d; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- 6. SAYFALAR ---
with st.sidebar:
    secim = option_menu("Robotik Lab", ["Giriş Ekranı", "Duyurular", "Liderlik", "Yönetici"], 
        icons=['cpu', 'megaphone', 'trophy', 'gear'], default_index=0)

if secim == "Giriş Ekranı":
    st.title("📟 Akıllı Terminal")

    if not ip_remembered:
        st.markdown('<div class="reg-box">', unsafe_allow_html=True)
        st.subheader("Devam etmek için Google Girişi Yapın")
        
        # Google Login
        authenticator.check_authenticity()
        
        if not st.session_state.get('connected'):
            authenticator.login()
        else:
            # Google'dan gelen verileri al
            user_info = st.session_state.get('user_info', {})
            g_email = user_info.get('email')
            g_name = user_info.get('name')
            g_verified = user_info.get('email_verified', False)

            # Mail onayı kontrolü ve kayıt
            if g_email:
                st.info(f"Doğrulanan Hesap: {g_email}")
                
                # Eğer email kayıtlı değilse sınıf sor
                if g_email not in df_users["Email"].values:
                    with st.form("complete_registration"):
                        u_class = st.selectbox("Sınıfınız:", ["9", "10", "11", "12"])
                        if st.form_submit_button("Kaydı Tamamla"):
                            new_u = pd.DataFrame([[g_name, u_class, g_email, current_ip]], columns=df_users.columns)
                            new_u.to_csv(FILES["users"], mode='a', index=False, header=False)
                            st.success("Kaydınız başarıyla oluşturuldu!")
                            time.sleep(1)
                            st.rerun()
                else:
                    # Email var ama IP farklıysa güncelle ve içeri al
                    df_users.loc[df_users["Email"] == g_email, "IP"] = current_ip
                    df_users.to_csv(FILES["users"], index=False)
                    st.rerun()
            else:
                st.error("Google'dan email bilgisi alınamadı. Lütfen tekrar deneyin.")
        st.markdown('</div>', unsafe_allow_html=True)

    else:
        # TANINAN KULLANICI
        user_name = user_by_ip["Isim"].values[0]
        st.success(f"✨ Hoş geldin, **{user_name}**")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            islem = st.text_area("Şu an ne yapıyorsun?")
        with col2:
            tr_simdi = get_turkiye_saati()
            tip = st.radio("İşlem:", ["GİRİŞ", "ÇIKIŞ"], horizontal=True)
            lehim = st.toggle("🔥 Lehim")

        if st.button("🚀 KAYDET"):
            zaman_str = f"{tr_simdi.strftime('%H:%M')} | {tr_simdi.strftime('%d-%m')}"
            pd.DataFrame([[zaman_str, user_name, islem, ("EVET" if lehim else "HAYIR"), tip, current_ip, 10 if tip=="GİRİŞ" else 0]], 
                        columns=df_logs.columns).to_csv(FILES["data"], mode='a', index=False, header=False)
            st.balloons()
            time.sleep(1)
            st.rerun()

# --- DUYURULAR VE DİĞERLERİ (Öncekiyle aynı) ---
elif secim == "Duyurular":
    st.title("📢 Atölye Panosu")
    with open(FILES["duyuru"], "r", encoding="utf-8") as f: content = f.read()
    st.markdown(f"<div style='background:#1c2128; padding:20px; border-radius:10px; border:1px solid #ff8c00;'>{content}</div>", unsafe_allow_html=True)

elif secim == "Liderlik":
    st.title("🏆 Sıralama")
    liderler = df_logs.groupby("İsim")["Puan"].sum().reset_index().sort_values("Puan", ascending=False)
    st.dataframe(liderler, use_container_width=True, hide_index=True)

elif secim == "Yönetici":
    sifre = st.text_input("Şifre:", type="password")
    if sifre == "15531552":
        st.subheader("Sistem Verileri")
        st.dataframe(df_users, use_container_width=True)
