import Link from "next/link";
import { Logo } from "./Logo";

const COLS = [
  {
    title: "Hakkımızda",
    links: [
      { label: "Biz kimiz", href: "#" },
      { label: "Kariyer", href: "#" },
      { label: "Blog", href: "#" },
    ],
  },
  {
    title: "Kategoriler",
    links: [
      { label: "Kadın", href: "#" },
      { label: "Erkek", href: "#" },
      { label: "Kozmetik", href: "#" },
    ],
  },
  {
    title: "Yardım",
    links: [
      { label: "SSS", href: "#" },
      { label: "İade", href: "#" },
      { label: "İletişim", href: "#" },
    ],
  },
  {
    title: "Hesap",
    links: [
      { label: "Giriş Yap", href: "#" },
      { label: "Üye Ol", href: "#" },
      { label: "Siparişlerim", href: "#" },
    ],
  },
] as const;

export function Footer() {
  return (
    <footer className="mt-auto border-t border-slate-200 bg-white">
      {}
      <div className="mx-auto grid max-w-[1280px] grid-cols-1 gap-10 px-8 py-14 md:grid-cols-[1.4fr_repeat(4,1fr)]">
        <div>
          <Logo />
          <p className="mt-[14px] max-w-[280px] text-sm leading-relaxed text-slate-500">
            Kankan kadar samimi, yapay zeka kadar akıllı bir alışveriş asistanı.
          </p>
        </div>
        {COLS.map((col) => (
          <div key={col.title}>
            <h4 className="mb-4 text-xs font-bold uppercase tracking-wider text-slate-900">
              {col.title}
            </h4>
            <ul className="flex flex-col gap-[10px]">
              {col.links.map((l) => (
                <li key={l.label}>
                  <Link
                    href={l.href}
                    className="text-sm text-slate-600 transition-colors hover:text-indigo-600"
                  >
                    {l.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>

      {}
      <div className="border-t border-slate-200">
        <div className="mx-auto flex max-w-[1280px] flex-col gap-2 px-8 py-5 text-sm text-slate-500 md:flex-row md:items-center md:justify-between md:gap-0">
          <span>© 2026 Kanka Teknoloji A.Ş.</span>
          <span>
            Kanka&apos;yı sevdiyseniz arkadaşlarınıza önerin{" "}
            <span className="text-indigo-600">💜</span>
          </span>
        </div>
      </div>
    </footer>
  );
}
