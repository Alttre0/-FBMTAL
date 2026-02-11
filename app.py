import streamlit as st
import pandas as pd
import requests
import os
import time
from datetime import datetime, timedelta
from streamlit_option_menu import option_menu

# --- 1. AYARLAR VE ONESIGNAL ---
st.set_page_config(page_title="Robotik Lab Terminal", page_icon="🤖", layout="wide")

# BURAYA ONESIGNAL BİLGİLERİNİ YAPIŞTIR
ONESIGNAL_APP_ID = "89c0debc-c7a8-4ffe-9848-9405df878dd4"
ONESIGNAL_REST_KEY = "os_v2_app_rhan5pghvbh75gcisqc57b4n2tunkecvtjcufbmlqc2ftlrm46yqi4jsgq4ecnaaihpcytzbpwradw2aujhk72d7upp3burrixmxfpq"

def get_turkiye_saati():
    return datetime.utcnow() + timedelta(hours=3)

def get_remote_ip():
    try: return st.context.headers.get("X-Forwarded-For", "127.0.0.1").split(",")[0]
    except: return "127.0.0.1"

def push_bildirim_gonder(mesaj):
    header = {"Content-Type": "application/json; charset=utf-8", "Authorization": f"Basic {ONESIGNAL_REST_KEY}"}
    payload = {
        "app_id": ONESIGNAL_APP_ID,
        "included_segments": ["Total Subscriptions"],
        "contents": {"tr": mesaj},
        "headings": {"tr": "Robotik Atölyesi 🤖"},
        "chrome_web_icon": "https://cdn-icons-png.flaticon.com/512/1087/1087815.png" # Buraya logonun internet linkini koyabilirsin
    }
    r = requests.post("https://api.onesignal.com/notifications", headers=header, json=payload)
    return r.status_code

