// Approved brand mark A — deep violet tile + gold ✦ (spec §4.6).
import { SparkleIcon } from "@/components/icons";

export default function BrandMark({ size = "sm", className = "" }) {
  const box = size === "lg" ? "h-[38px] w-[38px] rounded-[11px]" : "h-8 w-8 rounded-[9px]";
  const star = size === "lg" ? "h-5 w-5" : "h-4 w-4";
  return (
    <span
      aria-hidden="true"
      className={`flex shrink-0 items-center justify-center bg-gradient-to-br from-primary-600 to-primary-700 text-accent-300 shadow-[0_4px_10px_-3px_rgba(124,58,237,0.5)] ${box} ${className}`}
    >
      <SparkleIcon className={star} />
    </span>
  );
}
