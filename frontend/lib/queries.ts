import { useQuery, useMutation } from "@tanstack/react-query";
import { fetchJson } from "./api";
import type {
  Category,
  Product,
  ProductSummary,
  RiskAnalysis,
  SizeAdvice,
  ComboGroup,
  CouponResponse,
  Review,
  QAItem,
  SimilarProduct,
} from "./types";

export function useCategories() {
  return useQuery<Category[]>({
    queryKey: ["categories"],
    queryFn: () => fetchJson("/api/categories"),
    staleTime: Infinity,
  });
}

export function useProductRecommended(limit = 12, category?: string) {
  return useQuery<ProductSummary[]>({
    queryKey: ["products", "recommended", limit, category],
    queryFn: () => {
      const params = new URLSearchParams({ limit: String(limit) });
      if (category) params.set("category", category);
      return fetchJson(`/api/products/recommended?${params}`);
    },
    staleTime: 5 * 60 * 1000,
  });
}

export function useProduct(slug: string) {
  return useQuery<Product>({
    queryKey: ["product", slug],
    queryFn: () => fetchJson(`/api/products/${slug}`),
    enabled: !!slug,
    staleTime: 5 * 60 * 1000,
  });
}

export function useRiskAnalysis(slug: string) {
  return useQuery<RiskAnalysis>({
    queryKey: ["risk", slug],
    queryFn: () => fetchJson(`/api/products/${slug}/risk-analysis`),
    enabled: !!slug,
  });
}

export function useSizeAdviceMutation(slug: string) {
  return useMutation<SizeAdvice, Error, { height: number; weight: number }>({
    mutationFn: (body) =>
      fetchJson(`/api/products/${slug}/size-advice`, {
        method: "POST",
        body: JSON.stringify(body),
      }),
  });
}

export function useReviews(
  slug: string,
  filter: "all" | "pos" | "neg" | "me" = "all",
  limit = 10,
  offset = 0,
  matchedTo?: { height: number; weight: number }
) {
  return useQuery<{ items: Review[]; total: number }>({
    queryKey: ["reviews", slug, filter, limit, offset, matchedTo],
    queryFn: () => {
      const params = new URLSearchParams({ filter, limit: String(limit), offset: String(offset) });
      if (matchedTo) {
        params.set("height", String(matchedTo.height));
        params.set("weight", String(matchedTo.weight));
      }
      return fetchJson(`/api/products/${slug}/reviews?${params}`);
    },
    enabled: !!slug,
  });
}

export function useQA(slug: string, limit = 10, offset = 0) {
  return useQuery<{ items: QAItem[]; total: number; avgResponse: string }>({
    queryKey: ["qa", slug, limit, offset],
    queryFn: () =>
      fetchJson(`/api/products/${slug}/qa?limit=${limit}&offset=${offset}`),
    enabled: !!slug,
  });
}

export function useSimilarProducts(slug: string, limit = 4) {
  return useQuery<SimilarProduct[]>({
    queryKey: ["similar", slug, limit],
    queryFn: () => fetchJson(`/api/products/${slug}/similar?limit=${limit}`),
    enabled: !!slug,
  });
}

export function useCouponMutation() {
  return useMutation<CouponResponse, Error, { code: string }>({
    mutationFn: (body) =>
      fetchJson("/api/cart/coupon", {
        method: "POST",
        body: JSON.stringify(body),
      }),
  });
}

export function useComboSuggestions(ids: string[]) {
  return useQuery<ComboGroup[]>({
    queryKey: ["combo", ids],
    queryFn: () => fetchJson(`/api/cart/combo-suggestions?ids=${ids.join(",")}`),
    enabled: ids.length > 0,
  });
}

export function useSellerQuality(slug: string) {
  return useQuery({
    queryKey: ["seller-quality", slug],
    queryFn: () => fetchJson(`/api/products/${slug}/seller-quality`),
    enabled: !!slug,
  });
}

export function useProductTrend(slug: string, window = "90d") {
  return useQuery({
    queryKey: ["trend", slug, window],
    queryFn: () => fetchJson(`/api/products/${slug}/trend?window=${window}`),
    enabled: !!slug,
  });
}

export function useCompareProducts(slugA: string, slugB: string) {
  return useQuery({
    queryKey: ["compare", slugA, slugB],
    queryFn: () =>
      fetchJson("/api/products/compare", {
        method: "POST",
        body: JSON.stringify({ slug_a: slugA, slug_b: slugB }),
      }),
    enabled: !!slugA && !!slugB,
  });
}

export function useAspectSummary(slug: string, aspect: string) {
  return useQuery({
    queryKey: ["aspect", slug, aspect],
    queryFn: () => fetchJson(`/api/products/${slug}/reviews/aspect?aspect=${encodeURIComponent(aspect)}`),
    enabled: !!slug && !!aspect,
  });
}
