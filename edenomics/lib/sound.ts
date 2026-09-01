"use client";

/**
 * Synthesised sound. No audio files — every cue is a few oscillators with an
 * envelope, which costs nothing to ship and lets the pitch respond to what
 * just happened (a confident miss lands lower and uglier than a hedged one).
 *
 * Nothing ever plays on its own. The context is only created on the first
 * real gesture, so this can never behave like autoplay.
 */
let context: AudioContext | null = null;
let muted = false;
let loaded = false;

const STORAGE_KEY = "edenomics.muted";
const listeners = new Set<() => void>();

function load() {
  if (loaded) return;
  loaded = true;
  try {
    muted = window.localStorage.getItem(STORAGE_KEY) === "1";
  } catch {
    muted = false;
  }
}

/**
 * Exposed as a store so the toggle can be read with useSyncExternalStore:
 * reading storage inside an effect would render the wrong icon first and then
 * correct itself.
 */
export function subscribeMuted(listener: () => void): () => void {
  load();
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function getMutedSnapshot(): boolean {
  return muted;
}

export function getMutedServerSnapshot(): boolean {
  return false;
}

export function setMuted(next: boolean): void {
  muted = next;
  try {
    window.localStorage.setItem(STORAGE_KEY, next ? "1" : "0");
  } catch {
    // Storage blocked — the setting just won't survive a reload.
  }
  for (const listener of listeners) listener();
}

function ready(): AudioContext | null {
  if (muted || typeof window === "undefined") return null;
  try {
    context ??= new (window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext)();
    if (context.state === "suspended") void context.resume();
    return context;
  } catch {
    return null;
  }
}

interface Tone {
  freq: number;
  /** Slide to this frequency across the note, for whooshes and drops. */
  to?: number;
  duration?: number;
  type?: OscillatorType;
  gain?: number;
  delay?: number;
}

function tone({ freq, to, duration = 0.12, type = "sine", gain = 0.08, delay = 0 }: Tone): void {
  const ctx = ready();
  if (!ctx) return;

  const start = ctx.currentTime + delay;
  const osc = ctx.createOscillator();
  const amp = ctx.createGain();

  osc.type = type;
  osc.frequency.setValueAtTime(freq, start);
  if (to !== undefined) osc.frequency.exponentialRampToValueAtTime(Math.max(1, to), start + duration);

  // A quick attack and an exponential tail — a click, not a beep.
  amp.gain.setValueAtTime(0.0001, start);
  amp.gain.exponentialRampToValueAtTime(gain, start + 0.012);
  amp.gain.exponentialRampToValueAtTime(0.0001, start + duration);

  osc.connect(amp).connect(ctx.destination);
  osc.start(start);
  osc.stop(start + duration + 0.02);
}

export const sfx = {
  /** Card leaves the felt. */
  lift: () => tone({ freq: 320, to: 460, duration: 0.09, type: "triangle", gain: 0.05 }),
  /** One step of conviction. Pitch rises with certainty, so the hand hears it. */
  notch: (certainty: number) =>
    tone({ freq: 420 + certainty * 520, duration: 0.035, type: "square", gain: 0.022 }),
  /** The throw. */
  whoosh: () => tone({ freq: 700, to: 180, duration: 0.22, type: "sawtooth", gain: 0.045 }),
  /** Called it. Two notes, a rising third. */
  good: () => {
    tone({ freq: 523, duration: 0.14, type: "triangle", gain: 0.09 });
    tone({ freq: 784, duration: 0.28, type: "triangle", gain: 0.075, delay: 0.09 });
  },
  /** Missed it. The lower it lands, the surer you were. */
  bad: (certainty: number) => {
    tone({ freq: 220 - certainty * 70, to: 90, duration: 0.34, type: "sawtooth", gain: 0.07 });
  },
  /** Hand complete. */
  fanfare: () => {
    [523, 659, 784, 1047].forEach((freq, i) =>
      tone({ freq, duration: 0.34, type: "triangle", gain: 0.07, delay: i * 0.085 }),
    );
  },
  tap: () => tone({ freq: 600, duration: 0.03, type: "square", gain: 0.03 }),
};
