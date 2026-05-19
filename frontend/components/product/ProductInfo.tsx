"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Star,
  Shield,
  Share2,
  Heart,
  Ruler,
  Sparkles,
  ShoppingCart,
  Truck,
  RotateCcw,
  ChevronDown,
  Tag,
} from "lucide-react";
import { motion, AnimatePresence } from "motion/react";
import type { Product, RiskLevel, SizeAdvice } from "@/lib/types";
import { formatTRY, formatPercent } from "@/lib/format";
import { useChatStore } from "@/store/chatStore";
import { useAdminStore } from "@/store/adminStore";
import { useCartStore } from "@/store/cartStore";
import { useSizeAdviceMutation } from "@/lib/queries";

const MEASUREMENTS_KEY = "user-measurements";

interface UserMeasurements {
  height: number;
  weight: number;
}

function readMeasurements(): UserMeasurements | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(MEASUREMENTS_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Partial<UserMeasurements>;
    if (typeof parsed.height === "number" && typeof parsed.weight === "number") {
      return { height: parsed.height, weight: parsed.weight };
    }
    return null;
  } catch {
    return null;
  }
}

function writeMeasurements(m: UserMeasurements) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(MEASUREMENTS_KEY, JSON.stringify(m));
}

const RISK_TONES: Record<RiskLevel, { bg: string; text: string; ring: string }> = {
  low: { bg: "bg-green-50", text: "text-[#047857]", ring: "bg-green-500" },
  mid: { bg: "bg-amber-50", text: "text-[#B45309]", ring: "bg-amber-500" },
  high: { bg: "bg-red-50", text: "text-[#B91C1C]", ring: "bg-red-500" },
};

function hasMeaningfulSizes(sizes: Product["sizes"]): boolean {
  if (!sizes || sizes.length === 0) return false;
  if (sizes.length > 1) return true;
  const lbl = (sizes[0]?.label || "").trim().toLowerCase();
  return !/^(standart|standard|tek\s*beden|one\s*size|tek|—|-|x)$/i.test(lbl);
}

