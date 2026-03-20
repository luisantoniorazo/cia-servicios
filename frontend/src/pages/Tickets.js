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
  Plus,
  Camera,
  Send,
  Clock,
  CheckCircle,
  AlertTriangle,
  XCircle,
  MessageSquare,
  Loader2,
  Image as ImageIcon,
  X,
  Paperclip,
  FileText,
  Download,
  File,
} from "lucide-react";

const PRIORITIES = [
  { value: "low", label: "Baja", color: "bg-slate-500" },
  { value: "medium", label: "Media", color: "bg-amber-500" },
  { value: "high", label: "Alta", color: "bg-orange-500" },
  { value: "critical", label: "Crítica", color: "bg-red-500" },
];

const CATEGORIES = [
  { value: "general", label: "General" },
  { value: "bug", label: "Error/Bug" },
  { value: "feature", label: "Solicitud de Función" },
  { value: "billing", label: "Facturación" },
];

const STATUS_CONFIG = {
  open: { label: "Abierto", color: "bg-blue-500", icon: Clock },
  in_progress: { label: "En Progreso", color: "bg-amber-500", icon: Loader2 },
  resolved: { label: "Resuelto", color: "bg-emerald-500", icon: CheckCircle },
  closed: { label: "Cerrado", color: "bg-slate-500", icon: XCircle },
};

