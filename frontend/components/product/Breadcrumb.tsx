import Link from "next/link";

export function Breadcrumb({
  items,
}: {
  items: Array<{ label: string; href: string }>;
}) {
  const last = items.length - 1;
  return (
    <nav
      aria-label="breadcrumb"
      className="mx-auto max-w-[1140px] px-8 pt-6 text-[13px] text-slate-500"
    >
      <ol className="flex flex-wrap items-center gap-2">
        {items.map((item, i) => (
          <li key={i} className="inline-flex items-center gap-2">
            {i === last ? (
              <span className="font-medium text-slate-900">{item.label}</span>
            ) : (
              <>
                <Link
                  href={item.href}
                  className="text-slate-500 transition-colors hover:text-indigo-600"
                >
                  {item.label}
                </Link>
                <span aria-hidden className="text-slate-300">
                  ›
                </span>
              </>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
}
