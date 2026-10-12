// Lightweight inline SVG icon set (lucide-style strokes).

function StrokeIcon({ className, children, strokeWidth = 1.8 }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      {children}
    </svg>
  );
}

// Two arrows in a loop — returning / repeat activity.
export function RepeatIcon({ className = "h-4 w-4" }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="m17 2 4 4-4 4" />
      <path d="M3 11v-1a4 4 0 0 1 4-4h14" />
      <path d="m7 22-4-4 4-4" />
      <path d="M21 13v1a4 4 0 0 1-4 4H3" />
    </svg>
  );
}

export function SparkleIcon({ className = "h-5 w-5" }) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" className={className} aria-hidden="true">
      <path d="M12 2l2.35 7.65L22 12l-7.65 2.35L12 22l-2.35-7.65L2 12l7.65-2.35L12 2z" />
    </svg>
  );
}

export function HandIcon({ className = "h-5 w-5" }) {
  return (
    <StrokeIcon className={className}>
      <path d="M18 11V6a2 2 0 0 0-4 0v5" />
      <path d="M14 10V4a2 2 0 0 0-4 0v2" />
      <path d="M10 10.5V6a2 2 0 0 0-4 0v8" />
      <path d="M18 8a2 2 0 1 1 4 0v6a8 8 0 0 1-8 8h-2c-2.8 0-4.5-.86-5.99-2.34l-3.6-3.6a2 2 0 0 1 2.83-2.82L7 15" />
    </StrokeIcon>
  );
}

export function CardsIcon({ className = "h-5 w-5" }) {
  return (
    <StrokeIcon className={className}>
      <rect x="3" y="5" width="13" height="17" rx="2" />
      <path d="M8 5V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v13a2 2 0 0 1-2 2h-1" />
    </StrokeIcon>
  );
}

export function ScanIcon({ className = "h-5 w-5" }) {
  return (
    <StrokeIcon className={className}>
      <path d="M3 7V5a2 2 0 0 1 2-2h2" />
      <path d="M17 3h2a2 2 0 0 1 2 2v2" />
      <path d="M21 17v2a2 2 0 0 1-2 2h-2" />
      <path d="M7 21H5a2 2 0 0 1-2-2v-2" />
      <circle cx="12" cy="12" r="3.5" />
    </StrokeIcon>
  );
}

export function ShieldIcon({ className = "h-5 w-5" }) {
  return (
    <StrokeIcon className={className}>
      <path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1 1 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z" />
      <path d="m9 12 2 2 4-4" />
    </StrokeIcon>
  );
}

export function ArrowRightIcon({ className = "h-4 w-4" }) {
  return (
    <StrokeIcon className={className} strokeWidth={2}>
      <path d="M5 12h14" />
      <path d="m12 5 7 7-7 7" />
    </StrokeIcon>
  );
}

export function ArrowLeftIcon({ className = "h-4 w-4" }) {
  return (
    <StrokeIcon className={className} strokeWidth={2}>
      <path d="M19 12H5" />
      <path d="m12 19-7-7 7-7" />
    </StrokeIcon>
  );
}

export function UploadIcon({ className = "h-5 w-5" }) {
  return (
    <StrokeIcon className={className}>
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <path d="m17 8-5-5-5 5" />
      <path d="M12 3v12" />
    </StrokeIcon>
  );
}

export function RetryIcon({ className = "h-4 w-4" }) {
  return (
    <StrokeIcon className={className} strokeWidth={2}>
      <path d="M21 12a9 9 0 1 1-2.64-6.36L21 8" />
      <path d="M21 3v5h-5" />
    </StrokeIcon>
  );
}

export function CheckIcon({ className = "h-4 w-4" }) {
  return (
    <StrokeIcon className={className} strokeWidth={2.2}>
      <path d="M20 6 9 17l-5-5" />
    </StrokeIcon>
  );
}

export function MenuIcon({ className = "h-5 w-5" }) {
  return (
    <StrokeIcon className={className} strokeWidth={2}>
      <path d="M4 6h16" />
      <path d="M4 12h16" />
      <path d="M4 18h16" />
    </StrokeIcon>
  );
}

export function CloseIcon({ className = "h-5 w-5" }) {
  return (
    <StrokeIcon className={className} strokeWidth={2}>
      <path d="M18 6 6 18" />
      <path d="m6 6 12 12" />
    </StrokeIcon>
  );
}

