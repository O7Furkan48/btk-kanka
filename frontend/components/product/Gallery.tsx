"use client";

import { useState } from "react";
import type { GallerySlide } from "@/lib/types";

export function Gallery({ slides }: { slides: GallerySlide[] }) {
  const [idx, setIdx] = useState(0);

  return (
    <div className="sticky top-[90px]">
      {}
      <div className="relative mb-[14px] aspect-square overflow-hidden rounded-lg bg-slate-100">
        {slides.map((s, i) => (
          <div
            key={i}
            className={`absolute inset-0 transition-opacity duration-300 ${
              i === idx ? "opacity-100" : "opacity-0"
            }`}
          >
            {s.imageUrl ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={s.imageUrl}
                alt={s.label}
                className="h-full w-full object-cover"
                loading={i === 0 ? "eager" : "lazy"}
              />
            ) : (
              <div
                className={`ph ${s.bg} flex h-full w-full items-center justify-center font-mono text-[13px] uppercase tracking-wider text-slate-900/40`}
              >
                {s.label}
              </div>
            )}
          </div>
        ))}
      </div>

      {}
      <div className="grid grid-cols-4 gap-[10px]">
        {slides.map((s, i) => (
          <button
            key={i}
            type="button"
            aria-label={`Görsel ${i + 1}`}
            onClick={() => setIdx(i)}
            className={`relative aspect-square overflow-hidden rounded-md border-2 transition-all hover:-translate-y-0.5 ${
              i === idx
                ? "border-indigo-600 shadow-glow"
                : "border-transparent"
            } ${s.imageUrl ? "" : `ph ${s.bg}`}`}
          >
            {s.imageUrl && (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={s.imageUrl}
                alt={s.label}
                className="h-full w-full object-cover"
                loading="lazy"
              />
            )}
          </button>
        ))}
      </div>
    </div>
  );
}
