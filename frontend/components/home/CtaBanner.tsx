"use client";

import { ArrowRight } from "lucide-react";
import { useChatStore } from "@/store/chatStore";

export function CtaBanner() {
  const openChat = useChatStore((s) => s.open);

  return (
    <div className="mx-auto mb-14 mt-4 max-w-[1280px] px-8">
      <div
        className="relative grid grid-cols-1 items-center gap-8 overflow-hidden rounded-[28px] px-16 py-14 text-white md:grid-cols-[1.4fr_1fr]"
        style={{
          background: [
            "radial-gradient(circle at 80% 30%, rgba(151,71,255,.4), transparent 50%)",
            "radial-gradient(circle at 20% 80%, rgba(91,46,255,.3), transparent 50%)",
            "linear-gradient(135deg, #2E1A6B 0%, #4F22E8 100%)",
          ].join(", "),
        }}
      >
        {}
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0"
          style={{
            backgroundImage: [
              "linear-gradient(rgba(255,255,255,.06) 1px, transparent 1px)",
              "linear-gradient(90deg, rgba(255,255,255,.06) 1px, transparent 1px)",
            ].join(", "),
            backgroundSize: "48px 48px",
            maskImage:
              "radial-gradient(ellipse 80% 100% at 100% 50%, black, transparent 70%)",
            WebkitMaskImage:
              "radial-gradient(ellipse 80% 100% at 100% 50%, black, transparent 70%)",
          }}
        />

        <div className="relative">
          <h2 className="mb-3 text-[36px] font-bold leading-tight tracking-tight">
            Kankana sor, doğru bedeni al.
            <br />
            İade derdi sende kalmasın.
          </h2>
          <p className="mb-6 max-w-[460px] text-base leading-relaxed text-white/80">
            Tek bir mesajda boy-kilo-zevk eşleşmesi. 30 saniyede sana uygun ürünü bulur, riskini önden söyler.
          </p>
          <button
            type="button"
            onClick={() => openChat()}
            className="inline-flex h-[52px] items-center gap-2 rounded-md bg-white px-[26px] text-[15px] font-bold text-indigo-700 transition-all hover:-translate-y-px hover:scale-[1.02] hover:bg-indigo-50"
            style={{
              boxShadow:
                "0 8px 22px -8px rgba(91,46,255,.55), inset 0 1px 0 rgba(255,255,255,.18)",
            }}
          >
            Beni tanı, kanka <ArrowRight className="h-4 w-4" strokeWidth={2} />
          </button>
        </div>

        <div className="relative flex flex-col items-end gap-3">
          <CtaChip>
            Sen: <b className="font-bold">Düğüne ne giysem?</b>
          </CtaChip>
          <CtaChip right tinted>
            Açık mavi gömlek + bej chino. %94 senlik.
          </CtaChip>
          <CtaChip>
            Sen: <b className="font-bold">Bu beden bana olur mu?</b>
          </CtaChip>
        </div>
      </div>
    </div>
  );
}

function CtaChip({
  children,
  right,
  tinted,
}: {
  children: React.ReactNode;
  right?: boolean;
  tinted?: boolean;
}) {
  const radius = right ? "rounded-[14px_14px_14px_4px]" : "rounded-[14px_14px_4px_14px]";
  return (
    <div
      className={`${radius} ${
        tinted
          ? "self-start bg-white/95 text-slate-900"
          : "border border-white/15 bg-white/10 text-white backdrop-blur"
      } px-4 py-[10px] text-sm`}
    >
      {children}
    </div>
  );
}
