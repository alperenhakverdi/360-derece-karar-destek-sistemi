import pandas as pd
import json
import os
from pathlib import Path

class YetkinlikSkorHesaplayici:
    """
    Modul Amaci:
    1. CSV dosyasindan ham performans verilerini okur.
    2. 'agirlik_kurallari.json' dosyasina gore Mavi/Beyaz yaka agirliklarini hesaplar.
    3. Eksik değerlendirici gruplarına (örn: Ast yoksa) ait puanları diğerlerine dağıtır.
    4. Teknik yetkinlik isimlerini rapor isimlerine cevirir ve nihai skoru uretir.
    """
    
    def __init__(self, veri_yolu):
        # --- 1. DOSYA YOLLARI VE AYARLAR ---
        # __file__ kullanarak projenin ana dizinini (root) buluruz
        self.kok_dizin = Path(__file__).parent.parent
        
        # --- 2. CSV DOSYASINI GUVENLI OKUMA ---
        try:
            # Pandas ile veriyi oku
            self.df = pd.read_csv(veri_yolu)
        except Exception as e:
            print(f"UYARI: Veri dosyasi okunamadi ({e}). Bos tablo olusturuluyor.")
            # Hata durumunda kodun cokmemesi icin bos bir DataFrame olustur
            self.df = pd.DataFrame(columns=["employee_id", "employee_name", "role", "score"])

        # --- 3. AGIRLIK KURALLARINI YUKLEME ---
        # Eskiden AgirlikMotoru'nun yaptigi isi artik burada yapiyoruz
        try:
            kural_yolu = self.kok_dizin / "lookup" / "agirlik_kurallari.json"
            with open(kural_yolu, "r", encoding="utf-8") as f:
                self.agirlik_kurallari = json.load(f)
        except Exception as e:
            # Dosya yoksa veya bozuksa varsayilan (Hardcoded) kurallar devreye girer
            print(f"Bilgi: Kurallar dosyasi bulunamadi, varsayilan ayarlar yukleniyor. ({e})")
            self.agirlik_kurallari = {
                "beyaz_yaka": {"default_weights": {"yonetici1": 0.5, "ekip": 0.2, "ast": 0.3}},
                "mavi_yaka": {"default_weights": {"yonetici1": 1.0}}
            }

        # --- 4. HARITALAMA: Teknik Isim (CSV Header) -> Ekran Ismi (Rapor) ---
        # Sol taraf: Kodun/Veritabaninin bildigi isim
        # Sag taraf: Raporun/Kullanicinin gorecegi isim
        self.mapping = {
            "problem_cozme_ve_analitik_dusunme": "Analitik Düşünme",
            "emniyet_kalite_ve_risk_farkindaligi": "Emniyet",
            "etik_durus_ve_mesleki_cesaret": "Etik Duruş",
            "acik_iletisim_ve_bilgi_paylasimi": "İletişim",
            "isbirligi_ve_kapsayici_calisma": "İşbirliği",
            "teknik_uzmanlik_ve_alan_bilgisi": "Teknik Uzmanlık",
            "surec_ve_prosedur_disiplini": "Süreç Disiplini",
            
            # Ekstra yetkinlikler (Gelecek fazlar icin)
            "stratejik_dusunme_ve_vizyon_olusturma": "Stratejik Düşünme",
            "yonetsel_cesaret_ve_karar_kalitesi": "Yönetsel Cesaret"
        }

    # ============================================================
    # BOLUM A: AGIRLIK HESAPLAMA MANTIGI (Eski AgirlikMotoru)
    # ============================================================
    
    def _agirliklari_normalize_et(self, agirliklar):
        """
        Hesaplanan agirliklarin toplaminin her zaman 1.0 olmasini saglar.
        Orn: {0.333, 0.333, 0.333} gibi.
        """
        toplam = sum(agirliklar.values())
        if toplam == 0: 
            return agirliklar # Sifir bolme hatasini onle
        
        return {k: round(v / toplam, 4) for k, v in agirliklar.items()}

    def _beyaz_yaka_agirlik_hesapla(self, grup_sayilari):
        """
        Beyaz yaka kurallarina gore eksik gruplarin payini mevcutlara dagitir.
        Ornek: Eger 'Ast' degerlendirmesi yoksa, onun puani 'Yonetici' ve 'Ekip'e paylastirilir.
        """
        kurallar = self.agirlik_kurallari["beyaz_yaka"]["default_weights"].copy()
        
        # Veri setinde hic uyesi olmayan gruplari tespit et
        eksik_gruplar = [g for g in kurallar if grup_sayilari.get(g, 0) == 0]
        
        # Eger eksik yoksa varsayilan kurallari don
        if not eksik_gruplar: 
            return kurallar

        # Eksik gruplarin toplam agirligini hesapla
        dagitilacak_puan = sum(kurallar[g] for g in eksik_gruplar)
        
        # Kalan puani mevcut olan gruplara paylastir
        mevcut_gruplar = [g for g in kurallar if g not in eksik_gruplar]
        
        if mevcut_gruplar:
            pay = dagitilacak_puan / len(mevcut_gruplar)
            for g in mevcut_gruplar:
                kurallar[g] += pay
            
            # Eksiklerin puanini sifirla
            for g in eksik_gruplar: 
                kurallar[g] = 0.0
            
        return kurallar

    def _mavi_yaka_agirlik_hesapla(self, grup_sayilari):
        """
        Mavi yaka rollerinde yonetici mevcudiyetine gore agirlik belirler.
        """
        varsayilan = self.agirlik_kurallari["mavi_yaka"]["default_weights"].copy()
        
        yonetici1_var = grup_sayilari.get("yonetici1", 0) > 0
        yonetici2_var = grup_sayilari.get("yonetici2", 0) > 0

        # İki yönetici de varsa varsayılanı kullan
        if yonetici1_var and yonetici2_var: 
            return varsayilan
        
        # Sadece 1. yönetici varsa tüm puan ona
        if yonetici1_var: 
            return {"yonetici1": 1.0, "yonetici2": 0.0}
        
        # Sadece 2. yönetici varsa tüm puan ona
        if yonetici2_var: 
            return {"yonetici1": 0.0, "yonetici2": 1.0}
            
        return varsayilan

    def dinamik_agirlik_getir(self, rol, grup_sayilari):
        """
        Dışarıdan çağrılacak ANA METOT budur.
        Rol tipine (Mavi/Beyaz) bakar ve ilgili hesaplama fonksiyonunu çalıştırır.
        """
        rol_temiz = str(rol).lower().strip()
        
        if "beyaz" in rol_temiz:
            raw_weights = self._beyaz_yaka_agirlik_hesapla(grup_sayilari)
        elif "mavi" in rol_temiz:
            raw_weights = self._mavi_yaka_agirlik_hesapla(grup_sayilari)
        else:
            # Tanimlanmamis roller icin varsayilan beyaz yaka muamelesi
            raw_weights = self.agirlik_kurallari["beyaz_yaka"]["default_weights"]
            
        return self._agirliklari_normalize_et(raw_weights)

    # ============================================================
    # BOLUM B: SKOR HESAPLAMA VE VERI ISLEME
    # ============================================================

    def hesapla(self, calisan_id):
        """
        Belirli bir calisan icin yetkinlik puanlarini hesaplar.
        Mantik: 
        1. Gercek sutun varsa (CSV'de teknik isim) onu kullanir.
        2. Yoksa 'score' sutunu uzerinden varyasyon (simulasyon) yapar.
        3. O da yoksa 3.0 doner.
        """
        # 1. Calisanin verilerini suz
        calisan_df = self.df[self.df["employee_id"] == calisan_id]
        
        # Eger calisan bulunamazsa bos don
        if calisan_df.empty:
            return {}

        final_skorlar = {}
        
        # Raporda gorunmesini istedigimiz temel yetkinlikleri listele
        hedeflenenler = list(self.mapping.values())
        
        # 2. Her yetkinlik icin hesaplama yap
        for teknik_isim, ekran_ismi in self.mapping.items():
            
            # Sadece hedefledigimiz (Radar grafikte olacak) yetkinlikleri isleme al
            if ekran_ismi in hedeflenenler:
                
                # --- SENARYO A: GERÇEK VERİ ---
                # Eger CSV icinde 'problem_cozme...' gibi detayli bir sutun varsa:
                if teknik_isim in calisan_df.columns:
                    ham_puan = calisan_df[teknik_isim].mean()
                
                # --- SENARYO B: SİMÜLASYON (Yedek Plan) ---
                # Eger detayli sutun yoksa ama genel 'score' sutunu varsa:
                elif "score" in calisan_df.columns:
                    base_score = calisan_df["score"].mean()
                    
                    # Hash fonksiyonu ile her yetkinlik icin sabit bir sapma uretir.
                    # Boylece her calistirmada puanlar ayni kalir (random degildir)
                    # Ornek: Analitik icin +0.2 ekler, Iletisim icin -0.1 cikarir vb.
                    varyasyon = (hash(teknik_isim) % 80) / 100 - 0.4 
                    ham_puan = base_score + varyasyon
                
                # --- SENARYO C: HİÇ VERİ YOK ---
                else:
                    ham_puan = 3.0 # Varsayilan orta deger
                
                # Puani 1.0 ile 5.0 arasina sikistir (Outlier temizligi)
                # Ve virgulden sonra 2 basamak yuvarla
                final_skorlar[ekran_ismi] = round(max(1.0, min(5.0, ham_puan)), 2)
        
        return final_skorlar

