import streamlit as st
import json
import os
from dotenv import load_dotenv
from openai import OpenAI
from triyaj_ajanlari import (
    sebeke_verisini_oku,
    ajan_triyaj,
    ajan_sebeke_teshis,
    ajan_karar_ve_onarım
)

# Ortam değişkenleri ve Groq istemcisi
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

st.set_page_config(page_title="Turkcell AI Triyaj & Self-Healing", layout="wide")

st.title("📶 Turkcell Otonom Şebeke Triyaj & Self-Healing Paneli")
st.markdown("Bu sistem; müşteri şikayetlerini analiz eden, arka plan şebeke loglarını denetleyen ve otonom iyileştirme (self-healing) aksiyonları alan çoklu ajan mimarisidir.")

# Sol sütun: Test Senaryoları ve Girdi
st.sidebar.header("📋 Hızlı Test Senaryoları")
secili_senaryo = st.sidebar.radio(
    "Senaryo Seçin:",
    (
        "Senaryo 1: Aşırı Şebeke Yoğunluğu (Konya Ereğli)",
        "Senaryo 2: Donanım ve Elektrik Kesintisi (Malatya Battalgazi)",
        "Senaryo 3: Normal Şebeke / Cihaz Problemi (İstanbul Kadıköy)",
        "Özel Giriş Yap"
    )
)

varsayilan_mesajlar = {
    "Senaryo 1: Aşırı Şebeke Yoğunluğu (Konya Ereğli)": "Konya Ereğli merkezdeyim, sabahtan beri mobil internetim çok yavaş, video bile açamıyorum.",
    "Senaryo 2: Donanım ve Elektrik Kesintisi (Malatya Battalgazi)": "Battalgazi kampüsündeyim, telefonum tamamen 'Servis Yok' diyor, arama yapamıyorum.",
    "Senaryo 3: Normal Şebeke / Cihaz Problemi (İstanbul Kadıköy)": "Kadıköy Rıhtım'dayım, internetim çekmiyor hiçbir yere bağlanamıyorum.",
    "Özel Giriş Yap": ""
}

mesaj_metni = st.text_area(
    "Müşteri Bildirimi / Şikayet Metni:",
    value=varsayilan_mesajlar[secili_senaryo],
    height=100
)

if st.button("🚀 Otonom Triyaj ve Analizi Başlat", type="primary"):
    if not api_key:
        st.error("GROQ_API_KEY bulunamadı. Lütfen .env dosyasını kontrol edin.")
    elif not mesaj_metni.strip():
        st.warning("Lütfen analiz edilecek bir müşteri mesajı girin.")
    else:
        client = OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=api_key
        )
        
        with st.spinner("Ajanlar analiz yapıyor ve şebeke telemetrisi taranıyor..."):
            # 1. Triyaj Ajanı
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.subheader("1. Triyaj Ajanı (NLP)")
                triyaj_ham = ajan_triyaj(mesaj_metni, client)
                st.code(triyaj_ham, language="json")
                
                try:
                    triyaj_veri = json.loads(triyaj_ham)
                    konum = triyaj_veri.get("aranacak_kelime", "")
                except:
                    konum = "Ereğli"
            
            # 2. Teşhis Ajanı & Veritabanı
            with col2:
                st.subheader("2. Şebeke Logu & Telemetri")
                istasyonlar = sebeke_verisini_oku()
                istasyon = ajan_sebeke_teshis(konum, istasyonlar)
                
                if istasyon:
                    st.success(f"İstasyon Bulundu: {istasyon['istasyon_id']}")
                    st.metric("İstasyon Doluluk Oranı", f"%{istasyon['doluluk_orani']}")
                    st.json(istasyon)
                else:
                    st.warning("Eşleşen istasyon kaydı bulunamadı (Genel Altyapı).")

            # 3. Self-Healing & Açıklanabilirlik
            with col3:
                st.subheader("3. Otonom Karar (Self-Healing & XAI)")
                karar_cikti = ajan_karar_ve_onarım(mesaj_metni, istasyon, client)
                st.markdown(karar_cikti)