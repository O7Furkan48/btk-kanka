from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict

RiskLevel = Literal["low", "mid", "high"]
SizeFit = Literal["fits", "small", "large", "unknown"]
Sentiment = Literal["pos", "mid", "neg"]
CategoryKey = Literal["dress", "shirt", "shoe", "bag", "home", "cosmetics", "tech", "sport", "baby"]
CareIcon = Literal["wash", "iron", "shield", "truck", "check"]

class Category(BaseModel):
    key: CategoryKey
    label: str

class ProductSummary(BaseModel):
    slug: str
    brand: str
    name: str
    bg: str
    imageUrl: str | None = None
    placeholder: str
    price: str
    risk: RiskLevel
    riskLabel: str
    rating: str

class HeroBubble(BaseModel):
    position: Literal[1, 2, 3]
    text: str

class CartNudge(BaseModel):
    type: Literal["size", "combo"]
    parts: list[dict]
    cta: dict

class CartItem(BaseModel):
    id: str
    brand: str
    name: str
    bg: str
    color: str
    colorClass: str
    size: str
    unitPrice: float
    quantity: int
    nudge: CartNudge | None = None

class ComboItem(BaseModel):
    id: str
    brand: str
    name: str
    bg: str
    price: float
    risk: RiskLevel
    riskLabel: str

class ComboGroup(BaseModel):
    sourceId: str
    sourceName: str
    sourceBg: str
    scenario: str
    items: list[ComboItem]

class CouponRequest(BaseModel):
    code: str

class CouponResponse(BaseModel):
    valid: bool
    discount: float | None = None
    message: str

class GallerySlide(BaseModel):
    bg: str
    label: str
    imageUrl: str | None = None

class SizeOption(BaseModel):
    label: str
    risk: RiskLevel
    available: bool

class ColorOption(BaseModel):
    name: str
    hex: str
    border: str

class SizeAdvice(BaseModel):
    parts: list[dict]
    type: RiskLevel

class RiskBar(BaseModel):
    label: str
    value: int
    level: RiskLevel

class RiskAnalysis(BaseModel):
    level: RiskLevel
    percent: int
    levelLabel: str
    reviewCount: int
    satisfaction: int
    bars: list[RiskBar]

class ReviewTopic(BaseModel):
    label: str
    sentiment: Sentiment

class Review(BaseModel):
    name: str
    initials: str
    heightWeight: str
    size: str
    rating: float
    date: str
    text: str
    topics: list[ReviewTopic]
    helpful: int

class QAItem(BaseModel):
    question: str
    answer: str
    by: str

class SimilarProduct(BaseModel):
    brand: str
    name: str
    price: str
    rating: str
    bg: str
    imageUrl: str | None = None
    href: str

class CareItem(BaseModel):
    icon: CareIcon
    text: str

class Product(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    slug: str
    brand: str
    title: str
    category: list[dict]
    rating: float
    reviewCount: int
    salesCount: str
    price: float
    oldPrice: float
    discountPercent: int
    risk: RiskAnalysis
    colors: list[ColorOption]
    defaultColorIndex: int
    sizes: list[SizeOption]
    defaultSizeIndex: int
    adviceBySize: dict[int, SizeAdvice]
    gallery: list[GallerySlide]
    summary: str
    audience: list[str]
    occasions: list[str]
    description: list[str]
    care: list[CareItem]
    specs: list[list[str]]
    reviews: list[Review]
    reviewCounts: dict
    qa: list[QAItem]
    qaMeta: dict
    similar: list[SimilarProduct]

class SizeAdviceRequest(BaseModel):
    height: int
    weight: int

class ChatRequest(BaseModel):
    slug: str
    message: str
    history: list[dict] = []

class SellerQuality(BaseModel):
    satici: str
    ortalama_sent: float
    kumas_freq: float
    kargo_freq: float
    ornek_sayisi: int

class TrendPoint(BaseModel):
    tarih: str
    sent_pos: float
    yorum_sayisi: int

class TrendResponse(BaseModel):
    slug: str
    son_90_gun: float
    onceki: float
    trend: Literal["yukseliyor", "dusuyor", "sabit"]
    veri: list[TrendPoint]

class PersonaMatchRequest(BaseModel):
    height: int
    weight: int

class PersonaMatchResponse(BaseModel):
    cluster_id: int
    ornek_sayisi: int
    en_cok_beden: str
    memnuniyet: float
    tanim: str

class CompareRequest(BaseModel):
    slug_a: str
    slug_b: str
