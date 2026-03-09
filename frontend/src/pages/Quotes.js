import React, { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { formatCurrency, formatDate, getStatusColor, getStatusLabel, generateQuoteNumber } from "../lib/utils";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import { Badge } from "../components/ui/badge";
import { Skeleton } from "../components/ui/skeleton";
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
  const { api, company } = useAuth();
  const [quotes, setQuotes] = useState([]);
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [formData, setFormData] = useState({
    client_id: "",
    quote_number: "",
    title: "",
    description: "",
    status: "prospect",
    items: [{ description: "", quantity: 1, unit: "pza", unit_price: 0, total: 0 }],
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

  const calculateTotals = (items) => {
    const subtotal = items.reduce((acc, item) => acc + (item.quantity * item.unit_price), 0);
    const tax = subtotal * 0.16;
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
      items: [...formData.items, { description: "", quantity: 1, unit: "pza", unit_price: 0, total: 0 }],
    });
  };

  const removeItem = (index) => {
    if (formData.items.length === 1) return;
    const newItems = formData.items.filter((_, i) => i !== index);
    setFormData({ ...formData, items: newItems });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const { subtotal, tax, total } = calculateTotals(formData.items);
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
      toast.error(error.response?.data?.detail || "Error al crear cotización");
    }
  };

  const handleStatusChange = async (quoteId, status) => {
    try {
      await api.patch(`/quotes/${quoteId}/status?status=${status}`);
      toast.success("Estado actualizado");
      fetchData();
    } catch (error) {
      toast.error("Error al actualizar estado");
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

  const resetForm = () => {
    setFormData({
      client_id: "",
      quote_number: generateQuoteNumber(),
      title: "",
      description: "",
      status: "prospect",
      items: [{ description: "", quantity: 1, unit: "pza", unit_price: 0, total: 0 }],
    });
  };

  const getClientName = (clientId) => {
    const client = clients.find((c) => c.id === clientId);
    return client?.name || "N/A";
  };

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

  const { subtotal, tax, total } = calculateTotals(formData.items);

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
          <div className="rounded-sm border overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow className="bg-slate-50">
                  <TableHead>Folio</TableHead>
                  <TableHead>Título</TableHead>
                  <TableHead>Cliente</TableHead>
                  <TableHead>Monto</TableHead>
                  <TableHead>Estado</TableHead>
                  <TableHead>Fecha</TableHead>
                  <TableHead className="w-[50px]"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {quotes.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center py-8 text-muted-foreground">
                      No hay cotizaciones registradas
                    </TableCell>
                  </TableRow>
                ) : (
                  quotes.map((quote) => (
                    <TableRow key={quote.id} data-testid={`quote-row-${quote.id}`}>
                      <TableCell className="font-mono text-sm">{quote.quote_number}</TableCell>
                      <TableCell>
                        <div className="font-medium">{quote.title}</div>
                        {quote.description && (
                          <div className="text-sm text-muted-foreground truncate max-w-[200px]">
                            {quote.description}
                          </div>
                        )}
                      </TableCell>
                      <TableCell>{getClientName(quote.client_id)}</TableCell>
                      <TableCell className="font-medium">{formatCurrency(quote.total)}</TableCell>
                      <TableCell>
                        <Badge className={getStatusColor(quote.status)}>
                          {getStatusLabel(quote.status)}
                        </Badge>
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
                          {client.name}
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
                  <div key={index} className="grid grid-cols-12 gap-2 items-end p-3 bg-slate-50 rounded-sm">
                    <div className="col-span-4">
                      <Label className="text-xs">Descripción</Label>
                      <Input
                        value={item.description}
                        onChange={(e) => handleItemChange(index, "description", e.target.value)}
                        placeholder="Concepto"
                      />
                    </div>
                    <div className="col-span-2">
                      <Label className="text-xs">Cantidad</Label>
                      <Input
                        type="number"
                        value={item.quantity}
                        onChange={(e) => handleItemChange(index, "quantity", parseFloat(e.target.value) || 0)}
                      />
                    </div>
                    <div className="col-span-1">
                      <Label className="text-xs">Unidad</Label>
                      <Input
                        value={item.unit}
                        onChange={(e) => handleItemChange(index, "unit", e.target.value)}
                      />
                    </div>
                    <div className="col-span-2">
                      <Label className="text-xs">P. Unitario</Label>
                      <Input
                        type="number"
                        value={item.unit_price}
                        onChange={(e) => handleItemChange(index, "unit_price", parseFloat(e.target.value) || 0)}
                      />
                    </div>
                    <div className="col-span-2">
                      <Label className="text-xs">Total</Label>
                      <Input value={formatCurrency(item.quantity * item.unit_price)} disabled />
                    </div>
                    <div className="col-span-1">
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
                ))}
              </div>

              {/* Totals */}
              <div className="space-y-2 p-4 bg-slate-100 rounded-sm">
                <div className="flex justify-between">
                  <span>Subtotal:</span>
                  <span className="font-medium">{formatCurrency(subtotal)}</span>
                </div>
                <div className="flex justify-between">
                  <span>IVA (16%):</span>
                  <span className="font-medium">{formatCurrency(tax)}</span>
                </div>
                <div className="flex justify-between text-lg font-bold">
                  <span>Total:</span>
                  <span className="text-primary">{formatCurrency(total)}</span>
                </div>
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
    </div>
  );
};

export default Quotes;
