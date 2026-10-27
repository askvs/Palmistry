// Client detail: profile, evidence panels, session history, and notes.
import { useRouter } from "next/router";
import { useCallback, useState } from "react";
import { Button, ErrorState, Spinner, useToast } from "@/components/ui";
import Seo from "@/components/Seo";
import { useAsyncData } from "@/hooks/useAsyncData";
import { useAuth } from "@/hooks/useAuth";
import { useRoleGuard } from "@/hooks/useRoleGuard";
import { CompassIcon, UsersIcon } from "@/components/icons";
import {
  fetchClientAIInsights,
  fetchClientNotes,
  fetchClientPalmSummary,
  fetchClientTarotHistory,
  fetchConsultantClient,
  saveClientNotes,
} from "@/services/consultant";
import {
  ClientConsultationHistory,
  ClientOverviewCards,
  ClientOverviewHeader,
} from "@/components/consultant/ClientOverview";
import PalmAnalysisSummary from "@/components/consultant/PalmAnalysisSummary";
import GoalProgressPanel from "@/components/consultant/GoalProgressPanel";
import TarotHistoryTable from "@/components/consultant/TarotHistoryTable";
import AIConsultationInsights from "@/components/consultant/AIInsightCard";
import ConsultantNotes from "@/components/consultant/ConsultantNotes";
import StartConsultationDialog from "@/components/consultant/StartConsultationDialog";
import { SourceBadge } from "@/components/consultant/shared";

export default function ConsultantClientDetailPage() {
  const router = useRouter();
  const clientId = typeof router.query.clientId === "string" ? router.query.clientId : "";
  const blocked = useRoleGuard();
  const { user, loading: authLoading } = useAuth();
  const toast = useToast();

  const [dialogOpen, setDialogOpen] = useState(false);
  const [savingNotes, setSavingNotes] = useState(false);
  const [notesSaved, setNotesSaved] = useState(false);

  const loader = useCallback(
    () => fetchConsultantClient(clientId),
    [clientId]
  );
  const { data, error, loading, refresh } = useAsyncData(loader, {
    enabled: !authLoading && !!user && Boolean(clientId),
  });

  const palmLoader = useCallback(() => fetchClientPalmSummary(clientId), [clientId]);
  const { data: palmData, loading: palmLoading, error: palmError, refresh: refreshPalm } =
    useAsyncData(palmLoader, { enabled: Boolean(data?.client) });

  const tarotLoader = useCallback(() => fetchClientTarotHistory(clientId), [clientId]);
  const { data: tarotData, loading: tarotLoading } = useAsyncData(tarotLoader, {
    enabled: Boolean(data?.client),
  });

  const insightLoader = useCallback(() => fetchClientAIInsights(clientId), [clientId]);
  const { data: insightData, loading: insightLoading } = useAsyncData(insightLoader, {
    enabled: Boolean(data?.client),
  });

  const notesLoader = useCallback(() => fetchClientNotes(clientId), [clientId]);
  const { data: notesData } = useAsyncData(notesLoader, {
    enabled: Boolean(data?.client),
  });

  if (authLoading || (loading && !data)) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <Spinner label="Opening client profile…" />
      </div>
    );
  }

  if (blocked) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <Spinner label="Returning to your dashboard…" />
      </div>
    );
  }

  if (error || !data?.client) {
    return (
      <div className="space-y-4">
        <ErrorState
          title="Client not available"
          message={
            error?.message ||
            "This client is not part of your workspace, or their profile is no longer shared."
          }
        />
        <div className="flex justify-center">
          <Button href="/consultant/clients" variant="secondary">
            Back to Clients
          </Button>
        </div>
      </div>
    );
  }

  const client = data.client;

  async function handleSaveNotes(value, { asConsultation = false } = {}) {
    setSavingNotes(true);
    setNotesSaved(false);
    try {
      await saveClientNotes(clientId, value);
      setNotesSaved(true);
      toast.success(
        asConsultation ? "Notes saved to consultation" : "Draft saved",
        asConsultation
          ? "Your notes are attached to this client's consultation record."
          : "Your draft is saved on this device."
      );
    } catch {
      toast.error("Could not save notes", "Please try again.");
    } finally {
      setSavingNotes(false);
    }
  }

  return (
    <div className="animate-fade-in space-y-8">
      <Seo
        title={`${client.name} | Client Profile`}
        description={`Consultant workspace profile for ${client.name}: readings, goals, palm and tarot context.`}
      />

      <ClientOverviewHeader
        client={client}
        onStartConsultation={() => setDialogOpen(true)}
      />

      {client.profilePending && (
        <div className="surface-card border-accent-200 bg-accent-50/70 p-5">
          <h2 className="text-sm font-semibold text-accent-900">Profile pending</h2>
          <p className="mt-1 max-w-2xl text-sm leading-relaxed text-accent-800">
            This seeker has reached out to you, but the platform does not yet expose their profile
            or readings to consultants. You can conduct the session and record your own notes —
            the palm, tarot, personality and insight panels below stay empty rather than showing
            invented data.
          </p>
          <div className="mt-3">
            <SourceBadge source="live" />
          </div>
        </div>
      )}

      <ClientOverviewCards client={client} />

      <GoalProgressPanel client={client} />

      <div className="grid gap-5 xl:grid-cols-2">
        <PalmAnalysisSummary
          palm={client.palm}
          source={palmData?.source}
          loading={palmLoading}
          error={palmError}
          onRetry={refreshPalm}
        />
        <TarotHistoryTable
          rows={tarotData?.rows || []}
          source={tarotData?.source}
          loading={tarotLoading}
        />
      </div>

      <AIConsultationInsights
        insights={insightData?.insights || []}
        source={insightData?.source}
        loading={insightLoading}
      />

      <ClientConsultationHistory consultations={client.consultations || []} source={client.source} />

      <div className="space-y-4">
        <ConsultantNotes
          key={`${clientId}-${notesData ? "loaded" : "loading"}`}
          value={notesData?.notes ?? ""}
          saving={savingNotes}
          saved={notesSaved}
          onSaveDraft={(value) => handleSaveNotes(value, { asConsultation: false })}
          onSaveConsultation={(value) => handleSaveNotes(value, { asConsultation: true })}
          contextLabel={client.name}
        />
      </div>

      <div className="surface-card flex flex-wrap items-center justify-between gap-3 p-5">
        <div className="flex items-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-primary-50 text-primary-600 ring-1 ring-primary-100">
            <CompassIcon className="h-5 w-5" />
          </span>
          <div>
            <p className="text-sm font-semibold text-slate-900">Ready to work with {client.name}?</p>
            <p className="text-xs text-slate-500">
              Start a consultation to generate insights, add guidance and produce a report.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button href="/consultant/clients" variant="ghost" icon={UsersIcon}>
            All clients
          </Button>
          <Button onClick={() => setDialogOpen(true)}>Start Consultation</Button>
        </div>
      </div>

      {dialogOpen && (
        <StartConsultationDialog
          key={client.id}
          open
          clients={[client]}
          preselectedClientId={client.id}
          onClose={() => setDialogOpen(false)}
          onCreated={(session) => {
            setDialogOpen(false);
            if (session?.id) router.push(`/consultant/consultations/${session.id}`);
          }}
        />
      )}
    </div>
  );
}
