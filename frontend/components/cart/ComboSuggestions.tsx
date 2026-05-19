"use client";

import { Sparkles, Plus, Heart } from "lucide-react";
import { motion } from "motion/react";
import type {
  CartItem,
  ComboGroup as ComboGroupType,
  ComboItem,
  RiskLevel,
} from "@/lib/types";
import { formatTRY } from "@/lib/format";
import { useComboSuggestions } from "@/lib/queries";

export function ComboSuggestions({ items }: { items: CartItem[] }) {

  const ids = items.map((i) => i.id);
  const { data, isLoading, isError } = useComboSuggestions(ids);

  if (ids.length === 0) return null;

  return (
    <section className="mt-14 border-t border-dashed border-slate-200 pt-8">
      <div className="mb-6 max-w-[640px]">
        <span className="mb-3 inline-flex items-center gap-[6px] rounded-full bg-indigo-50 px-[10px] py-[5px] text-[11.5px] font-bold uppercase tracking-wider text-indigo-600">
          <Sparkles className="h-3 w-3" />
          Kanka önerisi
        </span>
        <h2 className="mb-[6px] text-[26px] font-bold tracking-tight text-slate-900">
          Sepetindekilerle tamamla
        </h2>
        <p className="text-sm leading-relaxed text-slate-600">
          AI, sepetindeki her ürün için ayrı kombin kurdu — hangisinin eşleştiği üstünde belirtildi.
        </p>
      </div>

      {isLoading ? (
        <ComboSkeletonList />
      ) : isError ? (
        <ComboEmpty message="Şu an kombin önerisi getiremedim, az sonra tekrar dene." />
      ) : !data || data.length === 0 ? null : (
        <div className="flex flex-col gap-9">
          {data.map((g) => (
            <ComboGroup key={g.sourceId} group={g} />
          ))}
        </div>
      )}
    </section>
  );
}

function ComboGroup({ group }: { group: ComboGroupType }) {
  const total = group.items.reduce((s, i) => s + i.price, 0);
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-[22px] transition hover:shadow-md">
      {}
      <div className="mb-5 grid items-center gap-5 border-b border-dashed border-slate-200 pb-[18px] md:grid-cols-[auto_1fr_auto]">
        <div>
          <span className="mb-[6px] block text-[10.5px] font-bold uppercase tracking-wider text-slate-500">
            Bunla eşleştirildi
          </span>
          <div className="inline-flex items-center gap-[10px] rounded-xl border-[1.5px] border-indigo-200 bg-indigo-50 py-2 pl-2 pr-[14px]">
            <div
              className={`ph ${group.sourceBg} relative h-11 w-11 flex-shrink-0 overflow-hidden rounded-lg`}
            />
            <div>
              <div className="text-[13.5px] font-bold leading-tight tracking-tight text-slate-900">
                {group.sourceName}
              </div>
              <span className="mt-[3px] inline-flex items-center gap-1 whitespace-nowrap text-[11px] font-semibold text-indigo-600">
                <Sparkles className="h-2.5 w-2.5" />
                {group.scenario}
              </span>
            </div>
          </div>
        </div>

        {}
        <div className="hidden flex-col items-center gap-[2px] text-indigo-500 opacity-60 md:flex">
          <svg
            viewBox="0 0 80 24"
            className="h-6 w-[60px]"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeDasharray="3 3"
            strokeLinecap="round"
          >
            <path d="M2 12h70" />
            <path d="M68 6l8 6-8 6" strokeDasharray="0" />
          </svg>
          <span className="text-[10px] font-bold uppercase tracking-widest text-slate-400">
            tamamla
          </span>
        </div>

        <button
          type="button"
          className="inline-flex items-center gap-[6px] whitespace-nowrap rounded-[10px] bg-slate-900 px-4 py-[10px] text-[12.5px] font-bold text-white transition hover:-translate-y-px hover:bg-indigo-600"
        >
          <Plus className="h-3.5 w-3.5" strokeWidth={2.5} />
          Hepsini sepete ekle · {formatTRY(total)}
        </button>
      </div>

      {}
      <div className="grid grid-cols-2 gap-[14px] sm:grid-cols-3">
        {group.items.map((item) => (
          <ComboCard key={item.id} item={item} />
        ))}
      </div>
    </div>
  );
}

