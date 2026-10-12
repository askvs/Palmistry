import { useEffect } from "react";
import { useRouter } from "next/router";

// Consultant entry point redirecting to the dashboard.
export default function ConsultantIndexPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/consultant/dashboard");
  }, [router]);

  return null;
}
