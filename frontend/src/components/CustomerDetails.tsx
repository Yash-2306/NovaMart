import { useState, useEffect } from 'react';
import type { Order } from '../types';
import { ADMIN_KEY } from '../api';

interface CustomerDetailsProps {
  customerId: string;
  onBack: () => void;
}

export default function CustomerDetails({ customerId, onBack }: CustomerDetailsProps) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`/api/admin/customer/${customerId}`, { headers: { 'X-Admin-Key': ADMIN_KEY } })
      .then(res => {
        if (!res.ok) throw new Error('Failed to fetch customer details');
        return res.json();
      })
      .then(d => {
        setData(d);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, [customerId]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-slate-400 dark:text-zinc-500">
        <div className="w-8 h-8 rounded-full border-2 border-slate-300 border-t-slate-800 dark:border-zinc-700 dark:border-t-zinc-300 animate-spin mb-4" />
        <p className="text-xs font-semibold">Loading customer details...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-rose-500 bg-white dark:bg-black border border-slate-200 dark:border-zinc-800 rounded-xl shadow-sm">
        <p className="text-xs font-semibold">{error || 'Customer not found'}</p>
        <button onClick={onBack} className="mt-4 text-xs underline">Go Back</button>
      </div>
    );
  }

  const { customer, orders, refunds } = data;

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <button 
        onClick={onBack}
        className="flex items-center text-xs font-semibold text-slate-500 dark:text-zinc-400 hover:text-slate-900 dark:hover:text-white transition-colors"
      >
        <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
        </svg>
        Back to Customers
      </button>

      {/* Customer Profile Card */}
      <div className="bg-white dark:bg-black border border-slate-200 dark:border-zinc-800 rounded-xl shadow-sm overflow-hidden flex flex-col md:flex-row items-center p-6 gap-6 transition-colors">
        <div className="w-20 h-20 rounded-full bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 flex items-center justify-center text-3xl font-bold uppercase shrink-0">
          {customer.name.charAt(0)}
        </div>
        <div className="flex-1 text-center md:text-left">
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white">{customer.name}</h2>
          <p className="text-sm text-slate-500 dark:text-zinc-400">{customer.email}</p>
          {customer.delivery_address && (
            <p className="text-xs text-slate-500 dark:text-zinc-450 mt-1 flex items-center justify-center md:justify-start gap-1">
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.242-4.243a8 8 0 1111.314 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              {customer.delivery_address}
            </p>
          )}
          <div className="mt-2 flex flex-wrap gap-2 justify-center md:justify-start">
            <span className={`text-xs uppercase tracking-wider font-bold px-2 py-0.5 rounded border ${
              customer.account_tier === 'vip' 
                ? 'bg-amber-50 dark:bg-amber-950/30 text-amber-600 dark:text-amber-400 border-amber-200 dark:border-amber-900/50' 
                : customer.account_tier === 'premium'
                ? 'bg-indigo-50 dark:bg-indigo-950/30 text-indigo-600 dark:text-indigo-400 border-indigo-200 dark:border-indigo-900/50'
                : 'bg-slate-100 dark:bg-zinc-900 text-slate-600 dark:text-zinc-400 border-slate-200 dark:border-zinc-700'
            }`}>
              {customer.account_tier}
            </span>
            <span className="text-xs bg-slate-100 dark:bg-zinc-900 text-slate-600 dark:text-zinc-400 px-2 py-0.5 rounded border border-slate-200 dark:border-zinc-700">
              Joined {new Date(customer.joined_at).toLocaleDateString()}
            </span>
          </div>
        </div>
        <div className="text-center md:text-right p-4 bg-slate-50 dark:bg-zinc-900 rounded-lg border border-slate-100 dark:border-zinc-800">
          <div className="text-xs font-semibold text-slate-500 dark:text-zinc-400 uppercase tracking-wider">Total Spent</div>
          <div className="text-3xl font-mono font-bold text-emerald-600 dark:text-emerald-400">
            ${customer.total_spent.toFixed(2)}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Order History */}
        <div className="bg-white dark:bg-black border border-slate-200 dark:border-zinc-800 rounded-xl shadow-sm p-5">
          <h3 className="text-sm font-bold text-slate-800 dark:text-zinc-150 uppercase tracking-wider mb-4 border-b border-slate-100 dark:border-zinc-800 pb-2">Order History</h3>
          <div className="space-y-3">
            {orders.length === 0 ? (
              <p className="text-xs text-slate-500 dark:text-zinc-500 italic">No orders found.</p>
            ) : orders.map((o: Order) => (
              <div key={o.id} className="flex items-center justify-between p-3 rounded-lg border border-slate-100 dark:border-zinc-800 bg-slate-50 dark:bg-zinc-900/50">
                <div>
                  <div className="font-bold text-sm text-slate-800 dark:text-zinc-200">{o.product_name}</div>
                  <div className="text-xs text-slate-500 dark:text-zinc-400 font-mono mt-0.5">Ordered: {o.purchase_date ? new Date(o.purchase_date).toLocaleDateString() : 'N/A'}</div>
                </div>
                <div className="text-right">
                  <div className="font-mono font-bold text-emerald-600 dark:text-emerald-400">${o.amount.toFixed(2)}</div>
                  <div className={`text-[10px] inline-block uppercase tracking-wider font-bold px-1.5 py-0.5 mt-1 rounded ${
                    o.order_status === 'delivered' ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-400' :
                    o.order_status === 'shipped' ? 'bg-blue-100 text-blue-700 dark:bg-blue-950/50 dark:text-blue-400' :
                    'bg-slate-200 text-slate-600 dark:bg-zinc-800 dark:text-zinc-400'
                  }`}>
                    {o.order_status}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Refund Requests */}
        <div className="bg-white dark:bg-black border border-slate-200 dark:border-zinc-800 rounded-xl shadow-sm p-5">
          <h3 className="text-sm font-bold text-slate-800 dark:text-zinc-150 uppercase tracking-wider mb-4 border-b border-slate-100 dark:border-zinc-800 pb-2">Refund Requests</h3>
          <div className="space-y-3">
            {refunds.length === 0 ? (
              <p className="text-xs text-slate-500 dark:text-zinc-500 italic">No refund requests.</p>
            ) : refunds.map((r: any) => (
              <div key={r.id} className="p-3 rounded-lg border border-slate-100 dark:border-zinc-800 bg-slate-50 dark:bg-zinc-900/50">
                <div className="flex justify-between items-start mb-2">
                  <div className="text-xs text-slate-500 dark:text-zinc-400 font-mono">{new Date(r.created_at).toLocaleString()}</div>
                  <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded border ${
                    r.decision === 'approved' ? 'bg-emerald-100 text-emerald-700 border-emerald-200 dark:bg-emerald-900/30 dark:text-emerald-400 dark:border-emerald-800' :
                    r.decision === 'denied' ? 'bg-rose-100 text-rose-700 border-rose-200 dark:bg-rose-900/30 dark:text-rose-400 dark:border-rose-800' :
                    'bg-amber-100 text-amber-700 border-amber-200 dark:bg-amber-900/30 dark:text-amber-400 dark:border-amber-800'
                  }`}>
                    {r.decision}
                  </span>
                </div>
                <div className="text-sm font-medium text-slate-800 dark:text-zinc-200 mb-1 line-clamp-2">
                  {r.decision_reason || 'No reasoning provided.'}
                </div>
                <div className="text-[10px] text-slate-400 font-mono mt-2">Req ID: {r.id.substring(0,8)}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
