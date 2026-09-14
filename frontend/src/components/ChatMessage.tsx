import { ChatMessage as ChatMessageType } from '../types';
import StatusBadge from './StatusBadge';

interface Props {
  message: ChatMessageType;
}

const RULE_LABELS: Record<string, string> = {
  R01_FINAL_SALE: 'R01',
  R02_DIGITAL_PRODUCT: 'R02',
  R03_FOOD_PERISHABLE: 'R03',
  R04_CANCELLED_ORDER: 'R04',
  R05_UNDELIVERED: 'R05',
  R06_MISSING_DELIVERY_DATE: 'R06',
  R07_PAST_RETURN_WINDOW: 'R07',
  R08_HIGH_VALUE: 'R08',
  R09_HIGH_VALUE_JEWELRY: 'R09',
  R10_VIP_BORDERLINE: 'R10',
  R11_LOW_CONFIDENCE: 'R11',
  R12_ALL_PASS: 'R12',
};

export default function ChatMessage({ message }: Props) {
  const isAssistant = message.role === 'assistant';
  const hasPolicy = message.decision && message.decision !== 'clarification' && message.decision !== 'flagged';
  const confidencePct = message.confidence != null ? Math.round(message.confidence * 100) : null;
  const ruleLabel = message.ruleApplied ? (RULE_LABELS[message.ruleApplied] ?? message.ruleApplied) : null;

  return (
    <div className={`flex w-full gap-3 ${isAssistant ? 'justify-start' : 'justify-end'} animate-slide-up`}>
      {isAssistant && (
        <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-slate-100 dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 flex items-center justify-center shadow-sm">
          <svg className="w-4 h-4 text-slate-500 dark:text-zinc-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 21l8.982-5.063M18 13.612v5.333a2.25 2.25 0 01-2.249 2.25H9.75M3 8.25h18M3 12h18M3 15.75h18M5.25 5.25h13.5c.621 0 1.125.504 1.125 1.125v11.25a1.125 1.125 0 01-1.125 1.125H5.25a1.125 1.125 0 01-1.125-1.125V6.375c0-.621.504-1.125 1.125-1.125z" />
          </svg>
        </div>
      )}
      <div className={`max-w-[78%] rounded-xl px-4 py-3.5 shadow-sm transition-all ${
        isAssistant 
          ? 'glass-card text-slate-800 dark:text-zinc-200' 
          : 'bg-gradient-to-br from-slate-800 to-slate-900 dark:from-zinc-100 dark:to-zinc-300 text-white dark:text-black shadow-md'
      }`}>
        <div className="flex items-center gap-2.5 mb-1 opacity-70">
          <span className="text-[10px] font-bold uppercase tracking-wider font-sans text-slate-500 dark:text-zinc-400">
            {isAssistant ? 'Nova System' : 'Customer'}
          </span>
          <span className="text-[9px] font-mono text-slate-400 dark:text-zinc-500">
            {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
        </div>
        <div className="text-[13.5px] leading-relaxed whitespace-pre-wrap font-sans font-normal">
          {message.content}
        </div>
        
        {message.decision && (
          <div className={`mt-3 pt-3 border-t flex items-center justify-between gap-4 ${isAssistant ? 'border-slate-100 dark:border-zinc-850' : 'border-slate-800 dark:border-zinc-300'}`}>
            <div className="flex items-center gap-2">
              <span className={`text-[10px] font-semibold uppercase tracking-wider ${isAssistant ? 'text-slate-400 dark:text-zinc-500' : 'text-slate-300 dark:text-zinc-700'}`}>Decision</span>
              {/* Rule ID badge */}
              {hasPolicy && ruleLabel && (
                <span className="text-[9px] font-mono bg-slate-100 dark:bg-zinc-800 text-slate-500 dark:text-zinc-400 px-1.5 py-0.5 rounded border border-slate-200 dark:border-zinc-700" title={message.ruleApplied ?? ''}>
                  {ruleLabel}
                </span>
              )}
              {/* Confidence pct */}
              {hasPolicy && confidencePct != null && (
                <span className="text-[9px] font-mono text-slate-400 dark:text-zinc-500">
                  {confidencePct}% confidence
                </span>
              )}
            </div>
            <StatusBadge status={message.decision} />
          </div>
        )}
      </div>
      {!isAssistant && (
        <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-slate-200 dark:bg-zinc-800 border border-slate-300 dark:border-zinc-700 flex items-center justify-center shadow-sm">
          <svg className="w-4 h-4 text-slate-600 dark:text-zinc-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
          </svg>
        </div>
      )}
    </div>
  );
}
