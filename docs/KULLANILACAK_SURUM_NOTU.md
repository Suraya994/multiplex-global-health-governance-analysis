# Kullanilacak Surum Notu

Bu hakem paketinde esas alinacak analiz ve sonuc kaynagi:

`00_CURRENT_SOURCE_DERGI_PAKETI`

Bu klasor, son dergi/replication paketinden temizlenerek olusturulmustur.

Bu surumun IV sonuclari makaledeki degerlerle uyumludur:

- Distance-weighted peer eigen: first-stage F = 5.38870; second-stage p = 0.6954933.
- Common-language peer eigen: first-stage F = 247.5837; second-stage p = 0.32766267.
- Historical-tie peer eigen: first-stage F = 278.86312; second-stage p = 0.269813.
- Contiguous-neighbor peer eigen: first-stage F = 724.79477; second-stage p = 0.63711699.

Not: Daha eski ara klasorlerde farkli zamanlarda uretilmis IV/model ciktilari bulunabilir. Hakeme gidecek metod-sonuc kontrolunde bu eski taslak ciktilar referans alinmamalidir.

Word dosyasindaki sayisal IV bulgulari bu surumle uyumludur. Ancak metod/formul aciklamasi dort fiili IV degiskenini acik sekilde yazmalidir:

- `l_iv_distance_weighted_peer_eigen`
- `l_iv_language_peer_eigen`
- `l_iv_historical_peer_eigen`
- `l_iv_contiguous_peer_eigen`

Tek bir genel `affinity_score` veya `Z_aff` anlatimi, mevcut kodun tahmin ettigi IV modellerini tam yansitmaz.
