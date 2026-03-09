import React, { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { formatCurrency, getStatusColor, getStatusLabel, getPhaseLabel } from "../lib/utils";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Progress } from "../components/ui/progress";
import { Badge } from "../components/ui/badge";
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
} from "lucide-react";
import { toast } from "sonner";

const COLORS = ["#004e92", "#f59e0b", "#10b981", "#64748b", "#8b5cf6", "#ef4444"];

const StatCard = ({ title, value, description, icon: Icon, trend, trendValue, color = "primary" }) => (
  <Card className="stat-card" data-testid={`stat-${title.toLowerCase().replace(/\s/g, "-")}`}>
    <CardHeader className="flex flex-row items-center justify-between pb-2">
      <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
      <div className={`p-2 rounded-sm bg-${color}/10`}>
        <Icon className={`h-5 w-5 text-${color === "primary" ? "[#004e92]" : color}`} />
      </div>
    </CardHeader>
    <CardContent>
      <div className="text-3xl font-bold font-[Chivo]">{value}</div>
      {description && <p className="text-sm text-muted-foreground mt-1">{description}</p>}
      {trend && (
        <div className="flex items-center mt-2">
          {trend === "up" ? (
            <ArrowUpRight className="h-4 w-4 text-emerald-500" />
          ) : (
            <ArrowDownRight className="h-4 w-4 text-red-500" />
          )}
          <span className={`text-sm ${trend === "up" ? "text-emerald-500" : "text-red-500"}`}>
            {trendValue}
          </span>
        </div>
      )}
    </CardContent>
  </Card>
);

export const Dashboard = () => {
  const { api, company } = useAuth();
  const [stats, setStats] = useState(null);
  const [projectProgress, setProjectProgress] = useState([]);
  const [monthlyRevenue, setMonthlyRevenue] = useState([]);
  const [quotePipeline, setQuotePipeline] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (company?.id) {
      fetchDashboardData();
    }
  }, [company]);

  const fetchDashboardData = async () => {
    try {
      const [statsRes, progressRes, revenueRes, pipelineRes] = await Promise.all([
        api.get(`/dashboard/stats?company_id=${company.id}`),
        api.get(`/dashboard/project-progress?company_id=${company.id}`),
        api.get(`/dashboard/monthly-revenue?company_id=${company.id}`),
        api.get(`/dashboard/quote-pipeline?company_id=${company.id}`),
      ]);

      setStats(statsRes.data);
      setProjectProgress(progressRes.data);
      setMonthlyRevenue(revenueRes.data);
      setQuotePipeline(pipelineRes.data);
    } catch (error) {
      toast.error("Error al cargar datos del dashboard");
      console.error(error);
    } finally {
      setLoading(false);
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
    <div className="space-y-6 animate-fade-in" data-testid="dashboard">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold font-[Chivo] text-slate-900">Dashboard Estratégico</h1>
          <p className="text-muted-foreground">{company.business_name}</p>
        </div>
        <Badge variant="outline" className="w-fit">
          Actualizado: {new Date().toLocaleDateString("es-MX")}
        </Badge>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
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

      {/* Secondary Stats */}
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

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Monthly Revenue Chart */}
        <Card className="chart-container" data-testid="monthly-revenue-chart">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <DollarSign className="h-5 w-5 text-primary" />
              Facturación vs Cobranza Mensual
            </CardTitle>
            <CardDescription>Últimos 12 meses</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={monthlyRevenue}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="month" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 12 }} tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} />
                  <Tooltip
                    formatter={(value) => formatCurrency(value)}
                    contentStyle={{ borderRadius: "4px", border: "1px solid #e2e8f0" }}
                  />
                  <Legend />
                  <Bar dataKey="invoiced" name="Facturado" fill="#004e92" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="collected" name="Cobrado" fill="#10b981" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Quote Pipeline Chart */}
        <Card className="chart-container" data-testid="quote-pipeline-chart">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-primary" />
              Pipeline de Cotizaciones
            </CardTitle>
            <CardDescription>Estado actual por etapa</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-72">
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
      </div>

      {/* Project Progress */}
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
