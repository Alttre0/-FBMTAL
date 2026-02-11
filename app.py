import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
from streamlit_option_menu import option_menu
import time

# --- 1. AYARLAR VE SAAT ---
st.set_page_config(page_title="Robotik Lab Terminal", page_icon="🤖", layout="wide")

def get_turkiye_saati():
    return datetime.utcnow() + timedelta(hours=3)

def get_remote_ip():
    try:
        return st.context.headers.get("X-Forwarded-For", "127.0.0.1").split(",")[0]
    except:
        return "127.0.0.1"

# --- 2. DOSYA YÖNETİMİ ---
FILES = {"data": "robotik_log.csv", "users": "ogrenciler.csv", "ban": "yarisma_ban.csv", "duyuru": "duyuru.txt"}

def db_check():
    for f, path in FILES.items():
        if not os.path.exists(path) or (f != "duyuru" and os.stat(path).st_size == 0):
            if f == "data": cols = ["Zaman", "İsim", "İşlem", "Lehim", "Tip", "IP", "Puan"]
            elif f == "users": cols = ["Isim", "Sinif"]
            elif f == "ban": cols = ["IP", "Isim", "Sebep"]
            if f != "duyuru": pd.DataFrame(columns=cols).to_csv(path, index=False)
            else:
                with open(path, "w", encoding="utf-8") as d: d.write("Robotik Atölyesine Hoş Geldiniz! İlk duyuru burada görünecek.")

db_check()

# --- 3. VERİ ÇEKME ---
current_ip = get_remote_ip()
df_logs = pd.read_csv(FILES["data"])
df_users = pd.read_csv(FILES["users"])
df_ban = pd.read_csv(FILES["ban"])

# IP Tanıma
last_entry = df_logs[df_logs["IP"] == current_ip].tail(1)
recognized_name = last_entry["İsim"].values[0] if not last_entry.empty else "Seçiniz..."
last_job = last_entry["İşlem"].values[0] if not last_entry.empty else ""

# --- 4. ÖZEL CSS TASARIMI ---
st.markdown("""
    <style>
    /* Ana Tema */
    .stApp { background-color: #0d1117; color: #c9d1d9; }
    
    /* Kart Yapıları */
    .main-card { background: #161b22; padding: 25px; border-radius: 15px; border: 1px solid #30363d; box-shadow: 0 10px 30px rgba(0,0,0,0.5); margin-bottom: 20px; }
    
    /* Butonlar */
    .stButton button { 
        background: linear-gradient(135deg, #ff8c00 0%, #ff4500 100%); 
        color: white; border: none; border-radius: 10px; padding: 12px;
        font-weight: bold; font-size: 16px; transition: all 0.3s ease;
    }
    .stButton button:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(255,140,0,0.4); }
    
    /* KVKK Kutusu */
    .kvkk-text { background: #0d1117; padding: 15px; border-radius: 10px; border-left: 4px solid #f85149; font-size: 12px; color: #8b949e; margin-bottom: 15px; }
    
    /* Liderlik Tablosu Güzelleştirme */
    .stDataFrame { border-radius: 10px; overflow: hidden; }
    
    /* Header */
    h1 { color: #ff8c00; font-family: 'Orbitron', sans-serif; text-transform: uppercase; letter-spacing: 2px; }
    </style>
    """, unsafe_allow_html=True)

# --- 5. YAN MENÜ ---
with st.sidebar:
    st.markdown(f"<h2 style='text-align: center; color: #ff8c00;'>🤖 LAB HUB</h2>", unsafe_allow_html=True)
    secim = option_menu(None, ["Terminal", "Duyurular", "Sıralama", "Admin"], 
        icons=['cpu', 'broadcast', 'award', 'shield-lock'], 
        menu_icon="cast", default_index=0,
        styles={"nav-link-selected": {"background-color": "#ff8c00"}})
    st.markdown("---")
    st.caption(f"📍 IP: {current_ip}")
    st.caption(f"🕒 {get_turkiye_saati().strftime('%H:%M:%S')}")

# --- 6. SAYFALAR ---

if secim == "Terminal":
    st.title("📟 Giriş Terminali")
    
    with st.container():
        st.markdown("<div class='main-card'>", unsafe_allow_html=True)
        
        # KVKK Bölümü
        st.markdown("""<div class='kvkk-text'><b>KAYIT AYDINLATMA:</b> Bu sistemde IP adresiniz ve adınız hile önleme amacıyla işlenmektedir. 
        Butona basarak KVKK şartlarını kabul etmiş olursunuz.</div>""", unsafe_allow_html=True)
        
        c_kvkk = st.checkbox("Şartları Okudum ve Kabul Ediyorum", value=False)
        
        if c_kvkk:
            if recognized_name != "Seçiniz...":
                st.success(f"📡 Sistem: **{recognized_name}** cihazdan tanındı. Hoş geldin!")
            
            col1, col2 = st.columns([2, 1])
            with col1:
                u_list = sorted(df_users["Isim"].tolist())
                v_idx = u_list.index(recognized_name) + 1 if recognized_name in u_list else 0
                secilen_ad = st.selectbox("Operatör Seçimi:", ["Seçiniz..."] + u_list, index=v_idx)
                islem = st.text_area("Görev Tanımı:", value=last_job if secilen_ad == recognized_name else "", placeholder="Şu an ne üzerinde çalışıyorsun?")
            
            with col2:
                tr_simdi = get_turkiye_saati()
                secilen_saat = st.time_input("Saat:", tr_simdi.time())
                tip = st.radio("İşlem Tipi:", ["GİRİŞ", "ÇIKIŞ"], horizontal=True)
                lehim = st.toggle("🔥 Lehim İstasyonu Aktif")

            if st.button("SİSTEME İŞLE 🚀"):
                if secilen_ad != "Seçiniz...":
                    z_str = f"{secilen_saat.strftime('%H:%M')} | {tr_simdi.strftime('%d-%m')}"
                    puan = 15 if tip == "GİRİŞ" else 5
                    if lehim: puan += 5
                    
                    pd.DataFrame([[z_str, secilen_ad, islem, ("EVET" if lehim else "HAYIR"), tip, current_ip, puan]], 
                                columns=df_logs.columns).to_csv(FILES["data"], mode='a', index=False, header=False)
                    st.balloons()
                    st.toast(f"Kayıt Başarılı: {secilen_ad}", icon='✅')
                    time.sleep(1)
                    st.rerun()
                else: st.error("Lütfen bir isim seçin!")
        else:
            st.warning("⚠️ Terminali kullanmak için şartları kabul etmelisiniz.")
        st.markdown("</div>", unsafe_allow_html=True)

