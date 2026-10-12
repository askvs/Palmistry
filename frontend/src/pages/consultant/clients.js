// My Clients: searchable roster assembled from live queue and demo profiles.
import Head from "next/head";
import { useCallback, useState } from "react";
import { useRouter } from "next/router";
import { PageHeader } from "@/components/ui";
import { useAsyncData } from "@/hooks/useAsyncData";
import { useAuth } from "@/hooks/useAuth";
import { UsersIcon } from "@/components/icons";
import { fetchConsultantClients } from "@/services/consultant";
import ClientDirectory from "@/components/consultant/ClientDirectory";
import StartConsultationDialog from "@/components/consultant/StartConsultationDialog";

export default function ConsultantClientsPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();

  const initialSearch =
    typeof router.query.search === "string" ? router.query.search : "";
  const [search, setSearch] = useState(initialSearch);
  const [status, setStatus] = useState("all");
  const [sort, setSort] = useState("recent");
  const [startClientId, setStartClientId] = useState("");
  const [startOpen, setStartOpen] = useState(false);

  const loader = useCallback(
    () => fetchConsultantClients({ search, status, sort }),
    [search, status, sort]
  );
  const { data, error, loading, refresh } = useAsyncData(loader, {
    enabled: !authLoading && !!user,
  });

  return (
    <div className="animate-fade-in space-y-8">
      <Head>
        <title>My Clients | Palmistry &amp; Tarot</title>
      </Head>

      <PageHeader
        icon={UsersIcon}
        tileTone="emerald"
        eyebrow="Spiritual Consultant"
        title="My Clients"
        description="View client profiles, reading history and consultation insights. Open a client to review their palm, tarot and personality signals before you start a session."
      />

      <ClientDirectory
        clients={data?.clients || []}
        source={data?.source}
        total={data?.total || 0}
        loading={loading}
        error={error}
        onRetry={refresh}
        search={search}
        onSearchChange={setSearch}
        status={status}
        onStatusChange={setStatus}
        sort={sort}
        onSortChange={setSort}
        onStartConsultation={(client) => {
          setStartClientId(client.id);
          setStartOpen(true);
        }}
      />

      {startOpen && (
        <StartConsultationDialog
          key={startClientId || "new-session"}
          open
          clients={data?.clients || []}
          preselectedClientId={startClientId}
          onClose={() => setStartOpen(false)}
          onCreated={(session) => {
            setStartOpen(false);
            refresh();
            if (session?.id) router.push(`/consultant/consultations/${session.id}`);
          }}
        />
      )}
    </div>
  );
}
