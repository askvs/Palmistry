import { apiFetch } from "@/services/api";

// Upload palm image for feature extraction and line detection.
export async function analyzePalm(file, hand = null) {
  const formData = new FormData();
  formData.append("file", file);
  if (hand) {
    formData.append("hand", hand);
  }
  return apiFetch("/api/v1/palm/analyze", {
    method: "POST",
    body: formData,
  });
}

// Reference catalog of primary palm lines.
export async function getPalmLinesCatalog() {
  return apiFetch("/api/v1/palm/lines");
}

// Reference catalog of traditional palm mounts.
export async function getPalmMountsCatalog() {
  return apiFetch("/api/v1/palm/mounts");
}

// Fast live-frame check for hand presence.
export async function checkHandFrame(frameBlob) {
  const formData = new FormData();
  formData.append("file", frameBlob, "frame.jpg");
  return apiFetch("/api/v1/palm/check-frame", {
    method: "POST",
    body: formData,
  });
}

