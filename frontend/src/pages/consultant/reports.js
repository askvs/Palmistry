// Consultation reports: filter, view, download, or share.
import Head from "next/head";
import { useRouter } from "next/router";
import { useCallback, useState } from "react";
import { FileTextIcon } from "@/components/icons";
import { useAsyncData } from "@/hooks/useAsyncData";
import { useAuth } from "@/hooks/useAuth";
import { PageHeader, useToast } from "@/components/ui";
import {
  fetchConsultantClients,
  fetchConsultationReports,
  downloadConsultationReport,
} from "@/services/consultant";
import ConsultationReportsTable from "@/components/consultant/ConsultationReportsTable";

export default function ConsultantReportsPage() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
  const toast = useToast();

  const initialClient = typeof router.query.client === "string" ? router.query.client : "";
  const [clientId, setClientId] = useState(initialClient);
  const [status, setStatus] = useState("all");
  const [downloadingId, setDownloadingId] = useState(null);

  const loader = useCallback(
    () => fetchConsultationReports({ clientId, status }),
    [clientId, status]
  );
  const { data, error, loading, refresh } = useAsyncData(loader, {
    enabled: !authLoading && !!user,
  });

  const clientsLoader = useCallback(() => fetchConsultantClients({}), []);
  const { data: clientsData } = useAsyncData(clientsLoader, {
    enabled: !authLoading && !!user,
  });

  const clientOptions = (clientsData?.clients || [])
    .filter((client) => !client.profilePending)
    .map((client) => ({ value: client.id, label: client.name }));

  async function handleDownload(report) {
    setDownloadingId(report.id);
    try {
      await downloadConsultationReport(report.id);
      toast.success("Report downloaded", `${report.title || "Report"} has been saved as a PDF.`);
    } catch (err) {
      toast.error("Could not download the report", err?.message || "Please try again.");
    } finally {
      setDownloadingId(null);
    }
  }

  async function handleShare(report) {
    const text = `${report.title || "Consultation report"} — ${report.clientName || "client"}`;
    try {
      if (navigator.share) {
        await navigator.share({ title: report.title || "Consultation report", text });
        return;
      }
      await navigator.clipboard.writeText(text);
      toast.success("Link copied", "The report reference has been copied to your clipboard.");
    } catch {
      /* user cancelled the share sheet, or the clipboard is unavailable */
    }
  }

  return (
    <div className="animate-fade-in space-y-8">
      <Head>
        <title>Consultation Reports | Palmistry &amp; Tarot</title>
      </Head>

      <PageHeader
        icon={FileTextIcon}
        tileTone="emerald"
        eyebrow="Spiritual Consultant"
        title="Consultation Reports"
        description="Reports generated from your consultation sessions. Export as PDF, or open the client to review the underlying readings."
      />

      <ConsultationReportsTable
        reports={data?.reports || []}
        source={data?.source}
        total={data?.total || 0}
        loading={loading}
        error={error?.message || null}
        onRetry={refresh}
        status={status}
        onStatusChange={setStatus}
        clientId={clientId}
        onClientChange={setClientId}
        clientOptions={clientOptions}
        onDownload={handleDownload}
        downloadingId={downloadingId}
        onShare={handleShare}
      />
    </div>
  );
}
