export type RiskLevel = "low" | "mid" | "high";

export type SizeFit = "fits" | "small" | "large" | "unknown";

export type Sentiment = "pos" | "mid" | "neg";

export type CategoryKey =
  | "dress"
  | "shirt"
  | "shoe"
  | "bag"
  | "home"
  | "cosmetics"
  | "tech"
  | "sport"
  | "baby";

export interface Category {
  key: CategoryKey;
  label: string;
}

export interface ProductSummary {
  slug: string;
  brand: string;
  name: string;
  bg: string;
  placeholder: string;
  price: string;
  risk: RiskLevel;
  riskLabel: string;
  rating: string;
  imageUrl?: string | null;
}

export interface HeroBubble {
  position: 1 | 2 | 3;
  text: string;
}

export interface HowItWorksFeature {
  num: string;
  icon: "spark" | "ruler" | "hanger";
  title: string;
  description: string;
  example: string;
}

export type CartNudgeType = "size" | "combo";

export interface CartNudge {
  type: CartNudgeType;
  parts: Array<{ text: string; bold?: boolean }>;
  cta: { label: string; href: string };
}

export interface CartItem {
  id: string;
  brand: string;
  name: string;
  bg: string;
  color: string;
  colorClass: string;
  size: string;
  unitPrice: number;
  quantity: number;
  nudge: CartNudge | null;
}

export interface ComboItem {
  id: string;
  brand: string;
  name: string;
  bg: string;
  price: number;
  risk: RiskLevel;
  riskLabel: string;
}

export interface ComboGroup {
  sourceId: string;
  sourceName: string;
  sourceBg: string;
  scenario: string;
  items: ComboItem[];
}

export interface CouponResponse {
  valid: boolean;
  discount: number | null;
  message: string;
}

export interface GallerySlide {
  bg: string;
  label: string;

  imageUrl?: string | null;
}

export interface SizeOption {
  label: string;
  risk: RiskLevel;
  available: boolean;
}

export interface ColorOption {
  name: string;
  hex: string;
  border: string;
}

export interface SizeAdvice {

  parts: Array<{ text: string; bold?: boolean }>;

  type: RiskLevel;
}

export interface RiskBar {
  label: string;
  value: number;
  level: RiskLevel;
}

export interface RiskAnalysis {
  level: RiskLevel;
  percent: number;
  levelLabel: string;
  reviewCount: number;
  satisfaction: number;
  bars: RiskBar[];
}

export interface ReviewTopic {
  label: string;
  sentiment: Sentiment;
}

export interface ReviewClassification {
  sent: "positive" | "neutral" | "negative" | null;
  fit: "tam" | "kucuk" | "buyuk" | null;
  risk: "kumas" | "renk" | "kalite" | "kargo" | "koku" | "gorsel" | null;
}

export interface Review {
  name: string;
  initials: string;
  heightWeight: string;
  size: string;
  rating: number;
  date: string;
  text: string;
  topics: ReviewTopic[];
  helpful: number;

  classification?: ReviewClassification;
}

export interface QAItem {
  question: string;
  answer: string;

  by: string;
}

export interface SimilarProduct {
  brand: string;
  name: string;
  price: string;
  rating: string;
  bg: string;

  imageUrl?: string | null;
  href: string;
}

export interface Product {
  slug: string;
  brand: string;
  title: string;
  category: { label: string; href: string }[];
  rating: number;
  reviewCount: number;
  salesCount: string;
  price: number;
  oldPrice: number;
  discountPercent: number;
  risk: RiskAnalysis;
  colors: ColorOption[];
  defaultColorIndex: number;
  sizes: SizeOption[];
  defaultSizeIndex: number;

  adviceBySize: Record<number, SizeAdvice>;
  gallery: GallerySlide[];
  summary: string;
  audience: string[];
  occasions: string[];
  description: string[];
  care: Array<{ icon: "wash" | "iron" | "shield" | "truck" | "check"; text: string }>;
  specs: Array<[string, string]>;
  reviews: Review[];
  reviewCounts: { all: number; positive: number; negative: number; matchedToMe: number };
  qa: QAItem[];
  qaMeta: { total: number; avgResponse: string };
  similar: SimilarProduct[];
}
