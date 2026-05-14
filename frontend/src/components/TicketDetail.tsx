import { useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { fetchTicket } from "../api/tickets";
import { Ticket, TicketStatus } from "../types/ticket";
import { StatusBadge } from "./StatusBadge";

export function TicketDetail() {
  const { id } = useParams<{ id: string }>();

  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [summary, setSummary] = useState("");
  const [summaryStreaming, setSummaryStreaming] = useState(false);
  const [summaryError, setSummaryError] = useState<string | null>(null);
  const esRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    setError(null);
    fetchTicket(Number(id))
      .then(setTicket)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));

    return () => {
      esRef.current?.close();
    };
  }, [id]);

  const generateSummary = () => {
    if (!id || summaryStreaming) return;

    esRef.current?.close();
    setSummary("");
    setSummaryError(null);
    setSummaryStreaming(true);

    const es = new EventSource(`/api/tickets/${id}/summary`);
    esRef.current = es;

    es.onmessage = (event: MessageEvent) => {
      if (event.data === "[DONE]") {
        es.close();
        setSummaryStreaming(false);
        return;
      }
      try {
        const parsed = JSON.parse(event.data) as { content?: string; error?: string };
        if (parsed.error) {
          setSummaryError(parsed.error);
          setSummaryStreaming(false);
          es.close();
          return;
        }
        if (parsed.content) {
          setSummary((prev) => prev + parsed.content);
        }
      } catch {
        // non-JSON line from SSE — ignore
      }
    };

    es.onerror = () => {
      if (es.readyState === EventSource.CLOSED) return;
      setSummaryError("Connection lost. The LLM API may be unavailable — please try again.");
      setSummaryStreaming(false);
      es.close();
    };
  };

  if (loading) return <div className="loading-screen">Loading ticket…</div>;
  if (error) return <div className="alert alert-error full-page-error">{error}</div>;
  if (!ticket) return null;

  return (
    <div className="detail-page">
      <Link to="/" className="back-link">
        ← Back to tickets
      </Link>

      <div className="detail-card">
        <div className="detail-header">
          <div className="detail-title-row">
            <span className="ticket-num">#{ticket.id}</span>
            <h1 className="detail-title">{ticket.title}</h1>
          </div>
          <StatusBadge status={ticket.status as TicketStatus} />
        </div>

        <div className="detail-meta">
          <span>
            Created:{" "}
            {new Date(ticket.created_at).toLocaleString("en-GB", {
              dateStyle: "medium",
              timeStyle: "short",
            })}
          </span>
          <span>
            Updated:{" "}
            {new Date(ticket.updated_at).toLocaleString("en-GB", {
              dateStyle: "medium",
              timeStyle: "short",
            })}
          </span>
        </div>

        <section className="detail-section">
          <h2 className="section-title">Description</h2>
          <p className="description-text">{ticket.description}</p>
        </section>

        <section className="detail-section summary-section">
          <div className="summary-header">
            <h2 className="section-title">AI Summary</h2>
            <button
              className="generate-btn"
              onClick={generateSummary}
              disabled={summaryStreaming}
            >
              {summaryStreaming
                ? "Generating…"
                : summary
                ? "Regenerate"
                : "Generate Summary"}
            </button>
          </div>

          {summaryStreaming && !summary && (
            <div className="summary-placeholder">
              <span className="pulse-dot" />
              Connecting to AI…
            </div>
          )}

          {summaryError && (
            <div className="alert alert-error">{summaryError}</div>
          )}

          {summary && (
            <div className="summary-text">
              {summary}
              {summaryStreaming && <span className="cursor-blink">▋</span>}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
