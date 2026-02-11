import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime, timedelta

# --- 1. AYARLAR ---
WEBPUSHR_KEY = "BCE7SJuELLpGqUp7Xt3R7PpMCnR3admiEEHit8oRIyaf5UfRGGRxiaxo2xV17U-BbuSnMrjxIIiruQivccEcSm8"

def get_turkiye_saati():
    return datetime.utcnow() + timedelta(hours=3)

# --- 2. WEBPUSHR JAVASCRIPT ---
# Bu kod öğrencilerin cihazını Webpushr sistemine kaydeder.
st.markdown(f"""
<script>
(function(w,d, s, id) {{
    if(typeof(w.webpushr)!=='undefined') return;
    w.webpushr=w.webpushr||function(){{(w.webpushr.q=w.webpushr.q||[]).push(arguments)}};
    var js, fjs = d.getElementsByTagName(s)[0];
    js = d.createElement(s); js.id = id;js.async=1;
    js.src = "https://cdn.webpushr.com/app.min.js";
    fjs.parentNode.appendChild(js);
}}(window,document, 'script', 'webpushr-jssdk'));

webpushr('setup',{{'key':'{WEBPUSHR_KEY}' }});

// Kullanıcı giriş yapınca ismi Webpushr'a 'sid' (Subscriber ID) olarak gönderelim
window.cihazKaydet = function(isim) {{
    webpushr('attributes', {{"name": isim}});
    console.log("Cihaz " + isim + " adına kaydedildi.");
}};
</script>
""", unsafe_allow_html=True)

# --- 3. DOSYA YÖNETİMİ ---
FILES = {"data": "robotik_log.csv", "users": "ogrenciler.csv"}

def veri_yukle(t):
    yol = FILES[t]
    if not os.path.exists(yol) or os.stat(yol).st_size == 0:
        cols = ["Zaman", "İsim", "İşlem", "Puan"] if t=="data" else ["Isim", "Puan"]
        df = pd.DataFrame(columns=cols)
        df.to_csv(yol, index=False)
        return df
    return pd.read_csv(yol)

# --- 4. TASARIM ---
st.markdown("""
<style>
    .stApp { background-color: #0d1117; color: #c9d1d9; }
    .main-card { background: #161b22; padding: 20px; border-radius: 10px; border-top: 4px solid #00a2ff; }
    .stButton button { background: #00a2ff; color: white; width: 100%; font-weight: bold; border: none; }
</style>
""", unsafe_allow_html=True)

# --- 5. ARAYÜZ ---
st.title("🤖 Robotik Atölye Terminali")

tab1, tab2 = st.tabs(["Giriş Paneli", "Admin (Mesaj Gönder)"])

with tab1:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    df_u = veri_yukle("users")
    
    if df_u.empty:
        st.warning("Henüz öğrenci eklenmemiş. Admin panelinden ekleyin.")
    else:
        isimler = sorted(df_u["Isim"].astype(str).tolist())
        secilen = st.selectbox("İsminizi Seçin:", ["Seçiniz..."] + isimler)
        islem = st.text_input("Şu an ne yapıyorsun?")
        
        if st.button("Sisteme Giriş Yap"):
            if secilen != "Seçiniz...":
                # Cihazı Webpushr'da bu isimle işaretle
                st.markdown(f"<script>window.cihazKaydet('{secilen}');</script>", unsafe_allow_html=True)
                
                # Log kaydı
                zaman = get_turkiye_saati().strftime("%H:%M | %d-%m")
                df_l = veri_yukle("data")
                yeni_log = pd.DataFrame([[zaman, secilen, islem, 10]], columns=df_l.columns)
                yeni_log.to_csv(FILES["data"], mode='a', index=False, header=False)
                
                st.success(f"Hoş geldin {secilen}! Girişin kaydedildi.")
                time.sleep(1)
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    sifre = st.text_input("Yönetici Şifresi:", type="password")
    if sifre == "15531552":
        st.subheader("📢 Duyuru Yönetimi")
        st.info("Mesaj göndermek için Webpushr panelini kullanacağız. Aşağıdaki butona basarak panele gidebilirsin.")
        
        st.markdown("[🚀 Webpushr Paneline Git (Bildirim At)](https://dashboard.webpushr.com/)", unsafe_allow_html=True)
        
        st.write("---")
        st.write("### Yeni Öğrenci Ekle")
        yeni_ad = st.text_input("Ad Soyad:")
        if st.button("Öğrenciyi Kaydet"):
            if yeni_ad:
                df_u = veri_yukle("users")
                pd.DataFrame([[yeni_ad, 10]], columns=df_u.columns).to_csv(FILES["users"], mode='a', index=False, header=False)
                st.success(f"{yeni_ad} eklendi.")
                st.rerun()
