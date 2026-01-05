import json
import os

class AgirlikMotoru:
    """
    Modul Amaci: 360 derece degerlendirme sistemindeki dinamik agirlik 
    hesaplamalarini ve grup bazli paylastirma mantigini yonetir.
    """

    def __init__(self):
        # Proje kok dizinine ulasarak JSON dosyasinin yolunu belirler
        anaDizin = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        jsonYolu = os.path.join(anaDizin, "lookup", "agirlik_kurallari.json")

        try:
            with open(jsonYolu, "r", encoding="utf-8") as dosya:
                self.kurallar = json.load(dosya)
        except Exception as hata:
            raise RuntimeError(f"Agirlik kurallari dosyasi yuklenemedi: {hata}")

    def hesaplaAgirliklar(self, rol, grupSayilari):
        """
        Gelen rol ve grup mevcudiyetine gore nihai agirlik sozlugunu doner.
        """
        rolTemiz = rol.lower().strip()

        if rolTemiz == "beyaz":
            agirliklar = self._beyazYakaAgirlikHesapla(grupSayilari)
        elif rolTemiz == "mavi":
            agirliklar = self._maviYakaAgirlikHesapla(grupSayilari)
        else:
            raise ValueError("Gecersiz rol tanimi. 'beyaz' veya 'mavi' olmali.")

        return self._agirliklariNormalizeEt(agirliklar)

    def _beyazYakaAgirlikHesapla(self, grupSayilari):
        """
        Beyaz yaka kurallarina gore eksik gruplarin payini mevcutlara dagitir.
        """
        guncelAgirliklar = self.kurallar["beyaz_yaka"]["default_weights"].copy()
        
        # Veri setinde hic uyesi olmayan gruplari tespit eder
        eksikGruplar = [g for g in guncelAgirliklar if grupSayilari.get(g, 0) == 0]

        if not eksikGruplar:
            return guncelAgirliklar

        # Eksik gruplarin toplam agirligini hesaplar ve onlari sifirlar
        dagitilacakPuan = sum(guncelAgirliklar[g] for g in eksikGruplar)
        for grup in eksikGruplar:
            guncelAgirliklar[grup] = 0.0

        # Kalan puani mevcut olan gruplara esit sekilde paylastirir
        mevcutGruplar = [g for g in guncelAgirliklar if g not in eksikGruplar]
        
        if mevcutGruplar:
            payBasinaEk = dagitilacakPuan / len(mevcutGruplar)
            for grup in mevcutGruplar:
                guncelAgirliklar[grup] += payBasinaEk

        return guncelAgirliklar

    def _maviYakaAgirlikHesapla(self, grupSayilari):
        """
        Mavi yaka rollerinde yonetici mevcudiyetine gore agirlik belirler.
        """
        varsayilan = self.kurallar["mavi_yaka"]["default_weights"].copy()
        
        yonetici1VarMi = grupSayilari.get("yonetici1", 0) > 0
        yonetici2VarMi = grupSayilari.get("yonetici2", 0) > 0

        if yonetici1VarMi and yonetici2VarMi:
            return varsayilan
        
        if yonetici1VarMi:
            return {"yonetici1": 1.0, "yonetici2": 0.0}
        
        if yonetici2VarMi:
            return {"yonetici1": 0.0, "yonetici2": 1.0}

        raise ValueError("Mavi yaka hesaplamasi icin en az bir yonetici gereklidir.")

    def _agirliklariNormalizeEt(self, agirliklar):
        """
        Hesaplanan tum agirliklarin toplaminin 1.0 olmasini saglar.
        """
        toplamPuan = sum(agirliklar.values())

        if toplamPuan == 0:
            raise ValueError("Sistem hatasi: Toplam agirlik sifir cikamaz.")

        for anahtar in agirliklar:
            agirliklar[anahtar] = round(agirliklar[anahtar] / toplamPuan, 4)

        return agirliklar

if __name__ == "__main__":
    # Modulun bagimsiz test edilmesi
    motor = AgirlikMotoru()
    testGruplari = {"yonetici1": 1, "ekip": 3, "ortak": 0, "ast": 0}
    sonuc = motor.hesaplaAgirliklar("beyaz", testGruplari)
    print(f"Dinamik Agirlik Sonuclari: {sonuc}")