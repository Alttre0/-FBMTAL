import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
from streamlit_option_menu import option_menu
import time

# --- 1. AYARLAR VE SAAT ---
st.set_page_config(page_title="Robotik Akıllı Terminal", page_icon="🤖", layout="wide")

def get_turkiye_saati():
    return datetime.utcnow() + timedelta(hours=3)

# --- IP ADRESİNİ ALMA ---
# Streamlit Cloud üzerinde gerçek IP'yi almak için headers kullanılır
def get_remote_ip():
    try:
        # Streamlit Cloud/Nginx için standart yöntem
        return st.context.headers.get("X-Forwarded-For", "127.0.0.1").split(",")[0]
    except:
        return "127.0.0.1"

# --- 2. DOSYA YÖNETİMİ ---
FILES = {
    "data": "robotik_log.csv",
    "users": "ogrenciler.csv",
    "ban": "yarisma_ban.csv",
    "duyuru": "duyuru.txt",
    "logo": "logo.jpg"
}

def db_check():
    for f in ["data", "users", "ban"]:
        if not os.path.exists(FILES[f]) or os.stat(FILES[f]).st_size == 0:
            cols = ["Zaman", "İsim", "İşlem", "Lehim", "Tip", "IP", "Puan"] if f=="data" else (["Isim", "Sinif"] if f=="users" else ["IP", "Isim", "Sebep"])
            pd.DataFrame(columns=cols).to_csv(FILES[f], index=False)
    if not os.path.exists(FILES["duyuru"]):
        with open(FILES["duyuru"], "w", encoding="utf-8") as f: f.write("Robotik Atölyesi Akıllı Terminal")

db_check()

# --- 3. TASARIM ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #c9d1d9; }
    .stButton button { background: linear-gradient(45deg, #ff8c00, #d35400); color: white; border-radius: 8px; font-weight: bold; }
    .user-box { background: #1c2128; padding: 15px; border-radius: 10px; border: 1px solid #30363d; margin-bottom: 10px; }
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; text-align: center; font-size: 12px; color: #666; padding: 10px; background: #161b22; z-index: 999; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. YAN MENÜ ---
with st.sidebar:
    if os.path.exists(FILES["logo"]): st.image(FILES["logo"], use_container_width=True)
    st.markdown("<h3 style='text-align: center;'>ROBOTİK TAYFASI</h3>", unsafe_allow_html=True)
    secim = option_menu(None, ["Giriş Ekranı", "Duyurular", "Liderlik", "Yönetici"], 
        icons=['cpu', 'megaphone', 'trophy', 'gear'], default_index=0)

# --- 5. VERİ ÇEKME ---
current_ip = get_remote_ip()
df_logs = pd.read_csv(FILES["data"])
df_users = pd.read_csv(FILES["users"])

# Bu IP'den daha önce giriş yapan son kullanıcıyı bul
last_entry = df_logs[df_logs["IP"] == current_ip].tail(1)
recognized_name = last_entry["İsim"].values[0] if not last_entry.empty else "Seçiniz..."
last_job = last_entry["İşlem"].values[0] if not last_entry.empty else ""

# --- 6. SAYFALAR ---

if secim == "Giriş Ekranı":
    st.title("📟 Akıllı Terminal")
    
    # IP Tanıma Bilgisi
    if recognized_name != "Seçiniz...":
        st.markdown(f"""<div class='user-box'>✨ Seni tanıdım! En son <b>{recognized_name}</b> olarak giriş yapmışsın.<br>
        Önceki işin: <i>{last_job}</i></div>""", unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])
    
    with col1:
        # İsim Listesi (Eğer tanıyorsa onu varsayılan seçer)
        u_list = sorted(df_users["Isim"].tolist())
        try:
            v_index = u_list.index(recognized_name) + 1
        except:
            v_index = 0
            
        secilen_ad = st.selectbox("İsminiz:", ["Seçiniz..."] + u_list, index=v_index)
        islem = st.text_area("Ne yapıyorsun?", value=last_job if secilen_ad == recognized_name else "", placeholder="İşlemini yaz...")
        
    with col2:
        tr_simdi = get_turkiye_saati()
        secilen_saat = st.time_input("Saat:", tr_simdi.time())
        tip = st.radio("Durum:", ["GİRİŞ", "ÇIKIŞ"], horizontal=True)
        lehim = st.toggle("🔥 Lehim")

    if st.button("🚀 TEK TIKLA KAYDET"):
        if secilen_ad != "Seçiniz...":
            zaman_str = f"{secilen_saat.strftime('%H:%M')} | {tr_simdi.strftime('%d-%m')}"
            puan = 10 if tip == "GİRİŞ" else 0
            
            yeni_log = pd.DataFrame([[zaman_str, secilen_ad, islem, ("EVET" if lehim else "HAYIR"), tip, current_ip, puan]], 
                                   columns=["Zaman", "İsim", "İşlem", "Lehim", "Tip", "IP", "Puan"])
            yeni_log.to_csv(FILES["data"], mode='a', index=False, header=False)
            st.balloons()
            st.success(f"Kaydedildi! Hoş geldin {secilen_ad}")
            time.sleep(1)
            st.rerun()
        else:
            st.error("İsim seçmelisin!")

    # --- AYNI IP GEÇMİŞİ ---
    st.write("---")
    st.subheader("📍 Bu Cihazdan Yapılan Son İşlemler")
    ip_history = df_logs[df_logs["IP"] == current_ip].tail(5)[::-1]
    if not ip_history.empty:
        st.table(ip_history[["Zaman", "İsim", "İşlem", "Tip"]])
    else:
        st.info("Bu cihazdan henüz giriş yapılmadı.")

elif secim == "Liderlik":
    st.title("🏆 Puan Durumu")
    df = pd.read_csv(FILES["data"])
    if not df.empty:
        liderler = df.groupby("İsim")["Puan"].sum().reset_index().sort_values("Puan", ascending=False)
        st.dataframe(liderler, use_container_width=True, hide_index=True)
    else:
        st.info("Veri yok.")

elif secim == "Yönetici":
    sifre = st.text_input("Şifre:", type="password")
    if sifre == "15531552":
        tab1, tab2 = st.tabs(["Öğrenci Ekle", "Loglar"])
        with tab1:
            y_ad = st.text_input("Ad Soyad:")
            if st.button("Ekle"):
                if y_ad and y_ad not in df_users["Isim"].values:
                    pd.DataFrame([[y_ad, "Sınıf"]], columns=["Isim", "Sinif"]).to_csv(FILES["users"], mode='a', index=False, header=False)
                    st.success("Eklendi")
                    st.rerun()
        with tab2:
            st.dataframe(pd.read_csv(FILES["data"]))

# --- FOOTER ---
st.markdown(f'<div class="footer">IP Adresin: {current_ip} | {get_turkiye_saati().strftime("%H:%M")}</div>', unsafe_allow_html=True)
