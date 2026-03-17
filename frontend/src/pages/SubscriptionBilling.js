import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { formatCurrency, formatDate } from "../lib/utils";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Badge } from "../components/ui/badge";
import { Textarea } from "../components/ui/textarea";
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
  DropdownMenuTrigger,
} from "../components/ui/dropdown-menu";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { toast } from "sonner";
import {
  ArrowLeft,
  CreditCard,
  Building2,
  DollarSign,
  Plus,
  MoreVertical,
  CheckCircle,
  Clock,
  AlertTriangle,
  Banknote,
  Settings,
  FileText,
  TrendingUp,
  Calendar,
  RefreshCw,
  Trash2,
  Eye,
  Receipt,
} from "lucide-react";

const SubscriptionBilling = () => {
  const { api } = useAuth();
  const navigate = useNavigate();
  
  // State
  const [loading, setLoading] = useState(true);
  const [dashboard, setDashboard] = useState(null);
  const [invoices, setInvoices] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [plans, setPlans] = useState([]);
  const [billingCycles, setBillingCycles] = useState([]);
  const [config, setConfig] = useState({
    stripe_enabled: true,
    bank_transfer_enabled: true,
    bank_accounts: [],
    generate_cfdi: false,
    cfdi_serie: "S",
    reminder_days_before: [15, 7, 3, 1],
    auto_suspend_days_after: 5,
  });
  
  // Dialog states
  const [createInvoiceDialogOpen, setCreateInvoiceDialogOpen] = useState(false);
  const [recordPaymentDialogOpen, setRecordPaymentDialogOpen] = useState(false);
  const [configDialogOpen, setConfigDialogOpen] = useState(false);
  const [selectedInvoice, setSelectedInvoice] = useState(null);
  
  // Form states
  const [newInvoiceForm, setNewInvoiceForm] = useState({
    company_id: "",
    plan_id: "base",
    billing_cycle: "monthly",
    notes: ""
  });
  const [paymentForm, setPaymentForm] = useState({
    payment_method: "bank_transfer",
    payment_reference: "",
    notes: ""
  });
  const [newBankAccount, setNewBankAccount] = useState({
    bank_name: "",
    account_holder: "",
    account_number: "",
    clabe: "",
    reference_instructions: "Usar RFC de la empresa como referencia",
    additional_notes: ""
  });
  
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [dashboardRes, invoicesRes, plansRes, configRes, companiesRes] = await Promise.all([
        api.get("/subscriptions/dashboard"),
        api.get("/subscriptions/invoices"),
        api.get("/subscriptions/plans"),
        api.get("/subscriptions/config"),
        api.get("/super-admin/companies")
      ]);
      
      setDashboard(dashboardRes.data);
      setInvoices(invoicesRes.data);
      setPlans(plansRes.data.plans || []);
      setBillingCycles(plansRes.data.billing_cycles || []);
      setConfig(configRes.data);
      setCompanies(companiesRes.data || []);
    } catch (error) {
      console.error("Error fetching data:", error);
      toast.error("Error al cargar datos");
    } finally {
      setLoading(false);
    }
  };

  const handleCreateInvoice = async (e) => {
    e.preventDefault();
    if (!newInvoiceForm.company_id) {
      toast.error("Selecciona una empresa");
      return;
    }
    
    setSubmitting(true);
    try {
      await api.post("/subscriptions/invoices", newInvoiceForm);
      toast.success("Factura de suscripción creada");
      setCreateInvoiceDialogOpen(false);
      setNewInvoiceForm({ company_id: "", plan_id: "base", billing_cycle: "monthly", notes: "" });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al crear factura");
    } finally {
      setSubmitting(false);
    }
  };

  const handleRecordPayment = async (e) => {
    e.preventDefault();
    if (!selectedInvoice) return;
    
    setSubmitting(true);
    try {
      await api.post(`/subscriptions/invoices/${selectedInvoice.id}/record-payment`, {
        invoice_id: selectedInvoice.id,
        ...paymentForm
      });
      toast.success("Pago registrado exitosamente");
      setRecordPaymentDialogOpen(false);
      setSelectedInvoice(null);
      setPaymentForm({ payment_method: "bank_transfer", payment_reference: "", notes: "" });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al registrar pago");
    } finally {
      setSubmitting(false);
    }
  };

  const handleSaveConfig = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await api.post("/subscriptions/config", config);
      toast.success("Configuración guardada");
      setConfigDialogOpen(false);
    } catch (error) {
      toast.error("Error al guardar configuración");
    } finally {
      setSubmitting(false);
    }
  };

  const addBankAccount = () => {
    if (!newBankAccount.bank_name || !newBankAccount.clabe) {
      toast.error("Completa los campos requeridos");
      return;
    }
    setConfig({
      ...config,
      bank_accounts: [...config.bank_accounts, { ...newBankAccount }]
    });
    setNewBankAccount({
      bank_name: "",
      account_holder: "",
      account_number: "",
      clabe: "",
      reference_instructions: "Usar RFC de la empresa como referencia",
      additional_notes: ""
    });
  };

  const removeBankAccount = (index) => {
    const updated = [...config.bank_accounts];
    updated.splice(index, 1);
    setConfig({ ...config, bank_accounts: updated });
  };

  const getStatusBadge = (status) => {
    const styles = {
      pending: "bg-yellow-500/20 text-yellow-300 border-yellow-500/30",
      paid: "bg-emerald-500/20 text-emerald-300 border-emerald-500/30",
      overdue: "bg-red-500/20 text-red-300 border-red-500/30",
      cancelled: "bg-slate-500/20 text-slate-300 border-slate-500/30"
    };
    const labels = {
      pending: "Pendiente",
      paid: "Pagada",
      overdue: "Vencida",
      cancelled: "Cancelada"
    };
    return (
      <Badge variant="outline" className={styles[status] || styles.pending}>
        {labels[status] || status}
      </Badge>
    );
  };

  const calculatePreview = () => {
    const plan = plans.find(p => p.id === newInvoiceForm.plan_id);
    const cycle = billingCycles.find(c => c.id === newInvoiceForm.billing_cycle);
    if (!plan || !cycle) return null;
    
    const subtotal = plan.price * cycle.months;
    const discount = subtotal * cycle.discount;
    const total = subtotal - discount;
    
    return { subtotal, discount, total, months: cycle.months };
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-amber-500"></div>
      </div>
    );
  }

  const preview = calculatePreview();

  return (
    <div className="min-h-screen bg-slate-900" data-testid="subscription-billing-page">
      {/* Header */}
      <div className="bg-slate-800 border-b border-slate-700">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Button 
              variant="ghost" 
              size="icon" 
              onClick={() => navigate("/admin-portal/dashboard")}
              className="text-slate-400 hover:text-white"
            >
              <ArrowLeft className="h-5 w-5" />
            </Button>
            <div>
              <h1 className="text-xl font-bold text-white font-[Chivo] flex items-center gap-2">
                <CreditCard className="h-6 w-6 text-amber-500" />
                Facturación de Suscripciones
              </h1>
              <p className="text-sm text-slate-400">Gestión de pagos y facturación a clientes</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              className="border-slate-600 text-slate-300"
              onClick={() => setConfigDialogOpen(true)}
              data-testid="config-btn"
            >
              <Settings className="mr-2 h-4 w-4" />
              Configuración
            </Button>
            <Button
              className="bg-amber-500 hover:bg-amber-600 text-slate-900"
              onClick={() => setCreateInvoiceDialogOpen(true)}
              data-testid="create-invoice-btn"
            >
              <Plus className="mr-2 h-4 w-4" />
              Nueva Factura
            </Button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-6 space-y-6">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="bg-slate-800 border-slate-700">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400">Pendiente de Cobro</p>
                  <p className="text-2xl font-bold text-amber-400">
                    {formatCurrency(dashboard?.stats?.total_pending || 0)}
                  </p>
                </div>
                <Clock className="h-8 w-8 text-amber-500/50" />
              </div>
            </CardContent>
          </Card>
          <Card className="bg-slate-800 border-slate-700">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400">Cobrado Este Mes</p>
                  <p className="text-2xl font-bold text-emerald-400">
                    {formatCurrency(dashboard?.stats?.total_paid_this_month || 0)}
                  </p>
                </div>
                <CheckCircle className="h-8 w-8 text-emerald-500/50" />
              </div>
            </CardContent>
          </Card>
          <Card className="bg-slate-800 border-slate-700">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400">Facturas Pendientes</p>
                  <p className="text-2xl font-bold text-white">
                    {dashboard?.stats?.pending_count || 0}
                  </p>
                </div>
                <FileText className="h-8 w-8 text-slate-500" />
              </div>
            </CardContent>
          </Card>
          <Card className="bg-slate-800 border-slate-700">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400">Vencidas</p>
                  <p className="text-2xl font-bold text-red-400">
                    {dashboard?.stats?.overdue_count || 0}
                  </p>
                </div>
                <AlertTriangle className="h-8 w-8 text-red-500/50" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Monthly Revenue Chart */}
        {dashboard?.monthly_revenue && dashboard.monthly_revenue.length > 0 && (
          <Card className="bg-slate-800 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-emerald-500" />
                Ingresos por Suscripciones
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex gap-2 items-end h-40">
                {dashboard.monthly_revenue.map((month, idx) => {
                  const maxRevenue = Math.max(...dashboard.monthly_revenue.map(m => m.revenue || 1));
                  const height = maxRevenue > 0 ? (month.revenue / maxRevenue) * 100 : 0;
                  return (
                    <div key={idx} className="flex-1 flex flex-col items-center gap-1">
                      <div 
                        className="w-full bg-emerald-500/30 rounded-t hover:bg-emerald-500/50 transition-colors relative group"
                        style={{ height: `${Math.max(height, 5)}%` }}
                      >
                        <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-slate-700 px-2 py-1 rounded text-xs text-white opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
                          {formatCurrency(month.revenue)}
                        </div>
                      </div>
                      <span className="text-xs text-slate-500">{month.month}</span>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Tabs */}
        <Tabs defaultValue="pending" className="w-full">
          <TabsList className="bg-slate-800 border border-slate-700">
            <TabsTrigger value="pending" className="data-[state=active]:bg-amber-500 data-[state=active]:text-slate-900">
              Pendientes ({dashboard?.stats?.pending_count || 0})
            </TabsTrigger>
            <TabsTrigger value="all" className="data-[state=active]:bg-amber-500 data-[state=active]:text-slate-900">
              Todas las Facturas
            </TabsTrigger>
            <TabsTrigger value="expiring" className="data-[state=active]:bg-amber-500 data-[state=active]:text-slate-900">
              Por Vencer ({dashboard?.expiring_soon?.length || 0})
            </TabsTrigger>
          </TabsList>

          <TabsContent value="pending" className="mt-4">
            <Card className="bg-slate-800 border-slate-700">
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow className="border-slate-700 hover:bg-slate-800">
                      <TableHead className="text-slate-300">Factura</TableHead>
                      <TableHead className="text-slate-300">Empresa</TableHead>
                      <TableHead className="text-slate-300">Plan</TableHead>
                      <TableHead className="text-slate-300">Período</TableHead>
                      <TableHead className="text-slate-300">Total</TableHead>
                      <TableHead className="text-slate-300">Estado</TableHead>
                      <TableHead className="w-[50px]"></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {invoices.filter(i => i.status === "pending" || i.status === "overdue").length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={7} className="text-center py-8 text-slate-500">
                          No hay facturas pendientes
                        </TableCell>
                      </TableRow>
                    ) : (
                      invoices.filter(i => i.status === "pending" || i.status === "overdue").map((invoice) => (
                        <TableRow key={invoice.id} className="border-slate-700 hover:bg-slate-700/50">
                          <TableCell className="text-white font-medium">{invoice.invoice_number}</TableCell>
                          <TableCell className="text-slate-300">{invoice.company_name}</TableCell>
                          <TableCell className="text-slate-300">{invoice.plan_name}</TableCell>
                          <TableCell className="text-slate-400 text-sm">
                            {invoice.billing_cycle === "monthly" ? "Mensual" :
                             invoice.billing_cycle === "quarterly" ? "Trimestral" :
                             invoice.billing_cycle === "semiannual" ? "Semestral" : "Anual"}
                          </TableCell>
                          <TableCell className="text-amber-400 font-semibold">{formatCurrency(invoice.total)}</TableCell>
                          <TableCell>{getStatusBadge(invoice.status)}</TableCell>
                          <TableCell>
                            <DropdownMenu>
                              <DropdownMenuTrigger asChild>
                                <Button variant="ghost" size="icon" className="text-slate-400">
                                  <MoreVertical className="h-4 w-4" />
                                </Button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end" className="bg-slate-800 border-slate-700">
                                <DropdownMenuItem 
                                  className="text-emerald-400"
                                  onClick={() => {
                                    setSelectedInvoice(invoice);
                                    setRecordPaymentDialogOpen(true);
                                  }}
                                >
                                  <Banknote className="mr-2 h-4 w-4" />
                                  Registrar Pago
                                </DropdownMenuItem>
                                <DropdownMenuItem className="text-slate-300">
                                  <Eye className="mr-2 h-4 w-4" />
                                  Ver Detalle
                                </DropdownMenuItem>
                              </DropdownMenuContent>
                            </DropdownMenu>
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="all" className="mt-4">
            <Card className="bg-slate-800 border-slate-700">
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow className="border-slate-700 hover:bg-slate-800">
                      <TableHead className="text-slate-300">Factura</TableHead>
                      <TableHead className="text-slate-300">Empresa</TableHead>
                      <TableHead className="text-slate-300">Plan</TableHead>
                      <TableHead className="text-slate-300">Total</TableHead>
                      <TableHead className="text-slate-300">Método</TableHead>
                      <TableHead className="text-slate-300">Fecha Pago</TableHead>
                      <TableHead className="text-slate-300">Estado</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {invoices.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={7} className="text-center py-8 text-slate-500">
                          No hay facturas registradas
                        </TableCell>
                      </TableRow>
                    ) : (
                      invoices.map((invoice) => (
                        <TableRow key={invoice.id} className="border-slate-700 hover:bg-slate-700/50">
                          <TableCell className="text-white font-medium">{invoice.invoice_number}</TableCell>
                          <TableCell className="text-slate-300">{invoice.company_name}</TableCell>
                          <TableCell className="text-slate-300">{invoice.plan_name}</TableCell>
                          <TableCell className="text-white font-semibold">{formatCurrency(invoice.total)}</TableCell>
                          <TableCell className="text-slate-400 capitalize">
                            {invoice.payment_method || "-"}
                          </TableCell>
                          <TableCell className="text-slate-400">
                            {invoice.payment_date ? formatDate(invoice.payment_date) : "-"}
                          </TableCell>
                          <TableCell>{getStatusBadge(invoice.status)}</TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="expiring" className="mt-4">
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white text-lg flex items-center gap-2">
                  <Calendar className="h-5 w-5 text-amber-500" />
                  Suscripciones por Vencer (próximos 15 días)
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow className="border-slate-700 hover:bg-slate-800">
                      <TableHead className="text-slate-300">Empresa</TableHead>
                      <TableHead className="text-slate-300">Vencimiento</TableHead>
                      <TableHead className="text-slate-300">Mensualidad</TableHead>
                      <TableHead className="text-slate-300">Acción</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {(!dashboard?.expiring_soon || dashboard.expiring_soon.length === 0) ? (
                      <TableRow>
                        <TableCell colSpan={4} className="text-center py-8 text-slate-500">
                          No hay suscripciones próximas a vencer
                        </TableCell>
                      </TableRow>
                    ) : (
                      dashboard.expiring_soon.map((company) => (
                        <TableRow key={company.id} className="border-slate-700 hover:bg-slate-700/50">
                          <TableCell className="text-white font-medium">{company.business_name}</TableCell>
                          <TableCell className="text-amber-400">
                            {formatDate(company.subscription_end)}
                          </TableCell>
                          <TableCell className="text-slate-300">{formatCurrency(company.monthly_fee || 2500)}</TableCell>
                          <TableCell>
                            <Button 
                              size="sm" 
                              className="bg-amber-500 hover:bg-amber-600 text-slate-900"
                              onClick={() => {
                                setNewInvoiceForm({ ...newInvoiceForm, company_id: company.id });
                                setCreateInvoiceDialogOpen(true);
                              }}
                            >
                              <Receipt className="mr-2 h-4 w-4" />
                              Generar Factura
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>

      {/* Create Invoice Dialog */}
      <Dialog open={createInvoiceDialogOpen} onOpenChange={setCreateInvoiceDialogOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <form onSubmit={handleCreateInvoice}>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Receipt className="h-5 w-5 text-amber-500" />
                Nueva Factura de Suscripción
              </DialogTitle>
              <DialogDescription>
                Genera una factura para cobrar la suscripción a una empresa
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="grid gap-2">
                <Label>Empresa *</Label>
                <Select 
                  value={newInvoiceForm.company_id} 
                  onValueChange={(v) => setNewInvoiceForm({ ...newInvoiceForm, company_id: v })}
                >
                  <SelectTrigger data-testid="select-company">
                    <SelectValue placeholder="Selecciona una empresa" />
                  </SelectTrigger>
                  <SelectContent>
                    {companies.map((c) => (
                      <SelectItem key={c.id} value={c.id}>{c.business_name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="grid gap-2">
                  <Label>Plan</Label>
                  <Select 
                    value={newInvoiceForm.plan_id} 
                    onValueChange={(v) => setNewInvoiceForm({ ...newInvoiceForm, plan_id: v })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {plans.map((p) => (
                        <SelectItem key={p.id} value={p.id}>
                          {p.name} - {formatCurrency(p.price)}/mes
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid gap-2">
                  <Label>Período</Label>
                  <Select 
                    value={newInvoiceForm.billing_cycle} 
                    onValueChange={(v) => setNewInvoiceForm({ ...newInvoiceForm, billing_cycle: v })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {billingCycles.map((c) => (
                        <SelectItem key={c.id} value={c.id}>
                          {c.label} {c.discount > 0 ? `(-${c.discount * 100}%)` : ""}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {preview && (
                <div className="bg-slate-100 dark:bg-slate-800 rounded-lg p-4 space-y-2">
                  <h4 className="font-semibold text-sm">Resumen</h4>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Subtotal ({preview.months} mes{preview.months > 1 ? "es" : ""}):</span>
                    <span>{formatCurrency(preview.subtotal)}</span>
                  </div>
                  {preview.discount > 0 && (
                    <div className="flex justify-between text-sm text-emerald-600">
                      <span>Descuento:</span>
                      <span>-{formatCurrency(preview.discount)}</span>
                    </div>
                  )}
                  <Separator />
                  <div className="flex justify-between font-bold">
                    <span>Total:</span>
                    <span className="text-amber-600">{formatCurrency(preview.total)}</span>
                  </div>
                </div>
              )}

              <div className="grid gap-2">
                <Label>Notas (opcional)</Label>
                <Textarea 
                  value={newInvoiceForm.notes}
                  onChange={(e) => setNewInvoiceForm({ ...newInvoiceForm, notes: e.target.value })}
                  placeholder="Notas adicionales para la factura"
                  rows={2}
                />
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setCreateInvoiceDialogOpen(false)}>
                Cancelar
              </Button>
              <Button type="submit" className="bg-amber-500 hover:bg-amber-600 text-slate-900" disabled={submitting}>
                {submitting ? <RefreshCw className="mr-2 h-4 w-4 animate-spin" /> : <Plus className="mr-2 h-4 w-4" />}
                Crear Factura
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Record Payment Dialog */}
      <Dialog open={recordPaymentDialogOpen} onOpenChange={setRecordPaymentDialogOpen}>
        <DialogContent className="sm:max-w-[450px]">
          <form onSubmit={handleRecordPayment}>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Banknote className="h-5 w-5 text-emerald-500" />
                Registrar Pago
              </DialogTitle>
              <DialogDescription>
                {selectedInvoice && (
                  <span>
                    Factura {selectedInvoice.invoice_number} - {formatCurrency(selectedInvoice.total)}
                  </span>
                )}
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="grid gap-2">
                <Label>Método de Pago</Label>
                <Select 
                  value={paymentForm.payment_method} 
                  onValueChange={(v) => setPaymentForm({ ...paymentForm, payment_method: v })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="bank_transfer">Transferencia Bancaria</SelectItem>
                    <SelectItem value="cash">Efectivo</SelectItem>
                    <SelectItem value="other">Otro</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div className="grid gap-2">
                <Label>Referencia de Pago</Label>
                <Input 
                  value={paymentForm.payment_reference}
                  onChange={(e) => setPaymentForm({ ...paymentForm, payment_reference: e.target.value })}
                  placeholder="Número de transferencia, folio, etc."
                />
              </div>

              <div className="grid gap-2">
                <Label>Notas</Label>
                <Textarea 
                  value={paymentForm.notes}
                  onChange={(e) => setPaymentForm({ ...paymentForm, notes: e.target.value })}
                  placeholder="Notas adicionales"
                  rows={2}
                />
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setRecordPaymentDialogOpen(false)}>
                Cancelar
              </Button>
              <Button type="submit" className="bg-emerald-500 hover:bg-emerald-600 text-white" disabled={submitting}>
                {submitting ? <RefreshCw className="mr-2 h-4 w-4 animate-spin" /> : <CheckCircle className="mr-2 h-4 w-4" />}
                Confirmar Pago
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Configuration Dialog */}
      <Dialog open={configDialogOpen} onOpenChange={setConfigDialogOpen}>
        <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
          <form onSubmit={handleSaveConfig}>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Settings className="h-5 w-5 text-blue-500" />
                Configuración de Facturación
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-6 py-4">
              {/* Payment Methods */}
              <div>
                <h4 className="font-semibold mb-3">Métodos de Pago Habilitados</h4>
                <div className="space-y-2">
                  <label className="flex items-center gap-2">
                    <input 
                      type="checkbox" 
                      checked={config.stripe_enabled}
                      onChange={(e) => setConfig({ ...config, stripe_enabled: e.target.checked })}
                      className="rounded"
                    />
                    <CreditCard className="h-4 w-4 text-blue-500" />
                    <span>Pago con Tarjeta (Stripe)</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <input 
                      type="checkbox" 
                      checked={config.bank_transfer_enabled}
                      onChange={(e) => setConfig({ ...config, bank_transfer_enabled: e.target.checked })}
                      className="rounded"
                    />
                    <Banknote className="h-4 w-4 text-emerald-500" />
                    <span>Transferencia Bancaria</span>
                  </label>
                </div>
              </div>

              <Separator />

              {/* Bank Accounts */}
              <div>
                <h4 className="font-semibold mb-3">Cuentas Bancarias para Depósito</h4>
                
                {config.bank_accounts.map((account, idx) => (
                  <div key={idx} className="bg-slate-100 dark:bg-slate-800 rounded-lg p-3 mb-2">
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="font-medium">{account.bank_name}</p>
                        <p className="text-sm text-muted-foreground">Titular: {account.account_holder}</p>
                        <p className="text-sm text-muted-foreground">CLABE: {account.clabe}</p>
                      </div>
                      <Button 
                        type="button" 
                        variant="ghost" 
                        size="icon"
                        onClick={() => removeBankAccount(idx)}
                        className="text-red-500"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}

                <div className="border rounded-lg p-3 space-y-3">
                  <h5 className="text-sm font-medium">Agregar Cuenta</h5>
                  <div className="grid grid-cols-2 gap-3">
                    <Input 
                      placeholder="Banco"
                      value={newBankAccount.bank_name}
                      onChange={(e) => setNewBankAccount({ ...newBankAccount, bank_name: e.target.value })}
                    />
                    <Input 
                      placeholder="Titular"
                      value={newBankAccount.account_holder}
                      onChange={(e) => setNewBankAccount({ ...newBankAccount, account_holder: e.target.value })}
                    />
                  </div>
                  <Input 
                    placeholder="Número de Cuenta"
                    value={newBankAccount.account_number}
                    onChange={(e) => setNewBankAccount({ ...newBankAccount, account_number: e.target.value })}
                  />
                  <Input 
                    placeholder="CLABE Interbancaria (18 dígitos)"
                    value={newBankAccount.clabe}
                    onChange={(e) => setNewBankAccount({ ...newBankAccount, clabe: e.target.value })}
                    maxLength={18}
                  />
                  <Input 
                    placeholder="Instrucciones de referencia"
                    value={newBankAccount.reference_instructions}
                    onChange={(e) => setNewBankAccount({ ...newBankAccount, reference_instructions: e.target.value })}
                  />
                  <Button type="button" variant="outline" size="sm" onClick={addBankAccount}>
                    <Plus className="mr-2 h-4 w-4" />
                    Agregar Cuenta
                  </Button>
                </div>
              </div>

              <Separator />

              {/* Automation Settings */}
              <div>
                <h4 className="font-semibold mb-3">Configuración de Avisos</h4>
                <div className="grid gap-3">
                  <div className="grid gap-2">
                    <Label>Días antes de vencimiento para avisar (separados por coma)</Label>
                    <Input 
                      value={config.reminder_days_before?.join(", ") || "15, 7, 3, 1"}
                      onChange={(e) => setConfig({ 
                        ...config, 
                        reminder_days_before: e.target.value.split(",").map(d => parseInt(d.trim())).filter(d => !isNaN(d))
                      })}
                      placeholder="15, 7, 3, 1"
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label>Días después de vencimiento para suspender automáticamente</Label>
                    <Input 
                      type="number"
                      value={config.auto_suspend_days_after || 5}
                      onChange={(e) => setConfig({ ...config, auto_suspend_days_after: parseInt(e.target.value) || 5 })}
                      min={1}
                      max={30}
                    />
                  </div>
                </div>
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setConfigDialogOpen(false)}>
                Cancelar
              </Button>
              <Button type="submit" className="bg-blue-500 hover:bg-blue-600 text-white" disabled={submitting}>
                Guardar Configuración
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default SubscriptionBilling;
