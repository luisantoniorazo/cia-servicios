import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { Toaster } from "./components/ui/sonner";
import "@/App.css";

// Pages
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import SuperAdmin from "./pages/SuperAdmin";
import Projects from "./pages/Projects";
import CRM from "./pages/CRM";
import Quotes from "./pages/Quotes";
import Invoices from "./pages/Invoices";
import Purchases from "./pages/Purchases";
import Suppliers from "./pages/Suppliers";
import Documents from "./pages/Documents";
import FieldReports from "./pages/FieldReports";
import KPIs from "./pages/KPIs";
import Intelligence from "./pages/Intelligence";
import Settings from "./pages/Settings";

// Layout
import MainLayout from "./components/Layout/MainLayout";

// Protected Route Component
const ProtectedRoute = ({ children, requireSuperAdmin = false }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-muted-foreground">Cargando...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (requireSuperAdmin && user.role !== "super_admin") {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
};

// Public Route Component (redirect if logged in)
const PublicRoute = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-muted-foreground">Cargando...</p>
        </div>
      </div>
    );
  }

  if (user) {
    return <Navigate to={user.role === "super_admin" ? "/super-admin" : "/dashboard"} replace />;
  }

  return children;
};

function AppRoutes() {
  return (
    <Routes>
      {/* Public Routes */}
      <Route
        path="/login"
        element={
          <PublicRoute>
            <Login />
          </PublicRoute>
        }
      />

      {/* Protected Routes */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <MainLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="projects" element={<Projects />} />
        <Route path="crm" element={<CRM />} />
        <Route path="quotes" element={<Quotes />} />
        <Route path="invoices" element={<Invoices />} />
        <Route path="purchases" element={<Purchases />} />
        <Route path="suppliers" element={<Suppliers />} />
        <Route path="documents" element={<Documents />} />
        <Route path="field-reports" element={<FieldReports />} />
        <Route path="kpis" element={<KPIs />} />
        <Route path="intelligence" element={<Intelligence />} />
        <Route path="settings" element={<Settings />} />
        <Route
          path="super-admin"
          element={
            <ProtectedRoute requireSuperAdmin>
              <SuperAdmin />
            </ProtectedRoute>
          }
        />
      </Route>

      {/* Catch all */}
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
        <Toaster position="top-right" richColors />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
