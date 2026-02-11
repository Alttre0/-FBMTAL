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
            elif f == "users": cols = ["Isim", "Sinif"]
            elif f == "ban": cols = ["IP", "Isim", "Sebep"]
            if f != "duyuru": pd.DataFrame(columns=cols).to_csv(path, index=False)
            else:
                with open(path, "w", encoding="utf-8") as d:
                    d.write("Robotik Atölyesi Hoş Geldiniz!")

db_check()

# --- 3. VERİLERİ ÇEK ---
current_ip = get_remote_ip()
df_logs = pd.read_csv(FILES["data"])
df_users = pd.read_csv(FILES["users"])
df_ban = pd.read_csv(FILES["ban"])

# IP Tanıma
last_entry = df_logs[df_logs["IP"] == current_ip].tail(1)
recognized_name = last_entry["İsim"].values[0] if not last_entry.empty else "Seçiniz..."
last_job = last_entry["İşlem"].values[0] if not last_entry.empty else ""

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
    </style>
    """, unsafe_allow_html=True)

# --- 5. YAN MENÜ ---
with st.sidebar:
    secim = option_menu("Robotik Lab", ["Giriş Ekranı", "Duyurular", "Liderlik", "Yönetici"], 
        icons=['cpu', 'megaphone', 'trophy', 'gear'], default_index=0)

# --- 6. SAYFALAR ---

if secim == "Giriş Ekranı":
    st.title("📟 Akıllı Terminal")
    
    # KVKK Metni
    with st.expander("📄 KVKK Aydınlatma Metni (Okumak için tıklayın)", expanded=True):
        st.markdown("""
        <div class="kvkk-box">
        <b>Kişisel Verilerin Korunması Kanunu (KVKK) Bilgilendirmesi:</b><br>
        Bu sistem, atölye güvenliğini sağlamak, hileleri önlemek ve öğrenci gelişimini takip etmek amacıyla kullanılmaktadır. 
        Sisteme giriş yaptığınızda; <b>Ad-Soyad, IP Adresiniz ve İşlem Detaylarınız</b> veritabanımıza kaydedilir. 
        Bu veriler üçüncü şahıslarla paylaşılmaz ve sadece atölye yönetimi tarafından görülür. 
        Kayıt butonuna basarak bu verilerin işlenmesini kabul etmiş sayılırsınız.
        </div>
        """, unsafe_allow_html=True)
    
    kvkk_onay = st.checkbox("KVKK Metnini okudum, verilerimin işlenmesini kabul ediyorum.")

    if kvkk_onay:
        if recognized_name != "Seçiniz...":
            st.info(f"✨ Tanındı: {recognized_name} (Son iş: {last_job})")

        col1, col2 = st.columns([2, 1])
        with col1:
            u_list = sorted(df_users["Isim"].tolist())
            v_idx = u_list.index(recognized_name) + 1 if recognized_name in u_list else 0
            secilen_ad = st.selectbox("İsminiz:", ["Seçiniz..."] + u_list, index=v_idx)
            islem = st.text_area("Ne yapıyorsun?", value=last_job if secilen_ad == recognized_name else "")
        with col2:
            tr_simdi = get_turkiye_saati()
            secilen_saat = st.time_input("Saat:", tr_simdi.time())
            tip = st.radio("İşlem:", ["GİRİŞ", "ÇIKIŞ"], horizontal=True)
            lehim = st.toggle("🔥 Lehim")

        if st.button("🚀 KAYDET"):
            if secilen_ad != "Seçiniz...":
                zaman_str = f"{secilen_saat.strftime('%H:%M')} | {tr_simdi.strftime('%d-%m')}"
                pd.DataFrame([[zaman_str, secilen_ad, islem, ("EVET" if lehim else "HAYIR"), tip, current_ip, 10 if tip=="GİRİŞ" else 0]], 
                            columns=df_logs.columns).to_csv(FILES["data"], mode='a', index=False, header=False)
                st.balloons(); st.success("Kaydedildi!"); time.sleep(1); st.rerun()
            else: st.error("İsim seç!")
    else:
        st.warning("⚠️ Devam etmek için KVKK metnini onaylamanız gerekmektedir.")

elif secim == "Duyurular":
    st.title("📢 Atölye Panosu")
    with open(FILES["duyuru"], "r", encoding="utf-8") as f: content = f.read()
    st.markdown(f"<div style='background:#1c2128; padding:20px; border-radius:10px; border:1px solid #ff8c00;'>{content}</div>", unsafe_allow_html=True)
    # Bildirim isteği butonu
    if st.button("🔔 Bildirimleri Aç (PC/Mobil)"):
        st.components.v1.html("<script>notifyMe('Bildirimler Aktif!');</script>")

elif secim == "Liderlik":
    st.title("🏆 Sıralama")
    liderler = df_logs.groupby("İsim")["Puan"].sum().reset_index().sort_values("Puan", ascending=False)
    banli_adlar = df_ban["Isim"].tolist()
    st.dataframe(liderler[~liderler["İsim"].isin(banli_adlar)], use_container_width=True, hide_index=True)

elif secim == "Yönetici":
    sifre = st.text_input("Şifre:", type="password")
    if sifre == "15531552":
        t1, t2, t3 = st.tabs(["Öğrenci & Puan", "Ban Yönetimi", "Duyuru"])
        
        with t1:
            st.subheader("Yeni Öğrenci")
            y_ad = st.text_input("Ad Soyad:")
            y_si = st.selectbox("Sınıf:", ["9","10","11","12"])
            if st.button("Ekle"):
                if y_ad and y_ad not in df_users["Isim"].values:
                    pd.DataFrame([[y_ad, y_si]], columns=["Isim", "Sinif"]).to_csv(FILES["users"], mode='a', index=False, header=False)
                    st.success("Eklendi"); st.rerun()

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
                # KİŞİYE ÖZEL BAN KALDIRMA
                un_ad = st.selectbox("Banı Kaldırılacak Kişi:", ["Seçiniz..."] + sorted(banli_list))
                if st.button("Seçili Kişinin Banını Kaldır"):
                    if un_ad != "Seçiniz...":
                        yeni_ban_df = df_ban[df_ban["Isim"] != un_ad]
                        yeni_ban_df.to_csv(FILES["ban"], index=False)
                        st.success(f"{un_ad} artık cezalı değil."); time.sleep(1); st.rerun()

        with t3:
            y_duy = st.text_area("Duyuru Yaz:")
            if st.button("Yayınla"):
                with open(FILES["duyuru"], "w", encoding="utf-8") as f: f.write(y_duy)
                st.components.v1.html(f"<script>notifyMe('YENİ DUYURU: {y_duy}');</script>")
                st.success("Duyuru yayınlandı ve bildirim gönderildi."); time.sleep(1); st.rerun()
