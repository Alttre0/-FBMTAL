import streamlit as st
import pandas as pd
import requests
import os
import time
from datetime import datetime, timedelta
from streamlit_option_menu import option_menu

# --- 1. AYARLAR ---
ONESIGNAL_APP_ID = "89c0debc-c7a8-4ffe-9848-9405df878dd4"
ONESIGNAL_REST_KEY = "os_v2_app_rhan5pghvbh75gcisqc57b4n2tunkecvtjcufbmlqc2ftlrm46yqi4jsgq4ecnaaihpcytzbpwradw2aujhk72d7upp3burrixmxfpq"

def get_turkiye_saati():
    return datetime.utcnow() + timedelta(hours=3)

# --- 2. JAVASCRIPT: PENCEREYİ ZORLA AÇ ---
# Hem slidedown hem de native prompt deniyoruz
st.markdown(f"""
<script src="https://cdn.onesignal.com/sdks/web/v16/OneSignalSDK.sw.js" defer></script>
<script src="https://cdn.onesignal.com/sdks/OneSignalSDK.js" async=""></script>
<script>
  window.OneSignal = window.OneSignal || [];
  OneSignal.push(function() {{
    OneSignal.init({{
      appId: "{ONESIGNAL_APP_ID}",
      allowLocalhostAsSecureOrigin: true,
      autoResubscribe: true,
      promptOptions: {{
        slidedown: {{
          enabled: true,
          autoPrompt: true,
          timeDelay: 1
        }}
      }}
    }});

    // Pencereyi zorla tetikle
    setTimeout(function() {{
        OneSignal.showNativePrompt();
    }}, 2000);

    // İzin durumunu kontrol et ve gizli inputa yaz
    setInterval(function() {{
        OneSignal.getNotificationPermission(function(permission) {{
            const input = window.parent.document.querySelector('input[aria-label="perm_status"]');
            if (input) {{
                input.value = permission;
                input.dispatchEvent(new Event('input', {{ bubbles: true }}));
            }}
        }});
    }}, 1000);
  }});

  // Manuel tetikleme fonksiyonu
  function forcePrompt() {{
      OneSignal.push(function() {{
          OneSignal.showNativePrompt();
      }});
  }}
</script>
""", unsafe_allow_html=True)

# --- 3. TASARIM ---
st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: #c9d1d9; }
    .main-card { background: #161b22; padding: 20px; border-radius: 10px; border-left: 4px solid #ff8c00; margin-bottom: 20px; }
    .stButton button { background: #ff8c00; color: white; border-radius: 5px; width: 100%; border: none; font-weight: bold; }
    div[data-testid="stInput"] { display: none; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. VERİ YÜKLEME ---
FILES = {"data": "robotik_log.csv", "users": "ogrenciler.csv", "duyuru": "duyuru.txt"}
for f in [FILES["data"], FILES["users"]]:
    if not os.path.exists(f): 
        pd.DataFrame(columns=["Zaman", "İsim", "İşlem", "Bildirim_Izni", "Puan"] if "log" in f else ["Isim", "Sinif", "Son_Bildirim_Durumu"]).to_csv(f, index=False)

df_users = pd.read_csv(FILES["users"])
df_logs = pd.read_csv(FILES["data"])
perm_status = st.text_input("perm_status", value="default", label_visibility="collapsed")

# --- 5. MENÜ ---
with st.sidebar:
    secim = option_menu(None, ["Giriş", "Admin"], icons=['cpu', 'shield-lock'], default_index=0)

# --- 6. SAYFALAR ---
if secim == "Giriş":
    st.title("Atölye Kayıt")
    
    if perm_status != "granted":
        st.error("Bildirim izni algılanmadı!")
        st.markdown('<button onclick="forcePrompt()" style="width:100%; padding:15px; background:#ff8c00; color:white; border:none; border-radius:5px; cursor:pointer; font-weight:bold;">BİLDİRİM İZNİNİ ŞİMDİ VER</button>', unsafe_allow_html=True)
        st.info("Eğer butona bastığında pencere açılmıyorsa, tarayıcı adres çubuğundaki KİLİT 🔒 simgesine tıkla ve bildirimleri 'İzin Ver' yap.")
    
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    if not df_users.empty:
        secilen = st.selectbox("İsminiz:", ["Seçiniz..."] + sorted(df_users["Isim"].tolist()))
        islem = st.text_input("İşlem:")
        if st.button("Sisteme İşle"):
            if secilen != "Seçiniz...":
                zaman = get_turkiye_saati().strftime("%H:%M | %d-%m")
                durum = "Verildi" if perm_status == "granted" else "Verilmedi"
                pd.DataFrame([[zaman, secilen, islem, durum, 10]], columns=df_logs.columns).to_csv(FILES["data"], mode='a', index=False, header=False)
                df_users.loc[df_users["Isim"] == secilen, "Son_Bildirim_Durumu"] = durum
                df_users.to_csv(FILES["users"], index=False)
                st.success("Kayıt yapıldı.")
                time.sleep(1); st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

elif secim == "Admin":
    sifre = st.text_input("Şifre:", type="password")
    if sifre == "15531552":
        st.subheader("Öğrenci ve Bildirim Takibi")
        st.table(df_users[["Isim", "Son_Bildirim_Durumu"]])
        
        yeni = st.text_input("Yeni Öğrenci:")
        if st.button("Ekle"):
            pd.DataFrame([[yeni, "10", "Bilinmiyor"]], columns=df_users.columns).to_csv(FILES["users"], mode='a', index=False, header=False)
            st.rerun()
