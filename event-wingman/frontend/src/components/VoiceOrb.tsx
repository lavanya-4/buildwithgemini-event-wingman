import React, { useEffect, useRef } from 'react';
import { AgentState } from '../types';
import { Mic, MicOff, Volume2, Sparkles, Pause } from 'lucide-react';

interface VoiceOrbProps {
  state: AgentState;
  audioLevel: number; // 0 to 1
  onClick: () => void;
  onInterrupt: () => void;
}

export const VoiceOrb: React.FC<VoiceOrbProps> = ({
  state,
  audioLevel,
  onClick,
  onInterrupt,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  // Dynamic canvas soundwave animation
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    let phase = 0;

    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const width = canvas.width;
      const height = canvas.height;
      const centerY = height / 2;

      // Base wave parameters based on state
      let amplitude = 10;
      let frequency = 0.03;
      let strokeColor = 'rgba(99, 102, 241, 0.4)';

      if (state === 'LISTENING') {
        amplitude = 15 + audioLevel * 35;
        frequency = 0.05;
        strokeColor = 'rgba(16, 185, 129, 0.8)';
      } else if (state === 'THINKING') {
        amplitude = 8;
        frequency = 0.08;
        strokeColor = 'rgba(245, 158, 11, 0.7)';
      } else if (state === 'SPEAKING') {
        amplitude = 20 + audioLevel * 40;
        frequency = 0.04;
        strokeColor = 'rgba(236, 72, 153, 0.8)';
      }

      ctx.beginPath();
      ctx.lineWidth = 2.5;
      ctx.strokeStyle = strokeColor;

      for (let x = 0; x < width; x++) {
        const y = centerY + Math.sin(x * frequency + phase) * amplitude * Math.sin((x / width) * Math.PI);
        if (x === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      }
      ctx.stroke();

      // Second harmonic wave
      ctx.beginPath();
      ctx.lineWidth = 1.5;
      ctx.strokeStyle = strokeColor.replace('0.8', '0.4').replace('0.7', '0.3');
      for (let x = 0; x < width; x++) {
        const y = centerY + Math.cos(x * frequency * 1.5 - phase) * (amplitude * 0.6) * Math.sin((x / width) * Math.PI);
        if (x === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      }
      ctx.stroke();

      phase += state === 'THINKING' ? 0.12 : 0.05;
      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animationFrameId);
    };
  }, [state, audioLevel]);

  // Orb gradient and glow styling
  const getOrbStyles = () => {
    switch (state) {
      case 'LISTENING':
        return {
          gradient: 'from-emerald-400 via-teal-500 to-cyan-600',
          glow: 'shadow-[0_0_60px_rgba(16,185,129,0.5)] border-emerald-400/60',
          ring: 'border-emerald-500/40 animate-ping',
          scale: `scale(${1 + audioLevel * 0.25})`,
          icon: <Mic className="w-10 h-10 text-white animate-pulse" />,
          label: 'Listening...',
          sublabel: 'Speak naturally — Gemini is listening',
        };
      case 'THINKING':
        return {
          gradient: 'from-amber-400 via-purple-500 to-indigo-600',
          glow: 'shadow-[0_0_70px_rgba(245,158,11,0.5)] border-amber-400/60',
          ring: 'border-amber-500/30 animate-spin-slow',
          scale: 'scale-105',
          icon: <Sparkles className="w-10 h-10 text-white animate-spin" />,
          label: 'Thinking & Reasoning...',
          sublabel: 'Querying memory & analyzing context',
        };
      case 'SPEAKING':
        return {
          gradient: 'from-pink-500 via-rose-500 to-purple-600',
          glow: 'shadow-[0_0_75px_rgba(236,72,153,0.55)] border-pink-400/70',
          ring: 'border-pink-500/40 animate-pulse',
          scale: `scale(${1 + audioLevel * 0.2})`,
          icon: <Volume2 className="w-10 h-10 text-white animate-bounce" />,
          label: 'Speaking...',
          sublabel: 'Tap orb or speak to interrupt (barge-in)',
        };
      case 'IDLE':
      default:
        return {
          gradient: 'from-indigo-500 via-indigo-600 to-purple-700',
          glow: 'shadow-[0_0_45px_rgba(99,102,241,0.35)] border-indigo-400/40',
          ring: 'border-indigo-500/20',
          scale: 'scale-100',
          icon: <Mic className="w-10 h-10 text-slate-200" />,
          label: 'Ready to listen',
          sublabel: 'Tap to start talking to your Wingman',
        };
    }
  };

  const current = getOrbStyles();

  return (
    <div className="flex flex-col items-center justify-center py-6 px-4 select-none">
      <div className="relative flex items-center justify-center">
        {/* Outer ambient wave rings */}
        <div
          className={`absolute w-56 h-56 rounded-full border-2 transition-all duration-500 pointer-events-none ${current.ring}`}
        />
        <div
          className={`absolute w-64 h-64 rounded-full border border-slate-700/30 transition-all duration-700 pointer-events-none ${
            state === 'LISTENING' || state === 'SPEAKING' ? 'opacity-80 scale-110' : 'opacity-20'
          }`}
        />

        {/* Core Animated Orb Button */}
        <button
          onClick={state === 'SPEAKING' ? onInterrupt : onClick}
          className={`relative z-10 w-40 h-40 rounded-full bg-gradient-to-tr ${current.gradient} ${current.glow} border-2 flex items-center justify-center transition-transform duration-150 cursor-pointer shadow-2xl active:scale-95 group focus:outline-none`}
          style={{ transform: current.scale }}
          title={state === 'SPEAKING' ? 'Click to interrupt' : 'Click to toggle microphone'}
          aria-label={current.label}
        >
          {/* Subtle glossy overlay */}
          <div className="absolute inset-2 rounded-full bg-white/10 blur-[1px] pointer-events-none" />
          <div className="relative z-20 flex flex-col items-center justify-center">
            {current.icon}
          </div>
        </button>
      </div>

      {/* Real-time Audio Waveform Canvas */}
      <div className="w-64 h-10 mt-6 flex items-center justify-center">
        <canvas ref={canvasRef} width={256} height={40} className="w-full h-full" />
      </div>

      {/* State Badge & Prompt */}
      <div className="text-center mt-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold tracking-wide uppercase bg-slate-800/80 border border-slate-700/60 shadow-inner">
          <span
            className={`w-2 h-2 rounded-full ${
              state === 'LISTENING'
                ? 'bg-emerald-400 animate-ping'
                : state === 'THINKING'
                ? 'bg-amber-400 animate-spin'
                : state === 'SPEAKING'
                ? 'bg-pink-400 animate-pulse'
                : 'bg-indigo-400'
            }`}
          />
          <span className="text-slate-200">{current.label}</span>
        </div>
        <p className="text-xs text-slate-400 mt-1.5 font-medium">{current.sublabel}</p>
      </div>
    </div>
  );
};
