import BrandMark from "@/components/BrandMark";
import Seo from "@/components/Seo";
import { Button } from "@/components/ui";

export default function NotFound() {
  return (
    <div className="flex animate-fade-in flex-col items-center py-16 text-center sm:py-24">
      <Seo title="Page not found" />
      <BrandMark size="lg" />
      <h1 className="mt-6 font-display text-3xl font-semibold tracking-[-0.02em] text-slate-900 sm:text-4xl">
        Lost among the cards
      </h1>
      <p className="mt-3 max-w-md text-sm leading-relaxed text-slate-600 sm:text-base">
        The page you&rsquo;re looking for doesn&rsquo;t exist — but your reading is still waiting.
      </p>
      <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
        <Button href="/" size="lg">
          Back home
        </Button>
        <Button href="/readings" variant="secondary" size="lg">
          Browse readings
        </Button>
      </div>
    </div>
  );
}
