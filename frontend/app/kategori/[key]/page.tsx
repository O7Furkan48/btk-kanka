import type { Metadata } from "next";

import { Header } from "@/components/shared/Header";
import { Footer } from "@/components/shared/Footer";
import { ChatStateCleaner } from "@/components/chat/ChatStateCleaner";
import { fetchJson } from "@/lib/api";
import type { ProductSummary, Category } from "@/lib/types";
import { CategoryGrid } from "@/components/kategori/CategoryGrid";

interface PageProps {
  params: Promise<{ key: string }>;
}

function slugToCategoryKey(slug: string): { key: string | null; label: string } {
  const lower = slug.toLowerCase();
  const label = slug
    .split("-")
    .map((w) => (w ? w[0].toUpperCase() + w.slice(1) : ""))
    .join(" ");

  if (/(elbise|etek)/.test(lower)) return { key: "dress", label };
  if (/(ayakkab|sneaker|bot|terlik|çizme)/.test(lower)) return { key: "shoe", label };
  if (/(çanta|cüzdan|kemer|aksesuar|saat|bileklik|kolye|küpe|yüzük)/.test(lower)) return { key: "bag", label };
  if (/(kozmetik|cilt|parfüm|makyaj)/.test(lower)) return { key: "cosmetics", label };
  if (/(teknoloji|bilgisayar|telefon)/.test(lower)) return { key: "tech", label };
  if (/(spor|yoga)/.test(lower)) return { key: "sport", label };
  if (/(bebek|çocuk)/.test(lower)) return { key: "baby", label };
  if (/(ev|mutfak|dekor|yaşam)/.test(lower)) return { key: "home", label };

  return { key: "shirt", label };
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { key } = await params;
  const { label } = slugToCategoryKey(key);
  return { title: `${label} — kanka.` };
}

export default async function KategoriPage({ params }: PageProps) {
  const { key } = await params;
  const { key: catKey, label } = slugToCategoryKey(key);

  let products: ProductSummary[] = [];
  try {
    products = await fetchJson<ProductSummary[]>(
      `/api/products/recommended?limit=24${catKey ? `&category=${catKey}` : ""}`,
    );
  } catch {
    products = [];
  }

  return (
    <div className="min-h-screen flex flex-col">
      <ChatStateCleaner />
      <Header />
      <main className="flex-1 px-4 md:px-8 py-6 max-w-7xl w-full mx-auto">
        <nav className="text-sm text-slate-500 mb-2">
          <a href="/" className="hover:text-violet-700">Ana sayfa</a>
          <span className="mx-2">›</span>
          <span className="text-slate-700 font-medium">{label}</span>
        </nav>
        <h1 className="text-3xl font-bold mb-1">{label}</h1>
        <p className="text-slate-500 mb-6">{products.length} ürün listeleniyor</p>

        {products.length === 0 ? (
          <div className="rounded-2xl bg-slate-50 p-12 text-center">
            <p className="text-slate-600 mb-2">Bu kategoride şu an gösterilecek ürün yok.</p>
            <a href="/" className="text-violet-700 font-medium hover:underline">Tüm ürünlere göz at →</a>
          </div>
        ) : (
          <CategoryGrid initial={products} categoryKey={catKey ?? ""} />
        )}
      </main>
      <Footer />
    </div>
  );
}
