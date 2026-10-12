import { useEffect } from "react";
import { useRouter } from "next/router";
import { useAuth } from "@/hooks/useAuth";
import { pageAccess } from "@/lib/roles";

// Route guard for restricted pages.
export function useRoleGuard() {
  const router = useRouter();
  const { user, loading } = useAuth();
  const blocked =
    !loading && !!user && pageAccess(router.pathname, user.role) === false;

  useEffect(() => {
    if (blocked) {
      router.replace(`/dashboard?blocked=${encodeURIComponent(router.asPath)}`);
    }
  }, [blocked, router, router.asPath]);

  return blocked;
}
