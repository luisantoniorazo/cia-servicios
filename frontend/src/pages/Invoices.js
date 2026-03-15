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
import { SATProductSearch, SATUnitSearch } from "../components/SATSearch";
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
  PlusCircle,
  MinusCircle,
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
  Search,
  X,
} from "lucide-react";

const PAYMENT_METHODS = [
  { value: "transferencia", label: "Transferencia Bancaria" },
  { value: "efectivo", label: "Efectivo" },
  { value: "cheque", label: "Cheque" },
  { value: "tarjeta", label: "Tarjeta" },
];

// Catálogo SAT c_FormaPago para CFDI
const SAT_FORMAS_PAGO = [
  { value: "01", label: "01 - Efectivo" },
  { value: "02", label: "02 - Cheque nominativo" },
  { value: "03", label: "03 - Transferencia electrónica de fondos" },
  { value: "04", label: "04 - Tarjeta de crédito" },
  { value: "05", label: "05 - Monedero electrónico" },
  { value: "06", label: "06 - Dinero electrónico" },
  { value: "08", label: "08 - Vales de despensa" },
  { value: "12", label: "12 - Dación en pago" },
  { value: "13", label: "13 - Pago por subrogación" },
  { value: "14", label: "14 - Pago por consignación" },
  { value: "15", label: "15 - Condonación" },
  { value: "17", label: "17 - Compensación" },
  { value: "23", label: "23 - Novación" },
  { value: "24", label: "24 - Confusión" },
  { value: "25", label: "25 - Remisión de deuda" },
  { value: "26", label: "26 - Prescripción o caducidad" },
  { value: "27", label: "27 - A satisfacción del acreedor" },
  { value: "28", label: "28 - Tarjeta de débito" },
  { value: "29", label: "29 - Tarjeta de servicios" },
  { value: "30", label: "30 - Aplicación de anticipos" },
  { value: "31", label: "31 - Intermediario pagos" },
  { value: "99", label: "99 - Por definir" },
];

