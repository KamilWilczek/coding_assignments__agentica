import { BrowserRouter, Route, Routes } from "react-router-dom";
import { TicketDetail } from "./components/TicketDetail";
import { TicketList } from "./components/TicketList";

export default function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <header className="app-header">
          <div className="header-inner">
            <div className="header-brand">
              <span className="header-logo">HD</span>
              <span className="header-name">Help Desk</span>
            </div>
            <span className="header-tagline">Ticket Management System</span>
          </div>
        </header>

        <main className="app-main">
          <Routes>
            <Route path="/" element={<TicketList />} />
            <Route path="/tickets/:id" element={<TicketDetail />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
