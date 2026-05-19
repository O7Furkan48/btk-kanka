"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { usePathname } from "next/navigation";
import { Sparkles, Minus, ChevronsUpDown, X, ArrowRight } from "lucide-react";
import { motion, AnimatePresence } from "motion/react";
import Image from "next/image";
import Link from "next/link";
import { useChatStore } from "@/store/chatStore";
import { useAdminStore } from "@/store/adminStore";
import {
  streamChat,
  streamCombo,
  type ChatHistoryItem,
  type ChatErrorEvent,
  type TokenEvent,
  type ToolCallEvent,
  type ToolResultEvent,
} from "@/lib/chatStream";

const PLACEHOLDERS = [
  "örn: Bu yazın terletir mi?",
  "örn: Hangi beden bana uyar?",
  "örn: Bunun üstüne ne giyilir?",
  "örn: Düğünde giyilir mi?",
];

const HISTORY_WINDOW = 12;

function slugFromPath(pathname: string | null): string {
  if (!pathname) return "home";
  const match = pathname.match(/^\/urun\/([^/?#]+)/);
  if (match?.[1]) return decodeURIComponent(match[1]);
  return "home";
}

export function ChatPanel() {
  const isOpen = useChatStore((s) => s.isOpen);
  const isMinimized = useChatStore((s) => s.isMinimized);
  const isAdminMode = useAdminStore((s) => s.isAdmin);
  const close = useChatStore((s) => s.close);
  const toggleMinimize = useChatStore((s) => s.toggleMinimize);

  const productSlug = useChatStore((s) => s.productSlug);
  const messages = useChatStore((s) => s.messages);

  const isStreaming = useChatStore((s) => s.isStreaming);
  const addMessage = useChatStore((s) => s.addMessage);
  const appendToMessage = useChatStore((s) => s.appendToMessage);
  const markMessageDone = useChatStore((s) => s.markMessageDone);
  const addToolCall = useChatStore((s) => s.addToolCall);
  const attachToolResult = useChatStore((s) => s.attachToolResult);
  const attachEvidence = useChatStore((s) => s.attachEvidence);
  const attachEvidenceProducts = useChatStore((s) => s.attachEvidenceProducts);
  const setStreaming = useChatStore((s) => s.setStreaming);
  const bumpTurn = useChatStore((s) => s.bumpTurn);

  const pathname = usePathname();
  const fallbackSlug = useMemo(() => slugFromPath(pathname), [pathname]);
  const activeSlug = productSlug ?? fallbackSlug;

  const [draft, setDraft] = useState("");
  const [exIdx, setExIdx] = useState(0);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const [comboStatus, setComboStatus] = useState<{ emoji: string; text: string } | null>(null);

  const abortRef = useRef<AbortController | null>(null);
  const scrollRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!isOpen || isMinimized) return;
    const id = setInterval(
      () => setExIdx((i) => (i + 1) % PLACEHOLDERS.length),
      3200,
    );
    return () => clearInterval(id);
  }, [isOpen, isMinimized]);

  useEffect(() => {
    if (!scrollRef.current) return;
    scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages, isStreaming, comboStatus]);

  useEffect(() => {
    if (!isOpen || isMinimized) return;

    const t = setTimeout(() => {
      if (scrollRef.current) {
        scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
      }
    }, 60);
    return () => clearTimeout(t);
  }, [isOpen, isMinimized]);

  useEffect(() => {
    if (!isOpen && abortRef.current) {
      abortRef.current.abort();
      abortRef.current = null;
    }
  }, [isOpen]);

  function comboStatusFor(toolName: string, args: Record<string, unknown> | undefined): { emoji: string; text: string } {
    const pick = <T,>(arr: T[]): T => arr[Math.floor(Math.random() * arr.length)];
    const slot = (args?.slot as string) || "";

    if (toolName === "search_products_by_intent") {
      const SLOT_OPTIONS: Record<string, { emoji: string; texts: string[] }> = {
        ust: {
          emoji: "👕",
          texts: [
            "Sana uyacak üst parçayı buluyorum…",
            "Üst için iyi bir aday arıyorum…",
            "Üst seçeneklerini gözden geçiriyorum…",
          ],
        },
        alt: {
          emoji: "👖",
          texts: [
            "Alta uygun parça arıyorum…",
            "Pantolon/şort/etek bakıyorum…",
            "Alt için uyumlu bir şey seçiyorum…",
          ],
        },
        ayakkabi: {
          emoji: "👟",
          texts: [
            "Ayakkabı dolabını tarıyorum…",
            "Stil için uygun ayakkabı bakıyorum…",
            "Ayakkabı önerisi hazırlıyorum…",
          ],
        },
        aksesuar: {
          emoji: "✨",
          texts: [
            "Detayları tamamlıyorum…",
            "Aksesuar fikirleri arıyorum…",
            "Komple görünüm için bir parça daha…",
          ],
        },
        dis_giyim: {
          emoji: "🧥",
          texts: [
            "Üstüne giyilecek bir şey arıyorum…",
            "Dış giyim aday parçalarına bakıyorum…",
            "Hava soğursa diye dış parça…",
          ],
        },
        elbise: {
          emoji: "👗",
          texts: [
            "Komple bir parça arıyorum…",
            "Elbise/etek seçeneklerine bakıyorum…",
          ],
        },
      };
      const opt = SLOT_OPTIONS[slot];
      if (opt) return { emoji: opt.emoji, text: pick(opt.texts) };
      return { emoji: "🔍", text: pick(["Kataloğu tarıyorum…", "İyi bir eşleşme arıyorum…"]) };
    }
    if (toolName === "get_size_recommendation") {
      return { emoji: "📏", text: pick(["Beden verilerini topluyorum…", "Profiline uygun beden bakıyorum…"]) };
    }
    if (toolName === "search_reviews") {
      return { emoji: "💬", text: pick(["Yorumları okuyorum…", "Müşteri görüşlerine bakıyorum…", "İlgili yorumları topluyorum…"]) };
    }
    if (toolName === "get_review_summary") {
      return { emoji: "📝", text: pick(["Yorumları özetliyorum…", "Bu konudaki yorumları derliyorum…"]) };
    }
    if (toolName === "get_return_risk") {
      return { emoji: "⚖️", text: "İade riskini hesaplıyorum…" };
    }
    if (toolName === "get_qa_answer_if_exists") {
      return { emoji: "❓", text: pick(["Hazır cevap var mı diye bakıyorum…", "Önceki sorularda bu var mı bakıyorum…"]) };
    }
    if (toolName === "find_compatible_products") {
      return { emoji: "🎨", text: pick(["Tarzına yakışanları topluyorum…", "Uyumlu parçaları çıkarıyorum…"]) };
    }
    if (toolName === "get_alternative_product") {
      return { emoji: "🔄", text: "Alternatif öneri arıyorum…" };
    }
    if (toolName === "compare_products") {
      return { emoji: "⚖️", text: "İki ürünü karşılaştırıyorum…" };
    }
    if (toolName === "get_seller_quality") {
      return { emoji: "🏪", text: "Satıcı kalitesine bakıyorum…" };
    }
    if (toolName === "get_trending_for_category") {
      return { emoji: "📈", text: "Trend ürünleri çekiyorum…" };
    }
    return { emoji: "🧠", text: pick(["Düşünüyorum…", "Birkaç saniyem var…", "Bunu anlamaya çalışıyorum…"]) };
  }

  async function handleComboSuggest() {
    if (isStreaming || !activeSlug) return;
    setErrorMsg(null);

    const userId = makeId();
    const assistantId = makeId();
    addMessage({
      id: userId,
      role: "user",
      content: "✨ Bu üründen yola çıkıp uyumlu kombin öner",
      done: true,
    });
    addMessage({ id: assistantId, role: "assistant", content: "", done: false });

    const turn = bumpTurn();
    setStreaming(true);
    setComboStatus({ emoji: "🧠", text: "Ürünü analiz ediyorum…" });
    const controller = new AbortController();
    abortRef.current = controller;
    let firstTokenSeen = false;

    try {
      for await (const evt of streamCombo(activeSlug, "", controller.signal)) {
        if (evt.type === "token") {
          const data = evt.data as TokenEvent;
          if (!firstTokenSeen) {
            firstTokenSeen = true;
            setComboStatus({ emoji: "✨", text: "Tarzı oluşturuyorum…" });
          }
          if (data?.text) appendToMessage(assistantId, data.text);
        } else if (evt.type === "tool_call") {
          const data = evt.data as ToolCallEvent;
          setComboStatus(comboStatusFor(data?.name ?? "", data?.args));
          addToolCall({
            id: `${turn}-${makeId()}`,
            name: data?.name ?? "unknown",
            args: data?.args ?? {},
          });
        } else if (evt.type === "tool_result") {
          const data = evt.data as ToolResultEvent;
          const log = useChatStore.getState().toolLog;
          const target = [...log].reverse().find(
            (t) => t.turn === turn && t.name === data?.name && t.result === undefined,
          );
          if (target) attachToolResult(target.id, data?.payload);

          if (data?.name === "search_reviews") {
            const payload = data.payload as { reviews?: Array<{ text: string; meta?: Record<string, unknown>; score?: number }> } | undefined;
            const items = payload?.reviews ?? [];
            if (items.length > 0) {
              attachEvidence(
                assistantId,
                items.slice(0, 4).map((r) => ({
                  text: r.text,
                  beden: r.meta?.beden as string | undefined,
                  boy_bin: r.meta?.boy_bin as number | undefined,
                  kilo_bin: r.meta?.kilo_bin as number | undefined,
                  sent_label: r.meta?.sent_label as string | undefined,
                  fit_label: r.meta?.fit_label as string | undefined,
                  risk_top: r.meta?.risk_top as string | undefined,
                  score: r.score,
                })),
              );
            }
          }

          if (data?.name === "search_products_by_intent" || data?.name === "find_compatible_products") {
            const payload = data.payload as
              | {
                  products?: Array<{ slug: string; brand: string; name: string; fiyat?: number; rating?: number; imageUrl?: string; href: string; kategori_son?: string }>;
                  items?: Array<{ slug: string; brand: string; name: string; price?: number; rating?: number; imageUrl?: string; href?: string }>;
                  slot?: string;
                }
              | undefined;
            const arr = payload?.products ?? payload?.items ?? [];
            const slot = payload?.slot;
            if (arr.length > 0) {
              attachEvidenceProducts(
                assistantId,
                arr.slice(0, 4).map((p) => ({
                  slug: p.slug,
                  brand: p.brand,
                  name: p.name,
                  fiyat: ("fiyat" in p ? p.fiyat : (p as { price?: number }).price) ?? undefined,
                  rating: p.rating,
                  imageUrl: p.imageUrl,
                  href: p.href ?? `/urun/${p.slug}`,
                  slot,
                })),
              );
            }
          }
        } else if (evt.type === "error") {
          const data = evt.data as ChatErrorEvent;
          setErrorMsg(data?.mesaj ?? "Kombin önerisi üretilemedi.");
          break;
        } else if (evt.type === "done") {
          break;
        }
      }
    } catch (err) {
      if ((err as Error).name !== "AbortError") {
        setErrorMsg((err as Error).message || "Kombin önerisi üretilemedi, tekrar dener misin?");
      }
    } finally {
      markMessageDone(assistantId);
      setStreaming(false);
      setComboStatus(null);
      abortRef.current = null;
    }
  }

  async function handleSend() {
    const text = draft.trim();
    if (!text || isStreaming) return;

    setErrorMsg(null);
    setDraft("");

    const userId = makeId();
    const assistantId = makeId();
    addMessage({ id: userId, role: "user", content: text, done: true });
    addMessage({ id: assistantId, role: "assistant", content: "", done: false });

    const turn = bumpTurn();

    const history: ChatHistoryItem[] = messages
      .filter((m) => m.done !== false)
      .slice(-HISTORY_WINDOW)
      .map((m) => ({ role: m.role, content: m.content }));

    setStreaming(true);
    const controller = new AbortController();
    abortRef.current = controller;

    let regularFirstTokenSeen = false;
    setComboStatus({ emoji: "🧠", text: "Düşünüyorum…" });

    try {
      for await (const evt of streamChat(
        activeSlug,
        text,
        history,
        controller.signal,
      )) {
        if (evt.type === "token") {
          const data = evt.data as TokenEvent;
          if (!regularFirstTokenSeen) {
            regularFirstTokenSeen = true;
            setComboStatus(null);
          }
          if (data?.text) appendToMessage(assistantId, data.text);
        } else if (evt.type === "tool_call") {
          const data = evt.data as ToolCallEvent;
          setComboStatus(comboStatusFor(data?.name ?? "", data?.args));
          addToolCall({
            id: `${turn}-${makeId()}`,
            name: data?.name ?? "unknown",
            args: data?.args ?? {},
          });
        } else if (evt.type === "tool_result") {
          const data = evt.data as ToolResultEvent;

          const log = useChatStore.getState().toolLog;
          const target = [...log]
            .reverse()
            .find(
              (t) =>
                t.turn === turn &&
                t.name === data?.name &&
                t.result === undefined,
            );
          if (target) attachToolResult(target.id, data?.payload);

          if (data?.name === "search_reviews") {
            const payload = data.payload as
              | { reviews?: Array<{ text: string; meta?: Record<string, unknown>; score?: number }> }
              | undefined;
            const items = payload?.reviews ?? [];
            if (items.length > 0) {
              attachEvidence(
                assistantId,
                items.slice(0, 4).map((r) => ({
                  text: r.text,
                  beden: r.meta?.beden as string | undefined,
                  boy_bin: r.meta?.boy_bin as number | undefined,
                  kilo_bin: r.meta?.kilo_bin as number | undefined,
                  sent_label: r.meta?.sent_label as string | undefined,
                  fit_label: r.meta?.fit_label as string | undefined,
                  risk_top: r.meta?.risk_top as string | undefined,
                  score: r.score,
                })),
              );
            }
          }
          if (data?.name === "search_products_by_intent" || data?.name === "find_compatible_products") {
            const payload = data.payload as
              | {
                  products?: Array<{ slug: string; brand: string; name: string; fiyat?: number; rating?: number; imageUrl?: string; href: string }>;
                  items?: Array<{ slug: string; brand: string; name: string; price?: number; rating?: number; imageUrl?: string; href?: string }>;
                  slot?: string;
                }
              | undefined;
            const arr = payload?.products ?? payload?.items ?? [];
            const slot = payload?.slot;
            if (arr.length > 0) {
              attachEvidenceProducts(
                assistantId,
                arr.slice(0, 4).map((p) => ({
                  slug: p.slug,
                  brand: p.brand,
                  name: p.name,
                  fiyat: ("fiyat" in p ? p.fiyat : (p as { price?: number }).price) ?? undefined,
                  rating: p.rating,
                  imageUrl: p.imageUrl,
                  href: p.href ?? `/urun/${p.slug}`,
                  slot,
                })),
              );
            }
          }
        } else if (evt.type === "error") {
          const data = evt.data as ChatErrorEvent;
          setErrorMsg(data?.mesaj ?? "Hımm, bir aksilik oldu.");
          break;
        } else if (evt.type === "done") {
          break;
        }
      }
    } catch (err) {
      if ((err as Error).name === "AbortError") {

      } else {
        setErrorMsg(
          (err as Error).message ||
            "Hımm, şu an cevap üretemedim, bir dakka sonra dener misin?",
        );
      }
    } finally {
      markMessageDone(assistantId);
      setStreaming(false);
      setComboStatus(null);
      abortRef.current = null;
    }
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.aside
          key="chatpanel"
          initial={{ opacity: 0, scale: 0.96, y: 16 }}
          animate={{
            opacity: 1,
            scale: 1,
            y: 0,
            height: isMinimized ? 64 : 620,
          }}
          exit={{ opacity: 0, scale: 0.96, y: 16 }}
          transition={{
            duration: 0.28,
            ease: [0.2, 0.8, 0.2, 1],
            height: { duration: 0.28, ease: [0.2, 0.8, 0.2, 1] },
          }}
          style={{
            transformOrigin: "bottom right",
            maxHeight: "calc(100vh - 56px)",
          }}
          className="fixed bottom-7 right-7 z-[90] flex w-[400px] flex-col overflow-hidden rounded-[20px] bg-white"
        >
          <div
            aria-hidden
            className="pointer-events-none absolute inset-0 rounded-[20px] ring-1 ring-slate-900/5"
            style={{
              boxShadow:
                "0 32px 64px -16px rgba(15,23,42,.22), 0 12px 24px -6px rgba(15,23,42,.12)",
            }}
          />

          {}
          <header
            onClick={() => isMinimized && toggleMinimize()}
            className={`relative flex flex-shrink-0 items-center gap-3 border-b border-slate-200 bg-white px-4 py-[14px] ${
              isMinimized ? "cursor-pointer border-b-0" : ""
            }`}
          >
            <div className="relative h-9 w-9 flex-shrink-0">
              <div
                className="flex h-full w-full items-center justify-center rounded-full text-white"
                style={{
                  background: "linear-gradient(135deg, #7C5CFF, #5B2EFF)",
                  boxShadow: "0 4px 12px -3px rgba(91,46,255,.5)",
                }}
              >
                <Sparkles className="h-[18px] w-[18px]" />
              </div>
              <span
                aria-hidden
                className="absolute -bottom-[1px] -right-[1px] h-[10px] w-[10px] rounded-full border-2 border-white bg-green-500"
              />
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-[6px] text-[14.5px] font-bold tracking-tight text-slate-900">
                Kanka
                <span className="rounded bg-indigo-50 px-[5px] py-[2px] text-[9px] font-extrabold tracking-wider text-indigo-600">
                  AI
                </span>
              </div>
              <div className="mt-[1px] inline-flex items-center gap-[5px] text-[11.5px] text-slate-500">
                <span
                  aria-hidden
                  className="inline-block h-[5px] w-[5px] rounded-full bg-green-500"
                />
                {isStreaming ? "düşünüyor…" : "çevrimiçi"}
              </div>
            </div>
            <div className="flex items-center gap-[2px]">
              {}
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  toggleMinimize();
                }}
                aria-label={isMinimized ? "Genişlet" : "Küçült"}
                className="inline-flex h-8 w-8 items-center justify-center rounded-md text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-900"
              >
                {isMinimized ? (
                  <ChevronsUpDown className="h-4 w-4" />
                ) : (
                  <Minus className="h-4 w-4" />
                )}
              </button>
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  close();
                }}
                aria-label="Kapat"
                className="inline-flex h-8 w-8 items-center justify-center rounded-md text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-900"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            {}
            {!isMinimized && (
              <span
                aria-hidden
                className="absolute bottom-[-1px] left-5 right-5 h-px"
                style={{
                  background:
                    "linear-gradient(90deg, transparent, #5B2EFF, transparent)",
                  opacity: 0.4,
                }}
              />
            )}
          </header>

          {}
          {!isMinimized && (
            <div
              ref={scrollRef}
              className="flex min-h-0 flex-1 flex-col gap-[14px] overflow-y-auto bg-white px-4 py-5"
            >
              {}
              <AssistantBubble>
                Selam! Bu ürün hakkında bana soru sorabilirsin — kumaş, beden,
                kombin, iade, ne istersen.
              </AssistantBubble>

              {messages.map((m) =>
                m.role === "user" ? (
                  <UserBubble key={m.id}>{m.content}</UserBubble>
                ) : m.content ? (

                  <div key={m.id} className="flex flex-col gap-2">
                    <AssistantBubble streaming={!m.done}>
                      {m.content}
                    </AssistantBubble>
                    {}
                    {m.done && m.evidenceProducts && m.evidenceProducts.length > 0 && (
                      <EvidenceProducts items={m.evidenceProducts} />
                    )}
                    {}
                    {m.done && m.evidenceReviews && m.evidenceReviews.length > 0 && (
                      <EvidenceReviews items={m.evidenceReviews} />
                    )}
                  </div>
                ) : null,
              )}

              {}
              {comboStatus && isStreaming && (
                <div className="self-start inline-flex items-center gap-2 rounded-full border border-indigo-100 bg-white px-3 py-1.5 text-[12.5px] text-slate-700 shadow-sm">
                  <span className="text-[15px] leading-none">{comboStatus.emoji}</span>
                  <span className="font-medium">{comboStatus.text}</span>
                  <svg
                    className="h-3 w-3 animate-spin text-indigo-500"
                    viewBox="0 0 24 24"
                    fill="none"
                    aria-hidden
                  >
                    <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeDasharray="14 28" />
                  </svg>
                </div>
              )}

              {errorMsg && (
                <div className="rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-[12.5px] text-rose-700">
                  {errorMsg}
                </div>
              )}
            </div>
          )}

          {}
          {!isMinimized && activeSlug && (
            <div className="flex flex-wrap items-center gap-2 border-t border-slate-100 bg-slate-50/50 px-4 py-2">
              <span className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold mr-1">
                Hızlı:
              </span>
              <button
                type="button"
                onClick={handleComboSuggest}
                disabled={isStreaming}
                className="inline-flex items-center gap-1.5 rounded-full border border-indigo-200 bg-white px-3 py-1 text-[12px] font-medium text-indigo-700 transition-all hover:border-indigo-600 hover:bg-indigo-50 disabled:cursor-not-allowed disabled:opacity-50"
                title="Bu üründen yola çıkıp 3-4 parçalık uyumlu kombin bul"
              >
                <Sparkles className="h-3 w-3" />
                Kombinleri Bul
              </button>
              <button
                type="button"
                onClick={() => {
                  setDraft("Bu ürün hakkında bana detaylı bilgi ver");
                  setTimeout(handleSend, 50);
                }}
                disabled={isStreaming}
                className="inline-flex items-center rounded-full border border-slate-200 bg-white px-3 py-1 text-[12px] text-slate-600 hover:border-indigo-400 hover:text-indigo-700 disabled:opacity-50"
              >
                Detaylı anlat
              </button>
              <button
                type="button"
                onClick={() => {
                  setDraft("Yorumlarda kumaş kalitesi nasıl?");
                  setTimeout(handleSend, 50);
                }}
                disabled={isStreaming}
                className="inline-flex items-center rounded-full border border-slate-200 bg-white px-3 py-1 text-[12px] text-slate-600 hover:border-indigo-400 hover:text-indigo-700 disabled:opacity-50"
              >
                Kumaş yorumları
              </button>
              <button
                type="button"
                onClick={() => {
                  setDraft("Hangi beden bana uyar?");
                  setTimeout(handleSend, 50);
                }}
                disabled={isStreaming}
                className="inline-flex items-center rounded-full border border-slate-200 bg-white px-3 py-1 text-[12px] text-slate-600 hover:border-indigo-400 hover:text-indigo-700 disabled:opacity-50"
              >
                Beden önerisi
              </button>
              {isAdminMode && (
                <button
                  type="button"
                  onClick={() => {
                    setDraft("Bu üründe nasıl iade riski var, ne yorumlarda geçiyor?");
                    setTimeout(handleSend, 50);
                  }}
                  disabled={isStreaming}
                  className="inline-flex items-center rounded-full border border-amber-200 bg-amber-50 px-3 py-1 text-[12px] font-medium text-amber-700 hover:border-amber-400 disabled:opacity-50"
                >
                  İade riski (admin)
                </button>
              )}
            </div>
          )}

          {}
          {!isMinimized && (
            <div className="flex items-center gap-2 border-t border-slate-200 bg-white px-4 pb-4 pt-[14px]">
              <input
                type="text"
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                onKeyDown={onKeyDown}
                disabled={isStreaming}
                placeholder={PLACEHOLDERS[exIdx]}
                className="h-10 min-w-0 flex-1 rounded-full border-[1.5px] border-slate-200 bg-slate-50 px-4 text-[13.5px] text-slate-900 transition-colors placeholder:italic placeholder:text-slate-400 focus:border-indigo-600 focus:bg-white focus:outline-none disabled:opacity-60"
              />
              <button
                type="button"
                onClick={handleSend}
                disabled={isStreaming || !draft.trim()}
                aria-label="Gönder"
                className="inline-flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-indigo-600 text-white transition-all hover:scale-110 hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:scale-100"
                style={{
                  boxShadow: "0 6px 14px -4px rgba(91,46,255,.5)",
                }}
              >
                <ArrowRight className="h-[18px] w-[18px]" strokeWidth={2.5} />
              </button>
            </div>
          )}
        </motion.aside>
      )}
    </AnimatePresence>
  );
}

