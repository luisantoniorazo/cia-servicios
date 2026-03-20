import React, { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { formatCurrency, getStatusColor, getStatusLabel, getPhaseLabel } from "../lib/utils";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Progress } from "../components/ui/progress";
import { Badge } from "../components/ui/badge";
import { Skeleton } from "../components/ui/skeleton";
import { Button } from "../components/ui/button";
import { Checkbox } from "../components/ui/checkbox";
import { Label } from "../components/ui/label";
import { Input } from "../components/ui/input";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "../components/ui/sheet";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  Legend,
} from "recharts";
import {
  FolderKanban,
  DollarSign,
  Users,
  TrendingUp,
  CheckCircle,
  Clock,
  FileText,
  AlertTriangle,
  ArrowUpRight,
  ArrowDownRight,
  Settings2,
  GripVertical,
  Eye,
  EyeOff,
  TrendingDown,
  ShoppingCart,
  Download,
  Loader2,
  Sparkles,
  Calendar,
  Filter,
  RefreshCw,
} from "lucide-react";
import { toast } from "sonner";

const COLORS = ["#004e92", "#f59e0b", "#10b981", "#64748b", "#8b5cf6", "#ef4444"];

// Widget definitions for configurable dashboard
const WIDGET_DEFINITIONS = [
  { id: "main_stats", label: "KPIs Principales", description: "Proyectos, facturación, clientes, conversión", default: true },
  { id: "secondary_stats", label: "Estadísticas Secundarias", description: "Pipeline, cotizaciones, completados", default: true },
  { id: "profitability", label: "Rentabilidad", description: "Ventas vs Compras (Solo Admin)", default: true, adminOnly: true },
  { id: "project_progress", label: "Progreso de Proyectos", description: "Gráfico de barras de avance", default: true },
  { id: "quote_pipeline", label: "Pipeline de Cotizaciones", description: "Gráfico circular de estados", default: true },
  { id: "monthly_revenue", label: "Ingresos Mensuales", description: "Gráfico de líneas de facturación", default: true },
  { id: "overdue_invoices", label: "Facturas Vencidas", description: "Alertas de cobranza", default: true },
  { id: "pending_followups", label: "Seguimientos Pendientes", description: "Próximas actividades CRM", default: true },
  { id: "recent_activity", label: "Actividad Reciente", description: "Últimas acciones en el sistema", default: true },
];

const StatCard = ({ title, value, description, icon: Icon, trend, trendValue, color = "primary" }) => (
  <Card className="stat-card" data-testid={`stat-${title.toLowerCase().replace(/\s/g, "-")}`}>
    <CardHeader className="flex flex-row items-center justify-between pb-2 p-3 sm:p-6">
      <CardTitle className="text-xs sm:text-sm font-medium text-muted-foreground">{title}</CardTitle>
      <div className={`p-1.5 sm:p-2 rounded-sm bg-${color}/10`}>
        <Icon className={`h-4 w-4 sm:h-5 sm:w-5 text-${color === "primary" ? "[#004e92]" : color}`} />
      </div>
    </CardHeader>
    <CardContent className="p-3 sm:p-6 pt-0">
      <div className="text-xl sm:text-2xl lg:text-3xl font-bold font-[Chivo]">{value}</div>
      {description && <p className="text-xs sm:text-sm text-muted-foreground mt-1 hidden sm:block">{description}</p>}
      {trend && (
        <div className="flex items-center mt-1 sm:mt-2">
          {trend === "up" ? (
            <ArrowUpRight className="h-3 w-3 sm:h-4 sm:w-4 text-emerald-500" />
          ) : (
            <ArrowDownRight className="h-3 w-3 sm:h-4 sm:w-4 text-red-500" />
          )}
          <span className={`text-xs sm:text-sm ${trend === "up" ? "text-emerald-500" : "text-red-500"}`}>
            {trendValue}
          </span>
        </div>
      )}
    </CardContent>
  </Card>
);

