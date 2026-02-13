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
        # Streamlit Cloud ve proxy arkası için IP alma
        return st.context.headers.get("X-Forwarded-For", "127.0.0.1").split(",")[0]
    except:
        return "127.0.0.1"

# --- 2. DOSYA YÖNETİMİ ---
FILES = {
    "data": "robotik_log.csv",
    "users": "ogrenciler.csv",
    "ban": "yarisma_ban.csv",
    "duyuru": "duyuru.txt"
}

def db_check():
    for f, path in FILES.items():
        if not os.path.exists(path) or (f != "duyuru" and os.stat(path).st_size == 0):
            if f == "data": cols = ["Zaman", "İsim", "İşlem", "Lehim", "Tip", "IP", "Puan"]
            elif f == "users": cols = ["Isim", "Sinif", "Email", "IP"] # Email ve IP eklendi
            elif f == "ban": cols = ["IP", "Isim", "Sebep"]
            
            if f != "duyuru": 
                pd.DataFrame(columns=cols).to_csv(path, index=False)
            else:
                with open(path, "w", encoding="utf-8") as d:
                    d.write("Robotik Atölyesi Hoş Geldiniz!")

db_check()

# --- 3. VERİLERİ ÇEK ---
current_ip = get_remote_ip()
df_logs = pd.read_csv(FILES["data"])
df_users = pd.read_csv(FILES["users"])
df_ban = pd.read_csv(FILES["ban"])

# IP Tanıma ve Otomatik Kayıt Kontrolü
# Öncelikle bu IP ile daha önce kayıt olunmuş mu bakıyoruz
user_row = df_users[df_users["IP"] == current_ip]
is_registered = not user_row.empty
recognized_name = user_row["Isim"].values[0] if is_registered else "Seçiniz..."