const MONEDAS = [
  { value: "MXN", label: "MXN - Peso Mexicano" },
  { value: "USD", label: "USD - Dólar Americano" },
  { value: "EUR", label: "EUR - Euro" },
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
    items: [{ description: "", quantity: 1, unit: "pza", unit_price: 0, total: 0, clave_prod_serv: "", clave_unidad: "" }],
    subtotal: 0,
    tax: 0,
    total: 0,
    invoice_date: new Date().toISOString().split("T")[0],
    due_date: "",
  });
  
  const [paymentForm, setPaymentForm] = useState({
    // Datos básicos del pago
    amount: "",
    payment_date: new Date().toISOString().split("T")[0],
    payment_method: "transferencia",
    reference: "",
    notes: "",
    proof_file: null,
    // Datos SAT para complemento de pago CFDI
    sat_forma_pago: "03", // Default: Transferencia electrónica
    moneda_pago: "MXN",
    tipo_cambio: "1",
    num_operacion: "",
    // Datos bancarios ordenante (quien paga)
    rfc_banco_ordenante: "",
    nombre_banco_ordenante: "",
    cuenta_ordenante: "",
    // Datos bancarios beneficiario (quien recibe)
    rfc_banco_beneficiario: "",
    cuenta_beneficiaria: "",
    // Control de parcialidades
    num_parcialidad: "1",
  });
  
  const [satForm, setSatForm] = useState({
    sat_uuid: "",
    sat_file: null,
  });
  
  const [searchFilter, setSearchFilter] = useState("");

  // Filter invoices based on search
  const getFilteredInvoices = (invoiceList) => {
    if (!searchFilter) return invoiceList;
    const search = searchFilter.toLowerCase();
    return invoiceList.filter((inv) => {
      const clientName = getClientName(inv.client_id)?.toLowerCase() || "";
      const projectName = getProjectName(inv.project_id)?.toLowerCase() || "";
      return (
        inv.invoice_number?.toLowerCase().includes(search) ||
        inv.concept?.toLowerCase().includes(search) ||
        clientName.includes(search) ||
        projectName.includes(search) ||
        inv.sat_uuid?.toLowerCase().includes(search) ||
        formatCurrency(inv.total).includes(search)
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
    const { subtotal, tax, total } = calculateTotals(newItems);
    setFormData({ ...formData, items: newItems, subtotal, tax, total });
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
    const { subtotal, tax, total } = calculateTotals(newItems);
    setFormData({ ...formData, items: newItems, subtotal, tax, total });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const { subtotal, tax, total } = calculateTotals(formData.items);
      const concept = formData.items.map(i => i.description).filter(Boolean).join(", ") || "Factura";
      
      await api.post("/invoices", {
        company_id: company.id,
        ...formData,
        concept,
        subtotal,
        tax,
        total,
        invoice_date: formData.invoice_date || new Date().toISOString().split("T")[0],
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

  const handleDownloadStatementPDF = async (clientId) => {
    try {
      toast.info("Generando estado de cuenta PDF...");
      const response = await api.get(`/clients/${clientId}/statement/pdf`);
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
      
      toast.success("Estado de cuenta descargado");
    } catch (error) {
      toast.error("Error al generar estado de cuenta PDF");
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
      items: [{ description: "", quantity: 1, unit: "pza", unit_price: 0, total: 0, clave_prod_serv: "", clave_unidad: "" }],
      subtotal: 0,
      tax: 0,
      total: 0,
      invoice_date: new Date().toISOString().split("T")[0],
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
    if (!client) return "N/A";
    return client.reference ? `${client.name} (${client.reference})` : client.name;
  };

  const stats = {
    total: invoices.reduce((acc, inv) => acc + inv.total, 0),
    collected: invoices.reduce((acc, inv) => acc + inv.paid_amount, 0),
    pending: invoices.reduce((acc, inv) => acc + (inv.total - inv.paid_amount), 0),
    overdue: overdueData.overdue?.length || 0,
  };

  const baseFilteredInvoices = activeTab === "all" 
    ? invoices 
    : activeTab === "overdue"
    ? overdueData.overdue
    : activeTab === "upcoming"
    ? overdueData.upcoming
    : invoices.filter(inv => inv.status === activeTab);
  
  const filteredInvoices = getFilteredInvoices(baseFilteredInvoices);

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
    <div className="space-y-4 sm:space-y-6 animate-fade-in" data-testid="invoices-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 sm:gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl lg:text-3xl font-bold font-[Chivo] text-slate-900">Control de Facturación</h1>
          <p className="text-sm sm:text-base text-muted-foreground">Gestión de facturas y cobranza</p>
        </div>
        <Button className="btn-industrial" size="sm" onClick={openNewInvoiceDialog} data-testid="new-invoice-btn">
          <Plus className="mr-1 sm:mr-2 h-4 w-4" />
          Nueva Factura
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-2 sm:gap-4">
        <Card>
          <CardContent className="p-3 sm:p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs sm:text-sm text-muted-foreground">Facturado</p>
                <p className="text-lg sm:text-2xl font-bold">{formatCurrency(stats.total)}</p>
              </div>
              <Receipt className="h-6 w-6 sm:h-8 sm:w-8 text-primary/50" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-3 sm:p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs sm:text-sm text-muted-foreground">Cobrado</p>
                <p className="text-lg sm:text-2xl font-bold text-emerald-600">{formatCurrency(stats.collected)}</p>
              </div>
              <CheckCircle className="h-6 w-6 sm:h-8 sm:w-8 text-emerald-500/50" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-3 sm:p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs sm:text-sm text-muted-foreground">Por Cobrar</p>
                <p className="text-lg sm:text-2xl font-bold text-amber-600">{formatCurrency(stats.pending)}</p>
              </div>
              <Clock className="h-6 w-6 sm:h-8 sm:w-8 text-amber-500/50" />
            </div>
            <Progress value={(stats.collected / stats.total) * 100 || 0} className="mt-2" />
          </CardContent>
        </Card>
        <Card className={stats.overdue > 0 ? "border-red-200 bg-red-50" : ""}>
          <CardContent className="p-3 sm:p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs sm:text-sm text-muted-foreground">Vencidas</p>
                <p className={`text-lg sm:text-2xl font-bold ${stats.overdue > 0 ? "text-red-600" : ""}`}>
                  {stats.overdue}
                </p>
              </div>
              <AlertTriangle className={`h-6 w-6 sm:h-8 sm:w-8 ${stats.overdue > 0 ? "text-red-500" : "text-slate-300"}`} />
            </div>
            {overdueData.total_overdue_amount > 0 && (
              <p className="text-xs text-red-600 mt-1">
                {formatCurrency(overdueData.total_overdue_amount)}
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Overdue Alert */}
      {overdueData.overdue?.length > 0 && (
        <Card className="border-red-300 bg-red-50">
          <CardContent className="p-3 sm:p-4">
            <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-3">
              <AlertTriangle className="h-5 w-5 text-red-600 hidden sm:block" />
              <div className="flex-1">
                <p className="font-semibold text-red-800 text-sm sm:text-base">¡Facturas Vencidas!</p>
                <p className="text-xs sm:text-sm text-red-700">
                  {overdueData.overdue.length} factura(s) - {formatCurrency(overdueData.total_overdue_amount)}
                </p>
              </div>
              <Button 
                variant="outline" 
                size="sm"
                className="border-red-300 text-red-700 hover:bg-red-100 text-xs sm:text-sm"
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
        <TabsList className="w-full sm:w-auto overflow-x-auto flex-nowrap">
          <TabsTrigger value="all" className="text-xs sm:text-sm">Todas ({invoices.length})</TabsTrigger>
          <TabsTrigger value="pending" className="text-xs sm:text-sm">Pendientes</TabsTrigger>
          <TabsTrigger value="partial" className="text-xs sm:text-sm">Parciales</TabsTrigger>
          <TabsTrigger value="paid" className="text-xs sm:text-sm">Pagadas</TabsTrigger>
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
              {/* Search Filter */}
              <div className="flex items-center gap-2 mb-4">
                <div className="relative flex-1 max-w-sm">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Buscar por folio, cliente, concepto, UUID SAT..."
                    value={searchFilter}
                    onChange={(e) => setSearchFilter(e.target.value)}
                    className="pl-9"
                    data-testid="invoices-search-filter"
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
                      <TableHead>Cliente</TableHead>
                      <TableHead>Concepto</TableHead>
                      <TableHead>Fecha Factura</TableHead>
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
                        <TableCell colSpan={10} className="text-center py-8 text-muted-foreground">
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
                          <TableCell className="text-slate-600">
                            {invoice.invoice_date ? formatDate(invoice.invoice_date) : formatDate(invoice.created_at)}
                          </TableCell>
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
        <DialogContent className="sm:max-w-[750px] max-h-[90vh] overflow-y-auto">
          <form onSubmit={handleSubmit}>
            <DialogHeader>
              <DialogTitle>Nueva Factura</DialogTitle>
              <DialogDescription>Registra una nueva factura con datos fiscales para CFDI</DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid grid-cols-3 gap-4">
                <div className="grid gap-2">
                  <Label>Folio</Label>
                  <Input
                    value={formData.invoice_number}
                    onChange={(e) => setFormData({ ...formData, invoice_number: e.target.value })}
                    required
                  />
                </div>
                <div className="grid gap-2">
                  <Label>Fecha de Factura *</Label>
                  <Input
                    type="date"
                    value={formData.invoice_date}
                    onChange={(e) => setFormData({ ...formData, invoice_date: e.target.value })}
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
              <div className="grid grid-cols-2 gap-4">
                <div className="grid gap-2">
                  <Label>Cliente *</Label>
                  <Select
                    value={formData.client_id}
                    onValueChange={(value) => setFormData({ ...formData, client_id: value })}
                  >
                    <SelectTrigger><SelectValue placeholder="Seleccionar cliente" /></SelectTrigger>
                    <SelectContent>
                      {clients.filter(c => !c.is_prospect).map((c) => (
                        <SelectItem key={c.id} value={c.id}>
                          {c.name} {c.reference && `(${c.reference})`} {c.rfc && `- ${c.rfc}`}
                        </SelectItem>
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
              </div>

              {/* Items Section */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <Label className="text-sm font-medium">Conceptos / Partidas</Label>
                  <Button type="button" variant="outline" size="sm" onClick={addItem}>
                    <PlusCircle className="mr-1 h-4 w-4" />
                    Agregar
                  </Button>
                </div>
                {formData.items.map((item, index) => (
                  <div key={index} className="p-3 bg-slate-50 rounded-lg space-y-3 border">
                    <div className="grid grid-cols-12 gap-2 items-end">
                      <div className="col-span-12 md:col-span-5">
                        <Label className="text-xs">Descripción *</Label>
                        <Input
                          value={item.description}
                          onChange={(e) => handleItemChange(index, "description", e.target.value)}
                          placeholder="Descripción del servicio/producto"
                          required
                        />
                      </div>
                      <div className="col-span-3 md:col-span-2">
                        <Label className="text-xs">Cantidad</Label>
                        <Input
                          type="number"
                          value={item.quantity}
                          onChange={(e) => handleItemChange(index, "quantity", parseFloat(e.target.value) || 0)}
                        />
                      </div>
                      <div className="col-span-3 md:col-span-1">
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
                      <div className="col-span-2 md:col-span-2 flex items-end gap-1">
                        <div className="flex-1">
                          <Label className="text-xs">Total</Label>
                          <Input value={formatCurrency(item.quantity * item.unit_price)} disabled className="text-xs" />
                        </div>
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon"
                          onClick={() => removeItem(index)}
                          disabled={formData.items.length === 1}
                          className="h-9 w-9"
                        >
                          <MinusCircle className="h-4 w-4 text-red-500" />
                        </Button>
                      </div>
                    </div>
                    {/* SAT Keys */}
                    <div className="grid grid-cols-12 gap-2 items-end border-t pt-2">
                      <div className="col-span-6 md:col-span-5">
                        <Label className="text-xs text-blue-600">Clave SAT Producto/Servicio</Label>
                        <SATProductSearch
                          value={item.clave_prod_serv || ""}
                          onChange={(val) => handleItemChange(index, "clave_prod_serv", val)}
                          placeholder="Buscar clave SAT..."
                        />
                      </div>
                      <div className="col-span-6 md:col-span-3">
                        <Label className="text-xs text-blue-600">Clave Unidad SAT</Label>
                        <SATUnitSearch
                          value={item.clave_unidad || ""}
                          onChange={(val) => handleItemChange(index, "clave_unidad", val)}
                        />
                      </div>
                      <div className="col-span-12 md:col-span-4">
                        <p className="text-[10px] text-slate-400">Requeridos para facturación CFDI</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Totals */}
              <div className="space-y-2 p-4 bg-slate-100 rounded-lg">
                <div className="flex justify-between text-sm">
                  <span>Subtotal:</span>
                  <span className="font-medium">{formatCurrency(formData.subtotal)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>IVA (16%):</span>
                  <span className="font-medium">{formatCurrency(formData.tax)}</span>
                </div>
                <Separator />
                <div className="flex justify-between text-lg font-bold">
                  <span>Total:</span>
                  <span className="text-primary">{formatCurrency(formData.total)}</span>
                </div>
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>Cancelar</Button>
              <Button type="submit" className="btn-industrial">Registrar Factura</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Payment Dialog - Complemento de Pago CFDI */}
      <Dialog open={paymentDialogOpen} onOpenChange={setPaymentDialogOpen}>
        <DialogContent className="sm:max-w-[700px] max-h-[90vh] overflow-y-auto">
          <form onSubmit={handlePayment}>
            <DialogHeader>
              <DialogTitle>Registrar Abono / Complemento de Pago</DialogTitle>
              <DialogDescription>
                Factura: <strong>{selectedInvoice?.invoice_number}</strong> | 
                Total: {formatCurrency(selectedInvoice?.total || 0)} |
                Pagado: {formatCurrency(selectedInvoice?.paid_amount || 0)} |
                <span className="text-primary font-semibold"> Saldo: {formatCurrency((selectedInvoice?.total || 0) - (selectedInvoice?.paid_amount || 0))}</span>
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              {/* Sección: Datos del Pago */}
              <div className="space-y-3">
                <h4 className="text-sm font-semibold text-slate-700 flex items-center gap-2">
                  <DollarSign className="h-4 w-4" />
                  Datos del Pago
                </h4>
                <div className="grid grid-cols-3 gap-3">
                  <div className="grid gap-1">
                    <Label className="text-xs">Monto del Abono *</Label>
                    <Input
                      type="number"
                      step="0.01"
                      value={paymentForm.amount}
                      onChange={(e) => setPaymentForm({ ...paymentForm, amount: e.target.value })}
                      placeholder="0.00"
                      required
                      className="h-9"
                    />
                  </div>
                  <div className="grid gap-1">
                    <Label className="text-xs">Fecha de Pago *</Label>
                    <Input
                      type="date"
                      value={paymentForm.payment_date}
                      onChange={(e) => setPaymentForm({ ...paymentForm, payment_date: e.target.value })}
                      required
                      className="h-9"
                    />
                  </div>
                  <div className="grid gap-1">
                    <Label className="text-xs">No. Parcialidad</Label>
                    <Input
                      type="number"
                      min="1"
                      value={paymentForm.num_parcialidad}
                      onChange={(e) => setPaymentForm({ ...paymentForm, num_parcialidad: e.target.value })}
                      className="h-9"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="grid gap-1">
                    <Label className="text-xs">Forma de Pago SAT *</Label>
                    <Select
                      value={paymentForm.sat_forma_pago}
                      onValueChange={(value) => setPaymentForm({ ...paymentForm, sat_forma_pago: value })}
                    >
                      <SelectTrigger className="h-9"><SelectValue /></SelectTrigger>
                      <SelectContent>
                        {SAT_FORMAS_PAGO.map((m) => (
                          <SelectItem key={m.value} value={m.value}>{m.label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="grid gap-1">
                    <Label className="text-xs">Número de Operación</Label>
                    <Input
                      value={paymentForm.num_operacion}
                      onChange={(e) => setPaymentForm({ ...paymentForm, num_operacion: e.target.value })}
                      placeholder="No. transferencia, autorización, etc."
                      className="h-9"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-3">
                  <div className="grid gap-1">
                    <Label className="text-xs">Moneda del Pago</Label>
                    <Select
                      value={paymentForm.moneda_pago}
                      onValueChange={(value) => setPaymentForm({ ...paymentForm, moneda_pago: value })}
                    >
                      <SelectTrigger className="h-9"><SelectValue /></SelectTrigger>
                      <SelectContent>
                        {MONEDAS.map((m) => (
                          <SelectItem key={m.value} value={m.value}>{m.label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="grid gap-1">
                    <Label className="text-xs">Tipo de Cambio</Label>
                    <Input
                      type="number"
                      step="0.0001"
                      value={paymentForm.tipo_cambio}
                      onChange={(e) => setPaymentForm({ ...paymentForm, tipo_cambio: e.target.value })}
                      placeholder="1.0000"
                      disabled={paymentForm.moneda_pago === "MXN"}
                      className="h-9"
                    />
                  </div>
                  <div className="grid gap-1">
                    <Label className="text-xs">Método (interno)</Label>
                    <Select
                      value={paymentForm.payment_method}
                      onValueChange={(value) => setPaymentForm({ ...paymentForm, payment_method: value })}
                    >
                      <SelectTrigger className="h-9"><SelectValue /></SelectTrigger>
                      <SelectContent>
                        {PAYMENT_METHODS.map((m) => (
                          <SelectItem key={m.value} value={m.value}>{m.label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>

              <Separator />

              {/* Sección: Datos Bancarios */}
              <div className="space-y-3">
                <h4 className="text-sm font-semibold text-slate-700 flex items-center gap-2">
                  <CreditCard className="h-4 w-4" />
                  Datos Bancarios <span className="text-xs font-normal text-slate-400">(Opcionales para CFDI)</span>
                </h4>
                
                {/* Banco Ordenante (quien paga) */}
                <div className="p-3 bg-slate-50 rounded-lg space-y-2">
                  <p className="text-xs font-medium text-slate-600">Banco Ordenante (quien paga)</p>
                  <div className="grid grid-cols-3 gap-3">
                    <div className="grid gap-1">
                      <Label className="text-xs">RFC Banco</Label>
                      <Input
                        value={paymentForm.rfc_banco_ordenante}
                        onChange={(e) => setPaymentForm({ ...paymentForm, rfc_banco_ordenante: e.target.value.toUpperCase() })}
                        placeholder="BBA830831LJ2"
                        maxLength={12}
                        className="h-8 text-xs"
                      />
                    </div>
                    <div className="grid gap-1">
                      <Label className="text-xs">Nombre Banco</Label>
                      <Input
                        value={paymentForm.nombre_banco_ordenante}
                        onChange={(e) => setPaymentForm({ ...paymentForm, nombre_banco_ordenante: e.target.value })}
                        placeholder="BBVA México"
                        className="h-8 text-xs"
                      />
                    </div>
                    <div className="grid gap-1">
                      <Label className="text-xs">Cuenta Ordenante</Label>
                      <Input
                        value={paymentForm.cuenta_ordenante}
                        onChange={(e) => setPaymentForm({ ...paymentForm, cuenta_ordenante: e.target.value })}
                        placeholder="Últimos 4 dígitos o CLABE"
                        className="h-8 text-xs"
                      />
                    </div>
                  </div>
                </div>

                {/* Banco Beneficiario (quien recibe) */}
                <div className="p-3 bg-blue-50 rounded-lg space-y-2">
                  <p className="text-xs font-medium text-blue-700">Banco Beneficiario (quien recibe el pago)</p>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="grid gap-1">
                      <Label className="text-xs">RFC Banco</Label>
                      <Input
                        value={paymentForm.rfc_banco_beneficiario}
                        onChange={(e) => setPaymentForm({ ...paymentForm, rfc_banco_beneficiario: e.target.value.toUpperCase() })}
                        placeholder="BNM840515VB1"
                        maxLength={12}
                        className="h-8 text-xs"
                      />
                    </div>
                    <div className="grid gap-1">
                      <Label className="text-xs">Cuenta Beneficiaria</Label>
                      <Input
                        value={paymentForm.cuenta_beneficiaria}
                        onChange={(e) => setPaymentForm({ ...paymentForm, cuenta_beneficiaria: e.target.value })}
                        placeholder="CLABE o No. Cuenta"
                        className="h-8 text-xs"
                      />
                    </div>
                  </div>
                </div>
              </div>

              <Separator />

              {/* Sección: Comprobante y Notas */}
              <div className="space-y-3">
                <h4 className="text-sm font-semibold text-slate-700 flex items-center gap-2">
                  <FileText className="h-4 w-4" />
                  Comprobante y Notas
                </h4>
                <div className="grid grid-cols-2 gap-3">
                  <div className="grid gap-1">
                    <Label className="text-xs">Comprobante de Pago</Label>
                    <Input
                      type="file"
                      accept=".pdf,.png,.jpg,.jpeg"
                      onChange={(e) => setPaymentForm({ ...paymentForm, proof_file: e.target.files?.[0] })}
                      className="h-9 text-xs"
                    />
                    <p className="text-[10px] text-muted-foreground">PDF o imagen del comprobante bancario</p>
                  </div>
                  <div className="grid gap-1">
                    <Label className="text-xs">Referencia</Label>
                    <Input
                      value={paymentForm.reference}
                      onChange={(e) => setPaymentForm({ ...paymentForm, reference: e.target.value })}
                      placeholder="No. de cheque, folio, etc."
                      className="h-9"
                    />
                  </div>
                </div>
                <div className="grid gap-1">
                  <Label className="text-xs">Notas / Observaciones</Label>
                  <Textarea
                    value={paymentForm.notes}
                    onChange={(e) => setPaymentForm({ ...paymentForm, notes: e.target.value })}
                    placeholder="Observaciones adicionales del pago..."
                    rows={2}
                    className="text-xs"
                  />
                </div>
              </div>

              {/* Resumen del documento relacionado */}
              {selectedInvoice?.sat_invoice_uuid && (
                <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                  <p className="text-xs font-medium text-green-700 mb-2">Documento Relacionado (CFDI)</p>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div><span className="text-slate-500">UUID:</span> <span className="font-mono">{selectedInvoice.sat_invoice_uuid}</span></div>
                    <div><span className="text-slate-500">Folio:</span> {selectedInvoice.invoice_number}</div>
                    <div><span className="text-slate-500">Total Factura:</span> {formatCurrency(selectedInvoice.total)}</div>
                    <div><span className="text-slate-500">Saldo Anterior:</span> {formatCurrency((selectedInvoice.total || 0) - (selectedInvoice.paid_amount || 0))}</div>
                  </div>
                </div>
              )}

              {/* Info para CFDI */}
              <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg">
                <p className="text-xs text-amber-700">
                  <strong>Nota:</strong> Los datos bancarios son opcionales pero recomendados para el complemento de pago CFDI 4.0. 
                  El saldo insoluto se calculará automáticamente al registrar el pago.
                </p>
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setPaymentDialogOpen(false)}>Cancelar</Button>
              <Button type="submit" className="btn-industrial">Registrar Abono</Button>
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
