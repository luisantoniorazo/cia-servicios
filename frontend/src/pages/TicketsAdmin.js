import React, { useState, useEffect, useCallback } from "react";
import { useAuth } from "../context/AuthContext";
import { formatDate, getApiErrorMessage } from "../lib/utils";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import { Badge } from "../components/ui/badge";
import { Separator } from "../components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
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
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../components/ui/table";
import { toast } from "sonner";
import {
  TicketIcon,
  Clock,
  CheckCircle,
  AlertTriangle,
  XCircle,
  MessageSquare,
  Loader2,
  ArrowLeft,
  Send,
  Building2,
  AlertCircle,
  Brain,
  Sparkles,
} from "lucide-react";
import { useNavigate } from "react-router-dom";

const PRIORITIES = [
  { value: "low", label: "Baja", color: "bg-slate-500" },
  { value: "medium", label: "Media", color: "bg-amber-500" },
  { value: "high", label: "Alta", color: "bg-orange-500" },
  { value: "critical", label: "Crítica", color: "bg-red-500" },
];

const CATEGORIES = [
  { value: "general", label: "General" },
  { value: "bug", label: "Error/Bug" },
  { value: "feature", label: "Solicitud" },
  { value: "billing", label: "Facturación" },
];

const STATUS_CONFIG = {
  open: { label: "Abierto", color: "bg-blue-500", icon: Clock },
  in_progress: { label: "En Progreso", color: "bg-amber-500", icon: Loader2 },
  resolved: { label: "Resuelto", color: "bg-emerald-500", icon: CheckCircle },
  closed: { label: "Cerrado", color: "bg-slate-500", icon: XCircle },
};

