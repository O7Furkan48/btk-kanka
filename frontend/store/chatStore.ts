import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

export interface EvidenceReview {
  text: string;
  beden?: string;
  boy_bin?: number;
  kilo_bin?: number;
  sent_label?: string;
  fit_label?: string;
  risk_top?: string;
  score?: number;
}

export interface EvidenceProduct {
  slug: string;
  brand: string;
  name: string;
  fiyat?: number;
  rating?: number;
  imageUrl?: string;
  href: string;

  slot?: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;

  done?: boolean;

  evidenceReviews?: EvidenceReview[];

  evidenceProducts?: EvidenceProduct[];
}

export interface ToolLogEntry {
  id: string;
  name: string;
  args: Record<string, unknown>;
  result?: unknown;

  turn: number;
}

interface ChatState {
  isOpen: boolean;
  isMinimized: boolean;

  productSlug: string | null;

  messages: ChatMessage[];
  toolLog: ToolLogEntry[];

  isStreaming: boolean;

  currentTurn: number;

  open: (slug?: string) => void;
  close: () => void;
  toggleMinimize: () => void;

  setProductContext: (slug: string) => void;

  clearProductContext: () => void;

  addMessage: (msg: ChatMessage) => void;
  appendToMessage: (id: string, chunk: string) => void;
  markMessageDone: (id: string) => void;
  attachEvidence: (id: string, reviews: EvidenceReview[]) => void;
  attachEvidenceProducts: (id: string, products: EvidenceProduct[]) => void;
  addToolCall: (entry: Omit<ToolLogEntry, "turn">) => void;
  attachToolResult: (id: string, result: unknown) => void;
  setStreaming: (v: boolean) => void;
  bumpTurn: () => number;
  resetConversation: () => void;
}

export const useChatStore = create<ChatState>()(
  persist(
    (set, get) => ({
  isOpen: false,
  isMinimized: false,
  productSlug: null,

  messages: [],
  toolLog: [],
  isStreaming: false,
  currentTurn: 0,

  open: (slug) => {
    const current = get().productSlug;
    if (slug && slug !== current) {

      set({
        isOpen: true,
        isMinimized: false,
        productSlug: slug,
        messages: [],
        toolLog: [],
        currentTurn: 0,
      });
    } else {
      set({ isOpen: true, isMinimized: false, productSlug: slug ?? current });
    }
  },
  close: () => set({ isOpen: false, isMinimized: false }),
  toggleMinimize: () =>
    set((state) => ({ isMinimized: !state.isMinimized })),

  setProductContext: (slug) => {
    const current = get().productSlug;
    if (slug === current) return;

    set({
      productSlug: slug,
      messages: [],
      toolLog: [],
      currentTurn: 0,
      isStreaming: false,
      isOpen: false,
      isMinimized: false,
    });
  },

  clearProductContext: () => {

    set({ isOpen: false, isMinimized: false, isStreaming: false });
  },

  addMessage: (msg) =>
    set((state) => ({ messages: [...state.messages, msg] })),

  appendToMessage: (id, chunk) =>
    set((state) => ({
      messages: state.messages.map((m) =>
        m.id === id ? { ...m, content: m.content + chunk } : m,
      ),
    })),

  markMessageDone: (id) =>
    set((state) => ({
      messages: state.messages.map((m) =>
        m.id === id ? { ...m, done: true } : m,
      ),
    })),

  attachEvidence: (id, reviews) =>
    set((state) => ({
      messages: state.messages.map((m) => {
        if (m.id !== id) return m;
        const existing = m.evidenceReviews ?? [];

        const seen = new Set(existing.map((e) => e.text));
        const merged = [...existing];
        for (const r of reviews) {
          if (!seen.has(r.text)) {
            merged.push(r);
            seen.add(r.text);
          }
        }
        return { ...m, evidenceReviews: merged.slice(0, 6) };
      }),
    })),

  attachEvidenceProducts: (id, products) =>
    set((state) => ({
      messages: state.messages.map((m) => {
        if (m.id !== id) return m;
        const existing = m.evidenceProducts ?? [];
        const seen = new Set(existing.map((p) => p.slug));
        const merged = [...existing];
        for (const p of products) {
          if (!seen.has(p.slug)) {
            merged.push(p);
            seen.add(p.slug);
          }
        }
        return { ...m, evidenceProducts: merged.slice(0, 8) };
      }),
    })),

  addToolCall: (entry) =>
    set((state) => ({
      toolLog: [...state.toolLog, { ...entry, turn: state.currentTurn }],
    })),

  attachToolResult: (id, result) =>
    set((state) => ({
      toolLog: state.toolLog.map((t) =>
        t.id === id ? { ...t, result } : t,
      ),
    })),

  setStreaming: (v) => set({ isStreaming: v }),

  bumpTurn: () => {
    const next = get().currentTurn + 1;
    set({ currentTurn: next });
    return next;
  },

  resetConversation: () =>
    set({ messages: [], toolLog: [], currentTurn: 0, isStreaming: false }),
    }),
    {
      name: "kanka-chat",
      storage: createJSONStorage(() => localStorage),

      partialize: (state) => ({
        productSlug: state.productSlug,
        messages: state.messages,
        toolLog: state.toolLog,
        currentTurn: state.currentTurn,
      }),
    },
  ),
);
