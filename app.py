import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
from streamlit_option_menu import option_menu
from PIL import Image

# --- 1. AYARLAR VE SAAT DÜZELTME ---
st.set_page_config(page_title="Robotik Tayfası", page_icon="🤖", layout="wide")

def get_turkiye_saati():
    # Sunucu saati üzerine 3 saat ekleyerek Türkiye saatini bulur
    return datetime.utcnow() + timedelta(hours=3)

# --- 2. DOSYA YÖNETİMİ ---
FILES = {
    "data": "robotik_log.csv",
    "users": "ogrenciler.csv",
    "ban": "yarisma_ban.csv",
    "duyuru": "duyuru.txt",
    "logo": "logo.jpg"
}

def db_check():
    # Log dosyası
    if not os.path.exists(FILES["data"]):
        pd.DataFrame(columns=["Zaman", "İsim", "İşlem", "Lehim", "Tip", "IP", "Puan"]).to_csv(FILES["data"], index=False)
    # Öğrenci listesi dosyası
    if not os.path.exists(FILES["users"]):
        pd.DataFrame(columns=["Isim", "Sinif"]).to_csv(FILES["users"], index=False)
    # Ban listesi
    if not os.path.exists(FILES["ban"]):
        pd.DataFrame(columns=["IP", "Isim", "Sebep"]).to_csv(FILES["ban"], index=False)
    # Duyuru
    if not os.path.exists(FILES["duyuru"]):
        with open(FILES["duyuru"], "w", encoding="utf-8") as f: f.write("Robotik Tayfası Hoş Geldiniz!")

db_check()

# --- 3. TASARIM ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #c9d1d9; }
    h1, h2 { color: #ff8c00; }
    .stButton button { background: linear-gradient(45deg, #ff8c00, #ff4500); color: white; border-radius: 10px; }
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; text-align: center; font-size: 12px; color: #555; padding: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. YAN MENÜ ---
with st.sidebar:
    if os.path.exists(FILES["logo"]):
        st.image(FILES["logo"], use_container_width=True)
    st.markdown("<h3 style='text-align: center;'>ROBOTİK TAYFASI</h3>", unsafe_allow_html=True)
    
    secim = option_menu(None, ["Giriş Ekranı", "Duyurular", "Liderlik", "Yönetici"], 
        icons=['house', 'megaphone', 'trophy', 'gear'], default_index=0)

# --- 5. SAYFALAR ---

# > GİRİŞ EKRANI
if secim == "Giriş Ekranı":
    st.title("📟 Atölye Günlüğü")
    
    # Öğrenci Listesini Çek
    df_users = pd.read_csv(FILES["users"])
    ogrenci_listesi = ["Seçiniz..."] + df_users["Isim"].tolist()

    col1, col2 = st.columns([2, 1])
    with col1:
        # Kullanıcı Ekleme/Seçme Sistemi
        secilen_ad = st.selectbox("İsminiz:", ogrenci_listesi)
        islem = st.text_area("Ne yapıyorsun? (Örn: Kodlama, Montaj...)")
        
    with col2:
        # Saat Seçimi (Otomatik Türkiye saati gelir ama değiştirilebilir)
        tr_simdi = get_turkiye_saati()
        secilen_saat = st.time_input("İşlem Saati:", tr_simdi.time())
        secilen_tarih = st.date_input("Tarih:", tr_simdi.date())
        
        tip = st.radio("Hareket:", ["GİRİŞ", "ÇIKIŞ"])
        lehim = st.toggle("🔥 Lehim Yaptım")

    if st.button("SİSTEME İŞLE"):
        if secilen_ad != "Seçiniz...":
            zaman_str = f"{secilen_saat.strftime('%H:%M')} | {secilen_tarih.strftime('%d-%m')}"
            puan = 10 if tip == "GİRİŞ" else 0
            
            yeni_log = pd.DataFrame([[zaman_str, secilen_ad, islem, ("EVET" if lehim else "HAYIR"), tip, "127.0.0.1", puan]], 
                                   columns=["Zaman", "İsim", "İşlem", "Lehim", "Tip", "IP", "Puan"])
            yeni_log.to_csv(FILES["data"], mode='a', index=False, header=False)
            st.success(f"Kaydedildi! Saat: {secilen_saat.strftime('%H:%M')}")
        else:
            st.error("Lütfen listeden ismini seç! (Yoksa Admin'e eklet)")

# > DUYURULAR
elif secim == "Duyurular":
    st.title("📢 Duyuru Panosu")
    with open(FILES["duyuru"], "r", encoding="utf-8") as f: icerik = f.read()
    st.info(icerik)

# > LİDERLİK
elif secim == "Liderlik":
    st.title("🏆 Puan Durumu")
    df = pd.read_csv(FILES["data"])
    if not df.empty:
        liderler = df.groupby("İsim")["Puan"].sum().reset_index().sort_values("Puan", ascending=False)
        st.dataframe(liderler, use_container_width=True, hide_index=True)

# > YÖNETİCİ (USER EKLEME BURADA)
elif secim == "Yönetici":
    sifre = st.text_input("Şifre:", type="password")
    if sifre == "15531552":
        tab1, tab2, tab3 = st.tabs(["Öğrenci Ekle/Sil", "Duyuru Yaz", "Loglar"])
        
        with tab1:
            st.subheader("Yeni Öğrenci Ekle")
            yeni_o_ad = st.text_input("Ad Soyad:")
            yeni_o_sinif = st.text_input("Sınıf:")
            if st.button("Öğrenciyi Kaydet"):
                if yeni_o_ad:
                    yeni_ogrenci = pd.DataFrame([[yeni_o_ad, yeni_o_sinif]], columns=["Isim", "Sinif"])
                    yeni_ogrenci.to_csv(FILES["users"], mode='a', index=False, header=False)
                    st.success(f"{yeni_o_ad} listeye eklendi. Artık Giriş Ekranında görünecek.")
                    st.rerun()

            st.write("---")
            st.subheader("Kayıtlı Öğrenciler")
            df_u = pd.read_csv(FILES["users"])
            st.dataframe(df_u)
            if st.button("Öğrenci Listesini Sıfırla"):
                os.remove(FILES["users"])
                st.rerun()

        with tab2:
            mesaj = st.text_area("Duyuru:")
            if st.button("Yayınla"):
                with open(FILES["duyuru"], "w", encoding="utf-8") as f: f.write(mesaj)
                st.success("Duyuru güncellendi.")

        with tab3:
            st.dataframe(pd.read_csv(FILES["data"]))

# --- FOOTER ---
st.markdown(f'<div class="footer">İrfan Bileydi MTAL | Made by alttre | TR Saati: {get_turkiye_saati().strftime("%H:%M")}</div>', unsafe_allow_html=True)
