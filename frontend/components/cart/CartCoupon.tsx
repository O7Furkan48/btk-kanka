"use client";

import { useState } from "react";
import { Tag, Check, Loader2 } from "lucide-react";

interface Props {
  applied: boolean;
  appliedCode?: string;
  appliedDiscount?: number;
  loading?: boolean;
  errorMessage?: string | null;
  onApply: (code: string) => void;
}

export function CartCoupon({
  applied,
  appliedCode,
  appliedDiscount,
  loading,
  errorMessage,
  onApply,
}: Props) {
  const [code, setCode] = useState("");

  const submit = () => {
    const trimmed = code.trim();
    if (!trimmed || loading) return;
    onApply(trimmed);
  };

  return (
    <div className="mt-4 flex flex-wrap items-center gap-3 rounded-lg border-[1.5px] border-dashed border-slate-200 bg-white p-4">
      <span className="inline-flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-indigo-50 text-indigo-600">
        <Tag className="h-4 w-4" strokeWidth={2} />
      </span>
      {applied ? (
        <div>
          <div className="text-xs font-semibold text-slate-500">
            Kupon uygulandı
          </div>
          <span className="mt-[2px] inline-flex items-center gap-[6px] rounded-full bg-green-50 px-[11px] py-[6px] text-[12px] font-bold text-[#047857]">
            <Check className="h-3 w-3" strokeWidth={2.5} />
            {(appliedCode ?? "KUPON").toUpperCase()} ·{" "}
            {(appliedDiscount ?? 0).toLocaleString("tr-TR", {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            })}{" "}
            ₺ indirim
          </span>
        </div>
      ) : (
        <>
          <div className="flex flex-col">
            <span className="text-xs font-semibold text-slate-500">
              İndirim kuponu
            </span>
          </div>
          <div className="flex flex-1 min-w-[200px] flex-col gap-1">
            <div className="flex gap-2">
              <input
                type="text"
                placeholder="Kupon kodunu yazın"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    submit();
                  }
                }}
                disabled={loading}
                className="h-[38px] min-w-0 flex-1 rounded-[10px] border-[1.5px] border-slate-200 bg-slate-50 px-[14px] text-[13px] font-semibold uppercase tracking-wider text-slate-900 placeholder:font-medium placeholder:normal-case placeholder:tracking-normal placeholder:text-slate-400 focus:border-indigo-600 focus:bg-white focus:outline-none disabled:opacity-60"
              />
              <button
                type="button"
                onClick={submit}
                disabled={loading || code.trim().length === 0}
                className="inline-flex h-[38px] min-w-[88px] items-center justify-center gap-[6px] rounded-[10px] bg-slate-900 px-4 text-[13px] font-semibold text-white transition hover:-translate-y-px hover:bg-indigo-600 disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:translate-y-0 disabled:hover:bg-slate-900"
              >
                {loading ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" strokeWidth={2.5} />
                ) : (
                  "Uygula"
                )}
              </button>
            </div>
            {errorMessage && (
              <span
                role="alert"
                className="text-[11.5px] font-semibold text-red-500"
              >
                {errorMessage}
              </span>
            )}
          </div>
        </>
      )}
    </div>
  );
}
