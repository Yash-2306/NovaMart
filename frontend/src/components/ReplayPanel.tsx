import { RefundLog, StepEvent } from '../types';
import ReasoningLog from './ReasoningLog';
import StatusBadge from './StatusBadge';

interface Props {
  replayOriginal: RefundLog | null;
  replaySteps: StepEvent[];
  replayResponse: string | null;
}

export default function ReplayPanel({ replayOriginal, replaySteps, replayResponse }: Props) {
  if (!replayOriginal) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-slate-400 dark:text-zinc-500 gap-2 bg-slate-50 dark:bg-zinc-900 rounded-xl border border-slate-200 dark:border-zinc-800">
        <svg className="w-6 h-6 opacity-30 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 1121.21 8H18.2" />
        </svg>
        <p className="text-xs font-semibold tracking-wide">Select log card to load simulated replay.</p>
      </div>
    );
  }

  return (
    <div className="space-y-5 animate-slide-up bg-transparent">
      {/* Comparison Header */}
      <div className="bg-slate-50 dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 rounded-xl p-4">
        <div className="flex items-center justify-between mb-4 border-b border-slate-200 dark:border-zinc-800 pb-2.5">
          <h3 className="text-xs font-bold text-slate-800 dark:text-zinc-200 uppercase tracking-wider">Differential Run Simulation</h3>
          <span className="text-[10px] bg-slate-200 dark:bg-zinc-800 text-slate-700 dark:text-zinc-300 font-mono px-2 py-0.5 rounded border border-slate-300 dark:border-zinc-700">Compare Engine</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Original decision */}
          <div className="bg-white dark:bg-zinc-950 rounded-xl p-4 border border-slate-200 dark:border-zinc-800 flex flex-col justify-between min-h-[110px]">
            <div>
              <div className="text-[9px] text-slate-400 dark:text-zinc-500 uppercase tracking-wider font-semibold mb-2">Original Decision</div>
              <StatusBadge status={replayOriginal.decision} />
            </div>
            {replayOriginal.decision_reason && (
              <p className="text-xs text-slate-600 dark:text-zinc-400 mt-3 italic line-clamp-2" title={replayOriginal.decision_reason}>
                &ldquo;{replayOriginal.decision_reason}&rdquo;
              </p>
            )}
          </div>

          {/* Simulation run */}
          <div className="bg-white dark:bg-zinc-950 rounded-xl p-4 border border-slate-200 dark:border-zinc-800 flex flex-col justify-between min-h-[110px]">
            <div>
              <div className="text-[9px] text-slate-400 dark:text-zinc-500 uppercase tracking-wider font-semibold mb-2">Simulation Run</div>
              {replaySteps.length > 0 && replaySteps[replaySteps.length - 1].decision ? (
                <StatusBadge status={replaySteps[replaySteps.length - 1].decision!} />
              ) : (
                <div className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-slate-500 dark:bg-zinc-400 animate-ping" />
                  <span className="text-xs text-slate-400 dark:text-zinc-500 italic font-mono">running steps...</span>
                </div>
              )}
            </div>
            {replayResponse ? (
              <p className="text-xs text-slate-600 dark:text-zinc-400 mt-3 italic line-clamp-2" title={replayResponse}>
                &ldquo;{replayResponse}&rdquo;
              </p>
            ) : replaySteps.length > 0 ? (
              <p className="text-xs text-slate-400 dark:text-zinc-500 mt-3 italic">Awaiting terminal token...</p>
            ) : null}
          </div>
        </div>
      </div>

      {/* Reasoning Steps */}
      <div>
        <h3 className="text-xs font-bold text-slate-500 dark:text-zinc-400 uppercase tracking-wider mb-3 ml-1">Simulation Execution Trace</h3>
        <ReasoningLog steps={replaySteps} />
      </div>
    </div>
  );
}
