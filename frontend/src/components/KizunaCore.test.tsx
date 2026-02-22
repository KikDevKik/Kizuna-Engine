/* eslint-disable @typescript-eslint/no-explicit-any */
/* eslint-disable @typescript-eslint/no-unsafe-function-type */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import * as React from 'react';
import { KizunaCore } from './KizunaCore';

// Mock CSS import
vi.mock('../KizunaHUD.css', () => ({}));

// Mock React
vi.mock('react', async (importOriginal) => {
  const actual = await importOriginal<any>();
  const mocks = {
    useRef: vi.fn(),
    useState: vi.fn(),
    useEffect: vi.fn(),
    createElement: vi.fn(),
  };

  return {
    ...actual,
    ...mocks,
    default: {
      ...actual,
      ...mocks,
    },
  };
});

describe('KizunaCore Optimization', () => {
  let volumeRefMock: { current: number };
  let coreRefMock: { current: any };
  let setStateMock: any;
  let useEffectCallbacks: Function[] = [];
  let rafCallbacks: Function[] = [];
  let rafIdCounter = 0;

  beforeEach(() => {
    // Reset mocks
    vi.clearAllMocks();
    useEffectCallbacks = [];
    rafCallbacks = [];
    rafIdCounter = 0;

    // Setup Refs
    volumeRefMock = { current: 0 };
    coreRefMock = {
      current: {
        style: {
          setProperty: vi.fn(),
        },
        dataset: {
          state: 'idle',
        },
      },
    };

    // Setup React Mocks
    (React.useRef as any).mockImplementation((initial: any) => {
        // KizunaCore calls useRef twice:
        // 1. coreRef (initial=null)
        // 2. userSpeakingRef (initial=false)
        if (initial === null) return coreRefMock;
        return { current: initial };
    });

    // useState Mock (Should not be called now)
    setStateMock = vi.fn();
    (React.useState as any).mockImplementation((initial: any) => [initial, setStateMock]);

    // useEffect Mock - capture callback
    (React.useEffect as any).mockImplementation((cb: Function) => {
      useEffectCallbacks.push(cb);
    });

    // RAF Mock
    vi.stubGlobal('requestAnimationFrame', (cb: Function) => {
      rafCallbacks.push(cb);
      return ++rafIdCounter;
    });
    vi.stubGlobal('cancelAnimationFrame', vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('initially sets up effects and does NOT use useState', () => {
    // Render
    KizunaCore({
      volumeRef: volumeRefMock as any,
      isListening: true,
      isAiSpeaking: false,
      status: 'connected',
    });

    // Check effects called
    expect(React.useEffect).toHaveBeenCalled();
    expect(useEffectCallbacks.length).toBeGreaterThan(0);

    // Check useState NOT called
    expect(React.useState).not.toHaveBeenCalled();
  });

  it('updates DOM directly via RAF when volume is high (Optimization Check)', () => {
    // Render
    KizunaCore({
      volumeRef: volumeRefMock as any,
      isListening: true,
      isAiSpeaking: false,
      status: 'connected',
    });

    // Run effects to start RAF loop
    useEffectCallbacks.forEach((cb) => cb());

    // Expect RAF loop started
    expect(rafCallbacks.length).toBeGreaterThan(0);

    // Simulate high volume
    volumeRefMock.current = 0.5;

    // Run one frame of animation (Merged Loop)
    const callbacks = [...rafCallbacks];
    rafCallbacks = []; // Clear for next frame
    callbacks.forEach((cb) => cb());

    // Check if setState was called (Should be NO)
    expect(setStateMock).not.toHaveBeenCalled();

    // Check if DOM attribute was updated directly
    expect(coreRefMock.current.dataset.state).toBe('listening');

    // Check if scale was updated
    expect(coreRefMock.current.style.setProperty).toHaveBeenCalledWith('--vol-scale', expect.any(String));
  });

  it('respects AI speaking priority', () => {
    // Render with AI speaking
    KizunaCore({
      volumeRef: volumeRefMock as any,
      isListening: true,
      isAiSpeaking: true,
      status: 'connected',
    });

    // Run effects
    useEffectCallbacks.forEach((cb) => cb());

    // Simulate high volume from user (should be ignored for visual state, but scale uses it combined)
    // Wait, logic says: if isAiSpeaking -> state='speaking'.
    volumeRefMock.current = 0.5;

    // Run frame
    const callbacks = [...rafCallbacks];
    rafCallbacks = [];
    callbacks.forEach((cb) => cb());

    // Check DOM state
    expect(coreRefMock.current.dataset.state).toBe('speaking');
  });
});
