import type { MutableRefObject } from 'react';
import { createAudioBuffer } from './audioUtils';

export class AudioStreamManager {
  private ctx: AudioContext | null = null;
  private workletNode: AudioWorkletNode | null = null;
  private sourceNode: MediaStreamAudioSourceNode | null = null;
  private systemSourceNode: MediaStreamAudioSourceNode | null = null;
  private mediaStream: MediaStream | null = null;
  private analyser: AnalyserNode | null = null;
  private animationFrame: number | null = null;
  private nextStartTime: number = 0;

  // AEC Audio Tag Hack
  private streamDestination: MediaStreamAudioDestinationNode | null = null;
  private hiddenAudioElement: HTMLAudioElement | null = null;

  // Track active sources for barge-in cancellation
  private activeSources: AudioBufferSourceNode[] = [];

  private volumeRef: MutableRefObject<number>;
  private onAudioInput: (data: ArrayBuffer) => void;

  constructor(
    volumeRef: MutableRefObject<number>,
    onAudioInput: (data: ArrayBuffer) => void
  ) {
    this.volumeRef = volumeRef;
    this.onAudioInput = onAudioInput;
  }

  async initialize() {
    if (this.ctx) return;

    this.ctx = new AudioContext({ sampleRate: 16000 });
    await this.ctx.resume();
    await this.ctx.audioWorklet.addModule('/pcm-processor.js');

    // AEC Audio Tag Hack: Route output to a MediaStreamDestination
    this.streamDestination = this.ctx.createMediaStreamDestination();

    // Create hidden audio element to play the stream
    // This forces the browser to recognize the audio as "media" for echo cancellation
    this.hiddenAudioElement = new Audio();
    this.hiddenAudioElement.srcObject = this.streamDestination.stream;
    this.hiddenAudioElement.autoplay = true;
    this.hiddenAudioElement.play().catch(e => console.error("Hidden Audio Play Error:", e));
  }

  addSystemAudioTrack(track: MediaStreamTrack) {
      if (!this.ctx || !this.workletNode) {
          console.warn("AudioContext not ready for system audio.");
          return;
      }

      console.log("Adding System Audio Track to Mixer...");

      // If a previous system source exists, disconnect it
      if (this.systemSourceNode) {
          this.systemSourceNode.disconnect();
      }

      const stream = new MediaStream([track]);
      this.systemSourceNode = this.ctx.createMediaStreamSource(stream);

      // Mix into the same Worklet Node (Web Audio API sums inputs automatically)
      this.systemSourceNode.connect(this.workletNode);
  }

  removeSystemAudioTrack() {
      if (this.systemSourceNode) {
          console.log("Removing System Audio Track...");
          this.systemSourceNode.disconnect();
          this.systemSourceNode = null;
      }
  }

