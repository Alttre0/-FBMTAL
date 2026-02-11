import streamlit as st
import pandas as pd
import requests
import os
import time
from datetime import datetime, timedelta
from streamlit_option_menu import option_menu

# --- 1. ONESIGNAL BİLGİLERİN (GÖRÜNTÜDEN ALINDI) ---
ONESIGNAL_APP_ID = "89c0debc-c7a8-4ffe-9848-9405df878dd4"
ONESIGNAL_REST_KEY = "unkecvtjcufbmlqc2ftlrm46y"

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

# --- 2. HATA VERMEYEN JS VE ZORUNLU İZİN MOTORU ---
# f-string hatasını önlemek için % operatörünü kullanıyoruz
onesignal_js = """
<script src="https://cdn.onesignal.com/sdks/web/v16/OneSignalSDK.sw.js" defer></script>
<script src="https://cdn.onesignal.com/sdks/OneSignalSDK.js" async=""></script>
<script>
  window.OneSignal = window.OneSignal || [];
  OneSignal.push(function() {
    OneSignal.init({
      appId: "%s",
      allowLocalhostAsSecureOrigin: true,
      promptOptions: {
        slidedown: {
          enabled: true,
          autoPrompt: true,
          timeDelay: 1,
          pageViews: 1
        }
      }
    });

    // Bildirim durumu kontrolü
    OneSignal.on('notificationPermissionChange', function(permissionChange) {
        if (permissionChange.to === 'granted') {
            location.reload();
        }
    });

    OneSignal.isPushNotificationsEnabled(function(isEnabled) {
      if (!isEnabled) {
        // İzin yoksa ekranı karart ve uyarı çıkar
        document.body.innerHTML = `
          <div style="background:#0d1117; color:white; height:100vh; display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center; font-family:sans-serif; padding:20px;">
            <h1 style="color:#ff8c00;">⚠️ ERİŞİM ENGELLENDİ</h1>
            <p style="font-size:18px;">Atölye sistemine girmek için bildirimlere izin vermeniz zorunludur.</p>
            <p>Lütfen tarayıcı adres çubuğundaki kilit simgesine tıklayın veya çıkan pencerede 'İzin Ver' butonuna basın.</p>
            <button onclick="OneSignal.showNativePrompt()" style="background:#ff8c00; border:none; padding:15px 30px; color:white; border-radius:10px; font-weight:bold; cursor:pointer; margin-top:20px;">İzin Penceresini Aç</button>
          </div>`;
      }
    });
  });
</script>
""" % ONESIGNAL_APP_ID

st.markdown(onesignal_js, unsafe_allow_html=True)

# --- 3. TASARIM VE DOSYALAR ---
st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: #c9d1d9; }
    .main-card { background: #161b22; padding: 20px; border-radius: 15px; border-left: 5px solid #ff8c00; }
    .stButton button { background: linear-gradient(135deg, #ff8c00 0%, #ff4500 100%); color: white; border-radius: 8px; font-weight: bold; width:100%; }
    </style>
    """, unsafe_allow_html=True)

FILES = {"data": "robotik_log.csv", "users": "ogrenciler.csv", "ban": "yarisma_ban.csv", "duyuru": "duyuru.txt", "logo": "logo.jpg"}

for f in ["data", "users", "ban"]:
    if not os.path.exists(FILES[f]):
        pd.DataFrame(columns=["Zaman", "İsim", "İşlem", "Lehim", "Tip", "IP", "Puan"] if f=="data" else (["Isim", "Sinif"] if f=="users" else ["IP", "Isim", "Sebep"])).to_csv(FILES[f], index=False)

# --- 4. YAN MENÜ ---
with st.sidebar:
    if os.path.exists(FILES["logo"]): st.image(FILES["logo"], use_container_width=True)
    secim = option_menu("Robotik Kontrol", ["Giriş", "Duyurular", "Sıralama", "Yönetici"], icons=['cpu', 'megaphone', 'award', 'shield-lock'], default_index=0)

# --- 5. SAYFALAR ---
if secim == "Giriş":
    st.title("📟 Atölye Kayıt")
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    
    df_u = pd.read_csv(FILES["users"])
    secilen = st.selectbox("İsminiz:", ["Seçiniz..."] + sorted(df_u["Isim"].tolist()))
    islem = st.text_input("Göreviniz?")
    
    if st.button("KAYDI TAMAMLA 🚀"):
        if secilen != "Seçiniz...":
            z_str = get_turkiye_saati().strftime("%H:%M | %d-%m")
            pd.DataFrame([[z_str, secilen, islem, "HAYIR", "GİRİŞ", "127.0.0.1", 10]], columns=["Zaman", "İsim", "İşlem", "Lehim", "Tip", "IP", "Puan"]).to_csv(FILES["data"], mode='a', index=False, header=False)
            st.balloons(); st.success("Sisteme giriş yapıldı!"); time.sleep(1); st.rerun()
        else: st.error("İsim seçilmedi!")
    st.markdown("</div>", unsafe_allow_html=True)

elif secim == "Yönetici":
    sifre = st.text_input("Şifre:", type="password")
    if sifre == "15531552":
        t1, t2 = st.tabs(["Kayıt Sil/Ban", "Duyuru Gönder"])
        with t1:
            sil_ad = st.selectbox("Silinecek/Banlanacak:", sorted(df_u["Isim"].tolist()))
            if st.button("ÖĞRENCİYİ SİSTEMDEN SİLLER"):
                df_u = df_u[df_u["Isim"] != sil_ad]
                df_u.to_csv(FILES["users"], index=False)
                st.warning(f"{sil_ad} sistemden silindi."); st.rerun()
        with t2:
            y_duy = st.text_area("Mesaj:")
            if st.button("BİLDİRİMİ GÖNDER 🚀"):
                with open(FILES["duyuru"], "w", encoding="utf-8") as f: f.write(y_duy)
                status = push_bildirim_gonder(y_duy)
                if status == 200: st.success("Duyuru yayınlandı ve herkese bildirim gitti!"); st.rerun()
