import { notFound } from "next/navigation";
import type { Metadata } from "next";

import { Header } from "@/components/shared/Header";
import { Footer } from "@/components/shared/Footer";
import { Breadcrumb } from "@/components/product/Breadcrumb";
import { Gallery } from "@/components/product/Gallery";
import { ProductInfo } from "@/components/product/ProductInfo";
import { ProductTabs } from "@/components/product/ProductTabs";
import { QASection } from "@/components/product/QASection";
import { SimilarProducts } from "@/components/product/SimilarProducts";
import { AdminInsightCard } from "@/components/product/AdminInsightCard";
import { ChatPanelMount } from "@/components/chat/ChatPanelMount";
import { fetchJson } from "@/lib/api";
import type { Product } from "@/lib/types";

interface PageProps {
  params: Promise<{ slug: string }>;
}

async function fetchProduct(slug: string): Promise<Product | null> {
  try {
    return await fetchJson<Product>(`/api/products/${slug}`);
  } catch {
    return null;
  }
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { slug } = await params;
  const product = await fetchProduct(slug);
  if (!product) return { title: "Ürün Bulunamadı — kanka." };
  return {
    title: `${product.brand} ${product.title.split(" ").slice(0, 4).join(" ")} — kanka.`,
    description: product.summary,
  };
}

export default async function ProductDetailPage({ params }: PageProps) {
  const { slug } = await params;
  const product = await fetchProduct(slug);
  if (!product) notFound();

  return (
    <>
      <Header />
      <Breadcrumb items={product.category} />

      {}
      <AdminInsightCard product={product} />

      {}
      <div className="mx-auto grid max-w-[1140px] grid-cols-1 gap-12 px-8 pb-12 pt-7 md:grid-cols-2">
        <Gallery slides={product.gallery} />
        <ProductInfo product={product} />
      </div>

      <ProductTabs product={product} />

      {}
      <div className="mx-auto grid max-w-[1140px] grid-cols-1 gap-10 px-8 pb-16 md:grid-cols-[1.6fr_1fr]">
        <QASection slug={product.slug} />
        <SimilarProducts slug={product.slug} />
      </div>

      <Footer />

      {}
      <ChatPanelMount slug={product.slug} />
    </>
  );
}