export const Tickets = () => {
  const { api, company, user } = useAuth();
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [detailDialogOpen, setDetailDialogOpen] = useState(false);
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [newComment, setNewComment] = useState("");
  const [commentAttachments, setCommentAttachments] = useState([]);
  const [submitting, setSubmitting] = useState(false);
  const [screenshots, setScreenshots] = useState([]);
  const [formData, setFormData] = useState({
    title: "",
    description: "",
    priority: "medium",
    category: "general",
  });

  const fetchTickets = useCallback(async () => {
    try {
      const response = await api.get(`/tickets?company_id=${company.id}`);
      setTickets(response.data);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  }, [api, company?.id]);

  useEffect(() => {
    if (company?.id) {
      fetchTickets();
    }
  }, [fetchTickets, company?.id]);

  // Auto-refresh ticket detail when AI is processing
  useEffect(() => {
    let interval;
    if (selectedTicket?.ai_processing) {
      interval = setInterval(async () => {
        try {
          const response = await api.get(`/tickets/${selectedTicket.id}`);
          setSelectedTicket(response.data);
          // Also refresh the list
          fetchTickets();
        } catch (error) {
          console.error("Error refreshing ticket:", error);
        }
      }, 5000); // Refresh every 5 seconds
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [selectedTicket?.ai_processing, selectedTicket?.id, api, fetchTickets]);

  const handleScreenshotCapture = async () => {
    try {
      // Use clipboard API to paste screenshot
      const clipboardItems = await navigator.clipboard.read();
      for (const item of clipboardItems) {
        if (item.types.includes("image/png")) {
          const blob = await item.getType("image/png");
          const reader = new FileReader();
          reader.onloadend = () => {
            setScreenshots(prev => [...prev, reader.result]);
            toast.success("Screenshot agregado");
          };
          reader.readAsDataURL(blob);
          return;
        }
      }
      toast.info("Copia un screenshot al portapapeles (Ctrl+V) y luego presiona este botón");
    } catch (error) {
      toast.info("Para agregar un screenshot: 1. Toma una captura (Win+Shift+S), 2. Presiona este botón");
    }
  };

  const handleFileUpload = (e) => {
    const files = e.target.files;
    if (!files) return;
    
    Array.from(files).forEach(file => {
      if (file.type.startsWith("image/")) {
        const reader = new FileReader();
        reader.onloadend = () => {
          setScreenshots(prev => [...prev, reader.result]);
        };
        reader.readAsDataURL(file);
      }
    });
  };

  const removeScreenshot = (index) => {
    setScreenshots(prev => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const response = await api.post("/tickets", {
        company_id: company.id,
        ...formData,
        screenshots: screenshots.map(s => s.split(",")[1] || s), // Remove data URL prefix
      });
      toast.success(
        <div>
          <p className="font-semibold">Ticket creado exitosamente</p>
          <p className="text-sm">Nuestro asistente de IA está analizando tu solicitud...</p>
        </div>,
        { duration: 5000 }
      );
      setDialogOpen(false);
      resetForm();
      fetchTickets();
      
      // Open the newly created ticket to see AI processing
      setTimeout(() => {
        openTicketDetail(response.data);
      }, 1000);
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Error al crear ticket"));
    } finally {
      setSubmitting(false);
    }
  };

  const handleAddComment = async () => {
    if (!newComment.trim() && commentAttachments.length === 0) return;
    if (!selectedTicket) return;
    
    try {
      // Process attachments
      const attachments = commentAttachments.map(att => ({
        filename: att.name,
        file_type: att.type,
        file_data: att.data.split(",")[1] || att.data  // Remove data URL prefix
      }));
      
      await api.post(`/tickets/${selectedTicket.id}/comment`, { 
        text: newComment,
        attachments: attachments
      });
      toast.success("Comentario agregado");
      setNewComment("");
      setCommentAttachments([]);
      // Refresh ticket details
      const response = await api.get(`/tickets/${selectedTicket.id}`);
      setSelectedTicket(response.data);
      fetchTickets();
    } catch (error) {
      toast.error("Error al agregar comentario");
    }
  };

  const handleCommentFileUpload = (e) => {
    const files = Array.from(e.target.files);
    files.forEach(file => {
      const reader = new FileReader();
      reader.onload = (event) => {
        setCommentAttachments(prev => [...prev, {
          name: file.name,
          type: file.type,
          data: event.target.result,
          size: file.size
        }]);
      };
      reader.readAsDataURL(file);
    });
    e.target.value = ""; // Reset input
  };

  const removeCommentAttachment = (index) => {
    setCommentAttachments(prev => prev.filter((_, i) => i !== index));
  };

  const resetForm = () => {
    setFormData({
      title: "",
      description: "",
      priority: "medium",
      category: "general",
    });
    setScreenshots([]);
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

  const handleConfirmResolution = async (resolved) => {
    try {
      await api.post(`/tickets/${selectedTicket.id}/confirm-resolution`, { resolved });
      toast.success(resolved ? "¡Ticket cerrado exitosamente!" : "Ticket escalado para revisión");
      // Refresh ticket details
      const response = await api.get(`/tickets/${selectedTicket.id}`);
      setSelectedTicket(response.data);
      fetchTickets();
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Error al confirmar"));
    }
  };

  const handleCloseTicket = async () => {
    try {
      await api.post(`/tickets/${selectedTicket.id}/confirm-resolution`, { resolved: true });
      toast.success("¡Ticket cerrado exitosamente!");
      // Refresh ticket details
      const response = await api.get(`/tickets/${selectedTicket.id}`);
      setSelectedTicket(response.data);
      fetchTickets();
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Error al cerrar ticket"));
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

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="tickets-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Soporte Técnico</h1>
          <p className="text-muted-foreground">Reporta problemas y da seguimiento a tus tickets</p>
        </div>
        <Button onClick={() => setDialogOpen(true)} className="btn-industrial" data-testid="new-ticket-btn">
          <Plus className="mr-2 h-4 w-4" />
          Nuevo Ticket
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-sm bg-blue-100">
                <TicketIcon className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <div className="text-2xl font-bold">{tickets.length}</div>
                <div className="text-sm text-muted-foreground">Total Tickets</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-sm bg-amber-100">
                <Clock className="h-5 w-5 text-amber-600" />
              </div>
              <div>
                <div className="text-2xl font-bold">{tickets.filter(t => t.status === "open").length}</div>
                <div className="text-sm text-muted-foreground">Abiertos</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-sm bg-orange-100">
                <Loader2 className="h-5 w-5 text-orange-600" />
              </div>
              <div>
                <div className="text-2xl font-bold">{tickets.filter(t => t.status === "in_progress").length}</div>
                <div className="text-sm text-muted-foreground">En Progreso</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-sm bg-emerald-100">
                <CheckCircle className="h-5 w-5 text-emerald-600" />
              </div>
              <div>
                <div className="text-2xl font-bold">{tickets.filter(t => ["resolved", "closed"].includes(t.status)).length}</div>
                <div className="text-sm text-muted-foreground">Resueltos</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tickets Table */}
      <Card>
        <CardHeader>
          <CardTitle>Mis Tickets</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="rounded-sm border overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow className="bg-slate-50">
                  <TableHead>Ticket</TableHead>
                  <TableHead>Título</TableHead>
                  <TableHead>Categoría</TableHead>
                  <TableHead>Prioridad</TableHead>
                  <TableHead>Estado</TableHead>
                  <TableHead>Fecha</TableHead>
                  <TableHead></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {tickets.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center py-8 text-muted-foreground">
                      No tienes tickets. Crea uno para reportar un problema.
                    </TableCell>
                  </TableRow>
                ) : (
                  tickets.map((ticket) => (
                    <TableRow key={ticket.id}>
                      <TableCell className="font-mono text-sm">{ticket.ticket_number}</TableCell>
                      <TableCell>
                        <div className="font-medium">{ticket.title}</div>
                        <div className="text-sm text-muted-foreground truncate max-w-[200px]">
                          {ticket.description}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">
                          {CATEGORIES.find(c => c.value === ticket.category)?.label || ticket.category}
                        </Badge>
                      </TableCell>
                      <TableCell>{getPriorityBadge(ticket.priority)}</TableCell>
                      <TableCell>{getStatusBadge(ticket.status)}</TableCell>
                      <TableCell>{formatDate(ticket.created_at)}</TableCell>
                      <TableCell>
                        <Button variant="ghost" size="sm" onClick={() => openTicketDetail(ticket)}>
                          <MessageSquare className="h-4 w-4 mr-1" />
                          Ver
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

      {/* New Ticket Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="sm:max-w-[600px]">
          <form onSubmit={handleSubmit}>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <TicketIcon className="h-5 w-5" />
                Reportar un Problema
              </DialogTitle>
              <DialogDescription>
                Describe el problema que estás experimentando. Incluye capturas de pantalla si es posible.
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid gap-2">
                <Label>Título del Problema *</Label>
                <Input
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  placeholder="Ej: Error al generar PDF de cotización"
                  required
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="grid gap-2">
                  <Label>Categoría</Label>
                  <Select
                    value={formData.category}
                    onValueChange={(value) => setFormData({ ...formData, category: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {CATEGORIES.map(cat => (
                        <SelectItem key={cat.value} value={cat.value}>{cat.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid gap-2">
                  <Label>Prioridad</Label>
                  <Select
                    value={formData.priority}
                    onValueChange={(value) => setFormData({ ...formData, priority: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {PRIORITIES.map(pri => (
                        <SelectItem key={pri.value} value={pri.value}>{pri.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="grid gap-2">
                <Label>Descripción Detallada *</Label>
                <Textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Describe el problema con el mayor detalle posible: qué estabas haciendo, qué error apareció, etc."
                  rows={4}
                  required
                />
              </div>
              
              {/* Screenshots Section */}
              <div className="grid gap-2">
                <Label className="flex items-center gap-2">
                  <Camera className="h-4 w-4" />
                  Capturas de Pantalla
                </Label>
                <div className="flex items-center gap-2">
                  <Button type="button" variant="outline" onClick={handleScreenshotCapture}>
                    <Camera className="mr-2 h-4 w-4" />
                    Pegar Screenshot
                  </Button>
                  <span className="text-sm text-muted-foreground">o</span>
                  <label className="cursor-pointer">
                    <Input
                      type="file"
                      accept="image/*"
                      multiple
                      className="hidden"
                      onChange={handleFileUpload}
                    />
                    <Button type="button" variant="outline" asChild>
                      <span>
                        <ImageIcon className="mr-2 h-4 w-4" />
                        Subir Imagen
                      </span>
                    </Button>
                  </label>
                </div>
                
                {screenshots.length > 0 && (
                  <div className="flex flex-wrap gap-2 mt-2">
                    {screenshots.map((screenshot, index) => (
                      <div key={index} className="relative">
                        <img
                          src={screenshot}
                          alt={`Screenshot ${index + 1}`}
                          className="h-20 w-auto rounded border"
                        />
                        <button
                          type="button"
                          onClick={() => removeScreenshot(index)}
                          className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full p-1"
                        >
                          <X className="h-3 w-3" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => { setDialogOpen(false); resetForm(); }}>
                Cancelar
              </Button>
              <Button type="submit" className="btn-industrial" disabled={submitting}>
                {submitting ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Send className="mr-2 h-4 w-4" />}
                Enviar Ticket
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Ticket Detail Dialog */}
      <Dialog open={detailDialogOpen} onOpenChange={setDetailDialogOpen}>
        <DialogContent className="sm:max-w-[700px] max-h-[80vh] overflow-y-auto">
          {selectedTicket && (
            <>
              <DialogHeader>
                <DialogTitle className="flex items-center justify-between">
                  <span>{selectedTicket.ticket_number}</span>
                  {getStatusBadge(selectedTicket.status)}
                </DialogTitle>
                <DialogDescription>{selectedTicket.title}</DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                {/* Ticket Info */}
                <div className="grid grid-cols-3 gap-4 text-sm">
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
                </div>
                
                <Separator />
                
                {/* Description */}
                <div>
                  <h4 className="font-semibold mb-2">Descripción</h4>
                  <p className="text-sm text-muted-foreground whitespace-pre-wrap">{selectedTicket.description}</p>
                </div>
                
                {/* Screenshots */}
                {selectedTicket.screenshots?.length > 0 && (
                  <div>
                    <h4 className="font-semibold mb-2">Capturas de Pantalla</h4>
                    <div className="flex flex-wrap gap-2">
                      {selectedTicket.screenshots.map((screenshot, index) => (
                        <img
                          key={index}
                          src={`data:image/png;base64,${screenshot}`}
                          alt={`Screenshot ${index + 1}`}
                          className="h-32 w-auto rounded border cursor-pointer hover:opacity-80"
                          onClick={() => window.open(`data:image/png;base64,${screenshot}`, "_blank")}
                        />
                      ))}
                    </div>
                  </div>
                )}
                
                {/* Processing Indicator - Humanized */}
                {selectedTicket.ai_processing && (
                  <div className="p-3 bg-blue-50 rounded-sm border border-blue-200 flex items-center gap-3">
                    <Loader2 className="h-5 w-5 text-blue-600 animate-spin" />
                    <div>
                      <p className="text-sm font-medium text-blue-800">Revisando tu caso...</p>
                      <p className="text-xs text-blue-600">Nuestro equipo está trabajando en tu solicitud</p>
                    </div>
                  </div>
                )}
                
                {/* Resolution */}
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
                  <div className="space-y-3 max-h-[250px] overflow-y-auto">
                    {selectedTicket.comments?.length === 0 ? (
                      <p className="text-sm text-muted-foreground">No hay comentarios aún</p>
                    ) : (
                      selectedTicket.comments?.filter(c => !c.is_internal).map((comment) => (
                        <div
                          key={comment.id}
                          className={`p-3 rounded-sm ${
                            comment.author_id === "support-agent" 
                              ? "bg-blue-50 border-l-4 border-l-blue-500" 
                              : comment.author_id === "system" 
                                ? "bg-slate-50 border-l-4 border-l-slate-400"
                                : comment.is_admin 
                                  ? "bg-blue-50 border-l-4 border-l-blue-500" 
                                  : "bg-slate-50"
                          }`}
                        >
                          <div className="flex items-center justify-between text-xs mb-1">
                            <span className="font-medium flex items-center gap-2">
                              {comment.author_name}
                              {(comment.author_id === "support-agent" || comment.is_admin) && (
                                <Badge className="bg-blue-500 text-xs">Soporte</Badge>
                              )}
                            </span>
                            <span className="text-muted-foreground">{formatDate(comment.created_at)}</span>
                          </div>
                          <p className="text-sm whitespace-pre-wrap">{comment.text}</p>
                          
                          {/* Attachments */}
                          {comment.attachments && comment.attachments.length > 0 && (
                            <div className="mt-2 flex flex-wrap gap-2">
                              {comment.attachments.map((att, idx) => (
                                <div key={idx} className="relative">
                                  {att.file_type?.startsWith("image/") ? (
                                    <a 
                                      href={`data:${att.file_type};base64,${att.file_data}`} 
                                      target="_blank" 
                                      rel="noopener noreferrer"
                                      className="block"
                                    >
                                      <img 
                                        src={`data:${att.file_type};base64,${att.file_data}`} 
                                        alt={att.filename}
                                        className="h-20 w-auto rounded border hover:opacity-90 transition-opacity cursor-pointer"
                                      />
                                    </a>
                                  ) : (
                                    <a 
                                      href={`data:${att.file_type};base64,${att.file_data}`}
                                      download={att.filename}
                                      className="flex items-center gap-2 p-2 bg-white rounded border text-xs hover:bg-slate-50"
                                    >
                                      <FileText className="h-4 w-4 text-blue-500" />
                                      <span className="max-w-[120px] truncate">{att.filename}</span>
                                      <Download className="h-3 w-3 text-slate-400" />
                                    </a>
                                  )}
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      ))
                    )}
                  </div>
                  
                  {/* Close Ticket Button - Always visible when not closed */}
                  {!["closed", "resolved"].includes(selectedTicket.status) && (
                    <div className="flex justify-end mt-3 pt-3 border-t">
                      <Button 
                        variant="outline"
                        className="text-green-700 border-green-300 hover:bg-green-50"
                        onClick={() => handleCloseTicket()}
                      >
                        <CheckCircle className="h-4 w-4 mr-2" />
                        Cerrar Ticket (Problema Resuelto)
                      </Button>
                    </div>
                  )}
                  
                  {/* Add Comment with Attachments - Only if not closed */}
                  {!["closed", "resolved"].includes(selectedTicket.status) && (
                    <div className="space-y-2 mt-3">
                      {/* Attachment Previews */}
                      {commentAttachments.length > 0 && (
                        <div className="flex flex-wrap gap-2 p-2 bg-slate-50 rounded">
                          {commentAttachments.map((att, index) => (
                            <div key={index} className="flex items-center gap-2 bg-white p-2 rounded border text-xs">
                              {att.type.startsWith("image/") ? (
                                <img src={att.data} alt={att.name} className="h-8 w-8 object-cover rounded" />
                              ) : (
                                <File className="h-4 w-4 text-slate-500" />
                              )}
                              <span className="max-w-[100px] truncate">{att.name}</span>
                              <button onClick={() => removeCommentAttachment(index)} className="text-red-500 hover:text-red-700">
                                <X className="h-3 w-3" />
                              </button>
                            </div>
                          ))}
                        </div>
                      )}
                      
                      <div className="flex gap-2">
                        <Input
                          value={newComment}
                          onChange={(e) => setNewComment(e.target.value)}
                          placeholder="Escribe un comentario..."
                          onKeyPress={(e) => e.key === "Enter" && !e.shiftKey && handleAddComment()}
                          className="flex-1"
                        />
                        <input
                          type="file"
                          id="comment-file-upload"
                          multiple
                          accept="image/*,.pdf,.doc,.docx,.xls,.xlsx,.txt"
                          onChange={handleCommentFileUpload}
                          className="hidden"
                        />
                        <Button 
                          variant="outline" 
                          onClick={() => document.getElementById("comment-file-upload").click()}
                          title="Adjuntar archivo"
                        >
                          <Paperclip className="h-4 w-4" />
                        </Button>
                        <Button 
                          onClick={handleAddComment} 
                          disabled={!newComment.trim() && commentAttachments.length === 0}
                        >
                          <Send className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  )}
                  
                  {/* Closed ticket message */}
                  {["closed", "resolved"].includes(selectedTicket.status) && (
                    <div className="mt-4 p-4 bg-green-50 rounded-lg border border-green-200 text-center">
                      <CheckCircle className="h-8 w-8 text-green-600 mx-auto mb-2" />
                      <p className="font-semibold text-green-800">Ticket Cerrado</p>
                      <p className="text-sm text-green-600">Este ticket ha sido resuelto y cerrado. Si necesitas ayuda adicional, puedes crear un nuevo ticket.</p>
                    </div>
                  )}
                </div>
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Tickets;
