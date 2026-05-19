function resolveApiBase(): string {
  const envBase = process.env.NEXT_PUBLIC_API_BASE;
  if (typeof window !== "undefined") {

    if (envBase) {
      try {
        const u = new URL(envBase);

        if (
          (u.hostname === "localhost" || u.hostname === "127.0.0.1") &&
          window.location.hostname !== "localhost" &&
          window.location.hostname !== "127.0.0.1"
        ) {
          return `${u.protocol}//${window.location.hostname}:${u.port || "8765"}`;
        }
        return envBase;
      } catch {

      }
    }
    return `${window.location.protocol}//${window.location.hostname}:8765`;
  }

  return envBase ?? "http://localhost:8765";
}

export const API_BASE = resolveApiBase();

export async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${resolveApiBase()}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.mesaj ?? `HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export function apiUrl(path: string): string {
  return `${API_BASE}${path}`;
}
