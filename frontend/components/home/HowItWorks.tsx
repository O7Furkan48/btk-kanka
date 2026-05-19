import { Sparkles, Ruler, Shirt } from "lucide-react";
import type { HowItWorksFeature } from "@/lib/types";
import { HOW_FEATURES } from "@/lib/homeMockData";

const ICONS = {
  spark: Sparkles,
  ruler: Ruler,
  hanger: Shirt,
} as const;

export function HowItWorks() {
  return (
    <section
      id="how"
      className="pb-18"
      style={{
        background: [
          "radial-gradient(ellipse 50% 70% at 50% 0%, rgba(245,243,255,.7), transparent 70%)",
          "var(--slate-50)",
        ].join(", "),
      }}
    >
      <div className="mx-auto max-w-[1280px] px-8 py-14">
        <div className="mb-9 text-center">
          <h2 className="mb-2 text-[36px] font-bold leading-tight tracking-tight text-slate-900">
            Kanka Nasıl Çalışır?
          </h2>
          <p className="text-[15px] text-slate-500">
            Üç sade özellik. Her ürün sayfasında, alışverişin bütün stresini alıyor.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-5 md:grid-cols-3">
          {HOW_FEATURES.map((f) => (
            <FeatureCard key={f.num} feature={f} />
          ))}
        </div>
      </div>
    </section>
  );
}

function FeatureCard({ feature }: { feature: HowItWorksFeature }) {
  const Icon = ICONS[feature.icon];
  return (
    <article className="group relative overflow-hidden rounded-lg border border-slate-200 bg-white px-7 pb-8 pt-[30px] transition-all duration-300 hover:-translate-y-1 hover:rotate-[-0.4deg] hover:shadow-xl">
      <span className="absolute right-6 top-[22px] font-mono text-[13px] font-bold tracking-wider text-slate-300">
        {feature.num}
      </span>
      <div
        className="relative mb-5 flex h-[52px] w-[52px] items-center justify-center rounded-[14px] border border-indigo-100 text-indigo-600"
        style={{
          background: "linear-gradient(135deg, var(--indigo-50), white)",
        }}
      >
        <Icon className="h-[26px] w-[26px]" strokeWidth={2} />
        <span
          aria-hidden
          className="absolute inset-[6px] -z-10 rounded-[10px]"
          style={{
            background:
              "linear-gradient(135deg, rgba(91,46,255,.0), rgba(91,46,255,.06))",
          }}
        />
      </div>
      <h3 className="mb-2 text-[19px] font-bold tracking-tight text-slate-900">
        {feature.title}
      </h3>
      <p className="text-[14.5px] leading-relaxed text-slate-600">
        {feature.description}
      </p>
      <div className="mt-5 flex items-start gap-2 border-t border-dashed border-slate-200 pt-[18px] text-[12.5px] italic text-slate-500">
        <span
          className="-mt-1 font-serif text-2xl font-bold not-italic leading-none text-indigo-500"
          aria-hidden
        >
          &ldquo;
        </span>
        {feature.example}
      </div>
    </article>
  );
}
