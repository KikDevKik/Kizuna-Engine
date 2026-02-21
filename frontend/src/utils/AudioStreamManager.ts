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
    source.connect(this.ctx.destination);

    const currentTime = this.ctx.currentTime;

    // El Jitter Buffer: Si el reproductor se quedó sin audio (currentTime superó a nextStartTime),
    // le damos un margen de 100ms a 150ms al futuro para que acumule el siguiente paquete y no se entrecorte.
    if (this.nextStartTime < currentTime) {
      this.nextStartTime = currentTime + 0.15; // 150ms de gracia
    }

    source.start(this.nextStartTime);
    this.nextStartTime += buffer.duration;
  }

  cleanup() {
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

    if (this.ctx) {
        this.ctx.close();
        this.ctx = null;
    }

    this.volumeRef.current = 0;
    this.nextStartTime = 0;
  }
}
