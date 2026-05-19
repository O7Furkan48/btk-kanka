"use client";

import Link from "next/link";
import { Star, ArrowRight } from "lucide-react";
import { useSimilarProducts } from "@/lib/queries";

export function SimilarProducts({ slug }: { slug: string }) {
  const { data, isLoading, isError } = useSimilarProducts(slug, 4);
  const items = data ?? [];

  return (
    <section className="rounded-lg border border-slate-200 bg-white px-[22px] pb-[22px] pt-6">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-lg font-bold tracking-tight text-slate-900">
          Benzer Ürünler
        </h3>
        <a
          href="#"
          className="inline-flex items-center gap-1 text-sm font-semibold text-indigo-600 hover:gap-2 hover:underline"
        >
          Hepsi <ArrowRight className="h-[14px] w-[14px]" strokeWidth={2.5} />
        </a>
      </div>

      {isLoading && (
        <div className="flex flex-col gap-3">
          {[0, 1, 2, 3].map((i) => (
            <div
              key={i}
              className="grid animate-pulse grid-cols-[72px_1fr] items-center gap-[14px] p-2"
            >
              <div className="aspect-square rounded-[10px] bg-slate-100" />
              <div>
                <div className="mb-2 h-3 w-4/5 rounded bg-slate-100" />
                <div className="h-3 w-1/2 rounded bg-slate-100" />
              </div>
            </div>
          ))}
        </div>
      )}

      {isError && !isLoading && (
        <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          Hımm, benzer ürünler yüklenemedi.
        </div>
      )}

      {!isLoading && !isError && (
        <div className="flex flex-col gap-3">
          {items.map((p, i) => (
            <Link
              key={i}
              href={p.href}
              className="group grid grid-cols-[72px_1fr] items-center gap-[14px] rounded-md border border-transparent p-2 transition-all hover:translate-x-[2px] hover:border-slate-200 hover:bg-slate-50"
            >
              <div
                className={`relative aspect-square overflow-hidden rounded-[10px] ${
                  p.imageUrl ? "bg-slate-100" : `ph ${p.bg}`
                }`}
              >
                {p.imageUrl && (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={p.imageUrl}
                    alt={`${p.brand} ${p.name}`}
                    className="h-full w-full object-cover"
                    loading="lazy"
                  />
                )}
              </div>
              <div className="min-w-0">
                <div className="mb-[6px] line-clamp-2 text-[13px] leading-snug text-slate-800">
                  <b className="font-bold text-slate-900">{p.brand}</b> {p.name}
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-bold tracking-tight text-indigo-600">
                    {p.price} ₺
                  </span>
                  <span className="inline-flex items-center gap-[3px] text-[11.5px] font-semibold text-slate-600">
                    <Star
                      className="h-[11px] w-[11px] fill-amber-500 text-amber-500"
                      strokeWidth={0}
                    />
                    {p.rating}
                  </span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </section>
  );
}
