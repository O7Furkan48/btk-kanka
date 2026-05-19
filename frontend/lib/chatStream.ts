import { API_BASE } from "@/lib/api";

export type ChatEventType =
  | "tool_call"
  | "tool_result"
  | "token"
  | "done"
  | "error";

export interface ChatEvent<T = unknown> {
  type: ChatEventType;
  data: T;
}

export interface ToolCallEvent {
  name: string;
  args: Record<string, unknown>;
}

export interface ToolResultEvent {
  name: string;
  payload: unknown;
}

export interface TokenEvent {
  text: string;
}

export interface ChatErrorEvent {
  mesaj: string;
}

export interface ChatHistoryItem {
  role: "user" | "assistant";
  content: string;
}

export async function* streamChat(
  slug: string,
  message: string,
  history: ChatHistoryItem[] = [],
  signal?: AbortSignal,
): AsyncGenerator<ChatEvent> {
  yield* _streamSSE(`${API_BASE}/api/chat/stream`, { slug, message, history }, signal);
}

export async function* streamCombo(
  slug: string,
  hint: string = "",
  signal?: AbortSignal,
): AsyncGenerator<ChatEvent> {
  yield* _streamSSE(`${API_BASE}/api/chat/combo-stream`, { slug, message: hint, history: [] }, signal);
}

async function* _streamSSE(
  url: string,
  body: Record<string, unknown>,
  signal?: AbortSignal,
): AsyncGenerator<ChatEvent> {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal,
  });

  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const errBody = await res.json();
      if (typeof errBody?.mesaj === "string") detail = errBody.mesaj;
    } catch {

    }
    throw new Error(detail);
  }

  if (!res.body) {
    throw new Error("Sunucudan stream alınamadı.");
  }

  const reader = res.body
    .pipeThrough(new TextDecoderStream())
    .getReader();

  let buffer = "";

  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += value;

      let idx: number;
      while ((idx = buffer.indexOf("\n\n")) !== -1) {
        const block = buffer.slice(0, idx);
        buffer = buffer.slice(idx + 2);

        const lines = block.split("\n");
        let eventName: ChatEventType = "token";
        const dataLines: string[] = [];

        for (const line of lines) {
          if (line.startsWith("event: ")) {
            eventName = line.slice(7).trim() as ChatEventType;
          } else if (line.startsWith("data: ")) {
            dataLines.push(line.slice(6));
          }
        }

        if (dataLines.length === 0) continue;
        const dataRaw = dataLines.join("\n");

        let parsed: unknown = dataRaw;
        try {
          parsed = JSON.parse(dataRaw);
        } catch {

        }

        yield { type: eventName, data: parsed };
      }
    }
  } finally {
    try {
      reader.releaseLock();
    } catch {

    }
  }
}
