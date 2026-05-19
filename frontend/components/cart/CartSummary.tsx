import { Truck, Tag, Lock, Sparkles, ArrowRight } from "lucide-react";
import type { CartItem } from "@/lib/types";
import { formatTRY } from "@/lib/format";

interface Props {
  items: CartItem[];
  couponApplied: boolean;
  couponDiscount: number;
  couponCode?: string;
}

const FREE_SHIPPING_THRESHOLD = 500;
const SHIPPING_FEE = 39.9;

export function CartSummary({
  items,
  couponApplied,
  couponDiscount,
  couponCode,
}: Props) {
  const subtotal = items.reduce(
    (s, it) => s + it.unitPrice * it.quantity,
    0,
  );
  const shipping = subtotal >= FREE_SHIPPING_THRESHOLD ? 0 : SHIPPING_FEE;
  const discount = couponApplied ? couponDiscount : 0;
  const total = subtotal + shipping - discount;
  const saved =
    (couponApplied ? couponDiscount : 0) +
    (shipping === 0 ? SHIPPING_FEE : 0);

  const itemCount = items.length;
  const totalQty = items.reduce((s, it) => s + it.quantity, 0);

  return (
    <aside className="static overflow-hidden rounded-lg border border-slate-200 bg-white shadow-md md:sticky md:top-[92px]">
      <div className="border-b border-slate-100 px-5 pb-[14px] pt-[18px]">
        <h3 className="text-base font-bold tracking-tight text-slate-900">
          Sipariş Özeti
        </h3>
        <div className="mt-[3px] text-xs text-slate-500">
          {itemCount} ürün · {totalQty} adet
        </div>
      </div>

      <div className="flex flex-col gap-[10px] px-5 py-[14px]">
        <Row label={<>Ara toplam</>} value={formatTRY(subtotal)} />
        <Row
          label={
            <>
              <Truck className="h-3.5 w-3.5 text-slate-400" strokeWidth={2} />
              Kargo
            </>
          }
          value={shipping === 0 ? "Ücretsiz" : formatTRY(shipping)}
          highlight={shipping === 0}
        />
        {couponApplied && (
          <Row
            label={
              <>
                <Tag className="h-3.5 w-3.5 text-slate-400" strokeWidth={2} />
                Kupon ({couponCode ?? "KUPON"})
              </>
            }
            value={`−${formatTRY(couponDiscount)}`}
            highlight
          />
        )}
        <div className="my-1 h-px bg-slate-100" />
      </div>

      <div className="flex items-baseline justify-between px-5 pb-1 pt-4">
        <span className="text-sm font-semibold text-slate-700">Toplam</span>
        <span className="text-right">
          <span className="text-[26px] font-extrabold tracking-tight tabular-nums text-indigo-600">
            {formatTRY(total)}
          </span>
          <span className="mt-[1px] block text-[10.5px] font-medium text-slate-500">
            KDV dahil
          </span>
        </span>
      </div>

      {saved > 0 && (
        <div className="mx-5 mt-2 flex items-center gap-[6px] rounded-[10px] bg-green-50 px-3 py-[9px] text-xs font-bold text-[#047857]">
          <Sparkles className="h-3 w-3" />
          Bu siparişte {formatTRY(saved)} tasarruf
        </div>
      )}

      <button
        type="button"
        className="mx-5 my-[14px] inline-flex h-[52px] w-[calc(100%-2.5rem)] items-center justify-center gap-2 rounded-xl bg-indigo-600 text-[15px] font-bold text-white transition hover:-translate-y-px hover:bg-indigo-700"
        style={{ boxShadow: "0 8px 20px -6px rgba(91,46,255,.4)" }}
      >
        Siparişi Tamamla
        <ArrowRight className="h-4 w-4" strokeWidth={2.5} />
      </button>

      <div className="flex items-center justify-center gap-[5px] px-5 pb-4 text-center text-[11.5px] text-slate-500">
        <Lock className="h-3 w-3 text-green-500" strokeWidth={2} />
        256-bit SSL ile güvenli ödeme
      </div>

      <div className="flex items-center justify-center gap-2 border-t border-slate-100 bg-slate-50 px-5 py-3">
        {["VISA", "MC", "TROY", "AMEX"].map((p) => (
          <span
            key={p}
            className="inline-flex h-[18px] items-center rounded bg-white px-2 text-[9.5px] font-extrabold tracking-wider text-slate-700 ring-1 ring-slate-200"
          >
            {p}
          </span>
        ))}
      </div>
    </aside>
  );
}

function Row({
  label,
  value,
  highlight,
}: {
  label: React.ReactNode;
  value: React.ReactNode;
  highlight?: boolean;
}) {
  return (
    <div className="flex items-center justify-between text-[13.5px] text-slate-700">
      <span className="inline-flex items-center gap-[6px]">{label}</span>
      <span
        className={`font-semibold tabular-nums ${
          highlight ? "text-[#047857]" : "text-slate-900"
        }`}
      >
        {value}
      </span>
    </div>
  );
}
