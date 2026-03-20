import React, { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { formatCurrency, formatDate, getStatusColor, getStatusLabel, generateQuoteNumber , getApiErrorMessage } from "../lib/utils";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import { Badge } from "../components/ui/badge";
import { Skeleton } from "../components/ui/skeleton";
import { Checkbox } from "../components/ui/checkbox";
import { Separator } from "../components/ui/separator";
import { SATProductSearch, SATUnitSearch } from "../components/SATSearch";
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
import { toast } from "sonner";
import {
  FileText,
  Plus,
  MoreVertical,
  Eye,
  Edit,
  Trash2,
  CheckCircle,
  XCircle,
  Clock,
  DollarSign,
  PlusCircle,
  MinusCircle,
  Download,
  Loader2,
  Receipt,
  Search,
  X,
  History,
  Ban,
} from "lucide-react";

const QUOTE_STATUSES = [
  { value: "prospect", label: "1. Prospecto" },
  { value: "negotiation", label: "2. Negociación e Ingeniería" },
  { value: "detailed_quote", label: "3. Cotización Detallada" },
  { value: "negotiating", label: "4. Negociación" },
  { value: "under_review", label: "5. En Revisión" },
  { value: "authorized", label: "6. Autorizada" },
  { value: "denied", label: "7. Negada" },
];

export const Quotes = () => {
  const { api, company, user } = useAuth();
  const [quotes, setQuotes] = useState([]);
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [denialDialogOpen, setDenialDialogOpen] = useState(false);
  const [historyDialogOpen, setHistoryDialogOpen] = useState(false);
  const [selectedQuote, setSelectedQuote] = useState(null);
  const [denialReason, setDenialReason] = useState("");
  const [quoteHistory, setQuoteHistory] = useState([]);
  const [searchFilter, setSearchFilter] = useState("");
  const [formData, setFormData] = useState({
    client_id: "",
    quote_number: "",
    title: "",
    description: "",
    status: "prospect",
    show_tax: true,
    custom_field: "",  // Campo personalizable alfanumérico
    custom_field_label: "",  // Etiqueta del campo personalizado
    items: [{ description: "", quantity: 1, unit: "pza", unit_price: 0, total: 0, clave_prod_serv: "", clave_unidad: "" }],
  });

  useEffect(() => {
    if (company?.id) {
      fetchData();
    }
  }, [company]);

  const fetchData = async () => {
    try {
      const [quotesRes, clientsRes] = await Promise.all([
        api.get(`/quotes?company_id=${company.id}`),
        api.get(`/clients?company_id=${company.id}`),
      ]);
      setQuotes(quotesRes.data);
      setClients(clientsRes.data);
    } catch (error) {
      toast.error("Error al cargar cotizaciones");
    } finally {
      setLoading(false);
    }
  };

  const calculateTotals = (items, showTax = true) => {
    const subtotal = items.reduce((acc, item) => acc + (item.quantity * item.unit_price), 0);
    const tax = showTax ? subtotal * 0.16 : 0;
    const total = subtotal + tax;
    return { subtotal, tax, total };
  };

  const handleItemChange = (index, field, value) => {
    const newItems = [...formData.items];
    newItems[index][field] = value;
    if (field === "quantity" || field === "unit_price") {
      newItems[index].total = newItems[index].quantity * newItems[index].unit_price;
    }
    setFormData({ ...formData, items: newItems });
  };

  const addItem = () => {
    setFormData({
      ...formData,
      items: [...formData.items, { description: "", quantity: 1, unit: "pza", unit_price: 0, total: 0, clave_prod_serv: "", clave_unidad: "" }],
    });
  };

  const removeItem = (index) => {
    if (formData.items.length === 1) return;
    const newItems = formData.items.filter((_, i) => i !== index);
    setFormData({ ...formData, items: newItems });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const { subtotal, tax, total } = calculateTotals(formData.items, formData.show_tax);
    try {
      await api.post("/quotes", {
        company_id: company.id,
        ...formData,
        subtotal,
        tax,
        total,
      });
      toast.success("Cotización creada exitosamente");
      setDialogOpen(false);
      resetForm();
      fetchData();
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Error al crear cotización"));
    }
  };

  const handleStatusChange = async (quoteId, status) => {
    // Si es negación, abrir diálogo para pedir motivo
    if (status === "denied") {
      const quote = quotes.find(q => q.id === quoteId);
      setSelectedQuote(quote);
      setDenialReason("");
      setDenialDialogOpen(true);
      return;
    }
    
    try {
      await api.patch(`/quotes/${quoteId}/status?status=${status}`);
      toast.success("Estado actualizado");
      fetchData();
    } catch (error) {
      toast.error("Error al actualizar estado");
    }
  };

  const handleDenyQuote = async () => {
    if (!selectedQuote) return;
    try {
      await api.patch(`/quotes/${selectedQuote.id}/status?status=denied&denial_reason=${encodeURIComponent(denialReason)}`);
      toast.success("Cotización negada");
      setDenialDialogOpen(false);
      setSelectedQuote(null);
      setDenialReason("");
      fetchData();
    } catch (error) {
      toast.error("Error al negar cotización");
    }
  };

  const handleEditQuote = (quote) => {
    setSelectedQuote(quote);
    setFormData({
      client_id: quote.client_id,
      quote_number: quote.quote_number,
      title: quote.title,
      description: quote.description || "",
      status: quote.status,
      show_tax: quote.show_tax !== false,
      items: quote.items || [{ description: "", quantity: 1, unit: "pza", unit_price: 0, total: 0, clave_prod_serv: "", clave_unidad: "" }],
    });
    setEditDialogOpen(true);
  };

  const handleUpdateQuote = async (e) => {
    e.preventDefault();
    if (!selectedQuote) return;
    const { subtotal, tax, total } = calculateTotals(formData.items, formData.show_tax);
    try {
      await api.put(`/quotes/${selectedQuote.id}`, {
        ...formData,
        subtotal,
        tax,
        total,
      });
      toast.success("Cotización actualizada");
      setEditDialogOpen(false);
      setSelectedQuote(null);
      resetForm();
      fetchData();
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Error al actualizar cotización"));
    }
  };

  const handleViewHistory = async (quote) => {
    try {
      const response = await api.get(`/quotes/${quote.id}/history`);
      setQuoteHistory(response.data.history || []);
      setSelectedQuote(quote);
      setHistoryDialogOpen(true);
    } catch (error) {
      toast.error("Error al cargar historial");
    }
  };

  const handleDelete = async (quoteId) => {
    if (!window.confirm("¿Estás seguro de eliminar esta cotización?")) return;
    try {
      await api.delete(`/quotes/${quoteId}`);
      toast.success("Cotización eliminada");
      fetchData();
    } catch (error) {
      toast.error("Error al eliminar cotización");
    }
  };

  const handleDownloadPDF = async (quoteId) => {
    try {
      toast.info("Generando PDF...");
      const response = await api.get(`/pdf/quote/${quoteId}`);
      const { filename, content } = response.data;
      
      // Convert base64 to blob and download
      const byteCharacters = atob(content);
      const byteNumbers = new Array(byteCharacters.length);
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
      }
      const byteArray = new Uint8Array(byteNumbers);
      const blob = new Blob([byteArray], { type: 'application/pdf' });
      
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      toast.success("PDF descargado");
    } catch (error) {
      toast.error("Error al generar PDF");
    }
  };

  const handleConvertToInvoice = async (quoteId) => {
    if (!window.confirm("¿Deseas crear una factura a partir de esta cotización?")) return;
    try {
      const response = await api.post(`/quotes/${quoteId}/to-invoice?due_days=30`);
      toast.success(`Factura ${response.data.invoice_number} creada exitosamente`);
      fetchData();
    } catch (error) {
      const detail = error.response?.data?.detail;
      toast.error(typeof detail === "string" ? detail : "Error al crear factura");
    }
  };

  const resetForm = () => {
    setFormData({
      client_id: "",
      quote_number: generateQuoteNumber(),
      title: "",
      description: "",
      status: "prospect",
      show_tax: true,
      items: [{ description: "", quantity: 1, unit: "pza", unit_price: 0, total: 0, clave_prod_serv: "", clave_unidad: "" }],
    });
  };

  const getClientName = (clientId) => {
    const client = clients.find((c) => c.id === clientId);
    return client?.name || "N/A";
  };

  const getClientWithRef = (clientId) => {
    const client = clients.find((c) => c.id === clientId);
    if (!client) return "N/A";
    const displayName = client.trade_name || client.name;
    return client.reference ? `${displayName} (${client.reference})` : displayName;
  };

  // Filter quotes based on search
  const filteredQuotes = quotes.filter((quote) => {
    if (!searchFilter) return true;
    const search = searchFilter.toLowerCase();
    const client = clients.find(c => c.id === quote.client_id);
    const clientTradeName = client?.trade_name?.toLowerCase() || "";
    const clientName = client?.name?.toLowerCase() || "";
    const clientRazonSocial = client?.razon_social_fiscal?.toLowerCase() || "";
    const clientRef = client?.reference?.toLowerCase() || "";
    return (
      quote.quote_number?.toLowerCase().includes(search) ||
      quote.title?.toLowerCase().includes(search) ||
      quote.description?.toLowerCase().includes(search) ||
      quote.created_by_name?.toLowerCase().includes(search) ||
      clientTradeName.includes(search) ||
      clientName.includes(search) ||
      clientRazonSocial.includes(search) ||
      clientRef.includes(search) ||
      formatCurrency(quote.total).includes(search) ||
      getStatusLabel(quote.status)?.toLowerCase().includes(search)
    );
  });

  const openNewQuoteDialog = () => {
    resetForm();
    setFormData((prev) => ({ ...prev, quote_number: generateQuoteNumber() }));
    setDialogOpen(true);
  };

  const stats = {
    total: quotes.length,
    authorized: quotes.filter((q) => q.status === "authorized").length,
    pending: quotes.filter((q) => !["authorized", "denied"].includes(q.status)).length,
    pipelineValue: quotes.filter((q) => !["authorized", "denied"].includes(q.status)).reduce((acc, q) => acc + q.total, 0),
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

  const { subtotal, tax, total } = calculateTotals(formData.items, formData.show_tax);

  return (
    <div className="space-y-6 animate-fade-in" data-testid="quotes-page">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold font-[Chivo] text-slate-900">Cotizaciones</h1>
          <p className="text-muted-foreground">Gestión del pipeline comercial</p>
        </div>
        <Button className="btn-industrial" onClick={openNewQuoteDialog} data-testid="add-quote-btn">
          <Plus className="mr-2 h-4 w-4" />
          Nueva Cotización
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="stat-card">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Cotizaciones</CardTitle>
            <FileText className="h-5 w-5 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold font-[Chivo]">{stats.total}</div>
          </CardContent>
        </Card>
        <Card className="stat-card">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Autorizadas</CardTitle>
            <CheckCircle className="h-5 w-5 text-emerald-500" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold font-[Chivo] text-emerald-600">{stats.authorized}</div>
          </CardContent>
        </Card>
        <Card className="stat-card">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">En Proceso</CardTitle>
            <Clock className="h-5 w-5 text-amber-500" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold font-[Chivo] text-amber-600">{stats.pending}</div>
          </CardContent>
        </Card>
        <Card className="stat-card">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Valor Pipeline</CardTitle>
            <DollarSign className="h-5 w-5 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold font-[Chivo] text-blue-600">{formatCurrency(stats.pipelineValue)}</div>
          </CardContent>
        </Card>
      </div>

      {/* Quotes Table */}
      <Card data-testid="quotes-table-card">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5 text-primary" />
            Listado de Cotizaciones
          </CardTitle>
          <CardDescription>
            Pipeline comercial con {quotes.length} cotizaciones
          </CardDescription>
        </CardHeader>
        <CardContent>
          {/* Search Filter */}
          <div className="flex items-center gap-2 mb-4">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Buscar por folio, título, cliente, estado..."
                value={searchFilter}
                onChange={(e) => setSearchFilter(e.target.value)}
                className="pl-9"
                data-testid="quotes-search-filter"
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
                  <TableHead>Folio</TableHead>
                  <TableHead>Título</TableHead>
                  <TableHead>Cliente</TableHead>
                  <TableHead>Monto</TableHead>
                  <TableHead>Estado</TableHead>
                  <TableHead>Creado por</TableHead>
                  <TableHead>Fecha</TableHead>
                  <TableHead className="w-[50px]"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredQuotes.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={8} className="text-center py-8 text-muted-foreground">
                      {searchFilter ? "No se encontraron cotizaciones" : "No hay cotizaciones registradas"}
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredQuotes.map((quote) => (
                    <TableRow key={quote.id} data-testid={`quote-row-${quote.id}`} className={quote.status === "denied" ? "bg-red-50" : ""}>
                      <TableCell className="font-mono text-sm">
                        {quote.quote_number}
                        {quote.version > 1 && (
                          <Badge variant="outline" className="ml-1 text-xs">v{quote.version}</Badge>
                        )}
                      </TableCell>
                      <TableCell>
                        <div className="font-medium">{quote.title}</div>
                        {quote.description && (
                          <div className="text-sm text-muted-foreground truncate max-w-[200px]">
                            {quote.description}
                          </div>
                        )}
                        {quote.denial_reason && (
                          <div className="text-sm text-red-600 truncate max-w-[200px]">
                            Motivo: {quote.denial_reason}
                          </div>
                        )}
                      </TableCell>
                      <TableCell>{getClientWithRef(quote.client_id)}</TableCell>
                      <TableCell className="font-medium">
                        {formatCurrency(quote.total)}
                        {!quote.show_tax && <span className="text-xs text-muted-foreground ml-1">(sin IVA)</span>}
                      </TableCell>
                      <TableCell>
                        <Badge className={getStatusColor(quote.status)}>
                          {getStatusLabel(quote.status)}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {quote.created_by_name || "-"}
                      </TableCell>
                      <TableCell>{formatDate(quote.created_at)}</TableCell>
                      <TableCell>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon">
                              <MoreVertical className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => handleEditQuote(quote)}>
                              <Edit className="mr-2 h-4 w-4 text-blue-500" />
                              Editar
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={() => handleViewHistory(quote)}>
                              <History className="mr-2 h-4 w-4 text-slate-500" />
                              Ver Historial
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={() => handleDownloadPDF(quote.id)}>
                              <Download className="mr-2 h-4 w-4 text-blue-500" />
                              Descargar PDF
                            </DropdownMenuItem>
                            {quote.status === "authorized" && (
                              <DropdownMenuItem onClick={() => handleConvertToInvoice(quote.id)}>
                                <Receipt className="mr-2 h-4 w-4 text-emerald-500" />
                                Pasar a Facturación
                              </DropdownMenuItem>
                            )}
                            <DropdownMenuSeparator />
                            <DropdownMenuItem onClick={() => handleStatusChange(quote.id, "authorized")}>
                              <CheckCircle className="mr-2 h-4 w-4 text-emerald-500" />
                              Autorizar
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={() => handleStatusChange(quote.id, "denied")}>
                              <XCircle className="mr-2 h-4 w-4 text-red-500" />
                              Negar
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            {QUOTE_STATUSES.map((s) => (
                              <DropdownMenuItem
                                key={s.value}
                                onClick={() => handleStatusChange(quote.id, s.value)}
                              >
                                {s.label}
                              </DropdownMenuItem>
                            ))}
                            <DropdownMenuSeparator />
                            <DropdownMenuItem
                              onClick={() => handleDelete(quote.id)}
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

      {/* Create Quote Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="sm:max-w-[700px] max-h-[90vh] overflow-y-auto">
          <form onSubmit={handleSubmit}>
            <DialogHeader>
              <DialogTitle>Nueva Cotización</DialogTitle>
              <DialogDescription>
                Crea una cotización detallada por conceptos
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="grid gap-2">
                  <Label htmlFor="quote_number">Folio</Label>
                  <Input
                    id="quote_number"
                    value={formData.quote_number}
                    onChange={(e) => setFormData({ ...formData, quote_number: e.target.value })}
                    required
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="client_id">Cliente *</Label>
                  <Select
                    value={formData.client_id}
                    onValueChange={(value) => setFormData({ ...formData, client_id: value })}
                  >
                    <SelectTrigger data-testid="quote-client-select">
                      <SelectValue placeholder="Seleccionar cliente" />
                    </SelectTrigger>
                    <SelectContent>
                      {clients.map((client) => (
                        <SelectItem key={client.id} value={client.id}>
                          {client.trade_name || client.name} {client.reference && `(${client.reference})`}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="grid gap-2">
                <Label htmlFor="title">Título de la Cotización *</Label>
                <Input
                  id="title"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  placeholder="Servicio de mantenimiento industrial"
                  required
                  data-testid="quote-title-input"
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="description">Descripción</Label>
                <Textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Descripción general..."
                  rows={2}
                />
              </div>

              {/* Items */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <Label>Conceptos</Label>
                  <Button type="button" variant="outline" size="sm" onClick={addItem}>
                    <PlusCircle className="mr-1 h-4 w-4" />
                    Agregar
                  </Button>
                </div>
                {formData.items.map((item, index) => (
                  <div key={index} className="p-3 bg-slate-50 rounded-sm space-y-2">
                    <div className="grid grid-cols-12 gap-2 items-end">
                      <div className="col-span-12 md:col-span-4">
                        <Label className="text-xs">Descripción</Label>
                        <Input
                          value={item.description}
                          onChange={(e) => handleItemChange(index, "description", e.target.value)}
                          placeholder="Concepto"
                        />
                      </div>
                      <div className="col-span-4 md:col-span-2">
                        <Label className="text-xs">Cantidad</Label>
                        <Input
                          type="number"
                          value={item.quantity}
                          onChange={(e) => handleItemChange(index, "quantity", parseFloat(e.target.value) || 0)}
                        />
                      </div>
                      <div className="col-span-4 md:col-span-1">
                        <Label className="text-xs">Unidad</Label>
                        <Input
                          value={item.unit}
                          onChange={(e) => handleItemChange(index, "unit", e.target.value)}
                        />
                      </div>
                      <div className="col-span-4 md:col-span-2">
                        <Label className="text-xs">P. Unitario</Label>
                        <Input
                          type="number"
                          value={item.unit_price}
                          onChange={(e) => handleItemChange(index, "unit_price", parseFloat(e.target.value) || 0)}
                        />
                      </div>
                      <div className="col-span-8 md:col-span-2">
                        <Label className="text-xs">Total</Label>
                        <Input value={formatCurrency(item.quantity * item.unit_price)} disabled />
                      </div>
                      <div className="col-span-4 md:col-span-1">
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon"
                          onClick={() => removeItem(index)}
                          disabled={formData.items.length === 1}
                        >
                          <MinusCircle className="h-4 w-4 text-red-500" />
                        </Button>
                      </div>
                    </div>
                    <div className="flex flex-wrap gap-3 items-start border-t border-slate-200 pt-3 mt-2">
                      <div className="flex-1 min-w-[180px] max-w-[250px]">
                        <Label className="text-xs text-blue-600 mb-1 block">Clave SAT Producto</Label>
                        <SATProductSearch
                          value={item.clave_prod_serv || ""}
                          onChange={(val) => handleItemChange(index, "clave_prod_serv", val)}
                          placeholder="Buscar producto SAT..."
                        />
                        {!item.clave_prod_serv && (
                          <p className="text-[10px] text-slate-400 mt-1">Ej: 01010101</p>
                        )}
                      </div>
                      <div className="flex-1 min-w-[150px] max-w-[200px]">
                        <Label className="text-xs text-blue-600 mb-1 block">Clave Unidad SAT</Label>
                        <SATUnitSearch
                          value={item.clave_unidad || ""}
                          onChange={(val) => handleItemChange(index, "clave_unidad", val)}
                        />
                        {!item.clave_unidad && (
                          <p className="text-[10px] text-slate-400 mt-1">Ej: H87</p>
                        )}
                      </div>
                      <div className="flex items-center text-[10px] text-slate-400 pt-5">
                        Claves SAT para CFDI
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Totals */}
              <div className="space-y-2 p-4 bg-slate-100 rounded-sm">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Checkbox
                      id="show_tax"
                      checked={formData.show_tax}
                      onCheckedChange={(checked) => setFormData({ ...formData, show_tax: checked })}
                    />
                    <Label htmlFor="show_tax" className="text-sm font-normal cursor-pointer">
                      Incluir IVA en cotización
                    </Label>
                  </div>
                </div>
                <Separator />
                <div className="flex justify-between">
                  <span>Subtotal:</span>
                  <span className="font-medium">{formatCurrency(subtotal)}</span>
                </div>
                {formData.show_tax && (
                  <div className="flex justify-between">
                    <span>IVA (16%):</span>
                    <span className="font-medium">{formatCurrency(tax)}</span>
                  </div>
                )}
                <div className="flex justify-between text-lg font-bold">
                  <span>Total:</span>
                  <span className="text-primary">{formatCurrency(total)}</span>
                </div>
              </div>
              
              {/* Campo Personalizado - Debajo de totales */}
              <div className="grid grid-cols-2 gap-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
                <div className="grid gap-2">
                  <Label className="text-blue-700">Etiqueta del Campo (opcional)</Label>
                  <Input
                    value={formData.custom_field_label}
                    onChange={(e) => setFormData({ ...formData, custom_field_label: e.target.value })}
                    placeholder="Ej: No. de Proyecto, Referencia, Código"
                    className="bg-white"
                  />
                </div>
                <div className="grid gap-2">
                  <Label className="text-blue-700">Valor del Campo</Label>
                  <Input
                    value={formData.custom_field}
                    onChange={(e) => setFormData({ ...formData, custom_field: e.target.value })}
                    placeholder="Ej: PROY-2024-001"
                    className="bg-white"
                  />
                </div>
                <p className="col-span-2 text-xs text-blue-600">Este campo aparecerá en el PDF de la cotización</p>
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
                Cancelar
              </Button>
              <Button type="submit" className="btn-industrial" data-testid="save-quote-btn">
                Crear Cotización
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Edit Quote Dialog */}
      <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <DialogContent className="sm:max-w-[700px] max-h-[90vh] overflow-y-auto">
          <form onSubmit={handleUpdateQuote}>
            <DialogHeader>
              <DialogTitle>Editar Cotización - {selectedQuote?.quote_number}</DialogTitle>
              <DialogDescription>
                Modifica la cotización. Los cambios se guardarán en el historial.
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="grid gap-2">
                  <Label>Cliente *</Label>
                  <Select
                    value={formData.client_id}
                    onValueChange={(value) => setFormData({ ...formData, client_id: value })}
                  >
                    <SelectTrigger className="truncate">
                      <SelectValue placeholder="Seleccionar cliente" />
                    </SelectTrigger>
                    <SelectContent>
                      {clients.map((client) => (
                        <SelectItem key={client.id} value={client.id} className="truncate">
                          <span className="truncate block max-w-[250px]">
                            {client.trade_name || client.name}
                          </span>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid gap-2">
                  <Label>Estado</Label>
                  <Select
                    value={formData.status}
                    onValueChange={(value) => setFormData({ ...formData, status: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {QUOTE_STATUSES.map((s) => (
                        <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="grid gap-2">
                <Label>Título *</Label>
                <Input
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  required
                />
              </div>
              <div className="grid gap-2">
                <Label>Descripción</Label>
                <Textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={2}
                />
              </div>

              {/* Items */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <Label>Conceptos</Label>
                  <Button type="button" variant="outline" size="sm" onClick={addItem}>
                    <PlusCircle className="mr-1 h-4 w-4" />
                    Agregar
                  </Button>
                </div>
                {formData.items.map((item, index) => (
                  <div key={index} className="p-3 bg-slate-50 rounded-sm space-y-2">
                    <div className="grid grid-cols-12 gap-2 items-end">
                      <div className="col-span-12 md:col-span-4">
                        <Label className="text-xs">Descripción</Label>
                        <Input
                          value={item.description}
                          onChange={(e) => handleItemChange(index, "description", e.target.value)}
                          placeholder="Concepto"
                        />
                      </div>
                      <div className="col-span-4 md:col-span-2">
                        <Label className="text-xs">Cantidad</Label>
                        <Input
                          type="number"
                          value={item.quantity}
                          onChange={(e) => handleItemChange(index, "quantity", parseFloat(e.target.value) || 0)}
                        />
                      </div>
                      <div className="col-span-4 md:col-span-1">
                        <Label className="text-xs">Unidad</Label>
                        <Input
                          value={item.unit}
                          onChange={(e) => handleItemChange(index, "unit", e.target.value)}
                        />
                      </div>
                      <div className="col-span-4 md:col-span-2">
                        <Label className="text-xs">P. Unitario</Label>
                        <Input
                          type="number"
                          value={item.unit_price}
                          onChange={(e) => handleItemChange(index, "unit_price", parseFloat(e.target.value) || 0)}
                        />
                      </div>
                      <div className="col-span-8 md:col-span-2">
                        <Label className="text-xs">Total</Label>
                        <Input value={formatCurrency(item.quantity * item.unit_price)} disabled />
                      </div>
                      <div className="col-span-4 md:col-span-1">
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon"
                          onClick={() => removeItem(index)}
                          disabled={formData.items.length === 1}
                        >
                          <MinusCircle className="h-4 w-4 text-red-500" />
                        </Button>
                      </div>
                    </div>
                    <div className="flex flex-wrap gap-3 items-start border-t border-slate-200 pt-3 mt-2">
                      <div className="flex-1 min-w-[180px] max-w-[250px]">
                        <Label className="text-xs text-blue-600 mb-1 block">Clave SAT Producto</Label>
                        <SATProductSearch
                          value={item.clave_prod_serv || ""}
                          onChange={(val) => handleItemChange(index, "clave_prod_serv", val)}
                          placeholder="Buscar producto SAT..."
                        />
                        {!item.clave_prod_serv && (
                          <p className="text-[10px] text-slate-400 mt-1">Ej: 01010101</p>
                        )}
                      </div>
                      <div className="flex-1 min-w-[150px] max-w-[200px]">
                        <Label className="text-xs text-blue-600 mb-1 block">Clave Unidad SAT</Label>
                        <SATUnitSearch
                          value={item.clave_unidad || ""}
                          onChange={(val) => handleItemChange(index, "clave_unidad", val)}
                        />
                        {!item.clave_unidad && (
                          <p className="text-[10px] text-slate-400 mt-1">Ej: H87</p>
                        )}
                      </div>
                      <div className="flex items-center text-[10px] text-slate-400 pt-5">
                        Claves SAT para CFDI
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Totals */}
              <div className="space-y-2 p-4 bg-slate-100 rounded-sm">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Checkbox
                      id="edit_show_tax"
                      checked={formData.show_tax}
                      onCheckedChange={(checked) => setFormData({ ...formData, show_tax: checked })}
                    />
                    <Label htmlFor="edit_show_tax" className="text-sm font-normal cursor-pointer">
                      Incluir IVA en cotización
                    </Label>
                  </div>
                </div>
                <Separator />
                <div className="flex justify-between">
                  <span>Subtotal:</span>
                  <span className="font-medium">{formatCurrency(subtotal)}</span>
                </div>
                {formData.show_tax && (
                  <div className="flex justify-between">
                    <span>IVA (16%):</span>
                    <span className="font-medium">{formatCurrency(tax)}</span>
                  </div>
                )}
                <div className="flex justify-between text-lg font-bold">
                  <span>Total:</span>
                  <span className="text-primary">{formatCurrency(total)}</span>
                </div>
              </div>
              
              {/* Campo Personalizado - Debajo de totales */}
              <div className="grid grid-cols-2 gap-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
                <div className="grid gap-2">
                  <Label className="text-blue-700">Etiqueta del Campo (opcional)</Label>
                  <Input
                    value={formData.custom_field_label}
                    onChange={(e) => setFormData({ ...formData, custom_field_label: e.target.value })}
                    placeholder="Ej: No. de Proyecto, Referencia, Código"
                    className="bg-white"
                  />
                </div>
                <div className="grid gap-2">
                  <Label className="text-blue-700">Valor del Campo</Label>
                  <Input
                    value={formData.custom_field}
                    onChange={(e) => setFormData({ ...formData, custom_field: e.target.value })}
                    placeholder="Ej: PROY-2024-001"
                    className="bg-white"
                  />
                </div>
                <p className="col-span-2 text-xs text-blue-600">Este campo aparecerá en el PDF de la cotización</p>
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setEditDialogOpen(false)}>
                Cancelar
              </Button>
              <Button type="submit" className="btn-industrial">
                Guardar Cambios
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Denial Reason Dialog */}
      <Dialog open={denialDialogOpen} onOpenChange={setDenialDialogOpen}>
        <DialogContent className="sm:max-w-[400px]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Ban className="h-5 w-5 text-red-500" />
              Negar Cotización
            </DialogTitle>
            <DialogDescription>
              Indica el motivo por el cual se niega esta cotización
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <Label>Motivo de negación *</Label>
            <Textarea
              value={denialReason}
              onChange={(e) => setDenialReason(e.target.value)}
              placeholder="Ej: Presupuesto excede capacidad del cliente, cambio de prioridades..."
              rows={3}
              className="mt-2"
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDenialDialogOpen(false)}>
              Cancelar
            </Button>
            <Button 
              onClick={handleDenyQuote} 
              className="bg-red-600 hover:bg-red-700"
              disabled={!denialReason.trim()}
            >
              Confirmar Negación
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* History Dialog */}
      <Dialog open={historyDialogOpen} onOpenChange={setHistoryDialogOpen}>
        <DialogContent className="sm:max-w-[600px] max-h-[70vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <History className="h-5 w-5" />
              Historial de Cambios - {selectedQuote?.quote_number}
            </DialogTitle>
            <DialogDescription>
              Versión actual: {selectedQuote?.version || 1}
            </DialogDescription>
          </DialogHeader>
          <div className="py-4 space-y-4">
            {quoteHistory.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                No hay cambios registrados para esta cotización
              </div>
            ) : (
              quoteHistory.slice().reverse().map((entry, idx) => (
                <Card key={idx} className="border-l-4 border-l-primary">
                  <CardContent className="pt-4">
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <Badge variant="outline">Versión {entry.version}</Badge>
                        <span className="ml-2 text-sm text-muted-foreground">
                          por {entry.modified_by_name}
                        </span>
                      </div>
                      <span className="text-xs text-muted-foreground">
                        {formatDate(entry.modified_at)}
                      </span>
                    </div>
                    <div className="text-sm space-y-1">
                      {Object.keys(entry.changes).map((field) => (
                        <div key={field} className="flex items-center gap-2">
                          <span className="font-medium capitalize">{field.replace(/_/g, ' ')}:</span>
                          {field === 'items' ? (
                            <span className="text-muted-foreground">Conceptos modificados</span>
                          ) : (
                            <>
                              <span className="text-red-500 line-through">
                                {typeof entry.previous_values[field] === 'number' 
                                  ? formatCurrency(entry.previous_values[field])
                                  : String(entry.previous_values[field] || '-').substring(0, 30)}
                              </span>
                              <span>→</span>
                              <span className="text-emerald-600">
                                {typeof entry.changes[field] === 'number'
                                  ? formatCurrency(entry.changes[field])
                                  : String(entry.changes[field] || '-').substring(0, 30)}
                              </span>
                            </>
                          )}
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              ))
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setHistoryDialogOpen(false)}>
              Cerrar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Quotes;
