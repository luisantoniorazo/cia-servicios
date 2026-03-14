import React, { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import { 
  Activity, 
  LogIn, 
  LogOut, 
  Plus, 
  Edit, 
  Trash2, 
  Eye, 
  Download, 
  Mail, 
  CreditCard,
  RefreshCw,
  Settings,
  Filter
} from "lucide-react";

const ACTIVITY_TYPES = [
  { value: "all", label: "Todas las actividades" },
  { value: "login", label: "Inicio de sesión" },
  { value: "create", label: "Creación" },
  { value: "update", label: "Actualización" },
  { value: "delete", label: "Eliminación" },
  { value: "export", label: "Exportación" },
  { value: "email", label: "Correo enviado" },
  { value: "subscription", label: "Suscripción" },
];

const MODULES = [
  { value: "all", label: "Todos los módulos" },
  { value: "auth", label: "Autenticación" },
  { value: "companies", label: "Empresas" },
  { value: "users", label: "Usuarios" },
  { value: "quotes", label: "Cotizaciones" },
  { value: "invoices", label: "Facturas" },
  { value: "projects", label: "Proyectos" },
  { value: "clients", label: "Clientes" },
  { value: "settings", label: "Configuración" },
];

const getActivityIcon = (type) => {
  switch (type) {
    case "login":
      return <LogIn className="h-4 w-4 text-emerald-500" />;
    case "logout":
      return <LogOut className="h-4 w-4 text-slate-500" />;
    case "create":
      return <Plus className="h-4 w-4 text-blue-500" />;
    case "update":
      return <Edit className="h-4 w-4 text-amber-500" />;
    case "delete":
      return <Trash2 className="h-4 w-4 text-red-500" />;
    case "view":
      return <Eye className="h-4 w-4 text-purple-500" />;
    case "export":
      return <Download className="h-4 w-4 text-cyan-500" />;
    case "email":
      return <Mail className="h-4 w-4 text-indigo-500" />;
    case "payment":
      return <CreditCard className="h-4 w-4 text-emerald-500" />;
    case "subscription":
      return <RefreshCw className="h-4 w-4 text-purple-500" />;
    default:
      return <Settings className="h-4 w-4 text-slate-500" />;
  }
};

export const ActivityLogs = ({ isSuperAdmin = false }) => {
  const { api } = useAuth();
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    activity_type: "all",
    module: "all",
    company_id: "",
  });
  const [companies, setCompanies] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const limit = 50;

  useEffect(() => {
    if (isSuperAdmin) {
      fetchCompanies();
    }
    fetchLogs();
  }, [filters, page]);

  const fetchCompanies = async () => {
    try {
      const response = await api.get("/super-admin/companies");
      setCompanies(response.data);
    } catch (error) {
      console.error("Error fetching companies:", error);
    }
  };

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.append("limit", limit);
      params.append("skip", page * limit);
      if (filters.activity_type !== "all") params.append("activity_type", filters.activity_type);
      if (filters.module !== "all") params.append("module", filters.module);
      if (filters.company_id) params.append("company_id", filters.company_id);

      const endpoint = isSuperAdmin ? "/super-admin/activity-logs" : "/activity-logs";
      const response = await api.get(`${endpoint}?${params.toString()}`);
      setLogs(response.data.logs || []);
      setTotal(response.data.total || 0);
    } catch (error) {
      console.error("Error fetching logs:", error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateStr) => {
    const date = new Date(dateStr);
    return date.toLocaleString("es-MX", {
      day: "numeric",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <div className="space-y-6 animate-fade-in" data-testid="activity-logs-page">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold font-[Chivo]">Historial de Actividad</h1>
          <p className="text-muted-foreground">
            {total} registros encontrados
          </p>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-wrap items-center gap-3">
            <Filter className="h-4 w-4 text-muted-foreground" />
            <Select
              value={filters.activity_type}
              onValueChange={(value) => {
                setFilters({ ...filters, activity_type: value });
                setPage(0);
              }}
            >
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Tipo de actividad" />
              </SelectTrigger>
              <SelectContent>
                {ACTIVITY_TYPES.map((type) => (
                  <SelectItem key={type.value} value={type.value}>
                    {type.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select
              value={filters.module}
              onValueChange={(value) => {
                setFilters({ ...filters, module: value });
                setPage(0);
              }}
            >
              <SelectTrigger className="w-[160px]">
                <SelectValue placeholder="Módulo" />
              </SelectTrigger>
              <SelectContent>
                {MODULES.map((mod) => (
                  <SelectItem key={mod.value} value={mod.value}>
                    {mod.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {isSuperAdmin && (
              <Select
                value={filters.company_id}
                onValueChange={(value) => {
                  setFilters({ ...filters, company_id: value });
                  setPage(0);
                }}
              >
                <SelectTrigger className="w-[200px]">
                  <SelectValue placeholder="Todas las empresas" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">Todas las empresas</SelectItem>
                  {companies.map((company) => (
                    <SelectItem key={company.id} value={company.id}>
                      {company.business_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}

            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setFilters({ activity_type: "all", module: "all", company_id: "" });
                setPage(0);
              }}
            >
              Limpiar filtros
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Logs List */}
      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
          ) : logs.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-64 text-muted-foreground">
              <Activity className="h-12 w-12 mb-4 opacity-50" />
              <p>No hay actividad registrada</p>
            </div>
          ) : (
            <div className="divide-y">
              {logs.map((log) => (
                <div key={log.id} className="p-4 hover:bg-slate-50 transition-colors">
                  <div className="flex items-start gap-3">
                    <div className="mt-0.5 p-2 bg-slate-100 rounded-full">
                      {getActivityIcon(log.activity_type)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <p className="font-medium text-sm">{log.action}</p>
                        <Badge variant="outline" className="text-xs capitalize">
                          {log.module}
                        </Badge>
                      </div>
                      <div className="flex flex-wrap items-center gap-2 mt-1 text-xs text-muted-foreground">
                        {log.user_email && (
                          <span>{log.user_name || log.user_email}</span>
                        )}
                        {isSuperAdmin && log.company_id && (
                          <Badge variant="secondary" className="text-xs">
                            {companies.find(c => c.id === log.company_id)?.business_name || "Empresa"}
                          </Badge>
                        )}
                        <span>•</span>
                        <span>{formatDate(log.created_at)}</span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Pagination */}
      {total > limit && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            Mostrando {page * limit + 1} - {Math.min((page + 1) * limit, total)} de {total}
          </p>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage(p => Math.max(0, p - 1))}
              disabled={page === 0}
            >
              Anterior
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage(p => p + 1)}
              disabled={(page + 1) * limit >= total}
            >
              Siguiente
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ActivityLogs;
