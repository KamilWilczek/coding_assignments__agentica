import { Ticket } from "../types/ticket";

const API_BASE = "/api";

export async function fetchTickets(status?: string): Promise<Ticket[]> {
  const url = status
    ? `${API_BASE}/tickets?status=${encodeURIComponent(status)}`
    : `${API_BASE}/tickets`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Failed to fetch tickets (${res.status})`);
  return res.json();
}

export async function fetchTicket(id: number): Promise<Ticket> {
  const res = await fetch(`${API_BASE}/tickets/${id}`);
  if (!res.ok) throw new Error(`Ticket not found (${res.status})`);
  return res.json();
}
