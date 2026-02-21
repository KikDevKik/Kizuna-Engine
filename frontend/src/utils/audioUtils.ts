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
