import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
from streamlit_option_menu import option_menu
import time

# --- 1. AYARLAR VE SAAT ---
st.set_page_config(page_title="Robotik Akıllı Terminal", page_icon="🤖", layout="wide")

def get_turkiye_saati():
    return datetime.utcnow() + timedelta(hours=3)

def get_remote_ip():
    try:
        # Streamlit Cloud/Proxy ayarı için
        ip = st.context.headers.get("X-Forwarded-For", "127.0.0.1").split(",")[0]
        return ip.strip() # Boşlukları temizle
    except:
        return "127.0.0.1"

# --- 2. DOSYA YÖNETİMİ ---
FILES = {
    "data": "robotik_log.csv",
    "users": "ogrenciler.csv",
    "ban": "yarisma_ban.csv",
    "duyuru": "duyuru.txt"
}

def db_check():
    for f, path in FILES.items():
        if not os.path.exists(path) or (f != "duyuru" and os.stat(path).st_size == 0):
            if f == "data": cols = ["Zaman", "İsim", "İşlem", "Lehim", "Tip", "IP", "Puan"]
            elif f == "users": cols = ["Isim", "Sinif", "Email", "IP"]
            elif f == "ban": cols = ["IP", "Isim", "Sebep"]
            
            if f != "duyuru": 
                pd.DataFrame(columns=cols).to_csv(path, index=False)
            else:
                with open(path, "w", encoding="utf-8") as d:
                    d.write("Robotik Atölyesi Hoş Geldiniz!")

db_check()

# --- 3. VERİLERİ VE OTURUMU YÖNET ---
current_ip = get_remote_ip()

# Verileri her zaman en güncel haliyle çek (Cache kullanmıyoruz)
df_users = pd.read_csv(FILES["users"])
df_logs = pd.read_csv(FILES["data"])
df_ban = pd.read_csv(FILES["ban"])

# IP Tanıma Mantığı
user_row = df_users[df_users["IP"] == current_ip]
is_registered = not user_row.empty

if is_registered:
    st.session_state["user_name"] = user_row["Isim"].values[0]
    st.session_state["is_logged_in"] = True
else:
    st.session_state["user_name"] = None
    st.session_state["is_logged_in"] = False

# --- 4. TASARIM ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #c9d1d9; }
    .stButton button { background: linear-gradient(45deg, #ff8c00, #d35400); color: white; border-radius: 8px; font-weight: bold; width: 100%; }
    .kvkk-box { background: #161b22; padding: 20px; border-radius: 10px; border: 1px solid #30363d; margin-bottom: 20px; }
    .reg-box { background: #1b2838; padding: 20px; border-radius: 10px; border: 2px solid #ff8c00; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- 5. YAN MENÜ ---
with st.sidebar:
    secim = option_menu("Robotik Lab", ["Giriş Ekranı", "Duyurular", "Liderlik", "Yönetici"], 
        icons=['cpu', 'megaphone', 'trophy', 'gear'], default_index=0)

# --- 6. SAYFALAR ---

if secim == "Giriş Ekranı":
    st.title("📟 Akıllı Terminal")
    
    if not st.session_state["is_logged_in"]:
        st.warning("🔎 Sistem sizi tanıyamadı. Lütfen kayıt olun veya yöneticiye başvurun.")
        with st.container():
            st.markdown('<div class="reg-box"><h3>📝 Kayıt Formu</h3>', unsafe_allow_html=True)
            reg_name = st.text_input("Ad Soyad:")
            reg_email = st.text_input("Gmail Adresiniz:")
            reg_class = st.selectbox("Sınıfınız:", ["9", "10", "11", "12"])
            
            if st.button("Kaydı Tamamla"):
                if reg_name and "@gmail.com" in reg_email.lower():
                    # Dosyaya kaydet
                    new_user = pd.DataFrame([[reg_name, reg_class, reg_email, current_ip]], 
                                          columns=["Isim", "Sinif", "Email", "IP"])
                    new_user.to_csv(FILES["users"], mode='a', index=False, header=False)
                    st.success("Kaydınız başarıyla yapıldı! Cihazınız tanımlandı.")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Hata: Geçerli bir isim ve Gmail adresi gereklidir.")
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        # KAYITLI KULLANICI EKRANI
        st.success(f"✅ Tanındı: **{st.session_state['user_name']}**")
        st.caption(f"Cihaz IP: {current_ip}")
        
        with st.expander("📄 KVKK Aydınlatma Metni"):
            st.write("Verileriniz atölye güvenliği için kaydedilmektedir.")

        col1, col2 = st.columns([2, 1])
        with col1:
            islem = st.text_area("Şu an ne üzerinde çalışıyorsun?", placeholder="Proje detayı giriniz...")
        with col2:
            tr_simdi = get_turkiye_saati()
            secilen_saat = st.time_input("İşlem Saati:", tr_simdi.time())
            tip = st.radio("İşlem Tipi:", ["GİRİŞ", "ÇIKIŞ"], horizontal=True)
            lehim = st.toggle("🔥 Lehim Masası Açık")

        if st.button("🚀 VERİYİ GÖNDER"):
            zaman_str = f"{secilen_saat.strftime('%H:%M')} | {tr_simdi.strftime('%d-%m')}"
            pd.DataFrame([[zaman_str, st.session_state['user_name'], islem, ("EVET" if lehim else "HAYIR"), tip, current_ip, 10 if tip=="GİRİŞ" else 0]], 
                        columns=df_logs.columns).to_csv(FILES["data"], mode='a', index=False, header=False)
            st.balloons()
            st.success("İşlem günlüğe kaydedildi!")
            time.sleep(1)
            st.rerun()

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
        st.subheader("Kayıtlı Cihazlar ve Öğrenciler")
        st.dataframe(df_users, use_container_width=True)
        if st.button("Listeyi Temizle (DİKKAT)"):
            pd.DataFrame(columns=["Isim", "Sinif", "Email", "IP"]).to_csv(FILES["users"], index=False)
            st.rerun()
