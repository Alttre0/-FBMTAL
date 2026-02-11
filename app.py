import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime, timedelta
from streamlit_option_menu import option_menu

# --- 1. AYARLAR ---
ONESIGNAL_APP_ID = "89c0debc-c7a8-4ffe-9848-9405df878dd4"

def get_turkiye_saati():
    return datetime.utcnow() + timedelta(hours=3)

# --- 2. JAVASCRIPT: PYTHON İLE KONUŞMA ---
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

    function checkAndReport() {{
        OneSignal.getNotificationPermission(function(permission) {{
            const input = window.parent.document.querySelector('input[aria-label="perm_status"]');
            if (input && input.value !== permission) {{
                input.value = permission;
                input.dispatchEvent(new Event('input', {{ bubbles: true }}));
            }}
        }});
    }}
    setInterval(checkAndReport, 1000);
    window.zorla = function() {{ OneSignal.showNativePrompt(); }};
  }});
</script>
""", unsafe_allow_html=True)

# --- 3. TASARIM ---
st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: #c9d1d9; }
    .izin-kart { background: #1c2128; border: 2px solid #ff8c00; padding: 25px; border-radius: 15px; text-align: center; }
    div[data-testid="stInput"] { display: none; }
    </style>
    """, unsafe_allow_html=True)

# Gizli input (JS buraya yazar)
perm_status = st.text_input("perm_status", value="default", label_visibility="collapsed")

# --- 4. DOSYA YÜKLEME ---
FILES = {"data": "robotik_log.csv", "users": "ogrenciler.csv", "duyuru": "duyuru.txt"}
def veri_yukle(t):
    if not os.path.exists(FILES[t]) or os.stat(FILES[t]).st_size == 0:
        cols = ["Zaman", "İsim", "İşlem", "Puan"] if t=="data" else ["Isim", "Sinif"]
        pd.DataFrame(columns=cols).to_csv(FILES[t], index=False)
        return pd.DataFrame(columns=cols)
    return pd.read_csv(FILES[t])

# --- 5. ANA EKRAN KONTROLÜ ---
# Eğer JS hala "default" diyorsa ama sen kilitte "İzin Verildi" görüyorsan, manuel geçiş sunuyoruz.
if perm_status != "granted":
    st.markdown('<div class="izin-kart">', unsafe_allow_html=True)
    st.header("🔔 Bildirim Onayı")
    st.write("Tarayıcında izin verildi görünüyor olabilir. Eğer pencere açılmıyorsa aşağıdaki butona basarak sisteme giriş yapabilirsin.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Pencereyi Aç"):
            st.markdown('<script>window.zorla();</script>', unsafe_allow_html=True)
    with col2:
        if st.button("Zaten İzin Verdim (Giriş Yap)"):
            # Bu buton perm_status'ü zorla "granted" yapar (Sadece bu oturum için)
            st.session_state["force_login"] = True
            st.rerun()
    
    st.info("İzin verdiysen ve hala buradaysan sağdaki butona tıkla.")
    st.markdown('</div>', unsafe_allow_html=True)
    
    if "force_login" not in st.session_state:
        st.stop()

# --- 6. SİSTEM (GİRİŞ YAPANLAR İÇİN) ---
with st.sidebar:
    secim = option_menu("Atölye", ["Giriş", "Admin"], icons=['cpu', 'lock'], default_index=0)

if secim == "Giriş":
    st.title("Atölye Terminali")
    df_u = veri_yukle("users")
    if not df_u.empty:
        secilen = st.selectbox("İsminiz:", ["Seçiniz..."] + sorted(df_u["Isim"].astype(str).tolist()))
        islem = st.text_input("Çalışma konusu:")
        if st.button("Kaydet"):
            if secilen != "Seçiniz...":
                zaman = get_turkiye_saati().strftime("%H:%M")
                pd.DataFrame([[zaman, secilen, islem, 10]], columns=veri_yukle("data").columns).to_csv(FILES["data"], mode='a', index=False, header=False)
                st.success("Başarıyla kaydedildi.")
                time.sleep(1); st.rerun()

elif secim == "Admin":
    sifre = st.text_input("Şifre:", type="password")
    if sifre == "15531552":
        st.subheader("Öğrenci Kaydı")
        yeni = st.text_input("Ad Soyad:")
        if st.button("Ekle"):
            pd.DataFrame([[yeni, "10"]], columns=veri_yukle("users").columns).to_csv(FILES["users"], mode='a', index=False, header=False)
            st.success("Öğrenci eklendi.")
