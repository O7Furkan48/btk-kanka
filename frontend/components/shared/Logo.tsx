import Link from "next/link";
import { Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";

export function Logo({
  className,
  href = "/",
}: {
  className?: string;
  href?: string;
}) {
  return (
    <Link
      href={href}
      className={cn(
        "inline-flex items-center gap-2 text-[22px] font-bold leading-none tracking-tight text-slate-900",
        className,
      )}
    >
      <span
        aria-hidden
        className="relative flex h-8 w-8 items-center justify-center rounded-[10px_10px_10px_4px] text-white"
        style={{
          background: "linear-gradient(135deg, #6E47FF 0%, #5B2EFF 100%)",
          boxShadow: "0 6px 14px -4px rgba(91,46,255,.45)",
        }}
      >
        <Sparkles className="h-4 w-4" strokeWidth={2.5} />
        {}
        <span
          className="absolute -bottom-[3px] left-[6px] h-0 w-0"
          style={{
            borderLeft: "5px solid transparent",
            borderRight: "5px solid transparent",
            borderTop: "6px solid #5B2EFF",
          }}
        />
      </span>
      <span>
        kanka<span className="text-indigo-600">.</span>
      </span>
    </Link>
  );
}