function ComboCard({ item }: { item: ComboItem }) {
  return (
    <motion.div
      whileHover={{ y: -3 }}
      transition={{ duration: 0.2, ease: "easeOut" }}
      className="group relative overflow-hidden rounded-md border border-slate-200 bg-white transition-colors hover:border-indigo-300"
    >
      <div className={`ph ${item.bg} relative aspect-square overflow-hidden`}>
        <button
          type="button"
          aria-label="Favoriye ekle"
          className="absolute right-2 top-2 inline-flex h-[30px] w-[30px] scale-[0.85] items-center justify-center rounded-full bg-white text-slate-500 opacity-0 shadow-sm transition-all hover:text-red-500 group-hover:scale-100 group-hover:opacity-100"
        >
          <Heart className="h-3.5 w-3.5" strokeWidth={1.8} />
        </button>
      </div>
      <div className="p-3 pb-[14px]">
        <div className="mb-1 text-[10.5px] font-bold uppercase tracking-wider text-slate-500">
          {item.brand}
        </div>
        <div className="mb-2 line-clamp-2 min-h-[34px] text-[12.5px] font-medium leading-tight text-slate-900">
          {item.name}
        </div>
        <div className="mb-2 flex items-center justify-between">
          <span className="text-[14.5px] font-bold tracking-tight text-indigo-600">
            {formatTRY(item.price)}
          </span>
          <button
            type="button"
            aria-label="Sepete ekle"
            className="inline-flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-600 text-white transition hover:scale-110 hover:bg-indigo-700"
          >
            <Plus className="h-3.5 w-3.5" strokeWidth={2.5} />
          </button>
        </div>
        <RiskChip risk={item.risk} label={item.riskLabel} />
      </div>
    </motion.div>
  );
}

function RiskChip({ risk, label }: { risk: RiskLevel; label: string }) {
  const style =
    risk === "low"
      ? { bg: "bg-green-50", text: "text-[#047857]", dot: "bg-green-500" }
      : risk === "mid"
        ? { bg: "bg-amber-50", text: "text-[#B45309]", dot: "bg-amber-500" }
        : { bg: "bg-red-50", text: "text-red-500", dot: "bg-red-500" };
  return (
    <span
      className={`inline-flex items-center gap-[5px] rounded-full px-2 py-[3px] text-[10.5px] font-bold ${style.bg} ${style.text}`}
    >
      <span className={`h-[6px] w-[6px] rounded-full ${style.dot}`} />
      {label} iade
    </span>
  );
}

function ComboSkeletonList() {
  return (
    <div className="flex flex-col gap-9">
      {[0, 1].map((i) => (
        <div
          key={i}
          className="rounded-lg border border-slate-200 bg-white p-[22px]"
        >
          <div className="mb-5 grid items-center gap-5 border-b border-dashed border-slate-200 pb-[18px] md:grid-cols-[auto_1fr_auto]">
            <div className="h-[60px] w-[200px] animate-pulse rounded-xl bg-slate-100" />
            <div className="hidden md:block" />
            <div className="h-[38px] w-[200px] animate-pulse rounded-[10px] bg-slate-100" />
          </div>
          <div className="grid grid-cols-2 gap-[14px] sm:grid-cols-3">
            {[0, 1, 2].map((j) => (
              <div
                key={j}
                className="overflow-hidden rounded-md border border-slate-200 bg-white"
              >
                <div className="aspect-square animate-pulse bg-slate-100" />
                <div className="space-y-2 p-3 pb-[14px]">
                  <div className="h-3 w-12 animate-pulse rounded bg-slate-100" />
                  <div className="h-3 w-full animate-pulse rounded bg-slate-100" />
                  <div className="h-3 w-3/4 animate-pulse rounded bg-slate-100" />
                  <div className="flex items-center justify-between pt-1">
                    <div className="h-4 w-16 animate-pulse rounded bg-slate-100" />
                    <div className="h-7 w-7 animate-pulse rounded-lg bg-slate-100" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function ComboEmpty({ message }: { message: string }) {
  return (
    <div className="rounded-lg border border-dashed border-slate-200 bg-white p-6 text-center text-sm text-slate-500">
      {message}
    </div>
  );
}
