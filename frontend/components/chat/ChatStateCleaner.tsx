"use client";

import { useEffect } from "react";
import { useChatStore } from "@/store/chatStore";

export function ChatStateCleaner() {
  const clearProductContext = useChatStore((s) => s.clearProductContext);
  useEffect(() => {
    clearProductContext();
  }, [clearProductContext]);
  return null;
}
