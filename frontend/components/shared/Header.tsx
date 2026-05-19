"use client";

import Link from "next/link";
import { Search, Heart, ShoppingCart, User } from "lucide-react";
import { Logo } from "./Logo";
import { AdminToggle } from "./AdminToggle";
import { useCartStore } from "@/store/cartStore";

const NAV_LINKS = [
  { label: "Kadın Giyim", href: "#kadin" },
  { label: "Erkek Giyim", href: "#erkek" },
  { label: "Ev", href: "#ev" },
  { label: "Kozmetik", href: "#kozmetik" },
] as const;

export function Header() {

  const cartCount = useCartStore((s) =>
    s.items.reduce((sum, it) => sum + it.quantity, 0),
  );

  return (
    <header className="sticky top-0 z-50 border-b border-slate-200 bg-white/85 backdrop-blur-md backdrop-saturate-[180%]">
      <div className="mx-auto grid max-w-[1280px] grid-cols-[auto_1fr_auto] items-center gap-7 px-8 py-[14px]">
        <Logo />

        {}
        <div className="relative w-full max-w-[560px] justify-self-center">
          <Search
            className="pointer-events-none absolute left-4 top-1/2 h-[18px] w-[18px] -translate-y-1/2 text-slate-400"
            strokeWidth={2}
          />
          <input
            type="search"
            placeholder="Bugün ne arıyorsun?"
            className="h-11 w-full rounded-full border-[1.5px] border-slate-200 bg-white pl-[46px] pr-[68px] text-[14.5px] text-slate-900 placeholder:text-slate-400 transition focus:border-indigo-600 focus:shadow-glow focus:outline-none"
          />
          <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 rounded-md bg-slate-100 px-[7px] py-[3px] text-[11px] font-semibold tracking-wider text-slate-400">
            ⌘ K
          </span>
        </div>

        {}
        <nav className="flex items-center gap-1">
          <div className="hidden items-center gap-1 lg:flex">
            {NAV_LINKS.map((l) => (
              <Link
                key={l.href}
                href={l.href}
                className="rounded-lg px-3 py-2 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-100 hover:text-slate-900"
              >
                {l.label}
              </Link>
            ))}
            <span aria-hidden className="mx-2 h-[22px] w-px bg-slate-200" />
          </div>

          <AdminToggle />

          <IconBtn aria-label="Favoriler">
            <Heart className="h-5 w-5" strokeWidth={2} />
          </IconBtn>

          <Link
            href="/cart"
            aria-label="Sepetim"
            className="relative inline-flex h-10 w-10 items-center justify-center rounded-[10px] text-slate-700 transition-colors hover:bg-slate-100 hover:text-slate-900"
          >
            <ShoppingCart className="h-5 w-5" strokeWidth={2} />
            {cartCount > 0 && (
              <span
                suppressHydrationWarning
                className="absolute right-1 top-1 inline-flex h-[18px] min-w-[18px] items-center justify-center rounded-full border-2 border-white bg-indigo-600 px-[5px] text-[11px] font-bold text-white"
              >
                {cartCount}
              </span>
            )}
          </Link>

          <IconBtn aria-label="Hesabım">
            <User className="h-5 w-5" strokeWidth={2} />
          </IconBtn>
        </nav>
      </div>
    </header>
  );
}

function IconBtn({
  children,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      type="button"
      className="inline-flex h-10 w-10 items-center justify-center rounded-[10px] text-slate-700 transition-colors hover:bg-slate-100 hover:text-slate-900"
      {...props}
    >
      {children}
    </button>
  );
}
