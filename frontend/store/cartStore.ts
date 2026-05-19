import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import type { CartItem } from "@/lib/types";

interface CartState {
  items: CartItem[];

  lastProductSlug: string | null;

  addItem: (item: CartItem, sourceSlug?: string) => void;

  updateQuantity: (id: string, delta: number) => void;

  removeItem: (id: string) => void;

  clearCart: () => void;

  loadDemo: () => void;

  noteLastProduct: (slug: string) => void;
}

export const DEMO_ITEMS: CartItem[] = [
  {
    id: "demo-tudors-tshirt",
    brand: "Tudors",
    name: "Unisex Oversize Geniş Kesim %100 Pamuk Basic Bisiklet Yaka Beyaz Tişört",
    bg: "ph-bg-1",
    color: "Beyaz",
    colorClass: "",
    size: "L",
    unitPrice: 414.98,
    quantity: 1,
    nudge: {
      type: "size",
      parts: [
        { text: "Senin bedenin için " },
        { text: "L tam oturuyor", bold: true },
        { text: " · %6 iade riski." },
      ],
      cta: { label: "Beden tablosu →", href: "#size-chart" },
    },
  },
  {
    id: "demo-mavi-denim",
    brand: "Mavi",
    name: "Erkek Slim Fit Yıkamalı Mavi Denim Pantolon",
    bg: "ph-bg-9",
    color: "Açık Mavi",
    colorClass: "",
    size: "32/32",
    unitPrice: 549.0,
    quantity: 1,
    nudge: {
      type: "combo",
      parts: [
        { text: "Bu pantolon, sepetteki tişörtle " },
        { text: "yazlık günlük kombin", bold: true },
        { text: " oluşturuyor." },
      ],
      cta: { label: "Kombini gör →", href: "#combo" },
    },
  },
  {
    id: "demo-lacoste-hat",
    brand: "Lacoste",
    name: "Erkek Klasik Krem Şapka — UV Korumalı Hasır",
    bg: "ph-bg-6",
    color: "Bej",
    colorClass: "beige",
    size: "Tek Beden",
    unitPrice: 230.51,
    quantity: 1,
    nudge: null,
  },
];

export const useCartStore = create<CartState>()(
  persist(
    (set) => ({
      items: [],
      lastProductSlug: null,
      addItem: (item, sourceSlug) =>
        set((state) => {
          const idx = state.items.findIndex((it) => it.id === item.id);
          let nextItems = state.items;
          if (idx >= 0) {
            nextItems = [...state.items];
            nextItems[idx] = {
              ...nextItems[idx],
              quantity: nextItems[idx].quantity + item.quantity,
            };
          } else {
            nextItems = [...state.items, item];
          }

          const slugFromId = item.id.split("__")[0];
          return {
            items: nextItems,
            lastProductSlug: sourceSlug ?? slugFromId ?? state.lastProductSlug,
          };
        }),
      updateQuantity: (id, delta) =>
        set((state) => ({
          items: state.items.map((it) =>
            it.id === id
              ? { ...it, quantity: Math.max(1, it.quantity + delta) }
              : it,
          ),
        })),
      removeItem: (id) =>
        set((state) => ({
          items: state.items.filter((it) => it.id !== id),
        })),
      clearCart: () => set({ items: [] }),
      loadDemo: () => set({ items: DEMO_ITEMS }),
      noteLastProduct: (slug) => set({ lastProductSlug: slug }),
    }),
    {
      name: "kanka-cart",
      storage: createJSONStorage(() => localStorage),

      partialize: (state) => ({
        items: state.items,
        lastProductSlug: state.lastProductSlug,
      }),
    },
  ),
);