export function CameraIcon({ className = "h-5 w-5" }) {
  return (
    <StrokeIcon className={className}>
      <path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z" />
      <circle cx="12" cy="13" r="3" />
    </StrokeIcon>
  );
}

// Extended icon set.

export function FileTextIcon({ className = "h-4 w-4" }) {
  return (
    <StrokeIcon className={className}>
      <path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7z" />
      <path d="M14 2v5h6" />
      <path d="M9 13h6" />
      <path d="M9 17h6" />
    </StrokeIcon>
  );
}

export function TableIcon({ className = "h-4 w-4" }) {
  return (
    <StrokeIcon className={className}>
      <rect x="3" y="4" width="18" height="16" rx="2" />
      <path d="M3 10h18" />
      <path d="M9 10v10" />
      <path d="M15 10v10" />
    </StrokeIcon>
  );
}

export function TrashIcon({ className = "h-4 w-4" }) {
  return (
    <StrokeIcon className={className}>
      <path d="M3 6h18" />
      <path d="M8 6V4a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v2" />
      <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6" />
      <path d="M10 11v6" />
      <path d="M14 11v6" />
    </StrokeIcon>
  );
}

export function DownloadIcon({ className = "h-4 w-4" }) {
  return (
    <StrokeIcon className={className}>
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <path d="m7 10 5 5 5-5" />
      <path d="M12 15V3" />
    </StrokeIcon>
  );
}

export function ChartIcon({ className = "h-4 w-4" }) {
  return (
    <StrokeIcon className={className}>
      <path d="M3 3v16a2 2 0 0 0 2 2h16" />
      <path d="M7 15v-3" />
      <path d="M12 15V8" />
      <path d="M17 15v-5" />
    </StrokeIcon>
  );
}

export function ActivityIcon({ className = "h-4 w-4" }) {
  return (
    <StrokeIcon className={className}>
      <path d="M22 12h-4l-3 8-6-16-3 8H2" />
    </StrokeIcon>
  );
}

export function UserIcon({ className = "h-4 w-4" }) {
  return (
    <StrokeIcon className={className}>
      <circle cx="12" cy="8" r="4" />
      <path d="M5 21c0-3.9 3.1-7 7-7s7 3.1 7 7" />
    </StrokeIcon>
  );
}

export function UsersIcon({ className = "h-4 w-4" }) {
  return (
    <StrokeIcon className={className}>
      <circle cx="9" cy="8" r="3.5" />
      <path d="M2.5 20c0-3.6 2.9-6.5 6.5-6.5s6.5 2.9 6.5 6.5" />
      <path d="M16 4.6a3.5 3.5 0 0 1 0 6.8" />
      <path d="M17.8 14.1a6.5 6.5 0 0 1 3.7 5.9" />
    </StrokeIcon>
  );
}

export function ClockIcon({ className = "h-4 w-4" }) {
  return (
    <StrokeIcon className={className}>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v5l3 2" />
    </StrokeIcon>
  );
}

export function CalendarIcon({ className = "h-4 w-4" }) {
  return (
    <StrokeIcon className={className}>
      <rect x="3" y="5" width="18" height="16" rx="2" />
      <path d="M3 10h18" />
      <path d="M8 3v4" />
      <path d="M16 3v4" />
    </StrokeIcon>
  );
}

export function CheckCircleIcon({ className = "h-5 w-5" }) {
  return (
    <StrokeIcon className={className}>
      <circle cx="12" cy="12" r="9" />
      <path d="m8.5 12 2.5 2.5 5-5" />
    </StrokeIcon>
  );
}

export function AlertIcon({ className = "h-5 w-5" }) {
  return (
    <StrokeIcon className={className}>
      <path d="M10.3 3.9 1.9 18a2 2 0 0 0 1.7 3h16.8a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z" />
      <path d="M12 9v4" />
      <path d="M12 17h.01" />
    </StrokeIcon>
  );
}

export function InfoIcon({ className = "h-4 w-4" }) {
  return (
    <StrokeIcon className={className}>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 11v5" />
      <path d="M12 8h.01" />
    </StrokeIcon>
  );
}

export function SearchIcon({ className = "h-4 w-4" }) {
  return (
    <StrokeIcon className={className}>
      <circle cx="11" cy="11" r="7" />
      <path d="m20 20-3.5-3.5" />
    </StrokeIcon>
  );
}

export function EyeIcon({ className = "h-4 w-4" }) {
  return (
    <StrokeIcon className={className}>
      <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7z" />
      <circle cx="12" cy="12" r="3" />
    </StrokeIcon>
  );
}

