"use client";

import { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { Star, Plus, Check, Heart, Sparkles, ArrowRight } from "lucide-react";
import type { ProductSummary } from "@/lib/types";
import { useProductRecommended } from "@/lib/queries";
import { useCartStore } from "@/store/cartStore";

export function ProductsSection() {
  const { data, isLoading, isError, error } = useProductRecommended(12);

  if (isError) {

    console.error("Ana sayfa ürünleri yüklenemedi:", error);
  }

  const products: ProductSummary[] = isError ? [] : data ?? [];

  return (
    <section id="products" className="mx-auto max-w-[1280px] px-8 py-14">
      <div className="mb-8 flex items-end justify-between">
        <div>
          <h2 className="text-[36px] font-bold leading-tight tracking-tight text-slate-900">
            Senin İçin Seçtik
            <span className="ml-3 inline-flex items-center gap-[6px] rounded-full bg-indigo-50 px-[11px] py-[5px] pl-2 align-middle text-xs font-semibold text-indigo-600">
              <Sparkles className="h-3 w-3" /> AI seçimi
            </span>
          </h2>
          <p className="mt-2 text-[15px] text-slate-500">
            Geçmiş aramalarına ve bedenine uygun, iade riski düşük 12 ürün.
          </p>
        </div>
        <Link
          href="#"
          className="inline-flex items-center gap-1 text-sm font-semibold text-indigo-600 hover:gap-2 hover:underline"
        >
          Hepsini gör <ArrowRight className="h-4 w-4" />
        </Link>
      </div>

      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {isLoading
          ? Array.from({ length: 12 }).map((_, i) => (
              <ProductCardSkeleton key={i} />
            ))
          : products.map((p) => <ProductCard key={p.slug} product={p} />)}
      </div>
    </section>
  );
}

function ProductCardSkeleton() {

  return (
    <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
      <div className="aspect-square animate-pulse bg-slate-200" />
      <div className="px-[14px] pb-4 pt-[14px]">
        <div className="mb-[6px] h-3 w-16 animate-pulse rounded bg-slate-200" />
        <div className="mb-2 h-4 w-full animate-pulse rounded bg-slate-200" />
        <div className="mb-3 h-4 w-2/3 animate-pulse rounded bg-slate-200" />
        <div className="flex items-center justify-between">
          <div className="h-5 w-20 animate-pulse rounded bg-slate-200" />
          <div className="h-4 w-10 animate-pulse rounded bg-slate-200" />
        </div>
      </div>
    </div>
  );
}

export function ProductCard({ product }: { product: ProductSummary }) {
  const addToCart = useCartStore((s) => s.addItem);
  const [added, setAdded] = useState(false);

  function handleQuickAdd(e: React.MouseEvent<HTMLButtonElement>) {
    e.preventDefault();
    e.stopPropagation();

    const priceNum = parseFloat(product.price.replace(/\./g, "").replace(",", ".")) || 0;
    addToCart({
      id: `${product.slug}__quick`,
      brand: product.brand,
      name: product.name,
      bg: product.bg,
      color: "Standart",
      colorClass: "",
      size: "Standart",
      unitPrice: priceNum,
      quantity: 1,
      nudge: null,
    });
    setAdded(true);
    setTimeout(() => setAdded(false), 1500);
  }

  return (
    <Link
      href={`/urun/${product.slug}`}
      className="group relative block overflow-hidden rounded-lg border border-slate-200 bg-white transition-all duration-200 hover:-translate-y-[3px] hover:border-transparent hover:shadow-lg"
    >
      <div className="relative aspect-square overflow-hidden bg-slate-100">
        {}
        <span
          className={`ph ${product.bg} absolute inset-0 flex items-center justify-center font-mono text-[11px] uppercase tracking-wider text-slate-900/40 transition-transform duration-500 group-hover:scale-105`}
        >
          {product.placeholder}
        </span>

        {}
        {product.imageUrl ? (
          <Image
            src={product.imageUrl}
            alt={product.name}
            fill
            sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 25vw"
            className="object-cover transition-transform duration-500 group-hover:scale-105"
          />
        ) : null}

        {}
        <button
          type="button"
          aria-label="Favorile"
          onClick={(e) => e.preventDefault()}
          className="absolute right-[10px] top-[10px] z-[2] inline-flex h-[34px] w-[34px] scale-[0.85] items-center justify-center rounded-full bg-white/95 text-slate-500 opacity-0 shadow-sm backdrop-blur-sm transition-all hover:bg-white hover:text-red-500 group-hover:scale-100 group-hover:opacity-100"
        >
          <Heart className="h-[17px] w-[17px]" />
        </button>

        {}
        <button
          type="button"
          aria-label={added ? "Sepete eklendi" : "Sepete ekle"}
          onClick={handleQuickAdd}
          className={`absolute bottom-[100px] right-[14px] z-[3] inline-flex h-[38px] w-[38px] items-center justify-center rounded-full text-white transition-all duration-200 hover:scale-110 ${
            added
              ? "scale-100 bg-emerald-600 opacity-100"
              : "translate-y-[6px] scale-[0.85] bg-indigo-600 opacity-0 hover:bg-indigo-700 group-hover:translate-y-0 group-hover:scale-100 group-hover:opacity-100"
          }`}
          style={{
            boxShadow: added
              ? "0 10px 22px -6px rgba(16,185,129,.55)"
              : "0 10px 22px -6px rgba(91,46,255,.55)",
          }}
        >
          {added ? (
            <Check className="h-[18px] w-[18px]" strokeWidth={2.5} />
          ) : (
            <Plus className="h-[18px] w-[18px]" strokeWidth={2.5} />
          )}
        </button>
      </div>

      <div className="px-[14px] pb-4 pt-[14px]">
        <div className="mb-[6px] text-[11px] font-semibold uppercase tracking-wider text-slate-400">
          {product.brand}
        </div>
        <div className="mb-3 line-clamp-2 min-h-[38px] text-sm font-medium leading-snug text-slate-900">
          {product.name}
        </div>
        <div className="flex items-center justify-between">
          <div className="text-lg font-bold tracking-tight text-indigo-600">
            {product.price} ₺
          </div>
          <div className="inline-flex items-center gap-[3px] text-xs font-semibold text-slate-600">
            <Star className="h-3 w-3 fill-amber-500 text-amber-500" strokeWidth={0} />
            {product.rating}
          </div>
        </div>
      </div>
    </Link>
  );
}
