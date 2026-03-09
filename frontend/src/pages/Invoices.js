import React, { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { formatCurrency, formatDate, getStatusColor, getStatusLabel, generateInvoiceNumber , getApiErrorMessage } from "../lib/utils";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Badge } from "../components/ui/badge";
import { Skeleton } from "../components/ui/skeleton";
import { Progress } from "../components/ui/progress";
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
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "../components/ui/dropdown-menu";
import { toast } from "sonner";
import {
  Receipt,
  Plus,
  MoreVertical,
  DollarSign,
  CheckCircle,
  Clock,
  AlertTriangle,
  CreditCard,
  Trash2,
} from "lucide-react";

export const Invoices = () => {
  const { api, company } = useAuth();
  const [invoices, setInvoices] = useState([]);
  const [clients, setClients] = useState([]);
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [paymentDialogOpen, setPaymentDialogOpen] = useState(false);
  const [selectedInvoice, setSelectedInvoice] = useState(null);
  const [paymentAmount, setPaymentAmount] = useState("");
  const [formData, setFormData] = useState({
    client_id: "",
    project_id: "",
    invoice_number: "",
    concept: "",
    subtotal: "",
    tax: "",
    total: "",
  });

  useEffect(() => {
    if (company?.id) {
      fetchData();
    }
  }, [company]);

  const fetchData = async () => {
    try {
      const [invoicesRes, clientsRes, projectsRes] = await Promise.all([
        api.get(`/invoices?company_id=${company.id}`),
        api.get(`/clients?company_id=${company.id}`),
        api.get(`/projects?company_id=${company.id}`),
      ]);
      setInvoices(invoicesRes.data);
      setClients(clientsRes.data);
      setProjects(projectsRes.data);
    } catch (error) {
      toast.error("Error al cargar facturas");
    } finally {
      setLoading(false);
    }
  };

  const calculateFromSubtotal = (subtotal) => {
    const sub = parseFloat(subtotal) || 0;
    const tax = sub * 0.16;
    const total = sub + tax;
    return { tax: tax.toFixed(2), total: total.toFixed(2) };
  };

  const handleSubtotalChange = (value) => {
    const { tax, total } = calculateFromSubtotal(value);
    setFormData({ ...formData, subtotal: value, tax, total });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await api.post("/invoices", {
        company_id: company.id,
        ...formData,
        subtotal: parseFloat(formData.subtotal) || 0,
        tax: parseFloat(formData.tax) || 0,
        total: parseFloat(formData.total) || 0,
      });
      toast.success("Factura creada exitosamente");
      setDialogOpen(false);
      resetForm();
      fetchData();
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Error al crear factura"));
    }
  };

  const handleRecordPayment = async () => {
    if (!selectedInvoice || !paymentAmount) return;
    try {
      await api.patch(`/invoices/${selectedInvoice.id}/payment?amount=${parseFloat(paymentAmount)}`);
      toast.success("Pago registrado exitosamente");
      setPaymentDialogOpen(false);
      setSelectedInvoice(null);
      setPaymentAmount("");
      fetchData();
    } catch (error) {
      toast.error("Error al registrar pago");
    }
  };

  const handleDelete = async (invoiceId) => {
    if (!window.confirm("¿Estás seguro de eliminar esta factura?")) return;
    try {
      await api.delete(`/invoices/${invoiceId}`);
      toast.success("Factura eliminada");
      fetchData();
    } catch (error) {
      toast.error("Error al eliminar factura");
    }
  };

  const resetForm = () => {
    setFormData({
      client_id: "",
      project_id: "",
      invoice_number: generateInvoiceNumber(),
      concept: "",
      subtotal: "",
      tax: "",
      total: "",
    });
  };

  const openNewInvoiceDialog = () => {
    resetForm();
    setFormData((prev) => ({ ...prev, invoice_number: generateInvoiceNumber() }));
    setDialogOpen(true);
  };

  const openPaymentDialog = (invoice) => {
    setSelectedInvoice(invoice);
    setPaymentAmount("");
    setPaymentDialogOpen(true);
  };

  const getClientName = (clientId) => {
    const client = clients.find((c) => c.id === clientId);
    return client?.name || "N/A";
  };

  const stats = {
    total: invoices.reduce((acc, inv) => acc + inv.total, 0),
    collected: invoices.reduce((acc, inv) => acc + inv.paid_amount, 0),
    pending: invoices.reduce((acc, inv) => acc + (inv.total - inv.paid_amount), 0),
    overdue: invoices.filter((inv) => inv.status === "overdue").length,
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
    <div className="space-y-6 animate-fade-in" data-testid="invoices-page">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold font-[Chivo] text-slate-900">Control Financiero</h1>
          <p className="text-muted-foreground">Facturación y cuentas por cobrar</p>
        </div>
        <Button className="btn-industrial" onClick={openNewInvoiceDialog} data-testid="add-invoice-btn">
          <Plus className="mr-2 h-4 w-4" />
          Nueva Factura
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="stat-card">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Facturado</CardTitle>
            <Receipt className="h-5 w-5 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold font-[Chivo]">{formatCurrency(stats.total)}</div>
          </CardContent>
        </Card>
        <Card className="stat-card">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Cobrado</CardTitle>
            <CheckCircle className="h-5 w-5 text-emerald-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold font-[Chivo] text-emerald-600">{formatCurrency(stats.collected)}</div>
          </CardContent>
        </Card>
        <Card className="stat-card">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Por Cobrar</CardTitle>
            <Clock className="h-5 w-5 text-amber-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold font-[Chivo] text-amber-600">{formatCurrency(stats.pending)}</div>
          </CardContent>
        </Card>
        <Card className="stat-card">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Vencidas</CardTitle>
            <AlertTriangle className="h-5 w-5 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold font-[Chivo] text-red-600">{stats.overdue}</div>
          </CardContent>
        </Card>
      </div>

      {/* Collection Progress */}
      <Card>
        <CardContent className="py-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium">Avance de Cobranza</span>
            <span className="text-sm text-muted-foreground">
              {stats.total > 0 ? Math.round((stats.collected / stats.total) * 100) : 0}%
            </span>
          </div>
          <Progress value={stats.total > 0 ? (stats.collected / stats.total) * 100 : 0} className="h-3" />
        </CardContent>
      </Card>

      {/* Invoices Table */}
      <Card data-testid="invoices-table-card">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Receipt className="h-5 w-5 text-primary" />
            Facturas
          </CardTitle>
          <CardDescription>
            {invoices.length} factura(s) registrada(s)
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="rounded-sm border overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow className="bg-slate-50">
                  <TableHead>Folio</TableHead>
                  <TableHead>Cliente</TableHead>
                  <TableHead>Concepto</TableHead>
                  <TableHead>Total</TableHead>
                  <TableHead>Pagado</TableHead>
                  <TableHead>Saldo</TableHead>
                  <TableHead>Estado</TableHead>
                  <TableHead className="w-[50px]"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {invoices.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={8} className="text-center py-8 text-muted-foreground">
                      No hay facturas registradas
                    </TableCell>
                  </TableRow>
                ) : (
                  invoices.map((invoice) => (
                    <TableRow key={invoice.id} data-testid={`invoice-row-${invoice.id}`}>
                      <TableCell className="font-mono text-sm">{invoice.invoice_number}</TableCell>
                      <TableCell>{getClientName(invoice.client_id)}</TableCell>
                      <TableCell className="max-w-[200px] truncate">{invoice.concept}</TableCell>
                      <TableCell className="font-medium">{formatCurrency(invoice.total)}</TableCell>
                      <TableCell className="text-emerald-600">{formatCurrency(invoice.paid_amount)}</TableCell>
                      <TableCell className="text-amber-600">
                        {formatCurrency(invoice.total - invoice.paid_amount)}
                      </TableCell>
                      <TableCell>
                        <Badge className={getStatusColor(invoice.status)}>
                          {getStatusLabel(invoice.status)}
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
                            <DropdownMenuItem onClick={() => openPaymentDialog(invoice)}>
                              <CreditCard className="mr-2 h-4 w-4 text-emerald-500" />
                              Registrar Pago
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem
                              onClick={() => handleDelete(invoice.id)}
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

      {/* Create Invoice Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <form onSubmit={handleSubmit}>
            <DialogHeader>
              <DialogTitle>Nueva Factura</DialogTitle>
              <DialogDescription>
                Registra una nueva factura para seguimiento
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="grid gap-2">
                  <Label htmlFor="invoice_number">Folio</Label>
                  <Input
                    id="invoice_number"
                    value={formData.invoice_number}
                    onChange={(e) => setFormData({ ...formData, invoice_number: e.target.value })}
                    required
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="client_id">Cliente *</Label>
                  <Select
                    value={formData.client_id}
                    onValueChange={(value) => setFormData({ ...formData, client_id: value })}
                  >
                    <SelectTrigger data-testid="invoice-client-select">
                      <SelectValue placeholder="Seleccionar" />
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
                <Label htmlFor="project_id">Proyecto (opcional)</Label>
                <Select
                  value={formData.project_id}
                  onValueChange={(value) => setFormData({ ...formData, project_id: value })}
                >
                  <SelectTrigger>
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
                <Label htmlFor="concept">Concepto *</Label>
                <Input
                  id="concept"
                  value={formData.concept}
                  onChange={(e) => setFormData({ ...formData, concept: e.target.value })}
                  placeholder="Anticipo proyecto industrial"
                  required
                  data-testid="invoice-concept-input"
                />
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div className="grid gap-2">
                  <Label htmlFor="subtotal">Subtotal *</Label>
                  <Input
                    id="subtotal"
                    type="number"
                    value={formData.subtotal}
                    onChange={(e) => handleSubtotalChange(e.target.value)}
                    placeholder="100000"
                    required
                    data-testid="invoice-subtotal-input"
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="tax">IVA (16%)</Label>
                  <Input
                    id="tax"
                    type="number"
                    value={formData.tax}
                    disabled
                    className="bg-slate-50"
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="total">Total</Label>
                  <Input
                    id="total"
                    type="number"
                    value={formData.total}
                    disabled
                    className="bg-slate-50 font-bold"
                  />
                </div>
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
                Cancelar
              </Button>
              <Button type="submit" className="btn-industrial" data-testid="save-invoice-btn">
                Crear Factura
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Payment Dialog */}
      <Dialog open={paymentDialogOpen} onOpenChange={setPaymentDialogOpen}>
        <DialogContent className="sm:max-w-[400px]">
          <DialogHeader>
            <DialogTitle>Registrar Pago</DialogTitle>
            <DialogDescription>
              Factura: {selectedInvoice?.invoice_number}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="p-4 bg-slate-50 rounded-sm space-y-2">
              <div className="flex justify-between">
                <span>Total factura:</span>
                <span className="font-medium">{formatCurrency(selectedInvoice?.total || 0)}</span>
              </div>
              <div className="flex justify-between">
                <span>Pagado:</span>
                <span className="text-emerald-600">{formatCurrency(selectedInvoice?.paid_amount || 0)}</span>
              </div>
              <div className="flex justify-between font-bold">
                <span>Saldo:</span>
                <span className="text-amber-600">
                  {formatCurrency((selectedInvoice?.total || 0) - (selectedInvoice?.paid_amount || 0))}
                </span>
              </div>
            </div>
            <div className="grid gap-2">
              <Label htmlFor="payment_amount">Monto del Pago</Label>
              <Input
                id="payment_amount"
                type="number"
                value={paymentAmount}
                onChange={(e) => setPaymentAmount(e.target.value)}
                placeholder="Ingresa el monto"
                data-testid="payment-amount-input"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setPaymentDialogOpen(false)}>
              Cancelar
            </Button>
            <Button className="btn-industrial" onClick={handleRecordPayment} data-testid="record-payment-btn">
              Registrar Pago
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Invoices;
