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

# --- 2. DOSYA YÖNETİMİ ---
FILES = {
    "data": "robotik_log.csv",
    "users": "ogrenciler.csv",
    "ban": "yarisma_ban.csv",
    "duyuru": "duyuru.txt",
    "logo": "logo.jpg"
}

# HATA ÖNLEYİCİ VE DOSYA OLUŞTURUCU
def db_check():
    # Log Dosyası
    if not os.path.exists(FILES["data"]) or os.stat(FILES["data"]).st_size == 0:
        pd.DataFrame(columns=["Zaman", "İsim", "İşlem", "Lehim", "Tip", "IP", "Puan"]).to_csv(FILES["data"], index=False)

    # Öğrenci Dosyası
    if not os.path.exists(FILES["users"]) or os.stat(FILES["users"]).st_size == 0:
        pd.DataFrame(columns=["Isim", "Sinif"]).to_csv(FILES["users"], index=False)

    # Ban Dosyası
    if not os.path.exists(FILES["ban"]) or os.stat(FILES["ban"]).st_size == 0:
        pd.DataFrame(columns=["IP", "Isim", "Sebep"]).to_csv(FILES["ban"], index=False)

    # Duyuru
    if not os.path.exists(FILES["duyuru"]):
        with open(FILES["duyuru"], "w", encoding="utf-8") as f: f.write("Robotik Tayfası Hoş Geldiniz!")

db_check()

