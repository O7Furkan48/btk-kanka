import { Header } from "@/components/shared/Header";
import { Footer } from "@/components/shared/Footer";
import { Hero } from "@/components/home/Hero";
import { Categories } from "@/components/home/Categories";
import { ProductsSection } from "@/components/home/ProductsSection";
import { HowItWorks } from "@/components/home/HowItWorks";
import { CtaBanner } from "@/components/home/CtaBanner";
import { ChatStateCleaner } from "@/components/chat/ChatStateCleaner";

export default function Home() {
  return (
    <>
      <ChatStateCleaner />
      <Header />
      <Hero />
      <Categories />
      <ProductsSection />
      <HowItWorks />
      <CtaBanner />
      <Footer />
    </>
  );
}
