// Tarot reader report management (role-guarded, backend stays authoritative).
import { PageHeader } from "@/components/ui";
import ReadingReportsTable from "@/components/reader/ReadingReportsTable";
import { TableIcon } from "@/components/icons";

export default function ReaderReportsPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        icon={TableIcon}
        eyebrow="Reader workspace"
        title="Reading Reports"
        description="Filter every platform reading by owner and review state, certify what you have checked, and export publication-grade PDF or Excel reports."
      />

      <ReadingReportsTable />
    </div>
  );
}
