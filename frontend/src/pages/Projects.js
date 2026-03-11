import React, { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { formatCurrency, formatDate, getStatusColor, getStatusLabel, getPhaseLabel , getApiErrorMessage } from "../lib/utils";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import { Badge } from "../components/ui/badge";
import { Progress } from "../components/ui/progress";
import { Skeleton } from "../components/ui/skeleton";
import { Calendar } from "../components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "../components/ui/popover";
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
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "../components/ui/dropdown-menu";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { toast } from "sonner";
import { format } from "date-fns";
import { es } from "date-fns/locale";
import {
  FolderKanban,
  Plus,
  MoreVertical,
  Calendar as CalendarIcon,
  MapPin,
  User,
  DollarSign,
  Clock,
  Eye,
  Edit,
  Trash2,
  CheckCircle,
  AlertCircle,
  PlayCircle,
  PauseCircle,
  ListTodo,
  Search,
  X,
  GanttChartSquare,
  LayoutList,
} from "lucide-react";
import { cn } from "../lib/utils";
import { GanttChart } from "../components/GanttChart";

const PROJECT_STATUSES = [
  { value: "quotation", label: "En Cotización" },
  { value: "authorized", label: "Autorizado" },
  { value: "active", label: "Activo" },
  { value: "completed", label: "Completado" },
  { value: "cancelled", label: "Cancelado" },
];

const PHASES = ["negotiation", "purchases", "process", "delivery"];

export const Projects = () => {
  const { api, company, user } = useAuth();
  const [projects, setProjects] = useState([]);
  const [clients, setClients] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [detailDialogOpen, setDetailDialogOpen] = useState(false);
  const [taskDialogOpen, setTaskDialogOpen] = useState(false);
  const [selectedProject, setSelectedProject] = useState(null);
  const [statusFilter, setStatusFilter] = useState("all");
  const [viewMode, setViewMode] = useState("list"); // list, gantt
  const [formData, setFormData] = useState({
    client_id: "",
    name: "",
    description: "",
    location: "",
    start_date: null,
    end_date: null,
    commitment_date: null,
    contract_amount: "",
    status: "quotation",
  });
  const [taskForm, setTaskForm] = useState({
    name: "",
    description: "",
    assigned_to: "",
    estimated_hours: "",
    estimated_cost: "",
    due_date: "",
    status: "pending",
  });
  
  const [searchFilter, setSearchFilter] = useState("");

  // Filter projects based on search
  const getFilteredProjects = (projectList) => {
    if (!searchFilter) return projectList;
    const search = searchFilter.toLowerCase();
    return projectList.filter((project) => {
      const clientName = getClientName(project.client_id)?.toLowerCase() || "";
      return (
        project.name?.toLowerCase().includes(search) ||
        project.description?.toLowerCase().includes(search) ||
        project.location?.toLowerCase().includes(search) ||
        clientName.includes(search) ||
        formatCurrency(project.contract_amount).includes(search)
      );
    });
  };

  useEffect(() => {
    if (company?.id) {
      fetchData();
    }
  }, [company]);

  const fetchData = async () => {
    try {
      const [projectsRes, clientsRes, usersRes] = await Promise.all([
        api.get(`/projects?company_id=${company.id}`),
        api.get(`/clients?company_id=${company.id}`),
        api.get(`/admin/users`),
      ]);
      setProjects(projectsRes.data);
      setClients(clientsRes.data);
      setUsers(usersRes.data || []);
    } catch (error) {
      toast.error("Error al cargar proyectos");
    } finally {
      setLoading(false);
    }
  };

  const fetchProjectTasks = async (projectId) => {
    try {
      const response = await api.get(`/projects/${projectId}/tasks`);
      setTasks(response.data);
    } catch (error) {
      console.error("Error fetching tasks:", error);
      setTasks([]);
    }
  };

  const handleCreateProject = async (e) => {
    e.preventDefault();
    try {
      await api.post("/projects", {
        company_id: company.id,
        ...formData,
        contract_amount: parseFloat(formData.contract_amount) || 0,
      });
      toast.success("Proyecto creado exitosamente");
      setDialogOpen(false);
      resetForm();
      fetchData();
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Error al crear proyecto"));
    }
  };

  const handleUpdateStatus = async (projectId, status) => {
    try {
      await api.patch(`/projects/${projectId}/status?status=${status}`);
      toast.success("Estado actualizado");
      fetchData();
    } catch (error) {
      toast.error("Error al actualizar estado");
    }
  };

  const handleUpdatePhase = async (projectId, phase, progress) => {
    try {
      await api.patch(`/projects/${projectId}/phase?phase=${phase}&progress=${progress}`);
      toast.success("Fase actualizada");
      fetchData();
      // Refresh selected project
      if (selectedProject?.id === projectId) {
        const res = await api.get(`/projects/${projectId}`);
        setSelectedProject(res.data);
      }
    } catch (error) {
      toast.error("Error al actualizar fase");
    }
  };

  const handleDeleteProject = async (projectId) => {
    if (!window.confirm("¿Estás seguro de eliminar este proyecto?")) return;
    try {
      await api.delete(`/projects/${projectId}`);
      toast.success("Proyecto eliminado");
      fetchData();
    } catch (error) {
      toast.error("Error al eliminar proyecto");
    }
  };

  const handleCreateTask = async (e) => {
    e.preventDefault();
    if (!selectedProject) return;
    try {
      await api.post(`/projects/${selectedProject.id}/tasks`, {
        project_id: selectedProject.id,
        company_id: company.id,
        name: taskForm.name,
        description: taskForm.description,
        assigned_to: taskForm.assigned_to || null,
        estimated_hours: parseFloat(taskForm.estimated_hours) || 0,
        estimated_cost: parseFloat(taskForm.estimated_cost) || 0,
        due_date: taskForm.due_date || null,
        status: taskForm.status,
      });
      toast.success("Tarea creada");
      setTaskDialogOpen(false);
      resetTaskForm();
      fetchProjectTasks(selectedProject.id);
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Error al crear tarea"));
    }
  };

  const handleUpdateTaskStatus = async (taskId, status) => {
    if (!selectedProject) return;
    try {
      await api.put(`/projects/${selectedProject.id}/tasks/${taskId}`, { status });
      toast.success("Tarea actualizada");
      fetchProjectTasks(selectedProject.id);
    } catch (error) {
      toast.error("Error al actualizar tarea");
    }
  };

  const handleDeleteTask = async (taskId) => {
    if (!selectedProject) return;
    if (!window.confirm("¿Eliminar esta tarea?")) return;
    try {
      await api.delete(`/projects/${selectedProject.id}/tasks/${taskId}`);
      toast.success("Tarea eliminada");
      fetchProjectTasks(selectedProject.id);
    } catch (error) {
      toast.error("Error al eliminar tarea");
    }
  };

  const resetForm = () => {
    setFormData({
      client_id: "",
      name: "",
      description: "",
      location: "",
      start_date: null,
      end_date: null,
      commitment_date: null,
      contract_amount: "",
      status: "quotation",
    });
  };

  const resetTaskForm = () => {
    setTaskForm({
      name: "",
      description: "",
      assigned_to: "",
      estimated_hours: "",
      estimated_cost: "",
      due_date: "",
      status: "pending",
    });
  };

  const openProjectDetail = (project) => {
    setSelectedProject(project);
    fetchProjectTasks(project.id);
    setDetailDialogOpen(true);
  };

  const getClientName = (clientId) => {
    const client = clients.find((c) => c.id === clientId);
    return client?.name || "N/A";
  };

  const baseFilteredProjects = statusFilter === "all" 
    ? projects 
    : projects.filter((p) => p.status === statusFilter);
  
  const filteredProjects = getFilteredProjects(baseFilteredProjects);

  const openDetailDialog = async (project) => {
    try {
      const res = await api.get(`/projects/${project.id}`);
      setSelectedProject(res.data);
      setDetailDialogOpen(true);
    } catch (error) {
      toast.error("Error al cargar detalles");
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
        <Skeleton className="h-96" />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in" data-testid="projects-page">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold font-[Chivo] text-slate-900">Gestión de Proyectos</h1>
          <p className="text-muted-foreground">Control de proyectos EPC y servicios</p>
        </div>
        <div className="flex items-center gap-3">
          {/* View Toggle */}
          <div className="flex border rounded-md">
            <Button
              variant={viewMode === "list" ? "secondary" : "ghost"}
              size="sm"
              onClick={() => setViewMode("list")}
              className="rounded-r-none"
              data-testid="view-list-btn"
            >
              <LayoutList className="h-4 w-4 mr-2" />
              Lista
            </Button>
            <Button
              variant={viewMode === "gantt" ? "secondary" : "ghost"}
              size="sm"
              onClick={() => setViewMode("gantt")}
              className="rounded-l-none"
              data-testid="view-gantt-btn"
            >
              <GanttChartSquare className="h-4 w-4 mr-2" />
              Gantt
            </Button>
          </div>
          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger asChild>
              <Button className="btn-industrial" data-testid="add-project-btn">
                <Plus className="mr-2 h-4 w-4" />
                Nuevo Proyecto
              </Button>
            </DialogTrigger>
          <DialogContent className="sm:max-w-[600px]">
            <form onSubmit={handleCreateProject}>
              <DialogHeader>
                <DialogTitle>Crear Nuevo Proyecto</DialogTitle>
                <DialogDescription>
                  Ingresa los datos del proyecto para iniciar su seguimiento
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="grid gap-2">
                    <Label htmlFor="client_id">Cliente *</Label>
                    <Select
                      value={formData.client_id}
                      onValueChange={(value) => setFormData({ ...formData, client_id: value })}
                    >
                      <SelectTrigger data-testid="project-client-select">
                        <SelectValue placeholder="Seleccionar cliente" />
                      </SelectTrigger>
                      <SelectContent>
                        {clients.map((client) => (
                          <SelectItem key={client.id} value={client.id}>
                            {client.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="status">Estado</Label>
                    <Select
                      value={formData.status}
                      onValueChange={(value) => setFormData({ ...formData, status: value })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {PROJECT_STATUSES.map((s) => (
                          <SelectItem key={s.value} value={s.value}>
                            {s.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="name">Nombre del Proyecto *</Label>
                  <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="Instalación Planta Industrial"
                    required
                    data-testid="project-name-input"
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="description">Descripción</Label>
                  <Textarea
                    id="description"
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    placeholder="Descripción del proyecto..."
                    rows={3}
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="grid gap-2">
                    <Label htmlFor="location">Ubicación</Label>
                    <Input
                      id="location"
                      value={formData.location}
                      onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                      placeholder="Ciudad, Estado"
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="contract_amount">Monto del Contrato (MXN)</Label>
                    <Input
                      id="contract_amount"
                      type="number"
                      value={formData.contract_amount}
                      onChange={(e) => setFormData({ ...formData, contract_amount: e.target.value })}
                      placeholder="500000"
                      data-testid="project-amount-input"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-4">
                  <div className="grid gap-2">
                    <Label>Fecha de Inicio</Label>
                    <Popover>
                      <PopoverTrigger asChild>
                        <Button
                          variant="outline"
                          className={cn(
                            "justify-start text-left font-normal",
                            !formData.start_date && "text-muted-foreground"
                          )}
                        >
                          <CalendarIcon className="mr-2 h-4 w-4" />
                          {formData.start_date
                            ? format(formData.start_date, "PPP", { locale: es })
                            : "Seleccionar fecha"}
                        </Button>
                      </PopoverTrigger>
                      <PopoverContent className="w-auto p-0">
                        <Calendar
                          mode="single"
                          selected={formData.start_date}
                          onSelect={(date) => setFormData({ ...formData, start_date: date })}
                          initialFocus
                        />
                      </PopoverContent>
                    </Popover>
                  </div>
                  <div className="grid gap-2">
                    <Label>Fecha de Fin</Label>
                    <Popover>
                      <PopoverTrigger asChild>
                        <Button
                          variant="outline"
                          className={cn(
                            "justify-start text-left font-normal",
                            !formData.end_date && "text-muted-foreground"
                          )}
                        >
                          <CalendarIcon className="mr-2 h-4 w-4" />
                          {formData.end_date
                            ? format(formData.end_date, "PPP", { locale: es })
                            : "Seleccionar fecha"}
                        </Button>
                      </PopoverTrigger>
                      <PopoverContent className="w-auto p-0">
                        <Calendar
                          mode="single"
                          selected={formData.end_date}
                          onSelect={(date) => setFormData({ ...formData, end_date: date })}
                          initialFocus
                        />
                      </PopoverContent>
                    </Popover>
                  </div>
                  <div className="grid gap-2">
                    <Label>Fecha Compromiso</Label>
                    <Popover>
                      <PopoverTrigger asChild>
                        <Button
                          variant="outline"
                          className={cn(
                            "justify-start text-left font-normal",
                            !formData.commitment_date && "text-muted-foreground"
                          )}
                        >
                          <CalendarIcon className="mr-2 h-4 w-4" />
                          {formData.commitment_date
                            ? format(formData.commitment_date, "PPP", { locale: es })
                            : "Seleccionar fecha"}
                        </Button>
                      </PopoverTrigger>
                      <PopoverContent className="w-auto p-0">
                        <Calendar
                          mode="single"
                          selected={formData.commitment_date}
                          onSelect={(date) => setFormData({ ...formData, commitment_date: date })}
                          initialFocus
                        />
                      </PopoverContent>
                    </Popover>
                  </div>
                </div>
              </div>
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
                  Cancelar
                </Button>
                <Button type="submit" className="btn-industrial" data-testid="save-project-btn">
                  Crear Proyecto
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {PROJECT_STATUSES.map((status) => {
          const count = projects.filter((p) => p.status === status.value).length;
          return (
            <Card
              key={status.value}
              className={cn(
                "cursor-pointer transition-all hover:shadow-md",
                statusFilter === status.value && "ring-2 ring-primary"
              )}
              onClick={() => setStatusFilter(status.value === statusFilter ? "all" : status.value)}
            >
              <CardContent className="p-4">
                <div className="text-2xl font-bold font-[Chivo]">{count}</div>
                <div className="text-sm text-muted-foreground">{status.label}</div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Gantt Chart View */}
      {viewMode === "gantt" && (
        <GanttChart
          projects={filteredProjects}
          tasks={tasks}
          clients={clients}
          onProjectClick={(project) => openDetailDialog(project)}
          onProjectUpdate={async (projectId, updates) => {
            try {
              await api.put(`/projects/${projectId}`, updates);
              fetchProjects();
            } catch (error) {
              throw error;
            }
          }}
        />
      )}

      {/* Projects Table View */}
      {viewMode === "list" && (
      <Card data-testid="projects-table-card">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FolderKanban className="h-5 w-5 text-primary" />
            Proyectos {statusFilter !== "all" && `- ${PROJECT_STATUSES.find((s) => s.value === statusFilter)?.label}`}
          </CardTitle>
          <CardDescription>
            {filteredProjects.length} proyecto(s) encontrado(s)
          </CardDescription>
        </CardHeader>
        <CardContent>
          {/* Search Filter */}
          <div className="flex items-center gap-2 mb-4">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Buscar por nombre, cliente, ubicación..."
                value={searchFilter}
                onChange={(e) => setSearchFilter(e.target.value)}
                className="pl-9"
                data-testid="projects-search-filter"
              />
              {searchFilter && (
                <button
                  onClick={() => setSearchFilter("")}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  <X className="h-4 w-4" />
                </button>
              )}
            </div>
            {searchFilter && (
              <Badge variant="secondary" className="flex items-center gap-1">
                Filtro activo: "{searchFilter}"
              </Badge>
            )}
          </div>
          <div className="rounded-sm border overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow className="bg-slate-50">
                  <TableHead>Proyecto</TableHead>
                  <TableHead>Cliente</TableHead>
                  <TableHead>Monto</TableHead>
                  <TableHead>Avance</TableHead>
                  <TableHead>Fecha Compromiso</TableHead>
                  <TableHead>Estado</TableHead>
                  <TableHead className="w-[50px]"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredProjects.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center py-8 text-muted-foreground">
                      No hay proyectos registrados
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredProjects.map((project) => (
                    <TableRow key={project.id} data-testid={`project-row-${project.id}`}>
                      <TableCell>
                        <div>
                          <div className="font-medium">{project.name}</div>
                          {project.location && (
                            <div className="text-sm text-muted-foreground flex items-center gap-1">
                              <MapPin className="h-3 w-3" />
                              {project.location}
                            </div>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>{getClientName(project.client_id)}</TableCell>
                      <TableCell className="font-medium">
                        {formatCurrency(project.contract_amount)}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Progress value={project.total_progress} className="w-20 h-2" />
                          <span className="text-sm font-medium">{project.total_progress}%</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        {project.commitment_date ? (
                          <div className="flex items-center gap-1 text-sm">
                            <Clock className="h-3 w-3" />
                            {formatDate(project.commitment_date)}
                          </div>
                        ) : (
                          "-"
                        )}
                      </TableCell>
                      <TableCell>
                        <Badge className={getStatusColor(project.status)}>
                          {getStatusLabel(project.status)}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon">
                              <MoreVertical className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => openProjectDetail(project)}>
                              <Eye className="mr-2 h-4 w-4" />
                              Ver Detalles
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={() => {
                              setSelectedProject(project);
                              fetchProjectTasks(project.id);
                              setTaskDialogOpen(true);
                            }}>
                              <ListTodo className="mr-2 h-4 w-4 text-purple-500" />
                              Agregar Tarea
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem onClick={() => handleUpdateStatus(project.id, "active")}>
                              <PlayCircle className="mr-2 h-4 w-4 text-emerald-500" />
                              Activar
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={() => handleUpdateStatus(project.id, "completed")}>
                              <CheckCircle className="mr-2 h-4 w-4 text-blue-500" />
                              Completar
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={() => handleUpdateStatus(project.id, "cancelled")}>
                              <PauseCircle className="mr-2 h-4 w-4 text-red-500" />
                              Cancelar
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem
                              onClick={() => handleDeleteProject(project.id)}
                              className="text-red-600"
                            >
                              <Trash2 className="mr-2 h-4 w-4" />
                              Eliminar
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
      )}

      {/* Project Detail Dialog */}
      <Dialog open={detailDialogOpen} onOpenChange={setDetailDialogOpen}>
        <DialogContent className="sm:max-w-[800px] max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{selectedProject?.name}</DialogTitle>
            <DialogDescription>
              {getClientName(selectedProject?.client_id)} • {selectedProject?.location || "Sin ubicación"}
            </DialogDescription>
          </DialogHeader>
          {selectedProject && (
            <div className="space-y-6">
              {/* Progress Overview */}
              <div className="flex items-center justify-between p-4 bg-slate-50 rounded-sm">
                <div>
                  <div className="text-sm text-muted-foreground">Avance Total</div>
                  <div className="text-3xl font-bold text-primary">{selectedProject.total_progress}%</div>
                </div>
                <div className="text-right">
                  <div className="text-sm text-muted-foreground">Monto del Contrato</div>
                  <div className="text-2xl font-bold">{formatCurrency(selectedProject.contract_amount)}</div>
                </div>
              </div>

              {/* Phases */}
              <div className="space-y-4">
                <h4 className="font-semibold">Control por Fases</h4>
                {selectedProject.phases?.map((phase, idx) => (
                  <div key={idx} className="p-4 border rounded-sm space-y-3">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-medium">{getPhaseLabel(phase.phase)}</div>
                        <div className="text-sm text-muted-foreground">Fase {idx + 1} de 4</div>
                      </div>
                      <div className="text-right">
                        <div className="text-2xl font-bold">{phase.progress}%</div>
                      </div>
                    </div>
                    <Progress value={phase.progress} className="h-2" />
                    <div className="flex gap-2">
                      {[0, 25, 50, 75, 100].map((val) => (
                        <Button
                          key={val}
                          size="sm"
                          variant={phase.progress === val ? "default" : "outline"}
                          onClick={() => handleUpdatePhase(selectedProject.id, phase.phase, val)}
                        >
                          {val}%
                        </Button>
                      ))}
                    </div>
                  </div>
                ))}
              </div>

              {/* Tasks Section */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h4 className="font-semibold flex items-center gap-2">
                    <ListTodo className="h-4 w-4" />
                    Tareas del Proyecto
                  </h4>
                  <Button size="sm" variant="outline" onClick={() => setTaskDialogOpen(true)}>
                    <Plus className="mr-1 h-3 w-3" />
                    Nueva Tarea
                  </Button>
                </div>
                {tasks.length === 0 ? (
                  <p className="text-sm text-muted-foreground text-center py-4">No hay tareas registradas</p>
                ) : (
                  <div className="border rounded-sm divide-y max-h-48 overflow-y-auto">
                    {tasks.map((task) => (
                      <div key={task.id} className="p-3 flex items-center justify-between hover:bg-slate-50">
                        <div className="flex-1">
                          <div className="font-medium">{task.name}</div>
                          <div className="text-sm text-muted-foreground">
                            {task.estimated_hours > 0 && <span>{task.estimated_hours}h</span>}
                            {task.estimated_cost > 0 && <span className="ml-2">{formatCurrency(task.estimated_cost)}</span>}
                            {task.due_date && <span className="ml-2">• Vence: {formatDate(task.due_date)}</span>}
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Select
                            value={task.status}
                            onValueChange={(value) => handleUpdateTaskStatus(task.id, value)}
                          >
                            <SelectTrigger className="w-32 h-8">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="pending">Pendiente</SelectItem>
                              <SelectItem value="in_progress">En Progreso</SelectItem>
                              <SelectItem value="completed">Completada</SelectItem>
                            </SelectContent>
                          </Select>
                          <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => handleDeleteTask(task.id)}>
                            <Trash2 className="h-3 w-3 text-red-500" />
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                {tasks.length > 0 && (
                  <div className="flex justify-between text-sm bg-slate-50 p-2 rounded">
                    <span>Total estimado: {tasks.reduce((a, t) => a + (t.estimated_hours || 0), 0)}h</span>
                    <span>Costo estimado: {formatCurrency(tasks.reduce((a, t) => a + (t.estimated_cost || 0), 0))}</span>
                  </div>
                )}
              </div>

              {/* Dates */}
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 bg-slate-50 rounded-sm">
                  <div className="text-sm text-muted-foreground">Fecha de Inicio</div>
                  <div className="font-medium">{formatDate(selectedProject.start_date) || "No definida"}</div>
                </div>
                <div className="p-4 bg-slate-50 rounded-sm">
                  <div className="text-sm text-muted-foreground">Fecha Compromiso</div>
                  <div className="font-medium">{formatDate(selectedProject.commitment_date) || "No definida"}</div>
                </div>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setDetailDialogOpen(false)}>
              Cerrar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Create Task Dialog */}
      <Dialog open={taskDialogOpen} onOpenChange={setTaskDialogOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <form onSubmit={handleCreateTask}>
            <DialogHeader>
              <DialogTitle>Nueva Tarea</DialogTitle>
              <DialogDescription>
                Proyecto: {selectedProject?.name}
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid gap-2">
                <Label>Nombre de la Tarea *</Label>
                <Input
                  value={taskForm.name}
                  onChange={(e) => setTaskForm({ ...taskForm, name: e.target.value })}
                  placeholder="Ej: Instalación de estructura"
                  required
                />
              </div>
              <div className="grid gap-2">
                <Label>Descripción</Label>
                <Textarea
                  value={taskForm.description}
                  onChange={(e) => setTaskForm({ ...taskForm, description: e.target.value })}
                  placeholder="Detalles de la tarea..."
                  rows={2}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="grid gap-2">
                  <Label>Horas Estimadas</Label>
                  <Input
                    type="number"
                    step="0.5"
                    value={taskForm.estimated_hours}
                    onChange={(e) => setTaskForm({ ...taskForm, estimated_hours: e.target.value })}
                    placeholder="0"
                  />
                </div>
                <div className="grid gap-2">
                  <Label>Costo Estimado</Label>
                  <Input
                    type="number"
                    value={taskForm.estimated_cost}
                    onChange={(e) => setTaskForm({ ...taskForm, estimated_cost: e.target.value })}
                    placeholder="0.00"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="grid gap-2">
                  <Label>Fecha Límite</Label>
                  <Input
                    type="date"
                    value={taskForm.due_date}
                    onChange={(e) => setTaskForm({ ...taskForm, due_date: e.target.value })}
                  />
                </div>
                <div className="grid gap-2">
                  <Label>Asignar a</Label>
                  <Select
                    value={taskForm.assigned_to}
                    onValueChange={(value) => setTaskForm({ ...taskForm, assigned_to: value })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Sin asignar" />
                    </SelectTrigger>
                    <SelectContent>
                      {users.map((u) => (
                        <SelectItem key={u.id} value={u.id}>{u.full_name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setTaskDialogOpen(false)}>Cancelar</Button>
              <Button type="submit" className="btn-industrial">Crear Tarea</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Projects;
