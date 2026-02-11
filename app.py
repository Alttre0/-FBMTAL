import streamlit as st
import pandas as pd
import requests
import os

# --- AYARLAR ---
APP_ID = "89c0debc-c7a8-4ffe-9848-9405df878dd4"
REST_KEY = "BURAYA_REST_API_KEY_YAPISTIR" # <--- BURAYI DOLDUR

def mesaj_at(kullanici_id, mesaj_metni):
    header = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"Basic {REST_KEY}"
    }
    payload = {
        "app_id": APP_ID,
        "include_external_user_ids": [kullanici_id],
        "contents": {"tr": mesaj_metni},
        "headings": {"tr": "Test Bildirimi"}
    }
    r = requests.post("https://api.onesignal.com/notifications", headers=header, json=payload)
    return r.status_code

# --- JS: CİHAZI İSİMLE DAMGALA ---
def cihaz_kaydet(isim):
    st.markdown(f"""
    <script>
      window.OneSignal = window.OneSignal || [];
      OneSignal.push(function() {{
        OneSignal.setExternalUserId("{isim}");
      }});
    </script>
    """, unsafe_allow_html=True)

# --- BASİT VERİ TABANI ---
if not os.path.exists("test_users.csv"):
    pd.DataFrame({"Isim": ["Test_Kullanici", "Ogrenci_1", "Hoca"]}).to_csv("test_users.csv", index=False)

df = pd.read_csv("test_users.csv")

# --- ARAYÜZ ---
st.title("🔔 Tekli Bildirim Testi")

tab1, tab2 = st.tabs(["1. Giriş (Cihazı Kaydet)", "2. Mesaj Gönder"])

with tab1:
    secilen = st.selectbox("Test için isim seç:", df["Isim"])
    if st.button("Bu Cihazı Bu İsimle Kaydet"):
        cihaz_kaydet(secilen)
        st.success(f"Bu tarayıcı artık '{secilen}' olarak OneSignal'a bildirildi.")
        st.info("Şimdi diğer sekmeye geçip kendine mesaj atabilirsin.")

with tab2:
    st.subheader("Kayıtlı Cihaza Mesaj At")
    hedef = st.selectbox("Kime gitsin:", df["Isim"])
    mesaj = st.text_input("Mesaj içeriği:", value="Test mesajı başarılı!")
    
    if st.button("Sadece Bu Kişiye Gönder"):
        if REST_KEY == "BURAYA_REST_API_KEY_YAPISTIR":
            st.error("Önce koddaki REST_KEY kısmını doldurmalısın!")
        else:
            sonuc = mesaj_at(hedef, mesaj)
            if sonuc == 200:
                st.balloons()
                st.success(f"Bildirim {hedef} isimli cihazın ekranına gönderildi!")
            else:
                st.error(f"Hata oluştu! Kod: {sonuc}. API anahtarın yanlış olabilir.")

# Bildirim izni isteme (Eğer daha önce verilmediyse)
st.markdown(f"""
<script src="https://cdn.onesignal.com/sdks/web/v16/OneSignalSDK.sw.js" defer></script>
<script src="https://cdn.onesignal.com/sdks/OneSignalSDK.js" async=""></script>
<script>
  window.OneSignal = window.OneSignal || [];
  OneSignal.push(function() {{
    OneSignal.init({{ appId: "{APP_ID}", allowLocalhostAsSecureOrigin: true }});
  }});
</script>
""", unsafe_allow_html=True)