# --- 2. HATA DÜZELTİLMİŞ BİLDİRİM SCRIPTI ---
# f-string kullanmadan, doğrudan JavaScript içine değişkeni gömüyoruz
st.markdown(f'<script src="https://cdn.onesignal.com/sdks/web/v16/OneSignalSDK.sw.js" defer></script>', unsafe_allow_html=True)
st.markdown(f'<script src="https://cdn.onesignal.com/sdks/OneSignalSDK.js" async=""></script>', unsafe_allow_html=True)
st.markdown("""
    <script>
      window.OneSignal = window.OneSignal || [];
      OneSignal.push(function() {
        OneSignal.init({
          appId: " """ + ONESIGNAL_APP_ID + """ ",
          notifyButton: {
            enable: true,
          },
        });
      });
    </script>
    <style>
    .stApp { background-color: #0d1117; color: #c9d1d9; }
    .main-card { background: #161b22; padding: 20px; border-radius: 15px; border: 1px solid #30363d; margin-bottom: 20px; border-left: 5px solid #ff8c00; }
    .stButton button { background: linear-gradient(135deg, #ff8c00 0%, #ff4500 100%); color: white; border: none; border-radius: 8px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. VERİTABANI VE LOGO ---
FILES = {"data": "robotik_log.csv", "users": "ogrenciler.csv", "ban": "yarisma_ban.csv", "duyuru": "duyuru.txt", "logo": "logo.jpg"}

def db_check():
    for f, path in FILES.items():
        if f == "logo": continue
        if not os.path.exists(path) or (f != "duyuru" and os.stat(path).st_size == 0):
            cols = ["Zaman", "İsim", "İşlem", "Lehim", "Tip", "IP", "Puan"] if f=="data" else (["Isim", "Sinif"] if f=="users" else ["IP", "Isim", "Sebep"])
            if f != "duyuru": pd.DataFrame(columns=cols).to_csv(path, index=False)
            else: 
                with open(path, "w", encoding="utf-8") as d: d.write("Duyuru yok.")

db_check()
df_logs = pd.read_csv(FILES["data"])
df_users = pd.read_csv(FILES["users"])
df_ban = pd.read_csv(FILES["ban"])
current_ip = get_remote_ip()

# IP Tanıma
last_entry = df_logs[df_logs["IP"] == current_ip].tail(1)
recognized_name = last_entry["İsim"].values[0] if not last_entry.empty else "Seçiniz..."

# --- 4. YAN MENÜ ---
with st.sidebar:
    if os.path.exists(FILES["logo"]):
        st.image(FILES["logo"], use_container_width=True)
    secim = option_menu("Robotik Kontrol", ["Giriş", "Duyurular", "Sıralama", "Yönetici"], 
        icons=['cpu', 'megaphone', 'award', 'shield-lock'], default_index=0)
    st.markdown("---")
    st.caption(f"Cihaz IP: {current_ip}")

# --- 5. SAYFALAR ---

if secim == "Giriş":
    st.title("📟 Atölye Kayıt")
    if os.path.exists(FILES["logo"]):
        st.image(FILES["logo"], width=150)

    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    kvkk = st.checkbox("KVKK: Verilerimin kaydedilmesini onaylıyorum.")
    
    if kvkk:
        if recognized_name != "Seçiniz...":
            st.success(f"🤖 Tanındı: **{recognized_name}**")
        
        u_list = sorted(df_users["Isim"].tolist())
        v_idx = u_list.index(recognized_name) + 1 if recognized_name in u_list else 0
        
        c1, c2 = st.columns(2)
        with c1:
            secilen_ad = st.selectbox("İsim:", ["Seçiniz..."] + u_list, index=v_idx)
            islem = st.text_input("Şu anki görev?")
        with c2:
            tip = st.radio("İşlem:", ["GİRİŞ", "ÇIKIŞ"], horizontal=True)
            lehim = st.toggle("🔥 Lehim")
            
        if st.button("SİSTEME KAYDET 🚀"):
            if secilen_ad != "Seçiniz...":
                z_str = get_turkiye_saati().strftime("%H:%M | %d-%m")
                puan = 10 if tip == "GİRİŞ" else 0
                pd.DataFrame([[z_str, secilen_ad, islem, ("EVET" if lehim else "HAYIR"), tip, current_ip, puan]], 
                            columns=df_logs.columns).to_csv(FILES["data"], mode='a', index=False, header=False)
                st.balloons(); st.success("Kayıt Başarılı!"); time.sleep(1); st.rerun()
            else: st.error("İsim seçiniz!")
    st.markdown("</div>", unsafe_allow_html=True)

elif secim == "Duyurular":
    st.title("📢 Atölye Panosu")
    with open(FILES["duyuru"], "r", encoding="utf-8") as f: content = f.read()
    st.markdown(f"<div class='main-card' style='font-size: 22px; text-align: center; border: 2px solid #ff8c00;'>{content}</div>", unsafe_allow_html=True)
    st.info("💡 Bildirim almak için sağ alttaki zil ikonuna basıp onay verin.")

elif secim == "Sıralama":
    st.title("🏆 Puan Durumu")
    liderler = df_logs.groupby("İsim")["Puan"].sum().reset_index().sort_values("Puan", ascending=False)
    banli_listesi = df_ban["Isim"].tolist()
    st.dataframe(liderler[~liderler["İsim"].isin(banli_listesi)], use_container_width=True, hide_index=True)

elif secim == "Yönetici":
    sifre = st.text_input("Yönetici Şifresi:", type="password")
    if sifre == "15531552":
        t1, t2, t3 = st.tabs(["Kayıt Sil/Ekle", "Ban & Af", "Bildirim Gönder"])
        
        with t1:
            st.subheader("Yeni Öğrenci")
            y_ad = st.text_input("Ad Soyad:")
            if st.button("Öğrenciyi Ekle"):
                pd.DataFrame([[y_ad, "10"]], columns=["Isim", "Sinif"]).to_csv(FILES["users"], mode='a', index=False, header=False)
                st.success("Eklendi."); st.rerun()
            
            st.write("---")
            st.subheader("Öğrenci Kaydı Sil (Kalıcı)")
            sil_ad = st.selectbox("Silinecek Öğrenci:", sorted(df_users["Isim"].tolist()))
            if st.button("ÖĞRENCİYİ SİSTEMDEN SİL"):
                df_u_yeni = df_users[df_users["Isim"] != sil_ad]
                df_u_yeni.to_csv(FILES["users"], index=False)
                st.warning(f"{sil_ad} silindi."); st.rerun()

        with t2:
            st.subheader("Ban Yönetimi")
            b_ad = st.selectbox("Banlanacak:", sorted(df_users["Isim"].tolist()))
            if st.button("Banla"):
                pd.DataFrame([["ADMIN", b_ad, "Yasak"]], columns=df_ban.columns).to_csv(FILES["ban"], mode='a', index=False, header=False)
                st.rerun()
            
            st.write("---")
            un_ad = st.selectbox("Af Çıkar (Ban Kaldır):", sorted(df_ban["Isim"].tolist()))
            if st.button("Seçili Kişinin Banını Kaldır"):
                df_b_yeni = df_ban[df_ban["Isim"] != un_ad]
                df_b_yeni.to_csv(FILES["ban"], index=False)
                st.success("Ban kaldırıldı."); st.rerun()

        with t3:
            st.subheader("🚀 OneSignal Global Bildirim")
            y_duy = st.text_area("Bildirim Mesajı:")
            if st.button("YAYINLA VE BİLDİRİM GÖNDER"):
                with open(FILES["duyuru"], "w", encoding="utf-8") as f: f.write(y_duy)
                st.toast("Bildirim gönderiliyor...")
                stat = push_bildirim_gonder(y_duy)
                if stat == 200: st.success("PC ve Telefonlara bildirim gitti!"); st.rerun()
                else: st.error(f"Hata: {stat}")
