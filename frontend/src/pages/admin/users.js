// Admin user governance: roles, suspension, and audit trail.
import { PageHeader } from "@/components/ui";
import UserGovernancePanel from "@/components/admin/UserGovernancePanel";
import AuditLogPanel from "@/components/admin/AuditLogPanel";
import { PermissionsPanel } from "@/components/admin/SystemPanels";
import Seo from "@/components/Seo";
import { UsersIcon } from "@/components/icons";

export default function AdminUsersPage() {
  return (
    <div className="space-y-6">
      <Seo title="Users" description="Accounts, roles and access across the platform." />

      <PageHeader
        icon={UsersIcon}
        eyebrow="Administration"
        title="User Governance"
        description="Manage identities, assign role permissions, and revoke access when an account must be suspended."
      />

      <UserGovernancePanel />

      <PermissionsPanel />

      <AuditLogPanel limit={25} />
    </div>
  );
}
