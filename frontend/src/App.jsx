import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import LandingPage from "./pages/LandingPage";
import AuthPage from "./pages/AuthPage";
import AuthFreePage from "./pages/AuthFreePage";
import MainPricingAnalysisPage from "./pages/MainPricingAnalysisPage";
import ReportsPage from "./pages/ReportsPage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/"           element={<LandingPage />} />
        <Route path="/auth"       element={<AuthPage />} />
        <Route path="/auth-free"  element={<AuthFreePage />} />
        <Route path="/analysis"   element={<MainPricingAnalysisPage />} />
        <Route path="/reports"    element={<ReportsPage />} />

        {/* Legacy /dashboard URL — redirect silently */}
        <Route path="/dashboard"  element={<Navigate to="/reports" replace />} />

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
