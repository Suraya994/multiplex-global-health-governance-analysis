# WDI 100 Country Data Audit Report

Denetim tarihi: 2026-05-03

## Sonuc

Ham WDI veri paketi yapisal olarak hazir: 100 ulke, 2004-2024 dengeli panel, 2100 wide satir ve 21000 long satir dogrulandi.

## Dosyalar ve SHA-256

- `analysis_panel_100countries_2004_2024.csv` | 326707 bytes | `1cc14d6162d2a44964dddf09ddb810985fe223b597670cbafb4fe4fd7f6b3abd`
- `wdi_panel_100countries_2004_2024_long.csv` | 1976222 bytes | `20a9e4ccea4dd3ef559a687961acaed2db32b679d6d5e62d125b4ee124c415ca`
- `missingness_check_100countries.csv` | 470 bytes | `e71ddf90a4026e3d8c519e8398b572afeaff0a3f28610abdca9cd42933fa1bdf`
- `missingness_check_100countries_by_country.csv` | 7920 bytes | `9070559a35225323574ee8f90f43aff94f41eaf75dfbcb9ed00d482792b55293`
- `global_health_100_country_template.csv` | 5186 bytes | `f2016c5f435d564d99a56adf1e09a190ddcdbbb9a45c148f419f968caeb5b990`
- `run_wdi_100_country_panel.R` | 6035 bytes | `ac768b508297b99b3246bf908a3c4afcfe579aee4bd1ff75af2e9cbb20608aad`

## Yapisal Kontroller

| Kontrol | Bulunan | Beklenen | Durum |
|---|---:|---:|---|
| Wide panel satiri | 2100 | 2100 | OK |
| Long panel satiri | 21000 | 21000 | OK |
| Ulke sayisi | 100 | 100 | OK |
| Yil araligi | 2004-2024 | 2004-2024 | OK |
| Wide tekrar kayit | 0 | 0 | OK |
| Long tekrar kayit | 0 | 0 | OK |
| Eksik ulke-yil paneli | 0 | 0 | OK |

## Degisken Eksiklik Karari

| Indicator | Aciklama | Eksik oran | Karar |
|---|---|---:|---|
| `SE.ADT.LITR.ZS` | Adult literacy rate | 0.745 | Ana modelden cikar; veri eksigi cok yuksek |
| `GB.XPD.RSDV.GD.ZS` | R&D expenditure (% of GDP) | 0.337 | Ek analiz veya robustness icin uygun |
| `SH.MED.PHYS.ZS` | Physicians per 1,000 people | 0.271 | Ana analizde dikkatli / imputasyon veya saglamlik kontrolu |
| `SH.MED.NUMW.P3` | Nurses and midwives per 1,000 people | 0.265 | Ana analizde dikkatli / imputasyon veya saglamlik kontrolu |
| `SH.MED.BEDS.ZS` | Hospital beds per 1,000 people | 0.230 | Ana analizde dikkatli / imputasyon veya saglamlik kontrolu |
| `SH.XPD.CHEX.GD.ZS` | Current health expenditure (% of GDP) | 0.040 | Ana analiz icin guclu |
| `IT.NET.USER.ZS` | Individuals using the Internet (%) | 0.007 | Ana analiz icin guclu |
| `NY.GDP.PCAP.PP.KD` | GDP per capita, PPP (constant international $) | 0.000 | Ana analiz icin guclu |
| `SP.DYN.LE00.IN` | Life expectancy at birth | 0.000 | Ana analiz icin guclu |
| `SP.POP.TOTL` | Population, total | 0.000 | Ana analiz icin guclu |

## Degisken Aralik Kontrolu

| Indicator | N | Min | Max |
|---|---:|---:|---:|
| `SH.XPD.CHEX.GD.ZS` | 2016 | 1.327 | 18.52 |
| `SH.MED.PHYS.ZS` | 1531 | 0.0129 | 7.51 |
| `SH.MED.NUMW.P3` | 1543 | 0.138 | 18.76 |
| `SH.MED.BEDS.ZS` | 1616 | 0.2 | 14.18 |
| `SP.DYN.LE00.IN` | 2100 | 46.04 | 84.58 |
| `NY.GDP.PCAP.PP.KD` | 2100 | 877.1 | 1.456e+05 |
| `SP.POP.TOTL` | 2100 | 2.921e+05 | 1.451e+09 |
| `SE.ADT.LITR.ZS` | 535 | 35.9 | 100 |
| `IT.NET.USER.ZS` | 2086 | 0.02434 | 100 |
| `GB.XPD.RSDV.GD.ZS` | 1392 | 0.00549 | 6.346 |

## Dergi Icin Saklama Notu

Bu paket analiz oncesi ham WDI veri paketi olarak saklanmistir. Ana modele okuryazarlik degiskeni yuksek eksiklik nedeniyle alinmamalidir. R&D degiskeni ek/robustness analizine ayrilmalidir. Saglik isgucu ve yatak degiskenleri imputasyon ya da dengeli alt-panel kontroluyle kullanilmalidir.
