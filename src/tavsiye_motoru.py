import json
import random
import os

class TavsiyeMotoru:
    """
    Modul Amaci: Hesaplanan yetkinlik skorlarina gore uygun gelisim 
    tavsiyelerini uretir ve her yetkinlik icin seviye belirlemesi yapar.
    """

    def __init__(self, jsonYolu=None):
        if jsonYolu is None:
            projeKoku = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.jsonYolu = os.path.join(projeKoku, "lookup", "tavsiye_kurallari.json")
        else:
            self.jsonYolu = jsonYolu

        self.tavsiyeVerisi = self._kurallariYukle(self.jsonYolu)
        self.kullanilanOneriler = set()

    def _kurallariYukle(self, dosyaYolu):
        """
        JSON dosyasini guvenli sekilde okur ve sozluk yapisina cevirir.
        """
        if not os.path.exists(dosyaYolu):
            return {}
        try:
            with open(dosyaYolu, "r", encoding="utf-8-sig") as dosya:
                icerik = dosya.read().strip()
                return json.loads(icerik) if icerik else {}
        except Exception:
            return {}

    def _metniNormalizeEt(self, metin):
        """
        Karsilastirma hatalarini onlemek icin metni kucuk harfe cevirir 
        ve Turkce karakterleri standart Latin karakterlerine donusturur.
        """
        metin = str(metin).lower()
        donusum = {
            'ç': 'c', 'ğ': 'g', 'ı': 'i', 'i̇': 'i', 'İ': 'i',
            'ö': 'o', 'ş': 's', 'ü': 'u'
        }
        for kaynak, hedef in donusum.items():
            metin = metin.replace(kaynak, hedef)
        return metin.strip()

    def _yetkinlikAnahtariniBul(self, yetkinlikAdi):
        """
        CSV'den gelen yetkinlik ismini JSON'daki teknik basliga donusturur.
        """
        temizAd = self._metniNormalizeEt(yetkinlikAdi)
        eslemeTablosu = {
            "analitik": "Analitik Düşünme",
            "iletisim": "İletişim",
            "isbirligi": "İşbirliği",
            "teknik": "Teknik Uzmanlık",
            "emniyet": "Emniyet",
            "surec": "Süreç Disiplini",
            "etik": "Etik Duruş"
        }
        for anahtar, tamAd in eslemeTablosu.items():
            if anahtar in temizAd:
                return tamAd
        return yetkinlikAdi

    def _kategoriBelirle(self, skor):
        """
        Puan araligina gore gelisim seviyesini (Strong, Medium, Weak) dondurur.
        """
        if skor >= 3.5:
            return "strong"
        if skor >= 3.0:
            return "medium"
        return "weak"

    def oneriSec(self, yetkinlikAdi, kategori):
        """
        Kategoriye uygun, tekrarsiz bir oneri secer.
        """
        anahtar = self._yetkinlikAnahtariniBul(yetkinlikAdi)
        adaylar = self.tavsiyeVerisi.get(anahtar, {}).get(kategori, [])
        
        if not adaylar:
            return f"{yetkinlikAdi} icin uygun aksiyon tanimi bulunamadi."

        # Rapor icinde her seferinde farkli tavsiyeler sunmaya calisir
        uygunlar = [o for o in adaylar if o not in self.kullanilanOneriler]
        secilen = random.choice(uygunlar if uygunlar else adaylar)
        self.kullanilanOneriler.add(secilen)
        return secilen

    def topluTavsiyeUret(self, skorlarSozlugu):
        """
        Tum yetkinlik skorlari icin seviye ve tavsiye iceren raporu uretir.
        """
        raporListesi = []
        for ad, puan in skorlarSozlugu.items():
            kategori = self._kategoriBelirle(puan)
            raporListesi.append({
                "yetkinlik": ad,
                "skor": puan,
                "seviye": kategori,
                "tavsiye": self.oneriSec(ad, kategori)
            })
        return raporListesi

if __name__ == "__main__":
    motor = TavsiyeMotoru()
    testVerisi = {
        'Analitik': 4.09, 'Emniyet': 2.53, 'Etik Duruş': 3.56, 
        'Süreç': 4.02, 'Teknik': 4.33, 'İletişim': 3.36, 'İşbirliği': 4.04
    }
    
    print("\n🚀 Toplu Gelişim Tavsiyeleri Raporu (Seviye Dahil)")
    print("-" * 60)
    for kalem in motor.topluTavsiyeUret(testVerisi):
        seviyeEtiketi = kalem['seviye'].upper()
        print(f"📌 {kalem['yetkinlik']} ({kalem['skor']}) -> [{seviyeEtiketi}]")
        print(f"   Öneri: {kalem['tavsiye']}\n")