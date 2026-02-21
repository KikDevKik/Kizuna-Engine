import { useRef, useEffect, useState, useCallback } from 'react';

export const useVision = (active: boolean = false) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [isCameraReady, setIsCameraReady] = useState(false);

  useEffect(() => {
    // Only request camera if 'active' is true
    if (!active) {
        // Cleanup if deactivated
        if (streamRef.current) {
            streamRef.current.getTracks().forEach(t => t.stop());
            streamRef.current = null;
        }
        setIsCameraReady(false);
        return;
    }

    const startCamera = async () => {
      try {
        console.log("[UseVision] Requesting camera access...");
        const stream = await navigator.mediaDevices.getUserMedia({
            video: {
                width: { ideal: 640 },
                height: { ideal: 480 },
                facingMode: "user"
            }
        });
        streamRef.current = stream;
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          videoRef.current.onloadedmetadata = () => {
             videoRef.current?.play().catch(e => console.error("Auto-play failed:", e));
             setIsCameraReady(true);
             console.log("[UseVision] Camera active and playing.");
          };
        }
      } catch (err) {
        console.error("Failed to access camera:", err);
        setIsCameraReady(false);
      }
    };

    startCamera();

    return () => {
      if (streamRef.current) {
        console.log("[UseVision] Stopping camera tracks...");
        streamRef.current.getTracks().forEach(t => t.stop());
        streamRef.current = null;
      }
    };
  }, [active]);

  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  const captureFrame = useCallback((): string | null => {
    if (!videoRef.current || !isCameraReady) return null;

    const video = videoRef.current;

    // Ensure dimensions are valid
    if (video.videoWidth === 0 || video.videoHeight === 0) return null;

    if (!canvasRef.current) {
      canvasRef.current = document.createElement('canvas');
    }
    const canvas = canvasRef.current;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const ctx = canvas.getContext('2d');
    if (!ctx) return null;

    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    // Convert to JPEG base64
    const dataUrl = canvas.toDataURL('image/jpeg', 0.8);
    // Remove prefix "data:image/jpeg;base64,"
    return dataUrl.split(',')[1];
  }, [isCameraReady]);

  return { videoRef, captureFrame, isCameraReady };
};
