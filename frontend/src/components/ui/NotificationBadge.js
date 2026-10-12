export function NotificationBadge({ count, className = "" }) {
  if (!count || count <= 0) return null;

  const displayCount = count > 99 ? "99+" : count.toString();

  return (
    <span
      className={`absolute -top-1 -right-1 min-w-[20px] h-[20px] rounded-full bg-rose-500 text-white text-xs font-semibold flex items-center justify-center px-1 ${className}`}
    >
      {displayCount}
    </span>
  );
}