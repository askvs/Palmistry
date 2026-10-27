export function NotificationBadge({ count, className = "", animate = true }) {
  if (!count || count <= 0) return null;

  const displayCount = count > 99 ? "99+" : count.toString();

  return (
    <span
      key={animate ? displayCount : "static"}
      className={`absolute -top-1 -right-1 min-w-[20px] h-[20px] rounded-full bg-rose-500 text-white text-xs font-semibold flex items-center justify-center px-1 ${
        animate ? "animate-badge-pop" : ""
      } ${className}`}
    >
      {displayCount}
    </span>
  );
}
