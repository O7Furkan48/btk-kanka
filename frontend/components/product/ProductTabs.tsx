"use client";

import { useEffect, useRef, useState } from "react";
import { Sparkles, Star, Tag } from "lucide-react";
import { useAdminStore } from "@/store/adminStore";
import { Droplet, Flame, Shield, Truck, Check } from "lucide-react";
import type { Product, Sentiment } from "@/lib/types";
import { useReviews } from "@/lib/queries";

const MEASUREMENTS_KEY = "user-measurements";

function readMeasurements(): { height: number; weight: number } | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(MEASUREMENTS_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as { height?: number; weight?: number };
    if (typeof parsed.height === "number" && typeof parsed.weight === "number") {
      return { height: parsed.height, weight: parsed.weight };
    }
    return null;
  } catch {
    return null;
  }
}

const CARE_ICONS = {
  wash: Droplet,
  iron: Flame,
  shield: Shield,
  truck: Truck,
  check: Check,
} as const;

export function ProductTabs({ product }: { product: Product }) {
  const [tab, setTab] = useState<0 | 1 | 2>(0);
  const sectionRef = useRef<HTMLElement | null>(null);

  const RESERVE_HEIGHT = 1800;

  function changeTab(t: 0 | 1 | 2) {
    if (t === tab) return;

    const section = sectionRef.current;
    const tabBarY = section
      ? section.getBoundingClientRect().top + window.scrollY
      : 0;
    const currentScrollY = window.scrollY;
    const offsetFromTabBar = currentScrollY - tabBarY;
    setTab(t);

    let frames = 0;
    function tick() {
      if (frames++ > 6) return;
      const newTabBarY = section
        ? section.getBoundingClientRect().top + window.scrollY
        : 0;
      const wantedY = Math.max(0, newTabBarY + offsetFromTabBar);
      if (Math.abs(window.scrollY - wantedY) > 0.5) {
        window.scrollTo({ top: wantedY, behavior: "auto" });
      }
      requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  }

  function handleTabMouseDown(e: React.MouseEvent<HTMLButtonElement>) {
    e.preventDefault();
  }

  return (
    <section ref={sectionRef} className="mx-auto max-w-[1140px] px-8 py-14">
      {}
      <div className="mb-7 flex gap-1 border-b border-slate-200">
        <TabBtn active={tab === 0} onClick={() => changeTab(0)} onMouseDown={handleTabMouseDown}>
          Açıklama
        </TabBtn>
        <TabBtn active={tab === 1} onClick={() => changeTab(1)} onMouseDown={handleTabMouseDown}>
          Özellikler
        </TabBtn>
        <TabBtn active={tab === 2} onClick={() => changeTab(2)} onMouseDown={handleTabMouseDown}>
          Yorumlar
          <span className="ml-1 font-medium text-slate-400">
            {product.reviewCount.toLocaleString("tr-TR")}
          </span>
        </TabBtn>
      </div>

      {}
      <div style={{ minHeight: RESERVE_HEIGHT }}>
        {tab === 0 && <DescriptionTab product={product} />}
        {tab === 1 && <SpecsTab product={product} />}
        {tab === 2 && <ReviewsTab product={product} />}
      </div>
    </section>
  );
}

function TabBtn({
  active,
  onClick,
  onMouseDown,
  children,
}: {
  active: boolean;
  onClick: () => void;
  onMouseDown?: (e: React.MouseEvent<HTMLButtonElement>) => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      onMouseDown={onMouseDown}
      className={`relative px-[18px] py-[14px] text-[15px] font-semibold transition-colors ${
        active ? "text-slate-900" : "text-slate-500 hover:text-slate-700"
      }`}
    >
      {children}
      {active && (
        <span
          aria-hidden
          className="absolute -bottom-px left-[18px] right-[18px] h-[2px] rounded bg-indigo-600"
        />
      )}
    </button>
  );
}

function DescriptionTab({ product }: { product: Product }) {
  const [expanded, setExpanded] = useState(false);

  const fullText = product.description.join("\n\n");
  const isLong = fullText.length > 400 || product.description.length > 1;
  const visibleParagraphs = expanded
    ? product.description
    : product.description.slice(0, 1);
  return (
    <div>
      {}
      <div className="mb-7 flex items-start gap-[14px] rounded-lg border border-indigo-600/15 bg-gradient-to-br from-indigo-50 to-[#FAFAFF] px-[22px] py-5">
        <span
          className="inline-flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-[10px] text-white"
          style={{ background: "linear-gradient(135deg, #7C5CFF, #5B2EFF)" }}
        >
          <Sparkles className="h-[18px] w-[18px]" />
        </span>
        <div>
          <div className="mb-1 text-[11px] font-bold uppercase tracking-wider text-indigo-600">
            Kanka&apos;nın 1 cümle özeti
          </div>
          <p className="text-[15px] font-medium leading-relaxed text-slate-800">
            {product.summary}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-10 md:grid-cols-[1.4fr_1fr]">
        <div>
          <SectionTitle first>Kim için uygun?</SectionTitle>
          <div className="mb-5 flex flex-wrap gap-2">
            {product.audience.map((a) => (
              <Chip key={a}>{a}</Chip>
            ))}
          </div>

          <SectionTitle>Hangi durumlar için?</SectionTitle>
          <div className="mb-5 flex flex-wrap gap-2">
            {product.occasions.map((o) => (
              <Chip key={o} subtle>
                {o}
              </Chip>
            ))}
          </div>

          <SectionTitle>Ürün açıklaması</SectionTitle>
          <div className="text-[14.5px] leading-loose text-slate-700">
            {visibleParagraphs.map((p, i) => (
              <p key={i} className="mb-3">
                {p.length > 400 && !expanded ? `${p.slice(0, 400)}…` : p}
              </p>
            ))}
            {isLong && (
              <button
                type="button"
                onClick={() => setExpanded((v) => !v)}
                className="mt-1 inline-flex cursor-pointer items-center gap-1 text-[13.5px] font-semibold text-indigo-600 hover:underline"
                aria-expanded={expanded}
              >
                {expanded ? "Daha az göster ↑" : "Devamını oku ↓"}
              </button>
            )}
          </div>
        </div>

        <div>
          <SectionTitle first>Bakım talimatları</SectionTitle>
          <ul className="flex flex-col gap-[10px]">
            {product.care.map((c, i) => {
              const Icon = CARE_ICONS[c.icon];
              return (
                <li
                  key={i}
                  className="flex items-center gap-[10px] text-sm text-slate-700"
                >
                  <Icon
                    className="h-[18px] w-[18px] flex-shrink-0 text-slate-500"
                    strokeWidth={1.8}
                  />
                  {c.text}
                </li>
              );
            })}
          </ul>
        </div>
      </div>
    </div>
  );
}

function SectionTitle({
  children,
  first,
}: {
  children: React.ReactNode;
  first?: boolean;
}) {
  return (
    <div
      className={`mb-3 text-[13px] font-bold uppercase tracking-wider text-slate-900 ${
        first ? "mt-0" : "mt-6"
      }`}
    >
      {children}
    </div>
  );
}

function Chip({
  children,
  subtle,
}: {
  children: React.ReactNode;
  subtle?: boolean;
}) {
  return (
    <span
      className={`rounded-full px-[13px] py-[7px] text-[13px] font-medium text-slate-700 ${
        subtle
          ? "border border-slate-200 bg-white"
          : "bg-slate-100"
      }`}
    >
      {children}
    </span>
  );
}

function SpecsTab({ product }: { product: Product }) {
  return (
    <table className="w-full border-collapse">
      <tbody>
        {product.specs.map((s, i) => (
          <tr key={i} className={i % 2 === 0 ? "bg-slate-50" : ""}>
            <td className="border-b border-slate-200 px-[18px] py-[14px] text-sm font-medium text-slate-500">
              {s[0]}
            </td>
            <td className="border-b border-slate-200 px-[18px] py-[14px] text-sm font-semibold text-slate-900">
              {s[1]}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

type ReviewFilter = "all" | "pos" | "neg" | "me";
const PAGE_SIZE = 20;
const MAX_REVIEWS = 200;

function hasMeaningfulSizes(sizes: Product["sizes"]): boolean {
  if (!sizes || sizes.length === 0) return false;
  if (sizes.length > 1) return true;
  const lbl = (sizes[0]?.label || "").trim().toLowerCase();
  return !/^(standart|standard|tek\s*beden|one\s*size|tek|—|-|x)$/i.test(lbl);
}

function ReviewsTab({ product }: { product: Product }) {
  const [filter, setFilter] = useState<ReviewFilter>("all");
  const [limit, setLimit] = useState(PAGE_SIZE);
  const counts = product.reviewCounts;
  const isAdmin = useAdminStore((s) => s.isAdmin);
  const sizesMeaningful = hasMeaningfulSizes(product.sizes);

  const [measurements, setMeasurements] = useState<
    { height: number; weight: number } | null
  >(null);
  useEffect(() => {
    setMeasurements(readMeasurements());
  }, []);

  const matchedTo = filter === "me" ? (measurements ?? undefined) : undefined;
  const meDisabled = !measurements;

  const { data, isLoading, isError } = useReviews(
    product.slug,
    filter,
    limit,
    0,
    matchedTo,
  );

  const list = data?.items ?? [];
  const total = data?.total ?? 0;

  function pickFilter(f: ReviewFilter) {
    setLimit(PAGE_SIZE);
    setFilter(f);
  }

  return (
    <div>
      <div className="mb-5 flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 pb-[18px]">
        <div className="flex flex-wrap gap-[6px]">
          <FilterChip active={filter === "all"} onClick={() => pickFilter("all")}>
            Tüm yorumlar{counts.all > 0 ? ` (${counts.all.toLocaleString("tr-TR")})` : ""}
          </FilterChip>
          {counts.positive > 0 && (
            <FilterChip active={filter === "pos"} onClick={() => pickFilter("pos")}>
              Pozitif ({counts.positive.toLocaleString("tr-TR")})
            </FilterChip>
          )}
          {counts.negative > 0 && (
            <FilterChip active={filter === "neg"} onClick={() => pickFilter("neg")}>
              Negatif ({counts.negative.toLocaleString("tr-TR")})
            </FilterChip>
          )}
          {}
          {sizesMeaningful && (
            <FilterChip
              active={filter === "me"}
              disabled={meDisabled}
              onClick={() => !meDisabled && pickFilter("me")}
            >
              {meDisabled
                ? "✨ Sadece bana uygun (boy-kilo gerekli)"
                : "✨ Sadece bana uygun"}
            </FilterChip>
          )}
        </div>
        <label className="inline-flex items-center gap-[6px] text-[13px] text-slate-600">
          Sırala:
          <select className="cursor-pointer rounded-md border-[1.5px] border-slate-200 bg-white px-[10px] py-[6px] text-[13px] font-semibold text-slate-900">
            <option>En faydalı</option>
            <option>En yeni</option>
            <option>En yüksek puan</option>
          </select>
        </label>
      </div>

      {isLoading && (
        <div className="flex flex-col gap-[18px]">
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              className="grid animate-pulse grid-cols-[56px_1fr] gap-4 rounded-md border border-slate-200 bg-white px-5 py-[18px]"
            >
              <div className="h-11 w-11 rounded-full bg-slate-200" />
              <div>
                <div className="mb-2 h-4 w-1/3 rounded bg-slate-200" />
                <div className="mb-2 h-3 w-1/2 rounded bg-slate-100" />
                <div className="mb-2 h-3 w-full rounded bg-slate-100" />
                <div className="h-3 w-4/5 rounded bg-slate-100" />
              </div>
            </div>
          ))}
        </div>
      )}

      {isError && !isLoading && (
        <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          Hımm, yorumlar yüklenemedi. Bir dakka sonra dener misin?
        </div>
      )}

      {!isLoading && !isError && list.length === 0 && (
        <div className="rounded-md border border-dashed border-slate-200 bg-slate-50 px-4 py-6 text-center text-sm text-slate-500">
          Bu filtrede yorum yok.
        </div>
      )}

      <div className="flex flex-col gap-[18px]">
        {list.map((r, i) => (
          <article
            key={i}
            className="grid grid-cols-[56px_1fr] gap-4 rounded-md border border-slate-200 bg-white px-5 py-[18px] transition-colors hover:border-slate-300"
          >
            <div>
              <div className="flex h-11 w-11 items-center justify-center rounded-full bg-gradient-to-br from-indigo-100 to-indigo-200 text-base font-bold text-indigo-700">
                {r.initials}
              </div>
            </div>
            <div>
              <div className="mb-2 flex flex-wrap items-center gap-[10px]">
                <span className="text-sm font-bold text-slate-900">
                  {r.name}
                </span>
                <span className="inline-flex gap-[1px]">
                  {[1, 2, 3, 4, 5].map((j) => (
                    <Star
                      key={j}
                      className={`h-[13px] w-[13px] ${
                        j <= r.rating
                          ? "fill-amber-500 text-amber-500"
                          : "fill-slate-200 text-slate-200"
                      }`}
                      strokeWidth={0}
                    />
                  ))}
                </span>
                {r.date && (
                  <span className="ml-auto text-xs text-slate-400">{r.date}</span>
                )}
              </div>
              {}
              {(r.heightWeight || r.size) && (
                <div className="mb-[10px] flex flex-wrap gap-[6px]">
                  {r.heightWeight && <InfoChip indigo>{r.heightWeight}</InfoChip>}
                  {r.size && <InfoChip>Beden: {r.size}</InfoChip>}
                </div>
              )}
              <p className="mb-3 text-sm leading-relaxed text-slate-700">
                {r.text}
              </p>
              <div className="flex flex-wrap items-center justify-between gap-3">
                {}
                {isAdmin && r.topics.length > 0 ? (
                  <div className="flex flex-wrap items-center gap-[6px]">
                    {r.topics.map((t, j) => (
                      <span
                        key={j}
                        className="inline-flex items-center gap-[5px] rounded-md bg-slate-100 px-[9px] py-[3px] text-[11.5px] font-medium text-slate-700"
                      >
                        <SentimentDot s={t.sentiment} />
                        {t.label}
                      </span>
                    ))}
                  </div>
                ) : (
                  <span aria-hidden />
                )}
                <div className="inline-flex items-center gap-[6px] text-xs text-slate-500">
                  Faydalı mı?
                  <HelpfulBtn>👍 {r.helpful}</HelpfulBtn>
                  <HelpfulBtn>👎</HelpfulBtn>
                </div>
              </div>

              {}
              {isAdmin && r.classification && (
                <div className="mt-3 flex flex-wrap items-center gap-[6px] rounded-md border border-dashed border-amber-300 bg-amber-50 px-2.5 py-1.5">
                  <span className="inline-flex items-center gap-1 text-[10.5px] font-bold uppercase tracking-wider text-amber-700">
                    <Tag className="h-3 w-3" />
                    BERT
                  </span>
                  {r.classification.sent && (
                    <span className={`inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-[11px] font-semibold ${
                      r.classification.sent === "positive"
                        ? "bg-emerald-100 text-emerald-700"
                        : r.classification.sent === "negative"
                          ? "bg-rose-100 text-rose-700"
                          : "bg-slate-200 text-slate-700"
                    }`}>
                      sent: {r.classification.sent}
                    </span>
                  )}
                  {r.classification.fit && (
                    <span className="inline-flex items-center gap-1 rounded-md bg-violet-100 px-2 py-0.5 text-[11px] font-semibold text-violet-700">
                      fit: {r.classification.fit}
                    </span>
                  )}
                  {r.classification.risk && (
                    <span className="inline-flex items-center gap-1 rounded-md bg-orange-100 px-2 py-0.5 text-[11px] font-semibold text-orange-700">
                      risk: {r.classification.risk}
                    </span>
                  )}
                  {!r.classification.sent &&
                   !r.classification.fit &&
                   !r.classification.risk && (
                    <span className="text-[11px] text-slate-500 italic">
                      (etiket yok — BERT atlamış)
                    </span>
                  )}
                </div>
              )}
            </div>
          </article>
        ))}
      </div>

      {list.length > 0 && list.length < total && limit < MAX_REVIEWS && (
        <button
          type="button"
          onClick={() => setLimit((l) => Math.min(l + PAGE_SIZE, MAX_REVIEWS))}
          className="mx-auto mt-6 block rounded-[10px] border-[1.5px] border-slate-200 bg-white px-6 py-3 text-sm font-semibold text-slate-900 transition-colors hover:border-indigo-600 hover:text-indigo-600"
        >
          Daha fazla yorum yükle (max {MAX_REVIEWS})
        </button>
      )}
      {limit >= MAX_REVIEWS && total > MAX_REVIEWS && (
        <p className="mt-4 text-center text-[12.5px] text-slate-500">
          İlk {MAX_REVIEWS} yorum gösteriliyor. Toplam {total.toLocaleString("tr-TR")} yorum mevcut.
        </p>
      )}
    </div>
  );
}

function FilterChip({
  active,
  onClick,
  children,
  disabled,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
  disabled?: boolean;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={`rounded-full border-[1.5px] px-[13px] py-[7px] text-[13px] font-medium transition-all ${
        active
          ? "border-slate-900 bg-slate-900 text-white"
          : "border-slate-200 bg-white text-slate-700 hover:border-slate-400"
      } ${disabled ? "cursor-not-allowed opacity-50 hover:border-slate-200" : ""}`}
    >
      {children}
    </button>
  );
}

function InfoChip({
  children,
  indigo,
}: {
  children: React.ReactNode;
  indigo?: boolean;
}) {
  return (
    <span
      className={`rounded-md px-[9px] py-[3px] text-[11.5px] font-medium ${
        indigo
          ? "bg-indigo-50 text-indigo-700"
          : "bg-slate-100 text-slate-700"
      }`}
    >
      {children}
    </span>
  );
}

function SentimentDot({ s }: { s: Sentiment }) {
  const cls =
    s === "pos"
      ? "bg-green-500"
      : s === "mid"
        ? "bg-amber-500"
        : "bg-red-500";
  return <span className={`h-2 w-2 rounded-full ${cls}`} />;
}

function HelpfulBtn({ children }: { children: React.ReactNode }) {
  return (
    <button
      type="button"
      className="inline-flex items-center gap-1 rounded-md border border-slate-200 px-[10px] py-[4px] text-xs font-medium text-slate-700 transition-colors hover:border-indigo-600 hover:text-indigo-600"
    >
      {children}
    </button>
  );
}
