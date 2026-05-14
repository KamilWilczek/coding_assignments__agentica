export type TicketStatus = "open" | "in_progress" | "resolved";

export interface Ticket {
  id: number;
  title: string;
  description: string;
  status: TicketStatus;
  created_at: string;
  updated_at: string;
}
