import React, { useState } from 'react';
import { Send, Sparkles } from 'lucide-react';

interface QuickActionsProps {
  onSendMessage: (text: string) => void;
  disabled: boolean;
}

export const QuickActions: React.FC<QuickActionsProps> = ({ onSendMessage, disabled }) => {
  const [inputText, setInputText] = useState('');

  const samplePrompts = [
    {
      label: 'Meet Sarah (Voice AI)',
      prompt: "I just met Sarah from Acme AI. She's building voice agents for healthcare. We talked about Gemini Live and she recommended exploring interruption handling. I told her I'd connect with her after the event.",
    },
    {
      label: 'Recall Voice Agents',
      prompt: 'Who did I talk to about voice agents?',
    },
    {
      label: 'Check Recommendations',
      prompt: 'What did Sarah recommend?',
    },
    {
      label: 'Draft Follow-up',
      prompt: 'Draft a follow-up to Sarah.',
    },
    {
      label: 'Similar Interests',
      prompt: 'Who have I met with interests similar to Sarah?',
    },
    {
      label: 'Event Recap',
      prompt: 'Give me my event recap.',
    },
  ];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || disabled) return;
    onSendMessage(inputText.trim());
    setInputText('');
  };

  return (
    <div className="w-full space-y-3">
      {/* Scrollable quick chip pills */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none">
        <span className="text-[11px] font-semibold text-slate-400 whitespace-nowrap flex items-center gap-1 pl-1">
          <Sparkles className="w-3 h-3 text-amber-400" /> Prompts:
        </span>
        {samplePrompts.map((item, idx) => (
          <button
            key={idx}
            disabled={disabled}
            onClick={() => onSendMessage(item.prompt)}
            className="text-xs whitespace-nowrap px-3 py-1.5 rounded-full bg-slate-800/80 hover:bg-indigo-900/60 text-slate-300 hover:text-white border border-slate-700/60 hover:border-indigo-500/50 transition-all cursor-pointer disabled:opacity-50 disabled:pointer-events-none shadow-sm"
          >
            {item.label}
          </button>
        ))}
      </div>

      {/* Manual text input fallback */}
      <form onSubmit={handleSubmit} className="relative flex items-center">
        <input
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder="Speak or type: 'I just met Priya from Google...' or 'Who did I meet?'"
          disabled={disabled}
          className="w-full bg-[#111726]/90 border border-slate-700/80 rounded-xl px-4 py-3 pr-12 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all shadow-inner"
        />
        <button
          type="submit"
          disabled={!inputText.trim() || disabled}
          className="absolute right-2 p-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white disabled:opacity-40 disabled:hover:bg-indigo-600 transition-colors cursor-pointer"
          aria-label="Send message"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
};
