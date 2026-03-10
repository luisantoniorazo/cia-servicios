import React, { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { formatCurrency, formatDate, getStatusColor, getStatusLabel, generateInvoiceNumber, getApiErrorMessage } from "../lib/utils";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Badge } from "../components/ui/badge";
import { Skeleton } from "../components/ui/skeleton";
import { Progress } from "../components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { Textarea } from "../components/ui/textarea";
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
  Download,
  Upload,
  FileText,
  User,
  Calendar,
  Eye,
} from "lucide-react";

const PAYMENT_METHODS = [
  { value: "transferencia", label: "Transferencia Bancaria" },
  { value: "efectivo", label: "Efectivo" },
  { value: "cheque", label: "Cheque" },
  { value: "tarjeta", label: "Tarjeta" },
];

export const Invoices = () => {
  const { api, company } = useAuth();
  const [invoices, setInvoices] = useState([]);
  const [clients, setClients] = useState([]);
  const [projects, setProjects] = useState([]);
  const [payments, setPayments] = useState([]);
  const [overdueData, setOverdueData] = useState({ overdue: [], upcoming: [] });
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [paymentDialogOpen, setPaymentDialogOpen] = useState(false);
  const [satDialogOpen, setSatDialogOpen] = useState(false);
  const [statementDialogOpen, setStatementDialogOpen] = useState(false);
  const [selectedInvoice, setSelectedInvoice] = useState(null);
  const [selectedClient, setSelectedClient] = useState(null);
  const [clientStatement, setClientStatement] = useState(null);
  const [activeTab, setActiveTab] = useState("all");
  
  const [formData, setFormData] = useState({
    client_id: "",
    project_id: "",
    invoice_number: "",
    concept: "",
    subtotal: "",
    tax: "",
    total: "",
    due_date: "",
  });
  
  const [paymentForm, setPaymentForm] = useState({
    amount: "",
    payment_date: new Date().toISOString().split("T")[0],
    payment_method: "transferencia",
    reference: "",
    notes: "",
    proof_file: null,
  });
  
  const [satForm, setSatForm] = useState({
    sat_uuid: "",
    sat_file: null,
  });

  useEffect(() => {
    if (company?.id) {
      fetchData();
    }
  }, [company]);

  const fetchData = async () => {
    try {
      const [invoicesRes, clientsRes, projectsRes, paymentsRes, overdueRes] = await Promise.all([
        api.get(`/invoices?company_id=${company.id}`),
        api.get(`/clients?company_id=${company.id}`),
        api.get(`/projects?company_id=${company.id}`),
        api.get(`/payments?company_id=${company.id}`),
        api.get(`/invoices/overdue?company_id=${company.id}`),
      ]);
      setInvoices(invoicesRes.data);
      setClients(clientsRes.data);
      setProjects(projectsRes.data);
      setPayments(paymentsRes.data);
      setOverdueData(overdueRes.data);
    } catch (error) {
      toast.error("Error al cargar datos");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const subtotal = parseFloat(formData.subtotal) || 0;
      const tax = subtotal * 0.16;
      const total = subtotal + tax;
      
      await api.post("/invoices", {
        company_id: company.id,
        ...formData,
        subtotal,
        tax,
        total,
        due_date: formData.due_date || null,
      });
      toast.success("Factura registrada");
      setDialogOpen(false);
      resetForm();
      fetchData();
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Error al registrar factura"));
    }
  };

  const handlePayment = async (e) => {
    e.preventDefault();
    if (!selectedInvoice) return;
    
    try {
      let proofBase64 = null;
      if (paymentForm.proof_file) {
        proofBase64 = await fileToBase64(paymentForm.proof_file);
      }
      
      const client = clients.find(c => c.id === selectedInvoice.client_id);
      
      await api.post("/payments", {
        company_id: company.id,
        invoice_id: selectedInvoice.id,
        client_id: selectedInvoice.client_id,
        amount: parseFloat(paymentForm.amount),
        payment_date: paymentForm.payment_date,
        payment_method: paymentForm.payment_method,
        reference: paymentForm.reference,
        notes: paymentForm.notes,
        proof_file: proofBase64,
      });
      
      toast.success("Abono registrado exitosamente");
      setPaymentDialogOpen(false);
      resetPaymentForm();
      fetchData();
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Error al registrar abono"));
    }
  };

  const handleUploadSAT = async (e) => {
    e.preventDefault();
    if (!selectedInvoice) return;
    
    try {
      let satFileBase64 = null;
      if (satForm.sat_file) {
        satFileBase64 = await fileToBase64(satForm.sat_file);
      }
      
      await api.post(`/invoices/${selectedInvoice.id}/upload-sat`, null, {
        params: {
          sat_uuid: satForm.sat_uuid || null,
          sat_file: satFileBase64,
        }
      });
      
      toast.success("Factura SAT subida");
      setSatDialogOpen(false);
      resetSatForm();
      fetchData();
    } catch (error) {
      toast.error("Error al subir factura SAT");
    }
  };

  const handleViewStatement = async (clientId) => {
    try {
      const response = await api.get(`/clients/${clientId}/statement`);
      setClientStatement(response.data);
      setStatementDialogOpen(true);
    } catch (error) {
      toast.error("Error al cargar estado de cuenta");
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

  const handleDownloadPDF = async (invoiceId) => {
    try {
      toast.info("Generando PDF...");
      const response = await api.get(`/pdf/invoice/${invoiceId}`);
      const { filename, content } = response.data;
      
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

  const fileToBase64 = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result.split(',')[1]);
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
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
      due_date: "",
    });
  };

  const resetPaymentForm = () => {
    setPaymentForm({
      amount: "",
      payment_date: new Date().toISOString().split("T")[0],
      payment_method: "transferencia",
      reference: "",
      notes: "",
      proof_file: null,
    });
    setSelectedInvoice(null);
  };

  const resetSatForm = () => {
    setSatForm({ sat_uuid: "", sat_file: null });
    setSelectedInvoice(null);
  };

  const openNewInvoiceDialog = () => {
    resetForm();
    setFormData((prev) => ({ ...prev, invoice_number: generateInvoiceNumber() }));
    setDialogOpen(true);
  };

  const openPaymentDialog = (invoice) => {
    setSelectedInvoice(invoice);
    setPaymentForm(prev => ({
      ...prev,
      amount: (invoice.total - invoice.paid_amount).toFixed(2),
    }));
    setPaymentDialogOpen(true);
  };

  const openSatDialog = (invoice) => {
    setSelectedInvoice(invoice);
    setSatDialogOpen(true);
  };

  const getClientName = (clientId) => {
    const client = clients.find((c) => c.id === clientId);
    return client?.name || "N/A";
  };

  const stats = {
    total: invoices.reduce((acc, inv) => acc + inv.total, 0),
    collected: invoices.reduce((acc, inv) => acc + inv.paid_amount, 0),
    pending: invoices.reduce((acc, inv) => acc + (inv.total - inv.paid_amount), 0),
    overdue: overdueData.overdue?.length || 0,
  };

  const filteredInvoices = activeTab === "all" 
    ? invoices 
    : activeTab === "overdue"
    ? overdueData.overdue
    : activeTab === "upcoming"
    ? overdueData.upcoming
    : invoices.filter(inv => inv.status === activeTab);

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => <Skeleton key={i} className="h-24" />)}
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
          <h1 className="text-3xl font-bold font-[Chivo] text-slate-900">Control de Facturación</h1>
          <p className="text-muted-foreground">Gestión de facturas, abonos y cobranza</p>
        </div>
        <Button className="btn-industrial" onClick={openNewInvoiceDialog} data-testid="new-invoice-btn">
          <Plus className="mr-2 h-4 w-4" />
          Nueva Factura
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Facturado Total</p>
                <p className="text-2xl font-bold">{formatCurrency(stats.total)}</p>
              </div>
              <Receipt className="h-8 w-8 text-primary/50" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Cobrado</p>
                <p className="text-2xl font-bold text-emerald-600">{formatCurrency(stats.collected)}</p>
              </div>
              <CheckCircle className="h-8 w-8 text-emerald-500/50" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Por Cobrar</p>
                <p className="text-2xl font-bold text-amber-600">{formatCurrency(stats.pending)}</p>
              </div>
              <Clock className="h-8 w-8 text-amber-500/50" />
            </div>
            <Progress value={(stats.collected / stats.total) * 100 || 0} className="mt-2" />
          </CardContent>
        </Card>
        <Card className={stats.overdue > 0 ? "border-red-200 bg-red-50" : ""}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Vencidas</p>
                <p className={`text-2xl font-bold ${stats.overdue > 0 ? "text-red-600" : ""}`}>
                  {stats.overdue}
                </p>
              </div>
              <AlertTriangle className={`h-8 w-8 ${stats.overdue > 0 ? "text-red-500" : "text-slate-300"}`} />
            </div>
            {overdueData.total_overdue_amount > 0 && (
              <p className="text-xs text-red-600 mt-1">
                Total: {formatCurrency(overdueData.total_overdue_amount)}
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Overdue Alert */}
      {overdueData.overdue?.length > 0 && (
        <Card className="border-red-300 bg-red-50">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <AlertTriangle className="h-5 w-5 text-red-600" />
              <div className="flex-1">
                <p className="font-semibold text-red-800">¡Atención! Facturas Vencidas</p>
                <p className="text-sm text-red-700">
                  Tienes {overdueData.overdue.length} factura(s) vencida(s) por un total de{" "}
                  {formatCurrency(overdueData.total_overdue_amount)}
                </p>
              </div>
              <Button 
                variant="outline" 
                className="border-red-300 text-red-700 hover:bg-red-100"
                onClick={() => setActiveTab("overdue")}
              >
                Ver Vencidas
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="all">Todas ({invoices.length})</TabsTrigger>
          <TabsTrigger value="pending">Pendientes</TabsTrigger>
          <TabsTrigger value="partial">Parciales</TabsTrigger>
          <TabsTrigger value="paid">Pagadas</TabsTrigger>
          <TabsTrigger value="overdue" className="text-red-600">
            Vencidas ({overdueData.overdue?.length || 0})
          </TabsTrigger>
          <TabsTrigger value="upcoming" className="text-amber-600">
            Próx. Vencer ({overdueData.upcoming?.length || 0})
          </TabsTrigger>
        </TabsList>

        <TabsContent value={activeTab} className="mt-4">
          <Card data-testid="invoices-table-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Receipt className="h-5 w-5 text-primary" />
                Listado de Facturas
              </CardTitle>
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
                      <TableHead>Vencimiento</TableHead>
                      <TableHead>Estado</TableHead>
                      <TableHead className="w-[50px]"></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredInvoices.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={9} className="text-center py-8 text-muted-foreground">
                          No hay facturas
                        </TableCell>
                      </TableRow>
                    ) : (
                      filteredInvoices.map((invoice) => (
                        <TableRow key={invoice.id} data-testid={`invoice-row-${invoice.id}`}>
                          <TableCell className="font-mono text-sm">
                            {invoice.invoice_number}
                            {invoice.sat_invoice_uuid && (
                              <Badge variant="outline" className="ml-2 text-xs">SAT</Badge>
                            )}
                          </TableCell>
                          <TableCell>
                            <Button 
                              variant="link" 
                              className="p-0 h-auto"
                              onClick={() => handleViewStatement(invoice.client_id)}
                            >
                              {invoice.client_name || getClientName(invoice.client_id)}
                            </Button>
                          </TableCell>
                          <TableCell className="max-w-[200px] truncate">{invoice.concept}</TableCell>
                          <TableCell className="font-medium">{formatCurrency(invoice.total)}</TableCell>
                          <TableCell className="text-emerald-600">{formatCurrency(invoice.paid_amount)}</TableCell>
                          <TableCell className="text-amber-600">
                            {formatCurrency(invoice.total - invoice.paid_amount)}
                          </TableCell>
                          <TableCell>
                            {invoice.due_date ? (
                              <div className="flex items-center gap-1">
                                <Calendar className="h-3 w-3" />
                                <span className={invoice.days_overdue > 0 ? "text-red-600 font-medium" : ""}>
                                  {formatDate(invoice.due_date)}
                                </span>
                                {invoice.days_overdue > 0 && (
                                  <Badge variant="destructive" className="ml-1 text-xs">
                                    +{invoice.days_overdue}d
                                  </Badge>
                                )}
                              </div>
                            ) : "-"}
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
                                <DropdownMenuItem onClick={() => handleDownloadPDF(invoice.id)}>
                                  <Download className="mr-2 h-4 w-4 text-blue-500" />
                                  Descargar PDF
                                </DropdownMenuItem>
                                <DropdownMenuItem onClick={() => openPaymentDialog(invoice)}>
                                  <CreditCard className="mr-2 h-4 w-4 text-emerald-500" />
                                  Registrar Abono
                                </DropdownMenuItem>
                                <DropdownMenuItem onClick={() => openSatDialog(invoice)}>
                                  <Upload className="mr-2 h-4 w-4 text-orange-500" />
                                  Subir Factura SAT
                                </DropdownMenuItem>
                                <DropdownMenuItem onClick={() => handleViewStatement(invoice.client_id)}>
                                  <User className="mr-2 h-4 w-4 text-purple-500" />
                                  Estado de Cuenta
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
        </TabsContent>
      </Tabs>

      {/* Create Invoice Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <form onSubmit={handleSubmit}>
            <DialogHeader>
              <DialogTitle>Nueva Factura</DialogTitle>
              <DialogDescription>Registra una nueva factura para seguimiento</DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="grid gap-2">
                  <Label>Folio</Label>
                  <Input
                    value={formData.invoice_number}
                    onChange={(e) => setFormData({ ...formData, invoice_number: e.target.value })}
                    required
                  />
                </div>
                <div className="grid gap-2">
                  <Label>Fecha Vencimiento</Label>
                  <Input
                    type="date"
                    value={formData.due_date}
                    onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
                  />
                </div>
              </div>
              <div className="grid gap-2">
                <Label>Cliente *</Label>
                <Select
                  value={formData.client_id}
                  onValueChange={(value) => setFormData({ ...formData, client_id: value })}
                >
                  <SelectTrigger><SelectValue placeholder="Seleccionar cliente" /></SelectTrigger>
                  <SelectContent>
                    {clients.filter(c => !c.is_prospect).map((c) => (
                      <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="grid gap-2">
                <Label>Proyecto (opcional)</Label>
                <Select
                  value={formData.project_id}
                  onValueChange={(value) => setFormData({ ...formData, project_id: value })}
                >
                  <SelectTrigger><SelectValue placeholder="Seleccionar proyecto" /></SelectTrigger>
                  <SelectContent>
                    {projects.map((p) => (
                      <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="grid gap-2">
                <Label>Concepto *</Label>
                <Input
                  value={formData.concept}
                  onChange={(e) => setFormData({ ...formData, concept: e.target.value })}
                  placeholder="Descripción del servicio"
                  required
                />
              </div>
              <div className="grid gap-2">
                <Label>Subtotal *</Label>
                <Input
                  type="number"
                  value={formData.subtotal}
                  onChange={(e) => setFormData({ ...formData, subtotal: e.target.value })}
                  placeholder="0.00"
                  required
                />
                <p className="text-xs text-muted-foreground">
                  IVA (16%): {formatCurrency((parseFloat(formData.subtotal) || 0) * 0.16)} | 
                  Total: {formatCurrency((parseFloat(formData.subtotal) || 0) * 1.16)}
                </p>
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>Cancelar</Button>
              <Button type="submit" className="btn-industrial">Registrar</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Payment Dialog */}
      <Dialog open={paymentDialogOpen} onOpenChange={setPaymentDialogOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <form onSubmit={handlePayment}>
            <DialogHeader>
              <DialogTitle>Registrar Abono</DialogTitle>
              <DialogDescription>
                Factura: {selectedInvoice?.invoice_number} | 
                Saldo: {formatCurrency((selectedInvoice?.total || 0) - (selectedInvoice?.paid_amount || 0))}
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="grid gap-2">
                  <Label>Monto del Abono *</Label>
                  <Input
                    type="number"
                    step="0.01"
                    value={paymentForm.amount}
                    onChange={(e) => setPaymentForm({ ...paymentForm, amount: e.target.value })}
                    placeholder="0.00"
                    required
                  />
                </div>
                <div className="grid gap-2">
                  <Label>Fecha de Pago *</Label>
                  <Input
                    type="date"
                    value={paymentForm.payment_date}
                    onChange={(e) => setPaymentForm({ ...paymentForm, payment_date: e.target.value })}
                    required
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="grid gap-2">
                  <Label>Método de Pago</Label>
                  <Select
                    value={paymentForm.payment_method}
                    onValueChange={(value) => setPaymentForm({ ...paymentForm, payment_method: value })}
                  >
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {PAYMENT_METHODS.map((m) => (
                        <SelectItem key={m.value} value={m.value}>{m.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid gap-2">
                  <Label>Referencia</Label>
                  <Input
                    value={paymentForm.reference}
                    onChange={(e) => setPaymentForm({ ...paymentForm, reference: e.target.value })}
                    placeholder="No. transferencia, cheque, etc."
                  />
                </div>
              </div>
              <div className="grid gap-2">
                <Label>Comprobante de Pago</Label>
                <Input
                  type="file"
                  accept=".pdf,.png,.jpg,.jpeg"
                  onChange={(e) => setPaymentForm({ ...paymentForm, proof_file: e.target.files?.[0] })}
                />
                <p className="text-xs text-muted-foreground">PDF o imagen del comprobante</p>
              </div>
              <div className="grid gap-2">
                <Label>Notas</Label>
                <Textarea
                  value={paymentForm.notes}
                  onChange={(e) => setPaymentForm({ ...paymentForm, notes: e.target.value })}
                  placeholder="Observaciones del pago..."
                  rows={2}
                />
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setPaymentDialogOpen(false)}>Cancelar</Button>
              <Button type="submit" className="bg-emerald-600 hover:bg-emerald-700">Registrar Abono</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* SAT Upload Dialog */}
      <Dialog open={satDialogOpen} onOpenChange={setSatDialogOpen}>
        <DialogContent className="sm:max-w-[400px]">
          <form onSubmit={handleUploadSAT}>
            <DialogHeader>
              <DialogTitle>Subir Factura SAT</DialogTitle>
              <DialogDescription>
                Adjunta el archivo XML o PDF de la factura del SAT
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid gap-2">
                <Label>UUID de Factura (opcional)</Label>
                <Input
                  value={satForm.sat_uuid}
                  onChange={(e) => setSatForm({ ...satForm, sat_uuid: e.target.value })}
                  placeholder="XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX"
                />
              </div>
              <div className="grid gap-2">
                <Label>Archivo de Factura SAT</Label>
                <Input
                  type="file"
                  accept=".xml,.pdf"
                  onChange={(e) => setSatForm({ ...satForm, sat_file: e.target.files?.[0] })}
                />
                <p className="text-xs text-muted-foreground">Archivo XML o PDF del SAT</p>
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setSatDialogOpen(false)}>Cancelar</Button>
              <Button type="submit" className="bg-orange-600 hover:bg-orange-700">Subir</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Client Statement Dialog */}
      <Dialog open={statementDialogOpen} onOpenChange={setStatementDialogOpen}>
        <DialogContent className="sm:max-w-[700px] max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Estado de Cuenta</DialogTitle>
            <DialogDescription>
              {clientStatement?.client?.name}
            </DialogDescription>
          </DialogHeader>
          {clientStatement && (
            <div className="space-y-4">
              {/* Summary */}
              <div className="grid grid-cols-3 gap-4">
                <Card>
                  <CardContent className="p-3 text-center">
                    <p className="text-sm text-muted-foreground">Total Facturado</p>
                    <p className="text-xl font-bold">{formatCurrency(clientStatement.summary.total_invoiced)}</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-3 text-center">
                    <p className="text-sm text-muted-foreground">Total Pagado</p>
                    <p className="text-xl font-bold text-emerald-600">{formatCurrency(clientStatement.summary.total_paid)}</p>
                  </CardContent>
                </Card>
                <Card className={clientStatement.summary.balance > 0 ? "border-amber-200 bg-amber-50" : ""}>
                  <CardContent className="p-3 text-center">
                    <p className="text-sm text-muted-foreground">Saldo Pendiente</p>
                    <p className={`text-xl font-bold ${clientStatement.summary.balance > 0 ? "text-amber-600" : "text-emerald-600"}`}>
                      {formatCurrency(clientStatement.summary.balance)}
                    </p>
                  </CardContent>
                </Card>
              </div>

              {/* Overdue Warning */}
              {clientStatement.summary.overdue_count > 0 && (
                <Card className="border-red-200 bg-red-50">
                  <CardContent className="p-3 flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4 text-red-600" />
                    <span className="text-red-800 text-sm">
                      {clientStatement.summary.overdue_count} factura(s) vencida(s) por {formatCurrency(clientStatement.summary.overdue_amount)}
                    </span>
                  </CardContent>
                </Card>
              )}

              {/* Invoices List */}
              <div>
                <h4 className="font-semibold mb-2">Facturas</h4>
                <div className="border rounded-sm max-h-40 overflow-y-auto">
                  {clientStatement.invoices.map((inv) => (
                    <div key={inv.id} className="p-2 border-b last:border-b-0 flex items-center justify-between text-sm">
                      <div>
                        <span className="font-mono">{inv.invoice_number}</span>
                        <span className="text-muted-foreground ml-2">{inv.concept}</span>
                      </div>
                      <div className="flex items-center gap-3">
                        <span>{formatCurrency(inv.total)}</span>
                        <Badge className={getStatusColor(inv.status)}>{getStatusLabel(inv.status)}</Badge>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Payments List */}
              {clientStatement.payments.length > 0 && (
                <div>
                  <h4 className="font-semibold mb-2">Pagos Recibidos</h4>
                  <div className="border rounded-sm max-h-40 overflow-y-auto">
                    {clientStatement.payments.map((p) => (
                      <div key={p.id} className="p-2 border-b last:border-b-0 flex items-center justify-between text-sm">
                        <div>
                          <span>{formatDate(p.payment_date)}</span>
                          <span className="text-muted-foreground ml-2">{p.payment_method}</span>
                          {p.reference && <span className="text-muted-foreground ml-1">({p.reference})</span>}
                        </div>
                        <span className="text-emerald-600 font-medium">{formatCurrency(p.amount)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
          <DialogFooter>
            {clientStatement && (
              <Button 
                variant="outline" 
                onClick={() => handleDownloadStatementPDF(clientStatement.client.id)}
                className="mr-auto"
              >
                <Download className="mr-2 h-4 w-4" />
                Descargar PDF
              </Button>
            )}
            <Button variant="outline" onClick={() => setStatementDialogOpen(false)}>Cerrar</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Invoices;
