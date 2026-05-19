import { create } from "zustand";

const STORAGE_KEY = "kanka-admin-mode";

interface AdminState {
  isAdmin: boolean;
  hydrated: boolean;
  toggleAdmin: () => void;
  setAdmin: (v: boolean) => void;

  hydrate: () => void;
}

export const useAdminStore = create<AdminState>((set, get) => ({
  isAdmin: false,
  hydrated: false,
  toggleAdmin: () => {
    const next = !get().isAdmin;
    if (typeof window !== "undefined") {
      try {
        localStorage.setItem(STORAGE_KEY, next ? "1" : "0");
      } catch {

      }
    }
    set({ isAdmin: next });
  },
  setAdmin: (v) => {
    if (typeof window !== "undefined") {
      try {
        localStorage.setItem(STORAGE_KEY, v ? "1" : "0");
      } catch {

      }
    }
    set({ isAdmin: v });
  },
  hydrate: () => {
    if (typeof window === "undefined" || get().hydrated) return;
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      set({ isAdmin: raw === "1", hydrated: true });
    } catch {
      set({ hydrated: true });
    }
  },
}));
