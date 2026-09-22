// app/src/hooks/useDaemonSocket.ts
// WebSocket connection to the local Python daemon on ws://127.0.0.1:8420/ws

import { useEffect, useRef, useCallback, useState } from "react";

export type SynapseState = "IDLE" | "CAPTURING" | "REASONING" | "READY" | "SUPPRESSED";

export interface SynapseCard {
  trigger: string;
  response: string;
  model_used: "nano" | "ultra";
  latency_ms: number;
  active_app: string;
  memory_used: boolean;
  tavily: {
    query: string;
    saved_path: string;
    sources: { title: string; url: string }[];
  } | null;
  usage: {
    total_tokens: number;
    nano_calls: number;
    ultra_calls: number;
    estimated_spend_usd: number;
    budget_remaining_usd: number;
  };
}

interface DaemonMessageBase {
  type: "state_change" | "synapse_card" | "synapse_chunk";
}

interface StateChangeMessage extends DaemonMessageBase {
  type: "state_change";
  state: SynapseState;
  elapsed_s?: number;
}

interface SynapseCardMessage extends DaemonMessageBase {
  type: "synapse_card";
  trigger: string;
  response: string;
  model_used: "nano" | "ultra";
  latency_ms: number;
  active_app: string;
  memory_used: boolean;
  tavily: SynapseCard["tavily"];
  usage: SynapseCard["usage"];
}

type DaemonMessage = StateChangeMessage | SynapseCardMessage | SynapseChunkMessage;

interface SynapseChunkMessage extends DaemonMessageBase {
  type: "synapse_chunk";
  trigger: string;
  delta: string;
}

const WS_URL = import.meta.env.VITE_DAEMON_WS_URL ?? "ws://127.0.0.1:8420/ws";
const HTTP_URL = import.meta.env.VITE_DAEMON_HTTP_URL ?? "http://127.0.0.1:8420";
const BASE_RECONNECT_DELAY_MS = 2000;
const MAX_RECONNECT_DELAY_MS = 30_000;
const HEARTBEAT_INTERVAL_MS = 20_000;

export type ConnectionStatus = "disconnected" | "connecting" | "connected";

export interface UseDaemonSocketOptions {
  onCard?: (card: SynapseCard) => void;
  onChunk?: (delta: string, trigger: string) => void;
  onStateChange?: (state: SynapseState) => void;
  onConnectionChange?: (status: ConnectionStatus) => void;
}

export interface StoreMemoryPayload {
  app_context: string;
  problem: string;
  resolution: string;
  extensions?: string[];
}

export interface UseDaemonSocketReturn {
  status: ConnectionStatus;
  daemonState: SynapseState;
  streaming: string;
  invoke: (query: string, signal?: AbortSignal) => Promise<void>;
  dismiss: (signal?: AbortSignal) => Promise<void>;
  applyFix: (patch: string, signal?: AbortSignal) => Promise<void>;
  storeMemory: (payload: StoreMemoryPayload, signal?: AbortSignal) => Promise<void>;
}

function isSynapseChunkMessage(msg: DaemonMessage): msg is SynapseChunkMessage {
  return msg.type === "synapse_chunk";
}

function isStateChangeMessage(msg: DaemonMessage): msg is StateChangeMessage {
  return msg.type === "state_change";
}

function isSynapseCardMessage(msg: DaemonMessage): msg is SynapseCardMessage {
  return msg.type === "synapse_card";
}

function messageToCard(msg: SynapseCardMessage): SynapseCard {
  return {
    trigger: msg.trigger,
    response: msg.response,
    model_used: msg.model_used,
    latency_ms: msg.latency_ms,
    active_app: msg.active_app,
    memory_used: msg.memory_used,
    tavily: msg.tavily,
    usage: msg.usage,
  };
}

