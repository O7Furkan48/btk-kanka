"use client";

import { useMemo } from "react";
import { Sparkles, Wrench } from "lucide-react";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import type { ToolLogEntry } from "@/store/chatStore";

const TOOL_LABELS: Record<string, string> = {
  search_reviews: "Yorum araması",
  get_size_recommendation: "Beden önerisi",
  find_compatible_products: "Kombin keşfi",
  get_return_risk: "İade risk skoru",
  get_alternative_product: "Alternatif ürün",
};

interface ToolCallLogProps {
  entries: ToolLogEntry[];
}

export function ToolCallLog({ entries }: ToolCallLogProps) {
  const lastTurnCount = useMemo(() => {
    if (entries.length === 0) return 0;
    const lastTurn = Math.max(...entries.map((e) => e.turn));
    return entries.filter((e) => e.turn === lastTurn).length;
  }, [entries]);

  return (
    <Sheet>
      <SheetTrigger
        render={
          <button
            type="button"
            className="inline-flex items-center gap-[6px] rounded-full bg-indigo-50 px-[10px] py-[5px] text-[11px] font-semibold text-indigo-700 transition-colors hover:bg-indigo-100"
            aria-label="AI mimarisi panelini aç"
          >
            <Wrench className="h-[12px] w-[12px]" />
            AI mimarisi
            <span className="rounded-full bg-indigo-600 px-[6px] py-[1px] text-[10px] font-bold text-white">
              {lastTurnCount}
            </span>
          </button>
        }
      />
      <SheetContent
        side="right"
        className="w-full bg-white sm:max-w-md"
      >
        <SheetHeader className="border-b border-slate-200 p-5 pb-4">
          <SheetTitle className="flex items-center gap-2 text-base font-bold text-slate-900">
            <Sparkles className="h-[16px] w-[16px] text-indigo-600" />
            Kanka neyi araştırdı?
          </SheetTitle>
          <SheetDescription className="text-[12.5px] text-slate-500">
            Gemini orchestrator her cevap için BERT, BGE-M3 ve katalog
            tool&apos;larını function calling ile sırayla çağırıyor.
          </SheetDescription>
        </SheetHeader>

        <div className="flex-1 overflow-y-auto p-5">
          {entries.length === 0 ? (
            <div className="rounded-xl border border-dashed border-slate-200 bg-slate-50 px-4 py-10 text-center text-[13px] text-slate-500">
              Henüz tool çağrısı yok. Bir soru sor, Kanka çalışmaya başlasın.
            </div>
          ) : (
            <ol className="flex flex-col gap-3">
              {entries.map((entry, idx) => (
                <ToolCallCard key={entry.id} entry={entry} index={idx + 1} />
              ))}
            </ol>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}

function ToolCallCard({
  entry,
  index,
}: {
  entry: ToolLogEntry;
  index: number;
}) {
  const label = TOOL_LABELS[entry.name] ?? entry.name;
  const argsPreview = useMemo(() => safeStringify(entry.args), [entry.args]);
  const resultPreview = useMemo(
    () => (entry.result === undefined ? null : safeStringify(entry.result)),
    [entry.result],
  );

  return (
    <li className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="inline-flex h-5 w-5 items-center justify-center rounded-full bg-slate-100 text-[10px] font-bold text-slate-600">
            {index}
          </span>
          <span
            className="rounded-full px-[10px] py-[3px] text-[11px] font-bold text-white"
            style={{ backgroundColor: "#5B2EFF" }}
          >
            {entry.name}
          </span>
        </div>
        <span className="text-[11px] text-slate-400">{label}</span>
      </div>

      <div className="mt-3">
        <div className="mb-1 text-[10.5px] font-semibold uppercase tracking-wider text-slate-400">
          Argümanlar
        </div>
        <pre className="max-h-32 overflow-auto whitespace-pre-wrap rounded-lg bg-slate-50 p-2 text-[11.5px] leading-snug text-slate-700">
          {argsPreview}
        </pre>
      </div>

      {resultPreview && (
        <div className="mt-2">
          <div className="mb-1 text-[10.5px] font-semibold uppercase tracking-wider text-emerald-500">
            Sonuç
          </div>
          <pre className="max-h-40 overflow-auto whitespace-pre-wrap rounded-lg bg-emerald-50 p-2 text-[11.5px] leading-snug text-emerald-900">
            {resultPreview}
          </pre>
        </div>
      )}
    </li>
  );
}

function safeStringify(value: unknown, max = 600): string {
  try {
    const str = JSON.stringify(value, null, 2);
    if (str.length > max) return str.slice(0, max) + "\n…";
    return str;
  } catch {
    return String(value);
  }
}
