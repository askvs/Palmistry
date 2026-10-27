// Palm reading: upload, CV analysis, and line results.

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import {
  ArrowLeftIcon,
  CameraIcon,
  CheckIcon,
  HandIcon,
  RetryIcon,
  ScanIcon,
  SparkleIcon,
  SparklesIcon,
} from "@/components/icons";
import Seo from "@/components/Seo";
import CameraCaptureModal from "@/components/palm/CameraCaptureModal";
import PalmVisualizer from "@/components/palm/PalmVisualizer";
import {
  PalmFingerStructure,
  PalmLinesList,
  PalmMountProfiles,
} from "@/components/palm/PalmAnalysisDetails";
import { useAuth } from "@/hooks/useAuth";
import { analyzePalm } from "@/services/palm";
import { downloadReportPdf, downloadReportExcel } from "@/services/reports";
import RecommendationsSection from "@/components/recommendations/RecommendationsSection";
import { generateRecommendations } from "@/services/recommendations";
import { interpretPalmDirect } from "@/services/readings";
import LoadingSpinner from "@/components/ai/LoadingSpinner";
import ChatBot from "@/components/ai/ChatBot";
import { Button, Spinner } from "@/components/ui";
import { useRoleGuard } from "@/hooks/useRoleGuard";

const MAX_SIZE_MB = 10;

const ELEMENT_THEMES = {
  Earth: {
    badge: "bg-emerald-50 text-emerald-700 ring-emerald-200",
    gradient: "from-emerald-50/80 via-teal-50/30 to-white",
    border: "border-emerald-200/80",
    accent: "text-emerald-700",
  },
  Air: {
    badge: "bg-sky-50 text-sky-700 ring-sky-200",
    gradient: "from-sky-50/80 via-indigo-50/30 to-white",
    border: "border-sky-200/80",
    accent: "text-sky-700",
  },
  Fire: {
    badge: "bg-amber-50 text-amber-700 ring-amber-200",
    gradient: "from-amber-50/80 via-rose-50/30 to-white",
    border: "border-amber-200/80",
    accent: "text-amber-700",
  },
  Water: {
    badge: "bg-cyan-50 text-cyan-700 ring-cyan-200",
    gradient: "from-cyan-50/80 via-blue-50/30 to-white",
    border: "border-cyan-200/80",
    accent: "text-cyan-700",
  },
};

