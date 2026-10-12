import { api, apiBlob, parseContentDisposition } from "./api";

export async function getReadingReport(readingId) {
  return api.get(`/api/v1/reports/reading/${readingId}`);
}

function ensureExtension(name, ext) {
  if (!name) return `reading-report${ext}`;
  return name.toLowerCase().endsWith(ext) ? name : `${name}${ext}`;
}

function triggerBlobDownload(blob, filename) {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  // Revoke on the next tick for slow browsers.
  setTimeout(() => window.URL.revokeObjectURL(url), 1000);
}

async function downloadReportFile(path, defaultFilename, ext) {
  const result = await apiBlob(path);
  // Tolerate a raw Blob for tests and mocks.
  const blob = result?.blob instanceof Blob ? result.blob : result;
  const serverFilename =
    result?.filename || (typeof result?.headers === "function" ? parseContentDisposition(result.headers.get?.("content-disposition")) : null);
  const filename = ensureExtension(serverFilename || defaultFilename, ext);
  if (!(blob instanceof Blob) || blob.size === 0) {
    throw new Error("The report came back empty. Please try again.");
  }
  triggerBlobDownload(blob, filename);
  return { filename, size: blob.size };
}

export async function downloadReportPdf(readingId, defaultFilename = "reading-report.pdf") {
  return downloadReportFile(`/api/v1/reports/reading/${readingId}/pdf`, defaultFilename, ".pdf");
}

export async function downloadReportExcel(readingId, defaultFilename = "reading-report.xlsx") {
  return downloadReportFile(
    `/api/v1/reports/reading/${readingId}/excel`,
    defaultFilename,
    ".xlsx"
  );
}
