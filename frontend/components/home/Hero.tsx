import Link from "next/link";
import { Sparkles, ArrowRight, MessageCircle, Ruler, RotateCcw, Shirt, Star } from "lucide-react";
import type { HeroBubble } from "@/lib/types";
import { HERO_BUBBLES } from "@/lib/homeMockData";

export function Hero() {
  return (
    <section
      className="relative overflow-hidden"
      style={{
        background: [
          "radial-gradient(ellipse 80% 60% at 80% 20%, rgba(124,92,255,.14) 0%, transparent 60%)",
          "radial-gradient(ellipse 60% 50% at 20% 80%, rgba(245,243,255,.8) 0%, transparent 60%)",
          "linear-gradient(180deg, var(--indigo-50) 0%, #FAFAFF 100%)",
        ].join(", "),
      }}
    >
      {}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0"
        style={{
          backgroundImage: [
            "linear-gradient(rgba(91,46,255,.04) 1px, transparent 1px)",
            "linear-gradient(90deg, rgba(91,46,255,.04) 1px, transparent 1px)",
          ].join(", "),
          backgroundSize: "64px 64px",
          maskImage:
            "radial-gradient(ellipse 70% 60% at 50% 50%, black 30%, transparent 80%)",
          WebkitMaskImage:
            "radial-gradient(ellipse 70% 60% at 50% 50%, black 30%, transparent 80%)",
        }}
      />

      <div className="relative mx-auto grid min-h-[520px] max-w-[1280px] grid-cols-1 items-center gap-16 px-8 py-22 md:grid-cols-2">
        {}
        <div>
          <span className="mb-6 inline-flex items-center gap-2 rounded-full border border-indigo-600/20 bg-white/75 py-[6px] pl-2 pr-[14px] text-[13px] font-medium text-slate-700">
            <span
              className="inline-flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full text-white"
              style={{ background: "linear-gradient(135deg, #7C5CFF, #5B2EFF)" }}
            >
              <Sparkles className="h-[11px] w-[11px]" />
            </span>
            Yapay zeka destekli alışveriş
          </span>

          <h1
            className="mb-[18px] text-[clamp(40px,5vw,64px)] font-bold leading-[1.02] tracking-tight text-slate-900"
          >
            Alışverişin{" "}
            <span
              className="bg-clip-text text-transparent"
              style={{
                backgroundImage:
                  "linear-gradient(120deg, #5B2EFF 0%, #9747FF 50%, #5B2EFF 100%)",
                backgroundSize: "200% auto",
                animation: "shimmer 6s ease-in-out infinite",
              }}
            >
              kankası
            </span>{" "}
            geldi.
          </h1>

          <p className="mb-8 max-w-[480px] text-lg leading-relaxed text-slate-600">
            Her ürünün altında sana özel akıl. Sor, dene, dert etme.
            Bedeninden iade riskine, kombininden kumaşına — kankana sor.
          </p>

          <div className="mb-9 flex flex-wrap items-center gap-3">
            <Link
              href="#products"
              className="inline-flex h-[52px] items-center gap-2 rounded-md bg-indigo-600 px-[26px] text-[15px] font-semibold text-white transition-all hover:-translate-y-px hover:scale-[1.02] hover:bg-indigo-700"
              style={{
                boxShadow:
                  "0 8px 22px -8px rgba(91,46,255,.55), inset 0 1px 0 rgba(255,255,255,.18)",
              }}
            >
              Hemen Keşfet <ArrowRight className="h-4 w-4" strokeWidth={2} />
            </Link>
            <Link
              href="#how"
              className="inline-flex h-[52px] items-center gap-2 rounded-md border-[1.5px] border-slate-200 bg-white px-[22px] text-[15px] font-semibold text-slate-900 transition-all hover:-translate-y-px hover:border-slate-400"
            >
              <MessageCircle className="h-4 w-4" strokeWidth={2} />
              Nasıl çalışır?
            </Link>
          </div>

          <div className="flex flex-wrap gap-[18px] text-[13px] font-medium text-slate-500">
            <TrustItem icon={<Ruler className="h-[14px] w-[14px] text-indigo-600" strokeWidth={2} />}>
              Akıllı beden önerisi
            </TrustItem>
            <TrustItem icon={<RotateCcw className="h-[14px] w-[14px] text-indigo-600" strokeWidth={2} />}>
              İade riski hesaplama
            </TrustItem>
            <TrustItem icon={<Shirt className="h-[14px] w-[14px] text-indigo-600" strokeWidth={2} />}>
              Senaryolu kombin
            </TrustItem>
          </div>
        </div>

        {}
        <div className="relative h-[460px]">
          {HERO_BUBBLES.map((b) => (
            <FloatBubble key={b.position} bubble={b} />
          ))}

          {}
          <div
            className="absolute right-10 top-[30px] w-[320px] rounded-[22px] bg-white p-[18px]"
            style={{
              boxShadow:
                "0 30px 60px -20px rgba(46,26,107,.25), 0 8px 20px -8px rgba(15,23,42,.1)",
              transform: "rotate(-2.5deg)",
              animation: "cardFloat 7s ease-in-out infinite",
            }}
          >
            <div className="relative h-[280px] overflow-hidden rounded-2xl ph-bg-1">
              <span className="absolute left-[14px] top-[14px] inline-flex items-center gap-1 rounded-full bg-white/95 px-[10px] py-[5px] text-[11px] font-bold text-green-500">
                <span aria-hidden className="h-[6px] w-[6px] rounded-full bg-green-500" />
                %12 İade Riski
              </span>
              <span
                className="absolute right-[14px] top-[14px] inline-flex items-center gap-1 rounded-full py-[5px] pl-[7px] pr-[10px] text-[11px] font-bold text-white"
                style={{
                  background: "linear-gradient(135deg, #7C5CFF, #5B2EFF)",
                  boxShadow: "0 4px 12px -2px rgba(91,46,255,.4)",
                }}
              >
                <Sparkles className="h-3 w-3" /> AI
              </span>
              <span className="absolute bottom-[14px] left-[14px] font-mono text-[11px] uppercase tracking-wider text-slate-900/50">
                T-Shirt · Oversize
              </span>
            </div>
            <div className="px-1 pt-[14px]">
              <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                Tudors
              </div>
              <div className="mt-1 text-sm font-medium leading-snug text-slate-900">
                Unisex Oversize Pamuk Bisiklet Yaka Beyaz Tişört
              </div>
              <div className="mt-[10px] flex items-center justify-between">
                <div className="text-lg font-bold text-indigo-600">414,98 ₺</div>
                <div className="inline-flex items-center gap-[3px] text-xs font-semibold text-slate-600">
                  <Star className="h-3 w-3 fill-amber-500 text-amber-500" strokeWidth={0} />
                  4.7
                </div>
              </div>
            </div>
          </div>

          {}
          <div
            className="absolute bottom-7 right-[30px] max-w-[220px] rounded-[18px_18px_4px_18px] px-4 py-3 text-[13.5px] font-medium leading-snug text-white"
            style={{
              background: "linear-gradient(135deg, #5B2EFF, #7C5CFF)",
              boxShadow: "0 14px 32px -10px rgba(91,46,255,.45)",
              animation: "bubbleFloat 5.5s ease-in-out infinite -2s",
            }}
          >
            <span className="mb-[3px] block text-[10.5px] font-bold uppercase tracking-wider opacity-75">
              Kanka diyor ki
            </span>
            182cm 80kg için <b>L beden</b> %92 isabetli görünüyor.
          </div>
        </div>
      </div>
    </section>
  );
}