export const TicketsAdmin = () => {
  const { api } = useAuth();
  const navigate = useNavigate();
  const [tickets, setTickets] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [detailDialogOpen, setDetailDialogOpen] = useState(false);
  const [newComment, setNewComment] = useState("");
  const [resolutionNotes, setResolutionNotes] = useState("");
  const [activeTab, setActiveTab] = useState("all");
  const [diagnosing, setDiagnosing] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const [ticketsRes, statsRes] = await Promise.all([
        api.get("/tickets"),
        api.get("/super-admin/tickets/stats"),
      ]);
      setTickets(ticketsRes.data);
      setStats(statsRes.data);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  }, [api]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleStatusChange = async (ticketId, newStatus) => {
    try {
      let url = `/tickets/${ticketId}/status?status=${newStatus}`;
      if (newStatus === "resolved" && resolutionNotes) {
        url += `&resolution_notes=${encodeURIComponent(resolutionNotes)}`;
      }
      await api.patch(url);
      toast.success(`Ticket actualizado a ${STATUS_CONFIG[newStatus]?.label}`);
      setResolutionNotes("");
      fetchData();
      // Refresh selected ticket
      if (selectedTicket?.id === ticketId) {
        const response = await api.get(`/tickets/${ticketId}`);
        setSelectedTicket(response.data);
      }
    } catch (error) {
      toast.error("Error al actualizar ticket");
    }
  };

  const handleAddComment = async () => {
    if (!newComment.trim() || !selectedTicket) return;
    try {
      await api.post(`/tickets/${selectedTicket.id}/comment`, { text: newComment });
      toast.success("Comentario agregado");
      setNewComment("");
      const response = await api.get(`/tickets/${selectedTicket.id}`);
      setSelectedTicket(response.data);
      fetchData();
    } catch (error) {
      toast.error("Error al agregar comentario");
    }
  };

  const openTicketDetail = async (ticket) => {
    try {
      const response = await api.get(`/tickets/${ticket.id}`);
      setSelectedTicket(response.data);
      setDetailDialogOpen(true);
    } catch (error) {
      toast.error("Error al cargar ticket");
    }
  };

  const handleAIDiagnosis = async () => {
    if (!selectedTicket) return;
    setDiagnosing(true);
    try {
      const response = await api.post(`/tickets/${selectedTicket.id}/ai-diagnosis`);
      toast.success("Diagnóstico generado exitosamente");
      // Refresh ticket to show diagnosis
      const ticketRes = await api.get(`/tickets/${selectedTicket.id}`);
      setSelectedTicket(ticketRes.data);
    } catch (error) {
      toast.error("Error al generar diagnóstico");
    } finally {
      setDiagnosing(false);
    }
  };

  const getPriorityBadge = (priority) => {
    const config = PRIORITIES.find(p => p.value === priority) || PRIORITIES[1];
    return <Badge className={`${config.color} text-white`}>{config.label}</Badge>;
  };

  const getStatusBadge = (status) => {
    const config = STATUS_CONFIG[status] || STATUS_CONFIG.open;
    const Icon = config.icon;
    return (
      <Badge className={`${config.color} text-white`}>
        <Icon className="h-3 w-3 mr-1" />
        {config.label}
      </Badge>
    );
  };

  const filteredTickets = tickets.filter(ticket => {
    if (activeTab === "all") return true;
    if (activeTab === "pending") return ["open", "in_progress"].includes(ticket.status);
    if (activeTab === "critical") return ticket.priority === "critical" && !["closed", "resolved"].includes(ticket.status);
    return ticket.status === activeTab;
  });

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-amber-500" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button
              variant="outline"
              size="icon"
              onClick={() => navigate("/admin-portal/dashboard")}
              className="border-slate-600 text-slate-300"
            >
              <ArrowLeft className="h-4 w-4" />
            </Button>
            <div>
              <h1 className="text-2xl font-bold text-white flex items-center gap-2">
                <TicketIcon className="h-6 w-6 text-amber-500" />
                Gestión de Tickets
              </h1>
              <p className="text-slate-400">Administra los tickets de soporte de todas las empresas</p>
            </div>
          </div>
        </div>

        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <Card className="bg-slate-800/50 border-slate-700">
              <CardContent className="pt-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-sm bg-blue-500/20">
                    <TicketIcon className="h-5 w-5 text-blue-400" />
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-white">{stats.total}</div>
                    <div className="text-sm text-slate-400">Total</div>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card className="bg-slate-800/50 border-slate-700">
              <CardContent className="pt-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-sm bg-amber-500/20">
                    <Clock className="h-5 w-5 text-amber-400" />
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-white">{stats.open}</div>
                    <div className="text-sm text-slate-400">Abiertos</div>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card className="bg-slate-800/50 border-slate-700">
              <CardContent className="pt-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-sm bg-orange-500/20">
                    <Loader2 className="h-5 w-5 text-orange-400" />
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-white">{stats.in_progress}</div>
                    <div className="text-sm text-slate-400">En Progreso</div>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card className="bg-slate-800/50 border-slate-700">
              <CardContent className="pt-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-sm bg-red-500/20">
                    <AlertCircle className="h-5 w-5 text-red-400" />
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-white">{stats.critical_pending}</div>
                    <div className="text-sm text-slate-400">Críticos</div>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card className="bg-slate-800/50 border-slate-700">
              <CardContent className="pt-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-sm bg-emerald-500/20">
                    <CheckCircle className="h-5 w-5 text-emerald-400" />
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-white">{stats.resolved + stats.closed}</div>
                    <div className="text-sm text-slate-400">Resueltos</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Tickets Table with Tabs */}
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <Tabs value={activeTab} onValueChange={setActiveTab}>
              <TabsList className="bg-slate-700">
                <TabsTrigger value="all" className="data-[state=active]:bg-amber-500">Todos</TabsTrigger>
                <TabsTrigger value="pending" className="data-[state=active]:bg-amber-500">Pendientes</TabsTrigger>
                <TabsTrigger value="critical" className="data-[state=active]:bg-amber-500">Críticos</TabsTrigger>
                <TabsTrigger value="resolved" className="data-[state=active]:bg-amber-500">Resueltos</TabsTrigger>
                <TabsTrigger value="closed" className="data-[state=active]:bg-amber-500">Cerrados</TabsTrigger>
              </TabsList>
            </Tabs>
          </CardHeader>
          <CardContent>
            <div className="rounded-sm border border-slate-700 overflow-hidden">
              <Table>
                <TableHeader>
                  <TableRow className="bg-slate-800/50 border-slate-700">
                    <TableHead className="text-slate-300">Ticket</TableHead>
                    <TableHead className="text-slate-300">Empresa</TableHead>
                    <TableHead className="text-slate-300">Título</TableHead>
                    <TableHead className="text-slate-300">Prioridad</TableHead>
                    <TableHead className="text-slate-300">Estado</TableHead>
                    <TableHead className="text-slate-300">Fecha</TableHead>
                    <TableHead className="text-slate-300"></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredTickets.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={7} className="text-center py-8 text-slate-400">
                        No hay tickets en esta categoría
                      </TableCell>
                    </TableRow>
                  ) : (
                    filteredTickets.map((ticket) => (
                      <TableRow key={ticket.id} className="border-slate-700 hover:bg-slate-700/30">
                        <TableCell className="font-mono text-sm text-slate-300">{ticket.ticket_number}</TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2 text-slate-300">
                            <Building2 className="h-4 w-4 text-slate-500" />
                            {ticket.company_name}
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="text-white font-medium">{ticket.title}</div>
                          <div className="text-sm text-slate-400 truncate max-w-[200px]">
                            {ticket.description}
                          </div>
                        </TableCell>
                        <TableCell>{getPriorityBadge(ticket.priority)}</TableCell>
                        <TableCell>{getStatusBadge(ticket.status)}</TableCell>
                        <TableCell className="text-slate-400">{formatDate(ticket.created_at)}</TableCell>
                        <TableCell>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => openTicketDetail(ticket)}
                            className="text-amber-400 hover:text-amber-300"
                          >
                            <MessageSquare className="h-4 w-4 mr-1" />
                            Atender
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>

        {/* Ticket Detail Dialog */}
        <Dialog open={detailDialogOpen} onOpenChange={setDetailDialogOpen}>
          <DialogContent className="sm:max-w-[800px] max-h-[85vh] overflow-y-auto">
            {selectedTicket && (
              <>
                <DialogHeader>
                  <DialogTitle className="flex items-center justify-between">
                    <span className="text-lg">{selectedTicket.ticket_number}</span>
                    {getStatusBadge(selectedTicket.status)}
                  </DialogTitle>
                  <DialogDescription className="text-left">
                    <span className="font-medium">{selectedTicket.title}</span>
                    <br />
                    <span className="text-xs">De: {selectedTicket.company_name} | {selectedTicket.created_by_name}</span>
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4 py-4">
                  {/* Status Actions */}
                  <div className="flex items-center gap-2 p-3 bg-slate-100 rounded-sm">
                    <span className="text-sm font-medium">Cambiar Estado:</span>
                    <Button
                      size="sm"
                      variant={selectedTicket.status === "in_progress" ? "default" : "outline"}
                      onClick={() => handleStatusChange(selectedTicket.id, "in_progress")}
                      className="bg-amber-500 hover:bg-amber-600"
                    >
                      En Progreso
                    </Button>
                    <Button
                      size="sm"
                      variant={selectedTicket.status === "resolved" ? "default" : "outline"}
                      onClick={() => handleStatusChange(selectedTicket.id, "resolved")}
                      className="bg-emerald-500 hover:bg-emerald-600"
                    >
                      Resolver
                    </Button>
                    <Button
                      size="sm"
                      variant={selectedTicket.status === "closed" ? "default" : "outline"}
                      onClick={() => handleStatusChange(selectedTicket.id, "closed")}
                      className="bg-slate-500 hover:bg-slate-600"
                    >
                      Cerrar
                    </Button>
                  </div>

                  {/* Resolution Notes */}
                  {!["resolved", "closed"].includes(selectedTicket.status) && (
                    <div className="grid gap-2">
                      <Label>Notas de Resolución (opcional)</Label>
                      <Textarea
                        value={resolutionNotes}
                        onChange={(e) => setResolutionNotes(e.target.value)}
                        placeholder="Describe cómo se resolvió el problema..."
                        rows={2}
                      />
                    </div>
                  )}

                  {/* Ticket Info */}
                  <div className="grid grid-cols-4 gap-4 text-sm">
                    <div>
                      <div className="text-muted-foreground">Categoría</div>
                      <Badge variant="outline">{CATEGORIES.find(c => c.value === selectedTicket.category)?.label}</Badge>
                    </div>
                    <div>
                      <div className="text-muted-foreground">Prioridad</div>
                      {getPriorityBadge(selectedTicket.priority)}
                    </div>
                    <div>
                      <div className="text-muted-foreground">Creado</div>
                      <div>{formatDate(selectedTicket.created_at)}</div>
                    </div>
                    <div>
                      <div className="text-muted-foreground">Reportado por</div>
                      <div>{selectedTicket.created_by_name}</div>
                    </div>
                  </div>

                  <Separator />

                  {/* Description */}
                  <div>
                    <h4 className="font-semibold mb-2">Descripción del Problema</h4>
                    <div className="p-3 bg-slate-50 rounded-sm">
                      <p className="text-sm whitespace-pre-wrap">{selectedTicket.description}</p>
                    </div>
                  </div>

                  {/* AI Diagnosis Section */}
                  <div className="p-4 bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg border border-purple-200">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <Brain className="h-5 w-5 text-purple-600" />
                        <h4 className="font-semibold text-purple-900">Diagnóstico con IA</h4>
                      </div>
                      <Button
                        size="sm"
                        onClick={handleAIDiagnosis}
                        disabled={diagnosing}
                        className="bg-purple-600 hover:bg-purple-700 gap-2"
                      >
                        {diagnosing ? (
                          <>
                            <Loader2 className="h-4 w-4 animate-spin" />
                            Analizando...
                          </>
                        ) : (
                          <>
                            <Sparkles className="h-4 w-4" />
                            {selectedTicket.ai_diagnosis ? "Re-analizar" : "Analizar con IA"}
                          </>
                        )}
                      </Button>
                    </div>
                    {selectedTicket.ai_diagnosis ? (
                      <div className="space-y-2">
                        <div className="p-3 bg-white rounded-md border">
                          <p className="text-sm whitespace-pre-wrap text-slate-700">
                            {selectedTicket.ai_diagnosis.diagnosis}
                          </p>
                        </div>
                        <p className="text-xs text-purple-600">
                          Generado por {selectedTicket.ai_diagnosis.created_by_name} el{" "}
                          {formatDate(selectedTicket.ai_diagnosis.created_at)}
                        </p>
                      </div>
                    ) : (
                      <p className="text-sm text-purple-700">
                        Haz clic en "Analizar con IA" para obtener un diagnóstico automático del problema.
                        El sistema analizará el ticket y sugerirá posibles soluciones.
                      </p>
                    )}
                  </div>

                  {/* Screenshots */}
                  {selectedTicket.screenshots?.length > 0 && (
                    <div>
                      <h4 className="font-semibold mb-2">Capturas de Pantalla ({selectedTicket.screenshots.length})</h4>
                      <div className="flex flex-wrap gap-2">
                        {selectedTicket.screenshots.map((screenshot, index) => (
                          <img
                            key={index}
                            src={`data:image/png;base64,${screenshot}`}
                            alt={`Screenshot ${index + 1}`}
                            className="h-40 w-auto rounded border cursor-pointer hover:opacity-80 transition-opacity"
                            onClick={() => window.open(`data:image/png;base64,${screenshot}`, "_blank")}
                          />
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Resolution Info */}
                  {selectedTicket.resolution_notes && (
                    <div className="p-3 bg-emerald-50 rounded-sm border border-emerald-200">
                      <h4 className="font-semibold text-emerald-800 mb-1">Resolución</h4>
                      <p className="text-sm text-emerald-700">{selectedTicket.resolution_notes}</p>
                      <p className="text-xs text-emerald-600 mt-1">
                        Resuelto por {selectedTicket.resolved_by_name} el {formatDate(selectedTicket.resolved_at)}
                      </p>
                    </div>
                  )}

                  <Separator />

                  {/* Comments */}
                  <div>
                    <h4 className="font-semibold mb-2">Conversación</h4>
                    <div className="space-y-3 max-h-[200px] overflow-y-auto p-2 bg-slate-50 rounded-sm">
                      {selectedTicket.comments?.length === 0 ? (
                        <p className="text-sm text-muted-foreground text-center py-4">No hay comentarios</p>
                      ) : (
                        selectedTicket.comments?.map((comment) => (
                          <div
                            key={comment.id}
                            className={`p-3 rounded-sm ${comment.is_admin ? "bg-blue-100 border-l-4 border-l-blue-500" : "bg-white border"}`}
                          >
                            <div className="flex items-center justify-between text-xs mb-1">
                              <span className="font-medium">
                                {comment.author_name}
                                {comment.is_admin && <Badge className="ml-2 bg-blue-500 text-xs">Admin</Badge>}
                              </span>
                              <span className="text-muted-foreground">{formatDate(comment.created_at)}</span>
                            </div>
                            <p className="text-sm">{comment.text}</p>
                          </div>
                        ))
                      )}
                    </div>

                    {/* Add Admin Comment */}
                    {!["closed"].includes(selectedTicket.status) && (
                      <div className="flex gap-2 mt-3">
                        <Input
                          value={newComment}
                          onChange={(e) => setNewComment(e.target.value)}
                          placeholder="Responder al usuario..."
                          onKeyPress={(e) => e.key === "Enter" && handleAddComment()}
                        />
                        <Button onClick={handleAddComment} disabled={!newComment.trim()} className="bg-blue-500 hover:bg-blue-600">
                          <Send className="h-4 w-4" />
                        </Button>
                      </div>
                    )}
                  </div>
                </div>
              </>
            )}
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
};

export default TicketsAdmin;
