import { Route, Routes } from "react-router-dom";
import AppLayout from "./components/AppLayout";
import Dashboard from "./pages/dashboard/Dashboard";
import CatalogoPage from "./pages/catalogo/CatalogoPage";
import ReservasPage from "./pages/reservas/ReservasPage";

export default function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<Dashboard />} />
        <Route path="/catalogo" element={<CatalogoPage />} />
        <Route path="/reservas" element={<ReservasPage />} />
      </Route>
    </Routes>
  );
}