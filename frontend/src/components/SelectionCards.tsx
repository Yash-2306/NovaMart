import type { CustomerCandidate, OrderCandidate } from '../api';

/* ── Customer Selection Card ─────────────────────────────────────── */

interface CustomerSelectionProps {
  candidates: CustomerCandidate[];
  onSelect: (customer: CustomerCandidate) => void;
  disabled?: boolean;
}

export function CustomerSelectionCard({ candidates, onSelect, disabled }: CustomerSelectionProps) {
  return (
    <div className="flex w-full gap-3 justify-start animate-slide-up">
      <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-slate-100 dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 flex items-center justify-center shadow-sm">
        <svg className="w-4 h-4 text-slate-500 dark:text-zinc-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2">
          <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
        </svg>
      </div>
      <div className="max-w-[85%] w-full">
        <div className="glass-card rounded-xl px-4 py-3.5 mb-2">
          <div className="flex items-center gap-2 mb-1 opacity-70">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-zinc-400">Nova System</span>
          </div>
          <p className="text-[13.5px] leading-relaxed text-slate-800 dark:text-zinc-200 mb-3 font-medium">
            I found the following account(s). Please verify which one is yours:
          </p>
        </div>
        <div className="space-y-2">
          {candidates.map((c) => (
            <button
              key={c.id}
              onClick={() => onSelect(c)}
              disabled={disabled}
              className="w-full text-left glass-card rounded-xl px-4 py-3.5 transition-all hover:scale-[1.01] hover:shadow-md active:scale-[0.99] disabled:opacity-50 disabled:cursor-not-allowed group cursor-pointer border border-slate-200 dark:border-zinc-800 hover:border-indigo-300 dark:hover:border-indigo-700"
            >
              <div className="flex items-center justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2.5 mb-1">
                    <span className="text-sm font-bold text-slate-900 dark:text-white truncate">{c.name}</span>
                    <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border ${
                      c.account_tier === 'vip'
                        ? 'bg-amber-50 dark:bg-amber-950/30 text-amber-600 dark:text-amber-400 border-amber-200 dark:border-amber-800'
                        : c.account_tier === 'premium'
                        ? 'bg-indigo-50 dark:bg-indigo-950/30 text-indigo-600 dark:text-indigo-400 border-indigo-200 dark:border-indigo-800'
                        : 'bg-slate-50 dark:bg-zinc-800 text-slate-500 dark:text-zinc-400 border-slate-200 dark:border-zinc-700'
                    }`}>
                      {c.account_tier}
                    </span>
                  </div>
                  <div className="flex items-center gap-3 text-xs text-slate-500 dark:text-zinc-400">
                    <span className="font-mono">{c.email}</span>
                    <span className="text-slate-300 dark:text-zinc-600">•</span>
                    <span>{c.order_count} order{c.order_count !== 1 ? 's' : ''}</span>
                  </div>
                </div>
                <div className="flex-shrink-0 ml-3">
                  <div className="w-8 h-8 rounded-lg bg-indigo-50 dark:bg-indigo-950/30 border border-indigo-200 dark:border-indigo-800 flex items-center justify-center group-hover:bg-indigo-100 dark:group-hover:bg-indigo-900/30 transition-colors">
                    <svg className="w-4 h-4 text-indigo-500 dark:text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2.5">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                    </svg>
                  </div>
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ── Order Selection Card ────────────────────────────────────────── */

interface OrderSelectionProps {
  orders: OrderCandidate[];
  onSelect: (order: OrderCandidate) => void;
  disabled?: boolean;
}

export function OrderSelectionCard({ orders, onSelect, disabled }: OrderSelectionProps) {
  return (
    <div className="flex w-full gap-3 justify-start animate-slide-up">
      <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-slate-100 dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 flex items-center justify-center shadow-sm">
        <svg className="w-4 h-4 text-slate-500 dark:text-zinc-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2">
          <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 10.5V6a3.75 3.75 0 10-7.5 0v4.5m11.356-1.993l1.263 12c.07.665-.45 1.243-1.119 1.243H4.25a1.125 1.125 0 01-1.12-1.243l1.264-12A1.125 1.125 0 015.513 7.5h12.974c.576 0 1.059.435 1.119 1.007zM8.625 10.5a.375.375 0 11-.75 0 .375.375 0 01.75 0zm7.5 0a.375.375 0 11-.75 0 .375.375 0 01.75 0z" />
        </svg>
      </div>
      <div className="max-w-[85%] w-full">
        <div className="glass-card rounded-xl px-4 py-3.5 mb-2">
          <div className="flex items-center gap-2 mb-1 opacity-70">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-zinc-400">Nova System</span>
          </div>
          <p className="text-[13.5px] leading-relaxed text-slate-800 dark:text-zinc-200 mb-3 font-medium">
            Which order would you like to request a refund for?
          </p>
        </div>
        <div className="space-y-2">
          {orders.map((o) => {
            const statusColor =
              o.order_status === 'delivered' ? 'text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/30 border-emerald-200 dark:border-emerald-800' :
              o.order_status === 'shipped' ? 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-950/30 border-blue-200 dark:border-blue-800' :
              o.order_status === 'cancelled' ? 'text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950/30 border-red-200 dark:border-red-800' :
              'text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/30 border-amber-200 dark:border-amber-800';
            
            return (
              <button
                key={o.id}
                onClick={() => onSelect(o)}
                disabled={disabled}
                className="w-full text-left glass-card rounded-xl px-4 py-3.5 transition-all hover:scale-[1.01] hover:shadow-md active:scale-[0.99] disabled:opacity-50 disabled:cursor-not-allowed group cursor-pointer border border-slate-200 dark:border-zinc-800 hover:border-indigo-300 dark:hover:border-indigo-700"
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2.5 mb-1">
                      <span className="text-sm font-bold text-slate-900 dark:text-white truncate">{o.product_name}</span>
                      <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border ${statusColor}`}>
                        {o.order_status}
                      </span>
                    </div>
                    <div className="flex items-center gap-3 text-xs text-slate-500 dark:text-zinc-400">
                      <span className="font-bold text-slate-700 dark:text-zinc-300">${o.amount.toFixed(2)} {o.currency}</span>
                      <span className="text-slate-300 dark:text-zinc-600">•</span>
                      <span className="capitalize">{o.product_category}</span>
                      {o.purchase_date && (
                        <>
                          <span className="text-slate-300 dark:text-zinc-600">•</span>
                          <span>Ordered {o.purchase_date.slice(0, 10)}</span>
                        </>
                      )}
                    </div>
                    <div className="flex items-center gap-3 mt-1 text-[10px] text-slate-400 dark:text-zinc-500">
                      {o.is_final_sale && <span className="text-red-500 dark:text-red-400 font-semibold">⚠ FINAL SALE</span>}
                      {o.is_digital && <span className="text-blue-500 dark:text-blue-400 font-semibold">💻 Digital</span>}
                      <span className="font-mono text-slate-400 dark:text-zinc-600">ID: {o.id.slice(0, 8)}…</span>
                    </div>
                  </div>
                  <div className="flex-shrink-0 ml-3">
                    <div className="w-8 h-8 rounded-lg bg-indigo-50 dark:bg-indigo-950/30 border border-indigo-200 dark:border-indigo-800 flex items-center justify-center group-hover:bg-indigo-100 dark:group-hover:bg-indigo-900/30 transition-colors">
                      <svg className="w-4 h-4 text-indigo-500 dark:text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2.5">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                      </svg>
                    </div>
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}

/* ── Refund Method Selection Card ────────────────────────────────── */

interface RefundMethodSelectionProps {
  methods: string[];
  onSelect: (method: string) => void;
  disabled?: boolean;
}

export function RefundMethodSelectionCard({ methods, onSelect, disabled }: RefundMethodSelectionProps) {
  const methodLabels: Record<string, { label: string, desc: string, icon: JSX.Element }> = {
    store_credit: {
      label: 'Store Credit',
      desc: 'Instant $50 added to your NovaMart balance',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v12m-3-2.818l.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879-1.106-2.303 0-3.182s2.9-.879 4.006 0l.415.33M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      )
    },
    original_payment: {
      label: 'Original Payment Method',
      desc: 'Refunded to your bank in 3-5 business days',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
        </svg>
      )
    }
  };

  return (
    <div className="flex w-full gap-3 justify-start animate-slide-up">
      <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-slate-100 dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 flex items-center justify-center shadow-sm">
        <svg className="w-4 h-4 text-slate-500 dark:text-zinc-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2">
          <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 18.75a60.07 60.07 0 0115.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 013 6h-.75m0 0v-.375c0-.621.504-1.125 1.125-1.125H20.25M2.25 6v9m18-10.5v.75c0 .414.336.75.75.75h.75m-1.5-1.5h.375c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-.375m1.5-1.5H21a.75.75 0 00-.75.75v.75m0 0H3.75m0 0h-.375a1.125 1.125 0 01-1.125-1.125V15m1.5 1.5v-.75A.75.75 0 003 15h-.75M15 10.5a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
      </div>
      <div className="max-w-[85%] w-full">
        <div className="glass-card rounded-xl px-4 py-3.5 mb-2">
          <div className="flex items-center gap-2 mb-1 opacity-70">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-zinc-400">Nova System</span>
          </div>
          <p className="text-[13.5px] leading-relaxed text-slate-800 dark:text-zinc-200 mb-3 font-medium">
            Please select your preferred refund method:
          </p>
        </div>
        <div className="space-y-2">
          {methods.map((method) => {
            const info = methodLabels[method] || { label: method, desc: '', icon: null };
            return (
              <button
                key={method}
                onClick={() => onSelect(method)}
                disabled={disabled}
                className="w-full text-left glass-card rounded-xl px-4 py-3.5 transition-all hover:scale-[1.01] hover:shadow-md active:scale-[0.99] disabled:opacity-50 disabled:cursor-not-allowed group cursor-pointer border border-slate-200 dark:border-zinc-800 hover:border-emerald-300 dark:hover:border-emerald-700"
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0 flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-slate-100 dark:bg-zinc-800 flex items-center justify-center text-emerald-500 dark:text-emerald-400 border border-slate-200 dark:border-zinc-700 group-hover:bg-emerald-50 dark:group-hover:bg-emerald-900/30 group-hover:border-emerald-200 dark:group-hover:border-emerald-800 transition-colors">
                      {info.icon}
                    </div>
                    <div>
                      <div className="text-sm font-bold text-slate-900 dark:text-white mb-0.5">{info.label}</div>
                      <div className="text-[11px] text-slate-500 dark:text-zinc-400">{info.desc}</div>
                    </div>
                  </div>
                  <div className="flex-shrink-0 ml-3">
                    <div className="w-8 h-8 rounded-lg bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800 flex items-center justify-center group-hover:bg-emerald-100 dark:group-hover:bg-emerald-900/30 transition-colors">
                      <svg className="w-4 h-4 text-emerald-500 dark:text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2.5">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                      </svg>
                    </div>
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
