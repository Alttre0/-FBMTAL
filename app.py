import streamlit as st
import pandas as pd
import requests
import os
import time
from datetime import datetime, timedelta
from streamlit_option_menu import option_menu

# --- 1. AYARLAR VE ONESIGNAL ---
st.set_page_config(page_title="Robotik Lab Terminal", page_icon="🤖", layout="wide")

# BURAYA ONESIGNAL BİLGİLERİNİ YAPIŞTIR
ONESIGNAL_APP_ID = "89c0debc-c7a8-4ffe-9848-9405df878dd4"
ONESIGNAL_REST_KEY = "os_v2_app_rhan5pghvbh75gcisqc57b4n2tunkecvtjcufbmlqc2ftlrm46yqi4jsgq4ecnaaihpcytzbpwradw2aujhk72d7upp3burrixmxfpq"

def get_turkiye_saati():
    return datetime.utcnow() + timedelta(hours=3)

def push_bildirim_gonder(mesaj):
    header = {"Content-Type": "application/json; charset=utf-8", "Authorization": "Basic " + ONESIGNAL_REST_KEY}
    payload = {
        "app_id": ONESIGNAL_APP_ID,
        "included_segments": ["Total Subscriptions"],
        "contents": {"tr": mesaj},
        "headings": {"tr": "Robotik Atölyesi 🤖"}
    }
    r = requests.post("https://api.onesignal.com/notifications", headers=header, json=payload)
    return r.status_code

# --- 2. HATA VERMEYEN BİLDİRİM SCRIPTI ---
# f-string kullanmıyoruz (f işaretini kaldırdık), değişkeni manuel ekliyoruz
st.markdown('<script src="https://cdn.onesignal.com/sdks/web/v16/OneSignalSDK.sw.js" defer></script>', unsafe_allow_html=True)
st.markdown('<script src="https://cdn.onesignal.com/sdks/OneSignalSDK.js" async=""></script>', unsafe_allow_html=True)

# Değişkeni JS içine güvenli bir şekilde gömme
onesignal_js = """
<script>
  window.OneSignal = window.OneSignal || [];
  OneSignal.push(function() {
    OneSignal.init({
      appId: "APP_ID_GOLECEK",
      allowLocalhostAsSecureOrigin: true,
      promptOptions: {
        slidedown: {
          enabled: true,
          autoPrompt: true,
          timeDelay: 1,
          pageViews: 1
        }
      },
      notifyButton: {
        enable: true,
        position: 'bottom-right'
      }
    });
  });
</script>
""".replace("APP_ID_GOLECEK", ONESIGNAL_APP_ID)

st.markdown(onesignal_js, unsafe_allow_html=True)

# --- 3. TASARIM VE DOSYALAR ---
st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: #c9d1d9; }
    .main-card { background: #161b22; padding: 20px; border-radius: 15px; border-left: 5px solid #ff8c00; margin-bottom: 20px; }
    .stButton button { background: linear-gradient(135deg, #ff8c00 0%, #ff4500 100%); color: white; border-radius: 8px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

FILES = {"data": "robotik_log.csv", "users": "ogrenciler.csv", "ban": "yarisma_ban.csv", "duyuru": "duyuru.txt", "logo": "logo.jpg"}

# Dosya kontrolü (Hata almamak için)
if not os.path.exists(FILES["data"]): pd.DataFrame(columns=["Zaman", "İsim", "İşlem", "Lehim", "Tip", "IP", "Puan"]).to_csv(FILES["data"], index=False)
if not os.path.exists(FILES["users"]): pd.DataFrame(columns=["Isim", "Sinif"]).to_csv(FILES["users"], index=False)
if not os.path.exists(FILES["ban"]): pd.DataFrame(columns=["IP", "Isim", "Sebep"]).to_csv(FILES["ban"], index=False)

# --- 4. YAN MENÜ ---
with st.sidebar:
    if os.path.exists(FILES["logo"]):
        st.image(FILES["logo"], use_container_width=True)
    secim = option_menu("Robotik HUB", ["Giriş", "Duyurular", "Sıralama", "Yönetici"], 
        icons=['cpu', 'megaphone', 'award', 'shield-lock'], default_index=0)

# --- 5. SAYFALAR ---
if secim == "Giriş":
    st.title("📟 Kayıt Terminali")
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    st.info("💡 Lütfen yukarıdan gelen veya sağ altta çıkan bildirim isteğine 'İzin Ver' deyin.")
    
    df_u = pd.read_csv(FILES["users"])
    secilen = st.selectbox("İsminiz:", ["Seçiniz..."] + sorted(df_u["Isim"].tolist()))
    
    if st.button("ATÖLYEYE GİRİŞ YAP 🚀"):
        if secilen != "Seçiniz...":
            st.balloons(); st.success(f"Hoş geldin {secilen}!"); time.sleep(1); st.rerun()
        else: st.error("İsim seçilmedi!")
    st.markdown("</div>", unsafe_allow_html=True)

elif secim == "Duyurular":
    st.title("📢 Atölye Panosu")
    with open(FILES["duyuru"], "r", encoding="utf-8") as f: content = f.read()
    st.markdown(f"<div class='main-card' style='font-size: 20px;'>{content}</div>", unsafe_allow_html=True)

elif secim == "Yönetici":
    sifre = st.text_input("Şifre:", type="password")
    if sifre == "15531552":
        st.subheader("📢 Bildirim Gönder")
        y_duy = st.text_area("Mesaj:")
        if st.button("HERKESE GÖNDER 🚀"):
            with open(FILES["duyuru"], "w", encoding="utf-8") as f: f.write(y_duy)
            status = push_bildirim_gonder(y_duy)
            if status == 200: st.success("Bildirimler başarıyla gönderildi!")
            else: st.error(f"Hata: {status}")
