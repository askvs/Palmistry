// Consultation workspace: client info, tabbed workspace, and summary.
import { useRouter } from "next/router";
import { useCallback, useState } from "react";
import { Button, Spinner, useToast } from "@/components/ui";
import Seo from "@/components/Seo";
import { useAsyncData } from "@/hooks/useAsyncData";
import { useAuth } from "@/hooks/useAuth";
import { useRoleGuard } from "@/hooks/useRoleGuard";
import { FileTextIcon } from "@/components/icons";
import {
  downloadConsultationReport,
  fetchConsultationReports,
  fetchConsultationWorkspace,
  saveConsultationNotes,
  sendConsultantGuidance,
} from "@/services/consultant";
import ConsultationWorkspace from "@/components/consultant/ConsultationWorkspace";
import { Panel, SectionError, SourceBadge } from "@/components/consultant/shared";

export default function ConsultantConsultationDetailPage() {
  const router = useRouter();
  const consultationId =
    typeof router.query.consultationId === "string" ? router.query.consultationId : "";
  const blocked = useRoleGuard();
  const { user, loading: authLoading } = useAuth();
  const toast = useToast();

  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [generatingReport, setGeneratingReport] = useState(false);

  const loader = useCallback(
    () => fetchConsultationWorkspace(consultationId),
    [consultationId]
  );
  const { data, error, loading, refresh } = useAsyncData(loader, {
    enabled: !authLoading && !!user && Boolean(consultationId),
  });

  const reportLoader = useCallback(() => fetchConsultationReports({}), []);
  const { data: reportData } = useAsyncData(reportLoader, { enabled: !authLoading && !!user });

  async function persist(sessionId, payload) {
    return saveConsultationNotes(sessionId, payload);
  }

  async function handleSaveNotes(notes) {
    if (!data?.session) return;
    setSaving(true);
    setSaved(false);
    try {
      await persist(data.session.id, { notes });
      setSaved(true);
      toast.success("Draft saved", "Your notes are stored for this consultation.");
    } catch {
      toast.error("Could not save notes", "Please try again.");
    } finally {
      setSaving(false);
    }
  }

  async function handleSaveConsultation(notes, extra = {}) {
    if (!data?.session) return;
    setSaving(true);
    setSaved(false);
    try {
      await persist(data.session.id, {
        notes,
        guidance: extra.guidance,
        followUpDate: extra.followUpDate,
        status: "completed",
      });
      setSaved(true);
      toast.success("Consultation saved", "Notes, guidance and follow-up are recorded.");
    } catch {
      toast.error("Could not save the consultation", "Please try again.");
    } finally {
      setSaving(false);
    }
  }

  async function handleGenerateReport() {
    if (!data?.client) {
      toast.error(
        "No client attached",
        "Reports are generated from a client's consultation records."
      );
      return;
    }
    setGeneratingReport(true);
    try {
      const reports = reportData?.reports || [];
      const match = reports.find((report) => report.clientId === data.client.id) || reports[0];
      if (match) {
        await downloadConsultationReport(match.id);
        toast.success("Report downloaded", `${match.title || "Report"} has been saved as a PDF.`);
      } else {
        router.push("/consultant/reports");
        toast.info("No report yet", "Generate one from the reports page for this client.");
      }
    } catch (err) {
      toast.error("Could not generate the report", err?.message || "Please try again.");
    } finally {
      setGeneratingReport(false);
    }
  }

  if (authLoading || (loading && !data)) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <Spinner label="Opening consultation workspace…" />
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

  return (
    <div className="animate-fade-in space-y-6">
      <Seo
        title="Consultation"
        description="The client's readings, guidance and notes — everything for this session in one workspace."
      />

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="font-display text-3xl font-semibold tracking-[-0.02em] text-slate-900">
            Consultation Workspace
          </h1>
          <p className="mt-1.5 max-w-2xl text-sm leading-relaxed text-slate-600">
            Review the client&rsquo;s readings, generate insights, write your guidance and produce a
            report — without leaving the session.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <SourceBadge source={data?.source} />
          <Button
            variant="secondary"
            icon={FileTextIcon}
            loading={generatingReport}
            onClick={handleGenerateReport}
          >
            Generate report
          </Button>
        </div>
      </div>

      <ConsultationWorkspace
        session={data?.session}
        client={data?.client}
        source={data?.source}
        loading={loading}
        error={error?.message || (data && !data.session ? "This consultation could not be found." : null)}
        onRetry={refresh}
        onSaveNotes={handleSaveNotes}
        onSaveConsultation={handleSaveConsultation}
        onGenerateReport={handleGenerateReport}
        onSendGuidance={async (liveId, payload) => {
          try {
            await sendConsultantGuidance(liveId, payload);
            toast.success("Guidance sent", "Your counsel has been dispatched to the seeker.");
            refresh();
          } catch (err) {
            toast.error("Could not send guidance", err?.message || "Please try again.");
          }
        }}
        saving={saving}
        saved={saved}
      />

      {data?.client && (
        <Panel title="Workspace checklist" subtitle="Where you are in this session">
          <ol className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
            {[
              "Client selected",
              "Purpose set",
              "Readings reviewed",
              "Insights reviewed",
              "Guidance + notes saved",
            ].map((step, index) => (
              <li
                key={step}
                className="rounded-card border border-slate-100 bg-slate-50/70 p-3.5 text-sm leading-relaxed text-slate-600"
              >
                <span className="mb-0.5 block text-xs font-bold uppercase tracking-wide text-primary-700">
                  Step {index + 1}
                </span>
                {step}
              </li>
            ))}
          </ol>
        </Panel>
      )}

      {!data?.session && !loading && (
        <SectionError
          title="Consultation not found"
          onRetry={() => router.push("/consultant/consultations")}
        />
      )}
    </div>
  );
}
