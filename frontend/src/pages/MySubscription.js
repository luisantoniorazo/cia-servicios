import React, { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { formatCurrency, formatDate } from "../lib/utils";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Separator } from "../components/ui/separator";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
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
import { toast } from "sonner";
import {
  CreditCard,
  Building2,
  Calendar,
  Clock,
  CheckCircle,
  AlertTriangle,
  Banknote,
  FileText,
  Copy,
  RefreshCw,
  Sparkles,
  Shield,
  Upload,
  Image,
} from "lucide-react";

const MySubscription = () => {
  const { api, user } = useAuth();
  
  // State
  const [loading, setLoading] = useState(true);
  const [subscription, setSubscription] = useState(null);
  const [pendingInvoices, setPendingInvoices] = useState([]);
  const [paymentHistory, setPaymentHistory] = useState([]);
  const [bankAccounts, setBankAccounts] = useState([]);
  const [plans, setPlans] = useState([]);
  const [billingCycles, setBillingCycles] = useState([]);
  
  // Dialog states
  const [requestInvoiceDialogOpen, setRequestInvoiceDialogOpen] = useState(false);
  const [paymentDialogOpen, setPaymentDialogOpen] = useState(false);
  const [uploadReceiptDialogOpen, setUploadReceiptDialogOpen] = useState(false);
  const [selectedInvoice, setSelectedInvoice] = useState(null);
  
  // Form states
  const [requestForm, setRequestForm] = useState({
    plan_id: "base",
    billing_cycle: "monthly"
  });
  const [receiptForm, setReceiptForm] = useState({
    file: null,
    reference: "",
    notes: ""
  });
  const [processingPayment, setProcessingPayment] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [uploadingReceipt, setUploadingReceipt] = useState(false);

  useEffect(() => {
    fetchData();
    // Check for Stripe return
    checkStripeReturn();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const response = await api.get("/subscriptions/my-subscription");
      setSubscription(response.data.subscription);
      setPendingInvoices(response.data.pending_invoices || []);
      setPaymentHistory(response.data.payment_history || []);
      setBankAccounts(response.data.bank_accounts || []);
      setPlans(response.data.plans || []);
      setBillingCycles(response.data.billing_cycles || []);
    } catch (error) {
      console.error("Error fetching subscription:", error);
      toast.error("Error al cargar información de suscripción");
    } finally {
      setLoading(false);
    }
  };

  const checkStripeReturn = () => {
    const urlParams = new URLSearchParams(window.location.search);
    const sessionId = urlParams.get('session_id');
    
    if (sessionId) {
      pollPaymentStatus(sessionId);
      // Clean URL
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  };

  const pollPaymentStatus = async (sessionId, attempts = 0) => {
    const maxAttempts = 10;
    const pollInterval = 2000;

    if (attempts >= maxAttempts) {
      toast.error("No se pudo verificar el estado del pago. Por favor revisa tu email o contacta a soporte.");
      return;
    }

    try {
      const response = await api.get(`/subscriptions/checkout/status/${sessionId}`);
      
      if (response.data.payment_status === 'paid') {
        toast.success("¡Pago exitoso! Tu suscripción ha sido actualizada.");
        fetchData();
        return;
      } else if (response.data.status === 'expired') {
        toast.error("La sesión de pago ha expirado. Por favor intenta de nuevo.");
        return;
      }

      // Continue polling
      setTimeout(() => pollPaymentStatus(sessionId, attempts + 1), pollInterval);
    } catch (error) {
      console.error("Error checking payment status:", error);
      setTimeout(() => pollPaymentStatus(sessionId, attempts + 1), pollInterval);
    }
  };

  const handleRequestInvoice = async () => {
    setSubmitting(true);
    try {
      const params = new URLSearchParams({
        plan_id: requestForm.plan_id,
        billing_cycle: requestForm.billing_cycle
      });
      await api.post(`/subscriptions/request-invoice?${params.toString()}`);
      toast.success("Solicitud de factura enviada");
      setRequestInvoiceDialogOpen(false);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al solicitar factura");
    } finally {
      setSubmitting(false);
    }
  };

  const handleStripePayment = async (invoice) => {
    setProcessingPayment(true);
    try {
      const originUrl = window.location.origin;
      const response = await api.post("/subscriptions/checkout/create-session", {
        invoice_id: invoice.id,
        origin_url: originUrl
      });
      
      if (response.data.url) {
        window.location.href = response.data.url;
      } else {
        toast.error("Error al crear sesión de pago");
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al procesar pago");
    } finally {
      setProcessingPayment(false);
    }
  };

  const handleQuickStripePayment = async () => {
    setProcessingPayment(true);
    try {
      const originUrl = window.location.origin;
      const response = await api.post("/subscriptions/checkout/quick-payment", {
        origin_url: originUrl
      });
      
      if (response.data.url) {
        window.location.href = response.data.url;
      } else {
        toast.error("Error al crear sesión de pago");
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al procesar pago");
    } finally {
      setProcessingPayment(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success("Copiado al portapapeles");
  };

  const handleUploadReceipt = async () => {
    if (!receiptForm.file) {
      toast.error("Por favor selecciona un archivo");
      return;
    }
    
    setUploadingReceipt(true);
    try {
      // Convert file to base64
      const reader = new FileReader();
      reader.readAsDataURL(receiptForm.file);
      
      reader.onload = async () => {
        const base64 = reader.result.split(',')[1];
        
        await api.post(`/subscriptions/invoices/${selectedInvoice.id}/upload-receipt`, {
          file_content: base64,
          file_name: receiptForm.file.name,
          file_type: receiptForm.file.type,
          reference: receiptForm.reference,
          notes: receiptForm.notes
        });
        
        toast.success("Comprobante enviado correctamente. Revisaremos tu pago pronto.");
        setUploadReceiptDialogOpen(false);
        setReceiptForm({ file: null, reference: "", notes: "" });
        fetchData();
        setUploadingReceipt(false);
      };
      
      reader.onerror = () => {
        toast.error("Error al leer el archivo");
        setUploadingReceipt(false);
      };
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al subir comprobante");
      setUploadingReceipt(false);
    }
  };

  const openUploadReceiptDialog = (invoice) => {
    setSelectedInvoice(invoice);
    setReceiptForm({ file: null, reference: "", notes: "" });
    setUploadReceiptDialogOpen(true);
  };

  const getStatusInfo = (status) => {
    const statusMap = {
      active: { label: "Activa", color: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30", icon: CheckCircle },
      pending: { label: "Pendiente", color: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30", icon: Clock },
      suspended: { label: "Suspendida", color: "bg-red-500/20 text-red-400 border-red-500/30", icon: AlertTriangle },
      trial: { label: "Prueba", color: "bg-blue-500/20 text-blue-400 border-blue-500/30", icon: Sparkles },
    };
    return statusMap[status] || statusMap.pending;
  };

  const calculateDaysRemaining = (endDate) => {
    if (!endDate) return null;
    const end = new Date(endDate);
    const now = new Date();
    const diff = Math.ceil((end - now) / (1000 * 60 * 60 * 24));
    return diff;
  };

  const calculatePreview = () => {
    const plan = plans.find(p => p.id === requestForm.plan_id);
    const cycle = billingCycles.find(c => c.id === requestForm.billing_cycle);
    if (!plan || !cycle) return null;
    
    const subtotal = plan.price * cycle.months;
    const discount = subtotal * cycle.discount;
    const total = subtotal - discount;
    
    return { subtotal, discount, total, months: cycle.months, plan, cycle };
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  const statusInfo = getStatusInfo(subscription?.status);
  const daysRemaining = calculateDaysRemaining(subscription?.end_date);
  const preview = calculatePreview();
  const StatusIcon = statusInfo.icon;

  return (
    <div className="space-y-6" data-testid="my-subscription-page">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Mi Suscripción</h1>
        <p className="text-muted-foreground">
          Gestiona tu plan y pagos de suscripción
        </p>
      </div>

      {/* Current Subscription Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5 text-primary" />
            Estado de Suscripción
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <Badge variant="outline" className={statusInfo.color}>
                  <StatusIcon className="h-3 w-3 mr-1" />
                  {statusInfo.label}
                </Badge>
                {subscription?.billing_included && (
                  <Badge variant="outline" className="bg-purple-500/20 text-purple-400 border-purple-500/30">
                    <Sparkles className="h-3 w-3 mr-1" />
                    Facturación Incluida
                  </Badge>
                )}
              </div>
              
              <div>
                <p className="text-sm text-muted-foreground">Plan Actual</p>
                <p className="text-lg font-semibold">
                  {subscription?.billing_included ? "Plan con Facturación Electrónica" : "Plan Base"}
                </p>
              </div>

              {subscription?.end_date && (
                <div>
                  <p className="text-sm text-muted-foreground">Fecha de Vencimiento</p>
                  <p className="text-lg font-semibold">{formatDate(subscription.end_date)}</p>
                  {daysRemaining !== null && (
                    <p className={`text-sm ${daysRemaining <= 15 ? 'text-amber-500' : 'text-muted-foreground'}`}>
                      {daysRemaining > 0 ? `${daysRemaining} días restantes` : 'Vencida'}
                    </p>
                  )}
                </div>
              )}
            </div>

            <div className="flex flex-col justify-center items-center md:items-end gap-3">
              {pendingInvoices.length === 0 && (
                <>
                  <Button 
                    onClick={handleQuickStripePayment}
                    disabled={processingPayment}
                    className="w-full md:w-auto bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
                    data-testid="quick-pay-btn"
                  >
                    {processingPayment ? (
                      <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                    ) : (
                      <CreditCard className="mr-2 h-4 w-4" />
                    )}
                    Pagar Suscripción
                  </Button>
                  <Button 
                    variant="outline"
                    onClick={() => setRequestInvoiceDialogOpen(true)}
                    className="w-full md:w-auto"
                    data-testid="request-invoice-btn"
                  >
                    <FileText className="mr-2 h-4 w-4" />
                    Solicitar Factura
                  </Button>
                </>
              )}
              {daysRemaining !== null && daysRemaining <= 15 && daysRemaining > 0 && (
                <p className="text-sm text-amber-500 text-center md:text-right">
                  Tu suscripción vence pronto. Renueva para evitar interrupciones.
                </p>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Pending Invoices */}
      {pendingInvoices.length > 0 && (
        <Card className="border-amber-500/30">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-amber-500">
              <AlertTriangle className="h-5 w-5" />
              Facturas Pendientes de Pago
            </CardTitle>
            <CardDescription>
              Tienes facturas pendientes. Realiza el pago para mantener tu suscripción activa.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {pendingInvoices.map((invoice) => (
              <div key={invoice.id} className="bg-muted/50 rounded-lg p-4">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div>
                    <p className="font-semibold">{invoice.invoice_number}</p>
                    <p className="text-sm text-muted-foreground">{invoice.plan_name}</p>
                    <p className="text-sm text-muted-foreground">
                      Período: {formatDate(invoice.period_start)} - {formatDate(invoice.period_end)}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold text-primary">{formatCurrency(invoice.total)}</p>
                    <Badge variant="outline" className="bg-yellow-500/20 text-yellow-600">
                      Pendiente
                    </Badge>
                  </div>
                </div>
                
                <Separator className="my-4" />
                
                <div className="flex flex-col md:flex-row gap-3">
                  <Button 
                    onClick={() => handleStripePayment(invoice)}
                    disabled={processingPayment}
                    className="flex-1"
                    data-testid="pay-with-card-btn"
                  >
                    {processingPayment ? (
                      <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                    ) : (
                      <CreditCard className="mr-2 h-4 w-4" />
                    )}
                    Pagar con Tarjeta
                  </Button>
                  <Button 
                    variant="outline"
                    onClick={() => {
                      setSelectedInvoice(invoice);
                      setPaymentDialogOpen(true);
                    }}
                    className="flex-1"
                    data-testid="bank-transfer-btn"
                  >
                    <Banknote className="mr-2 h-4 w-4" />
                    Transferencia Bancaria
                  </Button>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Payment History */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Historial de Pagos
          </CardTitle>
        </CardHeader>
        <CardContent>
          {paymentHistory.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No hay pagos registrados
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Factura</TableHead>
                  <TableHead>Plan</TableHead>
                  <TableHead>Período</TableHead>
                  <TableHead>Método</TableHead>
                  <TableHead>Fecha Pago</TableHead>
                  <TableHead className="text-right">Monto</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {paymentHistory.map((payment) => (
                  <TableRow key={payment.id}>
                    <TableCell className="font-medium">{payment.invoice_number}</TableCell>
                    <TableCell>{payment.plan_name}</TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {payment.billing_cycle === "monthly" ? "Mensual" :
                       payment.billing_cycle === "quarterly" ? "Trimestral" :
                       payment.billing_cycle === "semiannual" ? "Semestral" : "Anual"}
                    </TableCell>
                    <TableCell className="capitalize">{payment.payment_method || "-"}</TableCell>
                    <TableCell>{formatDate(payment.payment_date)}</TableCell>
                    <TableCell className="text-right font-semibold">{formatCurrency(payment.total)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Plans Info */}
      <Card>
        <CardHeader>
          <CardTitle>Planes Disponibles</CardTitle>
          <CardDescription>Conoce las opciones de suscripción</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-2 gap-4">
            {plans.map((plan) => (
              <div 
                key={plan.id} 
                className={`border rounded-lg p-4 ${
                  plan.includes_billing ? 'border-purple-500/50 bg-purple-500/5' : 'border-border'
                }`}
              >
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <h3 className="font-semibold">{plan.name}</h3>
                    <p className="text-sm text-muted-foreground">{plan.description}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold">{formatCurrency(plan.price)}</p>
                    <p className="text-xs text-muted-foreground">/mes</p>
                  </div>
                </div>
                <ul className="space-y-1">
                  {plan.features?.map((feature, idx) => (
                    <li key={idx} className="text-sm flex items-center gap-2">
                      <CheckCircle className="h-3 w-3 text-emerald-500" />
                      {feature}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Request Invoice Dialog */}
      <Dialog open={requestInvoiceDialogOpen} onOpenChange={setRequestInvoiceDialogOpen}>
        <DialogContent className="sm:max-w-[450px]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-primary" />
              Solicitar Renovación
            </DialogTitle>
            <DialogDescription>
              Selecciona el plan y período para tu renovación
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="grid gap-2">
              <label className="text-sm font-medium">Plan</label>
              <Select 
                value={requestForm.plan_id} 
                onValueChange={(v) => setRequestForm({ ...requestForm, plan_id: v })}
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
              <label className="text-sm font-medium">Período de Facturación</label>
              <Select 
                value={requestForm.billing_cycle} 
                onValueChange={(v) => setRequestForm({ ...requestForm, billing_cycle: v })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {billingCycles.map((c) => (
                    <SelectItem key={c.id} value={c.id}>
                      {c.label} {c.discount > 0 ? `(${c.discount * 100}% descuento)` : ""}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {preview && (
              <div className="bg-muted rounded-lg p-4 space-y-2">
                <h4 className="font-semibold text-sm">Resumen</h4>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">
                    {preview.plan.name} x {preview.months} mes{preview.months > 1 ? "es" : ""}
                  </span>
                  <span>{formatCurrency(preview.subtotal)}</span>
                </div>
                {preview.discount > 0 && (
                  <div className="flex justify-between text-sm text-emerald-600">
                    <span>Descuento ({preview.cycle.discount * 100}%)</span>
                    <span>-{formatCurrency(preview.discount)}</span>
                  </div>
                )}
                <Separator />
                <div className="flex justify-between font-bold">
                  <span>Total a Pagar</span>
                  <span className="text-primary">{formatCurrency(preview.total)}</span>
                </div>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setRequestInvoiceDialogOpen(false)}>
              Cancelar
            </Button>
            <Button onClick={handleRequestInvoice} disabled={submitting}>
              {submitting && <RefreshCw className="mr-2 h-4 w-4 animate-spin" />}
              Solicitar Factura
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Bank Transfer Dialog */}
      <Dialog open={paymentDialogOpen} onOpenChange={setPaymentDialogOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Banknote className="h-5 w-5 text-emerald-500" />
              Pago por Transferencia Bancaria
            </DialogTitle>
            <DialogDescription>
              Realiza la transferencia a alguna de las siguientes cuentas
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            {selectedInvoice && (
              <div className="bg-primary/5 rounded-lg p-3 border border-primary/20">
                <div className="flex justify-between items-center">
                  <div>
                    <p className="text-sm text-muted-foreground">Factura</p>
                    <p className="font-semibold">{selectedInvoice.invoice_number}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-muted-foreground">Monto a Pagar</p>
                    <p className="text-xl font-bold text-primary">{formatCurrency(selectedInvoice.total)}</p>
                  </div>
                </div>
              </div>
            )}

            {bankAccounts.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                No hay cuentas bancarias configuradas. Contacta a soporte.
              </div>
            ) : (
              <div className="space-y-3">
                {bankAccounts.map((account, idx) => (
                  <div key={idx} className="border rounded-lg p-4">
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <p className="font-semibold">{account.bank_name}</p>
                        <p className="text-sm text-muted-foreground">{account.account_holder}</p>
                      </div>
                      <Building2 className="h-5 w-5 text-muted-foreground" />
                    </div>
                    
                    {account.account_number && (
                      <div className="flex justify-between items-center py-2 border-t">
                        <div>
                          <p className="text-xs text-muted-foreground">Número de Cuenta</p>
                          <p className="font-mono">{account.account_number}</p>
                        </div>
                        <Button 
                          variant="ghost" 
                          size="icon"
                          onClick={() => copyToClipboard(account.account_number)}
                        >
                          <Copy className="h-4 w-4" />
                        </Button>
                      </div>
                    )}
                    
                    <div className="flex justify-between items-center py-2 border-t">
                      <div>
                        <p className="text-xs text-muted-foreground">CLABE Interbancaria</p>
                        <p className="font-mono">{account.clabe}</p>
                      </div>
                      <Button 
                        variant="ghost" 
                        size="icon"
                        onClick={() => copyToClipboard(account.clabe)}
                      >
                        <Copy className="h-4 w-4" />
                      </Button>
                    </div>

                    {account.reference_instructions && (
                      <div className="pt-2 border-t">
                        <p className="text-xs text-muted-foreground">Referencia</p>
                        <p className="text-sm">{account.reference_instructions}</p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

            <Separator className="my-4" />

            <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-lg p-4">
              <h4 className="font-semibold text-emerald-600 dark:text-emerald-400 flex items-center gap-2 mb-2">
                <Upload className="h-4 w-4" />
                ¿Ya realizaste la transferencia?
              </h4>
              <p className="text-sm text-muted-foreground mb-3">
                Sube tu comprobante de pago para que podamos verificarlo y activar tu suscripción más rápido.
              </p>
              <Button 
                onClick={() => {
                  setPaymentDialogOpen(false);
                  openUploadReceiptDialog(selectedInvoice);
                }}
                className="w-full bg-emerald-600 hover:bg-emerald-700"
              >
                <Upload className="h-4 w-4 mr-2" />
                Subir Comprobante de Transferencia
              </Button>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setPaymentDialogOpen(false)}>
              Cerrar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Upload Receipt Dialog */}
      <Dialog open={uploadReceiptDialogOpen} onOpenChange={setUploadReceiptDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Upload className="h-5 w-5 text-emerald-500" />
              Subir Comprobante de Transferencia
            </DialogTitle>
            <DialogDescription>
              Sube una imagen o PDF de tu comprobante de transferencia para la factura{" "}
              <strong>{selectedInvoice?.invoice_number}</strong>
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="receipt-file">Comprobante de pago *</Label>
              <Input
                id="receipt-file"
                type="file"
                accept="image/*,.pdf"
                onChange={(e) => setReceiptForm({ ...receiptForm, file: e.target.files?.[0] })}
              />
              <p className="text-xs text-muted-foreground">
                Formatos: JPG, PNG, PDF (máx. 5MB)
              </p>
              {receiptForm.file && (
                <div className="flex items-center gap-2 text-sm text-emerald-600 bg-emerald-50 p-2 rounded">
                  <Image className="h-4 w-4" />
                  {receiptForm.file.name}
                </div>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="reference">Número de referencia / confirmación</Label>
              <Input
                id="reference"
                value={receiptForm.reference}
                onChange={(e) => setReceiptForm({ ...receiptForm, reference: e.target.value })}
                placeholder="Ej: 123456789"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="notes">Notas adicionales (opcional)</Label>
              <Textarea
                id="notes"
                value={receiptForm.notes}
                onChange={(e) => setReceiptForm({ ...receiptForm, notes: e.target.value })}
                placeholder="Cualquier información adicional..."
                rows={2}
              />
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
              <p className="text-sm text-blue-700">
                <strong>Monto a verificar:</strong> {selectedInvoice && formatCurrency(selectedInvoice.total)}
              </p>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setUploadReceiptDialogOpen(false)}>
              Cancelar
            </Button>
            <Button 
              onClick={handleUploadReceipt}
              disabled={!receiptForm.file || uploadingReceipt}
              className="bg-emerald-600 hover:bg-emerald-700"
            >
              {uploadingReceipt ? (
                <>
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  Subiendo...
                </>
              ) : (
                <>
                  <Upload className="h-4 w-4 mr-2" />
                  Enviar Comprobante
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default MySubscription;
