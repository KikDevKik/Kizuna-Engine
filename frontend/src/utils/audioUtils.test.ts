import { describe, it, expect, vi } from 'vitest';
import { createAudioBuffer } from './audioUtils';

describe('createAudioBuffer', () => {
  it('should create an AudioBuffer with correct parameters and copy data', () => {
    // Arrange
    const sampleRate = 48000;
    const float32Data = new Float32Array([0.1, 0.2, 0.3]);

    // Mock AudioBuffer
    const mockAudioBuffer = {
      copyToChannel: vi.fn(),
      length: float32Data.length,
      sampleRate: sampleRate,
      numberOfChannels: 1
    };

    // Mock AudioContext
    const mockCtx = {
      createBuffer: vi.fn().mockReturnValue(mockAudioBuffer),
    } as unknown as AudioContext;

    // Act
    const result = createAudioBuffer(mockCtx, float32Data, sampleRate);

    // Assert
    expect(mockCtx.createBuffer).toHaveBeenCalledWith(1, float32Data.length, sampleRate);
    expect(result).toBe(mockAudioBuffer);
    expect(mockAudioBuffer.copyToChannel).toHaveBeenCalledWith(float32Data, 0);
  });

  it('should use default sample rate of 24000Hz if not provided', () => {
    // Arrange
    const float32Data = new Float32Array([0.5, -0.5]);
    const defaultSampleRate = 24000; // As per implementation default

    const mockAudioBuffer = {
      copyToChannel: vi.fn(),
    };

    const mockCtx = {
      createBuffer: vi.fn().mockReturnValue(mockAudioBuffer),
    } as unknown as AudioContext;

    // Act
    createAudioBuffer(mockCtx, float32Data);

    // Assert
    expect(mockCtx.createBuffer).toHaveBeenCalledWith(1, float32Data.length, defaultSampleRate);
  });

  it('should handle empty data', () => {
      const float32Data = new Float32Array([]);
      const mockAudioBuffer = { copyToChannel: vi.fn() };
      const mockCtx = { createBuffer: vi.fn().mockReturnValue(mockAudioBuffer) } as unknown as AudioContext;

      createAudioBuffer(mockCtx, float32Data);

      expect(mockCtx.createBuffer).toHaveBeenCalledWith(1, 0, 24000);
      expect(mockAudioBuffer.copyToChannel).toHaveBeenCalledWith(float32Data, 0);
  });
});
