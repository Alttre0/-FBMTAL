import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
from streamlit_option_menu import option_menu
from PIL import Image

# --- 1. AYARLAR VE SAAT ---
st.set_page_config(page_title="Robotik Tayfası", page_icon="🤖", layout="wide")

def get_turkiye_saati():
    return datetime.utcnow() + timedelta(hours=3)

# --- 2. DOSYA VE HATA YÖNETİMİ ---
FILES = {
    "data": "robotik_log.csv",
    "users": "ogrenciler.csv",
    "ban": "yarisma_ban.csv",
    "duyuru": "duyuru.txt",
    "logo": "logo.jpg"
}

# BU FONKSİYON HATAYI ÇÖZER
def db_check():
    # 1. LOG DOSYASI KONTROLÜ
    if not os.path.exists(FILES["data"]):
        pd.DataFrame(columns=["Zaman", "İsim", "İşlem", "Lehim", "Tip", "IP", "Puan"]).to_csv(FILES["data"], index=False)
    else:
        # Dosya boşsa onar
        if os.stat(FILES["data"]).st_size == 0:
            pd.DataFrame(columns=["Zaman", "İsim", "İşlem", "Lehim", "Tip", "IP", "Puan"]).to_csv(FILES["data"], index=False)

    # 2. ÖĞRENCİ DOSYASI KONTROLÜ (SENİN HATAN BURADAYDI)
    if not os.path.exists(FILES["users"]):
        pd.DataFrame(columns=["Isim", "Sinif"]).to_csv(FILES["users"], index=False)
    else:
        # Eğer dosya var ama BOŞSA (EmptyDataError sebebi), başlıkları yeniden yaz
        if os.stat(FILES["users"]).st_size == 0:
            pd.DataFrame(columns=["Isim", "Sinif"]).to_csv(FILES["users"], index=False)

    # 3. BAN DOSYASI
    if not os.path.exists(FILES["ban"]):
        pd.DataFrame(columns=["IP", "Isim", "Sebep"]).to_csv(FILES["ban"], index=False)

    # 4. DUYURU
    if not os.path.exists(FILES["duyuru"]):
        with open(FILES["duyuru"], "w", encoding="utf-8") as f: f.write("Robotik Tayfası Hoş Geldiniz!")

# Kontrolleri çalıştır
db_check()

