import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
import os
import base64
import mimetypes

# --- BACKEND MODÜL ENTEGRASYONU ---
# Not: Bu dosyaların (src/ klasörü altında) mevcut olduğundan emin olun.
from src.yetkinlik_skor_hesaplayici import YetkinlikSkorHesaplayici
from src.tavsiye_motoru import TavsiyeMotoru
from src.etkinlik_kaziyici import EtkinlikKaziyici

# 1. SAYFA VE TASARIM AYARLARI
st.set_page_config(
    page_title="TUSAŞ LiftUp | 360 Analiz", 
    layout="wide", 
    page_icon="📊", 
    initial_sidebar_state="expanded"
)

# --- KURUMSAL VE CİDDİ CSS (PROFESYONEL UI) ---
st.markdown("""
    <style>
    /* Genel Ayarlar */
    .main { background-color: #F8F9FA; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    
    /* Header (Üst Bant) */
    .report-header { 
        background-color: #1A237E; padding: 35px; border-radius: 6px; color: white; 
        margin-bottom: 30px; border-bottom: 4px solid #b71c1c; box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .report-title { font-size: 28px; font-weight: 700; margin: 0; letter-spacing: 0.5px; }
    .report-subtitle { font-size: 16px; opacity: 0.95; margin-top: 8px; font-weight: 400; }
    
    /* Bölüm Başlıkları */
    .section-header { 
        color: #1A237E; font-size: 20px; font-weight: 700; margin-top: 45px; margin-bottom: 25px;
        padding-bottom: 10px; border-bottom: 1px solid #E0E0E0; display: flex; align-items: center;
    }
    .section-header::before {
        content: ""; display: inline-block; width: 6px; height: 24px;
        background-color: #1A237E; margin-right: 12px; border-radius: 2px;
    }

    /* KPI Kutuları */
    .fark-box { 
        background: white; border-radius: 8px; padding: 25px 15px; 
        text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.06); border: 1px solid #EAEAEA;
    }
    .fark-label { font-size: 12px; font-weight: 700; color: #546E7A; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px; }
    .fark-val { font-size: 28px; font-weight: 800; color: #263238; }

    /* Kart Tasarımı */
    .rec-card {
        background-color: white; border-radius: 6px; padding: 20px; margin-bottom: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05); border: 1px solid #E0E0E0; border-top-width: 5px; 
        height: 100%; /* Kartları eşit boyda tutmaya çalışır */
        display: flex; flex-direction: column; justify-content: space-between;
    }
    .card-weak { border-top-color: #D32F2F; }   /* Kırmızı */
    .card-medium { border-top-color: #FF9800; } /* Turuncu */
    .card-strong { border-top-color: #2E7D32; } /* Yeşil */
    
    .status-badge { 
        font-size: 10px; padding: 4px 10px; border-radius: 12px; font-weight: 700; 
        text-transform: uppercase; letter-spacing: 0.5px; color: white;
    }
    .bg-weak { background-color: #D32F2F; }
    .bg-medium { background-color: #FF9800; }
    .bg-strong { background-color: #2E7D32; }
    
    .rec-body { font-size: 13px; color: #455A64; line-height: 1.6; margin-top: 12px; }

    /* Tablo Stili (DÜZELTİLDİ) */
    table.score-table { width: 100%; border-collapse: collapse; margin-top: 5px; background: white; }
    table.score-table td { padding: 12px 8px; border-bottom: 1px solid #f1f1f1; vertical-align: middle; }
    .score-label { font-size: 13px; font-weight: 600; color: #37474F; width: 40%; }
    .score-val { font-weight: 800; color: #1A237E; text-align: right; font-size: 14px; width: 10%; }
    .progress-container { width: 100%; background-color: #eceff1; border-radius: 4px; height: 8px; overflow: hidden; }
    .progress-fill { height: 100%; border-radius: 4px; transition: width 0.5s ease-in-out; }

    /* Kolon Başlıkları */
    .col-header {
        font-size: 14px; font-weight: 700; padding: 10px; 
        border-radius: 4px; text-align: center; margin-bottom: 15px; color: white; letter-spacing: 0.5px;
    }
    .header-weak { background-color: #C62828; }
    .header-medium { background-color: #EF6C00; }
    .header-strong { background-color: #2E7D32; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SİSTEMİ BAŞLAT ---
@st.cache_resource
def sistemi_baslat():
    kok_dizin = Path(__file__).parent
    veri_yolu = kok_dizin / "data" / "input" / "faz0_sentetik_veri.csv"
    json_yolu = kok_dizin / "lookup" / "tavsiye_kurallari.json"
    etkinlik_yolu = kok_dizin / "data" / "input" / "etkinlik_listesi.csv"
    
    hesaplayici = YetkinlikSkorHesaplayici(str(veri_yolu))
    tavsiye_motoru = TavsiyeMotoru(str(json_yolu))
    etkinlik_kaziyici = EtkinlikKaziyici(str(etkinlik_yolu))
    
    return hesaplayici, tavsiye_motoru, etkinlik_kaziyici, kok_dizin

try:
    hesaplayici, tavsiye_motoru, etkinlik_kaziyici, kok_dizin = sistemi_baslat()
except Exception as e:
    st.error(f"Sistem başlatılamadı: {e}")
    st.stop()

# --- 3. YAN PANEL (KULLANICI SEÇİMİ) ---
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/8/86/TUSA%C5%9E_logo.png", width=200)
st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ Parametreler")

if hesaplayici.df.empty:
    st.error("Veri bulunamadı.")
    st.stop()

calisan_listesi = sorted(hesaplayici.df["employee_name"].unique())
secilen_kisi = st.sidebar.selectbox("Çalışan Seçimi", calisan_listesi)

try:
    secilen_satir = hesaplayici.df[hesaplayici.df["employee_name"] == secilen_kisi].iloc[0]
    calisan_id = secilen_satir["employee_id"]
    unvan = secilen_satir["role"]
except IndexError:
    st.stop()

# Yaka Tipi Belirleme
def yaka_tipi_belirle(rol):
    beyaz_yaka_anahtarlar = ["muhendis", "yonetici", "uzman", "direktor", "mühendis", "analist", "lider"]
    if any(x in str(rol).lower() for x in beyaz_yaka_anahtarlar):
        return "beyaz"
    return "mavi"

yaka_tipi = yaka_tipi_belirle(unvan)
yaka_etiketi = f"{yaka_tipi.capitalize()} Yaka"

# Sidebar Bilgi Kutusu
st.sidebar.markdown(f"""
<div style="background-color:#F5F5F5; padding:12px; border-radius:5px; font-size:13px; border-left:4px solid #1A237E; color:#333; margin-top:20px;">
    <b>Sicil:</b> {calisan_id}<br>
    <b>Ünvan:</b> {unvan}<br>
    <b>Kategori:</b> {yaka_etiketi}
</div>
""", unsafe_allow_html=True)

# --- 4. HESAPLAMALAR VE FOTOĞRAF ---

# Fotoğraf Bulma Mantığı
def get_image_base64(path):
    try:
        mime_type, _ = mimetypes.guess_type(path)
        with open(path, "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode()
        return f"data:{mime_type};base64,{encoded}"
    except: return None

foto_klasoru = kok_dizin / "data" / "photos"
foto_yolu = None
id_str = str(calisan_id).strip()
id_numeric = str(int(calisan_id)) if id_str.isdigit() else id_str

arama_listesi = [id_str, id_numeric, id_str.zfill(3)]
uzantilar = [".png", ".jpg", ".jpeg"]

for isim in set(arama_listesi):
    for uzanti in uzantilar:
        dosya_yolu = foto_klasoru / f"{isim}{uzanti}"
        if dosya_yolu.exists():
            foto_yolu = dosya_yolu
            break
    if foto_yolu: break

# Skor Hesaplamaları
final_skorlar = hesaplayici.hesaplaAgirlikliYetkinlikSkorlari(calisan_id, yaka_tipi)
if not final_skorlar:
    st.warning("Yeterli veri yok.")
    st.stop()

toplu_veri = tavsiye_motoru.topluTavsiyeUret(final_skorlar)
kategoriler = {m["yetkinlik"]: m["seviye"] for m in toplu_veri}
tavsiyeler = {m["yetkinlik"]: m["tavsiye"] for m in toplu_veri}
etkinlik_onerileri = etkinlik_kaziyici.topluEtkinlikOner(final_skorlar)

# --- 5. EKRAN ÇIKTISI (DASHBOARD) ---

# Header (Başlık)
st.markdown(f"""
    <div class="report-header">
        <div class="report-title">BİREYSEL GERİBİLDİRİM RAPORU</div>
        <div class="report-subtitle">TUSAŞ Performans Değerlendirme Sistemi | <b>{yaka_etiketi} Personeli</b></div>
    </div>
    """, unsafe_allow_html=True)

# Künye Alanı (Fotoğraf ve İsim)
col_p1, col_p2 = st.columns([1, 6])

with col_p1:
    img_b64 = get_image_base64(foto_yolu) if foto_yolu else None
    if img_b64:
        st.markdown(f"""
        <div style="width:100px; height:100px; border-radius:50%; overflow:hidden; border:4px solid #C5CAE9; margin:auto; box-shadow: 0 4px 10px rgba(0,0,0,0.15);">
            <img src="{img_b64}" style="width:100%; height:100%; object-fit:cover;">
        </div>
        """, unsafe_allow_html=True)
    else:
        initials = "".join([name[0] for name in secilen_kisi.split()[:2]])
        st.markdown(f"""
        <div style='background-color:#E8EAF6; color:#1A237E; width:100px; height:100px; border-radius:50%; 
        display:flex; justify-content:center; align-items:center; font-size:36px; font-weight:bold; margin:auto; border:4px solid #C5CAE9;'>
        {initials}
        </div>
        """, unsafe_allow_html=True)

with col_p2:
    st.markdown(f"""
    <div style='padding-top:20px; padding-left:10px;'>
        <h2 style='margin:0; color:#263238; font-size:32px;'>{secilen_kisi}</h2>
        <span style='color:#546E7A; font-size:18px; font-weight:500;'>{unvan} &nbsp;|&nbsp; <b style="color:#1A237E">{yaka_etiketi}</b></span>
    </div>
    """, unsafe_allow_html=True)

# --- PERFORMANS ÖZETİ ---
st.markdown('<div class="section-header">Performans Özeti</div>', unsafe_allow_html=True)

kendi_skoru = sum(final_skorlar.values()) / len(final_skorlar)
genel_ortalama = hesaplayici.df["score"].mean() if "score" in hesaplayici.df.columns else 3.5
net_fark = kendi_skoru - genel_ortalama

c1, c2, c3 = st.columns(3)
with c1: st.markdown(f'<div class="fark-box"><div class="fark-label">Bireysel Skor</div><div class="fark-val">{kendi_skoru:.2f}</div></div>', unsafe_allow_html=True)
with c2: st.markdown(f'<div class="fark-box"><div class="fark-label">Şirket Ortalaması</div><div class="fark-val">{genel_ortalama:.2f}</div></div>', unsafe_allow_html=True)

renk = "#D32F2F" if net_fark < 0 else "#388E3C"
with c3: st.markdown(f'<div class="fark-box"><div class="fark-label">Net Fark</div><div class="fark-val" style="color:{renk}">{net_fark:+.2f}</div></div>', unsafe_allow_html=True)

# --- YENİ FARK ANALİZİ GÖRSELİ (OVERLAPPING BUBBLES) ---
fig_fark = go.Figure()

# Şirket Ortalaması (Turuncu Daire - Arkada)
fig_fark.add_trace(go.Scatter(
    x=[genel_ortalama], y=[1],
    mode='markers+text',
    name='Şirket Ort.',
    text=['G'], # Genel
    textposition='middle center',
    marker=dict(color='#FF9800', size=55, opacity=0.9, line=dict(color='white', width=1)),
    textfont=dict(color='white', size=16, weight='bold'),
    hoverinfo='text',
    hovertext=f"Şirket Ortalaması: {genel_ortalama:.2f}"
))

# Bireysel Skor (Lacivert Daire - Önde ve Şeffaf)
fig_fark.add_trace(go.Scatter(
    x=[kendi_skoru], y=[1],
    mode='markers+text',
    name='Bireysel',
    text=['B'], # Bireysel
    textposition='middle center',
    # Puan yüksekse daha büyük, düşükse daha küçük görünsün (opsiyonel görsel efekt)
    marker=dict(color='#1A237E', size=60, opacity=0.85, line=dict(color='white', width=2)),
    textfont=dict(color='white', size=18, weight='bold'),
    hoverinfo='text',
    hovertext=f"Bireysel Skor: {kendi_skoru:.2f}"
))

# Grafik Düzeni
fig_fark.update_layout(
    xaxis=dict(
        range=[0.5, 5.5], 
        showgrid=False, 
        zeroline=False, 
        showticklabels=True,
        tickvals=[1, 2, 3, 4, 5],
        ticktext=['1.0', '2.0', '3.0', '4.0', '5.0'],
        tickfont=dict(color='#90A4AE')
    ),
    yaxis=dict(visible=False), # Y eksenini gizle
    height=120, # Kompakt yükseklik
    margin=dict(t=10, b=30, l=20, r=20), 
    plot_bgcolor="rgba(0,0,0,0)",
    showlegend=False,
    shapes=[
        # Arka plan için ince bir skala çizgisi
        dict(type="line", x0=1, y0=1, x1=5, y1=1, line=dict(color="#E0E0E0", width=2, dash="dot"), layer="below")
    ]
)
st.plotly_chart(fig_fark, use_container_width=True)
st.caption("G: Genel Şirket Ortalaması | B: Bireysel Skor (Kesişim alanları farkı gösterir)")


# --- YETKİNLİK DETAYLARI ---
st.markdown('<div class="section-header">Yetkinlik Analizi</div>', unsafe_allow_html=True)

col_radar, col_table = st.columns([1, 1])

with col_radar:
    # Radar Grafik
    labels = list(final_skorlar.keys())
    values = list(final_skorlar.values())
    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=values + [values[0]], theta=labels + [labels[0]],
        fill='toself', name='Puan', 
        line=dict(color="#1A237E", width=3), fillcolor="rgba(26, 35, 126, 0.1)"
    ))
    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 5], tickfont=dict(size=10, color="#90A4AE")),
            angularaxis=dict(tickfont=dict(size=12, color="#37474F"))
        ),
        showlegend=False, height=420, margin=dict(t=20, b=20)
    )
    st.plotly_chart(fig_radar, use_container_width=True)

with col_table:
    # HTML Skor Tablosu (DÜZELTİLMİŞ - HTML GÖRÜNME HATASI YOK)
    st.markdown("**Detaylı Puan Tablosu**")
    sorted_scores = sorted(final_skorlar.items(), key=lambda x: x[1], reverse=True)
    
    rows_html = ""
    for k, v in sorted_scores:
        bar_width = int((v/5)*100)
        color = "#2E7D32" if v >= 3.5 else ("#FF9800" if v >= 3.0 else "#D32F2F")
        # HTML'i tek satırda, boşluksuz birleştiriyoruz (Compact HTML)
        rows_html += f"<tr><td class='score-label'>{k}</td><td style='width:50%;'><div class='progress-container'><div class='progress-fill' style='width:{bar_width}%; background-color:{color};'></div></div></td><td class='score-val'>{v}</td></tr>"

    full_table_html = f"""<table class="score-table">{rows_html}</table>"""
    st.markdown(full_table_html, unsafe_allow_html=True)

# --- STRATEJİK GELİŞİM PLANI ---
st.markdown('<div class="section-header">Stratejik Gelişim Planı</div>', unsafe_allow_html=True)

# Kategorileri Ayır
zayiflar = {k: v for k, v in tavsiyeler.items() if kategoriler[k] in ["weak", "zayif"]}
ortalar = {k: v for k, v in tavsiyeler.items() if kategoriler[k] in ["medium", "orta"]}
gucluler = {k: v for k, v in tavsiyeler.items() if kategoriler[k] in ["strong", "guclu"]}

col_weak, col_medium, col_strong = st.columns(3)

def kart_ciz(baslik, tavsiye, skor, tip):
    # Stil ve İçerik Belirleme
    if tip == "weak":
        css = "card-weak"; badge_bg = "bg-weak"; label = "GELİŞİM"
        body_content = f'<div class="rec-body">{tavsiye}</div>'
    elif tip == "medium":
        css = "card-medium"; badge_bg = "bg-medium"; label = "İYİLEŞTİRME"
        body_content = f'<div class="rec-body">{tavsiye}</div>'
    else: # Strong
        css = "card-strong"; badge_bg = "bg-strong"; label = "GÜÇLÜ"
        body_content = "" # Güçlü yönlerde metin gizli
    
    # Skor kutusu sağa yaslanmış bir "pill" şeklinde
    score_html = f"""
    <div style="margin-top:auto; display:flex; justify-content:flex-end;">
        <span style="background-color:#F5F5F5; padding:4px 8px; border-radius:4px; font-size:11px; font-weight:700; color:#546E7A;">
            Skor: {skor}
        </span>
    </div>
    """

    return f"""
    <div class="rec-card {css}">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <span style="font-weight:700; font-size:14px; color:#37474F;">{baslik}</span>
            <span class="status-badge {badge_bg}">{label}</span>
        </div>
        {body_content}
        {score_html}
    </div>
    """

# 1. Kolon: Öncelikli Gelişim
with col_weak:
    st.markdown('<div class="col-header header-weak">ÖNCELİKLİ GELİŞİM</div>', unsafe_allow_html=True)
    if zayiflar:
        for k, v in zayiflar.items():
            st.markdown(kart_ciz(k, v, final_skorlar[k], "weak"), unsafe_allow_html=True)
    else:
        st.success("Bu alanda madde yok.")

# 2. Kolon: İyileştirme Fırsatları
with col_medium:
    st.markdown('<div class="col-header header-medium">İYİLEŞTİRME FIRSATLARI</div>', unsafe_allow_html=True)
    if ortalar:
        for k, v in ortalar.items():
            st.markdown(kart_ciz(k, v, final_skorlar[k], "medium"), unsafe_allow_html=True)
    else:
        st.success("Bu alanda madde yok.")

# 3. Kolon: Güçlü Yönler (Metinsiz)
with col_strong:
    st.markdown('<div class="col-header header-strong">GÜÇLÜ YÖNLER</div>', unsafe_allow_html=True)
    if gucluler:
        for k, v in gucluler.items():
            st.markdown(kart_ciz(k, "", final_skorlar[k], "strong"), unsafe_allow_html=True)
    else:
        st.info("Bu alanda madde yok.")

# --- EĞİTİM ÖNERİLERİ (Sadece Zayıf/Orta - EMOJİSİZ) ---
filtrelenmis_egitimler = {k: v for k, v in etkinlik_onerileri.items() if kategoriler.get(k) != 'strong'}

if filtrelenmis_egitimler:
    st.markdown('<div class="section-header">Eğitim Kataloğu Önerileri</div>', unsafe_allow_html=True)
    for yetkinlik, egitimler in filtrelenmis_egitimler.items():
        with st.expander(f"{yetkinlik} - İlgili Eğitimler ({len(egitimler)})"):
            for e in egitimler:
                # Emojiler kaldırıldı, sadece metin
                st.markdown(f"""
                <div style='border-bottom:1px solid #f0f0f0; padding:12px 0; display:flex; justify-content:space-between; align-items:center;'>
                    <div>
                        <div style='font-weight:600; color:#333; font-size:14px;'>{e['ad']}</div>
                        <div style='font-size:12px; color:#777; margin-top:4px;'>Lokasyon: {e['lokasyon']}</div>
                    </div>
                    <a href="{e.get('link', '#')}" style="background:#1A237E; color:white; padding:6px 15px; border-radius:4px; text-decoration:none; font-size:12px; font-weight:600;">İncele</a>
                </div>
                """, unsafe_allow_html=True)