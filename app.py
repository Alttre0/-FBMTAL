import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime, timedelta
from streamlit_option_menu import option_menu

# --- 1. AYARLAR ---
# Sadece APP ID gerekli (Abone toplamak için). REST API KEY'i sildik.
ONESIGNAL_APP_ID = "89c0debc-c7a8-4ffe-9848-9405df878dd4"

def get_turkiye_saati():
    return datetime.utcnow() + timedelta(hours=3)

# --- 2. GÜÇLENDİRİLMİŞ DOSYA YÖNETİMİ (HATA ÖNLEYİCİ) ---
FILES = {
    "data": "robotik_log.csv", 
    "users": "ogrenciler.csv", 
    "duyuru": "duyuru.txt",
    "logo": "logo.jpg"
}

def veri_yukle(dosya_turu):
    yol = FILES[dosya_turu]
    # Sütunları belirle
    cols = ["Zaman", "İsim", "İşlem", "Bildirim_Izni", "Puan"] if dosya_turu == "data" else ["Isim", "Sinif", "Son_Bildirim_Durumu"]
    
    # Dosya yoksa veya boyutu 0 ise (boşsa) yeniden oluştur
    if not os.path.exists(yol) or os.stat(yol).st_size == 0:
        df = pd.DataFrame(columns=cols)
        df.to_csv(yol, index=False)
        return df
    
    # Okurken hata olursa boş döndür (EmptyDataError çözümü)
    try:
        return pd.read_csv(yol)
    except:
        return pd.DataFrame(columns=cols)

# Dosyaları yükle
df_users = veri_yukle("users")
df_logs = veri_yukle("data")

# Duyuru dosyası yoksa oluştur
if not os.path.exists(FILES["duyuru"]):
    with open(FILES["duyuru"], "w", encoding="utf-8") as f: f.write("Henüz duyuru yok.")

# --- 3. ABONE TOPLAMA SİSTEMİ (JS) ---
# Bu kısım ŞART. Yoksa öğrenci listesi OneSignal'e düşmez, mesaj atamazsın.
st.markdown(f"""
<script src="https://cdn.onesignal.com/sdks/web/v16/OneSignalSDK.sw.js" defer></script>
<script src="https://cdn.onesignal.com/sdks/OneSignalSDK.js" async=""></script>
<script>
  window.OneSignal = window.OneSignal || [];
  OneSignal.push(function() {{
    OneSignal.init({{
      appId: "{ONESIGNAL_APP_ID}",
      allowLocalhostAsSecureOrigin: true,
      promptOptions: {{ slidedown: {{ enabled: true, autoPrompt: true, timeDelay: 1 }} }}
    }});

    // İzin durumunu kontrol et ve Python'a bildir
    setInterval(function() {{
        OneSignal.getNotificationPermission(function(permission) {{
            const input = window.parent.document.querySelector('input[aria-label="perm_status"]');
            if (input && input.value !== permission) {{
                input.value = permission;
                input.dispatchEvent(new Event('input', {{ bubbles: true }}));
            }}
        }});
    }}, 1000);
  }});
</script>
""", unsafe_allow_html=True)

