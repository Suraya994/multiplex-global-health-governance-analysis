# DergiPark Oncesi Denetim: Multiplex Ag Analizi Makalesi

Denetlenen dosya: onceki bir makale PDF taslagi.

Sonuc: Bu PDF mevcut haliyle DergiPark'a yuklenmemeli. Makalede duzeltilebilir ama hakem onune gitmeden once mutlaka giderilmesi gereken hesaplama, metodoloji, kaynakca ve bicim sorunlari var.

## Kritik Hesaplama Hatalari

1. NLD formulu ile uygulanan hesap ters yazilmis.
   - Metinde once `NLD = 2E / N(N-1)` veriliyor.
   - 2021 orneginde `N=239`, `E=1844` deniyor.
   - Dogru hesap: `2*1844 / (239*238) = 3688 / 56882 = 0.0648`.
   - PDF'de ise denklem satirinda `239*(239-1) / (2*1844) = 56882/3688 ≈ 0.0648` yaziyor. Bu matematiksel olarak yanlis; `56882/3688 ≈ 15.42` eder. Sonuc sayisi dogru, denklem yolu yanlis.

2. 12 ulkeli ag ile 239 dugumlu ag ayni analiz gibi sunuluyor.
   - Makalenin ana evreni 12 ulke ve 2015-2023 donemi.
   - 2021 bolumunde birden BM uyesi devletler, WHO, PAHO, Global Fund, Gavi, sivil toplum ve bolgesel komitelerle `N=239` baska bir ag evrenine geciliyor.
   - Bu gecis, yontemi bozar; 12 ulkeli multiplex ag ile 239 aktorlu diplomasi agi ayri analizler olarak kurulmadikca ayni NLD anlatimina dahil edilmemeli.

3. Kenar tanimi isbirligi degil, fark olcumu olarak verilmis.
   - Metinde kenarlar ulkeler arasindaki saglik harcamasi ve istihdam farklari olarak tanimlaniyor.
   - Fark buyuklugu, isbirligi yogunlugu anlamina gelmez. Bu nedenle "baglanti yogunlugu arttikca isbirligi artar" yorumu metodolojik olarak zayif kaliyor.

4. NLD agirliklari dikkate almiyor.
   - NLD sadece kenar sayisini sayar; kenarin ne kadar guclu oldugunu olcmez.
   - Eger her ulke cifti arasina bir kenar cizildiyse 12 ulkeli tam agda yogunluk sabit olur. O zaman 2019 veya 2022'de "NLD artti" demek icin esikleme, kenar secim kurali veya agirlikli yogunluk tanimi gerekir.

5. Bulgular sayisal tabloyla desteklenmiyor.
   - "2019 ve 2022'de belirgin artis" deniyor ama PDF'de yil-yil NLD tablosu yok.
   - Hakem icin mutlaka `Yil, N, E, NLD, ortalama agirlik, merkezilik` gibi bir tablo eklenmeli.

## Metodoloji Hatalari

1. Veri kaynagi belirsiz ve izlenebilir degil.
   - Ozet WHO yillik raporlarini soyluyor; metodoloji WHO ve Dunya Bankasi diyor.
   - Hangi gostergeler, hangi kodlar, hangi veri indirme tarihi, hangi eksik veri kurali kullanildi yazilmamis.

2. Eksik veri islemi yetersiz aciklanmis.
   - "Istatistiksel yontemlerle tamamlanmis veya analizden cikarilmis" ifadesi hakem icin kabul edilemez kadar genel.
   - Hangi degiskenlerde kac eksik gozlem oldugu, hangi imputasyon yontemi kullanildigi ve duyarlilik kontrolu eklenmeli.

3. Metin analizi iddiasi bulgulara baglanmiyor.
   - NLTK/spaCy, anahtar kelime sikligi ve tema analizi anlatiliyor.
   - Ancak metin analizi sonuclari tablo, sekil veya kodlama semasi olarak sunulmuyor. Ya cikarilmali ya da bulgu tablosu eklenmeli.

