import streamlit as st
import pandas as pd
import requests
import os
import time
from datetime import datetime, timedelta
from streamlit_option_menu import option_menu

# --- 1. AYARLAR ---
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
        "headings": {"tr": "Robotik Atölyesi"}
    }
    r = requests.post("https://api.onesignal.com/notifications", headers=header, json=payload)
    return r.status_code

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
    if not os.path.exists(FILES["ban"]) or os.stat(FILES["ban"]).st_size == 0:
        pd.DataFrame(columns=["IP", "Isim", "Sebep"]).to_csv(FILES["ban"], index=False)
    if not os.path.exists(FILES["duyuru"]):
        with open(FILES["duyuru"], "w", encoding="utf-8") as f: f.write("Yeni duyuru bulunmuyor.")

dosya_kontrol()

# --- 3. BİLDİRİM İZNİ (ZORUNLU) ---
onesignal_js = """
<script src="https://cdn.onesignal.com/sdks/web/v16/OneSignalSDK.sw.js" defer></script>
<script src="https://cdn.onesignal.com/sdks/OneSignalSDK.js" async=""></script>
<script>
  window.OneSignal = window.OneSignal || [];
  OneSignal.push(function() {
    OneSignal.init({
      appId: "%s",
      allowLocalhostAsSecureOrigin: true,
      promptOptions: { slidedown: { enabled: true, autoPrompt: true, timeDelay: 2 } }
    });
    OneSignal.isPushNotificationsEnabled(function(isEnabled) {
      if (!isEnabled) {
        document.body.innerHTML = '<div style="background:#0d1117; color:white; height:100vh; display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center; font-family:sans-serif; padding:20px;"><h1>ERİŞİM KISITLANDI</h1><p>Sistemi kullanmak için bildirimlere izin vermeniz gerekmektedir.</p><button onclick="OneSignal.showNativePrompt()" style="background:#ff8c00; border:none; padding:15px 30px; color:white; border-radius:10px; cursor:pointer;">İzin Ver</button></div>';
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

# --- 5. VERİ YÜKLEME ---
df_logs = pd.read_csv(FILES["data"])
df_users = pd.read_csv(FILES["users"])
df_ban = pd.read_csv(FILES["ban"])

# --- 6. MENÜ ---
with st.sidebar:
    if os.path.exists(FILES["logo"]):
        st.image(FILES["logo"], use_container_width=True)
    secim = option_menu(None, ["Giriş", "Duyurular", "Sıralama", "Admin"], 
                        icons=['cpu', 'megaphone', 'award', 'shield-lock'], default_index=0)

# --- 7. SAYFALAR ---
if secim == "Giriş":
    st.title("Terminal Girişi")
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    if df_users.empty:
        st.warning("Sistemde kayıtlı öğrenci bulunamadı. Lütfen Admin panelinden ekleme yapın.")
    else:
        isim_listesi = sorted(df_users["Isim"].tolist())
        secilen = st.selectbox("İsminiz:", ["Seçiniz..."] + isim_listesi)
        islem = st.text_input("Yapılan İşlem:")
        if st.button("Kaydı Onayla"):
            if secilen != "Seçiniz...":
                zaman = get_turkiye_saati().strftime("%H:%M | %d-%m")
                yeni_kayit = pd.DataFrame([[zaman, secilen, islem, "HAYIR", "GİRİŞ", "127.0.0.1", 10]], columns=df_logs.columns)
                yeni_kayit.to_csv(FILES["data"], mode='a', index=False, header=False)
                st.success("Kayıt işlemi başarılı.")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Lütfen bir isim seçin.")
    st.markdown("</div>", unsafe_allow_html=True)

elif secim == "Duyurular":
    st.title("Duyuru Panosu")
    with open(FILES["duyuru"], "r", encoding="utf-8") as f:
        icerik = f.read()
    st.markdown(f"<div class='main-card' style='font-size: 18px;'>{icerik}</div>", unsafe_allow_html=True)

elif secim == "Sıralama":
    st.title("Puan Sıralaması")
    if not df_logs.empty:
        puanlar = df_logs.groupby("İsim")["Puan"].sum().reset_index().sort_values("Puan", ascending=False)
        st.table(puanlar)
    else:
        st.info("Henüz veri bulunmuyor.")

elif secim == "Admin":
    sifre = st.text_input("Admin Şifresi:", type="password")
    if sifre == "15531552":
        sekme1, sekme2, sekme3 = st.tabs(["Öğrenci Yönetimi", "Duyuru Paylaşımı", "Veri Temizleme"])
        
        with sekme1:
            st.subheader("Öğrenci Ekle")
            yeni_ad = st.text_input("Ad Soyad:")
            if st.button("Öğrenciyi Kaydet"):
                if yeni_ad:
                    pd.DataFrame([[yeni_ad, "Atölye"]], columns=["Isim", "Sinif"]).to_csv(FILES["users"], mode='a', index=False, header=False)
                    st.success("Öğrenci eklendi.")
                    st.rerun()

            st.write("---")
            st.subheader("Öğrenci Sil")
            if not df_users.empty:
                silinecek = st.selectbox("Silinecek Öğrenci:", df_users["Isim"].tolist())
                if st.button("Seçili Öğrenciyi Sil"):
                    yeni_df = df_users[df_users["Isim"] != silinecek]
                    yeni_df.to_csv(FILES["users"], index=False)
                    st.warning("Öğrenci sistemden kaldırıldı.")
                    st.rerun()

        with sekme2:
            st.subheader("Duyuru Yayınla")
            duyuru_metni = st.text_area("Mesaj içeriği:")
            if st.button("Duyuruyu Gönder"):
                if duyuru_metni:
                    with open(FILES["duyuru"], "w", encoding="utf-8") as f:
                        f.write(duyuru_metni)
                    durum = push_bildirim_gonder(duyuru_metni)
                    if durum == 200:
                        st.success("Duyuru yayınlandı ve bildirim gönderildi.")
                    else:
                        st.error(f"Bildirim hatası. Kod: {durum}")
                else:
                    st.warning("Mesaj alanı boş bırakılamaz.")

        with sekme3:
            st.subheader("Sistem Verileri")
            if st.button("Tüm Kayıtları Sıfırla"):
                pd.DataFrame(columns=df_logs.columns).to_csv(FILES["data"], index=False)
                st.success("Tüm giriş kayıtları temizlendi.")
                st.rerun()
