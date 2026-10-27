import { useState, useRef, useEffect } from "react";
import { chatWithReadingAI } from "../../services/readings";
import { Button, Spinner } from "@/components/ui";
import { ChatIcon, CloseIcon, SendIcon, SparkleIcon } from "@/components/icons";

export default function ChatBot({ readingId, readingType, result, position = "fixed" }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [open, setOpen] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend(e) {
    e.preventDefault();
    const text = input.trim();
    if (!text || !readingId || loading) return;

    const userMsg = { role: "user", content: text, timestamp: new Date().toISOString() };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);
    setError(null);

    try {
      const data = await chatWithReadingAI(readingId, readingType, text, messages);
      const assistantMsg = { role: "assistant", content: data.answer, timestamp: data.metadata?.timestamp || new Date().toISOString() };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      setError(err.message || "Chat failed. Please try again.");
      const errMsg = { role: "assistant", content: "I'm sorry, I couldn't process your question right now.", timestamp: new Date().toISOString() };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setLoading(false);
    }
  }

  if (!result && messages.length === 0) {
    return null;
  }

  const positionClass = position === "fixed"
    ? "fixed bottom-6 right-6 z-50"
    : "relative";

  return (
    <div className={positionClass}>
      {/* Floating trigger button */}
      <button
        type="button"
        onClick={() => setOpen((prev) => !prev)}
        aria-label="Open AI chat"
        aria-expanded={open}
        className="flex h-14 w-14 cursor-pointer items-center justify-center rounded-full bg-primary-600 text-white shadow-lg shadow-primary-500/25 transition duration-200 hover:bg-primary-700 hover:shadow-xl active:scale-[0.98] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600"
      >
        <ChatIcon className="h-6 w-6" />
      </button>

      {/* Chat panel */}
      {open && (
        <div className="absolute bottom-16 right-0 w-80 max-w-[90vw] animate-fade-in overflow-hidden surface-panel shadow-float">
          {/* Header */}
          <div className="flex items-center justify-between bg-primary-600 px-4 py-3 text-white">
            <div className="flex items-center gap-2.5">
              <span className="flex h-7 w-7 items-center justify-center rounded-full bg-white/15">
                <SparkleIcon className="h-4 w-4" />
              </span>
              <span className="font-display text-sm font-semibold tracking-tight">AI Chat</span>
              {messages.length > 0 && (
                <span className="rounded-full bg-white/20 px-2 py-0.5 text-sm font-medium">
                  {messages.length}
                </span>
              )}
            </div>
            <button
              type="button"
              onClick={() => setOpen(false)}
              aria-label="Close AI chat"
              className="inline-flex h-7 w-7 cursor-pointer items-center justify-center rounded-full text-white/80 transition hover:bg-white/15 hover:text-white focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
            >
              <CloseIcon className="h-4 w-4" />
            </button>
          </div>

          {/* Messages */}
          <div className="max-h-80 space-y-3 overflow-y-auto bg-slate-50/60 p-4">
            {messages.length === 0 && (
              <div className="flex justify-start">
                <div className="max-w-[85%] rounded-2xl rounded-bl-md bg-slate-100 px-3.5 py-2 text-sm leading-relaxed text-slate-700">
                  I&apos;ve loaded this {readingType === "palm" ? "palm" : "tarot"} analysis for you.
                  Ask me anything about it — I&apos;ll answer based on the actual reading data.
                </div>
              </div>
            )}
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[85%] rounded-2xl px-3.5 py-2 text-sm leading-relaxed ${
                    msg.role === "user"
                      ? "rounded-br-md bg-primary-600 text-white"
                      : "rounded-bl-md bg-slate-100 text-slate-700"
                  }`}
                >
                  {msg.content}
                </div>
              </div>
            ))}
            {loading && <Spinner className="h-4 w-4" label="Thinking…" />}
            <div ref={bottomRef} />
          </div>

          {/* Input */}
          <form onSubmit={handleSend} className="flex items-center gap-2 border-t border-slate-100 bg-white p-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about this reading…"
              disabled={loading}
              className="h-10 flex-1 rounded-[10px] border border-slate-200 bg-white px-3.5 text-sm text-slate-800 placeholder:text-slate-500 transition focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 focus:outline-none disabled:opacity-50"
            />
            <Button
              type="submit"
              size="sm"
              icon={SendIcon}
              loading={loading}
              disabled={loading || !input.trim()}
            >
              Send
            </Button>
          </form>
        </div>
      )}
    </div>
  );
}