function renderInlineMarkdown(text: string): React.ReactNode[] {
  if (!text) return [];
  const lines = text.split("\n");
  const out: React.ReactNode[] = [];
  for (let li = 0; li < lines.length; li++) {
    const line = lines[li];

    const bulletMatch = line.match(/^\s*[*•\-]\s+(.+)$/);
    if (bulletMatch) {
      out.push(
        <span key={`l-${li}`} className="flex gap-1.5 pl-0.5">
          <span aria-hidden className="select-none text-indigo-500">•</span>
          <span className="flex-1">{parseInline(bulletMatch[1], `bi-${li}`)}</span>
        </span>,
      );
    } else if (line.trim() === "") {
      out.push(<span key={`br-${li}`} className="block h-2" aria-hidden />);
    } else {
      out.push(<span key={`l-${li}`} className="block">{parseInline(line, `pl-${li}`)}</span>);
    }
  }
  return out;
}

function parseInline(text: string, keyPrefix: string): React.ReactNode[] {
  const nodes: React.ReactNode[] = [];

  const re = /(\*\*([^*]+)\*\*|\*([^*\n]+)\*)/g;
  let lastIdx = 0;
  let i = 0;
  let match: RegExpExecArray | null;
  while ((match = re.exec(text)) !== null) {
    if (match.index > lastIdx) {
      nodes.push(text.slice(lastIdx, match.index));
    }
    if (match[2] !== undefined) {
      nodes.push(
        <strong key={`${keyPrefix}-b-${i++}`} className="font-bold text-slate-900">
          {match[2]}
        </strong>,
      );
    } else if (match[3] !== undefined) {
      nodes.push(
        <em key={`${keyPrefix}-i-${i++}`} className="italic">
          {match[3]}
        </em>,
      );
    }
    lastIdx = re.lastIndex;
  }
  if (lastIdx < text.length) nodes.push(text.slice(lastIdx));
  return nodes;
}

