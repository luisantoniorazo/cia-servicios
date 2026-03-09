import React, { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { formatCurrency, calculatePercentage } from "../lib/utils";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Progress } from "../components/ui/progress";
import { Skeleton } from "../components/ui/skeleton";
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
  RadialBarChart,
  RadialBar,
  Legend,
} from "recharts";
import { toast } from "sonner";
import {
  BarChart3,
  TrendingUp,
  Target,
  Clock,
  DollarSign,
  CheckCircle,
  AlertCircle,
} from "lucide-react";

const COLORS = ["#004e92", "#f59e0b", "#10b981", "#64748b", "#8b5cf6"];

export const KPIs = () => {
  const { api, company } = useAuth();
  const [stats, setStats] = useState(null);
  const [projects, setProjects] = useState([]);
  const [quotes, setQuotes] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (company?.id) {
      fetchData();
    }
  }, [company]);

  const fetchData = async () => {
    try {
      const [statsRes, projectsRes, quotesRes] = await Promise.all([
        api.get(`/dashboard/stats?company_id=${company.id}`),
        api.get(`/projects?company_id=${company.id}`),
        api.get(`/quotes?company_id=${company.id}`),
      ]);
      setStats(statsRes.data);
      setProjects(projectsRes.data);
      setQuotes(quotesRes.data);
    } catch (error) {
      toast.error("Error al cargar indicadores");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Skeleton className="h-80" />
          <Skeleton className="h-80" />
        </div>
      </div>
    );
  }

  // Calculate KPIs
  const totalProjects = projects.length;
  const completedProjects = projects.filter((p) => p.status === "completed").length;
  const activeProjects = projects.filter((p) => p.status === "active").length;
  
  const totalQuotes = quotes.length;
  const authorizedQuotes = quotes.filter((q) => q.status === "authorized").length;
  const conversionRate = totalQuotes > 0 ? (authorizedQuotes / totalQuotes * 100).toFixed(1) : 0;
  
  const totalRevenue = stats?.financial?.total_revenue || 0;
  const totalCosts = stats?.financial?.total_costs || 0;
  const profitMargin = totalRevenue > 0 ? ((totalRevenue - totalCosts) / totalRevenue * 100).toFixed(1) : 0;
  
  const onTimeProjects = projects.filter((p) => {
    if (p.status !== "completed" || !p.commitment_date) return true;
    return new Date(p.updated_at) <= new Date(p.commitment_date);
  }).length;
  const onTimeRate = totalProjects > 0 ? (onTimeProjects / totalProjects * 100).toFixed(1) : 100;

  // Chart data
  const projectStatusData = [
    { name: "Cotización", value: projects.filter((p) => p.status === "quotation").length },
    { name: "Autorizados", value: projects.filter((p) => p.status === "authorized").length },
    { name: "Activos", value: activeProjects },
    { name: "Completados", value: completedProjects },
  ].filter((d) => d.value > 0);

  const quoteStatusData = [
    { name: "En proceso", value: quotes.filter((q) => !["authorized", "denied"].includes(q.status)).length },
    { name: "Autorizadas", value: authorizedQuotes },
    { name: "Negadas", value: quotes.filter((q) => q.status === "denied").length },
  ].filter((d) => d.value > 0);

  const kpiGaugeData = [
    { name: "Conversión", value: parseFloat(conversionRate), fill: "#004e92" },
    { name: "Rentabilidad", value: parseFloat(profitMargin), fill: "#10b981" },
    { name: "Puntualidad", value: parseFloat(onTimeRate), fill: "#f59e0b" },
  ];

  return (
    <div className="space-y-6 animate-fade-in" data-testid="kpis-page">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold font-[Chivo] text-slate-900">Indicadores KPI</h1>
        <p className="text-muted-foreground">Métricas clave de rendimiento empresarial</p>
      </div>

      {/* Main KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="stat-card">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Tasa de Conversión
            </CardTitle>
            <Target className="h-5 w-5 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold font-[Chivo] text-primary">{conversionRate}%</div>
            <p className="text-xs text-muted-foreground mt-1">
              {authorizedQuotes} de {totalQuotes} cotizaciones
            </p>
            <Progress value={parseFloat(conversionRate)} className="h-2 mt-3" />
          </CardContent>
        </Card>

        <Card className="stat-card">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Margen de Rentabilidad
            </CardTitle>
            <TrendingUp className="h-5 w-5 text-emerald-500" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold font-[Chivo] text-emerald-600">{profitMargin}%</div>
            <p className="text-xs text-muted-foreground mt-1">
              Utilidad: {formatCurrency(totalRevenue - totalCosts)}
            </p>
            <Progress value={parseFloat(profitMargin)} className="h-2 mt-3" />
          </CardContent>
        </Card>

        <Card className="stat-card">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Cumplimiento de Fechas
            </CardTitle>
            <Clock className="h-5 w-5 text-amber-500" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold font-[Chivo] text-amber-600">{onTimeRate}%</div>
            <p className="text-xs text-muted-foreground mt-1">
              {onTimeProjects} de {totalProjects} proyectos a tiempo
            </p>
            <Progress value={parseFloat(onTimeRate)} className="h-2 mt-3" />
          </CardContent>
        </Card>

        <Card className="stat-card">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Eficiencia de Cobranza
            </CardTitle>
            <DollarSign className="h-5 w-5 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold font-[Chivo] text-blue-600">
              {stats?.financial?.total_invoiced > 0 
                ? ((stats?.financial?.total_collected / stats?.financial?.total_invoiced) * 100).toFixed(1)
                : 0}%
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {formatCurrency(stats?.financial?.total_collected || 0)} cobrado
            </p>
            <Progress 
              value={stats?.financial?.total_invoiced > 0 
                ? (stats?.financial?.total_collected / stats?.financial?.total_invoiced) * 100
                : 0} 
              className="h-2 mt-3" 
            />
          </CardContent>
        </Card>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Project Status Distribution */}
        <Card className="chart-container" data-testid="project-status-chart">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-primary" />
              Distribución de Proyectos
            </CardTitle>
            <CardDescription>Por estado actual</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={projectStatusData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    dataKey="value"
                    label={({ name, value }) => `${name}: ${value}`}
                  >
                    {projectStatusData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Quote Conversion Funnel */}
        <Card className="chart-container" data-testid="quote-funnel-chart">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Target className="h-5 w-5 text-primary" />
              Embudo de Cotizaciones
            </CardTitle>
            <CardDescription>Conversión de pipeline comercial</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={quoteStatusData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis type="number" />
                  <YAxis type="category" dataKey="name" width={100} />
                  <Tooltip />
                  <Bar dataKey="value" fill="#004e92" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* KPI Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="bg-gradient-to-br from-primary to-blue-700 text-white">
          <CardHeader>
            <CardTitle className="text-white/80 text-sm flex items-center gap-2">
              <CheckCircle className="h-4 w-4" />
              Proyectos Completados
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-4xl font-bold">{completedProjects}</div>
            <p className="text-white/70 text-sm mt-1">de {totalProjects} totales</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-emerald-500 to-emerald-700 text-white">
          <CardHeader>
            <CardTitle className="text-white/80 text-sm flex items-center gap-2">
              <DollarSign className="h-4 w-4" />
              Ingresos Totales
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{formatCurrency(totalRevenue)}</div>
            <p className="text-white/70 text-sm mt-1">Contratos ejecutados</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-amber-500 to-amber-700 text-white">
          <CardHeader>
            <CardTitle className="text-white/80 text-sm flex items-center gap-2">
              <AlertCircle className="h-4 w-4" />
              Pipeline Activo
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{formatCurrency(stats?.quotes?.pipeline_value || 0)}</div>
            <p className="text-white/70 text-sm mt-1">En cotizaciones pendientes</p>
          </CardContent>
        </Card>
      </div>

      {/* KPI Definitions */}
      <Card>
        <CardHeader>
          <CardTitle>Definición de Indicadores</CardTitle>
          <CardDescription>Cómo se calculan los KPIs principales</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div className="p-4 bg-slate-50 rounded-sm">
              <h4 className="font-semibold mb-2">Tasa de Conversión</h4>
              <p className="text-muted-foreground">
                Porcentaje de cotizaciones que se convierten en proyectos autorizados.
                Se calcula: (Cotizaciones Autorizadas / Total Cotizaciones) × 100
              </p>
            </div>
            <div className="p-4 bg-slate-50 rounded-sm">
              <h4 className="font-semibold mb-2">Margen de Rentabilidad</h4>
              <p className="text-muted-foreground">
                Porcentaje de utilidad sobre los ingresos totales.
                Se calcula: ((Ingresos - Costos) / Ingresos) × 100
              </p>
            </div>
            <div className="p-4 bg-slate-50 rounded-sm">
              <h4 className="font-semibold mb-2">Cumplimiento de Fechas</h4>
              <p className="text-muted-foreground">
                Porcentaje de proyectos entregados en la fecha compromiso.
                Se calcula: (Proyectos a Tiempo / Total Proyectos) × 100
              </p>
            </div>
            <div className="p-4 bg-slate-50 rounded-sm">
              <h4 className="font-semibold mb-2">Eficiencia de Cobranza</h4>
              <p className="text-muted-foreground">
                Porcentaje del monto facturado que ha sido cobrado.
                Se calcula: (Monto Cobrado / Monto Facturado) × 100
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default KPIs;
