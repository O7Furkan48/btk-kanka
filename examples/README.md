# Veri Formatları

Bu klasör, sistemin kullandığı veri yapısını sentetik bir kıyafet örneği üzerinden gösterir. Gerçek üretim verisi `data-collection/raw/` ve `backend/app/data/` altındadır ve git'lenmemiştir.

| Dosya | Akış |
| --- | --- |
| `product.json` | Frontend ürün detay sayfasının okuduğu şema |
| `reviews.jsonl` | ETL çıktısı yorum satırı (PostgreSQL + ChromaDB beslemesi) |
| `bert_labels.jsonl` | ConvBERTurk multi-task inference çıktısı |
| `qwen_label_prompt.json` | Eğitim için weak-supervision (Qwen3) prompt şablonu |
| `chroma_documents.json` | 3 vektör koleksiyonun doküman + metadata yapısı |

Tüm içerikler tamamen kurgusal olup gerçek bir marka, satıcı veya kullanıcıyla ilişkili değildir.
