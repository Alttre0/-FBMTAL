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

def get_remote_ip():
    try:
        return st.context.headers.get("X-Forwarded-For", "127.0.0.1").split(",")[0]
    except:
        return "127.0.0.1"

# --- 2. DOSYA YÖNETİMİ (TAMİR EDİLDİ) ---
FILES = {
    "data": "robotik_log.csv",
    "users": "ogrenciler.csv",
    "ban": "yarisma_ban.csv",
    "duyuru": "duyuru.txt",
    "logo": "logo.jpg"
}

def db_check():
    for f, path in FILES.items():
        if f == "logo": continue
        if not os.path.exists(path) or (f != "duyuru" and os.stat(path).st_size == 0):
            if f == "data": cols = ["Zaman", "İsim", "İşlem", "Lehim", "Tip", "IP", "Puan"]
            elif f == "users": cols = ["Isim", "Sinif"]
            elif f == "ban": cols = ["IP", "Isim", "Sebep"]
            
            if f != "duyuru": 
                pd.DataFrame(columns=cols).to_csv(path, index=False)
            else: 
                with open(path, "w", encoding="utf-8") as d: 
                    d.write("Robotik Atölyesi Hoş Geldiniz! Duyuru kısmını admin panelinden güncelleyin.")

db_check()

# --- 3. VERİLERİ ÇEK ---
current_ip = get_remote_ip()
df_logs = pd.read_csv(FILES["data"])
df_users = pd.read_csv(FILES["users"])
df_ban = pd.read_csv(FILES["ban"])

# IP Tanıma: Son işlemi ve ismi bul
last_entry = df_logs[df_logs["IP"] == current_ip].tail(1)
recognized_name = last_entry["İsim"].values[0] if not last_entry.empty else "Seçiniz..."
last_job = last_entry["İşlem"].values[0] if not last_entry.empty else ""

