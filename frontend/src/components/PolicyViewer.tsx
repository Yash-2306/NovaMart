import { useState, useEffect } from 'react';
import { fetchPolicy } from '../api';

interface Rule {
  id: string;
  description: string;
}

interface Policy {
  version: string;
  last_updated: string;
  rules: Rule[];
}

export default function PolicyViewer() {
  const [policy, setPolicy] = useState<Policy | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPolicy()
      .then(data => {
        setPolicy(data);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-slate-400 dark:text-zinc-500 gap-3 py-16">
        <span className="w-8 h-8 border-2 border-slate-200 dark:border-zinc-700 border-t-slate-800 dark:border-t-zinc-200 rounded-full animate-spin" />
        <p className="text-xs font-semibold tracking-wide text-slate-500 dark:text-zinc-400">Syncing rules engine schema...</p>
      </div>
    );
  }

  if (!policy) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-red-500 dark:text-red-400 gap-3 py-16">
        <svg className="w-8 h-8 opacity-80" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <p className="text-xs font-semibold">Failed to load refund policy dataset.</p>
      </div>
    );
  }

  return (
    <div className="p-6 h-full overflow-y-auto space-y-6 bg-white dark:bg-zinc-950 transition-colors">
      {/* Header card */}
      <div className="flex items-center justify-between bg-slate-50 dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 rounded-xl p-5 shadow-sm">
        <div>
          <h2 className="text-sm font-bold text-slate-800 dark:text-zinc-100 uppercase tracking-wider">Refund System Configuration</h2>
          <p className="text-xs text-slate-500 dark:text-zinc-400 mt-1">Rule Set v{policy.version}</p>
        </div>
        <div className="text-right">
          <p className="text-[10px] text-slate-400 dark:text-zinc-500 uppercase tracking-wider font-bold">Last Schema Update</p>
          <p className="text-xs text-slate-700 dark:text-zinc-300 font-mono mt-1 font-semibold">{policy.last_updated}</p>
        </div>
      </div>

      {/* Rules list */}
      <div className="space-y-4">
        <h3 className="text-xs font-bold text-slate-400 dark:text-zinc-500 uppercase tracking-wider ml-1">Evaluation Tree Rules</h3>
        <div className="grid grid-cols-1 gap-3.5">
          {policy.rules.map(rule => (
            <div
              key={rule.id}
              className="bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 rounded-xl p-4 flex items-start gap-4 transition-all hover:border-slate-300 dark:hover:border-zinc-700"
            >
              {/* Rule ID badge */}
              <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-slate-100 dark:bg-zinc-800 border border-slate-200 dark:border-zinc-700 flex items-center justify-center font-mono text-[11px] font-bold text-slate-500 dark:text-zinc-400">
                {rule.id.split('_')[0]}
              </div>
              <div className="flex-1 min-w-0">
                <h4 className="text-xs font-bold text-slate-800 dark:text-zinc-200 uppercase tracking-wider mb-1.5 font-mono">
                  {rule.id.substring(rule.id.indexOf('_') + 1).replace(/_/g, ' ')}
                </h4>
                <p className="text-xs text-slate-600 dark:text-zinc-400 leading-relaxed font-normal">
                  {rule.description}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
