"use client";

import { useState } from "react";
import type { Category, CategoryKey } from "@/lib/types";
import { useCategories } from "@/lib/queries";

const ICONS: Record<CategoryKey, React.ReactNode> = {
  dress: (
    <svg viewBox="0 0 32 32" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 5h8l1 4-3 2 2 4-4 14H10L6 15l2-4-3-2 1-4z" />
      <path d="M14 5v3M18 5v3" />
    </svg>
  ),
  shirt: (
    <svg viewBox="0 0 32 32" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
      <path d="M11 5l5 3 5-3 6 3-2 6-4-1v13H11V13l-4 1-2-6z" />
    </svg>
  ),
  shoe: (
    <svg viewBox="0 0 32 32" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
      <path d="M4 22c0-2 1-3 3-3l3-1 3-9 5 1-1 4 4 1 7 5c1 1 1 4-1 4H6c-1 0-2-1-2-2z" />
      <path d="M14 13l5 2M11 19l3-1" />
    </svg>
  ),
  bag: (
    <svg viewBox="0 0 32 32" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
      <path d="M7 12h18l-1 15H8z" />
      <path d="M11 12V8a5 5 0 0 1 10 0v4" />
    </svg>
  ),
  home: (
    <svg viewBox="0 0 32 32" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
      <path d="M5 16 16 5l11 11M8 14v13h16V14" />
      <path d="M13 27v-6h6v6" />
    </svg>
  ),
  cosmetics: (
    <svg viewBox="0 0 32 32" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 4h8v6h-8z" />
      <path d="M10 10h12v17H10z" />
      <path d="M14 16h4" />
    </svg>
  ),
  tech: (
    <svg viewBox="0 0 32 32" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
      <rect x="9" y="4" width="14" height="24" rx="2" />
      <path d="M14 8h4M15 24h2" />
    </svg>
  ),
  baby: (
    <svg viewBox="0 0 32 32" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="16" cy="14" r="7" />
      <path d="M13 13h.01M19 13h.01" />
      <path d="M13 17c1 1.5 2 2 3 2s2-.5 3-2" />
      <path d="M9 10c-2 0-2 4 0 4M23 10c2 0 2 4 0 4" />
      <path d="M16 21v6M11 27h10" />
    </svg>
  ),
  sport: (
    <svg viewBox="0 0 32 32" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="16" cy="16" r="11" />
      <path d="M16 5c4 3 4 19 0 22M16 5c-4 3-4 19 0 22M5 16h22" />
    </svg>
  ),
};

export function Categories() {
  const [activeIdx, setActiveIdx] = useState(1);
  const { data, isLoading, isError } = useCategories();

  const categories: Category[] = isError ? [] : data ?? [];

  return (
    <div
      className="mx-auto flex max-w-[1280px] gap-[14px] overflow-x-auto px-8 pt-12"
      style={{ scrollbarWidth: "none" }}
    >
      <style jsx>{`
        div::-webkit-scrollbar { display: none; }
      `}</style>
      {isLoading
        ? Array.from({ length: 9 }).map((_, i) => (
            <div
              key={i}
              className="h-9 w-24 flex-shrink-0 animate-pulse rounded-full bg-slate-200"
              aria-hidden
            />
          ))
        : categories.map((cat, i) => (
            <CategoryButton
              key={cat.key}
              cat={cat}
              active={i === activeIdx}
              onClick={() => setActiveIdx(i)}
            />
          ))}
    </div>
  );
}

function CategoryButton({
  cat,
  active,
  onClick,
}: {
  cat: Category;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="flex w-[116px] flex-shrink-0 flex-col items-center gap-[10px] rounded-[14px] px-1 py-2 transition-all hover:-translate-y-0.5 hover:bg-white"
    >
      <span
        className={`flex h-[68px] w-[68px] items-center justify-center rounded-full border-2 bg-white shadow-sm transition-all ${
          active
            ? "border-indigo-600 text-indigo-600 shadow-glow"
            : "border-transparent text-slate-700 hover:text-indigo-600"
        }`}
      >
        <span className="block h-7 w-7">{ICONS[cat.key]}</span>
      </span>
      <span
        className={`text-[13px] transition-colors ${
          active
            ? "font-semibold text-indigo-600"
            : "font-medium text-slate-700"
        }`}
      >
        {cat.label}
      </span>
    </button>
  );
}