function AssistantBubble({
  children,
  streaming,
}: {
  children: React.ReactNode;
  streaming?: boolean;
}) {

  const content =
    typeof children === "string" ? renderInlineMarkdown(children) : children;
  return (
    <div className="flex items-start gap-2">
      <div
        className="mt-[2px] flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full text-white"
        style={{
          background: "linear-gradient(135deg, #7C5CFF, #5B2EFF)",
        }}
      >
        <Sparkles className="h-[14px] w-[14px]" />
      </div>
      <div className="max-w-[85%] rounded-2xl rounded-bl-[4px] bg-indigo-50 px-4 py-[11px] text-sm leading-relaxed text-slate-900">
        <span className="whitespace-pre-wrap">{content}</span>
        {streaming && <TypingDot />}
      </div>
    </div>
  );
}

function UserBubble({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex items-start justify-end">
      <div
        className="max-w-[85%] rounded-2xl rounded-br-[4px] px-4 py-[11px] text-sm leading-relaxed text-white"
        style={{
          background: "linear-gradient(135deg, #7C5CFF, #5B2EFF)",
        }}
      >
        <span className="whitespace-pre-wrap">{children}</span>
      </div>
    </div>
  );
}

function TypingDot() {
  return (
    <span
      aria-hidden
      className="ml-[2px] inline-block h-[7px] w-[7px] animate-pulse rounded-full bg-indigo-500 align-middle"
    />
  );
}