function TrustItem({
  icon,
  children,
}: {
  icon: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <span className="inline-flex items-center gap-[6px]">
      {icon}
      {children}
    </span>
  );
}

function FloatBubble({ bubble }: { bubble: HeroBubble }) {

  const layout =
    bubble.position === 1
      ? "left-[10px] top-5"
      : bubble.position === 2
        ? "-left-[10px] top-[180px]"
        : "left-[30px] bottom-[60px]";
  const delay = bubble.position === 2 ? "-1.5s" : bubble.position === 3 ? "-3s" : "0s";
  const dur = bubble.position === 1 ? "5s" : bubble.position === 2 ? "6s" : "6.5s";

  const isTinted = bubble.position === 2;
  return (
    <div
      className={`absolute ${layout} inline-flex items-center gap-2 rounded-[18px] px-4 py-3 text-[13.5px] font-medium text-slate-800 whitespace-nowrap`}
      style={{
        background: isTinted
          ? "linear-gradient(135deg, #F5F3FF 0%, #EDE9FE 100%)"
          : "white",
        border: isTinted ? "1px solid rgba(91,46,255,.15)" : undefined,
        boxShadow:
          "0 12px 30px -10px rgba(46,26,107,.22), 0 4px 10px -4px rgba(15,23,42,.08)",
        animation: `bubbleFloat ${dur} ease-in-out infinite ${delay}`,
      }}
    >
      <span
        aria-hidden
        className="h-[22px] w-[22px] flex-shrink-0 rounded-full"
        style={{
          background: isTinted
            ? "white"
            : "linear-gradient(135deg, #7C5CFF, #5B2EFF)",
          border: isTinted ? "2px solid #5B2EFF" : undefined,
          boxShadow: isTinted ? undefined : "0 2px 6px -1px rgba(91,46,255,.4)",
        }}
      />
      {bubble.text}
    </div>
  );
}