elif secim == "Duyurular":
    st.title("📢 Duyuru Panosu")
    with open(FILES["duyuru"], "r", encoding="utf-8") as f: content = f.read()
    st.markdown(f"""<div style='background: #1c2128; padding: 40px; border-radius: 20px; border: 2px solid #ff8c00; text-align: center;'>
        <h2 style='color: #ff8c00;'>SON MESAJ</h2>
        <p style='font-size: 24px; color: white;'>{content}</p>
    </div>""", unsafe_allow_html=True)
    st.toast("Yeni duyuru var mı kontrol et!", icon="🔔")

elif secim == "Sıralama":
    st.title("🏆 Atölye Liderleri")
    if not df_logs.empty:
        liderler = df_logs.groupby("İsim")["Puan"].sum().reset_index().sort_values("Puan", ascending=False)
        banli_adlar = df_ban["Isim"].tolist()
        temiz_liste = liderler[~liderler["İsim"].isin(banli_adlar)]
        
        st.dataframe(temiz_liste, use_container_width=True, hide_index=True)
        
        if not df_ban.empty:
            with st.expander("⛔ Cezalı Operatörler"):
                st.table(df_ban[["Isim", "Sebep"]])
    else: st.info("Henüz veri akışı sağlanmadı.")

elif secim == "Admin":
    sifre = st.text_input("Yönetici Yetkilendirme:", type="password")
    if sifre == "15531552":
        t1, t2, t3, t4 = st.tabs(["👤 Kullanıcı Ekle", "⚖️ Puan & Ban", "📢 Duyuru Yayınla", "📊 Veri Analizi"])
        
        with t1:
            y_ad = st.text_input("Operatör Adı Soyadı:")
            y_si = st.selectbox("Sınıf Seviyesi:", ["9", "10", "11", "12", "Mezun"])
            if st.button("Kullanıcıyı Tanımla"):
                if y_ad and y_ad not in df_users["Isim"].values:
                    pd.DataFrame([[y_ad, y_si]], columns=["Isim", "Sinif"]).to_csv(FILES["users"], mode='a', index=False, header=False)
                    st.success(f"{y_ad} eklendi."); st.rerun()

        with t2:
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("Puan Müdahalesi")
                p_ad = st.selectbox("Hedef Kullanıcı:", ["Seçiniz..."] + sorted(df_users["Isim"].tolist()))
                p_mik = st.number_input("Puan Değişimi:", step=1)
                if st.button("Puanı Güncelle"):
                    tr_z = get_turkiye_saati().strftime("%H:%M | %d-%m")
                    pd.DataFrame([[tr_z, p_ad, "Admin Düzenlemesi", "YOK", "ADMİN", "127.0.0.1", p_mik]], 
                                columns=df_logs.columns).to_csv(FILES["data"], mode='a', index=False, header=False)
                    st.success("Müdahale başarılı."); st.rerun()
            
            with c2:
                st.subheader("Cezalandırma & Af")
                b_ad = st.selectbox("Kısıtlanacak Kişi:", ["Seçiniz..."] + sorted(df_users["Isim"].tolist()))
                b_se = st.text_input("Kısıtlama Sebebi:")
                if st.button("Hemen Banla"):
                    pd.DataFrame([["ADMIN", b_ad, b_se]], columns=df_ban.columns).to_csv(FILES["ban"], mode='a', index=False, header=False)
                    st.rerun()
                
                st.markdown("---")
                # KİŞİYE ÖZEL BAN KALDIRMA
                un_ad = st.selectbox("Affedilecek Kişi:", ["Seçiniz..."] + sorted(df_ban["Isim"].tolist()))
                if st.button("Seçili Kişiyi Affet"):
                    if un_ad != "Seçiniz...":
                        new_ban = df_ban[df_ban["Isim"] != un_ad]
                        new_ban.to_csv(FILES["ban"], index=False)
                        st.success(f"{un_ad} affedildi."); time.sleep(1); st.rerun()

        with t3:
            y_duy = st.text_area("Duyuru Metni:")
            if st.button("Global Duyuru Yap"):
                with open(FILES["duyuru"], "w", encoding="utf-8") as f: f.write(y_duy)
                st.toast(f"YENİ DUYURU: {y_duy}", icon="🔔")
                st.success("Duyuru tüm terminale gönderildi."); st.rerun()

        with t4:
            st.dataframe(pd.read_csv(FILES["data"]).iloc[::-1])
            if st.button("Tüm Logları Temizle"):
                pd.DataFrame(columns=df_logs.columns).to_csv(FILES["data"], index=False)
                st.rerun()

st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)
st.markdown(f"<div class='footer'>Robotik Laboratuvarı Güvenli Terminal v5.0 | Sistem Saati: {get_turkiye_saati().strftime('%H:%M')}</div>", unsafe_allow_html=True)