export function LogOutIcon({ className = "h-4 w-4" }) {
  return (
    <StrokeIcon className={className}>
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
      <path d="m16 17 5-5-5-5" />
      <path d="M21 12H9" />
    </StrokeIcon>
  );
}

export function PencilIcon({ className = "h-4 w-4" }) {
  return (
    <StrokeIcon className={className}>
      <path d="M17 3a2.8 2.8 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5z" />
    </StrokeIcon>
  );
}

export function SendIcon({ className = "h-4 w-4" }) {
  return (
    <StrokeIcon className={className}>
      <path d="m22 2-7 20-4-9-9-4z" />
      <path d="M22 2 11 13" />
    </StrokeIcon>
  );
}

export function ChatIcon({ className = "h-5 w-5" }) {
  return (
    <StrokeIcon className={className}>
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
    </StrokeIcon>
  );
}

export function TrendingUpIcon({ className = "h-4 w-4" }) {
  return (
    <StrokeIcon className={className}>
      <path d="m22 7-8.5 8.5-5-5L2 17" />
      <path d="M16 7h6v6" />
    </StrokeIcon>
  );
}

export function CompassIcon({ className = "h-5 w-5" }) {
  return (
    <StrokeIcon className={className}>
      <circle cx="12" cy="12" r="9" />
      <path d="m15.5 8.5-2 5-5 2 2-5z" />
    </StrokeIcon>
  );
}

// Dashboard / workspace home tile.
export function LayoutGridIcon({ className = "h-4 w-4" }) {
  return (
    <StrokeIcon className={className}>
      <rect x="3" y="3" width="7" height="7" rx="1.5" />
      <rect x="14" y="3" width="7" height="7" rx="1.5" />
      <rect x="3" y="14" width="7" height="7" rx="1.5" />
      <rect x="14" y="14" width="7" height="7" rx="1.5" />
    </StrokeIcon>
  );
}

// Filter controls (sliders).
export function SlidersIcon({ className = "h-4 w-4" }) {
  return (
    <StrokeIcon className={className}>
      <path d="M4 21v-7" />
      <path d="M4 10V3" />
      <path d="M12 21v-9" />
      <path d="M12 8V3" />
      <path d="M20 21v-5" />
      <path d="M20 12V3" />
      <path d="M1 14h6" />
      <path d="M9 8h6" />
      <path d="M17 16h6" />
    </StrokeIcon>
  );
}

// Sort control (ascending / descending).
export function ArrowUpDownIcon({ className = "h-4 w-4" }) {
  return (
    <StrokeIcon className={className}>
      <path d="m7 15 5 5 5-5" />
      <path d="m7 9 5-5 5 5" />
      <path d="M12 3v18" />
    </StrokeIcon>
  );
}

// Share action.
export function ShareIcon({ className = "h-4 w-4" }) {
  return (
    <StrokeIcon className={className}>
      <path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8" />
      <path d="M16 6l-4-4-4 4" />
      <path d="M12 2v13" />
    </StrokeIcon>
  );
}

// Add / create action.
export function PlusIcon({ className = "h-4 w-4" }) {
  return (
    <StrokeIcon className={className}>
      <path d="M12 5v14" />
      <path d="M5 12h14" />
    </StrokeIcon>
  );
}

// Settings gear (simplified, stroke-based).
export function SettingsIcon({ className = "h-4 w-4" }) {
  return (
    <StrokeIcon className={className}>
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.7 1.7 0 0 0 .34 1.87l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.7 1.7 0 0 0-1.87-.34 1.7 1.7 0 0 0-1.03 1.56V21a2 2 0 1 1-4 0v-.11a1.7 1.7 0 0 0-1.11-1.56 1.7 1.7 0 0 0-1.87.34l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.7 1.7 0 0 0 4.6 15a1.7 1.7 0 0 0-1.56-1.03H3a2 2 0 1 1 0-4h.11A1.7 1.7 0 0 0 4.67 8.9a1.7 1.7 0 0 0-.34-1.87l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.7 1.7 0 0 0 1.87.34H9a1.7 1.7 0 0 0 1-1.56V3a2 2 0 1 1 4 0v.11a1.7 1.7 0 0 0 1.03 1.56 1.7 1.7 0 0 0 1.87-.34l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.7 1.7 0 0 0-.34 1.87V9a1.7 1.7 0 0 0 1.56 1H21a2 2 0 1 1 0 4h-.11a1.7 1.7 0 0 0-1.49 1z" />
    </StrokeIcon>
  );
}

