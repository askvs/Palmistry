// Admin system: RBAC matrix, auth posture, config, reports, and performance.
import { PageHeader } from "@/components/ui";
import { AuthSettingsPanel, PermissionsPanel, SystemConfigPanel } from "@/components/admin/SystemPanels";
import { SystemStatusPanel } from "@/components/admin/AnalyticsPanels";
import { useAsyncData } from "@/hooks/useAsyncData";
import { fetchSystemHealth } from "@/services/roles";
import { SettingsIcon } from "@/components/icons";

export default function AdminSystemPage() {
  const { data: health } = useAsyncData(fetchSystemHealth);

  return (
    <div className="space-y-6">
      <PageHeader
        icon={SettingsIcon}
        eyebrow="Administration"
        title="System & Configuration"
        description="Access permissions, authentication settings, deployment information and application performance."
      />

      <PermissionsPanel />

      <AuthSettingsPanel />

      <SystemConfigPanel />

      <div className="grid gap-5 lg:grid-cols-2">
        <SystemStatusPanel health={health} />
      </div>
    </div>
  );
}