function EvidenceReviews({ items }: { items: import("@/store/chatStore").EvidenceReview[] }) {
  const SENT_COLOR: Record<string, { dot: string; label: string }> = {
    positive: { dot: "bg-emerald-500", label: "Pozitif" },
    negative: { dot: "bg-rose-500", label: "Negatif" },
    neutral: { dot: "bg-slate-400", label: "Nötr" },
  };
  return (
    <div className="ml-9 mr-2 flex flex-col gap-1.5">
      <div className="text-[10.5px] font-bold uppercase tracking-wider text-slate-400">
        Bunlar yorumlardan kanıt:
      </div>
      {items.map((r, i) => {
        const sentInfo = r.sent_label ? SENT_COLOR[r.sent_label] : null;
        const profil = [
          r.boy_bin ? `${r.boy_bin}cm` : "",
          r.kilo_bin ? `${r.kilo_bin}kg` : "",
          r.beden ? `${r.beden} bedeni` : "",
        ].filter(Boolean).join(" · ");
        return (
          <div
            key={i}
            className="rounded-md border border-slate-200 bg-white px-3 py-2 text-[12.5px] leading-snug text-slate-700 shadow-sm"
          >
            <div className="mb-1 flex flex-wrap items-center gap-1.5 text-[10.5px] text-slate-500">
              {sentInfo && (
                <span className="inline-flex items-center gap-1">
                  <span className={`h-1.5 w-1.5 rounded-full ${sentInfo.dot}`} />
                  {sentInfo.label}
                </span>
              )}
              {profil && <span className="text-slate-400">· {profil}</span>}
              {r.risk_top && (
                <span className="rounded bg-amber-50 px-1.5 py-px text-[10px] font-semibold text-amber-700">
                  {r.risk_top}
                </span>
              )}
            </div>
            <div className="line-clamp-3 italic">&ldquo;{r.text}&rdquo;</div>
          </div>
        );
      })}
    </div>
  );
}

