// Roles: labels, navigation, and route access.
import {
  ArrowLeftIcon,
  BellIcon,
  CalendarIcon,
  CardsIcon,
  ChartIcon,
  CompassIcon,
  FileTextIcon,
  LayoutGridIcon,
  SettingsIcon,
  ShieldIcon,
  UserIcon,
  UsersIcon,
} from "@/components/icons";

// Nav entries by key.
export const NAV_ITEMS = {
  home: { href: "/", label: "Home" },
  tarot: { href: "/readings/tarot", label: "Tarot Sanctuary" },
  palm: { href: "/readings/palm", label: "Palm Reading" },
  archives: { href: "/readings", label: "Archives" },
  life_trends: { href: "/life-trends", label: "Life Trends" },
  personality: { href: "/personality", label: "Personality" },
  // Live consultation and booking.
  consultants: { href: "/consultants", label: "Find a Consultant" },
  sessions: { href: "/sessions", label: "My Sessions" },
  consultant_studio: { href: "/consultant-studio", label: "Consultant Studio" },
  // Reader workspace.
  reader_reports: { href: "/reader/reports", label: "Reading Reports" },
  reader_spreads: { href: "/reader/spreads", label: "Spread Studio" },
};
// Consultant workspace routes.
export const CONSULTANT_ROUTES = [
  { href: "/consultant/dashboard", label: "Dashboard", icon: LayoutGridIcon },
  { href: "/consultant/clients", label: "Clients", icon: UsersIcon },
  { href: "/consultant/consultations", label: "Consultations", icon: CalendarIcon },
  { href: "/consultant/insights", label: "Insights", icon: ChartIcon },
  { href: "/consultant/reports", label: "Reports", icon: FileTextIcon },
];

// Secondary consultant links.
export const CONSULTANT_SECONDARY_ROUTES = [
  { href: "/notifications", label: "Notifications", icon: BellIcon },
  { href: "/profile", label: "Profile", icon: UserIcon },
];

// Title and breadcrumb per consultant route.
export const CONSULTANT_PAGE_META = {
  "/consultant": { title: "Consultant Portal", crumb: "Overview" },
  "/consultant/dashboard": { title: "Consultant Dashboard", crumb: "Overview" },
  "/consultant/clients": { title: "My Clients", crumb: "Clients" },
  "/consultant/consultations": { title: "Consultations", crumb: "Consultations" },
  "/consultant/insights": { title: "Guidance Insights", crumb: "Insights" },
  "/consultant/reports": { title: "Consultation Reports", crumb: "Reports" },
};

// Breadcrumb for dynamic consultant routes.
export const CONSULTANT_DYNAMIC_META = {
  "/consultant/clients/[clientId]": { crumb: "Client profile" },
  "/consultant/consultations/[consultationId]": { crumb: "Consultation workspace" },
};

// Admin console routes.
export const ADMIN_ROUTES = [
  { href: "/admin", label: "Overview", icon: LayoutGridIcon },
  { href: "/admin/users", label: "User Governance", icon: UsersIcon },
  { href: "/admin/analytics", label: "Platform Analytics", icon: ChartIcon },
  { href: "/admin/security", label: "Security & Errors", icon: ShieldIcon },
  { href: "/admin/system", label: "System", icon: SettingsIcon },
  { href: "/admin/reports", label: "System Reports", icon: FileTextIcon },
];

// Secondary admin links.
export const ADMIN_SECONDARY_ROUTES = [
  { href: "/notifications", label: "Notifications", icon: BellIcon },
  { href: "/profile", label: "Profile", icon: UserIcon },
];

// Title and breadcrumb per admin route.
export const ADMIN_PAGE_META = {
  "/admin": { title: "Platform Overview", crumb: "Overview" },
  "/admin/users": { title: "User Governance", crumb: "Users" },
  "/admin/analytics": { title: "Platform Analytics", crumb: "Analytics" },
  "/admin/security": { title: "Security & Error Monitor", crumb: "Security" },
  "/admin/system": { title: "System & Configuration", crumb: "System" },
  "/admin/reports": { title: "System Reports", crumb: "Reports" },
};

