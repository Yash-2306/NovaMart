import React, { useRef, useEffect, useState } from 'react';
import ChatMessage from './ChatMessage';
import { CustomerSelectionCard, OrderSelectionCard, RefundMethodSelectionCard } from './SelectionCards';
import { useChat } from '../hooks/useChat';
import type { StepEvent } from '../types';

interface ChatWindowProps {
  onStepsUpdate: (steps: StepEvent[]) => void;
  active?: boolean;
}

export default function ChatWindow({ onStepsUpdate, active = true }: ChatWindowProps) {
  const {
    messages,
    isStreaming,
    steps,
    sessionId,
    error,
    turnCount,
    phase,
    customerCandidates,
    orderCandidates,
    refundMethodCandidates,
    sendMessage,
    selectCustomer,
    selectOrder,
    selectRefundMethod,
    clearSession,
  } = useChat();
  const [input, setInput] = useState('');
  const [copied, setCopied] = useState(false);
  const [showReasoning, setShowReasoning] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Whether the user can type freely
  const canType = phase === 'idle' || phase === 'free_text';
  const isSelecting = phase === 'select_customer' || phase === 'select_order' || phase === 'select_refund_method';

  // Auto-scroll to latest
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, customerCandidates, orderCandidates, refundMethodCandidates]);

  // Forward steps to parent (admin dashboard)
  useEffect(() => {
    onStepsUpdate(steps);
  }, [steps, onStepsUpdate]);

  // Auto-focus input when tab becomes active, streaming ends, or transition to typing phase
  useEffect(() => {
    if (active && canType && !isStreaming && !isSelecting) {
      const timer = setTimeout(() => {
        inputRef.current?.focus();
      }, 50);
      return () => clearTimeout(timer);
    }
  }, [active, canType, isStreaming, isSelecting]);

  const handleSend = () => {
    if (!input.trim() || isStreaming || !canType) return;
    sendMessage(input);
    setInput('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const copySessionId = () => {
    navigator.clipboard.writeText(sessionId);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="flex flex-col h-full bg-slate-50/30 dark:bg-zinc-950/30 transition-colors relative">
      {/* Session header */}
      <div className="px-5 py-3 border-b border-slate-200 dark:border-zinc-800 flex items-center justify-between glass sticky top-0 z-10">
        <div className="flex items-center gap-3">
          <button
            onClick={copySessionId}
            className="flex items-center gap-1.5 text-xs text-slate-500 dark:text-zinc-400 hover:text-slate-800 dark:hover:text-zinc-200 transition-colors font-mono bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 px-2.5 py-1 rounded"
            title="Click to copy session ID"
          >
            <svg className="w-3 h-3 text-slate-400 dark:text-zinc-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 7.5V6.108c0-1.135.845-2.098 1.976-2.192.373-.03.748-.057 1.123-.08M15.75 18H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08M15.75 18.75v-1.875a3.375 3.375 0 00-3.375-3.375h-1.5a1.125 1.125 0 01-1.125-1.125v-1.5A3.375 3.375 0 006.375 7.5H5.25m11.9-3.664A2.251 2.251 0 0015 2.25h-1.5a2.251 2.251 0 00-2.15 1.586m5.8 0c.065.21.1.433.1.664v.75h-6V4.5c0-.231.035-.454.1-.664M6.75 7.5H4.875c-.621 0-1.125.504-1.125 1.125v12c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V16.5a9 9 0 00-9-9z" />
            </svg>
            <span>{copied ? '✓ Copied' : `Session: ${sessionId.slice(8, 20)}...`}</span>
          </button>
          {turnCount > 0 && (
            <span className="text-[11px] text-slate-500 dark:text-zinc-400 bg-slate-100 dark:bg-zinc-900 px-2 py-0.5 rounded border border-slate-200/50 dark:border-zinc-800/50 font-mono">
              Turn {turnCount}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowReasoning(!showReasoning)}
            className={`text-xs px-3 py-1.5 rounded border transition-all flex items-center gap-1.5 ${
              showReasoning 
                ? 'bg-slate-100 dark:bg-zinc-800 border-slate-300 dark:border-zinc-700 text-slate-800 dark:text-zinc-100 font-semibold' 
                : 'bg-white dark:bg-zinc-900 border-slate-200 dark:border-zinc-800 text-slate-600 dark:text-zinc-400 hover:text-slate-800 dark:hover:text-zinc-200 hover:bg-slate-50 dark:hover:bg-zinc-850'
            }`}
          >
            <span className={`w-1.5 h-1.5 rounded-full ${showReasoning ? 'bg-slate-700 dark:bg-zinc-300 animate-pulse' : 'bg-slate-400 dark:bg-zinc-600'}`} />
            <span>Reasoning Trace</span>
          </button>
          <button
            onClick={clearSession}
            className="text-xs px-3 py-1.5 rounded bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 text-slate-500 dark:text-zinc-400 hover:text-red-650 hover:border-red-200 dark:hover:border-red-900 hover:bg-red-50/50 dark:hover:bg-red-950/20 transition-colors"
          >
            Clear Session
          </button>
        </div>
      </div>

      {/* Reasoning Panel */}
      {showReasoning && steps.length > 0 && (
        <div className="px-5 py-3.5 bg-slate-50 dark:bg-zinc-900/60 border-b border-slate-200 dark:border-zinc-800 font-mono text-[11px] overflow-y-auto max-h-48">
          <div className="flex items-center justify-between mb-2">
            <span className="text-slate-400 dark:text-zinc-500 font-semibold uppercase text-[10px] tracking-wider">Evaluation Steps</span>
            <span className="text-[10px] text-slate-400 dark:text-zinc-500 font-medium font-sans">Trace logs</span>
          </div>
          <div className="space-y-1.5">
            {steps.map((step, idx) => (
              <div key={idx} className="flex gap-2 text-slate-600 dark:text-zinc-400 border-l-2 border-slate-200 dark:border-zinc-800 pl-3 ml-1">
                <span className="text-slate-800 dark:text-zinc-200 font-semibold">{step.step}</span>
                <span>
                  {step.status === 'failed' ? (
                    <span className="text-red-500 dark:text-red-400">Failed: {step.detail}</span>
                  ) : step.decision ? (
                    <span className="text-emerald-600 dark:text-emerald-400 font-semibold">Decision: {step.decision}</span>
                  ) : (
                    <span className="text-slate-500 dark:text-zinc-500">{step.detail || 'Running...'}</span>
                  )}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto px-5 py-6 space-y-5 bg-transparent relative z-0">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center max-w-md mx-auto py-12">
            <div className="w-12 h-12 rounded-xl bg-slate-900 dark:bg-zinc-100 flex items-center justify-center mb-6 shadow-sm">
              <svg className="w-6 h-6 text-white dark:text-black" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
            </div>
            <h3 className="text-lg font-bold text-slate-900 dark:text-white tracking-tight mb-2">
              Customer Refund Support
            </h3>
            <p className="text-xs text-slate-500 dark:text-zinc-400 leading-relaxed mb-6 font-normal">
              Our automated system processes customer store refunds based on official merchant policies. Please state your name and details of the item return request.
            </p>
            <div className="w-full space-y-2">
              <div className="flex flex-col gap-2">
                {[
                  "Hi, I'm James Okafor. I'd like a refund.",
                  "My name is Priya Sharma. I need to return my desk.",
                  "I'm David Kim. Can I return my jacket?",
                ].map((suggestion) => (
                  <button
                    key={suggestion}
                    onClick={() => {
                      setInput(suggestion);
                      // Focus input box immediately after suggestion selection
                      inputRef.current?.focus();
                    }}
                    className="suggestion-chip w-full flex items-center justify-between text-left bg-white dark:bg-zinc-900 border-slate-200 dark:border-zinc-800 text-slate-650 dark:text-zinc-350"
                  >
                    <span>{suggestion}</span>
                    <svg className="w-3.5 h-3.5 opacity-30 hover:opacity-100 transition-opacity" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <ChatMessage key={msg.id} message={msg} />
        ))}

        {/* Customer selection cards */}
        {phase === 'select_customer' && customerCandidates.length > 0 && (
          <CustomerSelectionCard
            candidates={customerCandidates}
            onSelect={selectCustomer}
            disabled={isStreaming}
          />
        )}

        {/* Order selection cards */}
        {phase === 'select_order' && orderCandidates.length > 0 && (
          <OrderSelectionCard
            orders={orderCandidates}
            onSelect={selectOrder}
            disabled={isStreaming}
          />
        )}

        {/* Refund Method selection cards */}
        {phase === 'select_refund_method' && refundMethodCandidates.length > 0 && (
          <RefundMethodSelectionCard
            methods={refundMethodCandidates}
            onSelect={selectRefundMethod}
            disabled={isStreaming}
          />
        )}

        {isStreaming && messages[messages.length - 1]?.content === '' && (
          <div className="flex w-full gap-3 justify-start animate-fade-in">
            <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-slate-100 dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 flex items-center justify-center shadow-sm">
              <span className="w-1.5 h-1.5 rounded-full bg-slate-500 dark:bg-zinc-450 animate-ping" />
            </div>
            <div className="bubble-agent px-4 py-3 flex items-center gap-1 bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800">
              <div className="typing-dot" />
              <div className="typing-dot" />
              <div className="typing-dot" />
            </div>
          </div>
        )}

        {/* Error banner */}
        {error && (
          <div className="mx-auto max-w-md px-4 py-3 rounded-lg bg-red-50 dark:bg-red-950/20 border border-red-100 dark:border-red-900/30 text-red-700 dark:text-red-400 text-xs font-semibold flex items-center gap-2">
            <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <span>{error}</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input bar — dynamic based on phase */}
      <div className="p-4 glass border-t border-slate-200 dark:border-zinc-800 transition-colors relative z-10">
        {isSelecting ? (
          /* Selection mode: show a disabled prompt */
          <div className="flex items-center justify-center gap-2 max-w-3xl mx-auto py-1.5">
            <div className="w-2 h-2 rounded-full bg-indigo-400 dark:bg-indigo-500 animate-pulse" />
            <span className="text-xs font-medium text-slate-500 dark:text-zinc-400">
              {phase === 'select_customer'
                ? 'Select your account above to continue'
                : phase === 'select_order'
                ? 'Select the order you want to return above'
                : 'Select your preferred refund method above'}
            </span>
          </div>
        ) : (
          /* Normal text input */
          <div className="relative flex items-end gap-2.5 max-w-3xl mx-auto">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isStreaming || !canType}
              placeholder={
                isStreaming
                  ? 'Processing customer ticket data...'
                  : 'Enter message or request details...'
              }
              rows={1}
              className="chat-input flex-1 min-h-[42px] bg-slate-50 dark:bg-zinc-900 border-slate-200 dark:border-zinc-800 text-slate-800 dark:text-zinc-200"
              style={{ maxHeight: '120px' }}
              onInput={(e) => {
                const target = e.target as HTMLTextAreaElement;
                target.style.height = 'auto';
                target.style.height = Math.min(target.scrollHeight, 120) + 'px';
              }}
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || isStreaming || !canType}
              className="send-btn bg-slate-900 dark:bg-zinc-100 hover:bg-slate-800 dark:hover:bg-white text-white dark:text-black transition-colors"
            >
              {isStreaming ? (
                <span className="w-4 h-4 border-2 border-slate-300 dark:border-zinc-650 border-t-white dark:border-t-black rounded-full animate-spin" />
              ) : (
                <svg className="w-4 h-4 transform rotate-45 -translate-x-[1px]" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
                </svg>
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
