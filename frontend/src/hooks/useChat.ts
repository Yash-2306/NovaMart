/* ── useChat hook — manages chat state, SSE streaming, selections, and sessions ── */

import { useState, useCallback, useRef, useEffect } from 'react';
import type { ChatMessage, StepEvent } from '../types';
import { startChatStream } from '../api';
import type { CustomerCandidate, OrderCandidate } from '../api';

function generateSessionId(): string {
  return `session-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

function getStoredSessionId(): string {
  // Always generate a fresh session ID on load. 
  // We do not persist it to localStorage because we do not fetch past messages from the backend on load.
  // This prevents the frontend state (empty) from desyncing with the backend state (loaded history).
  return generateSessionId();
}

export type ChatPhase =
  | 'idle'                // waiting for first message
  | 'streaming'           // agent is processing
  | 'select_customer'     // waiting for customer selection
  | 'select_order'        // waiting for order selection
  | 'select_refund_method'// waiting for refund method selection
  | 'free_text';          // user can type freely (negotiation)

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [steps, setSteps] = useState<StepEvent[]>([]);
  const [sessionId, setSessionId] = useState(() => getStoredSessionId());
  const [error, setError] = useState<string | null>(null);
  const [currentDecision, setCurrentDecision] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const turnCount = useRef(0);

  // Selection state
  const [phase, setPhase] = useState<ChatPhase>('idle');
  const [customerCandidates, setCustomerCandidates] = useState<CustomerCandidate[]>([]);
  const [orderCandidates, setOrderCandidates] = useState<OrderCandidate[]>([]);
  const [refundMethodCandidates, setRefundMethodCandidates] = useState<string[]>([]);

  useEffect(() => {
    if (!sessionId) {
      const newSessionId = generateSessionId();
      setSessionId(newSessionId);
    }
  }, [sessionId]);

  const sendMessage = useCallback(
    (text: string, customerName?: string) => {
      if (!text.trim() || isStreaming) return;

      setError(null);
      turnCount.current += 1;

      // Don't show protocol messages in the chat
      const isProtocol = text.startsWith('_select_customer:') || text.startsWith('_select_order:');

      if (!isProtocol) {
        // Add user message
        const userMsg: ChatMessage = {
          id: `user-${Date.now()}`,
          role: 'user',
          content: text.trim(),
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, userMsg]);
      }

      // Prepare streaming assistant message
      const assistantId = `assistant-${Date.now()}`;
      const assistantMsg: ChatMessage = {
        id: assistantId,
        role: 'assistant',
        content: '',
        timestamp: new Date(),
        isStreaming: true,
      };
      setMessages((prev) => [...prev, assistantMsg]);

      setIsStreaming(true);
      setPhase('streaming');
      setSteps([]);
      setCustomerCandidates([]);
      setOrderCandidates([]);
      setRefundMethodCandidates([]);

      const controller = startChatStream(text.trim(), sessionId, customerName, {
        onStep: (data) => {
          const stepEvent: StepEvent = {
            step: data.step as string,
            status: data.status as string,
            detail: data.detail as string | undefined,
            risk_score: data.risk_score as number | undefined,
            decision: data.decision as string | undefined,
            reason: data.reason as string | undefined,
            rules_evaluated: data.rules_evaluated as StepEvent['rules_evaluated'],
            confidence: data.confidence as number | undefined,
            sections_retrieved: data.sections_retrieved as number | undefined,
            receivedAt: new Date(),
          };
          setSteps((prev) => [...prev, stepEvent]);
        },
        onToken: (token) => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? { ...m, content: m.content + token }
                : m,
            ),
          );
        },
        onCustomerSelection: (data) => {
          setCustomerCandidates(data.candidates);
          setPhase('select_customer');
        },
        onOrderSelection: (data) => {
          setOrderCandidates(data.orders);
          setPhase('select_order');
        },
        onRefundMethodSelection: (data) => {
          setRefundMethodCandidates(data.methods);
          setPhase('select_refund_method');
        },
        onDone: (data) => {
          const decision = data.decision as string | null;
          const confidence = data.confidence as number | null | undefined;
          const ruleApplied = data.rule_applied as string | null | undefined;
          setCurrentDecision(decision);
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? { ...m, isStreaming: false, decision, confidence: confidence ?? null, ruleApplied: ruleApplied ?? null }
                : m,
            ),
          );
          setIsStreaming(false);
          // Set phase based on decision
          if (decision === 'awaiting_selection') {
            // Phase was already set by onCustomerSelection or onOrderSelection
          } else {
            setPhase('free_text');
          }
        },
        onError: (errMsg) => {
          setError(errMsg);
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? {
                    ...m,
                    isStreaming: false,
                    content:
                      m.content || 'Connection lost. Please try again.',
                  }
                : m,
            ),
          );
          setIsStreaming(false);
          setPhase('free_text');
        },
      });

      abortRef.current = controller;
    },
    [isStreaming, sessionId],
  );

  const selectCustomer = useCallback(
    (customer: CustomerCandidate) => {
      // Add a visible message showing the user's selection
      const selectionMsg: ChatMessage = {
        id: `user-${Date.now()}`,
        role: 'user',
        content: `✓ ${customer.name} (${customer.email})`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, selectionMsg]);
      setCustomerCandidates([]);
      // Send protocol message to backend
      sendMessage(`_select_customer:${customer.id}`);
    },
    [sendMessage],
  );

  const selectOrder = useCallback(
    (order: OrderCandidate) => {
      const selectionMsg: ChatMessage = {
        id: `user-${Date.now()}`,
        role: 'user',
        content: `✓ ${order.product_name} — $${order.amount.toFixed(2)}`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, selectionMsg]);
      setOrderCandidates([]);
      sendMessage(`_select_order:${order.id}`);
    },
    [sendMessage],
  );

  const selectRefundMethod = useCallback(
    (method: string) => {
      const labels: Record<string, string> = {
        store_credit: 'Store Credit',
        original_payment: 'Original Payment Method'
      };
      const selectionMsg: ChatMessage = {
        id: `user-${Date.now()}`,
        role: 'user',
        content: `✓ Selected Refund Method: ${labels[method] || method}`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, selectionMsg]);
      setRefundMethodCandidates([]);
      sendMessage(`_select_refund_method:${method}`);
    },
    [sendMessage],
  );

  const cancelStream = useCallback(() => {
    abortRef.current?.abort();
    setIsStreaming(false);
    setPhase('free_text');
  }, []);

  const clearSession = useCallback(() => {
    const newId = generateSessionId();
    setSessionId(newId);
    setMessages([]);
    setSteps([]);
    setCurrentDecision(null);
    setCustomerCandidates([]);
    setOrderCandidates([]);
    setRefundMethodCandidates([]);
    setPhase('idle');
    turnCount.current = 0;
  }, []);

  return {
    messages,
    isStreaming,
    steps,
    sessionId,
    error,
    currentDecision,
    turnCount: turnCount.current,
    phase,
    customerCandidates,
    orderCandidates,
    refundMethodCandidates,
    sendMessage,
    selectCustomer,
    selectOrder,
    selectRefundMethod,
    cancelStream,
    clearSession,
  };
}
