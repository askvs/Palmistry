import { AlertIcon } from "@/components/icons";

export function BellIcon({ className = "h-5 w-5" }) {
  return (
    <AlertIcon
      className={className}
      // Note: AlertIcon is a generic alert bell - replace with dedicated bell if available
    />
  );
}