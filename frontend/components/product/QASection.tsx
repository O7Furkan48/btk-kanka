"use client";

import { useState } from "react";
import { ChevronDown, MessageCircle, ArrowRight } from "lucide-react";
import { motion, AnimatePresence } from "motion/react";
import { useQA } from "@/lib/queries";

export function QASection({ slug }: { slug: string }) {
  const [openIdx, setOpenIdx] = useState<number | null>(0);
  const { data, isLoading, isError } = useQA(slug);

  const qa = data?.items ?? [];
  const total = data?.total ?? 0;
  const avgResponse = data?.avgResponse ?? "—";

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-6 pb-4">
      <div className="mb-[18px] flex items-start justify-between">
        <div>
          <h3 className="mb-[2px] text-lg font-bold tracking-tight text-slate-900">
            Diğer Müşteriler Ne Sordu?
          </h3>
          <span className="inline-flex items-center gap-[6px] text-[12.5px] text-slate-500">
            <span
              aria-hidden
              className="inline-block h-[6px] w-[6px] rounded-full bg-green-500 shadow-[0_0_0_3px_rgba(16,185,129,0.18)]"
            />
            {isLoading ? "Sorular yükleniyor..." : `${total} soru · ${avgResponse}`}
          </span>
        </div>
        <a
          href="#"
          className="inline-flex items-center gap-1 text-sm font-semibold text-indigo-600 hover:gap-2 hover:underline"
        >
          Tümü <ArrowRight className="h-[14px] w-[14px]" strokeWidth={2.5} />
        </a>
      </div>

      {isLoading && (
        <div className="flex flex-col gap-2">
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              className="h-12 animate-pulse rounded-md bg-slate-100"
            />
          ))}
        </div>
      )}

      {isError && !isLoading && (
        <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          Hımm, sorular yüklenemedi. Bir dakka sonra dener misin?
        </div>
      )}

      {!isLoading && !isError && qa.length === 0 && (
        <div className="rounded-md border border-dashed border-slate-200 bg-slate-50 px-4 py-6 text-center text-sm text-slate-500">
          Henüz soru sorulmamış.
        </div>
      )}

      <div className="flex flex-col gap-2">
        {qa.map((item, i) => {
          const isOpen = openIdx === i;
          const [byWho, byWhen] = item.by.includes(" · ")
            ? item.by.split(" · ")
            : [item.by, ""];
          return (
            <div
              key={i}
              className={`overflow-hidden rounded-md border transition-all ${
                isOpen
                  ? "border-slate-200 bg-white shadow-sm"
                  : "border-transparent bg-slate-50 hover:border-slate-200 hover:bg-white"
              }`}
            >
              <button
                type="button"
                onClick={() => setOpenIdx(isOpen ? null : i)}
                className="flex w-full items-center gap-3 px-4 py-[14px] text-left text-sm font-semibold leading-snug text-slate-900"
              >
                <span className="inline-flex h-[26px] w-[26px] flex-shrink-0 items-center justify-center rounded-md bg-indigo-600 text-xs font-extrabold text-white">
                  S
                </span>
                <span className="flex-1">{item.question}</span>
                <ChevronDown
                  className={`ml-auto h-4 w-4 flex-shrink-0 text-slate-400 transition-transform duration-300 ${
                    isOpen ? "rotate-180" : ""
                  }`}
                />
              </button>

              <AnimatePresence initial={false}>
                {isOpen && (
                  <motion.div
                    key="content"
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.28, ease: "easeOut" }}
                  >
                    <div className="px-4 pb-4">
                      <div className="flex gap-3 rounded-md border border-dashed border-slate-200 bg-white px-[14px] pb-3 pt-[14px] text-[13.5px] leading-relaxed text-slate-700">
                        <span className="inline-flex h-[26px] w-[26px] flex-shrink-0 items-center justify-center rounded-md bg-slate-100 text-xs font-extrabold text-slate-700">
                          C
                        </span>
                        <div>
                          {item.answer}
                          <div className="mt-2 text-[11.5px] font-medium text-slate-400">
                            <b className="font-bold text-slate-700">{byWho}</b>
                            {byWhen ? ` · ${byWhen}` : ""}
                          </div>
                        </div>
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          );
        })}
      </div>

      <button
        type="button"
        className="mt-[14px] inline-flex w-full items-center justify-center gap-2 rounded-md border-[1.5px] border-dashed border-slate-300 bg-transparent px-3 py-3 text-[13.5px] font-semibold text-slate-700 transition-all hover:border-indigo-600 hover:bg-indigo-50 hover:text-indigo-600"
      >
        <MessageCircle className="h-4 w-4" strokeWidth={2} />
        Sen de bir soru sor
      </button>
    </section>
  );
}
