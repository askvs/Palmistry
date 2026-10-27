// Admin security: errors, auth rejections, rate limits, and audit trail.
import { PageHeader } from "@/components/ui";
import SecurityMonitor from "@/components/admin/SecurityMonitor";
import AuditLogPanel from "@/components/admin/AuditLogPanel";
import { PerformancePanel } from "@/components/admin/SystemPanels";
import Seo from "@/components/Seo";
import { ShieldIcon } from "@/components/icons";

export default function AdminSecurityPage() {
  return (
    <div className="space-y-6">
      <Seo
        title="Security"
        description="Operational failures and rejected access attempts, plus the audit trail of administrative overrides."
      />

      <PageHeader
        icon={ShieldIcon}
        eyebrow="Administration"
        title="Security & Error Monitor"
        description="Operational failures and rejected access attempts, plus the audit trail of administrative overrides."
      />

      <SecurityMonitor />

      <PerformancePanel />

      <AuditLogPanel limit={50} />
    </div>
  );
}
