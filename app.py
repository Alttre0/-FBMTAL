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

# --- 2. DOSYA VE VERİ KONTROLÜ (HATA ÖNLEYİCİ) ---
FILES = {"data": "robotik_log.csv", "users": "ogrenciler.csv", "duyuru": "duyuru.txt"}

def veri_yukle(dosya_turu):
    yol = FILES[dosya_turu]
    cols = ["Zaman", "İsim", "İşlem", "Bildirim_Izni", "Puan"] if dosya_turu == "data" else ["Isim", "Sinif", "Son_Bildirim_Durumu"]
    
    if not os.path.exists(yol) or os.stat(yol).st_size == 0:
        df = pd.DataFrame(columns=cols)
        df.to_csv(yol, index=False)
        return df
    try:
        return pd.read_csv(yol)
    except:
        return pd.DataFrame(columns=cols)

# Dosyaları başta bir kez kontrol et
df_users = veri_yukle("users")
df_logs = veri_yukle("data")

# --- 3. BİLDİRİM İZNİ VE GİZLİ HABERLEŞME ---
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
      promptOptions: {{ slidedown: {{ enabled: true, autoPrompt: true, timeDelay: 1 }} }}
    }});

    // İzni periyodik olarak kontrol et ve gizli inputa yaz
    setInterval(function() {{
        OneSignal.getNotificationPermission(function(permission) {{
            const input = window.parent.document.querySelector('input[aria-label="perm_status"]');
            if (input && input.value !== permission) {{
                input.value = permission;
                input.dispatchEvent(new Event('input', {{ bubbles: true }}));
            }}
        }});
    }}, 1000);
  }});

  function triggerNotify() {{
      OneSignal.push(function() {{ OneSignal.showNativePrompt(); }});
  }}
</script>
""", unsafe_allow_html=True)

# --- 4. TASARIM ---
st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: #c9d1d9; }
    .main-card { background: #161b22; padding: 20px; border-radius: 10px; border-left: 4px solid #ff8c00; margin-bottom: 20px; }
    .stButton button { background: #ff8c00; color: white; border-radius: 5px; width: 100%; font-weight: bold; }
    div[data-testid="stInput"] { display: none; }
    </style>
    """, unsafe_allow_html=True)

perm_status = st.text_input("perm_status", value="default", label_visibility="collapsed")

# --- 5. MENÜ ---
with st.sidebar:
    secim = option_menu("Robotik Hub", ["Giriş", "Admin"], icons=['cpu', 'shield-lock'], default_index=0)

# --- 6. SAYFALAR ---
if secim == "Giriş":
    st.title("Terminal")
    
    # İzin kontrolü ve uyarı
    if perm_status != "granted":
        st.warning("Bildirim izni vermeniz gerekiyor.")
        st.markdown('<button onclick="triggerNotify()" style="width:100%; padding:12px; background:#ff8c00; color:white; border:none; border-radius:5px; cursor:pointer;">İzin Penceresini Aç</button>', unsafe_allow_html=True)
        st.info("Eğer pencere gelmiyorsa: Adres çubuğundaki kilit (🔒) simgesinden bildirimlere izin ver.")

    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    if df_users.empty:
        st.info("Sistemde öğrenci yok. Önce Admin panelinden ekleyin.")
    else:
        secilen = st.selectbox("İsminiz:", ["Seçiniz..."] + sorted(df_users["Isim"].tolist()))
        islem = st.text_input("Yapılan İş:")
        
        if st.button("Kaydı Onayla"):
            if secilen != "Seçiniz...":
                zaman = get_turkiye_saati().strftime("%H:%M | %d-%m")
                durum = "Verildi" if perm_status == "granted" else "Verilmedi"
                
                # Kayıt
                pd.DataFrame([[zaman, secilen, islem, durum, 10]], columns=df_logs.columns).to_csv(FILES["data"], mode='a', index=False, header=False)
                df_users.loc[df_users["Isim"] == secilen, "Son_Bildirim_Durumu"] = durum
                df_users.to_csv(FILES["users"], index=False)
                
                st.success("Kayıt başarılı!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Lütfen bir isim seçin.")
    st.markdown("</div>", unsafe_allow_html=True)

elif secim == "Admin":
    sifre = st.text_input("Şifre:", type="password")
    if sifre == "15531552":
        st.subheader("Öğrenci Listesi ve Bildirim İzinleri")
        st.dataframe(df_users[["Isim", "Son_Bildirim_Durumu"]], use_container_width=True)
        
        yeni_ad = st.text_input("Yeni Öğrenci Ad Soyad:")
        if st.button("Öğrenci Ekle"):
            if yeni_ad:
                pd.DataFrame([[yeni_ad, "10", "Bilinmiyor"]], columns=df_users.columns).to_csv(FILES["users"], mode='a', index=False, header=False)
                st.rerun()
