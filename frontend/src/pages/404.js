import { SparkleIcon } from "@/components/icons";
import { Button } from "@/components/ui";

export default function NotFound() {
  return (
    <div className="flex animate-fade-in flex-col items-center py-16 text-center sm:py-24">
      <span className="flex h-16 w-16 items-center justify-center rounded-3xl bg-primary-50 text-primary-500 ring-1 ring-primary-100">
        <SparkleIcon className="h-7 w-7" />
      </span>
      <h1 className="mt-6 font-display text-3xl tracking-tight text-slate-900 sm:text-4xl">
        Lost among the cards
      </h1>
      <p className="mt-3 max-w-md text-sm leading-relaxed text-slate-500 sm:text-base">
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
