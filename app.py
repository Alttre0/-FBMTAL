import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime, timedelta
from streamlit_option_menu import option_menu

# --- 1. AYARLAR ---
# OneSignal sadece "altyapı" olarak kalıyor, tarayıcıyla direkt konuşacağız.
ONESIGNAL_APP_ID = "89c0debc-c7a8-4ffe-9848-9405df878dd4"

def get_turkiye_saati():
    return datetime.utcnow() + timedelta(hours=3)

# --- 2. JAVASCRIPT: BİLDİRİM İZNİNİ KİLİTLEYİCİ ---
# Eğer izin verilmediyse Python'a "blocked" mesajı gönderir.
st.markdown(f"""
<script src="https://cdn.onesignal.com/sdks/web/v16/OneSignalSDK.sw.js" defer></script>
<script src="https://cdn.onesignal.com/sdks/OneSignalSDK.js" async=""></script>
<script>
  window.OneSignal = window.OneSignal || [];
  OneSignal.push(function() {{
    OneSignal.init({{
      appId: "{ONESIGNAL_APP_ID}",
      allowLocalhostAsSecureOrigin: true,
      autoResubscribe: true
    }});

    function updateStatus() {{
        OneSignal.getNotificationPermission(function(permission) {{
            const input = window.parent.document.querySelector('input[aria-label="perm_status"]');
            if (input) {{
                input.value = permission;
                input.dispatchEvent(new Event('input', {{ bubbles: true }}));
            }}
        }});
    }}
    
    setInterval(updateStatus, 1000);
    window.zorlaIzin = function() {{ OneSignal.showNativePrompt(); }};
  }});
</script>
""", unsafe_allow_html=True)

# --- 3. DOSYA YÖNETİMİ ---
FILES = {"data": "robotik_log.csv", "users": "ogrenciler.csv", "duyuru": "duyuru.txt"}

def veri_yukle(dosya_turu):
    yol = FILES[dosya_turu]
    cols = ["Zaman", "İsim", "İşlem", "Puan"] if dosya_turu == "data" else ["Isim", "Sinif"]
    if not os.path.exists(yol) or os.stat(yol).st_size == 0:
        pd.DataFrame(columns=cols).to_csv(yol, index=False)
        return pd.DataFrame(columns=cols)
    return pd.read_csv(yol)

# --- 4. TASARIM ---
st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: #c9d1d9; }
    .izin-kart { background: #1c2128; border: 2px solid #ff3e3e; padding: 30px; border-radius: 15px; text-align: center; margin-top: 50px; }
    .stButton button { width: 100%; height: 50px; font-weight: bold; }
    div[data-testid="stInput"] { display: none; }
    </style>
    """, unsafe_allow_html=True)

perm_status = st.text_input("perm_status", value="default", label_visibility="collapsed")

# --- 5. ANA MANTIK (İZİN KONTROLÜ) ---
if perm_status != "granted":
    st.markdown('<div class="izin-kart">', unsafe_allow_html=True)
    st.error("🛑 SİSTEM ERİŞİMİ ENGELLENDİ!")
    st.warning("Bildirimleri almayı kabul etmeden giriş yapamazsınız.")
    if st.button("🔔 BİLDİRİM İZNİNİ ŞİMDİ VER"):
        st.markdown('<script>window.zorlaIzin();</script>', unsafe_allow_html=True)
    st.info("Eğer pencere açılmıyorsa adres çubuğundaki kilit (🔒) simgesinden izinleri sıfırlayıp sayfayı yenileyin.")
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop() # Sayfanın geri kalanını yükleme

# --- 6. MENÜ VE SAYFALAR (Sadece izin verenler burayı görür) ---
with st.sidebar:
    secim = option_menu("Atölye", ["Giriş", "Admin"], icons=['cpu', 'shield-lock'], default_index=0)

if secim == "Giriş":
    st.title("Robotik Terminal")
    df_u = veri_yukle("users")
    if not df_u.empty:
        secilen = st.selectbox("İsim:", ["Seçiniz..."] + sorted(df_u["Isim"].tolist()))
        islem = st.text_input("İşlem:")
        if st.button("Onayla"):
            if secilen != "Seçiniz...":
                zaman = get_turkiye_saati().strftime("%H:%M | %d-%m")
                pd.DataFrame([[zaman, secilen, islem, 10]], columns=veri_yukle("data").columns).to_csv(FILES["data"], mode='a', index=False, header=False)
                st.success("Kayıt yapıldı.")
                time.sleep(1); st.rerun()

elif secim == "Admin":
    sifre = st.text_input("Şifre:", type="password")
    if sifre == "15531552":
        st.subheader("Duyuru Yayınla")
        st.info("Duyuruyu buradan yayınlayın, sonra OneSignal sitesinden Push atın.")
        mesaj = st.text_area("Mesaj:")
        if st.button("Pano Güncelle"):
            with open(FILES["duyuru"], "w", encoding="utf-8") as f: f.write(mesaj)
            st.success("Pano güncellendi.")
