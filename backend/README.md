# Backend

FastAPI tabanlı orkestratör + AI katmanları. Ana sayfaya geri dönmek için → [`../README.md`](../README.md).

## Servis topolojisi

| Servis | Port | Açıklama |
| --- | --- | --- |
| `uvicorn` | 8765 | FastAPI ana servis, REST + SSE |
| `postgres` | 5432 | Yorumlar, soru-cevaplar, BERT etiketleri |
| `chroma`  | 8001 | ChromaDB HTTP modu (3 koleksiyon) |
| `chroma-admin` | 3500 | Vektör veritabanını tarayıcıdan görmek için |

PostgreSQL ve Chroma `docker-compose` üzerinden başlatılır:

```bash
docker-compose up -d postgres chroma chroma-admin
```

## Proje yapısı

```
backend/
├── app/
│   ├── main.py            FastAPI lifespan — modelleri eager-load eder
│   ├── config.py          Pydantic Settings (.env'den)
│   ├── errors.py          Türkçe hata sözlüğü (KankaError)
│   ├── schemas.py         Frontend tipleriyle birebir eşleşen Pydantic modelleri
│   ├── db.py              asyncpg + SQLAlchemy 2.0 havuzu
│   ├── ai/
│   │   ├── berturk.py     ConvBERTurk multi-task inference
│   │   ├── retrieval.py   BGE-M3 + ChromaDB sarmalayıcısı
│   │   ├── gemini.py      Orkestratör + fallback chain
│   │   ├── tools.py       11 function declaration + sistem prompt'ları
│   │   └── vllm_client.py Etiketleme aşaması için OpenAI uyumlu istemci
│   └── routes/
│       ├── products.py    /products, /size-advice, /risk-analysis, /similar
│       ├── reviews.py     /reviews (sentiment + fit filtreli)
│       ├── qa.py          /qa (ürün başına müşteri soru-cevapları)
│       ├── cart.py        /cart/coupon, /cart/combo-suggestions
│       ├── chat.py        /chat/stream, /chat/combo-stream (SSE)
│       ├── categories.py  /categories
│       ├── seller.py      /seller/{id}/quality
│       └── compare.py     /compare
└── scripts/
    ├── etl_normalize.py       Ham JSON → parquet + products.json
    ├── build_dataset.py       HF warm-start veri setini hazırlar
    ├── llm_label_qwen.py      Yerel Qwen3 ile zayıf etiketleme
    ├── train_berturk.py       İki fazlı fine-tune
    ├── infer_berturk.py       Tüm yorumlara batch inference
    ├── aggregate_features.py  Ürün başına risk / size / trend agregasyonu
    ├── ingest_chroma.py       Vektör veritabanı beslemesi
    └── ingest_postgres.py     İlişkisel veritabanı beslemesi
```

## AI mimarisi nasıl çalışıyor

### 1. Yorum sınıflandırma (ConvBERTurk)

`dbmdz/convbert-base-turkish-cased` üzerine üç başlık eklenmiş multi-task bir model:

- **Sentiment** (3 sınıf): positive · neutral · negative
- **Fit** (4 sınıf): tam · küçük · büyük · belirsiz
- **Risk** (5 etiket, multi-label): kumaş · renk · kalite · kargo · koku

Eğitim iki fazda yapıldı.

**Faz 1 — sentiment warm-start.** Hugging Face'teki `fthbrmnby/turkish_product_reviews` veri seti binary etiketli (positive / negative) ve dengesiz (yaklaşık 9 pozitife 1 negatif). Negatifleri tümüyle alıp pozitiflerden 30K downsample edip yaklaşık 45K dengeli alt küme oluşturduk. 2 epoch boyunca yalnızca sentiment başlığı (encoder'ın son iki katmanı + classifier) eğitildi.

**Faz 2 — joint training.** Stratified örnekleme ile (kategori orantılı, uzun metin tercihli, beden bilgisi içeren yorumlar ağırlıklı) 8.000 yorum seçtik. Yerel Qwen3 modeli (vLLM üzerinde OpenAI uyumlu API ile) bunlara JSON formatında etiket üretti. Prompt şablonu için bkz. [`../examples/qwen_label_prompt.json`](../examples/qwen_label_prompt.json). Bu zayıf etiketli set üstüne 300 örnekten oluşan altın doğrulama setini ekledik. Tüm encoder + üç başlık 3 epoch, batch=32, lr=2e-5, max_seq=128 ayarlarıyla birlikte eğitildi. Kayıp fonksiyonu: `α·CE(sent) + β·CE(fit) + γ·BCE(risk)` (α=β=1, γ=0.8).

