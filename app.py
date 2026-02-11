import streamlit as st
import pandas as pd
import requests
import os
import time
from datetime import datetime, timedelta
from streamlit_option_menu import option_menu

# --- 1. GÜNCELLENMİŞ ONESIGNAL BİLGİLERİ ---
ONESIGNAL_APP_ID = "89c0debc-c7a8-4ffe-9848-9405df878dd4"
ONESIGNAL_REST_KEY = "os_v2_app_rhan5pghvbh75gcisqc57b4n2tunkecvtjcufbmlqc2ftlrm46yqi4jsgq4ecnaaihpcytzbpwradw2aujhk72d7upp3burrixmxfpq"

def get_turkiye_saati():
    return datetime.utcnow() + timedelta(hours=3)

def push_bildirim_gonder(mesaj):
    header = {
        "Content-Type": "application/json; charset=utf-8", 
        "Authorization": "Basic " + ONESIGNAL_REST_KEY
    }
    payload = {
        "app_id": ONESIGNAL_APP_ID,
        "included_segments": ["Total Subscriptions"],
        "contents": {"tr": mesaj},
        "headings": {"tr": "Robotik Atölyesi Duyurusu"}
    }
    try:
        r = requests.post("https://api.onesignal.com/notifications", headers=header, json=payload)
        return r.status_code
    except:
        return 500

# --- 2. DOSYA YÖNETİMİ ---
FILES = {
    "data": "robotik_log.csv", 
    "users": "ogrenciler.csv", 
    "ban": "yarisma_ban.csv", 
    "duyuru": "duyuru.txt", 
    "logo": "logo.jpg"
}

def dosya_kontrol():
    if not os.path.exists(FILES["data"]) or os.stat(FILES["data"]).st_size == 0:
        pd.DataFrame(columns=["Zaman", "İsim", "İşlem", "Lehim", "Tip", "IP", "Puan"]).to_csv(FILES["data"], index=False)
    if not os.path.exists(FILES["users"]) or os.stat(FILES["users"]).st_size == 0:
        pd.DataFrame(columns=["Isim", "Sinif"]).to_csv(FILES["users"], index=False)
    if not os.path.exists(FILES["duyuru"]):
        with open(FILES["duyuru"], "w", encoding="utf-8") as f: f.write("Henüz duyuru yayınlanmadı.")

dosya_kontrol()

# --- 3. ZORUNLU BİLDİRİM İZNİ VE JS ---
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
          <div style="background:#0d1117; color:white; height:100vh; display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center; font-family:sans-serif;">
            <h2 style="color:#ff8c00;">Erişim İçin Bildirim İzni Gereklidir</h2>
            <p>Atölye duyurularını alabilmeniz için lütfen bildirimlere izin verin.</p>
            <button onclick="OneSignal.showNativePrompt()" style="background:#ff8c00; border:none; padding:12px 25px; color:white; border-radius:5px; font-weight:bold; cursor:pointer;">İzin Ver</button>
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
    .main-card { background: #161b22; padding: 20px; border-radius: 10px; border-left: 4px solid #ff8c00; margin-bottom: 20px; }
    .stButton button { background: #ff8c00; color: white; border-radius: 5px; width: 100%; border: none; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 5. MENÜ ---
df_users = pd.read_csv(FILES["users"])
df_logs = pd.read_csv(FILES["data"])

with st.sidebar:
    if os.path.exists(FILES["logo"]):
        st.image(FILES["logo"], use_container_width=True)
    secim = option_menu(None, ["Giriş", "Duyurular", "Sıralama", "Admin"], 
                        icons=['cpu', 'megaphone', 'award', 'shield-lock'], default_index=0)

# --- 6. SAYFALAR ---
if secim == "Giriş":
    st.title("Terminal")
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    if df_users.empty:
        st.info("Öğrenci listesi boş. Lütfen Admin panelinden ekleme yapın.")
    else:
        isimler = sorted(df_users["Isim"].tolist())
        secilen = st.selectbox("İsminiz:", ["Seçiniz..."] + isimler)
        islem = st.text_input("Yapılan Çalışma:")
        if st.button("Sisteme İşle"):
            if secilen != "Seçiniz...":
                zaman = get_turkiye_saati().strftime("%H:%M | %d-%m")
                pd.DataFrame([[zaman, secilen, islem, "HAYIR", "GİRİŞ", "127.0.0.1", 10]], columns=df_logs.columns).to_csv(FILES["data"], mode='a', index=False, header=False)
                st.success("Kayıt başarılı.")
                time.sleep(1)
                st.rerun()
            else:
                st.error("İsim seçilmedi.")
    st.markdown("</div>", unsafe_allow_html=True)

elif secim == "Duyurular":
    st.title("Atölye Duyuruları")
    with open(FILES["duyuru"], "r", encoding="utf-8") as f:
        icerik = f.read()
    st.markdown(f"<div class='main-card' style='font-size: 18px;'>{icerik}</div>", unsafe_allow_html=True)

elif secim == "Sıralama":
    st.title("Puan Durumu")
    if not df_logs.empty:
        skor = df_logs.groupby("İsim")["Puan"].sum().reset_index().sort_values("Puan", ascending=False)
        st.table(skor)
    else:
        st.write("Henüz veri yok.")

elif secim == "Admin":
    sifre = st.text_input("Şifre:", type="password")
    if sifre == "15531552":
        t1, t2, t3 = st.tabs(["Öğrenciler", "Duyuru Gönder", "Veri Yönetimi"])
        
        with t1:
            yeni_ad = st.text_input("Yeni Öğrenci Adı:")
            if st.button("Öğrenci Ekle"):
                pd.DataFrame([[yeni_ad, "10"]], columns=["Isim", "Sinif"]).to_csv(FILES["users"], mode='a', index=False, header=False)
                st.success("Eklendi.")
                st.rerun()
            
            st.write("---")
            if not df_users.empty:
                sil_ad = st.selectbox("Silinecek Öğrenci:", df_users["Isim"].tolist())
                if st.button("Kayıt Sil"):
                    df_u_yeni = df_users[df_users["Isim"] != sil_ad]
                    df_u_yeni.to_csv(FILES["users"], index=False)
                    st.warning("Silindi.")
                    st.rerun()

        with t2:
            st.subheader("Yeni Duyuru ve Bildirim")
            mesaj = st.text_area("Mesaj metni:")
            if st.button("Yayınla"):
                if mesaj:
                    with open(FILES["duyuru"], "w", encoding="utf-8") as f:
                        f.write(mesaj)
                    kod = push_bildirim_gonder(mesaj)
                    if kod == 200:
                        st.success("Duyuru yayınlandı ve bildirim gönderildi.")
                    else:
                        st.error(f"Bildirim Hatası. Kod: {kod}")
                else:
                    st.error("Metin girilmedi.")

        with t3:
            if st.button("Giriş Loglarını Sıfırla"):
                pd.DataFrame(columns=df_logs.columns).to_csv(FILES["data"], index=False)
                st.success("Veriler temizlendi.")
                st.rerun()
