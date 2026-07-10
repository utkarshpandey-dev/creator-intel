"use client";

import { useRef, useState } from "react";
import { ArrowUp, Brain, Sparkles } from "lucide-react";

type Msg = { role: "user" | "assistant"; content: string };

const SUGGESTIONS = [
  "Why did my best video perform so well?",
  "What should I make next?",
  "What mistakes am I repeating?",
  "What does my audience complain about most?",
];

/** Three-dot "AI thinking" indicator. */
function Thinking() {
  return (
    <span className="inline-flex items-center gap-1 py-1">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="h-1.5 w-1.5 animate-pulse-dot rounded-full bg-brand-400"
          style={{ animationDelay: `${i * 0.18}s` }}
        />
      ))}
    </span>
  );
}

/** Chat-with-your-channel. Streams the assistant reply via the SSE proxy route. */
export function ChatPanel({ channelId }: { channelId: string }) {
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  async function send(text: string) {
    const question = text.trim();
    if (!question || busy) return;
    setInput("");
    setBusy(true);
    setMessages((m) => [...m, { role: "user", content: question }, { role: "assistant", content: "" }]);

    try {
      const res = await fetch(`/api/channels/${channelId}/chat`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ message: question }),
      });
      if (!res.ok || !res.body) throw new Error("chat failed");

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const events = buffer.split("\n\n");
        buffer = events.pop() ?? "";
        for (const evt of events) {
          const line = evt.replace(/^data: /, "").trim();
          if (!line) continue;
          try {
            const parsed = JSON.parse(line) as { delta?: string; done?: boolean };
            if (parsed.delta) {
              setMessages((m) => {
                const copy = [...m];
                copy[copy.length - 1] = {
                  role: "assistant",
                  content: copy[copy.length - 1].content + parsed.delta,
                };
                return copy;
              });
            }
          } catch {
            /* ignore keep-alive / partial frames */
          }
        }
        scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
      }
    } catch {
      setMessages((m) => {
        const copy = [...m];
        copy[copy.length - 1] = {
          role: "assistant",
          content: "Sorry — I couldn't reach the analysis service. Please try again.",
        };
        return copy;
      });
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex h-[500px] flex-col">
      {/* context strip */}
      <div className="mb-3 flex items-center gap-2 text-[11px] uppercase tracking-[0.14em] text-slate-500">
        <Brain size={13} className="text-brand-400" />
        Answers grounded in this channel&apos;s data &amp; memory
      </div>

      <div ref={scrollRef} className="flex-1 space-y-4 overflow-y-auto pr-1">
        {messages.length === 0 && (
          <div className="flex h-full flex-col items-center justify-center gap-5 text-center">
            <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-500 to-aiviolet text-white shadow-glow-sm">
              <Sparkles size={21} />
            </span>
            <p className="max-w-sm text-sm leading-relaxed text-slate-400">
              Ask anything about this channel. The AI answers from your real analytics,
              audience themes, and everything it remembers.
            </p>
            <div className="flex max-w-md flex-wrap justify-center gap-2">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => send(s)}
                  className="rounded-full border border-white/10 bg-white/[0.03] px-3.5 py-1.5 text-xs text-slate-300 transition hover:border-brand-400/40 hover:bg-brand-500/10 hover:text-brand-200"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m, i) => {
          const isUser = m.role === "user";
          const isStreaming = busy && i === messages.length - 1 && !isUser;
          return (
            <div key={i} className={`flex items-end gap-2.5 ${isUser ? "justify-end" : ""}`}>
              {!isUser && (
                <span className="mb-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-brand-500 to-aiviolet text-white">
                  <Sparkles size={13} />
                </span>
              )}
              <div
                className={
                  isUser
                    ? "max-w-[85%] rounded-2xl rounded-br-md bg-gradient-to-r from-brand-600 to-brand-500 px-4 py-2.5 text-sm text-white shadow-glow-sm"
                    : "max-w-[90%] whitespace-pre-wrap rounded-2xl rounded-bl-md border border-white/[0.07] bg-white/[0.04] px-4 py-2.5 text-sm leading-relaxed text-slate-200"
                }
              >
                {m.content ? (
                  <>
                    {m.content}
                    {isStreaming && (
                      <span className="ml-0.5 inline-block h-3.5 w-[2px] animate-pulse bg-brand-300 align-middle" />
                    )}
                  </>
                ) : isStreaming ? (
                  <Thinking />
                ) : (
                  ""
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* composer */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          send(input);
        }}
        className="mt-4 flex items-center gap-2 rounded-2xl border border-white/10 bg-white/[0.03] p-1.5 transition focus-within:border-brand-500/50 focus-within:shadow-glow-sm"
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about your channel…"
          disabled={busy}
          className="flex-1 bg-transparent px-3 py-2 text-sm text-slate-100 outline-none placeholder:text-slate-500 disabled:opacity-60"
        />
        <button
          type="submit"
          disabled={busy || !input.trim()}
          className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-r from-brand-600 to-brand-500 text-white transition hover:brightness-110 disabled:opacity-40"
          aria-label="Send"
        >
          <ArrowUp size={16} />
        </button>
      </form>
    </div>
  );
}
