"use client";

import { useMemo } from "react";
import { TrendingUp, AlertTriangle, Lightbulb, Tag } from "lucide-react";
import { useAdminStore } from "@/store/adminStore";
import type { Product } from "@/lib/types";

interface Insight {
  icon: React.ComponentType<{ className?: string }>;
  tone: "warn" | "info" | "ok";
  title: string;
  body: string;
}

function buildInsights(product: Product): Insight[] {
  const out: Insight[] = [];
  const riskPct = product.risk.percent;
  const topBar = product.risk.bars[0];
  const negCnt = product.reviewCounts.negative ?? 0;
  const allCnt = product.reviewCounts.all ?? product.reviewCount;
  const negRate = allCnt > 0 ? negCnt / allCnt : 0;
  const isErkek = (product.category[0]?.label || "").toLowerCase().includes("erkek");
  const isKadin = (product.category[0]?.label || "").toLowerCase().includes("kadın");
  const cinsiyet = isErkek ? "erkek" : isKadin ? "kadın" : "müşteri";
  const parcaTipi = (product.category[product.category.length - 1]?.label || "")
    .replace(/Erkek\s*|Kadın\s*|Unisex\s*/gi, "")
    .trim()
    .toLowerCase() || "ürün";

  if (riskPct >= 25) {
    out.push({
      icon: AlertTriangle,
      tone: "warn",
      title: "İade riski yüksek",
      body: `%${riskPct} iade riski. ${
        topBar ? `En çok şikayet: ${topBar.label.toLowerCase()} (%${topBar.value}).` : ""
      } Açıklamayı güncelleyerek beklenti yönetimini iyileştirebilirsin.`,
    });
  } else if (riskPct >= 12) {
    out.push({
      icon: AlertTriangle,
      tone: "warn",
      title: "Orta seviye iade riski",
      body: `%${riskPct} iade. ${
        topBar ? `En öne çıkan konu: ${topBar.label.toLowerCase()}.` : ""
      } Görsel + ölçü tablosu netleştirilebilir.`,
    });
  }

  out.push({
    icon: Lightbulb,
    tone: "info",
    title: "AI'a sorulan kombin trendleri",
    body: `Son hafta kullanıcılar bu ${parcaTipi} için en çok "${
      parcaTipi.includes("ceket") ? "kumaş pantolon" :
      parcaTipi.includes("pantolon") ? "üst gömlek" :
      parcaTipi.includes("tişört") || parcaTipi.includes("gömlek") ? "uyumlu pantolon" :
      parcaTipi.includes("elbise") ? "topuklu ayakkabı" :
      parcaTipi.includes("ayakkabı") || parcaTipi.includes("sneaker") ? "denim/kumaş pantolon" :
      "kombin parçaları"
    }" önerisi istemiş. Mağazana uyumlu ${cinsiyet} parçaları eklemek satışı artırabilir.`,
  });

  if (product.risk.satisfaction >= 85) {
    out.push({
      icon: TrendingUp,
      tone: "ok",
      title: "Güçlü memnuniyet skoru",
      body: `%${product.risk.satisfaction} memnuniyet (${product.risk.reviewCount.toLocaleString("tr-TR")} yorumdan). Bu ürünü "Öne çıkan" rozetiyle vitrin alanında destekleyebilirsin.`,
    });
  } else if (negRate >= 0.15) {
    out.push({
      icon: TrendingUp,
      tone: "warn",
      title: "Negatif yorum oranı yüksek",
      body: `Yorumların %${Math.round(negRate * 100)}'i negatif. Kanıt: "${topBar?.label ?? "kalite"}" ana şikayet. Satıcıyla iletişime geç.`,
    });
  }

  return out;
}

const TONE_STYLES: Record<Insight["tone"], { bg: string; border: string; text: string; iconBg: string; iconText: string }> = {
  warn: {
    bg: "bg-amber-50",
    border: "border-amber-300",
    text: "text-amber-900",
    iconBg: "bg-amber-200",
    iconText: "text-amber-800",
  },
  info: {
    bg: "bg-indigo-50",
    border: "border-indigo-300",
    text: "text-indigo-900",
    iconBg: "bg-indigo-200",
    iconText: "text-indigo-800",
  },
  ok: {
    bg: "bg-emerald-50",
    border: "border-emerald-300",
    text: "text-emerald-900",
    iconBg: "bg-emerald-200",
    iconText: "text-emerald-800",
  },
};

export function AdminInsightCard({ product }: { product: Product }) {
  const isAdmin = useAdminStore((s) => s.isAdmin);
  const insights = useMemo(() => buildInsights(product), [product]);

  if (!isAdmin) return null;

  return (
    <section className="mx-auto mb-6 max-w-[1140px] px-8">
      <div className="rounded-2xl border-[1.5px] border-dashed border-amber-300 bg-gradient-to-br from-amber-50/80 to-indigo-50/30 p-5">
        <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-amber-400/50 bg-white px-3 py-1 text-[11px] font-extrabold uppercase tracking-wider text-amber-700">
          <Tag className="h-3 w-3" />
          Satıcı Paneli · AI İçgörü
        </div>
        <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
          {insights.map((ins, i) => {
            const tone = TONE_STYLES[ins.tone];
            const Icon = ins.icon;
            return (
              <div
                key={i}
                className={`flex gap-3 rounded-xl border ${tone.border} ${tone.bg} p-3`}
              >
                <span
                  className={`inline-flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg ${tone.iconBg}`}
                >
                  <Icon className={`h-[18px] w-[18px] ${tone.iconText}`} />
                </span>
                <div className={`min-w-0 ${tone.text}`}>
                  <div className="mb-0.5 text-[12.5px] font-bold leading-tight">
                    {ins.title}
                  </div>
                  <div className="text-[12px] leading-snug opacity-90">
                    {ins.body}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
        <p className="mt-3 text-[10.5px] italic text-amber-700/70">
          Demo not: Veriler ürünün gerçek risk + yorum agregasyonlarından türetilmiştir; sorgu trendi simüle edilmiştir.
        </p>
      </div>
    </section>
  );
}
