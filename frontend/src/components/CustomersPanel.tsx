import { useState, useEffect } from 'react';
import type { Customer } from '../types';
import { fetchCustomers } from '../api';

export default function CustomersPanel({ onViewCustomer }: { onViewCustomer?: (id: string) => void }) {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  useEffect(() => {
    fetchCustomers()
      .then((data) => {
        setCustomers(data.customers);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-slate-400 dark:text-zinc-500">
        <div className="w-8 h-8 rounded-full border-2 border-slate-300 border-t-slate-800 dark:border-zinc-700 dark:border-t-zinc-300 animate-spin mb-4" />
        <p className="text-xs font-semibold">Loading customers...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-rose-500 bg-white dark:bg-black border border-slate-200 dark:border-zinc-800 rounded-xl shadow-sm">
        <svg className="w-8 h-8 opacity-50 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <p className="text-xs font-semibold">{error}</p>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-4">
      <div className="flex justify-between items-center bg-white dark:bg-black border border-slate-200 dark:border-zinc-800 p-4 rounded-xl shadow-sm transition-colors">
        <div>
          <h3 className="text-xs font-bold text-slate-800 dark:text-zinc-150 uppercase tracking-wider">Customer Database</h3>
          <p className="text-[11px] text-slate-500 dark:text-zinc-400 mt-0.5">View all registered customers and their order history.</p>
        </div>
        <div className="text-xs font-mono font-bold bg-slate-100 dark:bg-zinc-900 px-3 py-1.5 rounded border border-slate-200 dark:border-zinc-800 text-slate-700 dark:text-zinc-300">
          Total: {customers.length}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {customers.map((c) => (
          <div key={c.id} className="bg-white dark:bg-black border border-slate-200 dark:border-zinc-800 rounded-xl shadow-sm overflow-hidden flex flex-col transition-colors">
            <div className="p-4 border-b border-slate-100 dark:border-zinc-800/50 flex justify-between items-start">
              <div>
                <h4 className="text-sm font-bold text-slate-900 dark:text-zinc-100">{c.name}</h4>
                <p className="text-[11px] text-slate-500 dark:text-zinc-400 mt-0.5">{c.email}</p>
              </div>
              <span className={`text-[9px] uppercase tracking-wider font-bold px-2 py-0.5 rounded border ${
                c.account_tier === 'vip' 
                  ? 'bg-amber-50 dark:bg-amber-950/30 text-amber-600 dark:text-amber-400 border-amber-200 dark:border-amber-900/50' 
                  : c.account_tier === 'premium'
                  ? 'bg-indigo-50 dark:bg-indigo-950/30 text-indigo-600 dark:text-indigo-400 border-indigo-200 dark:border-indigo-900/50'
                  : 'bg-slate-100 dark:bg-zinc-900 text-slate-600 dark:text-zinc-400 border-slate-200 dark:border-zinc-700'
              }`}>
                {c.account_tier}
              </span>
            </div>
            
            <div className="p-4 flex-1 bg-slate-50/50 dark:bg-zinc-950/20">
              <div className="text-[10px] uppercase font-bold tracking-wider text-slate-400 dark:text-zinc-500 mb-2 flex justify-between">
                <span>Orders ({c.orders?.length || 0})</span>
                {c.orders?.length > 0 && (
                  <button 
                    onClick={() => setExpandedId(expandedId === c.id ? null : c.id)}
                    className="text-indigo-600 dark:text-indigo-400 hover:underline mr-3"
                  >
                    {expandedId === c.id ? 'Hide' : 'Orders'}
                  </button>
                )}
                <button onClick={() => onViewCustomer && onViewCustomer(c.id)} className="text-emerald-600 dark:text-emerald-400 hover:underline">
                    View Details
                </button>
              </div>
              
              {expandedId === c.id && c.orders?.length > 0 && (
                <div className="space-y-2 mt-3 animate-fade-in">
                  {c.orders.map((o) => (
                    <div key={o.id} className="bg-white dark:bg-zinc-900 p-2.5 rounded border border-slate-200 dark:border-zinc-800">
                      <div className="flex justify-between items-start mb-1">
                        <span className="text-xs font-bold text-slate-700 dark:text-zinc-300 truncate pr-2">{o.product_name}</span>
                        <span className="text-xs font-mono text-emerald-600 dark:text-emerald-400">${o.amount.toFixed(2)}</span>
                      </div>
                      <div className="flex justify-between items-center mt-1.5">
                        <span className={`text-[9px] uppercase tracking-wider font-bold px-1.5 py-0.5 rounded ${
                          o.order_status === 'delivered' ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-400' :
                          o.order_status === 'shipped' ? 'bg-blue-100 text-blue-700 dark:bg-blue-950/50 dark:text-blue-400' :
                          'bg-slate-200 text-slate-600 dark:bg-zinc-800 dark:text-zinc-400'
                        }`}>
                          {o.order_status}
                        </span>
                        <span className="text-[9px] text-slate-400 font-mono">
                          {o.purchase_date ? new Date(o.purchase_date).toLocaleDateString() : 'N/A'}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
            <div className="px-4 py-2 bg-white dark:bg-black border-t border-slate-100 dark:border-zinc-800/50 text-right text-[9px] font-mono text-slate-400 dark:text-zinc-600">
              ID: {c.id.substring(0, 8)}...
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