# --- 4. TASARIM ---
st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: #c9d1d9; }
    .main-card { background: #161b22; padding: 20px; border-radius: 10px; border-left: 4px solid #ff8c00; margin-bottom: 20px; }
    .stButton button { background: #ff8c00; color: white; border-radius: 5px; width: 100%; border: none; font-weight: bold; }
    div[data-testid="stInput"] { display: none; }
    </style>
    """, unsafe_allow_html=True)

# Gizli input (JS'den veri almak için)
perm_status = st.text_input("perm_status", value="default", label_visibility="collapsed")

# --- 5. MENÜ ---
with st.sidebar:
    if os.path.exists(FILES["logo"]):
        st.image(FILES["logo"], use_container_width=True)
    secim = option_menu(None, ["Giriş", "Duyurular", "Sıralama", "Admin"], 
                        icons=['cpu', 'megaphone', 'award', 'shield-lock'], default_index=0)

# --- 6. SAYFALAR ---
if secim == "Giriş":
    st.title("Atölye Giriş Paneli")
    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    
    if df_users.empty:
        st.info("⚠️ Sistemde öğrenci yok. Admin panelinden ekleyiniz.")
    else:
        # İzin uyarısı
        if perm_status != "granted":
            st.warning("⚠️ Bildirim izni vermediniz! OneSignal listesinde görünmezsiniz.")
        
        # Alfabetik sıralama ile isim listesi
        isimler = sorted(df_users["Isim"].astype(str).tolist())
        secilen = st.selectbox("İsminiz:", ["Seçiniz..."] + isimler)
        islem = st.text_input("Yapılacak İşlem:")
        
        if st.button("Giriş Yap"):
            if secilen != "Seçiniz...":
                zaman = get_turkiye_saati().strftime("%H:%M | %d-%m")
                durum = "Verildi" if perm_status == "granted" else "Verilmedi"
                
                # Log dosyasına yaz
                yeni_kayit = pd.DataFrame([[zaman, secilen, islem, durum, 10]], columns=df_logs.columns)
                yeni_kayit.to_csv(FILES["data"], mode='a', index=False, header=False)
                
                # Kullanıcı durumunu güncelle
                df_users.loc[df_users["Isim"] == secilen, "Son_Bildirim_Durumu"] = durum
                df_users.to_csv(FILES["users"], index=False)
                
                st.success(f"Giriş Başarılı: {secilen}")
                time.sleep(1); st.rerun()
            else:
                st.error("Lütfen isminizi seçin.")
    st.markdown("</div>", unsafe_allow_html=True)

elif secim == "Duyurular":
    st.title("Atölye Panosu")
    with open(FILES["duyuru"], "r", encoding="utf-8") as f:
        icerik = f.read()
    st.markdown(f"<div class='main-card' style='font-size: 18px;'>{icerik}</div>", unsafe_allow_html=True)

elif secim == "Sıralama":
    st.title("Puan Durumu")
    if not df_logs.empty:
        # Puanları topla ve sırala
        try:
            # Puan sütununu sayıya çevir (hata varsa 0 say)
            df_logs["Puan"] = pd.to_numeric(df_logs["Puan"], errors='coerce').fillna(0)
            skor = df_logs.groupby("İsim")["Puan"].sum().reset_index().sort_values("Puan", ascending=False)
            st.table(skor)
        except Exception as e:
            st.error(f"Sıralama hesaplanırken hata oluştu: {e}")
    else:
        st.info("Henüz veri girişi yapılmamış.")

elif secim == "Admin":
    sifre = st.text_input("Admin Şifresi:", type="password")
    if sifre == "15531552":
        t1, t2, t3 = st.tabs(["Öğrenci Yönetimi", "Site Panosu", "Log Temizle"])
        
        with t1:
            st.write("### Kayıtlı Öğrenciler ve Bildirim Durumu")
            st.dataframe(df_users[["Isim", "Son_Bildirim_Durumu"]], use_container_width=True)
            
            yeni_ad = st.text_input("Öğrenci Ekle (Ad Soyad):")
            if st.button("Kaydet"):
                if yeni_ad:
                    pd.DataFrame([[yeni_ad, "10", "Bilinmiyor"]], columns=df_users.columns).to_csv(FILES["users"], mode='a', index=False, header=False)
                    st.success("Eklendi.")
                    st.rerun()

            st.write("---")
            if not df_users.empty:
                sil = st.selectbox("Silinecek Kişi:", df_users["Isim"].tolist())
                if st.button("Sil"):
                    df_users = df_users[df_users["Isim"] != sil]
                    df_users.to_csv(FILES["users"], index=False)
                    st.warning("Silindi.")
                    st.rerun()

        with t2:
            st.subheader("Site İçi Duyuru Güncelle")
            st.info("ℹ️ Buraya yazdığın sadece **bu web sitesindeki** 'Duyurular' sayfasında görünür. Telefonlara gitmez.")
            mesaj = st.text_area("Pano Mesajı:")
            if st.button("Panoyu Güncelle"):
                with open(FILES["duyuru"], "w", encoding="utf-8") as f:
                    f.write(mesaj)
                st.success("Web sitesindeki duyuru güncellendi. Şimdi OneSignal sitesinden bildirim atabilirsin.")

        with t3:
            if st.button("Tüm Giriş Loglarını Sıfırla"):
                # Sadece başlıkları bırak, içeriği sil
                pd.DataFrame(columns=df_logs.columns).to_csv(FILES["data"], index=False)
                st.success("Loglar temizlendi.")
                st.rerun()
