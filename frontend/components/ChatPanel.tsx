"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api, type ChatConversation, type ChatMessage } from "@/lib/api";

interface ChatPanelProps {
  userId: string;
  role: "farmer" | "officer";
  farmId?: string;
  officerId?: string;
  scanId?: string;
  initialScanId?: string;
  diagnosis?: string;
  onClose?: () => void;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const mediaUrl = (value?: string | null): string | undefined => value ? (value.startsWith("/") ? `${API_URL}${value}` : value) : undefined;

export default function ChatPanel({ userId, role, farmId, officerId = "officer-1", scanId, initialScanId, diagnosis, onClose }: ChatPanelProps) {
  const [conversations, setConversations] = useState<ChatConversation[]>([]);
  const [active, setActive] = useState<ChatConversation | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [attachment, setAttachment] = useState<File | null>(null);
  const [typing, setTyping] = useState(false);
  const [connected, setConnected] = useState(false);
  const [busy, setBusy] = useState(false);
  const [correctedLabel, setCorrectedLabel] = useState("");
  const [error, setError] = useState<string | null>(null);
  const socketRef = useRef<WebSocket | null>(null);
  const reconnectRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  const refreshConversations = useCallback(async () => {
    try {
      setConversations(await api.listConversations(userId));
    } catch {
      // The panel remains usable when the backend is temporarily unavailable.
    }
  }, [userId]);

  const refreshMessages = useCallback(async () => {
    if (!active) return;
    try {
      const page = await api.getMessages(userId, active.id);
      setMessages((current) => {
        const merged = new Map([...current, ...page.items].map((item) => [item.id, item]));
        return Array.from(merged.values()).sort((a, b) => a.created_at.localeCompare(b.created_at));
      });
      await api.markChatRead(userId, active.id);
      setConversations((items) => items.map((item) => item.id === active.id ? { ...item, unread_count: 0 } : item));
    } catch {
      // Polling is deliberately best effort; the next interval retries.
    }
  }, [active, userId]);

  useEffect(() => {
    refreshConversations();
    const interval = window.setInterval(refreshConversations, 5000);
    return () => window.clearInterval(interval);
  }, [refreshConversations]);

  useEffect(() => {
    if (initialScanId) {
      const match = conversations.find((conversation) => conversation.scan_id === initialScanId);
      if (match) setActive(match);
    }
  }, [conversations, initialScanId]);

  useEffect(() => {
    if (!active) return;
    setMessages([]);
    refreshMessages();
    const interval = window.setInterval(refreshMessages, 4000);
    return () => window.clearInterval(interval);
  }, [active, refreshMessages]);

  useEffect(() => {
    if (!active) return;
    let stopped = false;
    const connect = () => {
      if (stopped) return;
      const socket = new WebSocket(api.chatWebSocketUrl(active.id, userId));
      socketRef.current = socket;
      socket.onopen = () => setConnected(true);
      socket.onclose = () => {
        setConnected(false);
        if (!stopped) reconnectRef.current = setTimeout(connect, 2000);
      };
      socket.onerror = () => socket.close();
      socket.onmessage = (event) => {
        const payload = JSON.parse(event.data) as { type: string; message?: ChatMessage; user_id?: string; is_typing?: boolean };
        if (payload.type === "message" && payload.message) {
          setMessages((current) => current.some((item) => item.id === payload.message?.id) ? current : [...current, payload.message!]);
        }
        if (payload.type === "typing" && payload.user_id !== userId) setTyping(Boolean(payload.is_typing));
      };
    };
    connect();
    return () => {
      stopped = true;
      if (reconnectRef.current) clearTimeout(reconnectRef.current);
      socketRef.current?.close();
      socketRef.current = null;
    };
  }, [active, userId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, typing]);

  async function startConversation() {
    if (!farmId) return;
    setBusy(true);
    try {
      const conversation = await api.createConversation(userId, { farm_id: farmId, officer_id: officerId, scan_id: scanId });
      setConversations((items) => [conversation, ...items.filter((item) => item.id !== conversation.id)]);
      setActive(conversation);
      setError(null);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to start chat");
    } finally {
      setBusy(false);
    }
  }

  async function send() {
    if (!active || (!draft.trim() && !attachment)) return;
    setBusy(true);
    try {
      let attachmentUrl: string | undefined;
      if (attachment) attachmentUrl = (await api.uploadChatAttachment(userId, attachment)).attachment_url;
      const message = await api.sendChatMessage(userId, active.id, { body: draft.trim(), attachment_url: attachmentUrl, lang: document.cookie.match(/(?:^|; )app_lang=([^;]+)/)?.[1] ?? "en" });
      setMessages((current) => current.some((item) => item.id === message.id) ? current : [...current, message]);
      setDraft("");
      setAttachment(null);
      setError(null);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to send message");
    } finally {
      setBusy(false);
    }
  }

  async function validateCase(verdict: "confirmed" | "corrected") {
    if (!active?.scan_id) return;
    const corrected = verdict === "corrected" ? correctedLabel.trim() : undefined;
    if (verdict === "corrected" && !corrected) return;
    setBusy(true);
    try {
      await api.submitValidation({ ai_result_id: active.scan_id, officer_id: userId, verdict, corrected_label: corrected });
    } finally {
      setBusy(false);
    }
  }

  function updateTyping(value: string) {
    setDraft(value);
    socketRef.current?.send(JSON.stringify({ type: "typing", is_typing: value.length > 0 }));
  }

  return (
    <section className="glass border border-emerald-500/30 rounded-2xl overflow-hidden flex flex-col md:flex-row min-h-[420px]">
      <aside className="md:w-64 border-b md:border-b-0 md:border-r border-white/10 p-3">
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-bold text-white">💬 Messages</h2>
          {onClose && <button onClick={onClose} className="text-slate-400 hover:text-white" aria-label="Close chat">✕</button>}
        </div>
        {farmId && role === "farmer" && (
          <button onClick={startConversation} disabled={busy} className="w-full mb-3 px-3 py-2 rounded-lg bg-emerald-500 text-slate-950 text-xs font-bold disabled:opacity-50">
            {scanId ? "Ask an officer about this scan" : "Start officer chat"}
          </button>
        )}
        <div className="space-y-1 max-h-72 overflow-y-auto">
          {conversations.map((conversation) => (
            <button key={conversation.id} onClick={() => setActive(conversation)} className={`w-full text-left p-3 rounded-lg ${active?.id === conversation.id ? "bg-emerald-500/20" : "hover:bg-white/5"}`}>
              <div className="flex justify-between gap-2 text-xs text-slate-300"><span>{role === "farmer" ? "Officer" : "Farmer"}</span>{conversation.unread_count > 0 && <b className="text-emerald-300">{conversation.unread_count}</b>}</div>
              <p className="text-[11px] text-slate-500 truncate">{conversation.last_message?.body || "New conversation"}</p>
            </button>
          ))}
          {conversations.length === 0 && <p className="text-xs text-slate-500 p-2">No conversations yet.</p>}
        </div>
      </aside>

      <div className="flex-1 flex flex-col min-w-0">
        {!active ? (
          <div className="flex-1 flex items-center justify-center p-6 text-center text-slate-400 text-sm">Select a conversation to start messaging.</div>
        ) : (
          <>
            <header className="p-4 border-b border-white/10 flex items-center justify-between">
              <div><h3 className="font-bold text-white">{role === "farmer" ? "Field Officer" : "Farmer Support"}</h3><p className="text-[11px] text-slate-500">{active.scan_label || diagnosis || (active.scan_id ? "Attached scan diagnosis" : "Agronomic support")}</p></div>
              <span className={`text-[10px] ${connected ? "text-emerald-400" : "text-amber-400"}`}>{connected ? "Live" : "Polling fallback"}</span>
            </header>
            {error && <p className="px-4 py-2 text-xs text-red-300 bg-red-500/10 border-b border-red-500/20">{error}</p>}
            {active.scan_id && (active.scan_image_url || active.heat_map_url) && <div className="p-3 border-b border-white/10 flex gap-2">
              {active.scan_image_url && <img src={mediaUrl(active.scan_image_url)} alt="Original scan" className="h-20 w-20 rounded-lg object-cover" />}
              {active.heat_map_url && <img src={mediaUrl(active.heat_map_url)} alt="Grad-CAM heatmap" className="h-20 w-20 rounded-lg object-cover" />}
              {role === "officer" && <div className="ml-auto flex flex-col gap-1">
                <div className="flex gap-1"><button onClick={() => validateCase("confirmed")} disabled={busy} className="px-2 py-1 rounded bg-emerald-500 text-slate-950 text-[10px] font-bold">Confirmed</button><button onClick={() => validateCase("corrected")} disabled={busy || !correctedLabel.trim()} className="px-2 py-1 rounded bg-amber-500 text-slate-950 text-[10px] font-bold">Corrected</button></div>
                <input value={correctedLabel} onChange={(event) => setCorrectedLabel(event.target.value)} placeholder="Corrected label" className="w-32 rounded bg-white/5 border border-white/10 px-2 py-1 text-[10px] text-white" />
              </div>}
            </div>}
            <div className="flex-1 p-4 space-y-2 overflow-y-auto max-h-72">
              {messages.map((message) => <div key={message.id} className={`flex ${message.sender_id === userId ? "justify-end" : "justify-start"}`}>
                <div className={`max-w-[80%] rounded-xl px-3 py-2 text-sm ${message.sender_id === userId ? "bg-emerald-500 text-slate-950" : "bg-white/10 text-slate-200"}`}>
                  {message.attachment_url && <img src={mediaUrl(message.attachment_url)} alt="Chat attachment" className="max-h-36 rounded-lg mb-2 object-contain" />}
                  {message.body && <p className="whitespace-pre-wrap break-words">{message.body}</p>}
                  <p className="text-[10px] opacity-60 mt-1 text-right">{new Date(message.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })} {message.sender_id === userId && (message.read_at ? "✓✓" : "✓")}</p>
                </div>
              </div>)}
              {typing && <p className="text-xs text-slate-500">The other participant is typing...</p>}
              <div ref={bottomRef} />
            </div>
            <div className="p-3 border-t border-white/10">
              {attachment && <p className="text-xs text-emerald-300 mb-2">Attached: {attachment.name}</p>}
              <div className="flex gap-2">
                <label className="cursor-pointer px-3 py-2 bg-white/5 rounded-lg text-slate-300" title="Attach image">📎<input type="file" accept="image/jpeg,image/png,image/webp" className="hidden" onChange={(event) => setAttachment(event.target.files?.[0] ?? null)} /></label>
                <input value={draft} onChange={(event) => updateTyping(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); send(); } }} placeholder="Write a message..." className="flex-1 min-w-0 rounded-lg bg-white/5 border border-white/10 px-3 text-sm text-white outline-none focus:border-emerald-500" />
                <button onClick={send} disabled={busy || (!draft.trim() && !attachment)} className="px-4 rounded-lg bg-emerald-500 text-slate-950 font-bold text-sm disabled:opacity-40">Send</button>
              </div>
            </div>
          </>
        )}
      </div>
    </section>
  );
}
