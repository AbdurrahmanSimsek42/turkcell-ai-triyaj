import json
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# Şebeke veritabanını yükle
def sebeke_verisini_oku():
    with open("sebeke_verileri.json", "r", encoding="utf-8") as f:
        return json.load(f)["istasyonlar"]

# 1. Triyaj Ajanı: Şikayetten konum ve problem türünü çıkarır
def ajan_triyaj(musteri_mesaji, client):
    prompt = f"""
    Sen Turkcell Triyaj Ajanısın. Görevin müşteri mesajını analiz edip konumu ve sorunu ayrıştırmaktır.
    Müşteri Mesajı: "{musteri_mesaji}"
    
    Yalnızca şu JSON formatında yanıt ver, başka hiçbir metin ekleme:
    {{"aranacak_kelime": "şehir veya ilçe adı", "sorun_tipi": "şebeke / fatura / cihaz"}}
    """
    response = client.chat.completions.create(
       model="qwen/qwen3.8-27b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )
    return response.choices[0].message.content

# 2. Teşhis Ajanı: JSON veritabanından istasyon durumunu eşleştirir
def ajan_sebeke_teshis(aranacak_kelime, istasyonlar):
    aranacak_kelime = aranacak_kelime.lower()
    for ist in istasyonlar:
        if aranacak_kelime in ist["bolge"].lower():
            return ist
    return None

# 3. Self-Healing ve Açıklama Ajanı: Otonom karar verir ve gerekçesini açıklar
def ajan_karar_ve_onarım(musteri_mesaji, istasyon_bilgisi, client):
    prompt = f"""
    Sen Turkcell Otonom Şebeke Çözüm ve Açıklanabilir Yapay Zekâ (XAI) Ajanısın.
    
    Müşteri Mesajı: "{musteri_mesaji}"
    Baz İstasyonu Verisi: {json.dumps(istasyon_bilgisi, ensure_ascii=False) if istasyon_bilgisi else "Bölgede arıza kaydı bulunamadı."}
    
    Aşağıdaki kurallara göre karar ver:
    - Doluluk oranı %85 üzerindeyse yedek istasyona trafik yönlendir (Self-Healing).
    - Elektrik veya donanım arızası varsa teknik saha ekibi için acil bilet aç.
    - Şebeke normalse müşteriye cihaz ayarlarını (uçak modu/APN) kontrol etmesini öner.
    
    Çıktını TAM OLARAK şu 3 başlıkla ver:
    1. TEŞHİS:
    2. OTONOM AKSİYON (SELF-HEALING):
    3. GEREKÇE (AÇIKLANABİLİR AI):
    """
    response = client.chat.completions.create(
        model="qwen/qwen3.8-27b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )
    return response.choices[0].message.content

# Test Fonksiyonu
if __name__ == "__main__":
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or api_key == "buraya_api_anahtari_gelecek":
        print("[!] Lütfen önce .env dosyasina geçerli bir GROQ_API_KEY ekleyin.")
    else:
        client = OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=api_key
        )
        ornek_mesaj = "Konya Ereğli merkezdeyim, sabahtan beri mobil internetim çok yavaş, video bile açamıyorum."
        print(f"--- MÜŞTERİ BİLDİRİMİ ---\n{ornek_mesaj}\n")
        
        # 1. Adım: Triyaj
        triyaj_ham = ajan_triyaj(ornek_mesaj, client)
        print(f"--- 1. TRİYAJ AJANI ÇIKTISI ---\n{triyaj_ham}\n")
        
        # Triyaj çıktısından konumu al
        try:
            triyaj_veri = json.loads(triyaj_ham)
            konum = triyaj_veri.get("aranacak_kelime", "Ereğli")
        except:
            konum = "Ereğli"
            
        # 2. Adım: Veri Tabanı Eşleşmesi
        istasyonlar = sebeke_verisini_oku()
        istasyon = ajan_sebeke_teshis(konum, istasyonlar)
        print(f"--- 2. TEŞHİS VERİSİ (BAZ İSTASYONU) ---\n{istasyon}\n")
        
        # 3. Adım: Otonom Karar ve Açıklama
        nihai_karar = ajan_karar_ve_onarım(ornek_mesaj, istasyon, client)
        print(f"--- 3. NİHAİ KARAR & SELF-HEALING ---\n{nihai_karar}")