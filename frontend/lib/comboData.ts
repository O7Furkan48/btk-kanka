import type { ComboGroup } from "./types";

export const COMBO_GROUPS: ComboGroup[] = [
  {
    sourceId: "demo-tudors-tshirt",
    sourceName: "Beyaz Tişört",
    sourceBg: "ph-bg-1",
    scenario: "Yazlık günlük",
    items: [
      {
        id: "combo-lacoste-bermuda",
        brand: "Lacoste",
        name: "Pamuklu Krem Bermuda Şort",
        bg: "ph-bg-2",
        price: 649.0,
        risk: "low",
        riskLabel: "%4",
      },
      {
        id: "combo-adidas-sneaker",
        brand: "Adidas",
        name: "Stan Smith Beyaz Sneaker",
        bg: "ph-bg-5",
        price: 2499.0,
        risk: "low",
        riskLabel: "%6",
      },
      {
        id: "combo-hm-gozluk",
        brand: "H&M",
        name: "Wayfarer Güneş Gözlüğü Siyah",
        bg: "ph-bg-3",
        price: 399.0,
        risk: "low",
        riskLabel: "%3",
      },
    ],
  },
  {
    sourceId: "demo-mavi-denim",
    sourceName: "Mavi Denim",
    sourceBg: "ph-bg-9",
    scenario: "Smart casual",
    items: [
      {
        id: "combo-polo-tshirt",
        brand: "Polo RL",
        name: "Lacivert Pamuk Bisiklet Yaka",
        bg: "ph-bg-7",
        price: 1199.0,
        risk: "low",
        riskLabel: "%7",
      },
      {
        id: "combo-camper-loafer",
        brand: "Camper",
        name: "Kahverengi Süet Loafer",
        bg: "ph-bg-8",
        price: 3299.0,
        risk: "mid",
        riskLabel: "%14",
      },
      {
        id: "combo-fossil-kemer",
        brand: "Fossil",
        name: "Kahverengi Deri Kemer",
        bg: "ph-bg-4",
        price: 549.0,
        risk: "low",
        riskLabel: "%5",
      },
    ],
  },
];
