// Tarot reader spread studio (role-guarded, backend stays authoritative).
import { PageHeader } from "@/components/ui";
import Seo from "@/components/Seo";
import SpreadStudio from "@/components/reader/SpreadStudio";
import { CardsIcon } from "@/components/icons";

export default function ReaderSpreadsPage() {
  return (
    <div className="space-y-6">
      <Seo
        title="Spread studio"
        description="Author your own tarot spreads beside the six standard layouts, then read with them."
      />

      <PageHeader
        icon={CardsIcon}
        eyebrow="Reader workspace"
        title="Spread Studio"
        description="Author your own spreads beside the six standard layouts, then run readings with them through the same interpretation engine."
      />

      <SpreadStudio />
    </div>
  );
}