export function useDaemonSocket(opts: UseDaemonSocketOptions = {}): UseDaemonSocketReturn {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const heartbeatIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const reconnectAttemptRef = useRef(0);
  const mountedRef = useRef(true);
  const optsRef = useRef(opts);

  optsRef.current = opts;

  const [status, setStatus] = useState<ConnectionStatus>("disconnected");
  const [daemonState, setDaemonState] = useState<SynapseState>("IDLE");
  const [streaming, setStreaming] = useState<string>("");

  const clearReconnectTimeout = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
  }, []);

  const clearHeartbeat = useCallback(() => {
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
      heartbeatIntervalRef.current = null;
    }
  }, []);

  const cleanup = useCallback(() => {
    clearHeartbeat();
    clearReconnectTimeout();
    wsRef.current?.close();
    wsRef.current = null;
  }, [clearHeartbeat, clearReconnectTimeout]);

  const scheduleReconnect = useCallback(() => {
    if (!mountedRef.current) return;

    const delay = Math.min(
      BASE_RECONNECT_DELAY_MS * Math.pow(2, reconnectAttemptRef.current),
      MAX_RECONNECT_DELAY_MS
    );
    const jitter = Math.random() * 1000;
    const totalDelay = delay + jitter;

    reconnectTimeoutRef.current = setTimeout(() => {
      if (mountedRef.current) {
        reconnectAttemptRef.current += 1;
        connect();
      }
    }, totalDelay);
  }, []);

  const connect = useCallback(() => {
    if (!mountedRef.current) return;

    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => {
      if (!mountedRef.current) {
        ws.close();
        return;
      }
      reconnectAttemptRef.current = 0;
      setStatus("connected");

      heartbeatIntervalRef.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send("ping");
        } else {
          clearHeartbeat();
        }
      }, HEARTBEAT_INTERVAL_MS);
    };

    ws.onmessage = (event) => {
      try {
        const msg: DaemonMessage = JSON.parse(event.data);
        if (isStateChangeMessage(msg) && msg.state) {
          setDaemonState(msg.state);
          if (msg.state === "REASONING") setStreaming("");
          optsRef.current.onStateChange?.(msg.state);
        } else if (isSynapseChunkMessage(msg)) {
          setStreaming((prev) => prev + (msg.delta || ""));
          optsRef.current.onChunk?.(msg.delta || "", msg.trigger);
        } else if (isSynapseCardMessage(msg)) {
          setStreaming("");
          optsRef.current.onCard?.(messageToCard(msg));
        }
      } catch {
        // ignore malformed messages
      }
    };

    ws.onclose = () => {
      if (!mountedRef.current) return;
      setStatus("disconnected");
      clearHeartbeat();
      scheduleReconnect();
    };

    ws.onerror = () => {
      clearHeartbeat();
      ws.close();
    };
  }, [clearHeartbeat, scheduleReconnect]);

  useEffect(() => {
    mountedRef.current = true;
    setStatus("connecting");
    connect();

    return () => {
      mountedRef.current = false;
      cleanup();
    };
  }, [connect, cleanup]);

  const httpRequest = useCallback(
    async (endpoint: string, body: unknown, signal?: AbortSignal) => {
      const res = await fetch(`${HTTP_URL}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
        signal,
      });
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${await res.text()}`);
      }
    },
    []
  );

  const invoke = useCallback(
    async (query: string = "", signal?: AbortSignal) => {
      await httpRequest("/invoke", { query }, signal);
    },
    [httpRequest]
  );

  const dismiss = useCallback(
    async (signal?: AbortSignal) => {
      await httpRequest("/action/dismiss", {}, signal);
    },
    [httpRequest]
  );

  const applyFix = useCallback(
    async (patch: string, signal?: AbortSignal) => {
      await httpRequest("/action/apply-fix", { patch }, signal);
    },
    [httpRequest]
  );

  const storeMemory = useCallback(
    async (payload: StoreMemoryPayload, signal?: AbortSignal) => {
      await httpRequest("/action/store-memory", payload, signal);
    },
    [httpRequest]
  );

  return { status, daemonState, streaming, invoke, dismiss, applyFix, storeMemory };
}