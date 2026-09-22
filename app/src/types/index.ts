// app/src/types/index.ts
// Shared TypeScript types for Synapse UI

export type SynapseState = "IDLE" | "CAPTURING" | "REASONING" | "READY" | "SUPPRESSED";

export interface TavilySource {
  title: string;
  url: string;
}

export interface TavilyData {
  query: string;
  saved_path: string;
  sources: TavilySource[];
}

export interface UsageData {
  total_tokens: number;
  nano_calls: number;
  ultra_calls: number;
  estimated_spend_usd: number;
  budget_remaining_usd: number;
}

export interface SynapseCard {
  trigger: string;
  response: string;
  model_used: "nano" | "ultra";
  latency_ms: number;
  active_app: string;
  memory_used: boolean;
  tavily: TavilyData | null;
  usage: UsageData;
}

export interface CardAction {
  id: "apply" | "save" | "search_more" | "dismiss";
  label: string;
  variant: "primary" | "ghost";
}
