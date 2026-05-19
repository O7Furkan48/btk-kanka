"use client";

import { useCartStore } from "@/store/cartStore";

export function DemoToggle() {

  const itemsLength = useCartStore((s) => s.items.length);
  const loadDemo = useCartStore((s) => s.loadDemo);
  const clearCart = useCartStore((s) => s.clearCart);

  if (process.env.NODE_ENV === "production") return null;

  const isFull = itemsLength > 0;

  return (
    <div className="fixed bottom-7 left-7 z-[60] inline-flex rounded-full border border-slate-200 bg-white p-1 shadow-md">
      <button
        type="button"
        onClick={loadDemo}
        className={`rounded-full px-[14px] py-2 text-xs font-semibold transition ${
          isFull
            ? "bg-indigo-600 text-white"
            : "text-slate-500 hover:text-slate-700"
        }`}
      >
        Dolu sepet
      </button>
      <button
        type="button"
        onClick={clearCart}
        className={`rounded-full px-[14px] py-2 text-xs font-semibold transition ${
          !isFull
            ? "bg-indigo-600 text-white"
            : "text-slate-500 hover:text-slate-700"
        }`}
      >
        Boş sepet
      </button>
    </div>
  );
}
