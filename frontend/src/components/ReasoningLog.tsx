import { StepEvent } from '../types';
import StatusBadge from './StatusBadge';

interface ReasoningLogProps {
  steps: StepEvent[];
}

export default function ReasoningLog({ steps }: ReasoningLogProps) {
  if (!steps || steps.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-slate-400 dark:text-zinc-500 gap-2 bg-slate-50 dark:bg-zinc-900 rounded-xl border border-slate-200 dark:border-zinc-800">
        <svg className="w-6 h-6 opacity-30" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
        <p className="text-xs font-semibold tracking-wide">No system telemetries logged.</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {steps.map((step, idx) => {
        const isFailed = step.status === 'failed';
        const isDecision = !!step.decision;
        const cardBorderClass = isFailed
          ? 'border-l-4 border-l-red-500'
          : isDecision
            ? 'border-l-4 border-l-emerald-500'
            : 'border-l-4 border-l-slate-400 dark:border-l-zinc-600';

        return (
          <div key={idx} className={`bg-white dark:bg-zinc-900 rounded-lg p-4 border border-slate-200 dark:border-zinc-800 shadow-sm ${cardBorderClass} animate-slide-up transition-colors`}>
            <div className="flex justify-between items-center mb-3">
              <span className="font-bold text-slate-800 dark:text-zinc-200 text-xs uppercase tracking-wider font-mono">
                {step.step.replace(/_/g, ' ')}
              </span>
              <span className="text-[10px] text-slate-400 dark:text-zinc-500 font-mono">
                {new Date(step.receivedAt).toLocaleTimeString()}
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5 text-xs text-slate-700 dark:text-zinc-300">
              {step.status && (
                <div className="flex items-center gap-2">
                  <span className="text-slate-400 dark:text-zinc-500 font-bold uppercase text-[9px] tracking-wider w-16">Status</span>
                  <span className="font-mono text-slate-800 dark:text-zinc-200">{step.status}</span>
                </div>
              )}
              {step.decision && (
                <div className="flex items-center gap-2">
                  <span className="text-slate-400 dark:text-zinc-500 font-bold uppercase text-[9px] tracking-wider w-16">Decision</span>
                  <StatusBadge status={step.decision} />
                </div>
              )}
              {step.confidence !== undefined && (
                <div className="flex items-center gap-2">
                  <span className="text-slate-400 dark:text-zinc-500 font-bold uppercase text-[9px] tracking-wider w-16">Confidence</span>
                  <span className="font-mono text-slate-900 dark:text-zinc-100 font-semibold">{Math.round(step.confidence * 100)}%</span>
                </div>
              )}
              {step.risk_score !== undefined && (
                <div className="flex items-center gap-2">
                  <span className="text-slate-400 dark:text-zinc-500 font-bold uppercase text-[9px] tracking-wider w-16">Risk Score</span>
                  <span className={`font-mono font-semibold ${step.risk_score > 0.6 ? 'text-red-600 dark:text-red-400' : 'text-emerald-600 dark:text-emerald-400'}`}>{step.risk_score}</span>
                </div>
              )}
              {step.reason && (
                <div className="md:col-span-2 flex items-start gap-2 pt-1.5 border-t border-slate-100 dark:border-zinc-800 mt-1">
                  <span className="text-slate-400 dark:text-zinc-500 font-bold uppercase text-[9px] tracking-wider w-16 mt-0.5">Reason</span>
                  <span className="flex-1 text-slate-700 dark:text-zinc-300 font-normal leading-relaxed">{step.reason}</span>
                </div>
              )}
              {step.detail && (
                <div className="md:col-span-2 flex items-start gap-2 pt-1.5 border-t border-slate-100 dark:border-zinc-800 mt-1">
                  <span className="text-slate-400 dark:text-zinc-500 font-bold uppercase text-[9px] tracking-wider w-16 mt-0.5">Details</span>
                  <span className="flex-1 text-slate-800 dark:text-zinc-200 font-mono text-[11px] leading-relaxed bg-slate-50 dark:bg-zinc-800 p-2.5 rounded border border-slate-200 dark:border-zinc-700 overflow-x-auto select-all">
                    {step.detail}
                  </span>
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
