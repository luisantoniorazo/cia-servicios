import React from "react";
import { BrowserRouter, Routes, Route, Navigate, useParams } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { Toaster } from "./components/ui/sonner";
import "./App.css";

// Auth Pages
import SuperAdminLogin from "./pages/SuperAdminLogin";
import SuperAdminDashboard from "./pages/SuperAdminDashboard";
import CompanyLogin from "./pages/CompanyLogin";

// Company Pages
import Dashboard from "./pages/Dashboard";
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

// Loading Component
const LoadingScreen = () => (
  <div className="min-h-screen flex items-center justify-center bg-slate-50">
    <div className="text-center">
      <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4" />
      <p className="text-muted-foreground">Cargando...</p>
    </div>
  </div>
);

// Super Admin Protected Route
const SuperAdminRoute = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) return <LoadingScreen />;

  if (!user || user.role !== "super_admin") {
    return <Navigate to="/admin-portal" replace />;
  }

  return children;
};

// Company Protected Route
const CompanyRoute = ({ children }) => {
  const { user, loading, companySlug } = useAuth();
  const { slug } = useParams();

  if (loading) return <LoadingScreen />;

  if (!user) {
    return <Navigate to={`/empresa/${slug}/login`} replace />;
  }

  if (user.role === "super_admin") {
    return <Navigate to="/admin-portal/dashboard" replace />;
  }

  if (companySlug && companySlug !== slug) {
    return <Navigate to={`/empresa/${companySlug}/login`} replace />;
  }

  return children;
};

// Public Route for Super Admin
const PublicSuperAdminRoute = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) return <LoadingScreen />;

  if (user && user.role === "super_admin") {
    return <Navigate to="/admin-portal/dashboard" replace />;
  }

  return children;
};

// Public Route for Company
const PublicCompanyRoute = ({ children }) => {
  const { user, loading, companySlug } = useAuth();
  const { slug } = useParams();

  if (loading) return <LoadingScreen />;

  if (user && user.role !== "super_admin" && companySlug === slug) {
    return <Navigate to={`/empresa/${slug}/dashboard`} replace />;
  }

  return children;
};

// Home Page - Redirect to appropriate login
const HomePage = () => {
  const { user, loading, companySlug, isSuperAdmin } = useAuth();

  if (loading) return <LoadingScreen />;

  if (user) {
    if (isSuperAdmin()) {
      return <Navigate to="/admin-portal/dashboard" replace />;
    }
    if (companySlug) {
      return <Navigate to={`/empresa/${companySlug}/dashboard`} replace />;
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-100 to-slate-200 flex items-center justify-center p-4">
      <div className="text-center max-w-md">
        <img
          src="https://customer-assets.emergentagent.com/job_cia-operacional/artifacts/0bkwa552_Logo%20CIA.jpg"
          alt="CIA Servicios"
          className="h-24 w-auto mx-auto mb-6"
        />
        <h1 className="text-3xl font-bold text-slate-900 font-[Chivo] mb-2">CIA SERVICIOS</h1>
        <p className="text-slate-600 mb-8">Control Estratégico de Servicios y Proyectos</p>
        
        <div className="space-y-4">
          <a
            href="/admin-portal"
            className="block w-full py-3 px-4 bg-slate-800 text-white rounded-sm hover:bg-slate-700 transition-colors"
          >
            Portal Super Administrador
          </a>
          <p className="text-sm text-slate-500">
            Si eres usuario de una empresa, accede a través de la URL proporcionada por tu administrador.
          </p>
        </div>
      </div>
    </div>
  );
};

function AppRoutes() {
  return (
    <Routes>
      {/* Home */}
      <Route path="/" element={<HomePage />} />

      {/* Super Admin Portal */}
      <Route
        path="/admin-portal"
        element={
          <PublicSuperAdminRoute>
            <SuperAdminLogin />
          </PublicSuperAdminRoute>
        }
      />
      <Route
        path="/admin-portal/dashboard"
        element={
          <SuperAdminRoute>
            <SuperAdminDashboard />
          </SuperAdminRoute>
        }
      />

      {/* Company Login */}
      <Route
        path="/empresa/:slug/login"
        element={
          <PublicCompanyRoute>
            <CompanyLogin />
          </PublicCompanyRoute>
        }
      />

      {/* Company App Routes */}
      <Route
        path="/empresa/:slug"
        element={
          <CompanyRoute>
            <MainLayout />
          </CompanyRoute>
        }
      >
        <Route index element={<Navigate to="dashboard" replace />} />
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
      </Route>

      {/* Catch all */}
      <Route path="*" element={<Navigate to="/" replace />} />
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
