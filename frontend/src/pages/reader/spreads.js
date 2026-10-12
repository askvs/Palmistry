// Tarot reader spread studio (role-guarded, backend stays authoritative).
import { PageHeader } from "@/components/ui";
import SpreadStudio from "@/components/reader/SpreadStudio";
import { CardsIcon } from "@/components/icons";

export default function ReaderSpreadsPage() {
  return (
    <div className="space-y-6">
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