# --- 3. TASARIM ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #c9d1d9; }
    h1, h2 { color: #ff8c00; font-family: sans-serif; }
    .stButton button { background: linear-gradient(45deg, #ff8c00, #ff4500); color: white; border-radius: 8px; border: none; }
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; text-align: center; font-size: 12px; color: #666; padding: 10px; background-color: #161b22; border-top: 1px solid #333; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. YAN MENÜ ---
with st.sidebar:
    if os.path.exists(FILES["logo"]):
        st.image(FILES["logo"], use_container_width=True)
    
    st.markdown("<h3 style='text-align: center; color: white;'>ROBOTİK TAYFASI</h3>", unsafe_allow_html=True)
    
    secim = option_menu(None, ["Giriş Ekranı", "Duyurular", "Liderlik", "Yönetici"], 
        icons=['house', 'megaphone', 'trophy', 'gear'], 
        default_index=0,
        styles={"nav-link-selected": {"background-color": "#ff8c00"}})

# --- 5. SAYFALAR ---

# > GİRİŞ EKRANI
if secim == "Giriş Ekranı":
    st.title("📟 Atölye Günlüğü")
    
    # Hata önleyici okuma
    try:
        df_users = pd.read_csv(FILES["users"])
        ogrenci_listesi = ["Seçiniz..."] + df_users["Isim"].tolist()
    except pd.errors.EmptyDataError:
        # Dosya bozuksa onar ve tekrar dene
        pd.DataFrame(columns=["Isim", "Sinif"]).to_csv(FILES["users"], index=False)
        ogrenci_listesi = ["Seçiniz..."]

    col1, col2 = st.columns([2, 1])
    with col1:
        secilen_ad = st.selectbox("İsminiz:", ogrenci_listesi)
        islem = st.text_area("Ne yapıyorsun?", placeholder="Örn: Drone montajı, Python kodlama...")
        
    with col2:
        tr_simdi = get_turkiye_saati()
        secilen_saat = st.time_input("Saat:", tr_simdi.time())
        secilen_tarih = st.date_input("Tarih:", tr_simdi.date())
        
        tip = st.radio("Durum:", ["GİRİŞ", "ÇIKIŞ"], horizontal=True)
        lehim = st.toggle("🔥 Lehim Yaptım")

    if st.button("KAYDET"):
        if secilen_ad != "Seçiniz...":
            zaman_str = f"{secilen_saat.strftime('%H:%M')} | {secilen_tarih.strftime('%d-%m')}"
            puan = 10 if tip == "GİRİŞ" else 0
            
            # Kayıt işlemi
            yeni_log = pd.DataFrame([[zaman_str, secilen_ad, islem, ("EVET" if lehim else "HAYIR"), tip, "127.0.0.1", puan]], 
                                   columns=["Zaman", "İsim", "İşlem", "Lehim", "Tip", "IP", "Puan"])
            yeni_log.to_csv(FILES["data"], mode='a', index=False, header=False)
            st.success(f"✅ Kayıt Alındı: {secilen_ad} ({secilen_saat.strftime('%H:%M')})")
        else:
            st.warning("Lütfen listeden ismini seç. İsmin yoksa Admin eklesin.")
            
    # KVKK Bilgisi (Yumuşatılmış)
    st.caption("ℹ️ Bu sistem atölye düzenini sağlamak için kullanılmaktadır.")

# > DUYURULAR
elif secim == "Duyurular":
    st.title("📢 Duyuru Panosu")
    with open(FILES["duyuru"], "r", encoding="utf-8") as f: icerik = f.read()
    st.markdown(f"<div style='background:#21262d; padding:20px; border-radius:10px; border-left: 5px solid #ff8c00;'>{icerik}</div>", unsafe_allow_html=True)

# > LİDERLİK
elif secim == "Liderlik":
    st.title("🏆 En Aktif Öğrenciler")
    try:
        df = pd.read_csv(FILES["data"])
        ban_df = pd.read_csv(FILES["ban"])
        if not df.empty:
            liderler = df.groupby("İsim")["Puan"].sum().reset_index().sort_values("Puan", ascending=False)
            # Banlıları çıkar
            temiz_liste = liderler[~liderler["İsim"].isin(ban_df["Isim"].tolist())]
            st.dataframe(temiz_liste, use_container_width=True, hide_index=True)
        else:
            st.write("Henüz veri girişi yok.")
    except:
        st.error("Veri dosyası okunurken hata oluştu. Admin'e bildirin.")

# > YÖNETİCİ
elif secim == "Yönetici":
    sifre = st.text_input("Yönetici Şifresi:", type="password")
    if sifre == "15531552":
        tab1, tab2, tab3 = st.tabs(["➕ Öğrenci İşlemleri", "📢 Duyuru", "📝 Loglar"])
        
        with tab1:
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("Öğrenci Ekle")
                yeni_o_ad = st.text_input("Ad Soyad:")
                yeni_o_sinif = st.text_input("Sınıf:")
                if st.button("Kaydet"):
                    if yeni_o_ad:
                        pd.DataFrame([[yeni_o_ad, yeni_o_sinif]], columns=["Isim", "Sinif"]).to_csv(FILES["users"], mode='a', index=False, header=False)
                        st.success(f"{yeni_o_ad} eklendi!")
                        st.rerun()
            
            with c2:
                st.subheader("Kayıtlı Listesi")
                try:
                    df_u = pd.read_csv(FILES["users"])
                    st.dataframe(df_u, use_container_width=True)
                    if st.button("⚠️ Listeyi Sıfırla"):
                        pd.DataFrame(columns=["Isim", "Sinif"]).to_csv(FILES["users"], index=False)
                        st.rerun()
                except pd.errors.EmptyDataError:
                    st.error("Liste boş veya hatalı.")
                    pd.DataFrame(columns=["Isim", "Sinif"]).to_csv(FILES["users"], index=False) # Onar

        with tab2:
            mesaj = st.text_area("Yeni Duyuru:")
            if st.button("Yayınla"):
                with open(FILES["duyuru"], "w", encoding="utf-8") as f: f.write(mesaj)
                st.success("Duyuru güncellendi.")

        with tab3:
            st.dataframe(pd.read_csv(FILES["data"]).iloc[::-1]) # Tersten göster (son kayıt en üstte)

# --- FOOTER ---
st.markdown(f'<div class="footer">İrfan Bileydi MTAL | Made by alttre | TR Saati: {get_turkiye_saati().strftime("%H:%M")}</div>', unsafe_allow_html=True)
