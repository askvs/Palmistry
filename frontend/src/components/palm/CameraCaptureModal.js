import { useCallback, useEffect, useRef, useState } from "react";
import { checkHandFrame } from "@/services/palm";

export default function CameraCaptureModal({ isOpen, onClose, onCapture }) {
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const canvasRef = useRef(null);
  const isCapturingRef = useRef(false);

  const [cameraError, setCameraError] = useState(null);
  const [isStarting, setIsStarting] = useState(true);
  const [autoCaptureEnabled, setAutoCaptureEnabled] = useState(true);
  const [autoProgress, setAutoProgress] = useState(0);
  const [guidanceStatus, setGuidanceStatus] = useState("Align palm inside outline");
  const [isGoodQuality, setIsGoodQuality] = useState(false);
  const [showShutterFlash, setShowShutterFlash] = useState(false);

  // Start camera.
  useEffect(() => {
    if (!isOpen) return;

    let isMounted = true;
    isCapturingRef.current = false;

    async function startCamera() {
      try {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
          throw new Error("Webcam access is not supported by your browser environment.");
        }

        const stream = await navigator.mediaDevices.getUserMedia({
          video: {
            facingMode: "user",
            width: { ideal: 1280 },
            height: { ideal: 960 },
          },
          audio: false,
        });

        if (!isMounted) {
          stream.getTracks().forEach((t) => t.stop());
          return;
        }

        streamRef.current = stream;
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          videoRef.current.play().catch(() => {});
        }
        setIsStarting(false);
      } catch (err) {
        if (!isMounted) return;
        setIsStarting(false);
        if (err.name === "NotAllowedError" || err.name === "PermissionDeniedError") {
          setCameraError("Camera permission was denied. Please allow camera access in your browser settings.");
        } else if (err.name === "NotFoundError" || err.name === "DevicesNotFoundError") {
          setCameraError("No camera device was detected on your system.");
        } else {
          setCameraError(err.message || "Failed to initialize camera.");
        }
      }
    }

    startCamera();

    return () => {
      isMounted = false;
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop());
        streamRef.current = null;
      }
    };
  }, [isOpen]);

  // Capture a frame.
  const executeCapture = useCallback(() => {
    if (!videoRef.current || isCapturingRef.current) return;
    isCapturingRef.current = true;
    setShowShutterFlash(true);

    const video = videoRef.current;
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth || 1280;
    canvas.height = video.videoHeight || 960;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    setTimeout(() => {
      canvas.toBlob(
        (blob) => {
          if (!blob) return;
          const file = new File([blob], `palm_camera_${Date.now()}.jpg`, {
            type: "image/jpeg",
          });
          onCapture(file);
          onClose();
        },
        "image/jpeg",
        0.92
      );
    }, 180);
  }, [onCapture, onClose]);

  // Auto-capture quality loop.
  useEffect(() => {
    if (!isOpen || !autoCaptureEnabled || isStarting || cameraError) {
      return;
    }

    const offscreenCanvas = document.createElement("canvas");
    offscreenCanvas.width = 320;
    offscreenCanvas.height = 240;
    const ctx = offscreenCanvas.getContext("2d", { willReadFrequently: true });
    if (!ctx) return;

    let progressAccumulator = 0;
    let isChecking = false;

    const intervalId = setInterval(() => {
      if (isCapturingRef.current || !videoRef.current || isChecking) return;
      const video = videoRef.current;
      if (video.readyState < 2) return;

      const w = offscreenCanvas.width;
      const h = offscreenCanvas.height;
      ctx.drawImage(video, 0, 0, w, h);

      // Sharpness check for motion blur.
      let imgData;
      try {
        imgData = ctx.getImageData(0, 0, w, h);
      } catch {
        return;
      }

      const data = imgData.data;
      let gradSum = 0;
      let sampleCount = 0;
      for (let y = 30; y < h - 30; y += 4) {
        for (let x = 40; x < w - 40; x += 4) {
          const idx = (y * w + x) * 4;
          const nextIdx = (y * w + (x + 2)) * 4;
          gradSum += Math.abs(data[idx] - data[nextIdx]);
          sampleCount++;
        }
      }
      const sharpness = sampleCount > 0 ? gradSum / sampleCount : 0;
      const isMotionSteady = sharpness >= 8.5;

      isChecking = true;
      offscreenCanvas.toBlob(
        async (blob) => {
          if (!blob || isCapturingRef.current) {
            isChecking = false;
            return;
          }

          try {
            const check = await checkHandFrame(blob);
            // Hand-frame check result shape.
            if (!check.hand_detected) {
              // No hand in frame.
              setGuidanceStatus("Hold open palm inside the guide outline");
              setIsGoodQuality(false);
              progressAccumulator = Math.max(0, progressAccumulator - 30);
            } else if (!check.is_palmar) {
              // Back of hand (dorsal) shown
              setGuidanceStatus("Turn hand around — show palm creases");
              setIsGoodQuality(false);
              progressAccumulator = Math.max(0, progressAccumulator - 25);
            } else {
              // Open palm facing camera.
              if (!isMotionSteady) {
                setGuidanceStatus(`Palm detected (${check.handedness} Hand) — hold steady`);
                setIsGoodQuality(true);
              } else {
                setGuidanceStatus(`✨ Open palm in focus (${check.handedness} Hand) — holding steady…`);
                setIsGoodQuality(true);
                progressAccumulator = Math.min(100, progressAccumulator + 35);
              }
            }

            setAutoProgress(progressAccumulator);

            if (progressAccumulator >= 100 && !isCapturingRef.current) {
              executeCapture();
            }
          } catch {
            // Ignore transient frame errors.
          } finally {
            isChecking = false;
          }
        },
        "image/jpeg",
        0.75
      );
    }, 280);

    return () => clearInterval(intervalId);
  }, [isOpen, autoCaptureEnabled, isStarting, cameraError, executeCapture]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-sm animate-fadeIn">
      <div className="relative w-full max-w-xl overflow-hidden rounded-3xl border border-slate-200/80 bg-white p-6 shadow-2xl">
        {/* Header with Auto-Capture Toggle */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-100">
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-display text-lg font-bold text-slate-900">
                Palm Camera Scanner
              </h3>
              {autoCaptureEnabled && (
                <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-0.5 text-[10px] font-semibold text-emerald-700 border border-emerald-200">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  Auto-Detect ON
                </span>
              )}
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Align full palm & wrist inside the guide frame
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setAutoCaptureEnabled(!autoCaptureEnabled)}
              className={`rounded-full px-3 py-1 text-[11px] font-medium border transition ${
                autoCaptureEnabled
                  ? "bg-violet-50 text-violet-700 border-violet-200"
                  : "bg-slate-100 text-slate-600 border-slate-200"
              }`}
            >
              {autoCaptureEnabled ? "Auto: ON" : "Auto: OFF"}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="rounded-full p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Camera Viewport */}
        <div className="relative mt-4 aspect-[4/3] w-full overflow-hidden rounded-2xl bg-slate-950 flex items-center justify-center">
          {cameraError ? (
            <div className="p-6 text-center text-rose-300">
              <p className="font-medium text-sm text-rose-200">Camera Unavailable</p>
              <p className="mt-1 text-xs text-slate-400 max-w-sm mx-auto">{cameraError}</p>
            </div>
          ) : (
            <>
              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                className="h-full w-full object-cover -scale-x-100"
              />

              {/* Shutter Flash Animation */}
              {showShutterFlash && (
                <div className="absolute inset-0 z-30 bg-white animate-fadeOut" />
              )}

              {/* Dynamic Hand Alignment Silhouette Guide */}
              <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
                <svg
                  viewBox="0 0 200 240"
                  className={`h-4/5 w-auto transition-colors duration-300 ${
                    isGoodQuality
                      ? "text-emerald-400 stroke-emerald-400 fill-emerald-400/15"
                      : "text-violet-400/50 stroke-current fill-violet-500/10"
                  }`}
                  strokeWidth={isGoodQuality ? "3" : "2"}
                  strokeDasharray={isGoodQuality ? "none" : "5 5"}
                >
                  {/* Hand contour silhouette */}
                  <path
                    d="M 70 230 C 70 190, 60 170, 50 150 C 40 135, 30 115, 38 105 C 45 95, 58 105, 65 125 C 62 100, 62 70, 72 65 C 80 62, 85 75, 85 105 C 86 80, 92 40, 103 40 C 112 40, 115 70, 115 105 C 117 85, 126 55, 136 58 C 144 60, 142 85, 140 115 C 145 100, 158 90, 166 98 C 172 108, 160 145, 150 170 C 140 195, 130 210, 130 230 Z"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>

                {/* Auto-Capture Circular Radial Progress Bar */}
                {autoCaptureEnabled && autoProgress > 0 && (
                  <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                    <svg className="h-44 w-44 -rotate-90" viewBox="0 0 100 100">
                      <circle
                        cx="50"
                        cy="50"
                        r="45"
                        stroke="rgba(255, 255, 255, 0.2)"
                        strokeWidth="3"
                        fill="none"
                      />
                      <circle
                        cx="50"
                        cy="50"
                        r="45"
                        stroke="#10b981"
                        strokeWidth="4"
                        fill="none"
                        strokeDasharray={2 * Math.PI * 45}
                        strokeDashoffset={
                          2 * Math.PI * 45 * (1 - autoProgress / 100)
                        }
                        strokeLinecap="round"
                        className="transition-all duration-100 ease-linear"
                      />
                    </svg>
                  </div>
                )}

                {/* Real-time Guidance Pill */}
                <div
                  className={`absolute bottom-3 rounded-full px-4 py-1.5 text-xs font-medium backdrop-blur-md transition-all shadow-md ${
                    isGoodQuality
                      ? "bg-emerald-950/85 text-emerald-200 border border-emerald-500/40"
                      : "bg-slate-950/80 text-white/90 border border-white/15"
                  }`}
                >
                  {autoCaptureEnabled && isGoodQuality
                    ? `Auto-capturing in steady frame… (${autoProgress}%)`
                    : guidanceStatus}
                </div>
              </div>

              {isStarting && (
                <div className="absolute inset-0 flex items-center justify-center bg-slate-950 text-slate-400 text-xs">
                  Starting camera…
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer Actions */}
        <div className="mt-5 flex items-center justify-between">
          <button
            type="button"
            onClick={onClose}
            className="rounded-full border border-slate-200 bg-white px-4 py-2 text-xs font-medium text-slate-700 hover:bg-slate-50 transition"
          >
            Cancel
          </button>

          <div className="flex items-center gap-3">
            {autoCaptureEnabled && (
              <span className="text-[11px] text-slate-500 hidden sm:inline">
                Hold hand steady inside frame
              </span>
            )}
            <button
              type="button"
              onClick={executeCapture}
              disabled={!!cameraError || isStarting}
              className="inline-flex items-center gap-2 rounded-full bg-violet-600 px-6 py-2.5 text-xs font-semibold text-white shadow-md shadow-violet-600/25 hover:bg-violet-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
            >
              <span className="h-2.5 w-2.5 rounded-full bg-white animate-pulse" />
              Capture Now
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