export const Dashboard = () => {
  const { api, company, user } = useAuth();
  const [stats, setStats] = useState(null);
  const [projectProgress, setProjectProgress] = useState([]);
  const [monthlyRevenue, setMonthlyRevenue] = useState([]);
  const [quotePipeline, setQuotePipeline] = useState([]);
  const [overdueInvoices, setOverdueInvoices] = useState([]);
  const [pendingFollowups, setPendingFollowups] = useState([]);
  const [profitability, setProfitability] = useState(null);
  const [generatingReport, setGeneratingReport] = useState(false);
  const [profitDateRange, setProfitDateRange] = useState({ start_date: "", end_date: "" });
  const [loading, setLoading] = useState(true);
  const [configOpen, setConfigOpen] = useState(false);
  
  // Dashboard configuration - stored in localStorage
  const [widgetConfig, setWidgetConfig] = useState(() => {
    const saved = localStorage.getItem(`dashboard_config_${company?.id || 'default'}`);
    if (saved) {
      return JSON.parse(saved);
    }
    return WIDGET_DEFINITIONS.reduce((acc, w) => ({ ...acc, [w.id]: w.default }), {});
  });

  useEffect(() => {
    if (company?.id) {
      fetchDashboardData();
      // Load saved config for this company
      const saved = localStorage.getItem(`dashboard_config_${company.id}`);
      if (saved) {
        setWidgetConfig(JSON.parse(saved));
      }
    }
  }, [company]);

  const saveWidgetConfig = (config) => {
    setWidgetConfig(config);
    localStorage.setItem(`dashboard_config_${company?.id || 'default'}`, JSON.stringify(config));
    toast.success("Configuración guardada");
    setConfigOpen(false);
  };

  const toggleWidget = (widgetId) => {
    setWidgetConfig(prev => ({ ...prev, [widgetId]: !prev[widgetId] }));
  };

  const fetchDashboardData = async () => {
    try {
      const requests = [
        api.get(`/dashboard/stats?company_id=${company.id}`),
        api.get(`/dashboard/project-progress?company_id=${company.id}`),
        api.get(`/dashboard/monthly-revenue?company_id=${company.id}`),
        api.get(`/dashboard/quote-pipeline?company_id=${company.id}`),
        api.get(`/invoices/overdue?company_id=${company.id}`).catch(() => ({ data: { overdue: [], due_soon: [] } })),
        api.get(`/followups/pending?company_id=${company.id}`).catch(() => ({ data: [] })),
      ];
      
      // Only fetch profitability for admin users
      if (user?.role === "admin") {
        requests.push(api.get(`/analytics/profitability`).catch(() => ({ data: null })));
      }

      const [statsRes, progressRes, revenueRes, pipelineRes, overdueRes, followupsRes, profitabilityRes] = await Promise.all(requests);

      setStats(statsRes.data);
      setProjectProgress(progressRes.data);
      setMonthlyRevenue(revenueRes.data);
      setQuotePipeline(pipelineRes.data);
      setOverdueInvoices(overdueRes.data);
      setPendingFollowups(followupsRes.data);
      if (profitabilityRes) {
        setProfitability(profitabilityRes.data);
      }
    } catch (error) {
      toast.error("Error al cargar datos del dashboard");
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const generateExecutiveReport = async () => {
    if (!profitability) {
      toast.error("No hay datos de rentabilidad para generar el reporte");
      return;
    }
    setGeneratingReport(true);
    try {
      const response = await api.post("/analytics/executive-report-pdf", {
        profitability,
        stats,
        company_name: company.business_name,
        trade_name: company.trade_name || company.business_name,
        start_date: profitDateRange.start_date || null,
        end_date: profitDateRange.end_date || null,
      }, { responseType: 'blob' });
      
      // Create a downloadable PDF
      const blob = new Blob([response.data], { type: "application/pdf" });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `Reporte_Ejecutivo_${company.business_name.replace(/\s/g, "_")}_${new Date().toISOString().split("T")[0]}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      toast.success("Reporte ejecutivo PDF generado exitosamente");
    } catch (error) {
      toast.error("Error al generar reporte ejecutivo");
    } finally {
      setGeneratingReport(false);
    }
  };

  const fetchProfitabilityWithDates = async () => {
    if (user?.role !== "admin") return;
    try {
      let url = "/analytics/profitability";
      const params = new URLSearchParams();
      if (profitDateRange.start_date) params.append("start_date", profitDateRange.start_date);
      if (profitDateRange.end_date) params.append("end_date", profitDateRange.end_date);
      if (params.toString()) url += `?${params.toString()}`;
      
      const response = await api.get(url);
      setProfitability(response.data);
    } catch (error) {
      console.error("Error fetching profitability:", error);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6" data-testid="dashboard-loading">
        <Skeleton className="h-8 w-48" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Skeleton className="h-80" />
          <Skeleton className="h-80" />
        </div>
      </div>
    );
  }

  if (!company) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <AlertTriangle className="h-12 w-12 text-amber-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold">No hay empresa asignada</h2>
          <p className="text-muted-foreground">Contacta al administrador para asignarte una empresa.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4 sm:space-y-6 animate-fade-in" data-testid="dashboard">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 sm:gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl lg:text-3xl font-bold font-[Chivo] text-slate-900">Dashboard Estratégico</h1>
          <p className="text-sm sm:text-base text-muted-foreground">{company.business_name}</p>
        </div>
        <div className="flex items-center gap-2 sm:gap-3">
          <Badge variant="outline" className="w-fit text-xs sm:text-sm">
            {new Date().toLocaleDateString("es-MX")}
          </Badge>
          <Sheet open={configOpen} onOpenChange={setConfigOpen}>
            <SheetTrigger asChild>
              <Button variant="outline" size="sm" data-testid="dashboard-config-btn" className="text-xs sm:text-sm">
                <Settings2 className="h-3 w-3 sm:h-4 sm:w-4 mr-1 sm:mr-2" />
                <span className="hidden xs:inline">Configurar</span>
              </Button>
            </SheetTrigger>
            <SheetContent>
              <SheetHeader>
                <SheetTitle>Configurar Dashboard</SheetTitle>
                <SheetDescription>
                  Selecciona los widgets que deseas mostrar en tu dashboard
                </SheetDescription>
              </SheetHeader>
              <div className="space-y-4 py-6">
                {WIDGET_DEFINITIONS.map((widget) => (
                  <div key={widget.id} className="flex items-start space-x-3 p-3 rounded-lg hover:bg-slate-50 transition-colors">
                    <Checkbox
                      id={widget.id}
                      checked={widgetConfig[widget.id]}
                      onCheckedChange={() => toggleWidget(widget.id)}
                    />
                    <div className="flex-1">
                      <Label htmlFor={widget.id} className="font-medium cursor-pointer">
                        {widget.label}
                      </Label>
                      <p className="text-sm text-muted-foreground">{widget.description}</p>
                    </div>
                    {widgetConfig[widget.id] ? (
                      <Eye className="h-4 w-4 text-emerald-500" />
                    ) : (
                      <EyeOff className="h-4 w-4 text-slate-300" />
                    )}
                  </div>
                ))}
              </div>
              <div className="flex gap-2">
                <Button variant="outline" className="flex-1" onClick={() => setConfigOpen(false)}>
                  Cancelar
                </Button>
                <Button className="flex-1 btn-industrial" onClick={() => saveWidgetConfig(widgetConfig)}>
                  Guardar
                </Button>
              </div>
            </SheetContent>
          </Sheet>
        </div>
      </div>

      {/* Stats Grid */}
      {widgetConfig.main_stats && (
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-2 sm:gap-4">
        <StatCard
          title="Proyectos Activos"
          value={stats?.projects?.active || 0}
          description={`${stats?.projects?.total || 0} totales`}
          icon={FolderKanban}
          color="primary"
        />
        <StatCard
          title="Facturación Total"
          value={formatCurrency(stats?.financial?.total_invoiced || 0)}
          description={`${formatCurrency(stats?.financial?.total_collected || 0)} cobrado`}
          icon={DollarSign}
          color="emerald-500"
        />
        <StatCard
          title="Clientes Activos"
          value={stats?.clients?.total || 0}
          description={`${stats?.clients?.prospects || 0} prospectos`}
          icon={Users}
          color="blue-500"
        />
        <StatCard
          title="Tasa de Conversión"
          value={`${stats?.quotes?.conversion_rate || 0}%`}
          description={`${stats?.quotes?.authorized || 0} cotizaciones autorizadas`}
          icon={TrendingUp}
          color="amber-500"
        />
      </div>
      )}

      {/* Secondary Stats */}
      {widgetConfig.secondary_stats && (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="En Cotización"
          value={stats?.projects?.quotation || 0}
          icon={FileText}
          color="slate-500"
        />
        <StatCard
          title="Autorizados"
          value={stats?.projects?.authorized || 0}
          icon={CheckCircle}
          color="emerald-500"
        />
        <StatCard
          title="Completados"
          value={stats?.projects?.completed || 0}
          icon={CheckCircle}
          color="blue-500"
        />
        <StatCard
          title="Pipeline Comercial"
          value={formatCurrency(stats?.quotes?.pipeline_value || 0)}
          icon={TrendingUp}
          color="purple-500"
        />
      </div>
      )}

      {/* Profitability Widget - Only for Admin */}
      {widgetConfig.profitability && user?.role === "admin" && profitability && (
        <Card className="border-2 border-emerald-200 bg-gradient-to-r from-emerald-50 to-blue-50" data-testid="profitability-widget">
          <CardHeader className="p-4 sm:p-6 pb-2">
            <div className="flex flex-col gap-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="p-2 bg-emerald-100 rounded-lg">
                    <TrendingUp className="h-5 w-5 text-emerald-600" />
                  </div>
                  <div>
                    <CardTitle className="text-lg font-bold text-emerald-900">Rentabilidad</CardTitle>
                    <CardDescription className="text-xs">Análisis de Ventas vs Compras</CardDescription>
                  </div>
                </div>
                <Button
                  size="sm"
                  onClick={generateExecutiveReport}
                  disabled={generatingReport}
                  className="bg-emerald-600 hover:bg-emerald-700 gap-2"
                >
                  {generatingReport ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Generando PDF...
                    </>
                  ) : (
                    <>
                      <Download className="h-4 w-4" />
                      Reporte Ejecutivo PDF
                    </>
                  )}
                </Button>
              </div>
              {/* Date Filters */}
              <div className="flex flex-wrap items-center gap-3 p-3 bg-white/60 rounded-lg border border-emerald-100">
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-emerald-600" />
                  <span className="text-xs font-medium text-emerald-800">Período:</span>
                </div>
                <div className="flex items-center gap-2">
                  <Input
                    type="date"
                    value={profitDateRange.start_date}
                    onChange={(e) => setProfitDateRange(prev => ({ ...prev, start_date: e.target.value }))}
                    className="h-8 text-xs w-[130px]"
                    placeholder="Desde"
                  />
                  <span className="text-xs text-muted-foreground">a</span>
                  <Input
                    type="date"
                    value={profitDateRange.end_date}
                    onChange={(e) => setProfitDateRange(prev => ({ ...prev, end_date: e.target.value }))}
                    className="h-8 text-xs w-[130px]"
                    placeholder="Hasta"
                  />
                </div>
                <Button 
                  size="sm" 
                  variant="outline" 
                  onClick={fetchProfitabilityWithDates}
                  className="h-8 gap-1 text-xs"
                >
                  <Filter className="h-3 w-3" />
                  Filtrar
                </Button>
                {(profitDateRange.start_date || profitDateRange.end_date) && (
                  <Button 
                    size="sm" 
                    variant="ghost" 
                    onClick={() => {
                      setProfitDateRange({ start_date: "", end_date: "" });
                      fetchDashboardData();
                    }}
                    className="h-8 text-xs text-muted-foreground"
                  >
                    <RefreshCw className="h-3 w-3 mr-1" />
                    Limpiar
                  </Button>
                )}
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-4 sm:p-6 pt-2">
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="p-3 bg-white rounded-lg border shadow-sm">
                <div className="flex items-center gap-2 text-blue-600 mb-1">
                  <FileText className="h-4 w-4" />
                  <span className="text-xs font-medium">Facturado</span>
                </div>
                <p className="text-xl font-bold text-blue-700">
                  {formatCurrency(profitability?.sales?.total_invoiced || 0)}
                </p>
                <p className="text-[10px] text-muted-foreground">
                  {profitability?.sales?.invoices_count || 0} facturas
                </p>
              </div>
              <div className="p-3 bg-white rounded-lg border shadow-sm">
                <div className="flex items-center gap-2 text-green-600 mb-1">
                  <DollarSign className="h-4 w-4" />
                  <span className="text-xs font-medium">Cobrado</span>
                </div>
                <p className="text-xl font-bold text-green-700">
                  {formatCurrency(profitability?.sales?.total_collected || 0)}
                </p>
                <p className="text-[10px] text-muted-foreground">
                  Pendiente: {formatCurrency(profitability?.sales?.pending_collection || 0)}
                </p>
              </div>
              <div className="p-3 bg-white rounded-lg border shadow-sm">
                <div className="flex items-center gap-2 text-red-600 mb-1">
                  <ShoppingCart className="h-4 w-4" />
                  <span className="text-xs font-medium">Compras</span>
                </div>
                <p className="text-xl font-bold text-red-700">
                  {formatCurrency(profitability?.purchases?.total_purchases || 0)}
                </p>
                <p className="text-[10px] text-muted-foreground">
                  {profitability?.purchases?.purchase_orders_count || 0} órdenes
                </p>
              </div>
              <div className={`p-3 rounded-lg border shadow-sm ${(profitability?.profitability?.gross_profit || 0) >= 0 ? "bg-emerald-50 border-emerald-200" : "bg-orange-50 border-orange-200"}`}>
                <div className={`flex items-center gap-2 mb-1 ${(profitability?.profitability?.gross_profit || 0) >= 0 ? "text-emerald-600" : "text-orange-600"}`}>
                  {(profitability?.profitability?.gross_profit || 0) >= 0 ? (
                    <TrendingUp className="h-4 w-4" />
                  ) : (
                    <TrendingDown className="h-4 w-4" />
                  )}
                  <span className="text-xs font-medium">Utilidad Bruta</span>
                </div>
                <p className={`text-xl font-bold ${(profitability?.profitability?.gross_profit || 0) >= 0 ? "text-emerald-700" : "text-orange-700"}`}>
                  {formatCurrency(profitability?.profitability?.gross_profit || 0)}
                </p>
                <p className="text-[10px] text-muted-foreground">
                  Margen: {(profitability?.profitability?.profit_margin || 0).toFixed(1)}%
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
        {/* Monthly Revenue Chart */}
        {widgetConfig.monthly_revenue && (
        <Card className="chart-container" data-testid="monthly-revenue-chart">
          <CardHeader className="p-3 sm:p-6">
            <CardTitle className="flex items-center gap-2 text-sm sm:text-base">
              <DollarSign className="h-4 w-4 sm:h-5 sm:w-5 text-primary" />
              Facturación vs Cobranza
            </CardTitle>
            <CardDescription className="text-xs sm:text-sm">Últimos 12 meses</CardDescription>
          </CardHeader>
          <CardContent className="p-2 sm:p-6">
            <div className="h-48 sm:h-72">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={monthlyRevenue}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="month" tick={{ fontSize: 10 }} />
                  <YAxis tick={{ fontSize: 10 }} tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} />
                  <Tooltip
                    formatter={(value) => formatCurrency(value)}
                    contentStyle={{ borderRadius: "4px", border: "1px solid #e2e8f0" }}
                  />
                  <Legend wrapperStyle={{ fontSize: '12px' }} />
                  <Bar dataKey="invoiced" name="Facturado" fill="#004e92" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="collected" name="Cobrado" fill="#10b981" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
        )}

        {/* Quote Pipeline Chart */}
        {widgetConfig.quote_pipeline && (
        <Card className="chart-container" data-testid="quote-pipeline-chart">
          <CardHeader className="p-3 sm:p-6">
            <CardTitle className="flex items-center gap-2 text-sm sm:text-base">
              <FileText className="h-4 w-4 sm:h-5 sm:w-5 text-primary" />
              Pipeline de Cotizaciones
            </CardTitle>
            <CardDescription className="text-xs sm:text-sm">Estado actual por etapa</CardDescription>
          </CardHeader>
          <CardContent className="p-2 sm:p-6">
            <div className="h-48 sm:h-72">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={quotePipeline.filter((p) => p.count > 0)}
                    cx="50%"
                    cy="50%"
                    outerRadius={100}
                    dataKey="count"
                    nameKey="status"
                    label={({ status, count }) => `${getStatusLabel(status)}: ${count}`}
                    labelLine={false}
                  >
                    {quotePipeline.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(value, name) => [value, getStatusLabel(name)]}
                    contentStyle={{ borderRadius: "4px", border: "1px solid #e2e8f0" }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
        )}
      </div>

      {/* Project Progress */}
      {widgetConfig.project_progress && (
      <Card data-testid="project-progress-card">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FolderKanban className="h-5 w-5 text-primary" />
            Avance de Proyectos Activos
          </CardTitle>
          <CardDescription>Progreso por fase de cada proyecto</CardDescription>
        </CardHeader>
        <CardContent>
          {projectProgress.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No hay proyectos activos actualmente
            </div>
          ) : (
            <div className="space-y-6">
              {projectProgress.map((project) => (
                <div key={project.id} className="space-y-3 p-4 bg-slate-50 rounded-sm">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-semibold text-slate-900">{project.name}</h4>
                      <p className="text-sm text-muted-foreground">{project.client_name}</p>
                    </div>
                    <div className="text-right">
                      <span className="text-2xl font-bold text-primary">{project.total_progress}%</span>
                      <p className="text-sm text-muted-foreground">
                        {formatCurrency(project.contract_amount)}
                      </p>
                    </div>
                  </div>
                  <Progress value={project.total_progress} className="h-2" />
                  
                  {/* Profitability Section */}
                  <div className="grid grid-cols-3 gap-2 p-2 bg-white rounded border">
                    <div className="text-center">
                      <p className="text-xs text-muted-foreground">Compras</p>
                      <p className="text-sm font-semibold text-red-600">{formatCurrency(project.total_purchases || 0)}</p>
                      <p className="text-xs text-red-500">({project.purchases_count || 0} órdenes)</p>
                    </div>
                    <div className="text-center border-x">
                      <p className="text-xs text-muted-foreground">% Compras</p>
                      <p className={`text-sm font-bold ${(project.purchases_percentage || 0) > 70 ? 'text-red-600' : (project.purchases_percentage || 0) > 50 ? 'text-amber-600' : 'text-green-600'}`}>
                        {project.purchases_percentage || 0}%
                      </p>
                      <Progress 
                        value={Math.min(project.purchases_percentage || 0, 100)} 
                        className={`h-1 mt-1 ${(project.purchases_percentage || 0) > 70 ? '[&>div]:bg-red-500' : (project.purchases_percentage || 0) > 50 ? '[&>div]:bg-amber-500' : '[&>div]:bg-green-500'}`}
                      />
                    </div>
                    <div className="text-center">
                      <p className="text-xs text-muted-foreground">Margen</p>
                      <p className={`text-sm font-bold ${(project.profit_margin || 0) < 30 ? 'text-red-600' : (project.profit_margin || 0) < 50 ? 'text-amber-600' : 'text-green-600'}`}>
                        {project.profit_margin || 0}%
                      </p>
                      <p className="text-xs text-green-600">{formatCurrency(project.estimated_profit || 0)}</p>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-4 gap-2">
                    {project.phases?.map((phase, idx) => (
                      <div key={idx} className="text-center">
                        <div className="text-xs text-muted-foreground mb-1">
                          {getPhaseLabel(phase.phase)}
                        </div>
                        <div className="text-sm font-medium">{phase.progress}%</div>
                        <Progress value={phase.progress} className="h-1 mt-1" />
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
      )}

      {/* Overdue Invoices Widget */}
      {widgetConfig.overdue_invoices && (overdueInvoices.overdue?.length > 0 || overdueInvoices.due_soon?.length > 0) && (
      <Card className="border-red-200" data-testid="overdue-invoices-widget">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-red-600">
            <AlertTriangle className="h-5 w-5" />
            Alertas de Cobranza
          </CardTitle>
          <CardDescription>Facturas que requieren atención</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {overdueInvoices.overdue?.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold text-red-600 mb-2">Vencidas ({overdueInvoices.overdue.length})</h4>
                <div className="space-y-2">
                  {overdueInvoices.overdue.slice(0, 5).map((inv) => (
                    <div key={inv.id} className="flex justify-between items-center p-2 bg-red-50 rounded-sm">
                      <div>
                        <span className="font-medium">{inv.invoice_number}</span>
                        <span className="text-sm text-muted-foreground ml-2">{inv.client_name}</span>
                      </div>
                      <div className="text-right">
                        <div className="font-bold text-red-600">{formatCurrency(inv.pending_amount)}</div>
                        <div className="text-xs text-red-500">{inv.days_overdue} días vencida</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            {overdueInvoices.due_soon?.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold text-amber-600 mb-2">Por vencer ({overdueInvoices.due_soon.length})</h4>
                <div className="space-y-2">
                  {overdueInvoices.due_soon.slice(0, 5).map((inv) => (
                    <div key={inv.id} className="flex justify-between items-center p-2 bg-amber-50 rounded-sm">
                      <div>
                        <span className="font-medium">{inv.invoice_number}</span>
                        <span className="text-sm text-muted-foreground ml-2">{inv.client_name}</span>
                      </div>
                      <div className="text-right">
                        <div className="font-bold text-amber-600">{formatCurrency(inv.pending_amount)}</div>
                        <div className="text-xs text-amber-500">Vence en {inv.days_until_due} días</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
      )}

      {/* Pending Followups Widget */}
      {widgetConfig.pending_followups && pendingFollowups.length > 0 && (
      <Card data-testid="pending-followups-widget">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5 text-primary" />
            Seguimientos Pendientes ({pendingFollowups.length})
          </CardTitle>
          <CardDescription>Próximas actividades de CRM</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {pendingFollowups.slice(0, 5).map((f) => {
              const isOverdue = new Date(f.scheduled_date) < new Date();
              const isToday = new Date(f.scheduled_date).toDateString() === new Date().toDateString();
              return (
                <div 
                  key={f.id} 
                  className={`flex justify-between items-center p-3 rounded-sm ${
                    isOverdue ? 'bg-red-50 border-l-4 border-red-500' : 
                    isToday ? 'bg-amber-50 border-l-4 border-amber-500' : 'bg-slate-50'
                  }`}
                >
                  <div>
                    <div className="font-medium">{f.client_name}</div>
                    <div className="text-sm text-muted-foreground capitalize">{f.followup_type} - {f.notes}</div>
                  </div>
                  <div className="text-right">
                    <Badge className={isOverdue ? 'bg-red-500' : isToday ? 'bg-amber-500' : 'bg-slate-500'}>
                      {new Date(f.scheduled_date).toLocaleDateString('es-MX')}
                    </Badge>
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>
      )}

      {/* Financial Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="bg-gradient-to-br from-emerald-500 to-emerald-600 text-white">
          <CardHeader>
            <CardTitle className="text-white/80 text-sm">Ingresos Totales</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{formatCurrency(stats?.financial?.total_revenue || 0)}</div>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-amber-500 to-amber-600 text-white">
          <CardHeader>
            <CardTitle className="text-white/80 text-sm">Costos Totales</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{formatCurrency(stats?.financial?.total_costs || 0)}</div>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-blue-600 to-blue-700 text-white">
          <CardHeader>
            <CardTitle className="text-white/80 text-sm">Utilidad Neta</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{formatCurrency(stats?.financial?.total_profit || 0)}</div>
          </CardContent>
        </Card>
      </div>

      {/* Reminder */}
      <Card className="border-amber-200 bg-amber-50">
        <CardContent className="flex items-center gap-3 py-4">
          <AlertTriangle className="h-5 w-5 text-amber-600" />
          <p className="text-sm text-amber-800">
            <strong>Recordatorio:</strong> El almacenamiento de archivos está pendiente de configuración.
            Los documentos y fotos se almacenarán temporalmente.
          </p>
        </CardContent>
      </Card>
    </div>
  );
};

export default Dashboard;