# --- 4. TASARIM ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #c9d1d9; }
    .stButton button { background: linear-gradient(45deg, #ff8c00, #d35400); color: white; border-radius: 8px; font-weight: bold; width: 100%; }
    .user-box { background: #1c2128; padding: 15px; border-radius: 10px; border-left: 5px solid #ff8c00; margin-bottom: 20px; }
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; text-align: center; font-size: 11px; color: #555; padding: 5px; background: #161b22; z-index: 999; }
    </style>
    """, unsafe_allow_html=True)

# --- 5. YAN MENÜ ---
with st.sidebar:
    if os.path.exists(FILES["logo"]): st.image(FILES["logo"], use_container_width=True)
    secim = option_menu("Robotik Lab", ["Giriş Ekranı", "Duyurular", "Liderlik", "Yönetici"], 
        icons=['cpu', 'megaphone', 'trophy', 'gear'], default_index=0)

# --- 6. SAYFALAR ---

if secim == "Giriş Ekranı":
    st.title("📟 Akıllı Terminal")
    if recognized_name != "Seçiniz...":
        st.markdown(f"<div class='user-box'>✨ <b>Tanındı:</b> {recognized_name} <br>Son işin: <i>{last_job}</i></div>", unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])
    with col1:
        u_list = sorted(df_users["Isim"].tolist())
        v_idx = u_list.index(recognized_name) + 1 if recognized_name in u_list else 0
        secilen_ad = st.selectbox("İsminiz:", ["Seçiniz..."] + u_list, index=v_idx)
        islem = st.text_area("Ne yapıyorsun?", value=last_job if secilen_ad == recognized_name else "", placeholder="Örn: 3D Tasarım...")
    with col2:
        tr_simdi = get_turkiye_saati()
        secilen_saat = st.time_input("Saat:", tr_simdi.time())
        tip = st.radio("İşlem:", ["GİRİŞ", "ÇIKIŞ"], horizontal=True)
        lehim = st.toggle("🔥 Lehim")

    if st.button("🚀 KAYDI TAMAMLA"):
        if secilen_ad != "Seçiniz...":
            zaman_str = f"{secilen_saat.strftime('%H:%M')} | {tr_simdi.strftime('%d-%m')}"
            puan = 10 if tip == "GİRİŞ" else 0
            pd.DataFrame([[zaman_str, secilen_ad, islem, ("EVET" if lehim else "HAYIR"), tip, current_ip, puan]], 
                        columns=df_logs.columns).to_csv(FILES["data"], mode='a', index=False, header=False)
            st.balloons()
            st.success(f"Kaydedildi, iyi çalışmalar {secilen_ad}!")
            time.sleep(1)
            st.rerun()

elif secim == "Duyurular":
    st.title("📢 Atölye Panosu")
    with open(FILES["duyuru"], "r", encoding="utf-8") as f:
        duyuru_icerik = f.read()
    st.markdown(f"<div style='background:#1c2128; padding:30px; border-radius:15px; border:2px solid #ff8c00; font-size:20px; color:white;'>{duyuru_icerik}</div>", unsafe_allow_html=True)

elif secim == "Liderlik":
    st.title("🏆 Sıralama")
    df_logs = pd.read_csv(FILES["data"])
    if not df_logs.empty:
        liderler = df_logs.groupby("İsim")["Puan"].sum().reset_index().sort_values("Puan", ascending=False)
        banli_listesi = df_ban["Isim"].tolist()
        temiz_liste = liderler[~liderler["İsim"].isin(banli_listesi)]
        st.dataframe(temiz_liste, use_container_width=True, hide_index=True)
    else: st.info("Henüz veri yok.")

elif secim == "Yönetici":
    sifre = st.text_input("Şifre:", type="password")
    if sifre == "15531552":
        t1, t2, t3, t4 = st.tabs(["Öğrenci Kayıt", "Puan & Ban", "Duyuru Yaz", "Veriler"])
        
        with t1:
            st.subheader("Yeni Öğrenci")
            y_ad = st.text_input("Ad Soyad:")
            y_sinif = st.selectbox("Sınıf:", ["9", "10", "11", "12"])
            if st.button("Ekle"):
                if y_ad and y_ad not in df_users["Isim"].values:
                    pd.DataFrame([[y_ad, y_sinif]], columns=["Isim", "Sinif"]).to_csv(FILES["users"], mode='a', index=False, header=False)
                    st.success("Öğrenci eklendi."); st.rerun()

        with t2:
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("Puan Ver/Sil")
                p_ad = st.selectbox("Kişi:", ["Seçiniz..."] + sorted(df_users["Isim"].tolist()))
                p_mik = st.number_input("Puan (+/-):", step=1)
                if st.button("Uygula"):
                    tr_z = get_turkiye_saati().strftime("%H:%M | %d-%m")
                    pd.DataFrame([[tr_z, p_ad, "Admin Düzenleme", "HAYIR", "ADMİN", "127.0.0.1", p_mik]], 
                                columns=df_logs.columns).to_csv(FILES["data"], mode='a', index=False, header=False)
                    st.success("Puan işlendi."); st.rerun()
            with c2:
                st.subheader("Ban & Af")
                b_ad = st.selectbox("Kişi Seç:", ["Seçiniz..."] + sorted(df_users["Isim"].tolist()))
                b_seb = st.text_input("Sebep:")
                if st.button("Banla"):
                    pd.DataFrame([["ADMIN", b_ad, b_seb]], columns=df_ban.columns).to_csv(FILES["ban"], mode='a', index=False, header=False)
                    st.error("Banlandı."); st.rerun()
                if st.button("BANLARI SIFIRLA (AF)"):
                    pd.DataFrame(columns=df_ban.columns).to_csv(FILES["ban"], index=False)
                    st.success("Tüm banlar kaldırıldı!"); st.rerun()

        with t3:
            st.subheader("Duyuruyu Değiştir")
            y_duyuru = st.text_area("Yeni Mesaj:")
            if st.button("Yayınla"):
                with open(FILES["duyuru"], "w", encoding="utf-8") as f: f.write(y_duyuru)
                st.success("Duyuru güncellendi!"); st.rerun()

        with t4:
            st.dataframe(pd.read_csv(FILES["data"]))
            if st.button("Logları Sıfırla"):
                pd.DataFrame(columns=df_logs.columns).to_csv(FILES["data"], index=False)
                st.rerun()

st.markdown(f'<div class="footer">IP: {current_ip} | {get_turkiye_saati().strftime("%H:%M")}</div>', unsafe_allow_html=True)
