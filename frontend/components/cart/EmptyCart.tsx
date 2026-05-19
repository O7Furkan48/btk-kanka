import Link from "next/link";
import { ShoppingCart, ArrowRight } from "lucide-react";

export function EmptyCart() {
  return (
    <div className="mx-auto my-10 max-w-[540px] rounded-2xl border border-slate-200 bg-white px-8 py-16 text-center">
      <div className="relative mb-5 inline-flex h-[88px] w-[88px] items-center justify-center rounded-full bg-indigo-50">
        <ShoppingCart className="h-11 w-11 text-indigo-600" strokeWidth={2} />
        {}
        <span
          aria-hidden
          className="absolute -inset-2 animate-spin-slow rounded-full border-[1.5px] border-dashed border-indigo-200"
        />
      </div>
      <h2 className="mb-2 text-[22px] font-bold tracking-tight text-slate-900">
        Sepetin daha boş, kankana bir bak
      </h2>
      <p className="mb-6 text-sm text-slate-600">
        Sana özel seçtiklerimize göz atmaya ne dersin? AI kankan kombin önerileri için hazır bekliyor.
      </p>
      <Link
        href="/"
        className="inline-flex items-center gap-[6px] rounded-md bg-indigo-600 px-[22px] py-[13px] text-sm font-bold text-white transition hover:-translate-y-0.5 hover:bg-indigo-700"
      >
        Alışverişe Başla
        <ArrowRight className="h-3.5 w-3.5" strokeWidth={2.5} />
      </Link>
    </div>
  );
}