4. BM'nin normatif liderligini ulke saglik harcamasi/istihdamiyla olcmek kuramsal olarak zayif kurulmus.
   - Saglik harcamasi ve istihdam ulusal kapasite gostergesidir; BM normatif liderliginin dogrudan gostergesi degildir.
   - Bu bag icin ara mekanizma kurulmasi gerekir: BM/WHO kararlarina katilim, ortak karar sponsorlugu, fon/teknik yardim, ortak program, norm benimseme veya diplomatik ag verisi gibi.

5. "Multiplex" kavrami iki katmanli gorsellestirmeye indirgenmis.
   - Multiplex ag analizi icin katmanlarin ayri tanimi, katmanlar arasi bag, dugum ayniligi, katman yogunlugu ve katmanlar arasi korelasyon verilmelidir.

## Dil ve Bicim Sorunlari

1. PDF'de ciddi dizgi/metin bozulmalari var.
   - Metin cikarmada "multkplexlkk", "normatkf", "Bkrleşmkş", "statkstkcs", "dok" gibi bozulmalar gorunuyor.
   - Sayfa goruntulerinde ana metnin bir kismi duzgun olsa da kaynakcada ve bazi basliklarda bozulma PDF uzerinde de izleniyor. DergiPark yuklemesi icin temiz Word/PDF yeniden uretilmeli.

2. Noktalama mekanik ve sikisik.
   - Ornek sorunlar: `ele alınabilir.(Buzan, 1993a)`, `odak noktalarıdır.Bu bağlamda`, `göstermektedir.2019`.
   - Atiflardan once bosluk olmali; cumleler dogal bolunmeli.

3. Ozet ve Abstract uyumsuz.
   - Turkce ozette 12 ulke listesi dogru.
   - Abstract'ta "sample of organisations from 12 countries" deniyor ve Brazil/Indonesia tekrarlaniyor.
   - Keywords'te "Multilateralism" iki kez geciyor, "multiplexity" yok.

4. ORCID yazimi hatali.
   - `ORCİD İD` yerine `ORCID ID` veya sadece `ORCID:` kullanilmali.

5. Tablo ve sekil basliklari bozuk.
   - `Tablo1`, `Şek+l`, `Mult+plex` gibi bicimler temizlenmeli.
   - Tum tablo ve sekillerde standart bicim: `Tablo 1. ...`, `Sekil 1. ...`

## Kaynakca Sorunlari

1. Kaynak sayisi makalenin iddiasi icin dusuk ve dengesiz.
   - Yaklasik 27 kaynak var; fakat ag analizi, multiplex network metodolojisi, global health governance ve WHO/BM normatif liderlik literaturu icin yetersiz.

2. Kaynakca bozulmus.
   - `American` yerine `Amer#can`, `International` yerine `Internat#onal`, `doi` yerine `dok`, URL'lerde `who.knt` gibi hatalar var.
   - Bu haliyle kaynakca otomatik intihal/metadata taramalarinda da sorun cikarabilir.

3. Zayif kaynak kullanimi var.
   - ResearchGate ve Academia linkleri yerine kitap/yayinevi/dergi DOI veya resmi kaynak kullanilmali.
   - Keohane, Hurrell, Nye gibi temel kaynaklar birincil basim bilgileriyle verilmeli.

4. Metinde olup kaynakcada eksik gorunen atiflar var.
   - Cox 1986, Nye 2004, Fukuda-Parr ve Muchhala 2020, Chasek ve Wagner 2016 metinde geciyor; kaynakca kayitlari tam ve tutarli degil.

## Oncelikli Duzeltme Plani

1. Kaynak Word dosyasindan temiz PDF yeniden uretilmeli.
2. Metodoloji tek veri evrenine indirilmeli: ya 12 ulke/2015-2023 analizi ya da 30 ulke/2010-2024 yeni analiz.
3. NLD formulu ve tum yil hesaplari yeniden tablo halinde verilmeli.
4. Kenar tanimi yeniden kurulmalı: benzerlik mi, esiklenmis isbirligi mi, ortak kurumsal katilim mi?
5. Metin analizi ya cikarilmali ya da ayri bulgu tablosuyla kanitlanmali.
6. Kaynakca Zotero/Word ile bastan temizlenmeli; DOI ve resmi URL'ler duzeltilmeli.
7. Ozet, Abstract ve anahtar kelimeler yeniden yazilmali.
8. DergiPark yuklemesinden once intihal, kaynakca ve sekil/tablo numarasi son kontrolu yapilmali.
