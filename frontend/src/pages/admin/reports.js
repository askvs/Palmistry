// Admin system reports: platform totals, health, errors, and performance.
import { useState } from "react";
import { PageHeader } from "@/components/ui";
import { AnalyticsWindowPicker } from "@/components/admin/AnalyticsPanels";
import {
  ErrorReportPanel,
  PerformanceReportPanel,
  SystemHealthPanel,
  SystemOverviewPanel,
} from "@/components/admin/ReportsPanels";
import { FileTextIcon } from "@/components/icons";

export default function AdminReportsPage() {
  const [days, setDays] = useState(7);

  return (
    <div className="space-y-6">
      <PageHeader
        icon={FileTextIcon}
        eyebrow="Administration"
        title="System Reports"
        description="Platform totals, service health, recent errors, and measured performance — all from real backend data, with unavailable metrics shown honestly."
      />

      <AnalyticsWindowPicker days={days} onChange={setDays} label="Report window" />

      <SystemOverviewPanel days={days} />

      <SystemHealthPanel />

      <PerformanceReportPanel days={days} />

      <ErrorReportPanel days={days} />
    </div>
  );
}
