/**
 * Converts a base64 string (PCM 16-bit) to a Float32Array suitable for Web Audio API.
 * Preserves the exact math used in the original implementation.
 */
export const base64ToFloat32 = (base64: string): Float32Array => {
  const binaryString = atob(base64);
  const len = binaryString.length;
  const bytes = new Uint8Array(len);
  for (let i = 0; i < len; i++) {
    bytes[i] = binaryString.charCodeAt(i);
  }
  // Create Int16Array from the buffer of Uint8Array
  // Note: This assumes the system endianness matches the data (usually Little Endian for WAV/PCM)
  const int16Data = new Int16Array(bytes.buffer);
  const float32Data = new Float32Array(int16Data.length);

  // Convert Int16 to Float32 [-1.0, 1.0]
  for (let i = 0; i < int16Data.length; i++) {
      float32Data[i] = int16Data[i] / 32768.0;
  }

  return float32Data;
};

/**
 * Creates an AudioBuffer from Float32 data.
 * Defaults to 24000Hz as per Gemini Live API output specifications.
 */
export const createAudioBuffer = (
  ctx: AudioContext,
  float32Data: Float32Array | Float32Array<ArrayBufferLike>,
  sampleRate: number = 24000
): AudioBuffer => {
  const buffer = ctx.createBuffer(1, float32Data.length, sampleRate);
  // Type assertion needed because AudioBuffer.copyToChannel expects Float32Array<ArrayBuffer>
  // but we might have ArrayBufferLike from other contexts.
  // We force cast to unknown then Float32Array<ArrayBuffer> to satisfy the compiler.
  buffer.copyToChannel(float32Data as unknown as Float32Array<ArrayBuffer>, 0);
  return buffer;
};
