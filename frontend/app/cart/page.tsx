"use client";

import Link from "next/link";
import { useState } from "react";
import { AnimatePresence } from "motion/react";
import { ArrowLeft } from "lucide-react";

import { Header } from "@/components/shared/Header";
import { Footer } from "@/components/shared/Footer";
import { CheckoutSteps } from "@/components/cart/CheckoutSteps";
import { CartItemRow } from "@/components/cart/CartItemRow";
import { CartCoupon } from "@/components/cart/CartCoupon";
import { CartSummary } from "@/components/cart/CartSummary";
import { EmptyCart } from "@/components/cart/EmptyCart";
import { ComboSuggestions } from "@/components/cart/ComboSuggestions";
import { DemoToggle } from "@/components/cart/DemoToggle";
import { useCartStore } from "@/store/cartStore";
import { useCouponMutation } from "@/lib/queries";

export default function CartPage() {
  const items = useCartStore((s) => s.items);
  const lastProductSlug = useCartStore((s) => s.lastProductSlug);
  const [appliedCode, setAppliedCode] = useState<string | null>(null);
  const [appliedDiscount, setAppliedDiscount] = useState<number>(0);
  const [couponError, setCouponError] = useState<string | null>(null);

  const continueHref = lastProductSlug ? `/urun/${lastProductSlug}` : "/";

  const couponMutation = useCouponMutation();

  const applyCoupon = (code: string) => {
    const trimmed = code.trim();
    if (!trimmed) return;
    setCouponError(null);
    couponMutation.mutate(
      { code: trimmed.toUpperCase() },
      {
        onSuccess: (res) => {
          if (res.valid && res.discount != null) {
            setAppliedCode(trimmed.toUpperCase());
            setAppliedDiscount(res.discount);
            setCouponError(null);
          } else {
            setCouponError(res.message || "Bu kupon kodu geçerli değil.");
          }
        },
        onError: (err) => {
          setCouponError(
            err.message || "Bu kupon kodu geçerli değil veya süresi dolmuş.",
          );
        },
      },
    );
  };

  const couponApplied = appliedCode !== null;
  const isEmpty = items.length === 0;

  return (
    <>
      <Header />
      <main className="mx-auto w-full max-w-[1140px] flex-1 px-7 pb-20 pt-8">
        <CheckoutSteps />

        {isEmpty ? (
          <EmptyCart />
        ) : (
          <div className="grid items-start gap-7 md:grid-cols-[1fr_380px]">
            <section>
              <div className="mb-4 flex items-baseline justify-between">
                <h1 className="text-2xl font-bold tracking-tight text-slate-900">
                  Sepetim{" "}
                  <span className="text-sm font-medium text-slate-500">
                    · {items.length} ürün
                  </span>
                </h1>
              </div>

              <div className="flex flex-col gap-3">
                <AnimatePresence initial={false}>
                  {items.map((item) => (
                    <CartItemRow key={item.id} item={item} />
                  ))}
                </AnimatePresence>
              </div>

              <CartCoupon
                applied={couponApplied}
                appliedCode={appliedCode ?? undefined}
                appliedDiscount={appliedDiscount}
                loading={couponMutation.isPending}
                errorMessage={couponError}
                onApply={applyCoupon}
              />

              <Link
                href={continueHref}
                className="mt-[18px] inline-flex items-center gap-[6px] text-[13px] font-semibold text-indigo-600 hover:text-indigo-700 hover:underline"
              >
                <ArrowLeft className="h-3.5 w-3.5" strokeWidth={2.2} />
                {lastProductSlug ? "Son baktığın ürüne dön" : "Alışverişe devam et"}
              </Link>
            </section>

            <CartSummary
              items={items}
              couponApplied={couponApplied}
              couponCode={appliedCode ?? undefined}
              couponDiscount={appliedDiscount}
            />
          </div>
        )}

        {!isEmpty && <ComboSuggestions items={items} />}
      </main>
      <DemoToggle />
      <Footer />
    </>
  );
}