# --- 3. TASARIM ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #c9d1d9; }
    h1, h2 { color: #ff8c00; font-family: sans-serif; }
    .stButton button { background: linear-gradient(45deg, #ff8c00, #d35400); color: white; border-radius: 8px; border: none; font-weight: bold;}
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; text-align: center; font-size: 12px; color: #666; padding: 10px; background-color: #161b22; border-top: 1px solid #333; z-index: 999;}
    </style>
    """, unsafe_allow_html=True)

# --- 4. YAN MENÜ ---
with st.sidebar:
    if os.path.exists(FILES["logo"]):
        st.image(FILES["logo"], use_container_width=True)
    
    st.markdown("<h3 style='text-align: center; color: white;'>ROBOTİK TAYFASI</h3>", unsafe_allow_html=True)
    
    secim = option_menu(None, ["Giriş Ekranı", "Duyurular", "Liderlik", "Yönetici"], 
        icons=['cpu', 'megaphone', 'trophy', 'shield-lock'], 
        default_index=0,
        styles={"nav-link-selected": {"background-color": "#ff8c00"}})

# --- 5. SAYFALAR ---

# > GİRİŞ EKRANI
if secim == "Giriş Ekranı":
    st.title("📟 Atölye Günlüğü")
    
    try:
        df_users = pd.read_csv(FILES["users"])
        ogrenci_listesi = ["Seçiniz..."] + df_users["Isim"].tolist()
    except:
        ogrenci_listesi = ["Seçiniz..."]

    col1, col2 = st.columns([2, 1])
    with col1:
        secilen_ad = st.selectbox("İsminiz:", ogrenci_listesi)
        islem = st.text_area("Ne yapıyorsun?", placeholder="Örn: Drone montajı...")
        
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
            
            yeni_log = pd.DataFrame([[zaman_str, secilen_ad, islem, ("EVET" if lehim else "HAYIR"), tip, "127.0.0.1", puan]], 
                                   columns=["Zaman", "İsim", "İşlem", "Lehim", "Tip", "IP", "Puan"])
            yeni_log.to_csv(FILES["data"], mode='a', index=False, header=False)
            st.success(f"✅ Kayıt Alındı: {secilen_ad}")
        else:
            st.error("Lütfen listeden ismini seç.")
            
    st.caption("ℹ️ Atölye giriş-çıkış takip sistemi.")

# > DUYURULAR
elif secim == "Duyurular":
    st.title("📢 Duyuru Panosu")
    with open(FILES["duyuru"], "r", encoding="utf-8") as f: icerik = f.read()
    st.markdown(f"<div style='background:#21262d; padding:20px; border-radius:10px; border-left: 5px solid #ff8c00;'>{icerik}</div>", unsafe_allow_html=True)

# > LİDERLİK
elif secim == "Liderlik":
    st.title("🏆 Puan Durumu")
    try:
        df = pd.read_csv(FILES["data"])
        ban_df = pd.read_csv(FILES["ban"])
        
        if not df.empty:
            # Puanları hesapla
            liderler = df.groupby("İsim")["Puan"].sum().reset_index().sort_values("Puan", ascending=False)
            
            # Banlananları filtrele
            banli_listesi = ban_df["Isim"].tolist() if not ban_df.empty else []
            temiz_liste = liderler[~liderler["İsim"].isin(banli_listesi)]
            
            st.dataframe(temiz_liste, use_container_width=True, hide_index=True)
            
            if not ban_df.empty:
                with st.expander("⛔ Cezalı / Diskalifiye Listesi"):
                    st.dataframe(ban_df[["Isim", "Sebep"]])
        else:
            st.write("Henüz veri yok.")
    except:
        st.error("Veri okuma hatası.")

# > YÖNETİCİ (GÜNCELLENDİ)
elif secim == "Yönetici":
    sifre = st.text_input("Yönetici Şifresi:", type="password")
    if sifre == "15531552":
        tab1, tab2, tab3, tab4 = st.tabs(["➕ Öğrenci Yönetimi", "⚖️ Puan & Ban", "📢 Duyuru", "📝 Loglar"])
        
        # TAB 1: ÖĞRENCİ EKLEME
        with tab1:
            st.subheader("Öğrenci Kaydı")
            yeni_o_ad = st.text_input("Ad Soyad:")
            yeni_o_sinif = st.text_input("Sınıf:")
            if st.button("Öğrenciyi Ekle"):
                if yeni_o_ad:
                    pd.DataFrame([[yeni_o_ad, yeni_o_sinif]], columns=["Isim", "Sinif"]).to_csv(FILES["users"], mode='a', index=False, header=False)
                    st.success(f"{yeni_o_ad} listeye eklendi!")
                    st.rerun()
            
            st.write("---")
            if st.button("Öğrenci Listesini Temizle"):
                pd.DataFrame(columns=["Isim", "Sinif"]).to_csv(FILES["users"], index=False)
                st.rerun()

        # TAB 2: PUAN VE BAN İŞLEMLERİ (BURASI YENİ)
        with tab2:
            col_puan, col_ban = st.columns(2)
            
            # SOL: PUAN DEĞİŞTİRME
            with col_puan:
                st.subheader("🔧 Puan Düzenle")
                try:
                    df_u = pd.read_csv(FILES["users"])
                    o_list = df_u["Isim"].tolist()
                except: o_list = []
                
                p_isim = st.selectbox("Öğrenci Seç:", ["Seçiniz..."] + o_list)
                p_miktar = st.number_input("Eklenecek Puan (+ veya -)", step=1, value=0)
                p_sebep = st.text_input("Sebep (Opsiyonel):", "Admin Düzenleme")
                
                if st.button("Puanı Güncelle"):
                    if p_isim != "Seçiniz..." and p_miktar != 0:
                        tr_now = get_turkiye_saati().strftime("%H:%M | %d-%m")
                        pd.DataFrame([[tr_now, p_isim, f"Puan Düzeltme: {p_sebep}", "HAYIR", "ADMİN", "127.0.0.1", p_miktar]], 
                                    columns=["Zaman", "İsim", "İşlem", "Lehim", "Tip", "IP", "Puan"]).to_csv(FILES["data"], mode='a', index=False, header=False)
                        st.success(f"{p_isim} kişisine {p_miktar} puan eklendi!")
                    else:
                        st.warning("İsim ve puan miktarını kontrol et.")

            # SAĞ: BANLAMA
            with col_ban:
                st.subheader("⛔ Yarışmadan Men Et")
                b_isim = st.selectbox("Banlanacak Kişi:", ["Seçiniz..."] + o_list, key="ban_select")
                b_sebep = st.text_input("Ban Sebebi:", "Kural İhlali")
                
                if st.button("Kişiyi Banla"):
                    if b_isim != "Seçiniz...":
                        pd.DataFrame([["ADMIN", b_isim, b_sebep]], columns=["IP", "Isim", "Sebep"]).to_csv(FILES["ban"], mode='a', index=False, header=False)
                        st.error(f"{b_isim} diskalifiye edildi!")
                    else:
                        st.warning("İsim seçmedin.")
                
                if st.button("Ban Listesini Sıfırla (Af Çıkar)"):
                     pd.DataFrame(columns=["IP", "Isim", "Sebep"]).to_csv(FILES["ban"], index=False)
                     st.success("Herkes affedildi.")

        # TAB 3: DUYURU
        with tab3:
            mesaj = st.text_area("Yeni Duyuru:")
            if st.button("Yayınla"):
                with open(FILES["duyuru"], "w", encoding="utf-8") as f: f.write(mesaj)
                st.success("Duyuru güncellendi.")

        # TAB 4: LOGLAR
        with tab4:
            st.dataframe(pd.read_csv(FILES["data"]).iloc[::-1])
            if st.button("Tüm Logları Sil (SIFIRLA)"):
                 os.remove(FILES["data"])
                 st.rerun()

# --- FOOTER ---
st.markdown(f'<div class="footer">İrfan Bileydi MTAL | Made by alttre | {get_turkiye_saati().strftime("%H:%M")}</div>', unsafe_allow_html=True)