Eğitim sonrası tüm yorum kümesinde batched inference çalıştırılıyor (CPU'da batch=64, ~50ms/batch). Çıktı parquet formatı için bkz. [`../examples/bert_labels.jsonl`](../examples/bert_labels.jsonl).

### 2. Semantic retrieval (BGE-M3 + ChromaDB)

`BAAI/bge-m3` Türkçe için güçlü, 1024 boyutlu bir multilingual encoder. ChromaDB 1.5 üzerinde üç koleksiyon tutuyoruz:

| Koleksiyon | İçerik | Anahtar metadata |
| --- | --- | --- |
| `reviews_collection` | Ürün başına bilgilendirici 200 yorum | `urun_slug`, `beden`, `boy_bin`, `kilo_bin`, `sent_label`, `fit_label`, `risk_top` |
| `products_collection` | Ürün özetleri (başlık + breadcrumb + spec) | `slug`, `marka`, `kategori_son`, `cinsiyet`, `fiyat`, `rating`, `risk_level` |
| `qa_collection`      | Müşteri soru-cevapları | `urun_slug`, `satici`, `soru_tarihi` |

Çıktı tarayıcıdan görmek için `docker-compose up -d chroma-admin` sonrası http://localhost:3500 → Connection alanına `http://chroma:8000` yaz.

### 3. Gemini orkestratör

`app/ai/gemini.py` doğrudan cevap üretmiyor. Sadece tool çağırıyor ve tool çıktılarını sentezliyor.

**Fallback chain.** Free tier kotaları her modelde ayrı tutulur. 429 RESOURCE_EXHAUSTED yiyen modeli `_MODEL_COOLDOWN_UNTIL` sözlüğüne kaydedip sıradakine geçer:

```
gemini-3.1-flash-lite -> gemini-2.5-flash-lite -> gemini-flash-lite-latest
-> gemini-3-flash-preview -> gemini-2.0-flash-lite -> gemini-2.5-flash
```

**Function declarations.** Toplam 11 tool, `app/ai/tools.py` içinde:

| Tool | Ne yapar |
| --- | --- |
| `get_qa_answer_if_exists` | Mevcut Q&A veritabanında benzer soru var mı diye bakar |
| `search_reviews` | Belirli bir konuda yorum semantik araması |
| `get_size_recommendation` | Boy/kilo profilinden beden önerisi |
| `get_return_risk` | İade riski + risk sinyallerinin dağılımı |
| `find_compatible_products` | Senaryoya uygun kombin parçaları |
| `search_products_by_intent` | Doğal dil sorgusuyla katalogdan ürün arar (multi-turn kombin için) |
| `get_alternative_product` | Kullanıcı kısıtına uygun alternatif |
| `get_seller_quality` | Çoklu satıcı varsa satıcı bazlı memnuniyet |
| `get_review_summary` | Belirli aspect (kumaş, renk vs.) için yorum özeti |
| `get_size_distribution` | Boy aralığına göre beden dağılımı |
| `compare_products` | İki ürünü risk + fiyat + özellikler açısından karşılaştır |
| `get_trending_for_category` | Kategorideki trend ürünler |

Sistem prompt'u her tool için ne zaman çağrılması gerektiğini netleştirir. Örneğin "bu üründe kumaş kalitesi nasıl?" sorusu mutlaka `search_reviews` çağırmaya yönlendirilir; modelin halüsinasyon üretmesi engellenir.

## API referansı (özet)

| Endpoint | Açıklama |
| --- | --- |
| `GET  /api/health` | Sağlık kontrolü |
| `GET  /api/categories` | Üst seviye kategoriler |
| `GET  /api/products/recommended?limit=12` | Önerilenler listesi |
| `GET  /api/products/{slug}` | Ürün detayı |
| `POST /api/products/{slug}/size-advice` | `{height, weight}` ile beden önerisi |
| `GET  /api/products/{slug}/reviews?filter=pos|neg|me|all` | Filtreli yorumlar |
| `GET  /api/products/{slug}/qa` | Soru-cevaplar |
| `GET  /api/products/{slug}/similar?limit=4` | Benzer ürünler |
| `GET  /api/products/{slug}/risk-analysis` | Risk + bar chart verisi |
| `POST /api/cart/coupon` | Kupon doğrulama |
| `GET  /api/cart/combo-suggestions?ids=...` | Sepet için kombin önerileri |
| `POST /api/chat/stream` | Gemini orkestratör SSE |
| `POST /api/chat/combo-stream` | "Kombinleri Bul" multi-turn SSE |

## Yerel veri pipeline

Repo veriyi içermiyor (boyut ve yasal nedenler). Kendi veri setinle eğitmek istersen:

```bash
# 0. Ham veriyi backend/app/data/raw/ altına JSON olarak koy.
#    Her JSON bir ürün objesi içermeli; format için examples/product.json'a bak.

python scripts/etl_normalize.py        # raw/ -> products.json + reviews.parquet + qa.parquet
python scripts/build_dataset.py        # HF warm-start veri setini indirir ve hazırlar
python scripts/llm_label_qwen.py       # 8K yorum için zayıf etiket üretir (vLLM gerekli)
python scripts/train_berturk.py        # İki fazlı fine-tune (CPU'da ~2 saat, GPU'da ~20 dk)
python scripts/infer_berturk.py        # Tüm yorumlara label çıkar
python scripts/aggregate_features.py   # risk.json / size_advice.json / trend.json
python scripts/ingest_chroma.py        # Vektör veritabanı beslemesi
python scripts/ingest_postgres.py      # İlişkisel veritabanı beslemesi
```

## Geliştirme notları

- Tüm endpointler async; veritabanı `asyncpg` üzerinden, vektör veritabanı ChromaDB'nin HTTP istemcisi üzerinden konuşur.
- BGE-M3 ve ConvBERTurk modelleri uygulama başlatılırken bir kere yüklenir (`lifespan`); ilk soğuk yüklenme yaklaşık 60 saniye sürer, sonrası ms düzeyinde.
- Hata mesajları kullanıcıya Türkçe gösterilir, `app/errors.py` üzerinden tek noktadan yönetilir.
- Test verisi yerine sentetik bir ürünle baş başa çalışmak istersen, `examples/product.json` içeriğini `backend/app/data/products.json` olarak kopyalayıp `[ örnek_objesi ]` şeklinde bir liste yap.
