import React, { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Badge } from "../components/ui/badge";
import { Switch } from "../components/ui/switch";
import { Skeleton } from "../components/ui/skeleton";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "../components/ui/dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { toast } from "sonner";
import {
  CreditCard,
  ArrowLeft,
  Settings,
  Save,
  Eye,
  EyeOff,
  CheckCircle,
  XCircle,
  AlertTriangle,
  DollarSign,
  TrendingUp,
  Building2,
  RefreshCw,
  ExternalLink,
  Info,
  Loader2,
  Wallet,
} from "lucide-react";

const formatCurrency = (amount) => {
  return new Intl.NumberFormat("es-MX", {
    style: "currency",
    currency: "MXN",
  }).format(amount || 0);
};

const formatDate = (date) => {
  if (!date) return "N/A";
  return new Date(date).toLocaleDateString("es-MX", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
};

export const StripeConfig = () => {
  const { api } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showKeys, setShowKeys] = useState(false);
  const [configDialog, setConfigDialog] = useState(false);
  const [payments, setPayments] = useState([]);
  const [stripePayments, setStripePayments] = useState([]);
  const [stripeBalance, setStripeBalance] = useState(null);
  const [loadingStripe, setLoadingStripe] = useState(false);
  const [pendingInvoices, setPendingInvoices] = useState([]);
  const [loadingInvoices, setLoadingInvoices] = useState(false);
  const [markingPaid, setMarkingPaid] = useState(null);
  const [stats, setStats] = useState({
    total_collected: 0,
    total_pending: 0,
    payments_count: 0,
    this_month: 0,
  });
  
  const [config, setConfig] = useState({
    stripe_enabled: false,
    stripe_api_key: "",
    stripe_webhook_secret: "",
    environment: "test",
  });

  const [formData, setFormData] = useState({
    stripe_api_key: "",
    stripe_webhook_secret: "",
    environment: "test",
  });

  const fetchConfig = useCallback(async () => {
    try {
      const response = await api.get("/subscriptions/config");
      const data = response.data;
      setConfig({
        stripe_enabled: data.stripe_enabled || false,
        stripe_api_key: data.stripe_api_key || "",
        stripe_webhook_secret: data.stripe_webhook_secret || "",
        environment: data.stripe_environment || "test",
      });
      setFormData({
        stripe_api_key: data.stripe_api_key || "",
        stripe_webhook_secret: data.stripe_webhook_secret || "",
        environment: data.stripe_environment || "test",
      });
    } catch (error) {
      console.error("Error fetching config:", error);
    }
  }, [api]);

  const fetchPayments = useCallback(async () => {
    try {
      const response = await api.get("/subscriptions/payments");
      setPayments(response.data.payments || []);
      
      // Calculate stats
      const stripePayments = (response.data.payments || []).filter(p => p.payment_method === "stripe");
      const thisMonth = new Date().getMonth();
      const thisYear = new Date().getFullYear();
      
      setStats({
        total_collected: stripePayments.reduce((sum, p) => sum + (p.amount || 0), 0),
        payments_count: stripePayments.length,
        this_month: stripePayments
          .filter(p => {
            const d = new Date(p.created_at);
            return d.getMonth() === thisMonth && d.getFullYear() === thisYear;
          })
          .reduce((sum, p) => sum + (p.amount || 0), 0),
      });
    } catch (error) {
      console.error("Error fetching payments:", error);
    }
  }, [api]);

  const fetchStripePayments = useCallback(async () => {
    setLoadingStripe(true);
    try {
      const [paymentsRes, balanceRes] = await Promise.all([
        api.get("/subscriptions/stripe/payments?limit=50"),
        api.get("/subscriptions/stripe/balance")
      ]);
      setStripePayments(paymentsRes.data.payments || []);
      setStripeBalance(balanceRes.data);
      
      // Update stats with Stripe data
      const succeeded = paymentsRes.data.payments?.filter(p => p.status === "succeeded") || [];
      const thisMonth = new Date().getMonth();
      const thisYear = new Date().getFullYear();
      
      setStats(prev => ({
        ...prev,
        total_collected: paymentsRes.data.total_succeeded || 0,
        payments_count: succeeded.length,
        this_month: succeeded
          .filter(p => {
            const d = new Date(p.created_at);
            return d.getMonth() === thisMonth && d.getFullYear() === thisYear;
          })
          .reduce((sum, p) => sum + (p.amount || 0), 0),
      }));
    } catch (error) {
      console.error("Error fetching Stripe payments:", error);
      if (error.response?.data?.detail) {
        toast.error(error.response.data.detail);
      }
    } finally {
      setLoadingStripe(false);
    }
  }, [api]);

  const fetchPendingInvoices = useCallback(async () => {
    setLoadingInvoices(true);
    try {
      const response = await api.get("/subscriptions/admin/invoices/pending");
      setPendingInvoices(response.data.invoices || []);
    } catch (error) {
      console.error("Error fetching pending invoices:", error);
    } finally {
      setLoadingInvoices(false);
    }
  }, [api]);

  const handleMarkAsPaid = async (invoiceId, paymentMethod = "stripe") => {
    setMarkingPaid(invoiceId);
    try {
      const response = await api.post(`/subscriptions/admin/invoices/${invoiceId}/mark-paid`, {
        payment_method: paymentMethod,
        notes: "Marcado manualmente desde panel de administración"
      });
      toast.success(`✅ ${response.data.message}`);
      // Refresh data
      fetchPendingInvoices();
      fetchStripePayments();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al marcar como pagada");
    } finally {
      setMarkingPaid(null);
    }
  };

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await fetchConfig();
      await fetchPendingInvoices();
      setLoading(false);
    };
    loadData();
  }, [fetchConfig, fetchPendingInvoices]);

  // Fetch Stripe payments when config is loaded and has API key
  useEffect(() => {
    if (config.stripe_api_key && config.stripe_api_key.startsWith("sk_")) {
      fetchStripePayments();
    }
  }, [config.stripe_api_key, fetchStripePayments]);

  const handleSaveConfig = async () => {
    setSaving(true);
    try {
      await api.post("/subscriptions/config", {
        stripe_enabled: config.stripe_enabled,
        stripe_api_key: formData.stripe_api_key,
        stripe_webhook_secret: formData.stripe_webhook_secret,
        stripe_environment: formData.environment,
      });
      toast.success("Configuración de Stripe guardada");
      setConfigDialog(false);
      fetchConfig();
    } catch (error) {
      toast.error("Error al guardar configuración");
    } finally {
      setSaving(false);
    }
  };

  const handleToggleStripe = async (enabled) => {
    try {
      await api.post("/subscriptions/config", {
        ...config,
        stripe_enabled: enabled,
      });
      setConfig({ ...config, stripe_enabled: enabled });
      toast.success(enabled ? "Stripe habilitado" : "Stripe deshabilitado");
    } catch (error) {
      toast.error("Error al actualizar configuración");
    }
  };

  const maskKey = (key) => {
    if (!key) return "No configurado";
    if (key.length < 12) return key;
    return key.substring(0, 7) + "..." + key.substring(key.length - 4);
  };

  if (loading) {
    return (
      <div className="space-y-6 p-6">
        <Skeleton className="h-10 w-64" />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
        <Skeleton className="h-96" />
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6" data-testid="stripe-config-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => navigate("/admin-portal/dashboard")}
            className="text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <CreditCard className="h-6 w-6 text-purple-500" />
              Configuración de Stripe
            </h1>
            <p className="text-muted-foreground">
              Gestiona pagos con tarjeta para suscripciones
            </p>
          </div>
        </div>
        <Button onClick={() => setConfigDialog(true)}>
          <Settings className="h-4 w-4 mr-2" />
          Configurar
        </Button>
      </div>

      {/* Status Alert */}
      {!config.stripe_api_key && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 flex items-start gap-3">
          <AlertTriangle className="h-5 w-5 text-amber-500 mt-0.5" />
          <div>
            <p className="font-medium text-amber-800">Stripe no configurado</p>
            <p className="text-sm text-amber-700">
              Configura tus credenciales de Stripe para habilitar pagos con tarjeta.
              <a 
                href="https://dashboard.stripe.com/apikeys" 
                target="_blank" 
                rel="noopener noreferrer"
                className="ml-1 underline inline-flex items-center gap-1"
              >
                Obtener API Keys <ExternalLink className="h-3 w-3" />
              </a>
            </p>
          </div>
        </div>
      )}

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Estado</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                {config.stripe_enabled ? (
                  <>
                    <CheckCircle className="h-5 w-5 text-green-500" />
                    <span className="font-medium text-green-600">Activo</span>
                  </>
                ) : (
                  <>
                    <XCircle className="h-5 w-5 text-red-500" />
                    <span className="font-medium text-red-600">Inactivo</span>
                  </>
                )}
              </div>
              <Switch
                checked={config.stripe_enabled}
                onCheckedChange={handleToggleStripe}
                disabled={!config.stripe_api_key}
              />
            </div>
            <Badge variant="outline" className="mt-2">
              {config.stripe_api_key?.startsWith("sk_live") ? "Producción" : "Modo Test"}
            </Badge>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Cobrado en Stripe</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-purple-600">
              {formatCurrency(stats.total_collected)}
            </p>
            <p className="text-sm text-muted-foreground">
              {stats.payments_count} pagos exitosos
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Balance Disponible</CardDescription>
          </CardHeader>
          <CardContent>
            {stripeBalance ? (
              <>
                <p className="text-2xl font-bold text-green-600">
                  {formatCurrency(stripeBalance.available?.[0]?.amount || 0)}
                </p>
                <p className="text-sm text-muted-foreground">
                  {stripeBalance.pending?.[0]?.amount > 0 && (
                    <span className="text-amber-600">
                      + {formatCurrency(stripeBalance.pending[0].amount)} pendiente
                    </span>
                  )}
                </p>
              </>
            ) : (
              <p className="text-2xl font-bold text-muted-foreground">--</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>API Key</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm font-mono text-muted-foreground">
              {maskKey(config.stripe_api_key)}
            </p>
            <Badge 
              variant={config.stripe_api_key?.startsWith("sk_live") ? "default" : "secondary"}
              className="mt-2"
            >
              {config.stripe_api_key?.startsWith("sk_live") ? "Live Key" : "Test Key"}
            </Badge>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="pending-invoices" className="space-y-4">
        <TabsList>
          <TabsTrigger value="pending-invoices" className="relative">
            <AlertTriangle className="h-4 w-4 mr-2" />
            Facturas Pendientes
            {pendingInvoices.length > 0 && (
              <Badge variant="destructive" className="ml-2 h-5 w-5 p-0 flex items-center justify-center text-xs">
                {pendingInvoices.length}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="stripe-payments">
            <Wallet className="h-4 w-4 mr-2" />
            Pagos en Stripe
          </TabsTrigger>
          <TabsTrigger value="payments">
            <DollarSign className="h-4 w-4 mr-2" />
            Pagos Registrados
          </TabsTrigger>
          <TabsTrigger value="info">
            <Info className="h-4 w-4 mr-2" />
            Información
          </TabsTrigger>
        </TabsList>

        {/* Pending Invoices Tab */}
        <TabsContent value="pending-invoices">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <AlertTriangle className="h-5 w-5 text-amber-500" />
                    Facturas de Suscripción Pendientes
                  </CardTitle>
                  <CardDescription>
                    Facturas que no se han marcado como pagadas. Puedes marcarlas manualmente si ya recibiste el pago.
                  </CardDescription>
                </div>
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={fetchPendingInvoices}
                  disabled={loadingInvoices}
                >
                  {loadingInvoices ? (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <RefreshCw className="h-4 w-4 mr-2" />
                  )}
                  Actualizar
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {loadingInvoices ? (
                <div className="text-center py-12">
                  <Loader2 className="h-8 w-8 mx-auto mb-4 animate-spin text-amber-500" />
                  <p className="text-muted-foreground">Cargando facturas...</p>
                </div>
              ) : pendingInvoices.length === 0 ? (
                <div className="text-center py-12 text-muted-foreground">
                  <CheckCircle className="h-12 w-12 mx-auto mb-4 text-green-300" />
                  <p className="text-green-600 font-medium">¡No hay facturas pendientes!</p>
                  <p className="text-sm mt-2">Todas las suscripciones están al día</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Factura</TableHead>
                      <TableHead>Empresa</TableHead>
                      <TableHead>Período</TableHead>
                      <TableHead className="text-right">Monto</TableHead>
                      <TableHead>Estado</TableHead>
                      <TableHead className="text-right">Acciones</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {pendingInvoices.map((invoice) => (
                      <TableRow key={invoice.id}>
                        <TableCell>
                          <p className="font-mono text-sm">{invoice.invoice_number}</p>
                          <p className="text-xs text-muted-foreground">
                            {invoice.plan_id === "with_billing" ? "Plan con Facturación" : "Plan Base"}
                          </p>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <Building2 className="h-4 w-4 text-muted-foreground" />
                            <div>
                              <p className="font-medium">{invoice.company_name}</p>
                              <p className="text-xs text-muted-foreground">{invoice.company_email}</p>
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <p className="text-sm">
                            {formatDate(invoice.period_start)?.split(",")[0]} - {formatDate(invoice.period_end)?.split(",")[0]}
                          </p>
                        </TableCell>
                        <TableCell className="text-right font-bold text-lg">
                          {formatCurrency(invoice.total)}
                        </TableCell>
                        <TableCell>
                          <Badge variant={invoice.status === "overdue" ? "destructive" : "warning"}>
                            {invoice.status === "overdue" ? "Vencida" : "Pendiente"}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right">
                          <Button
                            size="sm"
                            onClick={() => handleMarkAsPaid(invoice.id, "stripe")}
                            disabled={markingPaid === invoice.id}
                            className="bg-green-600 hover:bg-green-700"
                          >
                            {markingPaid === invoice.id ? (
                              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                            ) : (
                              <CheckCircle className="h-4 w-4 mr-2" />
                            )}
                            Marcar Pagada
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="stripe-payments">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Pagos Directos de Stripe</CardTitle>
                  <CardDescription>Todos los pagos recibidos en tu cuenta de Stripe</CardDescription>
                </div>
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={fetchStripePayments}
                  disabled={loadingStripe}
                >
                  {loadingStripe ? (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <RefreshCw className="h-4 w-4 mr-2" />
                  )}
                  Actualizar
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {loadingStripe ? (
                <div className="text-center py-12">
                  <Loader2 className="h-8 w-8 mx-auto mb-4 animate-spin text-purple-500" />
                  <p className="text-muted-foreground">Consultando Stripe...</p>
                </div>
              ) : stripePayments.length === 0 ? (
                <div className="text-center py-12 text-muted-foreground">
                  <CreditCard className="h-12 w-12 mx-auto mb-4 opacity-20" />
                  <p>No hay pagos en Stripe</p>
                  <p className="text-sm mt-2">Verifica que la API Key sea correcta (sk_live_...)</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Fecha</TableHead>
                      <TableHead>Cliente</TableHead>
                      <TableHead>Descripción</TableHead>
                      <TableHead className="text-right">Monto</TableHead>
                      <TableHead>Estado</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {stripePayments.map((payment) => (
                      <TableRow key={payment.id}>
                        <TableCell>{formatDate(payment.created_at)}</TableCell>
                        <TableCell>
                          <div>
                            <p className="font-medium">{payment.customer_name || "Sin nombre"}</p>
                            <p className="text-xs text-muted-foreground">{payment.customer_email || payment.id}</p>
                          </div>
                        </TableCell>
                        <TableCell className="max-w-[200px] truncate">
                          {payment.description || "Pago con tarjeta"}
                        </TableCell>
                        <TableCell className="text-right font-medium">
                          {payment.currency === "MXN" 
                            ? formatCurrency(payment.amount)
                            : `$${payment.amount.toFixed(2)} ${payment.currency}`
                          }
                        </TableCell>
                        <TableCell>
                          <Badge 
                            variant={payment.status === "succeeded" ? "success" : 
                                    payment.status === "processing" ? "warning" : "secondary"}
                          >
                            {payment.status === "succeeded" && <CheckCircle className="h-3 w-3 mr-1" />}
                            {payment.status === "succeeded" ? "Pagado" : 
                             payment.status === "processing" ? "Procesando" : 
                             payment.status === "requires_action" ? "Requiere acción" : payment.status}
                          </Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="payments">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Pagos Registrados en el Sistema</CardTitle>
                  <CardDescription>Pagos procesados a través del flujo de suscripciones</CardDescription>
                </div>
                <Button variant="outline" size="sm" onClick={fetchPayments}>
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Actualizar
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {payments.filter(p => p.payment_method === "stripe").length === 0 ? (
                <div className="text-center py-12 text-muted-foreground">
                  <CreditCard className="h-12 w-12 mx-auto mb-4 opacity-20" />
                  <p>No hay pagos con Stripe registrados</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Fecha</TableHead>
                      <TableHead>Empresa</TableHead>
                      <TableHead>Factura</TableHead>
                      <TableHead className="text-right">Monto</TableHead>
                      <TableHead>Estado</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {payments
                      .filter(p => p.payment_method === "stripe")
                      .map((payment) => (
                        <TableRow key={payment.id}>
                          <TableCell>{formatDate(payment.created_at)}</TableCell>
                          <TableCell>
                            <div className="flex items-center gap-2">
                              <Building2 className="h-4 w-4 text-muted-foreground" />
                              {payment.company_name || "N/A"}
                            </div>
                          </TableCell>
                          <TableCell>{payment.invoice_folio || "N/A"}</TableCell>
                          <TableCell className="text-right font-medium">
                            {formatCurrency(payment.amount)}
                          </TableCell>
                          <TableCell>
                            <Badge variant="success">
                              <CheckCircle className="h-3 w-3 mr-1" />
                              Pagado
                            </Badge>
                          </TableCell>
                        </TableRow>
                      ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="info">
          <Card>
            <CardHeader>
              <CardTitle>Cómo Funciona</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <h3 className="font-semibold flex items-center gap-2">
                    <span className="bg-purple-100 text-purple-600 rounded-full w-6 h-6 flex items-center justify-center text-sm">1</span>
                    Obtén tus API Keys
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    Ingresa a tu{" "}
                    <a href="https://dashboard.stripe.com/apikeys" target="_blank" rel="noopener noreferrer" className="text-purple-600 underline">
                      Dashboard de Stripe
                    </a>{" "}
                    y copia tu Secret Key (sk_test_... o sk_live_...)
                  </p>

                  <h3 className="font-semibold flex items-center gap-2">
                    <span className="bg-purple-100 text-purple-600 rounded-full w-6 h-6 flex items-center justify-center text-sm">2</span>
                    Configura el Webhook
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    En Stripe, crea un webhook apuntando a:<br />
                    <code className="bg-slate-100 px-2 py-1 rounded text-xs">
                      https://tudominio.com/api/webhook/stripe
                    </code>
                  </p>

                  <h3 className="font-semibold flex items-center gap-2">
                    <span className="bg-purple-100 text-purple-600 rounded-full w-6 h-6 flex items-center justify-center text-sm">3</span>
                    Habilita Stripe
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    Una vez configurado, activa el switch para que las empresas puedan pagar con tarjeta.
                  </p>
                </div>

                <div className="bg-slate-50 rounded-lg p-4">
                  <h3 className="font-semibold mb-3">Flujo de Pago</h3>
                  <ol className="space-y-2 text-sm text-muted-foreground">
                    <li className="flex items-start gap-2">
                      <span className="bg-slate-200 rounded-full w-5 h-5 flex items-center justify-center text-xs flex-shrink-0">1</span>
                      <span>Empresa ve su factura de suscripción pendiente</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="bg-slate-200 rounded-full w-5 h-5 flex items-center justify-center text-xs flex-shrink-0">2</span>
                      <span>Hace clic en "Pagar con Tarjeta"</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="bg-slate-200 rounded-full w-5 h-5 flex items-center justify-center text-xs flex-shrink-0">3</span>
                      <span>Es redirigido a Stripe Checkout (página segura)</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="bg-slate-200 rounded-full w-5 h-5 flex items-center justify-center text-xs flex-shrink-0">4</span>
                      <span>Ingresa datos de tarjeta y paga</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="bg-slate-200 rounded-full w-5 h-5 flex items-center justify-center text-xs flex-shrink-0">5</span>
                      <span>El sistema actualiza la factura como pagada automáticamente</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="bg-green-200 rounded-full w-5 h-5 flex items-center justify-center text-xs flex-shrink-0">✓</span>
                      <span className="text-green-700 font-medium">El dinero llega a tu cuenta de Stripe</span>
                    </li>
                  </ol>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Config Dialog */}
      <Dialog open={configDialog} onOpenChange={setConfigDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <CreditCard className="h-5 w-5 text-purple-500" />
              Configurar Stripe
            </DialogTitle>
            <DialogDescription>
              Ingresa tus credenciales de Stripe para habilitar pagos con tarjeta
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="stripe_api_key">Secret API Key *</Label>
              <div className="relative">
                <Input
                  id="stripe_api_key"
                  type={showKeys ? "text" : "password"}
                  value={formData.stripe_api_key}
                  onChange={(e) => setFormData({ ...formData, stripe_api_key: e.target.value })}
                  placeholder="sk_test_... o sk_live_..."
                  className="pr-10"
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="absolute right-0 top-0 h-full px-3"
                  onClick={() => setShowKeys(!showKeys)}
                >
                  {showKeys ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </Button>
              </div>
              <p className="text-xs text-muted-foreground">
                Obtén tu key en{" "}
                <a href="https://dashboard.stripe.com/apikeys" target="_blank" rel="noopener noreferrer" className="text-purple-600 underline">
                  Stripe Dashboard → API Keys
                </a>
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="stripe_webhook_secret">Webhook Secret (opcional)</Label>
              <Input
                id="stripe_webhook_secret"
                type={showKeys ? "text" : "password"}
                value={formData.stripe_webhook_secret}
                onChange={(e) => setFormData({ ...formData, stripe_webhook_secret: e.target.value })}
                placeholder="whsec_..."
              />
              <p className="text-xs text-muted-foreground">
                Para verificar webhooks de Stripe
              </p>
            </div>

            <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
              <p className="text-sm text-amber-800">
                <strong>Nota:</strong> Usa keys de prueba (sk_test_) para probar.
                Cambia a keys de producción (sk_live_) cuando estés listo.
              </p>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setConfigDialog(false)}>
              Cancelar
            </Button>
            <Button onClick={handleSaveConfig} disabled={saving}>
              {saving ? (
                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Save className="h-4 w-4 mr-2" />
              )}
              Guardar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default StripeConfig;
