import Link from "next/link";
import { Sparkles } from "lucide-react";
import type { CartNudge } from "@/lib/types";

export function AINudge({ nudge }: { nudge: CartNudge }) {
  return (
    <div className="col-span-full mt-1 flex items-center gap-[10px] rounded-[10px] bg-indigo-50 px-3 py-[10px] text-[12.5px] leading-snug text-slate-800">
      <span
        className="inline-flex h-[22px] w-[22px] flex-shrink-0 items-center justify-center rounded-full text-white"
        style={{ background: "linear-gradient(135deg, #7C5CFF, #5B2EFF)" }}
      >
        <Sparkles className="h-3 w-3" />
      </span>
      <span className="flex-1">
        {nudge.parts.map((p, i) =>
          p.bold ? (
            <b key={i} className="font-bold">
              {p.text}
            </b>
          ) : (
            <span key={i}>{p.text}</span>
          ),
        )}
      </span>
      <Link
        href={nudge.cta.href}
        className="ml-auto whitespace-nowrap text-[12.5px] font-bold text-indigo-600 hover:underline"
      >
        {nudge.cta.label}
      </Link>
    </div>
  );
}
