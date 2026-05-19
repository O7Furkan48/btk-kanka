"use client";

import { Plus, Minus, Trash2 } from "lucide-react";
import { motion } from "motion/react";
import type { CartItem } from "@/lib/types";
import { formatTRY } from "@/lib/format";
import { useCartStore } from "@/store/cartStore";
import { AINudge } from "./AINudge";

export function CartItemRow({ item }: { item: CartItem }) {
  const updateQuantity = useCartStore((s) => s.updateQuantity);
  const removeItem = useCartStore((s) => s.removeItem);

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8, scale: 0.96 }}
      transition={{ duration: 0.22, ease: [0.2, 0.8, 0.2, 1] }}
      className="group relative grid grid-cols-[100px_1fr_auto] items-center gap-4 rounded-lg border border-slate-200 bg-white p-4 transition hover:shadow-md"
    >
      <div
        className={`ph ${item.bg} relative h-[100px] w-[100px] overflow-hidden rounded-md`}
      />

      <div className="min-w-0">
        <span className="mb-[6px] inline-block rounded-md bg-indigo-50 px-2 py-[3px] text-[11px] font-bold tracking-wide text-indigo-700">
          {item.brand}
        </span>
        <div className="mb-2 line-clamp-2 text-sm font-medium leading-snug text-slate-900">
          {item.name}
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Chip>
            <ColorDot cls={item.colorClass} />
            {item.color}
          </Chip>
          <Chip>
            Beden: <b className="text-slate-900">{item.size}</b>
          </Chip>
        </div>
        <div className="mt-[10px] inline-flex h-[34px] items-center overflow-hidden rounded-[10px] border-[1.5px] border-slate-200 bg-white">
          <QtyBtn
            onClick={() => updateQuantity(item.id, -1)}
            disabled={item.quantity <= 1}
            label="Azalt"
          >
            <Minus className="h-3.5 w-3.5" strokeWidth={2.5} />
          </QtyBtn>
          <span className="inline-block min-w-[32px] text-center text-[13.5px] font-bold tabular-nums text-slate-900">
            {item.quantity}
          </span>
          <QtyBtn
            onClick={() => updateQuantity(item.id, +1)}
            label="Arttır"
          >
            <Plus className="h-3.5 w-3.5" strokeWidth={2.5} />
          </QtyBtn>
        </div>
      </div>

      <div className="flex h-full flex-col items-end justify-between gap-[6px] self-stretch">
        <button
          type="button"
          aria-label="Sepetten kaldır"
          onClick={() => removeItem(item.id)}
          className="inline-flex h-8 w-8 items-center justify-center rounded-lg text-slate-400 opacity-0 transition-all hover:scale-105 hover:bg-red-50 hover:text-red-500 group-hover:opacity-100"
        >
          <Trash2 className="h-4 w-4" />
        </button>
        <div className="text-right">
          <div className="text-[17px] font-bold tracking-tight tabular-nums text-slate-900">
            {formatTRY(item.unitPrice * item.quantity)}
          </div>
          {item.quantity > 1 && (
            <div className="text-[11px] text-slate-500">
              {item.quantity}× {formatTRY(item.unitPrice)}
            </div>
          )}
        </div>
      </div>

      {item.nudge && <AINudge nudge={item.nudge} />}
    </motion.div>
  );
}

function Chip({ children }: { children: React.ReactNode }) {
  return (
    <span className="inline-flex items-center gap-[5px] rounded-full bg-slate-100 px-[9px] py-1 text-[11.5px] font-semibold text-slate-700">
      {children}
    </span>
  );
}

function ColorDot({ cls }: { cls: string }) {

  const bg =
    cls === "black"
      ? "bg-[#111]"
      : cls === "beige"
        ? "bg-[#D6C7A8]"
        : "bg-white";
  const border =
    cls === "black"
      ? "border-[#111]"
      : cls === "beige"
        ? "border-[#C4B795]"
        : "border-slate-300";
  return (
    <span
      aria-hidden
      className={`inline-block h-2 w-2 rounded-full border ${bg} ${border}`}
    />
  );
}

function QtyBtn({
  children,
  label,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & { label: string }) {
  return (
    <button
      type="button"
      aria-label={label}
      className="inline-flex h-8 w-8 items-center justify-center text-slate-600 transition hover:bg-slate-100 hover:text-indigo-600 disabled:cursor-not-allowed disabled:opacity-35"
      {...props}
    >
      {children}
    </button>
  );
}
