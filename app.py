import streamlit as st
import pandas as pd
from datetime import datetime
import os
from streamlit_option_menu import option_menu
from PIL import Image

# --- 1. AYARLAR ---
st.set_page_config(page_title="İrfan Bileydi Robotik", page_icon="🤖", layout="wide")

# --- 2. DOSYA YÖNETİMİ ---
FILES = {
    "data": "robotik_log.csv",
    "ban": "yarisma_ban.csv",
    "duyuru": "duyuru.txt",
    "logo": "logo.jpg" # Uzantıyı .jpg olarak güncelledik
}

# Veritabanı Onarma (Hata almanı engeller)
def db_check():
    if not os.path.exists(FILES["data"]):
        pd.DataFrame(columns=["Zaman", "İsim", "İşlem", "Lehim", "Tip", "IP", "Puan"]).to_csv(FILES["data"], index=False)
    else:
        df = pd.read_csv(FILES["data"])
        if "Puan" not in df.columns:
            df["Puan"] = 0
            df.to_csv(FILES["data"], index=False)

db_check()
if not os.path.exists(FILES["ban"]): pd.DataFrame(columns=["IP", "Isim", "Sebep"]).to_csv(FILES["ban"], index=False)
if not os.path.exists(FILES["duyuru"]):
    with open(FILES["duyuru"], "w", encoding="utf-8") as f: f.write("Robotik Atölyesine Hoş Geldiniz!")

# --- 3. ÖZEL TEMA ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #c9d1d9; }
    h1, h2 { color: #ff8c00; font-family: 'Arial Black', sans-serif; }
    .stButton button { 
        background: linear-gradient(45deg, #ff8c00, #ff4500); 
        color: white; border-radius: 12px; font-weight: bold; border: none;
    }
    .footer {
        position: fixed; left: 0; bottom: 0; width: 100%;
        background-color: #161b22; color: #8b949e; text-align: center;
        padding: 8px; font-size: 14px; border-top: 1px solid #30363d; z-index: 100;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. YAN MENÜ VE LOGO ---
with st.sidebar:
    # Yerel Logo Kontrolü
    if os.path.exists(FILES["logo"]):
        st.image(FILES["logo"], use_container_width=True)
    else:
        st.error(f"'{FILES['logo']}' bulunamadı!")
        st.info("Lütfen resmin adını tam olarak 'logo.jpg' yapıp klasöre at.")
    
    st.markdown("<h3 style='text-align: center;'>İRFAN BİLEYDİ MTAL</h3>", unsafe_allow_html=True)
    
    secim = option_menu(None, ["Giriş Ekranı", "Duyuru Panosu", "Liderlik", "Admin"], 
        icons=['cpu', 'megaphone', 'award', 'lock'], 
        menu_icon="cast", default_index=0,
        styles={"nav-link-selected": {"background-color": "#ff8c00"}})

# --- 5. SAYFALAR ---

if secim == "Giriş Ekranı":
    st.title("📟 Robotik Terminali")
    with open(FILES["duyuru"], "r", encoding="utf-8") as f: d_txt = f.read()
    st.warning(f"🔔 **DUYURU:** {d_txt}")

    col1, col2 = st.columns([2, 1])
    with col1:
        ad = st.text_input("Ad Soyad:")
        islem = st.text_area("Yapılan Çalışma:")
    with col2:
        st.write("")
        lehim = st.toggle("🔥 Lehim Kullandım")
        tip = st.radio("İşlem:", ["GİRİŞ", "ÇIKIŞ"])
    
    if st.button("KAYDET"):
        if ad:
            zaman = datetime.now().strftime("%H:%M | %d-%m")
            puan = 10 if tip == "GİRİŞ" else 0
            yeni = pd.DataFrame([[zaman, ad, islem, ("EVET" if lehim else "HAYIR"), tip, "127.0.0.1", puan]], 
                               columns=["Zaman", "İsim", "İşlem", "Lehim", "Tip", "IP", "Puan"])
            yeni.to_csv(FILES["data"], mode='a', index=False, header=False)
            st.success(f"Hoş geldin {ad}!")
            st.balloons()

elif secim == "Duyuru Panosu":
    st.title("📢 Atölye Panosu")
    with open(FILES["duyuru"], "r", encoding="utf-8") as f: icerik = f.read()
    st.markdown(f"<div style='background:#1c2128; padding:30px; border-radius:15px; border:2px solid #ff8c00;'><h2>{icerik}</h2></div>", unsafe_allow_html=True)

elif secim == "Liderlik":
    st.title("🏆 Sıralama")
    df = pd.read_csv(FILES["data"])
    ban_df = pd.read_csv(FILES["ban"])
    if not df.empty:
        liderler = df.groupby("İsim")["Puan"].sum().reset_index().sort_values("Puan", ascending=False)
        temiz_liste = liderler[~liderler["İsim"].isin(ban_df["Isim"].tolist())]
        st.dataframe(temiz_liste, use_container_width=True, hide_index=True)
        if not ban_df.empty:
            with st.expander("🚫 Diskalifiye Edilenler"):
                st.table(ban_df[["Isim", "Sebep"]])

elif secim == "Admin":
    st.title("🔐 Kontrol Paneli")
    sifre = st.text_input("Şifre:", type="password")
    if sifre == "15531552":
        t1, t2, t3 = st.tabs(["📊 Veriler", "📣 Duyuru Yaz", "🔨 Ban"])
        with t1:
            st.dataframe(pd.read_csv(FILES["data"]).iloc[::-1])
        with t2:
            y_duyuru = st.text_area("Mesaj:")
            if st.button("Duyuruyu Güncelle"):
                with open(FILES["duyuru"], "w", encoding="utf-8") as f: f.write(y_duyuru)
                st.success("Duyuru güncellendi!")
        with t3:
            b_isim = st.text_input("Banlanacak İsim:")
            b_sebep = st.text_input("Sebep:")
            if st.button("MEN ET"):
                pd.DataFrame([["IP", b_isim, b_sebep]], columns=["IP", "Isim", "Sebep"]).to_csv(FILES["ban"], mode='a', index=False, header=False)
                st.warning(f"{b_isim} diskalifiye edildi.")

# --- FOOTER ---
st.markdown("""
    <div class="footer">
        İrfan Bileydi MTAL | <b>Made by alttre</b> 🚀
    </div>
    """, unsafe_allow_html=True)
