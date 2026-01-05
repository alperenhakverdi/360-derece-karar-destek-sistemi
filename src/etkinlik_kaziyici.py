import os
import pandas as pd
from src.tavsiye_motoru import TavsiyeMotoru

class EtkinlikKaziyici:
    """
    Modul Amaci: Calisanlarin gelisim ihtiyaci duydugu (zayif ve orta) 
    tum alanlar icin CSV veritabanindan uygun egitimleri filtreler.
    """

    def __init__(self, csvYolu):
        self.csvYolu = csvYolu
        self.motor = TavsiyeMotoru()
        self.df = self._veriyiYukle()

    def _veriyiYukle(self):
        """
        CSV dosyasini okur ve kolon isimlerini standartlastirir.
        """
        if not os.path.exists(self.csvYolu):
            return pd.DataFrame(columns=["ad", "tema", "tarih", "lokasyon", "ucret", "link"])
        
        try:
            df = pd.read_csv(self.csvYolu)
            # CSV basliklarini kod icindeki teknik isimlerle esler
            kolonEsleme = {
                "Etkinlik Adı": "ad", "Etkinlik Adi": "ad",
                "Tema": "tema", "Tarih": "tarih", "Lokasyon": "lokasyon",
                "Ücret (TL)": "ucret", "Ucret (TL)": "ucret", "Link": "link"
            }
            return df.rename(columns=kolonEsleme)
        except Exception:
            # Okuma hatasi durumunda sistemin durmamasi icin bos tablo doner
            return pd.DataFrame(columns=["ad", "tema", "tarih", "lokasyon", "ucret", "link"])

    def _temaEslemesiYap(self, standartAd):
        """
        Tavsiye motorundan gelen anahtar basliklari CSV 'tema' kolonuyla eslestirir.
        """
        eslemeTablosu = {
            "İletişim": "iletisim_gelistirme",
            "İşbirliği": "takim_calismasi",
            "Analitik Düşünme": "analitik_atolye",
            "Teknik Uzmanlık": "teknik_egitim",
            "Emniyet": "is_gucu_guvenligi",
            "Süreç Disiplini": "surec_yonetimi",
            "Etik Duruş": "etik_farkindalik"
        }
        # Eslesme bulunamazsa kucuk harf halini dondurur
        return eslemeTablosu.get(standartAd, standartAd.lower())

    def etkinlikOnerisiGetir(self, yetkinlikAdi, maksAdet=2):
        """
        Belirli bir yetkinlik icin en yakin tarihli etkinlikleri getirir.
        """
        if self.df.empty:
            return []

        # Karakter normalizasyonu icin motoru kullanir
        standartAd = self.motor._yetkinlikAnahtariniBul(yetkinlikAdi)
        temaAnahtari = self._temaEslemesiYap(standartAd)

        filtre = self.df[self.df["tema"] == temaAnahtari].copy()
        
        if filtre.empty:
            return []

        # Tarihe gore kronolojik siralama yapar
        filtre = filtre.sort_values(by="tarih")
        return filtre.head(maksAdet).to_dict("records")

    def topluEtkinlikOner(self, skorlarSozlugu, esikPuani=3.5):
        """
        Zayif ve orta seviyedeki (esik puani alti) tum yetkinlikler icin 
        ayri ayri etkinlik onerileri uretir.
        """
        topluRapor = {}
        
        for ad, puan in skorlarSozlugu.items():
            # Belirlenen esik degerinin altindaki yetkinlikleri gelisim alani kabul eder
            if puan < esikPuani:
                oneriler = self.etkinlikOnerisiGetir(ad)
                if oneriler:
                    topluRapor[ad] = oneriler
                    
        return topluRapor

if __name__ == "__main__":
    # Proje kok dizinine gore yol tanimlama
    anaDizin = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    veriYolu = os.path.join(anaDizin, "data", "input", "etkinlik_listesi.csv")
    
    kaziyici = EtkinlikKaziyici(veriYolu)
    
    # Ornek skor veri seti
    gelenSkorlar = {
        'Analitik': 4.09, 'Emniyet': 2.53, 'Etik Duruş': 3.56, 
        'Süreç': 4.02, 'Teknik': 4.33, 'İletişim': 3.36, 'İşbirliği': 4.04
    }

    print("\n🚀 GELİŞİM ALANLARI İÇİN ETKİNLİK ÖNERİ RAPORU")
    print("=" * 75)
    
    # Tüm zayıf yetkinlikler için tarama yapar
    rapor = kaziyici.topluEtkinlikOner(gelenSkorlar)

    if not rapor:
        print("Gelişim ihtiyacı olan (3.5 altı) yetkinlik bulunamadı.")
    else:
        for yetkinlik, liste in rapor.items():
            print(f"\n📌 {yetkinlik.upper()} (Gelişim Aksiyonları):")
            for e in liste:
                print(f"   -> {e['ad']} | Tarih: {e['tarih']} | Konum: {e['lokasyon']}")