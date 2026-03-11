import React, { useState, useEffect, useCallback } from "react";
import { useAuth } from "../context/AuthContext";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import { Skeleton } from "../components/ui/skeleton";
import { Progress } from "../components/ui/progress";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "../components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { toast } from "sonner";
import {
  Bot,
  Activity,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Play,
  RefreshCw,
  Database,
  Server,
  FileWarning,
  Wrench,
  Clock,
  PlusCircle,
  Eye,
  Bug,
  Shield,
  Zap,
  History,
} from "lucide-react";

const STATUS_ICONS = {
  passed: <CheckCircle className="h-4 w-4 text-emerald-500" />,
  failed: <XCircle className="h-4 w-4 text-red-500" />,
  warning: <AlertTriangle className="h-4 w-4 text-amber-500" />,
};

const STATUS_COLORS = {
  healthy: "bg-emerald-500",
  warning: "bg-amber-500",
  critical: "bg-red-500",
};

const CATEGORY_ICONS = {
  database: <Database className="h-4 w-4" />,
  backend: <Server className="h-4 w-4" />,
  frontend: <FileWarning className="h-4 w-4" />,
  integration: <Zap className="h-4 w-4" />,
};

export const SystemMonitor = () => {
  const { api } = useAuth();
  const [health, setHealth] = useState(null);
  const [reports, setReports] = useState([]);
  const [issues, setIssues] = useState([]);
  const [loading, setLoading] = useState(true);
  const [runningTests, setRunningTests] = useState(false);
  const [selectedReport, setSelectedReport] = useState(null);
  const [issueDialogOpen, setIssueDialogOpen] = useState(false);
  const [issueForm, setIssueForm] = useState({
    category: "general",
    description: "",
    severity: "medium",
  });
  const [autoRefresh, setAutoRefresh] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const [healthRes, reportsRes, issuesRes] = await Promise.all([
        api.get("/super-admin/system/health"),
        api.get("/super-admin/system/reports?limit=10"),
        api.get("/super-admin/system/issues"),
      ]);
      setHealth(healthRes.data);
      setReports(reportsRes.data);
      setIssues(issuesRes.data);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  }, [api]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Auto-refresh every 30 seconds if enabled
  useEffect(() => {
    let interval;
    if (autoRefresh) {
      interval = setInterval(fetchData, 30000);
    }
    return () => clearInterval(interval);
  }, [autoRefresh, fetchData]);

  const runTests = async () => {
    setRunningTests(true);
    try {
      toast.info("Ejecutando pruebas del sistema...");
      const response = await api.post("/super-admin/system/run-tests");
      setSelectedReport(response.data);
      
      if (response.data.overall_status === "healthy") {
        toast.success(`Pruebas completadas: ${response.data.passed}/${response.data.total_tests} pasadas`);
      } else if (response.data.overall_status === "warning") {
        toast.warning(`Pruebas con advertencias: ${response.data.warnings} warning(s)`);
      } else {
        toast.error(`Pruebas fallidas: ${response.data.failed} error(es)`);
      }
      
      fetchData();
    } catch (error) {
      toast.error("Error al ejecutar pruebas");
    } finally {
      setRunningTests(false);
    }
  };

  const reportIssue = async (e) => {
    e.preventDefault();
    try {
      await api.post("/super-admin/system/report-issue", issueForm);
      toast.success("Problema reportado");
      setIssueDialogOpen(false);
      setIssueForm({ category: "general", description: "", severity: "medium" });
      fetchData();
    } catch (error) {
      toast.error("Error al reportar problema");
    }
  };

  const updateIssue = async (issueId, status, resolution = null) => {
    try {
      await api.put(`/super-admin/system/issues/${issueId}`, { status, resolution });
      toast.success("Problema actualizado");
      fetchData();
    } catch (error) {
      toast.error("Error al actualizar");
    }
  };

  if (loading) {
    return (
      <div className="space-y-6 p-6">
        <Skeleton className="h-10 w-64" />
        <div className="grid grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="system-monitor">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold font-[Chivo] text-white flex items-center gap-3">
            <Bot className="h-8 w-8 text-amber-400" />
            Monitor del Sistema
          </h1>
          <p className="text-slate-400">Bot de pruebas y reparación automática</p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            variant={autoRefresh ? "secondary" : "outline"}
            size="sm"
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={autoRefresh ? "bg-emerald-500/20 text-emerald-400 border-emerald-500" : "border-slate-600 text-slate-300"}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${autoRefresh ? 'animate-spin' : ''}`} />
            Auto-refresh {autoRefresh ? "ON" : "OFF"}
          </Button>
          <Button
            onClick={runTests}
            disabled={runningTests}
            className="bg-amber-500 hover:bg-amber-600 text-slate-900"
            data-testid="run-tests-btn"
          >
            {runningTests ? (
              <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <Play className="h-4 w-4 mr-2" />
            )}
            Ejecutar Pruebas
          </Button>
        </div>
      </div>

      {/* Health Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="bg-slate-800/50 border-slate-700">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-slate-400">Estado General</div>
                <div className="text-2xl font-bold text-white capitalize flex items-center gap-2">
                  <div className={`w-3 h-3 rounded-full ${STATUS_COLORS[health?.status] || 'bg-slate-500'}`} />
                  {health?.status === "healthy" ? "Saludable" : health?.status === "warning" ? "Advertencia" : "Crítico"}
                </div>
              </div>
              <Shield className={`h-10 w-10 ${health?.status === 'healthy' ? 'text-emerald-400' : health?.status === 'warning' ? 'text-amber-400' : 'text-red-400'}`} />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-slate-800/50 border-slate-700">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-slate-400">Base de Datos</div>
                <div className="text-2xl font-bold text-white capitalize">
                  {health?.database === "healthy" ? "Conectada" : "Error"}
                </div>
              </div>
              <Database className={`h-10 w-10 ${health?.database === 'healthy' ? 'text-emerald-400' : 'text-red-400'}`} />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-slate-800/50 border-slate-700">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-slate-400">Entidades</div>
                <div className="text-lg font-bold text-white">
                  {health?.entities?.companies || 0} empresas
                </div>
                <div className="text-xs text-slate-400">
                  {health?.entities?.users || 0} usuarios • {health?.entities?.projects || 0} proyectos
                </div>
              </div>
              <Activity className="h-10 w-10 text-blue-400" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-slate-800/50 border-slate-700">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-slate-400">Problemas Abiertos</div>
                <div className="text-2xl font-bold text-white">
                  {issues.filter(i => i.status === "open").length}
                </div>
              </div>
              <Bug className={`h-10 w-10 ${issues.filter(i => i.status === "open").length > 0 ? 'text-amber-400' : 'text-slate-500'}`} />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <Tabs defaultValue="tests" className="space-y-4">
        <TabsList className="bg-slate-800 border-slate-700">
          <TabsTrigger value="tests" className="data-[state=active]:bg-amber-500 data-[state=active]:text-slate-900">
            <CheckCircle className="h-4 w-4 mr-2" />
            Pruebas
          </TabsTrigger>
          <TabsTrigger value="issues" className="data-[state=active]:bg-amber-500 data-[state=active]:text-slate-900">
            <Bug className="h-4 w-4 mr-2" />
            Problemas
          </TabsTrigger>
          <TabsTrigger value="history" className="data-[state=active]:bg-amber-500 data-[state=active]:text-slate-900">
            <History className="h-4 w-4 mr-2" />
            Historial
          </TabsTrigger>
        </TabsList>

        {/* Tests Tab */}
        <TabsContent value="tests" className="space-y-4">
          {selectedReport ? (
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-white flex items-center gap-2">
                      <Activity className="h-5 w-5 text-amber-400" />
                      Último Reporte de Pruebas
                    </CardTitle>
                    <CardDescription className="text-slate-400">
                      {new Date(selectedReport.created_at).toLocaleString("es-MX")}
                    </CardDescription>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-emerald-400">{selectedReport.passed}</div>
                      <div className="text-xs text-slate-400">Pasadas</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-amber-400">{selectedReport.warnings}</div>
                      <div className="text-xs text-slate-400">Warnings</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-red-400">{selectedReport.failed}</div>
                      <div className="text-xs text-slate-400">Fallidas</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-400">{selectedReport.auto_fixed}</div>
                      <div className="text-xs text-slate-400">Auto-reparadas</div>
                    </div>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="rounded-sm border border-slate-700 overflow-hidden">
                  <Table>
                    <TableHeader>
                      <TableRow className="bg-slate-900/50 border-slate-700">
                        <TableHead className="text-slate-300">Estado</TableHead>
                        <TableHead className="text-slate-300">Prueba</TableHead>
                        <TableHead className="text-slate-300">Categoría</TableHead>
                        <TableHead className="text-slate-300">Mensaje</TableHead>
                        <TableHead className="text-slate-300">Tiempo</TableHead>
                        <TableHead className="text-slate-300">Auto-reparado</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {selectedReport.tests.map((test, idx) => (
                        <TableRow key={idx} className="border-slate-700 hover:bg-slate-700/30">
                          <TableCell>{STATUS_ICONS[test.status]}</TableCell>
                          <TableCell className="text-white font-medium">{test.test_name}</TableCell>
                          <TableCell>
                            <Badge variant="outline" className="border-slate-600 text-slate-300">
                              {CATEGORY_ICONS[test.category]}
                              <span className="ml-1 capitalize">{test.category}</span>
                            </Badge>
                          </TableCell>
                          <TableCell className="text-slate-300 max-w-xs truncate">{test.message}</TableCell>
                          <TableCell className="text-slate-400">{test.duration_ms}ms</TableCell>
                          <TableCell>
                            {test.auto_fixed ? (
                              <Badge className="bg-blue-500/20 text-blue-400 border-blue-500">
                                <Wrench className="h-3 w-3 mr-1" />
                                Reparado
                              </Badge>
                            ) : (
                              <span className="text-slate-500">-</span>
                            )}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card className="bg-slate-800/50 border-slate-700">
              <CardContent className="p-8 text-center">
                <Bot className="h-16 w-16 mx-auto text-slate-500 mb-4" />
                <h3 className="text-xl font-medium text-white mb-2">No hay pruebas ejecutadas</h3>
                <p className="text-slate-400 mb-4">Haz clic en "Ejecutar Pruebas" para comenzar el diagnóstico del sistema</p>
                <Button onClick={runTests} disabled={runningTests} className="bg-amber-500 hover:bg-amber-600 text-slate-900">
                  <Play className="h-4 w-4 mr-2" />
                  Ejecutar Pruebas
                </Button>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Issues Tab */}
        <TabsContent value="issues" className="space-y-4">
          <div className="flex justify-end">
            <Dialog open={issueDialogOpen} onOpenChange={setIssueDialogOpen}>
              <DialogTrigger asChild>
                <Button className="bg-amber-500 hover:bg-amber-600 text-slate-900">
                  <PlusCircle className="h-4 w-4 mr-2" />
                  Reportar Problema
                </Button>
              </DialogTrigger>
              <DialogContent className="bg-slate-800 border-slate-700">
                <form onSubmit={reportIssue}>
                  <DialogHeader>
                    <DialogTitle className="text-white">Reportar Problema</DialogTitle>
                    <DialogDescription className="text-slate-400">
                      Describe el problema encontrado en el sistema
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4 py-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="grid gap-2">
                        <Label className="text-slate-300">Categoría</Label>
                        <Select
                          value={issueForm.category}
                          onValueChange={(v) => setIssueForm({ ...issueForm, category: v })}
                        >
                          <SelectTrigger className="bg-slate-700 border-slate-600 text-white">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent className="bg-slate-800 border-slate-700">
                            <SelectItem value="general">General</SelectItem>
                            <SelectItem value="database">Base de Datos</SelectItem>
                            <SelectItem value="backend">Backend</SelectItem>
                            <SelectItem value="frontend">Frontend</SelectItem>
                            <SelectItem value="integration">Integración</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="grid gap-2">
                        <Label className="text-slate-300">Severidad</Label>
                        <Select
                          value={issueForm.severity}
                          onValueChange={(v) => setIssueForm({ ...issueForm, severity: v })}
                        >
                          <SelectTrigger className="bg-slate-700 border-slate-600 text-white">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent className="bg-slate-800 border-slate-700">
                            <SelectItem value="low">Baja</SelectItem>
                            <SelectItem value="medium">Media</SelectItem>
                            <SelectItem value="high">Alta</SelectItem>
                            <SelectItem value="critical">Crítica</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                    <div className="grid gap-2">
                      <Label className="text-slate-300">Descripción</Label>
                      <Textarea
                        value={issueForm.description}
                        onChange={(e) => setIssueForm({ ...issueForm, description: e.target.value })}
                        placeholder="Describe el problema en detalle..."
                        className="bg-slate-700 border-slate-600 text-white min-h-[100px]"
                        required
                      />
                    </div>
                  </div>
                  <DialogFooter>
                    <Button type="button" variant="outline" onClick={() => setIssueDialogOpen(false)} className="border-slate-600 text-slate-300">
                      Cancelar
                    </Button>
                    <Button type="submit" className="bg-amber-500 hover:bg-amber-600 text-slate-900">
                      Reportar
                    </Button>
                  </DialogFooter>
                </form>
              </DialogContent>
            </Dialog>
          </div>

          <Card className="bg-slate-800/50 border-slate-700">
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow className="bg-slate-900/50 border-slate-700">
                    <TableHead className="text-slate-300">Estado</TableHead>
                    <TableHead className="text-slate-300">Categoría</TableHead>
                    <TableHead className="text-slate-300">Severidad</TableHead>
                    <TableHead className="text-slate-300">Descripción</TableHead>
                    <TableHead className="text-slate-300">Fecha</TableHead>
                    <TableHead className="text-slate-300">Acciones</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {issues.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={6} className="text-center py-8 text-slate-400">
                        No hay problemas reportados
                      </TableCell>
                    </TableRow>
                  ) : (
                    issues.map((issue) => (
                      <TableRow key={issue.id} className="border-slate-700 hover:bg-slate-700/30">
                        <TableCell>
                          <Badge className={`${
                            issue.status === "open" ? "bg-amber-500/20 text-amber-400" :
                            issue.status === "in_progress" ? "bg-blue-500/20 text-blue-400" :
                            "bg-emerald-500/20 text-emerald-400"
                          }`}>
                            {issue.status === "open" ? "Abierto" : issue.status === "in_progress" ? "En Progreso" : "Resuelto"}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline" className="border-slate-600 text-slate-300 capitalize">
                            {issue.category}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Badge className={`${
                            issue.severity === "critical" ? "bg-red-500/20 text-red-400" :
                            issue.severity === "high" ? "bg-orange-500/20 text-orange-400" :
                            issue.severity === "medium" ? "bg-amber-500/20 text-amber-400" :
                            "bg-slate-500/20 text-slate-400"
                          }`}>
                            {issue.severity === "critical" ? "Crítica" : issue.severity === "high" ? "Alta" : issue.severity === "medium" ? "Media" : "Baja"}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-slate-300 max-w-xs truncate">{issue.description}</TableCell>
                        <TableCell className="text-slate-400 text-sm">
                          {new Date(issue.created_at).toLocaleDateString("es-MX")}
                        </TableCell>
                        <TableCell>
                          {issue.status === "open" && (
                            <div className="flex gap-2">
                              <Button
                                size="sm"
                                variant="outline"
                                className="border-slate-600 text-slate-300 h-8"
                                onClick={() => updateIssue(issue.id, "in_progress")}
                              >
                                En Progreso
                              </Button>
                              <Button
                                size="sm"
                                className="bg-emerald-500/20 text-emerald-400 h-8"
                                onClick={() => updateIssue(issue.id, "resolved", "Resuelto")}
                              >
                                Resolver
                              </Button>
                            </div>
                          )}
                          {issue.status === "in_progress" && (
                            <Button
                              size="sm"
                              className="bg-emerald-500/20 text-emerald-400 h-8"
                              onClick={() => updateIssue(issue.id, "resolved", "Resuelto")}
                            >
                              Marcar Resuelto
                            </Button>
                          )}
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* History Tab */}
        <TabsContent value="history" className="space-y-4">
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <History className="h-5 w-5 text-amber-400" />
                Historial de Reportes
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {reports.length === 0 ? (
                  <div className="text-center py-8 text-slate-400">
                    No hay reportes anteriores
                  </div>
                ) : (
                  reports.map((report) => (
                    <div
                      key={report.id}
                      className="flex items-center justify-between p-4 bg-slate-700/30 rounded-lg cursor-pointer hover:bg-slate-700/50 transition-colors"
                      onClick={() => setSelectedReport(report)}
                    >
                      <div className="flex items-center gap-4">
                        <div className={`w-3 h-3 rounded-full ${STATUS_COLORS[report.overall_status]}`} />
                        <div>
                          <div className="text-white font-medium">
                            {new Date(report.created_at).toLocaleString("es-MX")}
                          </div>
                          <div className="text-slate-400 text-sm">
                            {report.total_tests} pruebas • {report.auto_fixed} auto-reparaciones
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="flex items-center gap-2">
                          <CheckCircle className="h-4 w-4 text-emerald-400" />
                          <span className="text-emerald-400">{report.passed}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <AlertTriangle className="h-4 w-4 text-amber-400" />
                          <span className="text-amber-400">{report.warnings}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <XCircle className="h-4 w-4 text-red-400" />
                          <span className="text-red-400">{report.failed}</span>
                        </div>
                        <Eye className="h-4 w-4 text-slate-400" />
                      </div>
                    </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default SystemMonitor;