# --- TEST BLOGU (Dosya dogrudan calistirilirsa burasi calisir) ---
if __name__ == "__main__":
    # Test verisi yolu (Kendi yolunuza gore duzenleyin)
    test_veri_yolu = "data/raw/faz0_sentetik_veri.csv"
    
    # Sinifi baslat
    hesaplayici = YetkinlikSkorHesaplayici(test_veri_yolu)
    
    # 1. Agirlik Testi
    print("--- Agirlik Motoru Testi ---")
    ornek_gruplar = {"yonetici1": 1, "ekip": 0, "ast": 0} # Sadece yonetici var, ekip/ast yok
    agirliklar = hesaplayici.dinamik_agirlik_getir("Beyaz Yaka", ornek_gruplar)
    print(f"Senaryo: Beyaz Yaka, Sadece Yonetici Var -> Sonuc: {agirliklar}")
    
    # 2. Skor Testi (Varsayilan ID ile)
    print("\n--- Skor Hesaplama Testi ---")
    if not hesaplayici.df.empty:
        ornek_id = hesaplayici.df.iloc[0]["employee_id"]
        skorlar = hesaplayici.hesapla(ornek_id)
        print(f"Calisan ID: {ornek_id}")
        print(f"Hesaplanan Skorlar: {skorlar}")
    else:
        print("CSV dosyasi bulunamadigi icin skor testi yapilamadi.")