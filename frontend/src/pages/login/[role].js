import { useRouter } from "next/router";
import PortalAuthForm from "@/components/PortalAuthForm";
import { ArrowLeftIcon, CompassIcon } from "@/components/icons";
import { Button, EmptyState, Spinner } from "@/components/ui";
import { findPortal } from "@/services/auth";

export default function PortalLoginPage() {
  const router = useRouter();
  const slug = router.query.role;
  const portal = findPortal(slug);

  if (!slug) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <Spinner className="h-6 w-6" label="Opening portal…" />
      </div>
    );
  }

  if (!portal) {
    return (
      <div className="mx-auto max-w-md py-16">
        <EmptyState
          icon={CompassIcon}
          title="Unknown portal"
          description={`"${slug}" is not a valid role portal. Head back to the portal list and choose your role.`}
          action={
            <Button variant="secondary" href="/login" icon={ArrowLeftIcon}>
              All portals
            </Button>
          }
        />
      </div>
    );
  }

  return <PortalAuthForm portal={portal} mode="login" />;
}