  async start() {
    if (!this.ctx) await this.initialize();
    if (!this.ctx) throw new Error("AudioContext failed to initialize");

    try {
      // 10s Timeout for Microphone Access
      const getUserMediaPromise = navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          autoGainControl: true,
          noiseSuppression: true
        }
      });

      const timeoutPromise = new Promise<never>((_, reject) =>
          setTimeout(() => reject(new Error("Microphone access timed out (10s).")), 10000)
      );

      this.mediaStream = await Promise.race([getUserMediaPromise, timeoutPromise]) as MediaStream;

      this.sourceNode = this.ctx.createMediaStreamSource(this.mediaStream);
      this.workletNode = new AudioWorkletNode(this.ctx, 'pcm-processor');

      this.workletNode.port.onmessage = (event) => {
        this.onAudioInput(event.data);
      };

      // Connect Source -> Worklet (but not to destination to avoid feedback)
      this.sourceNode.connect(this.workletNode);

      // Analyzer for Volume Visualization
      this.analyser = this.ctx.createAnalyser();
      this.analyser.fftSize = 256;
      this.sourceNode.connect(this.analyser);

      this.startVolumeAnalysis();

      this.nextStartTime = this.ctx.currentTime;

    } catch (err) {
      console.error("Error starting audio stream:", err);
      throw err;
    }
  }

  private startVolumeAnalysis() {
    if (!this.analyser) return;

    const dataArray = new Uint8Array(this.analyser.frequencyBinCount);

    const updateVolume = () => {
        if (!this.analyser) return;
        this.analyser.getByteFrequencyData(dataArray);

        let sum = 0;
        for (let i = 0; i < dataArray.length; i++) {
            sum += dataArray[i];
        }
        const average = sum / dataArray.length;

        // Update the ref directly
        this.volumeRef.current = Math.min(1, average / 128);

        this.animationFrame = requestAnimationFrame(updateVolume);
    };
    updateVolume();
  }

  playAudioChunk(data: ArrayBuffer) {
    if (!this.ctx) return;

    // Vista directa en memoria, sin el peso del Base64
    const int16Data = new Int16Array(data);
    const float32Data = new Float32Array(int16Data.length);

    // Normalización matemática directa
    for (let i = 0; i < int16Data.length; i++) {
      float32Data[i] = int16Data[i] / 32768.0;
    }

    // Inyección al AudioContext
    const buffer = createAudioBuffer(this.ctx, float32Data);
    const source = this.ctx.createBufferSource();
    source.buffer = buffer;

    // Track source for cancellation
    source.onended = () => {
        this.activeSources = this.activeSources.filter(s => s !== source);
    };
    this.activeSources.push(source);

    // AEC Audio Tag Hack: Route to stream destination instead of context.destination
    if (this.streamDestination) {
        source.connect(this.streamDestination);
    } else {
        // Fallback (should not happen if initialized correctly)
        source.connect(this.ctx.destination);
    }

    const currentTime = this.ctx.currentTime;

    // Dynamic Jitter Buffer Strategy
    // Goal: Maintain a smooth stream without hard resets or high latency.
    const JITTER_BUFFER_MS = 0.06; // 60ms target buffer (Tight but safe)
    const MAX_LATENCY_MS = 0.20;   // 200ms max latency before catch-up
    const CATCHUP_RATE = 1.05;     // 5% speedup to catch up gently

    let startTime = this.nextStartTime;

    // 1. Underrun Handling (The Gap)
    // If nextStartTime is in the past, we ran dry. Reset to now + small buffer.
    if (startTime < currentTime) {
        startTime = currentTime + JITTER_BUFFER_MS;
    }

    // 2. Latency Handling (The Drift)
    // If buffer is too large (startTime is far in future), play faster to catch up.
    let playbackRate = 1.0;
    if (startTime > currentTime + MAX_LATENCY_MS) {
        playbackRate = CATCHUP_RATE;
    }

    source.playbackRate.value = playbackRate;
    source.start(startTime);

    // 3. Advance Next Start Time
    // Calculate effective duration based on playback rate
    this.nextStartTime = startTime + (buffer.duration / playbackRate);
  }

  /**
   * Sovereign Voice Protocol: Immediate Silence
   * Flushes all pending audio buffers and resets the timeline.
   */
  flush() {
      if (!this.ctx) return;
      console.log("🔇 Sovereign Voice: Flushing Audio Buffer...");

      // 1. Stop all active sources
      this.activeSources.forEach(source => {
          try {
              source.stop();
              source.disconnect();
          } catch (e) {
              // Ignore already stopped errors
          }
      });
      this.activeSources = [];

      // 2. Reset timeline to now
      this.nextStartTime = this.ctx.currentTime;
  }

  cleanup() {
    this.flush();

    if (this.animationFrame) {
      cancelAnimationFrame(this.animationFrame);
      this.animationFrame = null;
    }

    if (this.sourceNode) {
        this.sourceNode.disconnect();
        this.sourceNode = null;
    }

    if (this.systemSourceNode) {
        this.systemSourceNode.disconnect();
        this.systemSourceNode = null;
    }

    if (this.workletNode) {
        this.workletNode.disconnect();
        this.workletNode = null;
    }

    if (this.mediaStream) {
        this.mediaStream.getTracks().forEach(track => track.stop());
        this.mediaStream = null;
    }

    if (this.hiddenAudioElement) {
        this.hiddenAudioElement.pause();
        this.hiddenAudioElement.srcObject = null;
        this.hiddenAudioElement = null;
    }

    if (this.streamDestination) {
        this.streamDestination.disconnect();
        this.streamDestination = null;
    }

    if (this.ctx) {
        this.ctx.close();
        this.ctx = null;
    }

    this.volumeRef.current = 0;
    this.nextStartTime = 0;
  }
}