export function ProductInfo({ product }: { product: Product }) {
  const [colorIdx, setColorIdx] = useState(product.defaultColorIndex);
  const [sizeIdx, setSizeIdx] = useState(product.defaultSizeIndex);
  const openChat = useChatStore((s) => s.open);
  const addToCart = useCartStore((s) => s.addItem);
  const noteLastProduct = useCartStore((s) => s.noteLastProduct);
  const [addedToCart, setAddedToCart] = useState(false);

  useEffect(() => {
    noteLastProduct(product.slug);

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [product.slug]);

  function handleAddToCart() {
    const selColor = product.colors[colorIdx];
    const selSize = product.sizes[sizeIdx];
    const colorName = selColor?.name || "Standart";
    const sizeLabel = selSize?.label || "Tek Beden";
    addToCart(
      {
        id: `${product.slug}__${colorName}__${sizeLabel}`,
        brand: product.brand,
        name: product.title,
        bg: product.gallery[0]?.bg || "ph-bg-1",
        color: colorName,
        colorClass: "",
        size: sizeLabel,
        unitPrice: product.price,
        quantity: 1,
        nudge: null,
      },
      product.slug,
    );
    setAddedToCart(true);
    setTimeout(() => setAddedToCart(false), 1800);
  }

  const sizesMeaningful = useMemo(() => hasMeaningfulSizes(product.sizes), [product.sizes]);

  const [overrideAdvice, setOverrideAdvice] = useState<SizeAdvice | null>(null);
  const [measurementsOpen, setMeasurementsOpen] = useState(false);
  const [heightInput, setHeightInput] = useState<string>("");
  const [weightInput, setWeightInput] = useState<string>("");

  const [hasUserProfile, setHasUserProfile] = useState(false);

  const [detailOpen, setDetailOpen] = useState(false);

  const sizeAdvice = useSizeAdviceMutation(product.slug);

  useEffect(() => {
    if (!sizesMeaningful) return;
    const m = readMeasurements();
    if (m) {
      setHasUserProfile(true);
      setHeightInput(String(m.height));
      setWeightInput(String(m.weight));
      sizeAdvice.mutate(m, {
        onSuccess: (data) => setOverrideAdvice(data),
      });
    }

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [product.slug, sizesMeaningful]);

  function handleMeasurementsSubmit(e: React.FormEvent) {
    e.preventDefault();
    const h = Number(heightInput);
    const w = Number(weightInput);
    if (!Number.isFinite(h) || !Number.isFinite(w) || h <= 0 || w <= 0) return;
    writeMeasurements({ height: h, weight: w });
    setHasUserProfile(true);
    sizeAdvice.mutate(
      { height: h, weight: w },
      { onSuccess: (data) => setOverrideAdvice(data) },
    );
    setMeasurementsOpen(false);
  }

  const color = product.colors[colorIdx];

  let advice: SizeAdvice | undefined;
  if (sizesMeaningful) {
    if (hasUserProfile && overrideAdvice) {
      advice = overrideAdvice;
    } else if (!hasUserProfile) {
      advice = {
        parts: [
          { text: "Boy ve kilonu girersen ", bold: false },
          { text: "sana özel beden öneririm.", bold: true },
        ],
        type: "low",
      };
    } else {
      advice = product.adviceBySize[sizeIdx];
    }
  }

  return (
    <div className="pt-1">
      {}
      <div className="mb-[14px] flex items-start justify-between gap-3">
        <h1 className="flex-1 text-2xl font-semibold leading-snug tracking-tight text-slate-900">
          <span className="mr-[6px] font-extrabold text-indigo-600">
            {product.brand}
          </span>
          {product.title}
        </h1>
        <div className="flex gap-1">
          <ShareBtn label="Paylaş">
            <Share2 className="h-[18px] w-[18px]" />
          </ShareBtn>
          <ShareBtn label="Favoriye ekle">
            <Heart className="h-[18px] w-[18px]" />
          </ShareBtn>
        </div>
      </div>

      {}
      <div className="my-[14px] mb-[22px] flex flex-wrap items-center gap-4">
        <span className="inline-flex items-center gap-[6px] text-sm text-slate-700">
          <span className="inline-flex gap-[1px]">
            {[1, 2, 3, 4, 5].map((j) => (
              <Star
                key={j}
                className={`h-[14px] w-[14px] ${
                  j <= Math.round(product.rating)
                    ? "fill-amber-500 text-amber-500"
                    : "fill-slate-200 text-slate-200"
                }`}
                strokeWidth={0}
              />
            ))}
          </span>
          <span className="font-bold text-slate-900">{product.rating}</span>
          <span aria-hidden className="mx-[2px] h-1 w-1 rounded-full bg-slate-300" />
          <span className="text-slate-500">
            {product.reviewCount.toLocaleString("tr-TR")} yorum
          </span>
          {product.salesCount && (
            <>
              <span aria-hidden className="mx-[2px] h-1 w-1 rounded-full bg-slate-300" />
              <span className="text-slate-500">{product.salesCount}</span>
            </>
          )}
        </span>
        {}
        <RiskPill product={product} />
      </div>

      {}
      <div className="mb-7 flex items-baseline gap-3">
        <div className="text-[38px] font-bold leading-none tracking-tight text-indigo-600">
          {formatTRY(product.price)}
        </div>
        <div className="text-base text-slate-400 line-through">
          {formatTRY(product.oldPrice)}
        </div>
        <div className="rounded-md bg-green-50 px-2 py-[3px] text-xs font-bold text-[#047857]">
          %{product.discountPercent} indirim
        </div>
      </div>

      {}
      <div className="mb-6">
        <div className="mb-3 flex items-center justify-between text-[13px] font-semibold text-slate-900">
          <span>Renk</span>
          <span className="font-medium text-slate-500">{color.name}</span>
        </div>
        <div className="flex gap-[10px]">
          {product.colors.map((c, i) => (
            <button
              key={i}
              type="button"
              aria-label={c.name}
              onClick={() => setColorIdx(i)}
              className={`h-10 w-10 rounded-full border-2 border-white transition-transform hover:scale-110 ${
                i === colorIdx
                  ? "ring-2 ring-indigo-600"
                  : "ring-[1.5px] ring-slate-200"
              }`}
              style={{ background: c.hex }}
            />
          ))}
        </div>
      </div>

      {}
      {!sizesMeaningful && product.sizes.length > 0 && (
        <div className="mb-6 inline-flex items-center gap-2 rounded-md bg-slate-100 px-3 py-2 text-[13px] text-slate-600">
          <Ruler className="h-[14px] w-[14px]" strokeWidth={2} />
          <span>Tek beden — {product.sizes[0].label}</span>
        </div>
      )}

      {sizesMeaningful && (
      <div className="mb-6">
        <button
          type="button"
          onClick={() => setMeasurementsOpen((v) => !v)}
          className="mb-3 inline-flex items-center gap-[6px] text-[13px] font-semibold text-indigo-600 underline decoration-indigo-600/30 decoration-[1.5px] underline-offset-[3px] transition-colors hover:decoration-indigo-600"
        >
          <Ruler className="h-[14px] w-[14px]" strokeWidth={2} />
          Boy-kilonu gir, sana özel beden önersin
        </button>

        {}
        {measurementsOpen && (
          <form
            onSubmit={handleMeasurementsSubmit}
            className="mb-3 flex flex-wrap items-end gap-2 rounded-md border border-indigo-200 bg-indigo-50/40 p-3"
          >
            <label className="flex flex-col text-[11px] font-semibold uppercase tracking-wider text-slate-600">
              Boy (cm)
              <input
                type="number"
                inputMode="numeric"
                min={120}
                max={230}
                value={heightInput}
                onChange={(e) => setHeightInput(e.target.value)}
                className="mt-1 w-20 rounded-md border border-slate-200 bg-white px-2 py-1 text-sm font-medium text-slate-900 focus:border-indigo-600 focus:outline-none"
                placeholder="180"
              />
            </label>
            <label className="flex flex-col text-[11px] font-semibold uppercase tracking-wider text-slate-600">
              Kilo (kg)
              <input
                type="number"
                inputMode="numeric"
                min={30}
                max={200}
                value={weightInput}
                onChange={(e) => setWeightInput(e.target.value)}
                className="mt-1 w-20 rounded-md border border-slate-200 bg-white px-2 py-1 text-sm font-medium text-slate-900 focus:border-indigo-600 focus:outline-none"
                placeholder="78"
              />
            </label>
            <button
              type="submit"
              disabled={sizeAdvice.isPending}
              className="h-9 rounded-md bg-indigo-600 px-4 text-[13px] font-semibold text-white transition hover:bg-indigo-700 disabled:opacity-60"
            >
              {sizeAdvice.isPending ? "Hesaplıyor..." : "Tavsiye al"}
            </button>
          </form>
        )}

        <div className="flex flex-wrap gap-2">
          {product.sizes.map((s, i) => (
            <SizeButton
              key={i}
              label={s.label}
              risk={s.risk}
              active={i === sizeIdx}
              disabled={!s.available}
              onClick={() => s.available && setSizeIdx(i)}
            />
          ))}
        </div>

        {sizeAdvice.isError && (
          <div className="mt-[14px] rounded-md border border-red-200 bg-red-50 px-3 py-2 text-[12.5px] text-red-700">
            Hımm, tavsiye alınamadı. Bir dakka sonra dener misin?
          </div>
        )}

        {}
        {advice && (
            <div
              className="mt-[14px] flex items-start gap-3 rounded-md border border-indigo-600/15 bg-gradient-to-br from-indigo-50 to-[#FAFAFF] px-[18px] py-4 text-sm leading-relaxed text-slate-700"
            >
              <span
                className="inline-flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg text-white"
                style={{ background: "linear-gradient(135deg, #7C5CFF, #5B2EFF)" }}
              >
                <Sparkles className="h-4 w-4" />
              </span>
              <div>
                <span>
                  {advice.parts.map((p, i) =>
                    p.bold ? (
                      <b key={i} className="font-bold text-slate-900">
                        {p.text}
                      </b>
                    ) : (
                      <span key={i}>{p.text}</span>
                    ),
                  )}
                </span>
                <button
                  type="button"
                  onClick={() => setDetailOpen((v) => !v)}
                  className="mt-1 inline-flex cursor-pointer items-center gap-1 font-semibold text-indigo-600 hover:underline"
                  aria-expanded={detailOpen}
                >
                  {detailOpen ? "Detayı gizle" : "Detayı gör"}
                  <ChevronDown className={`h-3 w-3 transition-transform ${detailOpen ? "rotate-180" : ""}`} />
                </button>
                <AnimatePresence>
                  {detailOpen && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: "auto" }}
                      exit={{ opacity: 0, height: 0 }}
                      transition={{ duration: 0.22 }}
                      className="mt-3 overflow-hidden text-[13px] leading-relaxed text-slate-600"
                    >
                      <div className="space-y-2 border-t border-indigo-600/15 pt-3">
                        <p>
                          <span className="font-semibold text-slate-900">Risk dağılımı:</span>{" "}
                          {product.risk.bars.slice(0, 3).map((b, i) => (
                            <span key={b.label}>
                              {i > 0 ? " · " : ""}
                              <span className="font-medium">{b.label}</span> %{b.value}
                            </span>
                          ))}
                        </p>
                        <p>
                          <span className="font-semibold text-slate-900">Toplam memnuniyet:</span> %{product.risk.satisfaction}{" "}
                          (<span className="font-medium">{product.risk.reviewCount}</span> yoruma dayalı)
                        </p>
                        <p>
                          <span className="font-semibold text-slate-900">Diğer bedenlerden:</span>{" "}
                          {product.sizes
                            .map((s, i) => ({ label: s.label, idx: i }))
                            .filter((s) => s.idx !== sizeIdx)
                            .slice(0, 4)
                            .map((s, i) => {
                              const adv = product.adviceBySize[s.idx];
                              const meta = adv?.parts.find((p) => p.bold && /^\d+ kişi/.test(p.text));
                              return (
                                <span key={s.label} className="mr-2">
                                  {i > 0 ? "· " : ""}
                                  <span className="font-medium">{s.label}</span>: {meta?.text ?? "veri az"}
                                </span>
                              );
                            })}
                        </p>
                        <p className="pt-1 text-slate-500">
                          Daha kapsamlı analiz için sağ alttaki{" "}
                          <button
                            type="button"
                            onClick={() => openChat(product.slug)}
                            className="font-semibold text-indigo-600 hover:underline"
                          >
                            AI&apos;ya sor
                          </button>
                          .
                        </p>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </div>
          )}
      </div>
      )}

      {}
      <div className="my-7 flex gap-[10px]">
        <button
          type="button"
          onClick={handleAddToCart}
          className={`inline-flex h-14 flex-[1.5] items-center justify-center gap-2 rounded-md text-base font-bold text-white shadow-md transition hover:-translate-y-px ${
            addedToCart
              ? "bg-emerald-600 hover:bg-emerald-700"
              : "bg-indigo-600 hover:bg-indigo-700"
          }`}
          aria-live="polite"
        >
          <ShoppingCart className="h-5 w-5" strokeWidth={2} />
          {addedToCart ? "Sepete eklendi ✓" : "Sepete Ekle"}
        </button>
        <button
          type="button"
          onClick={() => openChat(product.slug)}
          className="group inline-flex h-14 flex-1 items-center justify-center gap-2 rounded-md border-[1.5px] border-indigo-200 bg-white text-base font-semibold text-indigo-700 transition-all hover:-translate-y-px hover:border-indigo-600 hover:bg-indigo-50 hover:text-indigo-800"
        >
          <Sparkles
            className="h-[18px] w-[18px] text-indigo-500 transition-colors group-hover:text-indigo-700"
            strokeWidth={2}
          />
          Kanka&apos;ya Sor
        </button>
      </div>

      {}
      <div className="mt-2 flex flex-wrap gap-[18px] border-t border-slate-200 pt-[18px]">
        <Guarantee icon={<Truck className="h-4 w-4 text-indigo-600" />}>
          Ücretsiz Kargo
        </Guarantee>
        <Guarantee icon={<RotateCcw className="h-4 w-4 text-indigo-600" />}>
          15 Gün İade
        </Guarantee>
        <Guarantee icon={<Shield className="h-4 w-4 text-indigo-600" />}>
          Güvenli Ödeme
        </Guarantee>
      </div>

      {}
      <style jsx>{`
        @keyframes aiGlow {
          0%, 100% { opacity: 0.5; }
          50% { opacity: 0.9; }
        }
      `}</style>
    </div>
  );
}

function ShareBtn({
  children,
  label,
}: {
  children: React.ReactNode;
  label: string;
}) {
  return (
    <button
      type="button"
      aria-label={label}
      className="inline-flex h-9 w-9 items-center justify-center rounded-[10px] text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-900"
    >
      {children}
    </button>
  );
}

function Guarantee({
  icon,
  children,
}: {
  icon: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <span className="inline-flex items-center gap-2 text-[12.5px] font-medium text-slate-600">
      {icon}
      {children}
    </span>
  );
}

function SizeButton({
  label,
  risk,
  active,
  disabled,
  onClick,
}: {
  label: string;
  risk: RiskLevel;
  active: boolean;
  disabled: boolean;
  onClick: () => void;
}) {
  const dotColor =
    risk === "low"
      ? "bg-green-500"
      : risk === "mid"
        ? "bg-amber-500"
        : "bg-red-500";
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className={`relative min-w-[52px] rounded-[10px] border-[1.5px] px-[14px] text-sm font-semibold transition-all ${
        active
          ? "border-indigo-600 bg-indigo-600 text-white"
          : "border-slate-200 bg-white text-slate-700 hover:-translate-y-px hover:border-slate-400"
      } ${
        disabled
          ? "cursor-not-allowed bg-slate-50 text-slate-300 hover:translate-y-0 hover:border-slate-200"
          : ""
      } h-[46px]`}
    >
      {label}
      <span
        className={`absolute right-[5px] top-[5px] h-[7px] w-[7px] rounded-full ${dotColor} ${
          active ? "ring-2 ring-white" : ""
        }`}
      />
      {disabled && (
        <span
          aria-hidden
          className="pointer-events-none absolute inset-0 rounded-[9px]"
          style={{
            background:
              "linear-gradient(135deg, transparent calc(50% - 1px), #D1D5DB 50%, transparent calc(50% + 1px))",
          }}
        />
      )}
    </button>
  );
}