function EvidenceProducts({ items }: { items: import("@/store/chatStore").EvidenceProduct[] }) {
  const SLOT_LABEL: Record<string, { emoji: string; label: string }> = {
    ust: { emoji: "👕", label: "Üst" },
    alt: { emoji: "👖", label: "Alt" },
    ayakkabi: { emoji: "👟", label: "Ayakkabı" },
    aksesuar: { emoji: "✨", label: "Aksesuar" },
    dis_giyim: { emoji: "🧥", label: "Dış" },
    elbise: { emoji: "👗", label: "Elbise" },
  };

  function shortName(brand: string, name: string): string {
    let cleaned = (name || "").trim();
    if (brand) {

      const re = new RegExp(`^(${brand.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\s+)+`, "i");
      cleaned = cleaned.replace(re, "").trim();
    }

    const cutIdx = cleaned.indexOf(" > ");
    if (cutIdx > 0) cleaned = cleaned.slice(0, cutIdx);
    const words = cleaned.split(/\s+/);
    if (words.length > 8) cleaned = words.slice(0, 8).join(" ") + "…";
    return cleaned;
  }

  return (
    <div className="ml-9 mr-2 flex flex-col gap-2">
      <div className="text-[10.5px] font-bold uppercase tracking-wider text-indigo-500">
        Önerdiğim ürünler:
      </div>
      <div className="grid grid-cols-1 gap-2">
        {items.map((p) => {
          const slotInfo = p.slot ? SLOT_LABEL[p.slot] : null;
          const price = p.fiyat
            ? `${p.fiyat.toLocaleString("tr-TR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ₺`
            : "";
          return (
            <Link
              key={p.slug}
              href={p.href}
              className="group flex items-center gap-3 rounded-lg border border-slate-200 bg-white p-2 transition-all hover:-translate-y-px hover:border-indigo-400 hover:shadow-md"
            >
              <div className="relative h-14 w-14 flex-shrink-0 overflow-hidden rounded-md bg-slate-100">
                {p.imageUrl ? (
                  <Image
                    src={p.imageUrl}
                    alt={p.name}
                    fill
                    sizes="56px"
                    className="object-cover"
                    unoptimized
                  />
                ) : (
                  <div className="flex h-full w-full items-center justify-center text-[18px]">
                    {slotInfo?.emoji ?? "🛍️"}
                  </div>
                )}
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-1.5">
                  {slotInfo && (
                    <span className="inline-flex items-center gap-0.5 rounded bg-indigo-50 px-1.5 py-px text-[9.5px] font-bold uppercase tracking-wider text-indigo-700">
                      {slotInfo.emoji} {slotInfo.label}
                    </span>
                  )}
                  <span className="truncate text-[11px] font-bold uppercase tracking-wider text-indigo-600">
                    {p.brand}
                  </span>
                </div>
                <div className="mt-0.5 line-clamp-2 text-[12.5px] font-medium leading-snug text-slate-900 group-hover:text-indigo-700">
                  {shortName(p.brand, p.name)}
                </div>
                {price && (
                  <div className="mt-0.5 text-[12px] font-bold text-slate-800">{price}</div>
                )}
              </div>
              <ArrowRight className="h-4 w-4 flex-shrink-0 text-slate-300 transition-all group-hover:translate-x-0.5 group-hover:text-indigo-600" />
            </Link>
          );
        })}
      </div>
    </div>
  );
}

function makeId(): string {
  return Math.random().toString(36).slice(2, 10);
}
