import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchTickets } from "../api/tickets";
import { Ticket, TicketStatus } from "../types/ticket";
import { StatusBadge } from "./StatusBadge";

const FILTERS = [
  { value: "", label: "All" },
  { value: "open", label: "Open" },
  { value: "in_progress", label: "In Progress" },
  { value: "resolved", label: "Resolved" },
];

export function TicketList() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [filter, setFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    fetchTickets(filter || undefined)
      .then(setTickets)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [filter]);

  return (
    <div className="list-page">
      <div className="list-header">
        <div>
          <h1 className="page-title">Tickets</h1>
          <p className="page-subtitle">
            {loading ? "Loading…" : `${tickets.length} ticket${tickets.length !== 1 ? "s" : ""}`}
          </p>
        </div>
        <div className="filter-group">
          {FILTERS.map((f) => (
            <button
              key={f.value}
              className={`filter-btn${filter === f.value ? " active" : ""}`}
              onClick={() => setFilter(f.value)}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {!loading && !error && tickets.length === 0 && (
        <div className="empty-state">No tickets match this filter.</div>
      )}

      <div className="ticket-grid">
        {tickets.map((ticket) => (
          <Link key={ticket.id} to={`/tickets/${ticket.id}`} className="ticket-card">
            <div className="card-top">
              <span className="ticket-num">#{ticket.id}</span>
              <StatusBadge status={ticket.status as TicketStatus} />
            </div>
            <h3 className="card-title">{ticket.title}</h3>
            <p className="card-preview">
              {ticket.description.length > 120
                ? ticket.description.slice(0, 120) + "…"
                : ticket.description}
            </p>
            <span className="card-date">
              {new Date(ticket.created_at).toLocaleDateString("en-GB", {
                day: "numeric",
                month: "short",
                year: "numeric",
              })}
            </span>
          </Link>
        ))}
      </div>
    </div>
  );
}
