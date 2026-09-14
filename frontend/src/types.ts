/* ── TypeScript interfaces for the NovaMart app ──────────────────── */

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  decision?: string | null;
  confidence?: number | null;
  ruleApplied?: string | null;
  timestamp: Date;
  isStreaming?: boolean;
}

export interface SSEStepEvent {
  step: string;
  status: string;
  detail?: string;
  risk_score?: number;
  decision?: string;
  reason?: string;
  rules_evaluated?: RuleEvaluated[];
  confidence?: number;
  sections_retrieved?: number;
}

export interface SSETokenEvent {
  token: string;
}

export interface SSEDoneEvent {
  request_id: string | null;
  decision: string | null;
  session_id: string;
  confidence?: number | null;
  rule_applied?: string | null;
}

export interface RuleEvaluated {
  rule_id: string;
  rule_name: string;
  description: string;
  value_checked: unknown;
  triggered: boolean;
  outcome: string;
  weight: number;
}

export interface ReasoningStep {
  step: string;
  tool: string | null;
  input: Record<string, unknown>;
  output: Record<string, unknown>;
  timestamp: string;
  duration_ms: number;
}

export interface PolicyResult {
  decision: string;
  reason: string;
  rule_applied: string;
  confidence: number;
  days_since_delivery: number | null;
  amount: number;
  rules_evaluated: RuleEvaluated[];
  overrides_checked: string[];
  partial_refund_requested: boolean;
  policy_version: string;
}

export interface RefundLog {
  id: string;
  order_id: string;
  customer_id: string;
  customer_name: string | null;
  product_name: string | null;
  amount: number | null;
  request_date: string | null;
  decision: string;
  decision_reason: string | null;
  agent_reasoning: {
    reasoning_steps?: ReasoningStep[];
    policy_result?: PolicyResult;
    injection_result?: InjectionResult;
    original_request_id?: string;
  } | null;
  was_injection_attempt: boolean;
  is_replay: boolean;
  original_request_id: string | null;
  session_id: string | null;
  user_message: string | null;
  created_at: string | null;
}

export interface InjectionResult {
  risk_score: number;
  layer1_triggered: boolean;
  layer2_triggered: boolean;
  layer3_triggered: boolean;
  flagged_phrases: string[];
  action: string;
  reasoning: string;
}

export interface Customer {
  id: string;
  name: string;
  email: string;
  account_tier: string;
  created_at: string | null;
  orders: Order[];
}

export interface Order {
  id: string;
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

export interface SessionInfo {
  id: string;
  customer_id: string | null;
  customer_name: string | null;
  created_at: string | null;
  last_active: string | null;
  message_count: number;
}

export interface SessionDetail {
  session: SessionInfo;
  messages: ConversationMessageData[];
  refund_requests: RefundLog[];
}

export interface ConversationMessageData {
  id: string;
  session_id: string;
  role: string;
  content: string;
  created_at: string | null;
}

export interface Stats {
  total_requests: number;
  approved: number;
  denied: number;
  escalated: number;
  flagged: number;
  pending: number;
  approval_rate: number;
}

export interface StepEvent extends SSEStepEvent {
  receivedAt: Date;
  durationMs?: number;
}
