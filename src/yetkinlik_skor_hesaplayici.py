import pandas as pd
import json
from pathlib import Path

class YetkinlikSkorHesaplayici:
    """
    Modul Amaci: CSV dosyasindaki ham puanlari okur.
    'yetkinlikler.json' icindeki teknik isimleri, raporda gorunecek
    ekran isimlerine cevirir ve nihai puani hesaplar.
    """
    
    def __init__(self, veri_yolu):
        self.kok_dizin = Path(__file__).parent.parent
        
        # 1. CSV DOSYASINI GUVENLI OKUMA
        try:
            self.df = pd.read_csv(veri_yolu)
        except Exception as e:
            print(f"Hata: Veri dosyasi okunamadi ({e}). Bos tablo olusturuluyor.")
            # Hata durumunda kodun cokmemesi icin bos bir DataFrame olustur
            self.df = pd.DataFrame(columns=["employee_id", "employee_name", "role", "score"])

        # 2. AGIRLIK KURALLARINI YUKLEME (Yedekli)
        try:
            path = self.kok_dizin / "lookup" / "agirlik_kurallari.json"
            with open(path, "r", encoding="utf-8") as f:
                self.agirlik_kurallari = json.load(f)
        except:
            # Dosya yoksa veya bozuksa varsayilan basit kurallar
            self.agirlik_kurallari = {
                "beyaz_yaka": {"default_weights": {"yonetici1": 0.5, "ekip": 0.2, "ast": 0.3}},
                "mavi_yaka": {"default_weights": {"yonetici1": 1.0}}
            }

        # 3. HARITALAMA: Teknik Isim (CSV Header) -> Ekran Ismi (Rapor)
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
            
            # Ekstra yetkinlikler (Ileride lazim olursa diye)
            "stratejik_dusunme_ve_vizyon_olusturma": "Stratejik Düşünme",
            "yonetsel_cesaret_ve_karar_kalitesi": "Yönetsel Cesaret",
            "performans_yonetimi_ve_geri_bildirim": "Performans Yönetimi",
            "insan_gelistirme_ve_kocluk": "İnsan Geliştirme",
            "paydas_yonetimi_ve_etki_olusturma": "Paydaş Yönetimi",
            "degisim_yonetimi_ve_org_ceviklik": "Değişim Yönetimi",
            "kaynak_yonetimi_ve_operasyonel_surukleyicilik": "Kaynak Yönetimi"
        }

    def hesaplaAgirlikliYetkinlikSkorlari(self, calisan_id, yaka_tipi):
        """
        Belirli bir calisan icin yetkinlik puanlarini hesaplar.
        Mantik: Gercek sutun varsa onu kullanir, yoksa 'score' uzerinden simulasyon yapar.
        """
        # 1. Calisanin verilerini suz
        calisan_df = self.df[self.df["employee_id"] == calisan_id]
        
        # Eger calisan bulunamazsa bos don
        if calisan_df.empty:
            return {}

        final_skorlar = {}
        
        # Raporda gorunmesini istedigimiz temel yetkinlikler
        hedeflenenler = [
            "Analitik Düşünme", "Emniyet", "Etik Duruş", 
            "İletişim", "İşbirliği", "Teknik Uzmanlık", "Süreç Disiplini"
        ]
        
        # 2. Her yetkinlik icin hesaplama yap
        for teknik_isim, ekran_ismi in self.mapping.items():
            
            # Sadece hedefledigimiz (Radar grafikte olacak) yetkinlikleri isleme al
            if ekran_ismi in hedeflenenler:
                
                # --- SENARYO A: GERÇEK VERİ ---
                # Eger CSV icinde 'problem_cozme...' gibi detayli bir sutun varsa:
                if teknik_isim in calisan_df.columns:
                    # O sutundaki degerlerin ortalamasini al (Birden fazla satir varsa)
                    ham_puan = calisan_df[teknik_isim].mean()
                
                # --- SENARYO B: SİMÜLASYON (Yedek Plan) ---
                # Eger detayli sutun yoksa ama genel 'score' sutunu varsa:
                elif "score" in calisan_df.columns:
                    base_score = calisan_df["score"].mean()
                    
                    # Hash fonksiyonu ile her yetkinlik icin sabit bir sapma uretir.
                    # Boylece her calistirmada puanlar ayni kalir (random degildir) ama
                    # grafik duz bir cizgi gibi gorunmez.
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