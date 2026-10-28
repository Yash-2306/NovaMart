/* ── API client for NovaMart backend ─────────────────────────────── */

import type { Stats, RefundLog, Customer, SessionInfo, SessionDetail } from './types';

// In production (Vercel/Netlify), set VITE_API_URL to your Render backend URL
// e.g. https://novamart-backend.onrender.com/api
// Locally, falls back to /api which the nginx proxy routes to http://localhost:8000
const API_BASE = (import.meta.env.VITE_API_URL as string) || '/api';

// Admin API key — documented in README and .env.example as ADMIN_API_KEY
export const ADMIN_KEY = 'novamart-admin-2024';

/** Wrapper around fetch() that injects the X-Admin-Key header. */
function adminFetch(url: string, init?: RequestInit): Promise<Response> {
  return fetch(url, {
    ...init,
    headers: {
      ...(init?.headers ?? {}),
      'X-Admin-Key': ADMIN_KEY,
    },
  });
}

// ── Admin API ─────────────────────────────────────────────────────

export async function fetchStats(): Promise<Stats> {
  const res = await adminFetch(`${API_BASE}/admin/stats`);
  if (!res.ok) throw new Error(`Failed to fetch stats: ${res.status}`);
  return res.json();
}

export async function fetchLogs(
  limit = 20,
  offset = 0,
  decision?: string,
): Promise<{ logs: RefundLog[]; total: number }> {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  if (decision) params.set('decision', decision);
  const res = await adminFetch(`${API_BASE}/admin/logs?${params}`);
  if (!res.ok) throw new Error(`Failed to fetch logs: ${res.status}`);
  return res.json();
}

export async function fetchCustomers(): Promise<{ customers: Customer[] }> {
  const res = await adminFetch(`${API_BASE}/admin/customers`);
  if (!res.ok) throw new Error(`Failed to fetch customers: ${res.status}`);
  return res.json();
}

export async function fetchSessions(): Promise<{ sessions: SessionInfo[] }> {
  const res = await adminFetch(`${API_BASE}/admin/sessions`);
  if (!res.ok) throw new Error(`Failed to fetch sessions: ${res.status}`);
  return res.json();
}

export async function fetchSession(sessionId: string): Promise<SessionDetail> {
  const res = await adminFetch(`${API_BASE}/admin/session/${sessionId}`);
  if (!res.ok) throw new Error(`Failed to fetch session: ${res.status}`);
  return res.json();
}

export async function fetchPolicy(): Promise<{ version: string; last_updated: string; rules: { id: string; description: string }[] }> {
  const res = await adminFetch(`${API_BASE}/admin/policy`);
  if (!res.ok) throw new Error(`Failed to fetch policy: ${res.status}`);
  return res.json();
}

// ── SSE Chat Stream ───────────────────────────────────────────────

export interface SSECallbacks {
  onStep: (data: Record<string, unknown>) => void;
  onToken: (token: string) => void;
  onDone: (data: Record<string, unknown>) => void;
  onError: (error: string) => void;
  onCustomerSelection?: (data: { prompt: string; candidates: CustomerCandidate[] }) => void;
  onOrderSelection?: (data: { prompt: string; orders: OrderCandidate[] }) => void;
  onRefundMethodSelection?: (data: { prompt: string; methods: string[] }) => void;
}

export interface CustomerCandidate {
  id: string;
  name: string;
  email: string;
  account_tier: string;
  delivery_address: string | null;
  created_at: string | null;
  order_count: number;
}

export interface OrderCandidate {
  id: string;
  customer_id: string;
  product_name: string;
  product_category: string;
  amount: number;
  currency: string;
  purchase_date: string | null;
  is_final_sale: boolean;
  is_digital: boolean;
  order_status: string;
  delivered_at: string | null;
}

export function startChatStream(
  message: string,
  sessionId: string,
  customerName: string | undefined,
  callbacks: SSECallbacks,
): AbortController {
  const controller = new AbortController();

  (async () => {
    try {
      const res = await fetch(`${API_BASE}/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message,
          session_id: sessionId,
          customer_name: customerName || null,
        }),
        signal: controller.signal,
      });

      if (!res.ok) {
        const errText = await res.text();
        callbacks.onError(`Server error: ${res.status} — ${errText}`);
        return;
      }

      const reader = res.body?.getReader();
      if (!reader) {
        callbacks.onError('No response body');
        return;
      }

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        let currentEvent = '';
        for (const line of lines) {
          if (line.startsWith('event: ')) {
            currentEvent = line.slice(7).trim();
          } else if (line.startsWith('data: ')) {
            const jsonStr = line.slice(6);
            try {
              const data = JSON.parse(jsonStr);
              switch (currentEvent) {
                case 'step':
                  callbacks.onStep(data);
                  break;
                case 'token':
                  callbacks.onToken(data.token);
                  break;
                case 'done':
                  callbacks.onDone(data);
                  break;
                case 'customer_selection':
                  callbacks.onCustomerSelection?.(data);
                  break;
                case 'order_selection':
                  callbacks.onOrderSelection?.(data);
                  break;
                case 'refund_method_selection':
                  callbacks.onRefundMethodSelection?.(data);
                  break;
              }
            } catch {
              // Skip malformed JSON
            }
            currentEvent = '';
          }
        }
      }
    } catch (err: unknown) {
      if (err instanceof Error && err.name === 'AbortError') return;
      callbacks.onError(
        err instanceof Error ? err.message : 'Connection lost. Please try again.',
      );
    }
  })();

  return controller;
}

// ── Replay Stream ─────────────────────────────────────────────────

export function startReplayStream(
  requestId: string,
  callbacks: SSECallbacks,
): AbortController {
  const controller = new AbortController();

  (async () => {
    try {
      const res = await fetch(`${API_BASE}/admin/replay/${requestId}`, {
        method: 'POST',
        headers: { 'X-Admin-Key': ADMIN_KEY },
        signal: controller.signal,
      });

      if (!res.ok) {
        callbacks.onError(`Replay failed: ${res.status}`);
        return;
      }

      const reader = res.body?.getReader();
      if (!reader) {
        callbacks.onError('No response body');
        return;
      }

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        let currentEvent = '';
        for (const line of lines) {
          if (line.startsWith('event: ')) {
            currentEvent = line.slice(7).trim();
          } else if (line.startsWith('data: ')) {
            const jsonStr = line.slice(6);
            try {
              const data = JSON.parse(jsonStr);
              switch (currentEvent) {
                case 'step':
                  callbacks.onStep(data);
                  break;
                case 'token':
                  callbacks.onToken(data.token);
                  break;
                case 'done':
                  callbacks.onDone(data);
                  break;
              }
            } catch {
              // skip
            }
            currentEvent = '';
          }
        }
      }
    } catch (err: unknown) {
      if (err instanceof Error && err.name === 'AbortError') return;
      callbacks.onError(err instanceof Error ? err.message : 'Replay connection lost');
    }
  })();

  return controller;
}
