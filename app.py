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
    header = {"Content-Type": "application/json; charset=utf-8", "Authorization": f"Basic {ONESIGNAL_REST_KEY}"}
    payload = {
        "app_id": ONESIGNAL_APP_ID,
        "included_segments": ["Total Subscriptions"],
        "contents": {"tr": mesaj},
        "headings": {"tr": "Robotik Atölyesi 🤖"}
    }
    r = requests.post("https://api.onesignal.com/notifications", headers=header, json=payload)
    return r.status_code

# --- 2. GİRİŞTE İZİN İSTEYEN SİHİRLİ JS ---
# Zil butonunu görünür yapar ve girişte izin penceresini (Slidedown) açar
st.markdown(f'<script src="https://cdn.onesignal.com/sdks/web/v16/OneSignalSDK.sw.js" defer></script>', unsafe_allow_html=True)
st.markdown(f'<script src="https://cdn.onesignal.com/sdks/OneSignalSDK.js" async=""></script>', unsafe_allow_html=True)
st.markdown(f"""
    <script>
      window.OneSignal = window.OneSignal || [];
      OneSignal.push(function() {
        OneSignal.init({
          appId: "{ONESIGNAL_APP_ID}",
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
            displayPredicate: function() { return OneSignal.isPushNotificationsEnabled().then(function(isPushEnabled) { return !isPushEnabled; }); },
            position: 'bottom-right',
            size: 'medium',
            theme: 'default'
          }
        });
        // Girişte direkt izin penceresini tetikle
        OneSignal.showNativePrompt();
      });
    </script>
    <style>
    .stApp {{ background-color: #0d1117; color: #c9d1d9; }}
    .main-card {{ background: #161b22; padding: 20px; border-radius: 15px; border: 1px solid #30363d; margin-bottom: 20px; border-left: 5px solid #ff8c00; }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. VERİTABANI VE LOGO ---
FILES = {"data": "robotik_log.csv", "users": "ogrenciler.csv", "ban": "yarisma_ban.csv", "duyuru": "duyuru.txt", "logo": "logo.jpg"}

if not os.path.exists(FILES["data"]): pd.DataFrame(columns=["Zaman", "İsim", "İşlem", "Lehim", "Tip", "IP", "Puan"]).to_csv(FILES["data"], index=False)
if not os.path.exists(FILES["users"]): pd.DataFrame(columns=["Isim", "Sinif"]).to_csv(FILES["users"], index=False)
if not os.path.exists(FILES["ban"]): pd.DataFrame(columns=["IP", "Isim", "Sebep"]).to_csv(FILES["ban"], index=False)

# --- 4. YAN MENÜ ---
with st.sidebar:
    if os.path.exists(FILES["logo"]):
        st.image(FILES["logo"], use_container_width=True)
    else:
        st.markdown("<h2 style='text-align:center; color:#ff8c00;'>ROBOTİK</h2>", unsafe_allow_html=True)
    secim = option_menu(None, ["Giriş", "Duyurular", "Sıralama", "Admin"], 
        icons=['cpu', 'megaphone', 'award', 'shield-lock'], default_index=0)

# --- 5. SAYFALAR ---
if secim == "Giriş":
    st.title("📟 Operatör Kayıt")
    # Logoyu bir de burada gösteriyoruz
    if os.path.exists(FILES["logo"]):
        col_l, _ = st.columns([1, 4])
        with col_l: st.image(FILES["logo"], width=120)

    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    st.info("🔔 Bildirim uyarısı gelirse 'İzin Ver' diyerek duyurulardan haberdar olabilirsiniz.")
    
    df_u = pd.read_csv(FILES["users"])
    secilen = st.selectbox("İsminiz:", ["Seçiniz..."] + sorted(df_u["Isim"].tolist()))
    islem = st.text_input("Göreviniz:")
    
    if st.button("KAYDI TAMAMLA 🚀"):
        if secilen != "Seçiniz...":
            z_str = get_turkiye_saati().strftime("%H:%M | %d-%m")
            pd.DataFrame([[z_str, secilen, islem, "HAYIR", "GİRİŞ", "127.0.0.1", 10]], 
                        columns=["Zaman", "İsim", "İşlem", "Lehim", "Tip", "IP", "Puan"]).to_csv(FILES["data"], mode='a', index=False, header=False)
            st.balloons()
            st.success("Kaydedildi!")
        else: st.error("Lütfen ismini seç!")
    st.markdown("</div>", unsafe_allow_html=True)

elif secim == "Admin":
    sifre = st.text_input("Şifre:", type="password")
    if sifre == "15531552":
        st.subheader("📢 OneSignal Global Bildirim")
        y_duy = st.text_area("Mesaj içeriği:")
        if st.button("TÜM CİHAZLARA GÖNDER 🚀"):
            with open(FILES["duyuru"], "w", encoding="utf-8") as f: f.write(y_duy)
            stat = push_bildirim_gonder(y_duy)
            if stat == 200: st.success("Bildirimler yola çıktı!")
            else: st.error(f"Hata Kodu: {stat}")