# --- 4. TASARIM VE BİLDİRİM SCRIPTI ---
st.markdown("""
    <script>
    function notifyMe(text) {
      if (!("Notification" in window)) { alert("Bu tarayıcı bildirim desteklemiyor"); }
      else if (Notification.permission === "granted") { new Notification("Robotik Atölyesi", {body: text}); }
      else if (Notification.permission !== "denied") {
        Notification.requestPermission().then(permission => {
          if (permission === "granted") { new Notification("Robotik Atölyesi", {body: text}); }
        });
      }
    }
    </script>
    <style>
    .stApp { background-color: #0e1117; color: #c9d1d9; }
    .stButton button { background: linear-gradient(45deg, #ff8c00, #d35400); color: white; border-radius: 8px; font-weight: bold; }
    .kvkk-box { background: #161b22; padding: 20px; border-radius: 10px; border: 1px solid #30363d; font-size: 13px; line-height: 1.6; margin-bottom: 20px; }
    .reg-box { background: #1b2838; padding: 20px; border-radius: 10px; border: 1px solid #1a73e8; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- 5. YAN MENÜ ---
with st.sidebar:
    secim = option_menu("Robotik Lab", ["Giriş Ekranı", "Duyurular", "Liderlik", "Yönetici"], 
        icons=['cpu', 'megaphone', 'trophy', 'gear'], default_index=0)

# --- 6. SAYFALAR ---

if secim == "Giriş Ekranı":
    st.title("📟 Akıllı Terminal")
    
    # 1. ADIM: KAYIT KONTROLÜ
    if not is_registered:
        st.subheader("👋 İlk Kez Geldiniz! Lütfen Kayıt Olun")
        with st.container():
            st.markdown('<div class="reg-box">', unsafe_allow_html=True)
            reg_name = st.text_input("Ad Soyad:")
            reg_email = st.text_input("Gmail Adresiniz (Duyurular için):")
            reg_class = st.selectbox("Sınıfınız:", ["9", "10", "11", "12"], key="reg_class")
            
            if st.button("Kayıt Ol ve Sisteme Gir"):
                if reg_name and "@gmail.com" in reg_email.lower():
                    # Yeni kullanıcıyı kaydet
                    new_user = pd.DataFrame([[reg_name, reg_class, reg_email, current_ip]], 
                                          columns=["Isim", "Sinif", "Email", "IP"])
                    new_user.to_csv(FILES["users"], mode='a', index=False, header=False)
                    st.success("Kaydınız başarıyla yapıldı! Yönlendiriliyorsunuz...")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Lütfen geçerli bir isim ve @gmail.com adresi girin.")
            st.markdown('</div>', unsafe_allow_html=True)
            st.info("💡 Not: Her cihazdan (IP) sadece bir kez kayıt yapılabilir.")
    
    # 2. ADIM: GİRİŞ İŞLEMLERİ (Sadece kayıtlılarsa görürler)
    else:
        # KVKK Metni
        with st.expander("📄 KVKK Aydınlatma Metni", expanded=False):
            st.markdown("""
            <div class="kvkk-box">
            <b>Kişisel Verilerin Korunması Kanunu (KVKK) Bilgilendirmesi:</b><br>
            Sisteme giriş yaptığınızda; <b>Ad-Soyad, Email, IP Adresiniz ve İşlem Detaylarınız</b> kaydedilir. 
            Bu veriler duyuru gönderimi ve güvenlik takibi için kullanılır.
            </div>
            """, unsafe_allow_html=True)
        
        kvkk_onay = st.checkbox("KVKK Metnini okudum, devam etmek istiyorum.", value=True)

        if kvkk_onay:
            st.info(f"✨ Hoş geldin, **{recognized_name}**! (Sistem seni IP adresinden tanıdı)")

            col1, col2 = st.columns([2, 1])
            with col1:
                islem = st.text_area("Ne yapıyorsun?", placeholder="Örn: Arduino kodlama, Drone montajı...")
            with col2:
                tr_simdi = get_turkiye_saati()
                secilen_saat = st.time_input("Saat:", tr_simdi.time())
                tip = st.radio("İşlem:", ["GİRİŞ", "ÇIKIŞ"], horizontal=True)
                lehim = st.toggle("🔥 Lehim Kullanıldı")

            if st.button("🚀 İŞLEMİ KAYDET"):
                zaman_str = f"{secilen_saat.strftime('%H:%M')} | {tr_simdi.strftime('%d-%m')}"
                pd.DataFrame([[zaman_str, recognized_name, islem, ("EVET" if lehim else "HAYIR"), tip, current_ip, 10 if tip=="GİRİŞ" else 0]], 
                            columns=df_logs.columns).to_csv(FILES["data"], mode='a', index=False, header=False)
                st.balloons()
                st.success("İşlem başarıyla kaydedildi!")
                time.sleep(1)
                st.rerun()
        else:
            st.warning("⚠️ Devam etmek için KVKK onay kutusunu işaretleyin.")

elif secim == "Duyurular":
    st.title("📢 Atölye Panosu")
    with open(FILES["duyuru"], "r", encoding="utf-8") as f: content = f.read()
    st.markdown(f"<div style='background:#1c2128; padding:20px; border-radius:10px; border:1px solid #ff8c00;'>{content}</div>", unsafe_allow_html=True)
    if st.button("🔔 Bildirimleri Aç (Tarayıcı)"):
        st.components.v1.html("<script>notifyMe('Bildirimler Aktif!');</script>")

elif secim == "Liderlik":
    st.title("🏆 Sıralama")
    liderler = df_logs.groupby("İsim")["Puan"].sum().reset_index().sort_values("Puan", ascending=False)
    banli_adlar = df_ban["Isim"].tolist()
    st.dataframe(liderler[~liderler["İsim"].isin(banli_adlar)], use_container_width=True, hide_index=True)

elif secim == "Yönetici":
    sifre = st.text_input("Şifre:", type="password")
    if sifre == "15531552":
        t1, t2, t3 = st.tabs(["Kayıtlı Öğrenciler", "Ban Yönetimi", "Duyuru"])
        
        with t1:
            st.subheader("Kayıtlı Öğrenci Listesi")
            st.dataframe(df_users, use_container_width=True)
            if st.button("Verileri Yenile"): st.rerun()

        with t2:
            st.subheader("⛔ Ban / 🔓 Ban Kaldır")
            banli_list = df_ban["Isim"].tolist()
            c1, c2 = st.columns(2)
            with c1:
                b_ad = st.selectbox("Banlanacak Kişi:", ["Seçiniz..."] + sorted(df_users["Isim"].tolist()))
                b_se = st.text_input("Sebep:")
                if st.button("Banla"):
                    pd.DataFrame([["ADMIN", b_ad, b_se]], columns=df_ban.columns).to_csv(FILES["ban"], mode='a', index=False, header=False)
                    st.rerun()
            with c2:
                un_ad = st.selectbox("Banı Kaldırılacak Kişi:", ["Seçiniz..."] + sorted(banli_list))
                if st.button("Seçili Kişinin Banını Kaldır"):
                    if un_ad != "Seçiniz...":
                        df_ban[df_ban["Isim"] != un_ad].to_csv(FILES["ban"], index=False)
                        st.success(f"{un_ad} artık cezalı değil."); time.sleep(1); st.rerun()

        with t3:
            y_duy = st.text_area("Duyuru Yaz (Öğrencilere duyurulacaktır):")
            if st.button("Yayınla"):
                with open(FILES["duyuru"], "w", encoding="utf-8") as f: f.write(y_duy)
                st.components.v1.html(f"<script>notifyMe('YENİ DUYURU: {y_duy}');</script>")
                st.success("Duyuru yayınlandı."); time.sleep(1); st.rerun()