function RiskPill({ product }: { product: Product }) {
  const isAdmin = useAdminStore((s) => s.isAdmin);

  if (!isAdmin) return null;
  const tone = RISK_TONES[product.risk.level];

  const summaryText =
    product.risk.level === "low"
      ? "Bu üründe iade riski düşük."
      : product.risk.level === "mid"
        ? "Bu üründe iade riski orta seviyede."
        : "Bu üründe iade riski yüksek.";

  const BarsPanel = (
    <>
      <h4 className="mb-1 text-sm font-bold text-slate-900">{summaryText}</h4>
      <p className="mb-[14px] text-[13px] leading-relaxed text-slate-600">
        {product.risk.reviewCount.toLocaleString("tr-TR")} yorum analiz edildi.
        Müşterilerin {formatPercent(product.risk.satisfaction)}&apos;i memnun ayrılmış.
      </p>
      <div className="flex flex-col gap-[10px]">
        {product.risk.bars.map((bar) => (
          <div
            key={bar.label}
            className="grid grid-cols-[120px_1fr_36px] items-center gap-[10px] text-xs"
          >
            <span className="font-medium text-slate-700">{bar.label}</span>
            <div className="h-2 overflow-hidden rounded bg-slate-100">
              <div
                className="h-full rounded transition-all duration-700"
                style={{
                  width: `${bar.value}%`,
                  background:
                    bar.level === "low"
                      ? "linear-gradient(90deg, #34D399, #10B981)"
                      : bar.level === "mid"
                        ? "linear-gradient(90deg, #FBBF24, #F59E0B)"
                        : "linear-gradient(90deg, #F87171, #EF4444)",
                }}
              />
            </div>
            <span className="text-right font-bold text-slate-900">
              %{bar.value}
            </span>
          </div>
        ))}
      </div>
    </>
  );

  return (
    <div className="w-full">
      <button
        type="button"
        className={`inline-flex items-center gap-2 rounded-full px-[13px] py-[7px] pl-[10px] text-[13px] font-bold transition-all hover:-translate-y-px hover:shadow-md ${tone.bg} ${tone.text}`}
      >
        <span
          className={`relative flex h-[18px] w-[18px] items-center justify-center rounded-full ${tone.ring}`}
        >
          <Shield className="h-[11px] w-[11px] text-white" strokeWidth={2} />
          <span
            aria-hidden
            className={`absolute -inset-1 animate-pulse-dot rounded-full ${tone.ring} opacity-35`}
          />
        </span>
        %{product.risk.percent} İade Riski · {product.risk.levelLabel}
      </button>
      <div className="mt-3 rounded-lg border border-dashed border-amber-300 bg-amber-50/40 p-[16px]">
        <div className="mb-2 inline-flex items-center gap-1 text-[10.5px] font-bold uppercase tracking-wider text-amber-700">
          <Tag className="h-3 w-3" />
          Admin: Risk dağılımı
        </div>
        {BarsPanel}
      </div>
    </div>
  );
}