export default function PalmReadingPage() {
  const blocked = useRoleGuard();
  const { user } = useAuth();
  const inputRef = useRef(null);

  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [isCameraOpen, setIsCameraOpen] = useState(false);
  const [activeLineId, setActiveLineId] = useState(null);

  // States: 'empty' | 'preview' | 'loading' | 'success' | 'error'
  const [stage, setStage] = useState("empty");
  const [loadingStep, setLoadingStep] = useState(0);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [downloadingReport, setDownloadingReport] = useState(null);
  // AI interpretation states (non-blocking)
  const [aiLoading, setAiLoading] = useState(false);
  const [aiError, setAiError] = useState(null);
  // Chat state
  const [chatMessages, setChatMessages] = useState([]);

  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  if (blocked) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <Spinner label="Returning to your dashboard…" />
      </div>
    );
  }

  function pickFile(selected) {
    setError(null);
    if (!selected) return;

    if (selected.size > MAX_SIZE_MB * 1024 * 1024) {
      setError(`Image must be ${MAX_SIZE_MB} MB or smaller.`);
      setStage("error");
      return;
    }

    if (previewUrl) URL.revokeObjectURL(previewUrl);
    const url = URL.createObjectURL(selected);
    setFile(selected);
    setPreviewUrl(url);
    setStage("preview");
  }

  function resetForm() {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setFile(null);
    setPreviewUrl(null);
    setResult(null);
    setError(null);
    setActiveLineId(null);
    setStage("empty");
  }

  // Keyboard access for the dropzone (spec §5.2): Enter/Space open the file
  // picker, Escape clears the current selection. Only fires for the zone
  // itself, so nested buttons keep their own key handling.
  function onZoneKeyDown(event) {
    if (event.target !== event.currentTarget) return;
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      inputRef.current?.click(); // keep the existing <input type="file"> in the DOM
    }
    if (event.key === "Escape") resetForm();
  }

  async function handleAnalyze(e) {
    if (e) e.preventDefault();
    if (!file) return;

    setStage("loading");
    setError(null);
    setLoadingStep(0);

    const stepTimer1 = setTimeout(() => setLoadingStep(1), 600);
    const stepTimer2 = setTimeout(() => setLoadingStep(2), 1200);
    const stepTimer3 = setTimeout(() => setLoadingStep(3), 1800);

    try {
      const data = await analyzePalm(file);
      setResult(data);
      setStage("success");
    } catch (err) {
      setError(err.message || "Failed to analyze palm image. Please try again.");
      setStage("error");
    } finally {
      clearTimeout(stepTimer1);
      clearTimeout(stepTimer2);
      clearTimeout(stepTimer3);
    }
  }

  // Opt-in AI interpretation: only runs when the user clicks
  // "Generate AI Insight" (also the retry path when a previous attempt failed).
  async function handleGenerateAi() {
    if (!result || aiLoading) return;
    setAiLoading(true);
    setAiError(null);
    try {
      const aiResult = await interpretPalmDirect(result);
      if (aiResult) {
        setResult((prev) => ({ ...prev, ai_interpretation: aiResult }));
      }
    } catch (aiErr) {
      setAiError(aiErr.message || "AI interpretation failed. Please try again.");
    } finally {
      setAiLoading(false);
    }
  }

  const activeTheme = result
    ? ELEMENT_THEMES[result.palm_shape?.element] || ELEMENT_THEMES.Air
    : ELEMENT_THEMES.Air;

  const isCloseUpError = error && error.toLowerCase().includes("close-up");

  return (
    <div className="mx-auto max-w-5xl space-y-8">
      <Seo
        title="Palm reading"
        description="Upload a palm photo and get a guided line-by-line reading in under a minute."
      />
      {/* Top Breadcrumb & Reset Action */}
      <div className="flex items-center justify-between">
        <Link
          href="/dashboard"
          className="inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-sm font-medium text-slate-500 transition hover:bg-slate-100 hover:text-slate-800"
        >
          <ArrowLeftIcon className="h-4 w-4" />
          Back to dashboard
        </Link>
        {stage === "success" && (
          <button
            type="button"
            onClick={resetForm}
            className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-3.5 py-1.5 text-xs font-medium text-slate-700 shadow-xs transition hover:border-slate-300 hover:bg-slate-50"
          >
            <RetryIcon className="h-3.5 w-3.5 text-slate-500" />
            Analyze Another Palm
          </button>
        )}
      </div>

      {/* Header Banner matching MysticLens UI */}
      <div className="text-center">
        <span className="mx-auto flex h-14 w-14 items-center justify-center rounded-[14px] bg-primary-50 text-primary-600 ring-1 ring-primary-100">
          <HandIcon className="h-7 w-7" />
        </span>
        <h1 className="mt-4 font-display text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
          Computer Vision Palm Analysis
        </h1>
        <p className="mx-auto mt-2 max-w-xl text-sm leading-relaxed text-slate-500">
          MediaPipe 21-point topology, OpenCV ridge enhancement, and geometric line detection
          revealing your Life, Head, Heart, Fate, and Sun lines.
        </p>
      </div>

      {/* Upload stages: empty, preview, and error. */}
      {(stage === "empty" || stage === "preview" || stage === "error") && (
        <section className="surface-panel p-6 sm:p-8">
          {/* Upload Dropzone */}
          <div
            role="button"
            tabIndex={0}
            aria-label="Upload a palm photo — press Enter to browse files, Escape to clear"
            onClick={() => inputRef.current?.click()}
            onKeyDown={onZoneKeyDown}
            onDragOver={(e) => {
              e.preventDefault();
              setDragging(true);
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDragging(false);
              pickFile(e.dataTransfer.files?.[0]);
            }}
            className={`group relative flex cursor-pointer flex-col items-center justify-center rounded-[16px] border border-dashed p-8 text-center transition focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600 ${
              dragging
                ? "border-solid border-[#a78bfa] bg-[#f5f3ff]"
                : "border-slate-300 bg-[#f8f7fd] hover:border-primary-300"
            }`}
          >
            {previewUrl ? (
              <div className="flex w-full max-w-md items-center gap-3 rounded-[16px] border border-slate-200/90 bg-white p-3 text-left shadow-xs">
                <div className="h-11 w-11 shrink-0 overflow-hidden rounded-[10px] border border-slate-200 bg-slate-50">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={previewUrl}
                    alt="Palm preview"
                    className="h-full w-full object-cover"
                  />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-semibold text-slate-900">{file?.name}</p>
                  <p className="text-[12.5px] text-slate-500">
                    {(file.size / (1024 * 1024)).toFixed(2)} MB
                  </p>
                </div>
                <div className="flex shrink-0 items-center gap-1.5">
                  <button
                    type="button"
                    onClick={(event) => {
                      event.stopPropagation();
                      inputRef.current?.click();
                    }}
                    className="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 shadow-xs transition hover:border-slate-300 hover:bg-slate-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600"
                  >
                    Replace
                  </button>
                  <button
                    type="button"
                    onClick={(event) => {
                      event.stopPropagation();
                      resetForm();
                    }}
                    className="rounded-full px-3 py-1.5 text-xs font-medium text-slate-500 transition hover:bg-slate-100 hover:text-slate-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600"
                  >
                    Remove
                  </button>
                </div>
              </div>
            ) : (
              <>
                <span className="flex h-11 w-11 items-center justify-center rounded-[10px] bg-primary-50 text-primary-600 ring-1 ring-primary-100 transition group-hover:scale-105">
                  <ScanIcon className="h-5 w-5" />
                </span>
                <p className="mt-4 text-sm font-semibold text-slate-900">
                  {dragging ? "Release to upload" : "Drop your palm photo here"}
                </p>
                <p className="mt-1 text-[12.5px] text-slate-500">
                  or{" "}
                  <span className="font-medium text-primary-700 underline decoration-primary-200 underline-offset-2">
                    browse files
                  </span>{" "}
                  · JPG/PNG · ≤10 MB
                </p>

                {/* Instant Camera Capture CTA */}
                <div className="mt-4">
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      setIsCameraOpen(true);
                    }}
                    className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-4 py-1.5 text-xs font-semibold text-primary-700 shadow-xs transition hover:border-primary-300 hover:bg-primary-50"
                  >
                    <CameraIcon className="h-4 w-4 text-primary-600" />
                    Use Camera to Take Photo
                  </button>
                </div>

                {/* Clear Hand Framing Guide Grid */}
                <div className="mt-6 grid w-full max-w-xl grid-cols-1 gap-2 text-left sm:grid-cols-2">
                  <div className="surface-card flex items-start gap-2.5 p-3">
                    <CheckIcon className="h-4 w-4 text-emerald-600 shrink-0 mt-0.5" />
                    <div>
                      <span className="text-sm font-semibold text-slate-800">Show Full Hand & Wrist</span>
                      <p className="mt-0.5 text-[12.5px] leading-relaxed text-slate-500">
                        Capture the entire hand from wrist to fingertips. Do not crop into just the creases.
                      </p>
                    </div>
                  </div>
                  <div className="surface-card flex items-start gap-2.5 p-3">
                    <CheckIcon className="h-4 w-4 text-emerald-600 shrink-0 mt-0.5" />
                    <div>
                      <span className="text-sm font-semibold text-slate-800">Flat Open Palm</span>
                      <p className="mt-0.5 text-[12.5px] leading-relaxed text-slate-500">
                        Keep fingers naturally spread and palm facing directly toward the camera.
                      </p>
                    </div>
                  </div>
                  <div className="surface-card flex items-start gap-2.5 p-3">
                    <CheckIcon className="h-4 w-4 text-emerald-600 shrink-0 mt-0.5" />
                    <div>
                      <span className="text-sm font-semibold text-slate-800">Auto Left / Right Detection</span>
                      <p className="mt-0.5 text-[12.5px] leading-relaxed text-slate-500">
                        AI automatically verifies orientation and detects handedness topology.
                      </p>
                    </div>
                  </div>
                  <div className="surface-card flex items-start gap-2.5 p-3">
                    <CheckIcon className="h-4 w-4 text-emerald-600 shrink-0 mt-0.5" />
                    <div>
                      <span className="text-sm font-semibold text-slate-800">Adequate Lighting</span>
                      <p className="mt-0.5 text-[12.5px] leading-relaxed text-slate-500">
                        Ensure good contrast so the subtle skin folds and mounts are clearly visible.
                      </p>
                    </div>
                  </div>
                </div>
              </>
            )}
            <input
              ref={inputRef}
              type="file"
              accept="image/jpeg,image/png,image/webp"
              className="hidden"
              onChange={(e) => pickFile(e.target.files?.[0])}
            />
          </div>

          {/* Action Buttons */}
          <div className="mt-6 flex items-center justify-end gap-3">
            {stage === "preview" && (
              <button
                type="button"
                onClick={resetForm}
                className="rounded-full border border-slate-200 bg-white px-5 py-2 text-sm font-medium text-slate-700 shadow-xs transition hover:border-slate-300 hover:bg-slate-50"
              >
                Clear
              </button>
            )}
            <button
              type="button"
              onClick={handleAnalyze}
              disabled={!file}
              className="inline-flex items-center gap-2 rounded-full bg-primary-600 px-6 py-2.5 text-sm font-medium text-white shadow-sm shadow-primary-600/25 transition hover:bg-primary-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600 disabled:cursor-not-allowed disabled:opacity-60"
            >
              <ScanIcon className="h-4 w-4" />
              Analyze Palm Features
            </button>
          </div>

          {/* Error Banner with Smart Guidance */}
          {error && (
            <div
              role="alert"
              className="mt-6 rounded-2xl border border-rose-200 bg-rose-50 p-5 text-sm text-rose-800 shadow-xs"
            >
              <div className="flex items-start gap-3">
                <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-rose-200 text-xs font-bold text-rose-800">
                  !
                </span>
                <div className="space-y-2">
                  <p className="font-semibold text-rose-900">
                    {isCloseUpError ? "Hand Framing Adjustment Required" : "Analysis Halted"}
                  </p>
                  <p className="text-sm leading-relaxed text-rose-700">{error}</p>

                  {isCloseUpError && (
                    <div className="rounded-[16px] border border-rose-200/80 bg-white/90 p-3 shadow-xs">
                      <p className="text-sm font-semibold text-violet-800">Why did this happen?</p>
                      <p className="mt-1 text-sm leading-relaxed text-slate-600">
                        MysticLens uses anatomical landmarks across the wrist and knuckles to locate lines and calculate elemental ratios. When an image is cropped down to only the center creases, the computer vision model cannot identify the hand anchor points.
                      </p>
                      <p className="mt-1.5 flex items-start gap-1.5 text-sm font-medium text-emerald-700">
                        <CheckIcon className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" />
                        <span>Solution: Step back so the bottom of your palm/wrist and all 5 fingertips are in frame.</span>
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </section>
      )}

      {/* Loading stage with animated progress. */}
      {stage === "loading" && (
        <section className="surface-panel relative overflow-hidden p-10 text-center">
          {/* Scan-sweep recipe (Appendix A.8) — local until globals.css ships it */}
          <style>{`
            @keyframes scan-sweep {
              0% { transform: translateY(6%); opacity: 0; }
              12% { opacity: 1; }
              88% { opacity: 1; }
              100% { transform: translateY(94%); opacity: 0; }
            }
            .animate-scan-sweep { animation: scan-sweep 2.4s var(--ease-standard) infinite; }
          `}</style>

          {/* Drifting ✦ stardust (≤4% opacity) */}
          <div aria-hidden="true" className="pointer-events-none absolute inset-0 text-primary-600/[0.04]">
            <span className="absolute left-[10%] top-[20%] text-3xl">✦</span>
            <span className="absolute right-[14%] top-[16%] text-xl">✦</span>
            <span className="absolute left-[20%] bottom-[18%] text-2xl">✦</span>
            <span className="absolute right-[22%] bottom-[26%] text-sm">✦</span>
            <span className="absolute left-[46%] top-[10%] text-base">✦</span>
          </div>

          {/* Palm silhouette tile with violet scan line */}
          <div className="relative mx-auto h-28 w-24 overflow-hidden rounded-[16px] border border-slate-200 bg-primary-50/60 ring-1 ring-primary-100/70">
            <svg
              viewBox="0 0 200 240"
              className="h-full w-full text-primary-500/70"
              fill="none"
              stroke="currentColor"
              strokeWidth="3"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <path
                className="fill-primary-500/10"
                d="M 70 230 C 70 190, 60 170, 50 150 C 40 135, 30 115, 38 105 C 45 95, 58 105, 65 125 C 62 100, 62 70, 72 65 C 80 62, 85 75, 85 105 C 86 80, 92 40, 103 40 C 112 40, 115 70, 115 105 C 117 85, 126 55, 136 58 C 144 60, 142 85, 140 115 C 145 100, 158 90, 166 98 C 172 108, 160 145, 150 170 C 140 195, 130 210, 130 230 Z"
              />
            </svg>
            <div aria-hidden="true" className="pointer-events-none absolute inset-0 animate-scan-sweep">
              <div className="mx-auto h-[2.5px] w-[86%] rounded-full bg-gradient-to-r from-transparent via-primary-500 to-transparent shadow-[0_0_12px_rgba(139,92,246,0.8)]" />
            </div>
          </div>
          <h2 className="mt-6 font-display text-2xl font-bold text-slate-900">
            Analyzing Palm Topology & Creases…
          </h2>
          <p className="mt-1 text-sm text-slate-500">
            Running computer vision models and geometric line feature extraction
          </p>

          {/* Step list */}
          <div className="mx-auto mt-8 max-w-md space-y-2.5 text-left text-sm">
            <div
              className={`flex items-center gap-2.5 rounded-[10px] border p-3 transition duration-[240ms] ${
                loadingStep >= 0
                  ? "border-primary-200 bg-primary-50/70 text-primary-900 font-medium"
                  : "border-slate-200 bg-slate-50 text-slate-500"
              }`}
            >
              <CheckIcon className={`h-4 w-4 ${loadingStep >= 0 ? "text-primary-600" : "text-slate-300"}`} />
              Phase 1: Validating file signature & EXIF orientation
            </div>
            <div
              className={`flex items-center gap-2.5 rounded-[10px] border p-3 transition duration-[240ms] ${
                loadingStep >= 1
                  ? "border-primary-200 bg-primary-50/70 text-primary-900 font-medium"
                  : "border-slate-200 bg-slate-50 text-slate-500"
              }`}
            >
              <CheckIcon className={`h-4 w-4 ${loadingStep >= 1 ? "text-primary-600" : "text-slate-300"}`} />
              Phase 2: Extracting 21 3D MediaPipe hand landmarks
            </div>
            <div
              className={`flex items-center gap-2.5 rounded-[10px] border p-3 transition duration-[240ms] ${
                loadingStep >= 2
                  ? "border-primary-200 bg-primary-50/70 text-primary-900 font-medium"
                  : "border-slate-200 bg-slate-50 text-slate-500"
              }`}
            >
              <CheckIcon className={`h-4 w-4 ${loadingStep >= 2 ? "text-primary-600" : "text-slate-300"}`} />
              Phase 3: Classifying elemental hand shape & finger ratios
            </div>
            <div
              className={`flex items-center gap-2.5 rounded-[10px] border p-3 transition duration-[240ms] ${
                loadingStep >= 3
                  ? "border-primary-200 bg-primary-50/70 text-primary-900 font-medium"
                  : "border-slate-200 bg-slate-50 text-slate-500"
              }`}
            >
              <CheckIcon className={`h-4 w-4 ${loadingStep >= 3 ? "text-primary-600" : "text-slate-300"}`} />
              Phase 4: Tracing Life, Head, Heart, Fate & Sun lines
            </div>
          </div>
        </section>
      )}

      {/* Success stage with visualizer and result cards. */}
      {stage === "success" && result && (
        <div className="space-y-8 animate-tab-in">
          {/* Main Visualizer + Archetype Split Layout */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
            {/* Left Column: Interactive Palm Visualizer (5 cols) */}
            <div className="lg:col-span-5 lg:sticky lg:top-8 space-y-3">
              <div className="flex items-center justify-between px-1">
                <h3 className="font-display text-sm font-bold uppercase tracking-wider text-slate-700">
                  Biometric Scan Overlay
                </h3>
                <span className="text-[12.5px] text-slate-500">
                  Hover lines or mounts
                </span>
              </div>
              <PalmVisualizer
                imageUrl={previewUrl}
                result={result}
                activeLineId={activeLineId}
                onHoverLine={setActiveLineId}
              />
            </div>

            {/* Right Column: Archetype Hero & Biometrics (7 cols) */}
            <div className="lg:col-span-7 space-y-6">
              {/* Elemental Palm Shape Hero Card */}
              <section
                className={`overflow-hidden rounded-[20px] border bg-gradient-to-br p-6 shadow-xs sm:p-7 ${activeTheme.border} ${activeTheme.gradient}`}
              >
                <div className="flex flex-wrap items-center justify-between gap-4">
                  <div>
                    <span
                      className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold ring-1 ring-inset ${activeTheme.badge}`}
                    >
                      <SparkleIcon className="h-3.5 w-3.5" />
                      {result.palm_shape?.element} Hand Archetype
                    </span>
                    <h2 className="mt-3 font-display text-2xl font-bold text-slate-900 sm:text-3xl">
                      {result.palm_shape?.element} Palm Classification
                    </h2>
                    <p className="mt-1 text-sm leading-relaxed text-slate-600">
                      {result.palm_shape?.description}
                    </p>
                  </div>

                  {/* Confidence Badge */}
                  <div className="surface-card p-4 text-center">
                    <div className="font-display text-2xl font-bold tabular-nums text-primary-600">
                      {Math.round((result.metadata?.overall_confidence || 0) * 100)}%
                    </div>
                    <div className="text-xs font-medium text-slate-500">Analysis Confidence</div>
                    <div className="mt-1.5 inline-block rounded-full bg-slate-50 px-2.5 py-0.5 text-sm font-semibold text-slate-600 ring-1 ring-slate-200">
                      {(result.metadata?.overall_confidence || 0) >= 0.75
                        ? "High Confidence Scan"
                        : (result.metadata?.overall_confidence || 0) >= 0.55
                          ? "Verified Scan"
                          : "Low Confidence — Retake Photo"}
                    </div>
                  </div>
                </div>

                {/* Traits Chips */}
                <div className="mt-5 flex flex-wrap gap-2">
                  {result.palm_shape?.traits?.map((trait, idx) => (
                    <span
                      key={idx}
                      className="rounded-[10px] border border-slate-200 bg-white/90 px-3 py-1 text-[12.5px] font-medium text-slate-700 shadow-xs"
                    >
                      #{trait}
                    </span>
                  ))}
                </div>

                {/* Palm & Finger Metrics */}
                <div className="mt-6 grid grid-cols-2 gap-3 border-t border-slate-200/80 pt-4 sm:grid-cols-4">
                  <div className="surface-card p-3">
                    <span className="text-sm font-semibold uppercase text-slate-500">Identified Hand</span>
                    <p className="font-semibold tabular-nums text-slate-900">
                      {result.hand?.detected_handedness} Hand
                    </p>
                    <span className="text-[12.5px] font-medium text-emerald-700">
                      Auto-detected ({Math.round((result.hand?.handedness_confidence || 0.95) * 100)}%)
                    </span>
                  </div>
                  <div className="surface-card p-3">
                    <span className="text-sm font-semibold uppercase text-slate-500">Aspect Ratio</span>
                    <p className="font-semibold tabular-nums text-slate-900">
                      {result.palm_shape?.aspect_ratio}
                    </p>
                  </div>
                  <div className="surface-card p-3">
                    <span className="text-sm font-semibold uppercase text-slate-500">2D:4D Ratio</span>
                    <p className="font-semibold tabular-nums text-slate-900">
                      {result.finger_structure?.digit_ratio_2d_4d}
                    </p>
                  </div>
                  <div className="surface-card p-3">
                    <span className="text-sm font-semibold uppercase text-slate-500">Thumb Angle</span>
                    <p className="font-semibold tabular-nums text-slate-900">
                      {result.finger_structure?.thumb_angle_degrees}°
                    </p>
                  </div>
                </div>
              </section>

              {/* Detected Palm Lines Section */}
              <section className="surface-panel p-6 sm:p-7">
                <div className="mb-4 flex items-center justify-between">
                  <div>
                    <h3 className="font-display text-xl font-bold text-slate-900">Detected Palm Creases</h3>
                    <p className="text-xs text-slate-500">
                      Hover over any line to highlight its corresponding curve on the photo
                    </p>
                  </div>
                  <span className="rounded-full border border-violet-200 bg-violet-50 px-3 py-1 text-xs font-semibold text-violet-700">
                    {result.lines?.filter((l) => l.detected).length ?? 0} of {result.lines?.length ?? 5} Detected
                  </span>
                </div>

                {result.hand?.is_palmar === false && (
                  <div className="mb-4 rounded-[10px] border border-amber-200 bg-amber-50 px-4 py-3 text-sm leading-relaxed text-amber-800">
                    Back-of-hand (dorsal) view detected — line creases are naturally less visible
                    from this angle, so lower line confidences are expected. A flat palmar photo
                    gives the sharpest scan.
                  </div>
                )}

                <PalmLinesList
                  lines={result.lines}
                  activeLineId={activeLineId}
                  onHoverLine={setActiveLineId}
                />
              </section>
            </div>
          </div>

          {/* MEASURED BIOMETRICS CHART (always visible — computer vision, not AI) */}
          <section className="surface-panel p-6 sm:p-7">
            <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h3 className="font-display text-xl font-bold text-slate-900">Measured Biometrics</h3>
                <p className="text-xs text-slate-500">
                  Measured from your photo (computer vision) — no AI involved
                </p>
              </div>
              <span className="rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700">
                Actual Scan Data
              </span>
            </div>

            <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
              <div>
                <div className="mb-3 text-sm font-semibold uppercase tracking-wider text-slate-500">
                  Line detection confidence
                </div>
                <div className="space-y-3">
                  {(result.lines || []).map((line) => {
                    const pct = Math.round((line.confidence || 0) * 100);
                    return (
                      <div key={line.line_id} className="flex items-center gap-3">
                        <span className="w-20 shrink-0 text-sm font-semibold text-slate-700">
                          {line.name?.replace(" Line", "")}
                        </span>
                        <div className="h-3 flex-1 overflow-hidden rounded-full bg-slate-100">
                          <div
                            className="h-full rounded-full bg-gradient-to-r from-primary-400 to-primary-600 transition-all duration-700"
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                        <span className="w-10 text-sm font-medium tabular-nums text-slate-600">{pct}%</span>
                      </div>
                    );
                  })}
                </div>
              </div>

              <div>
                <div className="mb-3 text-sm font-semibold uppercase tracking-wider text-slate-500">
                  Mount prominence score
                </div>
                <div className="space-y-3">
                  {(result.mounts || []).map((mount) => {
                    const pct = Math.round((mount.score || 0) * 100);
                    return (
                      <div key={mount.mount_id} className="flex items-center gap-3">
                        <span className="w-20 shrink-0 truncate text-sm font-semibold text-slate-700">
                          {mount.name?.replace("Mount of ", "")}
                        </span>
                        <div className="h-3 flex-1 overflow-hidden rounded-full bg-slate-100">
                          <div
                            className="h-full rounded-full bg-gradient-to-r from-primary-400 to-primary-600 transition-all duration-700"
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                        <span className="w-10 text-sm font-medium tabular-nums text-slate-600">{pct}%</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </section>

          {/* FINGER STRUCTURE & MOUNT PROFILES DEEP DIVE (measured CV data) */}
          <section className="surface-panel p-6 sm:p-7">
            <div className="mb-5">
              <h3 className="font-display text-xl font-bold text-slate-900">
                Biometric Deep Dive
              </h3>
              <p className="text-xs text-slate-500">
                What each measured proportion and mount prominence traditionally signals
              </p>
            </div>

            {result.finger_structure && (
              <div className="mb-8">
                <div className="mb-3 text-sm font-semibold uppercase tracking-wider text-slate-500">
                  Finger structure &amp; dexterity signals
                </div>
                <PalmFingerStructure fingerStructure={result.finger_structure} />
              </div>
            )}

            {Array.isArray(result.mounts) && result.mounts.length > 0 && (
              <div>
                <div className="mb-3 text-sm font-semibold uppercase tracking-wider text-slate-500">
                  Planetary mount profiles
                </div>
                <PalmMountProfiles mounts={result.mounts} />
              </div>
            )}
          </section>

          {/* AI INTERPRETATION SECTION (Non-blocking) */}
          <div className="space-y-6 surface-panel p-6">
            <div className="flex flex-col sm:flex-row items-start gap-4">
              <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-primary-50 text-primary-600 ring-1 ring-primary-100">
                <SparklesIcon className="h-5 w-5" />
              </span>
              <div className="flex-1">
                <h2 className="font-display text-xl font-bold text-amber-700 sm:text-2xl">
                  AI Insights for This Reading
                </h2>
                <p className="text-sm text-amber-700 sm:text-base">
                  Personalized AI-powered interpretation of your palm reading — generated only
                  when you ask for it.
                </p>
              </div>
            </div>

            {/* AI Loading spinner (only this section waits) */}
            {aiLoading && (
              <LoadingSpinner label="Generating AI palm interpretation…" />
            )}

            {/* AI Error */}
            {aiError && !aiLoading && (
              <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
                <span className="font-semibold">AI Error:</span> {aiError}
                <div className="mt-3">
                  <Button variant="secondary" size="sm" icon={RetryIcon} onClick={handleGenerateAi}>
                    Try again
                  </Button>
                </div>
              </div>
            )}

            {/* Display AI interpretation when ready */}
            {result.ai_interpretation && !aiLoading && (
              <div className="surface-card p-6 animate-tab-in">
                <div className="space-y-4">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-display text-lg font-bold text-amber-700">
                      AI Interpretation {result.ai_interpretation.provider === "groq" && !result.ai_interpretation.rule_based ? "(Groq)" : ""}
                    </h3>
                    {result.ai_interpretation.rule_based ? (
                      <span className="rounded-full border border-amber-300 bg-amber-100 px-2.5 py-1 text-sm font-semibold text-amber-700">
                        Rule-based fallback
                      </span>
                    ) : (
                      <span className="text-[12.5px] text-amber-700">
                        {result.ai_interpretation.engine || "AI Engine"}
                      </span>
                    )}
                  </div>

                  {result.ai_interpretation.summary && (
                    <p className="mb-3 text-sm font-semibold text-slate-800">
                      {result.ai_interpretation.summary}
                    </p>
                  )}

                  {result.ai_interpretation.body && (
                    <div className="mb-4 rounded-xl border border-amber-100 bg-amber-50 p-4">
                      <div className="mb-2 text-sm font-semibold uppercase tracking-wider text-amber-700">
                        Detailed Interpretation
                      </div>
                      <p className="text-sm leading-relaxed text-amber-700">{result.ai_interpretation.body}</p>
                    </div>
                  )}

                  {result.ai_interpretation.guidance && result.ai_interpretation.guidance.length > 0 && (
                    <div className="mb-4 rounded-xl border border-amber-100 bg-amber-50 p-4">
                      <div className="mb-2 text-sm font-semibold uppercase tracking-wider text-amber-700">
                        AI Guidance
                      </div>
                      <ul className="space-y-2 text-sm text-amber-700">
                        {result.ai_interpretation.guidance.map((step, sIdx) => (
                          <li key={sIdx} className="flex items-start gap-2">
                            <span className="text-amber-500">✦</span>
                            <span>{step}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {result.ai_interpretation.domain_insights && Object.keys(result.ai_interpretation.domain_insights).length > 0 && (
                    <div className="mb-4 rounded-xl border border-amber-100 bg-amber-50 p-4">
                      <div className="mb-2 text-sm font-semibold uppercase tracking-wider text-amber-700">
                        Domain Insights
                      </div>
                      <div className="space-y-2">
                        {Object.entries(result.ai_interpretation.domain_insights).map(([domain, insight]) => (
                          <div key={domain}>
                            <span className="text-xs font-bold text-amber-800 uppercase">{domain}:</span>
                            <p className="text-sm leading-relaxed text-amber-700 ml-2">{insight}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {result.ai_interpretation.rule_based && (
                    <div>
                      <Button
                        variant="secondary"
                        size="sm"
                        icon={RetryIcon}
                        onClick={handleGenerateAi}
                      >
                        Retry AI interpretation
                      </Button>
                    </div>
                  )}

                  {result.ai_interpretation.disclaimer && (
                    <p className="mt-3 border-t border-amber-100 pt-2 text-[12.5px] italic text-slate-500">
                      {result.ai_interpretation.disclaimer}
                    </p>
                  )}
                </div>
              </div>
            )}

            {!result.ai_interpretation && !aiLoading && !aiError && (
              <div className="rounded-[16px] border border-dashed border-amber-300/70 bg-white px-6 py-8 text-center">
                <span className="mx-auto flex h-11 w-11 items-center justify-center rounded-full bg-amber-100 text-amber-600">
                  <SparkleIcon className="h-5 w-5" />
                </span>
                <h3 className="mt-3 font-display text-base font-bold text-amber-700">
                  Generate your AI insight
                </h3>
                <p className="mx-auto mt-1.5 max-w-md text-sm leading-relaxed text-amber-700">
                  No interpretation exists for this reading yet. Run the AI model to weave your
                  palm analysis into a personalized narrative with guidance — entirely on your
                  terms.
                </p>
                <Button variant="accent" className="mt-4" icon={SparkleIcon} onClick={handleGenerateAi}>
                  Generate AI Insight
                </Button>
                <p className="mt-3 text-[12.5px] text-slate-500">
                  Takes a few seconds · saved to this reading once generated
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Live Webcam Modal */}
      <CameraCaptureModal
        isOpen={isCameraOpen}
        onClose={() => setIsCameraOpen(false)}
        onCapture={(capturedFile) => pickFile(capturedFile)}
      />
      {/* AI Chat Bot */}
      <ChatBot readingId={result?.reading_id} readingType="palm" result={result} />
      {/* Personalized Recommendations */}
      {result?.reading_id && (
        <RecommendationsSection
          readingId={result.reading_id}
          generateFn={async () => generateRecommendations({
            reading_id: result.reading_id,
            max_total: 8,
            per_type: 2,
          })}
          autoGenerate={false}
        />
      )}
    </div>
  );
}
