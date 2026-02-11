import streamlit as st
import pandas as pd
import requests
import os
import time
from datetime import datetime, timedelta
from streamlit_option_menu import option_menu

# --- 1. ONESIGNAL BİLGİLERİ ---
ONESIGNAL_APP_ID = "89c0debc-c7a8-4ffe-9848-9405df878dd4"
ONESIGNAL_REST_KEY = "unkecvtjcufbmlqc2ftlrm46y"

def get_turkiye_saati():
    return datetime.utcnow() + timedelta(hours=3)

# --- 2. DOSYA KONTROLÜ (HATA ÖNLEYİCİ) ---
FILES = {
    "data": "robotik_log.csv", 
    "users": "ogrenciler.csv", 
    "ban": "yarisma_ban.csv", 
    "duyuru": "duyuru.txt", 
    "logo": "logo.jpg"
}

def check_files():
    # Eğer dosyalar yoksa veya içi boşsa (0 byte ise) başlıklarla beraber oluştur
    if not os.path.exists(FILES["data"]) or os.stat(FILES["data"]).st_size == 0:
        pd.DataFrame(columns=["Zaman", "İsim", "İşlem", "Lehim", "Tip", "IP", "Puan"]).to_csv(FILES["data"], index=False)
    
    if not os.path.exists(FILES["users"]) or os.stat(FILES["users"]).st_size == 0:
        pd.DataFrame(columns=["Isim", "Sinif"]).to_csv(FILES["users"], index=False)
    
    if not os.path.exists(FILES["ban"]) or os.stat(FILES["ban"]).st_size == 0:
        pd.DataFrame(columns=["IP", "Isim", "Sebep"]).to_csv(FILES["ban"], index=False)
    
    if not os.path.exists(FILES["duyuru"]):
        with open(FILES["duyuru"], "w", encoding="utf-8") as f: f.write("Hoş Geldiniz!")

check_files()

# --- 3. BİLDİRİM ZORUNLULUĞU (JS) ---
onesignal_js = """
<script src="https://cdn.onesignal.com/sdks/web/v16/OneSignalSDK.sw.js" defer></script>
<script src="https://cdn.onesignal.com/sdks/OneSignalSDK.js" async=""></script>
<script>
  window.OneSignal = window.OneSignal || [];
  OneSignal.push(function() {
    OneSignal.init({
      appId: "%s",
      allowLocalhostAsSecureOrigin: true,
      promptOptions: { slidedown: { enabled: true, autoPrompt: true, timeDelay: 1 } }
    });

    OneSignal.isPushNotificationsEnabled(function(isEnabled) {
      if (!isEnabled) {
        document.body.innerHTML = `
          <div style="background:#0d1117; color:white; height:100vh; display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center; font-family:sans-serif; padding:20px;">
            <h1 style="color:#ff8c00;">⚠️ ERİŞİM ENGELLENDİ</h1>
            <p style="font-size:18px;">Atölye sistemine girmek için bildirimlere izin vermeniz zorunludur.</p>
            <button onclick="OneSignal.showNativePrompt()" style="background:#ff8c00; border:none; padding:15px 30px; color:white; border-radius:10px; font-weight:bold; cursor:pointer; margin-top:20px;">İzin Ver ve Giriş Yap</button>
          </div>`;
      }
    });
  });
</script>
""" % ONESIGNAL_APP_ID

st.markdown(onesignal_js, unsafe_allow_html=True)

# --- 4. TASARIM ---
st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: #c9d1d9; }
    .main-card { background: #161b22; padding: 20px; border-radius: 15px; border-left: 5px solid #ff8c00; margin-bottom: 20px; }
    .stButton button { background: linear-gradient(135deg, #ff8c00 0%, #ff4500 100%); color: white; border-radius: 8px; font-weight: bold; width:100%; }
    </style>
    """, unsafe_allow_html=True)

# --- 5. VERİLERİ YÜKLE ---
df_logs = pd.read_csv(FILES["data"])
df_users = pd.read_csv(FILES["users"])
df_ban = pd.read_csv(FILES["ban"])

# --- 6. YAN MENÜ ---
with st.sidebar:
    if os.path.exists(FILES["logo"]): st.image(FILES["logo"], use_container_width=True)
    secim = option_menu("Robotik Kontrol", ["Giriş", "Duyurular", "Sıralama", "Yönetici"], 
                        icons=['cpu', 'megaphone', 'award', 'shield-lock'], default_index=0)

# --- 7. SAYFALAR ---
if secim == "Giriş":
    st.title("📟 Atölye Kayıt")
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    
    if df_users.empty:
        st.warning("⚠️ Henüz öğrenci kaydı yok. Lütfen Yönetici panelinden öğrenci ekleyin.")
    else:
        secilen = st.selectbox("İsminiz:", ["Seçiniz..."] + sorted(df_users["Isim"].tolist()))
        islem = st.text_input("Göreviniz?")
        if st.button("KAYDI TAMAMLA 🚀"):
            if secilen != "Seçiniz...":
                z_str = get_turkiye_saati().strftime("%H:%M | %d-%m")
                pd.DataFrame([[z_str, secilen, islem, "HAYIR", "GİRİŞ", "127.0.0.1", 10]], columns=df_logs.columns).to_csv(FILES["data"], mode='a', index=False, header=False)
                st.balloons(); st.success("Giriş kaydedildi!"); time.sleep(1); st.rerun()
            else: st.error("Lütfen isim seçin!")
    st.markdown("</div>", unsafe_allow_html=True)

elif secim == "Yönetici":
    sifre = st.text_input("Şifre:", type="password")
    if sifre == "15531552":
        t1, t2 = st.tabs(["Öğrenci Ekle/Sil", "Duyuru Paylaş"])
        
        with t1:
            y_ad = st.text_input("Yeni Öğrenci Adı:")
            if st.button("Ekle"):
                pd.DataFrame([[y_ad, "10"]], columns=["Isim", "Sinif"]).to_csv(FILES["users"], mode='a', index=False, header=False)
                st.success("Eklendi."); st.rerun()
            
            st.write("---")
            if not df_users.empty:
                sil_ad = st.selectbox("Silinecek Öğrenci:", sorted(df_users["Isim"].tolist()))
                if st.button("ÖĞRENCİYİ SİSTEMDEN SİL"):
                    df_u_new = df_users[df_users["Isim"] != sil_ad]
                    df_u_new.to_csv(FILES["users"], index=False)
                    st.success("Silindi."); st.rerun()
