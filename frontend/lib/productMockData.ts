import type { Product } from "./types";

export const TUDORS_TSHIRT: Product = {
  slug: "tudors-oversize-tisort",
  brand: "Tudors",
  title:
    "Unisex Oversize Geniş Kesim %100 Pamuk Basic Bisiklet Yaka Beyaz Tişört",
  category: [
    { label: "Ana Sayfa", href: "/" },
    { label: "Erkek Giyim", href: "#" },
    { label: "Üst Giyim", href: "#" },
    { label: "Tişört", href: "#" },
  ],
  rating: 4.7,
  reviewCount: 142,
  salesCount: "2.4k",
  price: 414.98,
  oldPrice: 549.0,
  discountPercent: 24,
  risk: {
    level: "low",
    percent: 12,
    levelLabel: "Düşük",
    reviewCount: 142,
    satisfaction: 88,
    bars: [
      { label: "Beden uyumu", value: 8, level: "low" },
      { label: "Kumaş çekme", value: 2, level: "low" },
      { label: "Renk farkı", value: 2, level: "low" },
    ],
  },
  colors: [
    { name: "Beyaz", hex: "#FAFAFA", border: "#E5E7EB" },
    { name: "Siyah", hex: "#0F172A", border: "#0F172A" },
    { name: "Lacivert", hex: "#1E3A8A", border: "#1E3A8A" },
  ],
  defaultColorIndex: 0,
  sizes: [
    { label: "XS", risk: "mid", available: true },
    { label: "S", risk: "low", available: true },
    { label: "M", risk: "mid", available: true },
    { label: "L", risk: "low", available: true },
    { label: "XL", risk: "low", available: true },
    { label: "2XL", risk: "mid", available: true },
    { label: "3XL", risk: "high", available: false },
  ],
  defaultSizeIndex: 3,
  adviceBySize: {
    0: {
      type: "high",
      parts: [
        { text: "182cm 80kg için " },
        { text: "XS beden küçük kalır.", bold: true },
        { text: " %62 iade riski — yorumların 9'unda “küçük geldi” geçiyor." },
      ],
    },
    1: {
      type: "high",
      parts: [
        { text: "182cm 80kg için " },
        { text: "S beden küçük kalır.", bold: true },
        { text: " %62 iade riski — yorumların 9'unda “küçük geldi” geçiyor." },
      ],
    },
    2: {
      type: "mid",
      parts: [
        { text: "182cm 80kg için " },
        { text: "M alırsan %18 iade riski", bold: true },
        { text: " — 24 yorumun 4'ünde “küçük kaldı” geçiyor." },
      ],
    },
    3: {
      type: "low",
      parts: [
        { text: "182cm 80kg için " },
        { text: "L beden tam oturur.", bold: true },
        { text: " Oversize kesimde rahat bir his — 38 müşteri aynı bedeni almış, %94 memnun kalmış." },
      ],
    },
    4: {
      type: "mid",
      parts: [
        { text: "L bedenle aynı vücut tipindeki kullanıcıların " },
        { text: "%21'i XL'i tercih ediyor", bold: true },
        { text: " — daha bol kesim için." },
      ],
    },
    5: {
      type: "mid",
      parts: [
        { text: "2XL bedenle çok bol bir kesim alırsın — " },
        { text: "%32 iade riski", bold: true },
        { text: " (genelde 'çok büyük geldi')." },
      ],
    },
  },
  gallery: [
    { bg: "ph-bg-1", label: "Ön · Düz Çekim" },
    { bg: "ph-bg-5", label: "Arka · Detay" },
    { bg: "ph-bg-8", label: "Yan · Stüdyo" },
    { bg: "ph-bg-9", label: "Model · Kombin" },
  ],
  summary:
    "Yazlık günlük kullanım için pamuklu, oversize, kolay kombinlenen beyaz basic tişört.",
  audience: ["Oversize sevenler", "170–195 cm boy", "Günlük rahat tarz", "Sıcak hava"],
  occasions: [
    "Üniversite kampüsü",
    "Hafta sonu kahvesi",
    "Plaj sonrası",
    "Ev içi rahatlık",
    "Spor sonrası",
  ],
  description: [
    "%100 ring spun pamuk kumaştan üretilmiş, gramajı 240 g/m². Bisiklet yaka, oversize kesim, geniş ve düşük omuz. Yaka çevresi ribana takviyeli, esnemez. Yıkamada minimum çekme için önceden büzdürülmüş kumaş.",
    "Erkek ve kadın kullanıma uygun unisex kalıp. Modelin üzerinde XL beden ve modelin ölçüleri: 1.88 m boy, 84 kg.",
  ],
  care: [
    { icon: "wash", text: "30°C'de hassas yıkama" },
    { icon: "iron", text: "Orta sıcaklıkta ütüleyin" },
    { icon: "shield", text: "Beyazlatıcı kullanmayın" },
    { icon: "truck", text: "Kuru temizleme önerilmez" },
    { icon: "check", text: "Tersten yıkayın, çamaşır makinesi uygundur" },
  ],
  specs: [
    ["Marka", "Tudors"],
    ["Materyal", "%100 Pamuk"],
    ["Kalıp", "Oversize / Unisex"],
    ["Yaka", "Bisiklet yaka, ribana takviyeli"],
    ["Kol Boyu", "Kısa kol"],
    ["Desen", "Düz, basic"],
    ["Gramaj", "240 g/m²"],
    ["Üretim", "Türkiye"],
    ["Yıkama Sıcaklığı", "30°C"],
    ["Menşei", "Türkiye"],
  ],
  reviews: [
    {
      name: "Mehmet K.",
      initials: "MK",
      heightWeight: "176cm 76kg",
      size: "M",
      rating: 5,
      date: "12 Mart 2026",
      text: "Oversize olarak aldım, kumaş kalitesi cidden iyi. Yıkamada çekmedi, rengini de korudu. Boyum 1.76, kilom 76 — M tam oturdu, oversize hissini de verdi. Yine alırım.",
      topics: [
        { label: "kumaş", sentiment: "pos" },
        { label: "fiyat-performans", sentiment: "pos" },
        { label: "beden uyumu", sentiment: "pos" },
      ],
      helpful: 24,
    },
    {
      name: "Ayşe T.",
      initials: "AT",
      heightWeight: "168cm 60kg",
      size: "S",
      rating: 4,
      date: "8 Mart 2026",
      text: "Eşim için aldım ama bana da geldi diye denedim, S bende oversize duruyor — eve ev kıyafeti oldu. Beyazı zamanla biraz sararabilir, ama bu fiyata gayet iyi.",
      topics: [
        { label: "oversize", sentiment: "pos" },
        { label: "beyaz", sentiment: "mid" },
      ],
      helpful: 18,
    },
    {
      name: "Burak Y.",
      initials: "BY",
      heightWeight: "182cm 92kg",
      size: "L",
      rating: 3,
      date: "1 Mart 2026",
      text: "L aldım, omuzlar biraz dar geldi. Belki XL daha iyi olurdu. Kumaş güzel ama dikiş bana göre özensiz. Fiyatı düşünürsek kabul edilebilir.",
      topics: [
        { label: "dikiş", sentiment: "neg" },
        { label: "omuz", sentiment: "neg" },
        { label: "kumaş", sentiment: "pos" },
      ],
      helpful: 9,
    },
  ],
  reviewCounts: { all: 142, positive: 118, negative: 14, matchedToMe: 38 },
  qa: [
    {
      question: "Kumaş ince mi, içi gösterir mi?",
      answer:
        "240 g/m² gramajla orta kalınlıkta. Beyaz olduğu için açık renkli iç kıyafet öneririz. İçi belli olmayacak şekilde dokuya sahiptir.",
      by: "Tudors Resmi · 5 Mart",
    },
    {
      question: "Yıkamada çekiyor mu?",
      answer:
        "Önceden büzdürülmüş kumaş kullanıyoruz. 30°C'de yıkamada ölçüleri korur. 40°C üstünde hafif çekme olabilir.",
      by: "Tudors Resmi · 3 Mart",
    },
    {
      question: "180cm 78kg için hangi beden uygun?",
      answer:
        "Oversize kalıp olduğundan boy/kilonuza göre L beden tam oturur. Daha bol kullanım için XL'i deneyebilirsiniz.",
      by: "Tudors Resmi · 28 Şubat",
    },
  ],
  qaMeta: { total: 28, avgResponse: "ortalama 4 saatte yanıtlanıyor" },
  similar: [
    {
      brand: "Mavi",
      name: "Comfort Fit Bisiklet Yaka Beyaz Basic Tişört",
      price: "349,00",
      rating: "4.5",
      bg: "ph-bg-5",
      href: "#",
    },
    {
      brand: "Defacto",
      name: "Regular Fit Pamuklu Basic Beyaz Tişört",
      price: "199,99",
      rating: "4.2",
      bg: "ph-bg-3",
      href: "#",
    },
    {
      brand: "Koton",
      name: "Oversize Geniş Kesim Bisiklet Yaka Pamuk Tişört",
      price: "299,99",
      rating: "4.4",
      bg: "ph-bg-8",
      href: "#",
    },
    {
      brand: "US Polo",
      name: "Premium %100 Pamuk Slim Fit Beyaz Tişört",
      price: "649,00",
      rating: "4.6",
      bg: "ph-bg-1",
      href: "#",
    },
  ],
};

export function getProductBySlug(slug: string): Product | null {
  if (slug === TUDORS_TSHIRT.slug) return TUDORS_TSHIRT;
  return null;
}
