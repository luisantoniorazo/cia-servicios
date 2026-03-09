import React, { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { formatDate, formatDateTime , getApiErrorMessage } from "../lib/utils";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import { Progress } from "../components/ui/progress";
import { Skeleton } from "../components/ui/skeleton";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "../components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "../components/ui/dropdown-menu";
import { toast } from "sonner";
import {
  ClipboardList,
  Plus,
  MoreVertical,
  Camera,
  AlertTriangle,
  Trash2,
  Calendar,
  MapPin,
  User,
} from "lucide-react";

export const FieldReports = () => {
  const { api, company, user } = useAuth();
  const [reports, setReports] = useState([]);
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [formData, setFormData] = useState({
    project_id: "",
    title: "",
    description: "",
    progress_percentage: 0,
    incidents: "",
  });

  useEffect(() => {
    if (company?.id) {
      fetchData();
    }
  }, [company]);

  const fetchData = async () => {
    try {
      const [reportsRes, projectsRes] = await Promise.all([
        api.get(`/field-reports?company_id=${company.id}`),
        api.get(`/projects?company_id=${company.id}`),
      ]);
      setReports(reportsRes.data);
      setProjects(projectsRes.data);
    } catch (error) {
      toast.error("Error al cargar reportes");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await api.post("/field-reports", {
        company_id: company.id,
        ...formData,
        progress_percentage: parseInt(formData.progress_percentage) || 0,
        reported_by: user?.id,
      });
      toast.success("Reporte creado exitosamente");
      setDialogOpen(false);
      resetForm();
      fetchData();
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Error al crear reporte"));
    }
  };

  const handleDelete = async (reportId) => {
    if (!window.confirm("¿Estás seguro de eliminar este reporte?")) return;
    try {
      await api.delete(`/field-reports/${reportId}`);
      toast.success("Reporte eliminado");
      fetchData();
    } catch (error) {
      toast.error("Error al eliminar reporte");
    }
  };

  const resetForm = () => {
    setFormData({
      project_id: "",
      title: "",
      description: "",
      progress_percentage: 0,
      incidents: "",
    });
  };

  const getProjectName = (projectId) => {
    const project = projects.find((p) => p.id === projectId);
    return project?.name || "N/A";
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-96" />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in" data-testid="field-reports-page">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold font-[Chivo] text-slate-900">Reportes de Campo</h1>
          <p className="text-muted-foreground">Seguimiento diario de servicios y proyectos</p>
        </div>
        <Button className="btn-industrial" onClick={() => setDialogOpen(true)} data-testid="add-report-btn">
          <Plus className="mr-2 h-4 w-4" />
          Nuevo Reporte
        </Button>
      </div>

      {/* Storage Warning */}
      <Card className="border-amber-200 bg-amber-50">
        <CardContent className="flex items-center gap-3 py-4">
          <AlertTriangle className="h-5 w-5 text-amber-600" />
          <p className="text-sm text-amber-800">
            <strong>Recordatorio:</strong> El almacenamiento de fotografías está pendiente.
            Las fotos podrán agregarse cuando se configure el almacenamiento.
          </p>
        </CardContent>
      </Card>

      {/* Reports Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {reports.length === 0 ? (
          <Card className="col-span-full">
            <CardContent className="flex flex-col items-center justify-center py-12">
              <ClipboardList className="h-12 w-12 text-slate-300 mb-4" />
              <p className="text-muted-foreground">No hay reportes de campo registrados</p>
              <Button 
                variant="outline" 
                className="mt-4"
                onClick={() => setDialogOpen(true)}
              >
                Crear primer reporte
              </Button>
            </CardContent>
          </Card>
        ) : (
          reports.map((report) => (
            <Card key={report.id} className="relative" data-testid={`report-card-${report.id}`}>
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="text-lg">{report.title}</CardTitle>
                    <CardDescription>{getProjectName(report.project_id)}</CardDescription>
                  </div>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon">
                        <MoreVertical className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem
                        onClick={() => handleDelete(report.id)}
                        className="text-red-600"
                      >
                        <Trash2 className="mr-2 h-4 w-4" />
                        Eliminar
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-sm text-slate-600 line-clamp-3">{report.description}</p>
                
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Avance reportado</span>
                    <span className="font-medium">{report.progress_percentage}%</span>
                  </div>
                  <Progress value={report.progress_percentage} className="h-2" />
                </div>

                {report.incidents && (
                  <div className="p-3 bg-red-50 rounded-sm border border-red-100">
                    <div className="flex items-center gap-2 text-red-700 text-sm font-medium mb-1">
                      <AlertTriangle className="h-4 w-4" />
                      Incidentes
                    </div>
                    <p className="text-sm text-red-600">{report.incidents}</p>
                  </div>
                )}

                <div className="flex items-center gap-4 text-xs text-muted-foreground pt-2 border-t">
                  <div className="flex items-center gap-1">
                    <Calendar className="h-3 w-3" />
                    {formatDate(report.report_date)}
                  </div>
                  {report.photos?.length > 0 && (
                    <div className="flex items-center gap-1">
                      <Camera className="h-3 w-3" />
                      {report.photos.length} fotos
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>

      {/* Create Report Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <form onSubmit={handleSubmit}>
            <DialogHeader>
              <DialogTitle>Nuevo Reporte de Campo</DialogTitle>
              <DialogDescription>
                Registra el avance diario del proyecto
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid gap-2">
                <Label htmlFor="project_id">Proyecto *</Label>
                <Select
                  value={formData.project_id}
                  onValueChange={(value) => setFormData({ ...formData, project_id: value })}
                >
                  <SelectTrigger data-testid="report-project-select">
                    <SelectValue placeholder="Seleccionar proyecto" />
                  </SelectTrigger>
                  <SelectContent>
                    {projects.map((project) => (
                      <SelectItem key={project.id} value={project.id}>
                        {project.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="grid gap-2">
                <Label htmlFor="title">Título del Reporte *</Label>
                <Input
                  id="title"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  placeholder="Avance instalación eléctrica"
                  required
                  data-testid="report-title-input"
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="description">Descripción de Actividades *</Label>
                <Textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Detalle las actividades realizadas..."
                  required
                  rows={4}
                  data-testid="report-description-input"
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="progress_percentage">Porcentaje de Avance</Label>
                <div className="flex items-center gap-4">
                  <Input
                    id="progress_percentage"
                    type="range"
                    min="0"
                    max="100"
                    value={formData.progress_percentage}
                    onChange={(e) => setFormData({ ...formData, progress_percentage: e.target.value })}
                    className="flex-1"
                  />
                  <span className="w-12 text-center font-medium">{formData.progress_percentage}%</span>
                </div>
              </div>
              <div className="grid gap-2">
                <Label htmlFor="incidents">Incidentes (si aplica)</Label>
                <Textarea
                  id="incidents"
                  value={formData.incidents}
                  onChange={(e) => setFormData({ ...formData, incidents: e.target.value })}
                  placeholder="Describa cualquier incidente o problema..."
                  rows={2}
                />
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
                Cancelar
              </Button>
              <Button type="submit" className="btn-industrial" data-testid="save-report-btn">
                Crear Reporte
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default FieldReports;
