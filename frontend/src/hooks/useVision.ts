import { useRef, useEffect, useState, useCallback } from 'react';

export type VisionMode = 'off' | 'camera' | 'screen';

export const useVision = (mode: VisionMode = 'off', onReset?: () => void) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    let currentStream: MediaStream | null = null;
    let isMounted = true;

    // Cleanup function to stop tracks
    const stopStream = () => {
      if (currentStream) {
        console.log("[UseVision] Stopping media tracks...");
        currentStream.getTracks().forEach(t => t.stop());
        currentStream = null;
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(t => t.stop());
        streamRef.current = null;
      }
      if (isMounted) setIsReady(false);
    };

    // If mode is off, just ensure cleanup
    if (mode === 'off') {
      stopStream();
      return;
    }

    const startStream = async () => {
      try {
        let stream: MediaStream;

        if (mode === 'camera') {
            console.log("[UseVision] Requesting camera access...");
            stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: { ideal: 640 },
                    height: { ideal: 480 },
                    facingMode: "user"
                }
            });
        } else if (mode === 'screen') {
            console.log("[UseVision] Requesting screen share access...");
            // Use generic video constraints for screen share to avoid TS issues
            stream = await navigator.mediaDevices.getDisplayMedia({
                video: true,
                audio: false
            });
        } else {
            return;
        }

        if (!isMounted) {
            stream.getTracks().forEach(t => t.stop());
            return;
        }

        currentStream = stream;
        streamRef.current = stream;

        // Handle stream ending (e.g. user clicks "Stop sharing" on browser UI)
        stream.getVideoTracks()[0].onended = () => {
            console.log("[UseVision] Stream ended externally.");
            stopStream();
            if (isMounted && onReset) onReset();
        };

        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          // Wait for metadata to load to ensure dimensions are known
          videoRef.current.onloadedmetadata = async () => {
             if (!isMounted) return;
             try {
                await videoRef.current?.play();
                if (isMounted) {
                    setIsReady(true);
                    console.log(`[UseVision] ${mode} active and playing.`);
                }
             } catch (e) {
                console.error("Auto-play failed:", e);
                stopStream();
                if (isMounted && onReset) onReset();
             }
          };
        }
      } catch (err) {
        console.error(`Failed to access ${mode}:`, err);
        stopStream();
        if (isMounted && onReset) onReset();
      }
    };

    startStream();

    return () => {
      isMounted = false;
      stopStream();
    };
  }, [mode]); // Removed onReset from deps to avoid re-running on callback change

  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  // Async capture to prevent UI freeze (Argus Optimization)
  const captureFrame = useCallback(async (): Promise<string | null> => {
    if (!videoRef.current || !isReady) return null;

    const video = videoRef.current;

    // Ensure dimensions are valid
    if (video.videoWidth === 0 || video.videoHeight === 0) return null;

    if (!canvasRef.current) {
      canvasRef.current = document.createElement('canvas');
    }
    const canvas = canvasRef.current;

    // Use actual video dimensions for capture
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const ctx = canvas.getContext('2d');
    if (!ctx) return null;

    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    // Convert to JPEG base64 via Blob (Async)
    return new Promise((resolve) => {
        canvas.toBlob((blob) => {
            if (!blob) {
                resolve(null);
                return;
            }
            const reader = new FileReader();
            reader.onloadend = () => {
                const base64data = reader.result as string;
                // Remove prefix "data:image/jpeg;base64,"
                resolve(base64data.split(',')[1]);
            };
            reader.readAsDataURL(blob);
        }, 'image/jpeg', 0.8);
    });
  }, [isReady]);

  return { videoRef, captureFrame, isReady };
};
