import { TicketStatus } from "../types/ticket";

const CONFIG: Record<TicketStatus, { label: string; cls: string }> = {
  open: { label: "Open", cls: "badge-open" },
  in_progress: { label: "In Progress", cls: "badge-in-progress" },
  resolved: { label: "Resolved", cls: "badge-resolved" },
};

export function StatusBadge({ status }: { status: TicketStatus }) {
  const { label, cls } = CONFIG[status] ?? { label: status, cls: "badge-open" };
  return <span className={`badge ${cls}`}>{label}</span>;
}
