import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import "./App.css";



const AGENT_LABELS = { advisor: "Thesis Advisor", job_scout: "Job Scout" };

function Route({ steps }) {
  const path = ["Supervisor", ...steps.map((s) => AGENT_LABELS[s.agent] || s.agent)];
  const label = steps.length === 0 ? "Supervisor → answered directly" : path.join(" → ");
  const tasks = steps.map((s, i) => `${i + 1}. ${AGENT_LABELS[s.agent]}: ${s.task}`).join("\n");

  return (
    <div className="route" title={tasks || "The Supervisor replied without an agent"}>
      [{label}]
    </div>
  );
}


export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [threadId, setThreadId] = useState(null);
  const [program, setProgram] = useState(null);
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

 useEffect(() => {
  bottomRef.current?.scrollIntoView({ behavior: "smooth" });
 }, [messages, loading]);

  async function send(e) {
    e.preventDefault();
    const message = input.trim();
    if (!message || loading) return;

    setMessages((m) => [...m, { role: "user", content: message }]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, thread_id: threadId }),
      });
      
      if (!res.ok) throw new Error();

      const data = await res.json();
      setThreadId(data.thread_id);

      if (data.program) setProgram(data.program);

      setMessages((m) => [...m, { role: "bot", content: data.reply, steps: data.steps }]);

    } catch {
      setMessages((m) => [...m, { role: "bot", content: "Sorry, something went wrong. Please try again." }]);
    } finally {
      setLoading(false);
    }
  }

  function newChat() {
    setMessages([]);
    setThreadId(null);
    setProgram(null);
  }

  return (
    <div className="app">
      <header>
        <h1>ThesisMate</h1>
        <div>
          {program && <span className="badge">{program}</span>}
          <button className="secondary" onClick={newChat}>New chat</button>
        </div>
      </header>

      <main>
        {messages.length === 0 && (
          <p className="hint">Ask about thesis rules, deadlines, or find thesis positions in Sweden.</p>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`msg ${m.role}`}>
            {m.role === "bot" && m.steps && <Route steps={m.steps} />}
            <div className={`bubble ${m.role}`}>
              <ReactMarkdown components={{ a: (p) => <a {...p} target="_blank" rel="noreferrer" /> }}>
                {m.content}
              </ReactMarkdown>
            </div>
          </div>
        ))}
        {loading && <div className="bubble bot thinking">Thinking…</div>}
        <div ref={bottomRef} />
      </main>

      <form onSubmit={send}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask ThesisMate…"
          disabled={loading}
        />
        <button disabled={loading || !input.trim()}>Send</button>
      </form>
    </div>
  );
}