// Bell — notifications.
export function BellIcon({ className = "h-4 w-4" }) {
  return (
    <StrokeIcon className={className}>
      <path d="M15 17h5l-1.4-1.4A2 2 0 0 1 18 14.2V11a6 6 0 0 0-4-5.7V5a2 2 0 1 0-4 0v.3C7.7 6.2 6 8.4 6 11v3.2c0 .5-.2 1-.6 1.4L4 17h5" />
      <path d="M15 17v1a3 3 0 1 1-6 0v-1" />
    </StrokeIcon>
  );
}

// Play / resume action.
export function PlayIcon({ className = "h-4 w-4" }) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" className={className} aria-hidden="true">
      <path d="M7 4.5v15l12-7.5z" />
    </svg>
  );
}

// Sparkle cluster — used for AI-generated surfaces.
export function SparklesIcon({ className = "h-4 w-4" }) {
  return (
    <StrokeIcon className={className}>
      <path d="M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9z" />
      <path d="M18.5 15.5l.8 2.2 2.2.8-2.2.8-.8 2.2-.8-2.2-2.2-.8 2.2-.8z" />
    </StrokeIcon>
  );
}

// Video camera — the "join session" affordance used by the live consultation & booking module (Google Meet links).
export function VideoIcon({ className = "h-4 w-4" }) {
  return (
    <StrokeIcon className={className}>
      <rect x="2" y="6" width="14" height="12" rx="2" />
      <path d="m16 10.5 6-3.5v10l-6-3.5z" />
    </StrokeIcon>
  );
}

export function ImageIcon({ className = "h-5 w-5" }) {
  return (
    <StrokeIcon className={className}>
      <rect x="3" y="3" width="18" height="18" rx="2" />
      <circle cx="9" cy="9" r="2" />
      <path d="m21 15-4.4-4.4a2 2 0 0 0-2.8 0L5 19" />
    </StrokeIcon>
  );
}

export function ListIcon({ className = "h-4 w-4" }) {
  return (
    <StrokeIcon className={className}>
      <path d="M8 6h13" />
      <path d="M8 12h13" />
      <path d="M8 18h13" />
      <path d="M3.5 6h.01" />
      <path d="M3.5 12h.01" />
      <path d="M3.5 18h.01" />
    </StrokeIcon>
  );
}

export function ChevronDownIcon({ className = "h-4 w-4" }) {
  return (
    <StrokeIcon className={className} strokeWidth={2}>
      <path d="m6 9 6 6 6-6" />
    </StrokeIcon>
  );
}

export function BrainIcon({ className = "h-4 w-4" }) {
  return (
    <StrokeIcon className={className}>
      <path d="M12 5a3 3 0 1 0-5.9.8 3 3 0 0 0-1.9 5.4 3 3 0 0 0 1.3 5.4A3 3 0 1 0 12 19z" />
      <path d="M12 5a3 3 0 1 1 5.9.8 3 3 0 0 1 1.9 5.4 3 3 0 0 1-1.3 5.4A3 3 0 1 1 12 19z" />
      <path d="M12 5v14" />
    </StrokeIcon>
  );
}

export function HeartIcon({ className = "h-4 w-4" }) {
  return (
    <StrokeIcon className={className}>
      <path d="M19 14c1.5-1.5 3-3.3 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.8 0-3.4 1-4.5 2.5C10.9 4 9.3 3 7.5 3A5.5 5.5 0 0 0 2 8.5c0 2.2 1.5 4 3 5.5l7 7z" />
    </StrokeIcon>
  );
}

export function StarIcon({ className = "h-4 w-4" }) {
  return (
    <StrokeIcon className={className}>
      <path d="m12 3 2.7 5.7 6.3.9-4.5 4.4 1 6.2-5.5-3-5.5 3 1-6.2L3 9.6l6.3-.9z" />
    </StrokeIcon>
  );
}

export function CopyIcon({ className = "h-4 w-4" }) {
  return (
    <StrokeIcon className={className}>
      <rect x="9" y="9" width="12" height="12" rx="2" />
      <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
    </StrokeIcon>
  );
}

export function TargetIcon({ className = "h-4 w-4" }) {
  return (
    <StrokeIcon className={className}>
      <circle cx="12" cy="12" r="9" />
      <circle cx="12" cy="12" r="5" />
      <circle cx="12" cy="12" r="1.2" />
    </StrokeIcon>
  );
}