export const BACK_TO_CLIENTS = { href: "/consultant/clients", label: "Back to Clients", icon: ArrowLeftIcon };

// Guest navigation.
export const GUEST_NAV_KEYS = ["home", "tarot", "palm"];

export const ROLES = {
  user: {
    key: "user",
    label: "Seeker",
    badgeTone: "primary",
    icon: UserIcon,
    navKeys: [
      "home",
      "tarot",
      "palm",
      "archives",
      "life_trends",
      "personality",
      "consultants",
      "sessions",
    ],
    dashboardLabel: "Dashboard",
    dashboardCta: { href: "/readings/palm", label: "Start a palm reading" },
  },
  tarot_reader: {
    key: "tarot_reader",
    label: "Reader",
    badgeTone: "accent",
    icon: CardsIcon,
    // Staff craft tools plus booking surfaces.
    navKeys: [
      "home",
      "tarot",
      "archives",
      "reader_reports",
      "reader_spreads",
      "consultants",
      "sessions",
      "consultant_studio",
    ],
    dashboardLabel: "Reader Sanctuary",
    dashboardCta: { href: "/readings/tarot", label: "Open the tarot ritual" },
  },
  spiritual_consultant: {
    key: "spiritual_consultant",
    label: "Consultant",
    badgeTone: "emerald",
    icon: CompassIcon,
    navKeys: ["home", "consultants", "sessions", "consultant_studio"],
    dashboardLabel: "Consultant Portal",
    // No CTA; the workspace queue is the consultant entry point.
    dashboardCta: null,
    // Consultant console shell.
    workspace: { href: "/consultant/dashboard", label: "Consultant workspace" },
  },
  admin: {
    key: "admin",
    label: "Admin",
    badgeTone: "indigo",
    icon: ShieldIcon,
    // Governance only; session volume lives on Session Oversight.
    navKeys: ["home"],
    dashboardLabel: "Admin Console",
    dashboardCta: null,
    // Admin console shell.
    workspace: { href: "/admin", label: "Admin console" },
  },
};

export const DEFAULT_ROLE = ROLES.user;

export function roleMeta(role) {
  return ROLES[role] || DEFAULT_ROLE;
}

// Seeker-only pages; staff redirect to their dashboard.
export const SEEKER_ONLY_PAGES = {
  "/life-trends": { allowed: ["user"], feature: "life trends" },
  "/personality": { allowed: ["user"], feature: "personality insights" },
};

// Staff-only route prefixes.
export const STAFF_ONLY_PREFIXES = [
  { prefix: "/consultant", allowed: ["spiritual_consultant"], feature: "consultant workspace" },
  { prefix: "/admin", allowed: ["admin"], feature: "admin console" },
  { prefix: "/reader", allowed: ["tarot_reader"], feature: "reader workspace" },
  // Booking studio and session hub.
  {
    prefix: "/consultant-studio",
    allowed: ["tarot_reader", "spiritual_consultant"],
    feature: "consultant studio",
  },
  // Session hub without admins.
  {
    prefix: "/sessions",
    allowed: ["user", "tarot_reader", "spiritual_consultant"],
    feature: "session hub",
  },
];

// Prefix rule matching a pathname.
function staffPrefixRule(pathname) {
  return STAFF_ONLY_PREFIXES.find(
    (rule) => pathname === rule.prefix || pathname.startsWith(`${rule.prefix}/`)
  );
}

// Whether a role may open a pathname.
export function pageAccess(pathname, role) {
  const rule = SEEKER_ONLY_PAGES[pathname];
  if (rule) return rule.allowed.includes(role);

  const prefixRule = staffPrefixRule(pathname);
  if (prefixRule) return prefixRule.allowed.includes(role);

  return null;
}

// Reason a role was turned away from a pathname.
export function blockedPageInfo(pathname, role) {
  if (pageAccess(pathname, role) !== false) return null;
  const seekerRule = SEEKER_ONLY_PAGES[pathname];
  const prefixRule = staffPrefixRule(pathname);
  if (seekerRule) return { feature: seekerRule.feature };
  if (prefixRule) return { feature: prefixRule.feature };
  return null;
}

