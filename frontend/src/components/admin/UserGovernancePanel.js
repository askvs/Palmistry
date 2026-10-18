// User governance for the administrator (FR-007, §49.3).
import { useCallback, useEffect, useState } from "react";
import {
  Badge,
  Button,
  EmptyState,
  InlineError,
  Panel,
  SkeletonRow,
  useToast,
} from "@/components/ui";
import { Segmented } from "@/components/dashboards/shared";
import { useAsyncData } from "@/hooks/useAsyncData";
import { adminListUsers, adminUpdateUser } from "@/services/roles";
import { ROLES, roleMeta } from "@/lib/roles";
import { SearchIcon, UsersIcon } from "@/components/icons";

const ROLE_OPTIONS = Object.keys(ROLES);

const ROLE_FILTERS = [{ value: "", label: "All roles" }, ...ROLE_OPTIONS.map((role) => ({ value: role, label: roleMeta(role).label }))];

const STATUS_FILTERS = [
  { value: "", label: "All" },
  { value: "active", label: "Active" },
  { value: "disabled", label: "Disabled" },
];

export default function UserGovernancePanel() {
  const toast = useToast();
  const [roleFilter, setRoleFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [actionError, setActionError] = useState(null);

  useEffect(() => {
    const timer = setTimeout(() => setSearchQuery(searchInput.trim()), 350);
    return () => clearTimeout(timer);
  }, [searchInput]);

  const usersLoader = useCallback(
    () =>
      adminListUsers({
        role: roleFilter || undefined,
        search: searchQuery || undefined,
        limit: 200,
      }),
    [roleFilter, searchQuery]
  );
  const {
    data: usersData,
    error: usersError,
    loading: usersLoading,
    refresh: refreshUsers,
  } = useAsyncData(usersLoader);

  const users = usersData?.items || [];

  async function changeRole(user, role) {
    setActionError(null);
    try {
      await adminUpdateUser(user.id, { role });
      toast.success("Role updated", `${user.email} is now ${roleMeta(role).label}.`);
      await refreshUsers();
    } catch (err) {
      setActionError(err.message);
    }
  }

  async function toggleActive(user) {
    setActionError(null);
    try {
      await adminUpdateUser(user.id, { is_active: !user.is_active });
      toast.success(
        "Account updated",
        `${user.email} was ${user.is_active ? "suspended" : "reactivated"}.`
      );
      await refreshUsers();
    } catch (err) {
      setActionError(err.message);
    }
  }

  const visible = statusFilter
    ? users.filter((u) => (statusFilter === "active" ? u.is_active : !u.is_active))
    : users;

  return (
    <Panel
      title="User Governance & Role Management"
      subtitle="Manage identities, assign role permissions, or revoke access"
      action={
        <div className="flex flex-wrap items-center gap-2">
          <div className="relative w-56">
            <SearchIcon className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Search email or name…"
              aria-label="Search users by email or name"
              className="w-full rounded-xl border border-slate-200 bg-slate-50 py-1.5 pl-9 pr-3 text-xs text-slate-800 transition placeholder:text-slate-500 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600"
            />
          </div>
          <select
            value={roleFilter}
            onChange={(e) => setRoleFilter(e.target.value)}
            aria-label="Filter users by role"
            className="cursor-pointer rounded-xl border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-700 transition focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600"
          >
            {ROLE_FILTERS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
          <Segmented
            label="Account status filter"
            value={statusFilter}
            onChange={setStatusFilter}
            options={STATUS_FILTERS}
          />
        </div>
      }
    >
      {usersError ? (
        <InlineError message={usersError.message} />
      ) : usersLoading ? (
        <div className="space-y-3 py-2">
          <SkeletonRow lines={3} />
          <SkeletonRow lines={3} />
          <SkeletonRow lines={3} />
        </div>
      ) : visible.length === 0 ? (
        <EmptyState
          icon={UsersIcon}
          title="No users found"
          description={
            searchQuery || roleFilter || statusFilter
              ? "No accounts match the current filters."
              : "Accounts appear here once users register."
          }
        />
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-xs uppercase tracking-wider text-slate-500">
                <th className="py-2.5 pr-4">Email</th>
                <th className="py-2.5 pr-4">Name</th>
                <th className="py-2.5 pr-4">Assigned Role</th>
                <th className="py-2.5 pr-4">Joined</th>
                <th className="py-2.5 pr-4">Status</th>
                <th className="py-2.5">Actions</th>
              </tr>
            </thead>
            <tbody>
              {visible.map((u) => (
                <tr
                  key={u.id}
                  className="border-b border-slate-100 transition last:border-0 hover:bg-slate-50/60"
                >
                  <td className="py-3 pr-4 font-medium text-slate-800">{u.email}</td>
                  <td className="py-3 pr-4 text-slate-600">{u.full_name || "—"}</td>
                  <td className="py-3 pr-4">
                    <select
                      value={u.role}
                      onChange={(e) => changeRole(u, e.target.value)}
                      className="cursor-pointer rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-xs font-medium text-slate-700 transition focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600"
                      aria-label={`Role for ${u.email}`}
                    >
                      {ROLE_OPTIONS.map((role) => (
                        <option key={role} value={role}>
                          {roleMeta(role).label}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td className="py-3 pr-4 text-xs text-slate-500">
                    {new Date(u.created_at).toLocaleDateString()}
                  </td>
                  <td className="py-3 pr-4">
                    <Badge tone={u.is_active ? "emerald" : "rose"}>
                      {u.is_active ? "Active" : "Disabled"}
                    </Badge>
                  </td>
                  <td className="py-3">
                    <Button
                      size="sm"
                      variant={u.is_active ? "dangerGhost" : "secondary"}
                      onClick={() => toggleActive(u)}
                    >
                      {u.is_active ? "Suspend" : "Activate"}
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="mt-3 text-xs text-slate-500">
            Showing {visible.length} of {usersData?.total ?? visible.length} account(s)
            {searchQuery || roleFilter || statusFilter ? " matching the current filters" : ""}.
          </p>
        </div>
      )}
    </Panel>
  );
}
