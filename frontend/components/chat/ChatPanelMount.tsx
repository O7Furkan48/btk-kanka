"use client";

import { useEffect } from "react";
import { useChatStore } from "@/store/chatStore";
import { ChatPanel } from "./ChatPanel";

interface Props {
  slug: string;
}

export function ChatPanelMount({ slug }: Props) {
  const setProductContext = useChatStore((s) => s.setProductContext);

  useEffect(() => {
    setProductContext(slug);
  }, [slug, setProductContext]);

  return <ChatPanel />;
}
