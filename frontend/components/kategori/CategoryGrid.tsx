"use client";

import { useState } from "react";
import { useProductRecommended } from "@/lib/queries";
import { ProductCard } from "@/components/home/ProductsSection";
import type { ProductSummary } from "@/lib/types";

interface Props {
  initial: ProductSummary[];
  categoryKey: string;
}

export function CategoryGrid({ initial, categoryKey }: Props) {
  const [limit, setLimit] = useState(24);
  const { data, isFetching } = useProductRecommended(limit, categoryKey || undefined);

  const items = data ?? initial;

  return (
    <>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {items.map((p) => (
          <ProductCard key={p.slug} product={p} />
        ))}
      </div>
      {items.length >= limit && limit < 48 && (
        <div className="mt-6 flex justify-center">
          <button
            type="button"
            onClick={() => setLimit((n) => Math.min(n + 12, 48))}
            disabled={isFetching}
            className="rounded-full border border-slate-300 px-6 py-2.5 text-sm font-medium hover:bg-slate-50 disabled:opacity-50"
          >
            {isFetching ? "Yükleniyor…" : "Daha fazla göster"}
          </button>
        </div>
      )}
    </>
  );
}
