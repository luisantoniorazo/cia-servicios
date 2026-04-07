import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { formatCurrency, formatDate, getStatusColor, getStatusLabel } from "../lib/utils";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Badge } from "../components/ui/badge";
import { Skeleton } from "../components/ui/skeleton";
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
  Shield,
  Building2,
  Plus,
  MoreVertical,
  CheckCircle,
  XCircle,
  Pause,
  PlayCircle,
  DollarSign,
  Users,
  Eye,
  Link,
  Copy,
  LogOut,
  BarChart3,
  AlertTriangle,
  Upload,
  Image,
  UserX,
  UserCheck2,
  Edit,
  Lock,
  Unlock,
  Bot,
  Database,
  Server,
  Settings,
  Settings2,
  Save,
  TicketIcon,
  Mail,
  FileText,
  CreditCard,
  Receipt,
} from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { useTicketCounts } from "../components/Notifications/TicketBadge";
import { AppVersionBadge, APP_VERSION } from "../components/AppVersion";
import { ChangelogModal } from "../components/ChangelogModal";
import { History, Sparkles } from "lucide-react";

const LICENSE_TYPES = [
  { value: "test", label: "Prueba ($10 MXN)", users: 1, price: 10 },
  { value: "basic", label: "Básica ($499 MXN)", users: 5, price: 499 },
  { value: "professional", label: "Profesional ($999 MXN)", users: 15, price: 999 },
  { value: "enterprise", label: "Empresarial ($1,999 MXN)", users: 50, price: 1999 },
  { value: "unlimited", label: "Ilimitada", users: 999, price: 2999 },
];

export const SuperAdminDashboard = () => {
  const { api, superAdminLogout } = useAuth();
  const navigate = useNavigate();
  const ticketCounts = useTicketCounts();
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [detailDialogOpen, setDetailDialogOpen] = useState(false);
  const [adminDialogOpen, setAdminDialogOpen] = useState(false);
  const [serverConfigDialogOpen, setServerConfigDialogOpen] = useState(false);
  const [selectedCompany, setSelectedCompany] = useState(null);
  const [selectedAdmin, setSelectedAdmin] = useState(null);
  const [logoFile, setLogoFile] = useState(null);
  const [logoPreview, setLogoPreview] = useState(null);
  const [serverConfig, setServerConfig] = useState({
    mysql_host: "",
    mysql_port: 3306,
    mysql_user: "",
    mysql_password: "",
    mysql_database: "",
    backup_enabled: false,
    backup_schedule: "daily",
    cloud_provider: "mysql",
    migration_status: "pending",
    // Email Cobranza
    email_cobranza_enabled: false,
    email_cobranza_address: "",
    email_cobranza_password: "",
    email_cobranza_smtp_host: "",
    email_cobranza_smtp_port: 587,
    email_cobranza_use_tls: true,
    email_cobranza_use_ssl: false,
    email_cobranza_provider: "custom",
    // Email General
    email_general_enabled: false,
    email_general_address: "",
    email_general_password: "",
    email_general_smtp_host: "",
    email_general_smtp_port: 587,
    email_general_use_tls: true,
    email_general_use_ssl: false,
    email_general_provider: "custom",
    // Notification Settings
    notify_subscription_days_before: 15,
    notify_invoice_overdue: true,
    notify_invoice_days_before: 5,
  });
  const [smtpPresets, setSmtpPresets] = useState({});
  const [testingEmail, setTestingEmail] = useState(null);
  const [configTab, setConfigTab] = useState("database");
  const [revenueStats, setRevenueStats] = useState(null);
  const [loadingRevenue, setLoadingRevenue] = useState(false);
  const [savingServerConfig, setSavingServerConfig] = useState(false);
  const [testingConnection, setTestingConnection] = useState(false);
  const [creatingSchema, setCreatingSchema] = useState(false);
  const [migratingData, setMigratingData] = useState(false);
  const [renewDialogOpen, setRenewDialogOpen] = useState(false);
  const [renewingSubscription, setRenewingSubscription] = useState(false);
  const [changelogOpen, setChangelogOpen] = useState(false);
  const [renewForm, setRenewForm] = useState({
    months: 1,
    payment_amount: 0,
    payment_method: "transfer",
    notes: ""
  });
  const [adminForm, setAdminForm] = useState({
    full_name: "",
    email: "",
    phone: "",
    recovery_email: "",
    recovery_phone: "",
    new_password: "",
  });
  const [formData, setFormData] = useState({
    business_name: "",
    trade_name: "",
    rfc: "",
    address: "",
    phone: "",
    email: "",
    logo_url: "",
    logo_file: "",
    license_type: "professional",
    trial_days: 7,
    admin_full_name: "",
    admin_email: "",
    admin_phone: "",
    admin_password: "",
    recovery_email: "",
    recovery_phone: "",
  });

  useEffect(() => {
    fetchDashboard();
    fetchServerConfig();
    fetchRevenueStats();
  }, []);

  const fetchRevenueStats = async () => {
    setLoadingRevenue(true);
    try {
      const response = await api.get("/super-admin/revenue-stats");
      setRevenueStats(response.data);
    } catch (error) {
      console.log("Error fetching revenue stats:", error);
    } finally {
      setLoadingRevenue(false);
    }
  };

  const fetchDashboard = async () => {
    try {
      const response = await api.get("/super-admin/dashboard");
      setDashboard(response.data);
    } catch (error) {
      toast.error("Error al cargar dashboard");
      if (error.response?.status === 403) {
        navigate("/admin-portal");
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchServerConfig = async () => {
    try {
      const response = await api.get("/super-admin/server-config");
      if (response.data) {
        setServerConfig(response.data);
      }
      // Also fetch SMTP presets
      const presetsResponse = await api.get("/super-admin/smtp-presets");
      if (presetsResponse.data) {
        setSmtpPresets(presetsResponse.data);
      }
    } catch (error) {
      // Config might not exist yet, that's okay
      console.log("No server config found");
    }
  };

  const handleSaveServerConfig = async (e) => {
    e.preventDefault();
    setSavingServerConfig(true);
    try {
      await api.post("/super-admin/server-config", serverConfig);
      toast.success("Configuración de servidor guardada");
      fetchServerConfig();
    } catch (error) {
      toast.error("Error al guardar configuración");
    } finally {
      setSavingServerConfig(false);
    }
  };

  const applySmtpPreset = (emailType, provider) => {
    const preset = smtpPresets[provider];
    if (preset) {
      setServerConfig(prev => ({
        ...prev,
        [`email_${emailType}_provider`]: provider,
        [`email_${emailType}_smtp_host`]: preset.smtp_host,
        [`email_${emailType}_smtp_port`]: preset.smtp_port,
        [`email_${emailType}_use_tls`]: preset.use_tls,
        [`email_${emailType}_use_ssl`]: preset.use_ssl,
      }));
    }
  };

  const handleTestEmail = async (emailType) => {
    setTestingEmail(emailType);
    try {
      const response = await api.post("/super-admin/test-email", {
        email_type: emailType,
        test_recipient: serverConfig[`email_${emailType}_address`]
      });
      if (response.data.success) {
        toast.success("Correo de prueba enviado correctamente");
      } else {
        toast.error(response.data.message);
      }
    } catch (error) {
      toast.error("Error: " + (error.response?.data?.detail || error.message));
    } finally {
      setTestingEmail(null);
    }
  };

  const handleTestMySQLConnection = async () => {
    setTestingConnection(true);
    try {
      const response = await api.post("/super-admin/test-mysql-connection", serverConfig);
      if (response.data.success) {
        toast.success(
          <div>
            <p className="font-semibold">Conexión exitosa</p>
            <p className="text-sm">MySQL versión: {response.data.version}</p>
          </div>
        );
      } else {
        toast.error(response.data.message);
      }
    } catch (error) {
      toast.error("Error al probar conexión: " + (error.response?.data?.detail || error.message));
    } finally {
      setTestingConnection(false);
    }
  };

  const handleCreateMySQLSchema = async () => {
    setCreatingSchema(true);
    try {
      const response = await api.post("/super-admin/init-mysql-schema");
      if (response.data.success) {
        toast.success("Esquema MySQL creado exitosamente");
        fetchServerConfig();
      } else {
        toast.error(response.data.message);
      }
    } catch (error) {
      toast.error("Error al crear esquema: " + (error.response?.data?.detail || error.message));
    } finally {
      setCreatingSchema(false);
    }
  };

  const handleMigrateToMySQL = async () => {
    if (!window.confirm("¿Está seguro de migrar todos los datos a MySQL? Este proceso puede tomar varios minutos.")) {
      return;
    }
    setMigratingData(true);
    try {
      const response = await api.post("/super-admin/migrate-to-mysql");
      if (response.data.success) {
        toast.success(
          <div>
            <p className="font-semibold">Migración completada</p>
            <p className="text-sm">
              Empresas: {response.data.stats.companies}, 
              Usuarios: {response.data.stats.users},
              Clientes: {response.data.stats.clients}
            </p>
            {response.data.errors?.length > 0 && (
              <p className="text-xs text-yellow-600">
                {response.data.errors.length} errores menores registrados
              </p>
            )}
          </div>
        );
        fetchServerConfig();
      } else {
        toast.error(response.data.message);
      }
    } catch (error) {
      toast.error("Error en migración: " + (error.response?.data?.detail || error.message));
    } finally {
      setMigratingData(false);
    }
  };

  const handleCreateCompany = async (e) => {
    e.preventDefault();
    try {
      // Convert logo to base64 if selected
      let logoBase64 = null;
      if (logoFile) {
        logoBase64 = await fileToBase64(logoFile);
      }
      
      const response = await api.post("/super-admin/companies", {
        ...formData,
        logo_file: logoBase64,
        monthly_fee: parseFloat(formData.monthly_fee) || 0,
        max_users: parseInt(formData.max_users) || 5,
        subscription_months: parseInt(formData.subscription_months) || 1,
      });
      toast.success(
        <div>
          <p className="font-semibold">Empresa creada exitosamente</p>
          <p className="text-sm">URL de acceso: /empresa/{response.data.company.slug}/login</p>
        </div>
      );
      setDialogOpen(false);
      resetForm();
      fetchDashboard();
    } catch (error) {
      const detail = error.response?.data?.detail;
      toast.error(typeof detail === "string" ? detail : "Error al crear empresa");
    }
  };

  const handleStatusChange = async (companyId, status) => {
    try {
      await api.patch(`/super-admin/companies/${companyId}/status?status=${status}`);
      toast.success("Estado actualizado");
      fetchDashboard();
    } catch (error) {
      toast.error("Error al actualizar estado");
    }
  };

  const handleViewDetails = async (companyId) => {
    try {
      const response = await api.get(`/super-admin/companies/${companyId}`);
      setSelectedCompany(response.data);
      setDetailDialogOpen(true);
    } catch (error) {
      toast.error("Error al cargar detalles");
    }
  };

  const handleRenewSubscription = (company) => {
    setSelectedCompany(company);
    setRenewForm({
      months: 1,
      payment_amount: company.monthly_fee || 0,
      payment_method: "transfer",
      notes: ""
    });
    setRenewDialogOpen(true);
  };

  const handleSubmitRenewal = async (e) => {
    e.preventDefault();
    if (!selectedCompany) return;
    setRenewingSubscription(true);
    try {
      const response = await api.post(`/super-admin/companies/${selectedCompany.id}/subscription/renew`, renewForm);
      toast.success(
        <div>
          <p className="font-semibold">Suscripción renovada</p>
          <p className="text-sm">Nueva fecha de vencimiento: {formatDate(response.data.new_end_date)}</p>
        </div>
      );
      setRenewDialogOpen(false);
      fetchDashboard();
    } catch (error) {
      toast.error("Error al renovar suscripción");
    } finally {
      setRenewingSubscription(false);
    }
  };

  const handleEditAdmin = async (companyId) => {
    try {
      const response = await api.get(`/super-admin/companies/${companyId}/admin`);
      setSelectedAdmin({ ...response.data.admin, company_id: companyId, company_name: response.data.company_name });
      setAdminForm({
        full_name: response.data.admin.full_name || "",
        email: response.data.admin.email || "",
        phone: response.data.admin.phone || "",
        recovery_email: response.data.admin.recovery_email || "",
        recovery_phone: response.data.admin.recovery_phone || "",
        new_password: "",
      });
      setAdminDialogOpen(true);
    } catch (error) {
      const detail = error.response?.data?.detail;
      toast.error(typeof detail === "string" ? detail : "Error al cargar datos del admin");
    }
  };

  const handleUpdateAdmin = async (e) => {
    e.preventDefault();
    if (!selectedAdmin) return;
    try {
      await api.put(`/super-admin/companies/${selectedAdmin.company_id}/admin`, adminForm);
      toast.success("Admin actualizado exitosamente");
      setAdminDialogOpen(false);
      fetchDashboard();
    } catch (error) {
      const detail = error.response?.data?.detail;
      toast.error(typeof detail === "string" ? detail : "Error al actualizar admin");
    }
  };

  const handleToggleAdminStatus = async (companyId, currentStatus) => {
    const action = currentStatus ? "bloquear" : "desbloquear";
    if (!window.confirm(`¿Estás seguro de ${action} al admin de esta empresa?`)) return;
    try {
      const response = await api.patch(`/super-admin/companies/${companyId}/admin/toggle-status`);
      toast.success(response.data.message);
      fetchDashboard();
    } catch (error) {
      const detail = error.response?.data?.detail;
      toast.error(typeof detail === "string" ? detail : "Error al cambiar estado del admin");
    }
  };

  const copyLoginUrl = async (slug) => {
    const url = `${window.location.origin}/empresa/${slug}/login`;
    
    try {
      // Intentar usar la API moderna de clipboard
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(url);
        toast.success("URL copiada al portapapeles");
      } else {
        // Fallback para contextos no seguros
        const textArea = document.createElement("textarea");
        textArea.value = url;
        textArea.style.position = "fixed";
        textArea.style.left = "-999999px";
        textArea.style.top = "-999999px";
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        
        const successful = document.execCommand('copy');
        document.body.removeChild(textArea);
        
        if (successful) {
          toast.success("URL copiada al portapapeles");
        } else {
          // Mostrar URL para copiar manualmente
          toast.info(`URL: ${url}`, { duration: 10000 });
        }
      }
    } catch (err) {
      console.error("Error al copiar:", err);
      // Mostrar URL para copiar manualmente
      toast.info(`URL: ${url}`, { duration: 10000 });
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

  const handleLogoSelect = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      if (file.size > 2 * 1024 * 1024) {
        toast.error("El logo no debe exceder 2MB");
        return;
      }
      setLogoFile(file);
      // Preview
      const reader = new FileReader();
      reader.onload = () => setLogoPreview(reader.result);
      reader.readAsDataURL(file);
    }
  };

  const resetForm = () => {
    setFormData({
      business_name: "",
      trade_name: "",
      rfc: "",
      address: "",
      phone: "",
      email: "",
      logo_url: "",
      logo_file: "",
      license_type: "professional",
      trial_days: 7,
      admin_full_name: "",
      admin_email: "",
      admin_phone: "",
      admin_password: "",
      recovery_email: "",
      recovery_phone: "",
    });
    setLogoFile(null);
    setLogoPreview(null);
  };

  const handleLogout = () => {
    superAdminLogout();
    navigate("/admin-portal");
  };

  const handleLicenseTypeChange = (value) => {
    const license = LICENSE_TYPES.find((l) => l.value === value);
    setFormData({
      ...formData,
      license_type: value,
      max_users: license?.users || 5,
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 p-6">
        <div className="max-w-7xl mx-auto space-y-6">
          <Skeleton className="h-12 w-64 bg-slate-800" />
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {[...Array(4)].map((_, i) => (
              <Skeleton key={i} className="h-32 bg-slate-800" />
            ))}
          </div>
          <Skeleton className="h-96 bg-slate-800" />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900" data-testid="super-admin-dashboard">
      {/* Header */}
      <div className="bg-slate-800 border-b border-slate-700">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Shield className="h-6 sm:h-8 w-6 sm:w-8 text-amber-500" />
            <div>
              <h1 className="text-lg sm:text-xl font-bold text-white font-[Chivo]">Portal Super Admin</h1>
              <p className="text-xs sm:text-sm text-slate-400">Gestión de Licencias y Empresas</p>
            </div>
            <Button
              variant="outline"
              size="sm"
              className="hidden sm:flex border-slate-600 text-slate-300 hover:bg-slate-700 text-xs gap-1"
              onClick={() => setChangelogOpen(true)}
              data-testid="changelog-btn"
            >
              <Sparkles className="h-3 w-3 text-amber-400" />
              v{APP_VERSION}
            </Button>
          </div>
          <div className="flex flex-wrap items-center gap-2 sm:gap-3">
            <Button 
              variant="outline" 
              size="sm"
              className="border-blue-500 text-blue-400 hover:bg-blue-500/20 text-xs sm:text-sm" 
              onClick={() => setServerConfigDialogOpen(true)}
              data-testid="server-config-btn"
            >
              <Database className="mr-1 sm:mr-2 h-3 w-3 sm:h-4 sm:w-4" />
              <span className="hidden xs:inline">Config.</span> Servidor
            </Button>
            <Button 
              variant="outline" 
              size="sm"
              className="border-purple-500 text-purple-400 hover:bg-purple-500/20 text-xs sm:text-sm relative" 
              onClick={() => navigate("/admin-portal/tickets")}
              data-testid="tickets-admin-btn"
            >
              <TicketIcon className="mr-1 sm:mr-2 h-3 w-3 sm:h-4 sm:w-4" />
              Tickets
              {ticketCounts.unread > 0 && (
                <Badge className="absolute -top-2 -right-2 h-5 min-w-[20px] flex items-center justify-center text-[10px] px-1 bg-red-500 animate-pulse">
                  {ticketCounts.unread}
                </Badge>
              )}
            </Button>
            <Button 
              variant="outline" 
              size="sm"
              className="border-green-500 text-green-400 hover:bg-green-500/20 text-xs sm:text-sm" 
              onClick={() => navigate("/admin-portal/subscriptions")}
              data-testid="subscriptions-btn"
            >
              <DollarSign className="mr-1 sm:mr-2 h-3 w-3 sm:h-4 sm:w-4" />
              <span className="hidden sm:inline">Suscripciones</span>
            </Button>
            <Button 
              variant="outline" 
              size="sm"
              className="border-teal-500 text-teal-400 hover:bg-teal-500/20 text-xs sm:text-sm" 
              onClick={() => navigate("/admin-portal/pending-receipts")}
              data-testid="pending-receipts-btn"
            >
              <Receipt className="mr-1 sm:mr-2 h-3 w-3 sm:h-4 sm:w-4" />
              <span className="hidden sm:inline">Comprobantes</span>
            </Button>
            <Button 
              variant="outline" 
              size="sm"
              className="border-emerald-500 text-emerald-400 hover:bg-emerald-500/20 text-xs sm:text-sm" 
              onClick={() => navigate("/admin-portal/facturama")}
              data-testid="facturama-config-btn"
            >
              <FileText className="mr-1 sm:mr-2 h-3 w-3 sm:h-4 sm:w-4" />
              <span className="hidden sm:inline">Facturama</span>
            </Button>
            <Button 
              variant="outline" 
              size="sm"
              className="border-purple-500 text-purple-400 hover:bg-purple-500/20 text-xs sm:text-sm" 
              onClick={() => navigate("/admin-portal/stripe")}
              data-testid="stripe-config-btn"
            >
              <CreditCard className="mr-1 sm:mr-2 h-3 w-3 sm:h-4 sm:w-4" />
              <span className="hidden sm:inline">Stripe</span>
            </Button>
            <Button 
              variant="outline" 
              size="sm"
              className="border-amber-500 text-amber-400 hover:bg-amber-500/20 text-xs sm:text-sm" 
              onClick={() => navigate("/admin-portal/system-monitor")}
              data-testid="system-monitor-btn"
            >
              <Bot className="mr-1 sm:mr-2 h-3 w-3 sm:h-4 sm:w-4" />
              <span className="hidden sm:inline">Monitor</span>
            </Button>
            <Button variant="outline" size="sm" className="border-slate-600 text-slate-300 text-xs sm:text-sm" onClick={handleLogout}>
              <LogOut className="mr-1 sm:mr-2 h-3 w-3 sm:h-4 sm:w-4" />
              <span className="hidden sm:inline">Cerrar Sesión</span>
            </Button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-3 sm:px-6 py-4 sm:py-6 space-y-4 sm:space-y-6">
        {/* Stats */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2 sm:gap-4">
          <Card className="bg-slate-800 border-slate-700">
            <CardContent className="p-3 sm:p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs sm:text-sm text-slate-400">Total Empresas</p>
                  <p className="text-2xl sm:text-3xl font-bold text-white">{dashboard?.summary?.total_companies || 0}</p>
                </div>
                <Building2 className="h-6 w-6 sm:h-8 sm:w-8 text-slate-500" />
              </div>
            </CardContent>
          </Card>
          <Card className="bg-slate-800 border-slate-700">
            <CardContent className="p-3 sm:p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs sm:text-sm text-slate-400">Activas</p>
                  <p className="text-2xl sm:text-3xl font-bold text-emerald-400">{dashboard?.summary?.active || 0}</p>
                </div>
                <CheckCircle className="h-6 w-6 sm:h-8 sm:w-8 text-emerald-500/50" />
              </div>
            </CardContent>
          </Card>
          <Card className="bg-slate-800 border-slate-700">
            <CardContent className="p-3 sm:p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs sm:text-sm text-slate-400">Pendientes</p>
                  <p className="text-2xl sm:text-3xl font-bold text-amber-400">{dashboard?.summary?.pending || 0}</p>
                </div>
                <Pause className="h-6 w-6 sm:h-8 sm:w-8 text-amber-500/50" />
              </div>
            </CardContent>
          </Card>
          <Card className="bg-slate-800 border-slate-700 hidden sm:block">
            <CardContent className="p-3 sm:p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs sm:text-sm text-slate-400">En Prueba</p>
                  <p className="text-2xl sm:text-3xl font-bold text-blue-400">{dashboard?.summary?.trial || 0}</p>
                </div>
                <PlayCircle className="h-6 w-6 sm:h-8 sm:w-8 text-blue-500/50" />
              </div>
            </CardContent>
          </Card>
          <Card className="bg-gradient-to-br from-amber-500/20 to-amber-600/20 border-amber-500/30 col-span-2 sm:col-span-1">
            <CardContent className="p-3 sm:p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs sm:text-sm text-amber-200">Ingresos Mensuales</p>
                  <p className="text-xl sm:text-2xl font-bold text-amber-100">
                    {formatCurrency(dashboard?.summary?.monthly_revenue || 0)}
                  </p>
                </div>
                <DollarSign className="h-6 w-6 sm:h-8 sm:w-8 text-amber-500/50" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Revenue Statistics Section */}
        <Card className="bg-slate-800 border-slate-700">
          <CardHeader className="p-4 sm:p-6">
            <CardTitle className="text-white flex items-center gap-2 text-base sm:text-lg">
              <BarChart3 className="h-4 w-4 sm:h-5 sm:w-5 text-emerald-500" />
              Estadísticas de Ingresos
            </CardTitle>
            <CardDescription className="text-slate-400 text-xs sm:text-sm">
              Análisis de ingresos mensuales y renovaciones
            </CardDescription>
          </CardHeader>
          <CardContent className="p-4 sm:p-6">
            {loadingRevenue ? (
              <div className="flex justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-500"></div>
              </div>
            ) : revenueStats ? (
              <div className="space-y-6">
                {/* Monthly Revenue Chart */}
                <div>
                  <h4 className="text-sm font-medium text-slate-300 mb-3">Ingresos Últimos 12 Meses</h4>
                  <div className="flex gap-1 items-end h-32">
                    {revenueStats.monthly_revenue?.map((month, idx) => {
                      const maxRevenue = Math.max(...revenueStats.monthly_revenue.map(m => m.revenue || 1));
                      const height = maxRevenue > 0 ? (month.revenue / maxRevenue) * 100 : 0;
                      return (
                        <div key={idx} className="flex-1 flex flex-col items-center gap-1">
                          <div 
                            className="w-full bg-emerald-500/30 rounded-t hover:bg-emerald-500/50 transition-colors relative group"
                            style={{ height: `${Math.max(height, 5)}%` }}
                          >
                            <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-slate-700 px-2 py-1 rounded text-xs text-white opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
                              {formatCurrency(month.revenue)} ({month.companies} emp.)
                            </div>
                          </div>
                          <span className="text-[10px] text-slate-500 transform -rotate-45 origin-top-left mt-1 hidden sm:block">
                            {month.month?.split(' ')[0]}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* License Type Distribution */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {revenueStats.license_stats?.map((stat) => (
                    <div key={stat.license} className="bg-slate-900/50 rounded-lg p-3">
                      <p className="text-xs text-slate-400 capitalize">
                        {stat.license === "basic" ? "Básica" : 
                         stat.license === "professional" ? "Profesional" : 
                         stat.license === "enterprise" ? "Empresarial" : 
                         stat.license === "unlimited" ? "Ilimitada" : stat.license}
                      </p>
                      <p className="text-lg font-bold text-white">{stat.count}</p>
                      <p className="text-xs text-emerald-400">{formatCurrency(stat.revenue)}/mes</p>
                    </div>
                  ))}
                </div>

                {/* Upcoming Renewals */}
                {revenueStats.upcoming_renewals?.length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium text-slate-300 mb-3">Renovaciones Próximas (30 días)</h4>
                    <div className="space-y-2">
                      {revenueStats.upcoming_renewals.map((renewal, idx) => (
                        <div key={idx} className="flex justify-between items-center bg-slate-900/50 rounded-lg p-3">
                          <div>
                            <p className="text-sm text-white">{renewal.business_name}</p>
                            <p className="text-xs text-slate-400">
                              Vence: {renewal.subscription_end ? new Date(renewal.subscription_end).toLocaleDateString('es-MX') : '-'}
                            </p>
                          </div>
                          <p className="text-sm font-medium text-emerald-400">{formatCurrency(renewal.monthly_fee)}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Summary */}
                <div className="flex flex-wrap gap-4 pt-4 border-t border-slate-700">
                  <div className="bg-emerald-500/10 rounded-lg px-4 py-2">
                    <p className="text-xs text-emerald-400">Total Mensual Actual</p>
                    <p className="text-xl font-bold text-emerald-300">
                      {formatCurrency(revenueStats.total_monthly_revenue || 0)}
                    </p>
                  </div>
                  <div className="bg-blue-500/10 rounded-lg px-4 py-2">
                    <p className="text-xs text-blue-400">Empresas Activas</p>
                    <p className="text-xl font-bold text-blue-300">
                      {dashboard?.summary?.active || 0}
                    </p>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-slate-500">
                No hay datos de ingresos disponibles
              </div>
            )}
          </CardContent>
        </Card>

        {/* Payment Reminder */}
        {dashboard?.pending_payment?.length > 0 && (
          <Card className="bg-amber-500/10 border-amber-500/30">
            <CardContent className="p-4 flex items-center gap-3">
              <AlertTriangle className="h-5 w-5 text-amber-400" />
              <div>
                <p className="font-semibold text-amber-200">Cobranza del Mes</p>
                <p className="text-sm text-amber-300">
                  {dashboard.pending_payment.length} empresa(s) pendiente(s) de pago. Total:{" "}
                  {formatCurrency(dashboard.pending_payment.reduce((acc, p) => acc + p.amount, 0))}
                </p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Companies Table */}
        <Card className="bg-slate-800 border-slate-700">
          <CardHeader className="p-4 sm:p-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <CardTitle className="text-white flex items-center gap-2 text-base sm:text-lg">
                  <Building2 className="h-4 w-4 sm:h-5 sm:w-5 text-amber-500" />
                  Empresas Registradas
                </CardTitle>
                <CardDescription className="text-slate-400 text-xs sm:text-sm">
                  Gestión de licencias y suscripciones
                </CardDescription>
              </div>
              <Button
                className="bg-amber-500 hover:bg-amber-600 text-slate-900 text-sm"
                size="sm"
                onClick={() => setDialogOpen(true)}
                data-testid="create-company-btn"
              >
                <Plus className="mr-1 sm:mr-2 h-4 w-4" />
                <span className="sm:inline">Nueva Empresa</span>
              </Button>
            </div>
          </CardHeader>
          <CardContent className="p-2 sm:p-6">
            {/* Mobile Card View */}
            <div className="block lg:hidden space-y-3">
              {dashboard?.companies?.length === 0 ? (
                <div className="text-center py-8 text-slate-500">No hay empresas registradas</div>
              ) : (
                dashboard?.companies?.map((company) => (
                  <div key={company.id} className="bg-slate-900/50 rounded-lg p-4 border border-slate-700">
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <div className="text-white font-medium text-sm">{company.business_name}</div>
                        <div className="text-xs text-slate-400">{company.slug}</div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge className={getStatusColor(company.subscription_status || company.status)} variant="outline">
                          {getStatusLabel(company.subscription_status || company.status)}
                        </Badge>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon" className="text-slate-400 h-8 w-8">
                              <MoreVertical className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end" className="bg-slate-800 border-slate-700">
                            <DropdownMenuItem className="text-slate-300" onClick={() => handleViewDetails(company.id)}>
                              <Eye className="mr-2 h-4 w-4" />Ver Detalles
                            </DropdownMenuItem>
                            <DropdownMenuItem className="text-blue-400" onClick={() => handleEditAdmin(company.id)}>
                              <Edit className="mr-2 h-4 w-4" />Editar Admin
                            </DropdownMenuItem>
                            <DropdownMenuItem className="text-purple-400" onClick={() => handleRenewSubscription(company)}>
                              <DollarSign className="mr-2 h-4 w-4" />Renovar
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div>
                        <span className="text-slate-500">Admin:</span>
                        <span className="text-slate-300 ml-1">{company.admin_email || "-"}</span>
                      </div>
                      <div>
                        <span className="text-slate-500">Licencia:</span>
                        <span className="text-slate-300 ml-1">{LICENSE_TYPES.find((l) => l.value === company.license_type)?.label || "Básica"}</span>
                      </div>
                      <div>
                        <span className="text-slate-500">Mensualidad:</span>
                        <span className="text-white font-medium ml-1">{formatCurrency(company.monthly_fee)}</span>
                      </div>
                      <div>
                        <span className="text-slate-500">Vence:</span>
                        <span className="text-slate-300 ml-1">
                          {company.subscription_end ? formatDate(company.subscription_end) : "-"}
                        </span>
                      </div>
                    </div>
                    {company.days_until_expiry !== undefined && company.days_until_expiry <= 15 && (
                      <Badge className={`mt-2 ${company.days_until_expiry <= 0 ? "bg-red-500/20 text-red-300" : "bg-yellow-500/20 text-yellow-300"}`} variant="outline">
                        {company.days_until_expiry <= 0 ? "Vencida" : `${company.days_until_expiry} días para vencer`}
                      </Badge>
                    )}
                  </div>
                ))
              )}
            </div>

            {/* Desktop Table View */}
            <div className="hidden lg:block rounded-sm border border-slate-700 overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="bg-slate-900/50 border-slate-700">
                    <TableHead className="text-slate-300 text-xs">Empresa</TableHead>
                    <TableHead className="text-slate-300 text-xs">Admin</TableHead>
                    <TableHead className="text-slate-300 text-xs">Licencia</TableHead>
                    <TableHead className="text-slate-300 text-xs">Mensualidad</TableHead>
                    <TableHead className="text-slate-300 text-xs">Vencimiento</TableHead>
                    <TableHead className="text-slate-300 text-xs">Estado</TableHead>
                    <TableHead className="text-slate-300 text-xs">URL</TableHead>
                    <TableHead className="w-[50px]"></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {dashboard?.companies?.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={7} className="text-center py-8 text-slate-500">
                        No hay empresas registradas
                      </TableCell>
                    </TableRow>
                  ) : (
                    dashboard?.companies?.map((company) => (
                      <TableRow key={company.id} className="border-slate-700">
                        <TableCell>
                          <div className="text-white font-medium">{company.trade_name || company.business_name}</div>
                          {company.trade_name && company.business_name !== company.trade_name && (
                            <div className="text-xs text-slate-500">{company.business_name}</div>
                          )}
                          <div className="text-sm text-slate-400">{company.slug}</div>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <div>
                              <div className="text-slate-300">{company.admin_email || "-"}</div>
                              {company.admin_name && (
                                <div className="text-xs text-slate-500">{company.admin_name}</div>
                              )}
                            </div>
                            {company.admin_blocked && (
                              <Badge className="bg-red-500/20 text-red-300 text-xs">
                                <Lock className="h-3 w-3 mr-1" />
                                Bloqueado
                              </Badge>
                            )}
                          </div>
                        </TableCell>
                        <TableCell className="text-slate-300">
                          {LICENSE_TYPES.find((l) => l.value === company.license_type)?.label || "Básica"}
                        </TableCell>
                        <TableCell className="text-white font-medium">
                          {formatCurrency(company.monthly_fee)}
                        </TableCell>
                        <TableCell>
                          {company.subscription_end ? (
                            <div className="flex flex-col">
                              <span className="text-slate-300 text-sm">
                                {formatDate(company.subscription_end)}
                              </span>
                              {company.days_until_expiry !== undefined && company.days_until_expiry <= 15 && (
                                <Badge className={company.days_until_expiry <= 0 ? "bg-red-500/20 text-red-300" : "bg-yellow-500/20 text-yellow-300"} variant="outline">
                                  {company.days_until_expiry <= 0 ? "Vencida" : `${company.days_until_expiry} días`}
                                </Badge>
                              )}
                            </div>
                          ) : (
                            <span className="text-slate-500">-</span>
                          )}
                        </TableCell>
                        <TableCell>
                          <Badge className={getStatusColor(company.status)}>
                            {getStatusLabel(company.status)}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <code className="text-xs bg-slate-900 px-2 py-1 rounded text-slate-300">
                              /empresa/{company.slug}/login
                            </code>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="text-slate-400 hover:text-white h-7 w-7 p-0"
                              onClick={() => copyLoginUrl(company.slug)}
                              title="Copiar URL completa"
                            >
                              <Copy className="h-3 w-3" />
                            </Button>
                          </div>
                        </TableCell>
                        <TableCell>
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="icon" className="text-slate-400">
                                <MoreVertical className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end" className="bg-slate-800 border-slate-700">
                              <DropdownMenuItem
                                className="text-slate-300"
                                onClick={() => handleViewDetails(company.id)}
                              >
                                <Eye className="mr-2 h-4 w-4" />
                                Ver Detalles
                              </DropdownMenuItem>
                              <DropdownMenuItem
                                className="text-blue-400"
                                onClick={() => handleEditAdmin(company.id)}
                              >
                                <Edit className="mr-2 h-4 w-4" />
                                Editar Admin
                              </DropdownMenuItem>
                              <DropdownMenuItem
                                className={company.admin_blocked ? "text-emerald-400" : "text-orange-400"}
                                onClick={() => handleToggleAdminStatus(company.id, !company.admin_blocked)}
                              >
                                {company.admin_blocked ? (
                                  <>
                                    <Unlock className="mr-2 h-4 w-4" />
                                    Desbloquear Admin
                                  </>
                                ) : (
                                  <>
                                    <Lock className="mr-2 h-4 w-4" />
                                    Bloquear Admin
                                  </>
                                )}
                              </DropdownMenuItem>
                              <DropdownMenuSeparator className="bg-slate-700" />
                              <DropdownMenuItem
                                className="text-purple-400"
                                onClick={() => handleRenewSubscription(company)}
                              >
                                <DollarSign className="mr-2 h-4 w-4" />
                                Renovar Suscripción
                              </DropdownMenuItem>
                              <DropdownMenuSeparator className="bg-slate-700" />
                              <DropdownMenuItem
                                className="text-emerald-400"
                                onClick={() => handleStatusChange(company.id, "active")}
                              >
                                <CheckCircle className="mr-2 h-4 w-4" />
                                Activar
                              </DropdownMenuItem>
                              <DropdownMenuItem
                                className="text-blue-400"
                                onClick={() => handleStatusChange(company.id, "trial")}
                              >
                                <PlayCircle className="mr-2 h-4 w-4" />
                                Período de Prueba
                              </DropdownMenuItem>
                              <DropdownMenuItem
                                className="text-amber-400"
                                onClick={() => handleStatusChange(company.id, "suspended")}
                              >
                                <Pause className="mr-2 h-4 w-4" />
                                Suspender
                              </DropdownMenuItem>
                              <DropdownMenuItem
                                className="text-red-400"
                                onClick={() => handleStatusChange(company.id, "cancelled")}
                              >
                                <XCircle className="mr-2 h-4 w-4" />
                                Cancelar
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
      </div>

      {/* Create Company Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="sm:max-w-[700px] max-h-[90vh] overflow-y-auto">
          <form onSubmit={handleCreateCompany}>
            <DialogHeader>
              <DialogTitle>Nueva Empresa</DialogTitle>
              <DialogDescription>
                Crear empresa con su administrador asignado
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-6 py-4">
              {/* Company Info */}
              <div>
                <h4 className="font-semibold mb-3 flex items-center gap-2">
                  <Building2 className="h-4 w-4" />
                  Datos de la Empresa
                </h4>
                <div className="grid grid-cols-2 gap-4">
                  <div className="grid gap-2">
                    <Label>Nombre Comercial</Label>
                    <Input
                      value={formData.trade_name}
                      onChange={(e) => setFormData({ ...formData, trade_name: e.target.value })}
                      placeholder="Mi Empresa (marca)"
                      data-testid="new-company-trade-name"
                    />
                    <p className="text-xs text-slate-500">Nombre con el que se conoce comercialmente</p>
                  </div>
                  <div className="grid gap-2">
                    <Label>Razón Social *</Label>
                    <Input
                      value={formData.business_name}
                      onChange={(e) => setFormData({ ...formData, business_name: e.target.value })}
                      placeholder="Empresa S.A. de C.V."
                      required
                      data-testid="new-company-name"
                    />
                    <p className="text-xs text-slate-500">Nombre legal de la empresa</p>
                  </div>
                  <div className="grid gap-2">
                    <Label>RFC *</Label>
                    <Input
                      value={formData.rfc}
                      onChange={(e) => setFormData({ ...formData, rfc: e.target.value.toUpperCase() })}
                      placeholder="ABC123456XYZ"
                      required
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label>Email Empresa</Label>
                    <Input
                      type="email"
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      placeholder="contacto@empresa.com"
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label>Teléfono</Label>
                    <Input
                      value={formData.phone}
                      onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                      placeholder="+52 55 1234 5678"
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label>Logo de la Empresa</Label>
                    <div className="border-2 border-dashed rounded-lg p-3 text-center hover:border-primary transition-colors">
                      <input
                        type="file"
                        id="logo-file"
                        className="hidden"
                        accept=".png,.jpg,.jpeg,.webp"
                        onChange={handleLogoSelect}
                      />
                      <label htmlFor="logo-file" className="cursor-pointer">
                        {logoPreview ? (
                          <div className="flex items-center justify-center gap-2">
                            <img src={logoPreview} alt="Logo preview" className="h-10 w-10 object-contain rounded" />
                            <span className="text-sm text-muted-foreground">{logoFile?.name}</span>
                          </div>
                        ) : (
                          <div className="flex items-center justify-center gap-2 text-muted-foreground">
                            <Upload className="h-5 w-5" />
                            <span className="text-sm">Subir logo (máx. 2MB)</span>
                          </div>
                        )}
                      </label>
                    </div>
                  </div>
                  <div className="col-span-2 grid gap-2">
                    <Label>Dirección</Label>
                    <Input
                      value={formData.address}
                      onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                      placeholder="Av. Principal 123, Ciudad"
                    />
                  </div>
                </div>
              </div>

              <Separator />

              {/* License Info */}
              <div>
                <h4 className="font-semibold mb-3 flex items-center gap-2">
                  <DollarSign className="h-4 w-4" />
                  Licencia y Suscripción
                </h4>
                <div className="grid grid-cols-3 gap-4">
                  <div className="grid gap-2">
                    <Label>Tipo de Licencia</Label>
                    <Select value={formData.license_type} onValueChange={handleLicenseTypeChange}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {LICENSE_TYPES.map((l) => (
                          <SelectItem key={l.value} value={l.value}>
                            {l.label} ({l.users} usuarios)
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="grid gap-2">
                    <Label>Días de Prueba *</Label>
                    <Input
                      type="number"
                      min="1"
                      max="15"
                      value={formData.trial_days || 7}
                      onChange={(e) => {
                        const value = Math.min(15, Math.max(1, parseInt(e.target.value) || 7));
                        setFormData({ ...formData, trial_days: value });
                      }}
                      placeholder="7"
                      required
                    />
                    <p className="text-xs text-slate-500">Máximo 15 días de periodo de prueba</p>
                  </div>
                </div>
              </div>

              <Separator />

              {/* Admin Info */}
              <div>
                <h4 className="font-semibold mb-3 flex items-center gap-2">
                  <Users className="h-4 w-4" />
                  Administrador de la Empresa
                </h4>
                <div className="grid grid-cols-2 gap-4">
                  <div className="grid gap-2">
                    <Label>Nombre Completo *</Label>
                    <Input
                      value={formData.admin_full_name}
                      onChange={(e) => setFormData({ ...formData, admin_full_name: e.target.value })}
                      placeholder="Juan Pérez García"
                      required
                      data-testid="new-admin-name"
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label>Email del Admin *</Label>
                    <Input
                      type="email"
                      value={formData.admin_email}
                      onChange={(e) => setFormData({ ...formData, admin_email: e.target.value })}
                      placeholder="admin@empresa.com"
                      required
                      data-testid="new-admin-email"
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label>Teléfono del Admin</Label>
                    <Input
                      value={formData.admin_phone}
                      onChange={(e) => setFormData({ ...formData, admin_phone: e.target.value })}
                      placeholder="+52 55 1234 5678"
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label>Contraseña *</Label>
                    <Input
                      type="password"
                      value={formData.admin_password}
                      onChange={(e) => setFormData({ ...formData, admin_password: e.target.value })}
                      placeholder="Mínimo 8 caracteres"
                      required
                      data-testid="new-admin-password"
                    />
                  </div>
                </div>
              </div>

              <Separator />

              {/* Recovery Info */}
              <div>
                <h4 className="font-semibold mb-3">Datos de Recuperación</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div className="grid gap-2">
                    <Label>Email de Recuperación</Label>
                    <Input
                      type="email"
                      value={formData.recovery_email}
                      onChange={(e) => setFormData({ ...formData, recovery_email: e.target.value })}
                      placeholder="recuperacion@empresa.com"
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label>Teléfono de Recuperación</Label>
                    <Input
                      value={formData.recovery_phone}
                      onChange={(e) => setFormData({ ...formData, recovery_phone: e.target.value })}
                      placeholder="+52 55 9876 5432"
                    />
                  </div>
                </div>
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
                Cancelar
              </Button>
              <Button type="submit" className="bg-amber-500 hover:bg-amber-600 text-slate-900" data-testid="submit-new-company">
                Crear Empresa
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Company Details Dialog */}
      <Dialog open={detailDialogOpen} onOpenChange={setDetailDialogOpen}>
        <DialogContent className="sm:max-w-[600px]">
          <DialogHeader>
            <DialogTitle>{selectedCompany?.business_name}</DialogTitle>
            <DialogDescription>
              Vista de solo lectura - Información de la empresa
            </DialogDescription>
          </DialogHeader>
          {selectedCompany && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="p-3 bg-slate-50 rounded-sm">
                  <div className="text-sm text-muted-foreground">RFC</div>
                  <div className="font-mono">{selectedCompany.rfc}</div>
                </div>
                <div className="p-3 bg-slate-50 rounded-sm">
                  <div className="text-sm text-muted-foreground">Estado</div>
                  <Badge className={getStatusColor(selectedCompany.subscription_status)}>
                    {getStatusLabel(selectedCompany.subscription_status)}
                  </Badge>
                </div>
              </div>

              <div className="p-3 bg-slate-50 rounded-sm">
                <div className="text-sm text-muted-foreground mb-2">URL de Acceso</div>
                <div className="flex items-center gap-2">
                  <code className="text-sm bg-white p-2 rounded border flex-1">
                    {window.location.origin}/empresa/{selectedCompany.slug}/login
                  </code>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => copyLoginUrl(selectedCompany.slug)}
                  >
                    <Copy className="h-4 w-4" />
                  </Button>
                </div>
              </div>

              <div>
                <h4 className="font-semibold mb-2">Estadísticas</h4>
                <div className="grid grid-cols-3 gap-3">
                  <div className="p-3 bg-blue-50 rounded-sm text-center">
                    <div className="text-2xl font-bold text-blue-600">{selectedCompany.stats?.users || 0}</div>
                    <div className="text-xs text-blue-600">Usuarios</div>
                  </div>
                  <div className="p-3 bg-emerald-50 rounded-sm text-center">
                    <div className="text-2xl font-bold text-emerald-600">{selectedCompany.stats?.projects || 0}</div>
                    <div className="text-xs text-emerald-600">Proyectos</div>
                  </div>
                  <div className="p-3 bg-amber-50 rounded-sm text-center">
                    <div className="text-2xl font-bold text-amber-600">{selectedCompany.stats?.clients || 0}</div>
                    <div className="text-xs text-amber-600">Clientes</div>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="p-3 bg-slate-50 rounded-sm">
                  <div className="text-sm text-muted-foreground">Facturado</div>
                  <div className="font-semibold">{formatCurrency(selectedCompany.stats?.total_invoiced || 0)}</div>
                </div>
                <div className="p-3 bg-slate-50 rounded-sm">
                  <div className="text-sm text-muted-foreground">Cobrado</div>
                  <div className="font-semibold text-emerald-600">{formatCurrency(selectedCompany.stats?.total_collected || 0)}</div>
                </div>
              </div>

              {selectedCompany.users?.length > 0 && (
                <div>
                  <h4 className="font-semibold mb-2">Usuarios ({selectedCompany.users.length})</h4>
                  <div className="max-h-40 overflow-y-auto border rounded-sm">
                    {selectedCompany.users.map((u) => (
                      <div key={u.id} className="p-2 border-b last:border-b-0 flex items-center justify-between">
                        <div>
                          <div className="font-medium">{u.full_name}</div>
                          <div className="text-sm text-muted-foreground">{u.email}</div>
                        </div>
                        <Badge variant="outline">{getStatusLabel(u.role)}</Badge>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setDetailDialogOpen(false)}>
              Cerrar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Admin Dialog */}
      <Dialog open={adminDialogOpen} onOpenChange={setAdminDialogOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <form onSubmit={handleUpdateAdmin}>
            <DialogHeader>
              <DialogTitle>Editar Admin</DialogTitle>
              <DialogDescription>
                {selectedAdmin?.company_name}
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="grid gap-2">
                <Label>Nombre Completo</Label>
                <Input
                  value={adminForm.full_name}
                  onChange={(e) => setAdminForm({ ...adminForm, full_name: e.target.value })}
                  placeholder="Nombre del administrador"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="grid gap-2">
                  <Label>Email</Label>
                  <Input
                    type="email"
                    value={adminForm.email}
                    onChange={(e) => setAdminForm({ ...adminForm, email: e.target.value })}
                    placeholder="admin@empresa.com"
                  />
                </div>
                <div className="grid gap-2">
                  <Label>Teléfono</Label>
                  <Input
                    value={adminForm.phone}
                    onChange={(e) => setAdminForm({ ...adminForm, phone: e.target.value })}
                    placeholder="+52 55 1234 5678"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="grid gap-2">
                  <Label>Email de Recuperación</Label>
                  <Input
                    type="email"
                    value={adminForm.recovery_email}
                    onChange={(e) => setAdminForm({ ...adminForm, recovery_email: e.target.value })}
                    placeholder="recuperacion@empresa.com"
                  />
                </div>
                <div className="grid gap-2">
                  <Label>Teléfono de Recuperación</Label>
                  <Input
                    value={adminForm.recovery_phone}
                    onChange={(e) => setAdminForm({ ...adminForm, recovery_phone: e.target.value })}
                    placeholder="+52 55 9876 5432"
                  />
                </div>
              </div>
              <div className="grid gap-2">
                <Label>Nueva Contraseña (dejar vacío para mantener actual)</Label>
                <Input
                  type="password"
                  value={adminForm.new_password}
                  onChange={(e) => setAdminForm({ ...adminForm, new_password: e.target.value })}
                  placeholder="Mínimo 8 caracteres"
                />
              </div>
              {selectedAdmin && (
                <div className="p-3 bg-slate-100 rounded-sm">
                  <div className="text-sm text-muted-foreground">Estado actual</div>
                  <Badge className={selectedAdmin.is_active !== false ? "bg-emerald-100 text-emerald-800" : "bg-red-100 text-red-800"}>
                    {selectedAdmin.is_active !== false ? "Activo" : "Bloqueado"}
                  </Badge>
                </div>
              )}
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setAdminDialogOpen(false)}>
                Cancelar
              </Button>
              <Button type="submit" className="bg-amber-500 hover:bg-amber-600 text-slate-900">
                Guardar Cambios
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Server Configuration Dialog */}
      <Dialog open={serverConfigDialogOpen} onOpenChange={setServerConfigDialogOpen}>
        <DialogContent className="sm:max-w-[800px] max-h-[90vh] overflow-y-auto">
          <form onSubmit={handleSaveServerConfig}>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Settings2 className="h-5 w-5 text-blue-500" />
                Configuración del Sistema
              </DialogTitle>
              <DialogDescription>
                Configura la base de datos, correos y notificaciones del sistema
              </DialogDescription>
            </DialogHeader>
            
            <Tabs value={configTab} onValueChange={setConfigTab} className="mt-4">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="database" className="text-xs sm:text-sm">
                  <Database className="h-4 w-4 mr-1 sm:mr-2" />
                  <span className="hidden sm:inline">Base de</span> Datos
                </TabsTrigger>
                <TabsTrigger value="email_cobranza" className="text-xs sm:text-sm">
                  <Mail className="h-4 w-4 mr-1 sm:mr-2" />
                  Cobranza
                </TabsTrigger>
                <TabsTrigger value="email_general" className="text-xs sm:text-sm">
                  <Mail className="h-4 w-4 mr-1 sm:mr-2" />
                  General
                </TabsTrigger>
              </TabsList>

              {/* DATABASE TAB */}
              <TabsContent value="database" className="space-y-4 mt-4">
                {/* Connection Status Badge */}
                <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg border">
                  <span className="font-medium text-sm">Estado de Migración:</span>
                  <Badge className={
                    serverConfig.migration_status === "completed" ? "bg-green-500" :
                    serverConfig.migration_status === "schema_created" ? "bg-blue-500" :
                    serverConfig.migration_status === "in_progress" ? "bg-yellow-500" :
                    serverConfig.migration_status === "failed" ? "bg-red-500" :
                    "bg-slate-500"
                  }>
                    {serverConfig.migration_status === "completed" ? "Completado" :
                     serverConfig.migration_status === "schema_created" ? "Esquema Creado" :
                     serverConfig.migration_status === "in_progress" ? "En Progreso" :
                     serverConfig.migration_status === "failed" ? "Fallido" :
                     "Pendiente"}
                  </Badge>
                </div>

                {/* MySQL Connection Settings */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="grid gap-2">
                    <Label>Host del Servidor *</Label>
                    <Input
                      value={serverConfig.mysql_host}
                      onChange={(e) => setServerConfig({ ...serverConfig, mysql_host: e.target.value })}
                      placeholder="localhost o IP del servidor"
                      data-testid="mysql-host-input"
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label>Puerto</Label>
                    <Input
                      type="number"
                      value={serverConfig.mysql_port}
                      onChange={(e) => setServerConfig({ ...serverConfig, mysql_port: parseInt(e.target.value) || 3306 })}
                      placeholder="3306"
                      data-testid="mysql-port-input"
                    />
                  </div>
                </div>
                
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="grid gap-2">
                    <Label>Usuario *</Label>
                    <Input
                      value={serverConfig.mysql_user}
                      onChange={(e) => setServerConfig({ ...serverConfig, mysql_user: e.target.value })}
                      placeholder="root"
                      data-testid="mysql-user-input"
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label>Contraseña *</Label>
                    <Input
                      type="password"
                      value={serverConfig.mysql_password}
                      onChange={(e) => setServerConfig({ ...serverConfig, mysql_password: e.target.value })}
                      placeholder="••••••••"
                      data-testid="mysql-password-input"
                    />
                  </div>
                </div>

                <div className="grid gap-2">
                  <Label>Nombre de Base de Datos *</Label>
                  <Input
                    value={serverConfig.mysql_database}
                    onChange={(e) => setServerConfig({ ...serverConfig, mysql_database: e.target.value })}
                    placeholder="cia_servicios"
                    data-testid="mysql-database-input"
                  />
                </div>

                {/* Action Buttons */}
                <div className="flex flex-wrap gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={handleTestMySQLConnection}
                    disabled={testingConnection || !serverConfig.mysql_host || !serverConfig.mysql_user}
                    className="text-blue-600 border-blue-300 hover:bg-blue-50"
                  >
                    {testingConnection ? "Probando..." : "Probar Conexión"}
                  </Button>
                  
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={handleCreateMySQLSchema}
                    disabled={creatingSchema || serverConfig.migration_status === "completed"}
                    className="text-green-600 border-green-300 hover:bg-green-50"
                  >
                    {creatingSchema ? "Creando..." : "Crear Esquema"}
                  </Button>

                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={handleMigrateToMySQL}
                    disabled={migratingData || serverConfig.migration_status !== "schema_created"}
                    className="text-orange-600 border-orange-300 hover:bg-orange-50"
                  >
                    {migratingData ? "Migrando..." : "Migrar Datos"}
                  </Button>
                </div>

                <Separator />
                
                {/* Backup Settings */}
                <div className="space-y-3">
                  <h4 className="font-semibold text-sm">Configuración de Respaldos</h4>
                  <div className="flex items-center justify-between">
                    <div>
                      <Label>Respaldos Automáticos</Label>
                      <p className="text-xs text-muted-foreground">Habilitar respaldos automáticos</p>
                    </div>
                    <input
                      type="checkbox"
                      checked={serverConfig.backup_enabled}
                      onChange={(e) => setServerConfig({ ...serverConfig, backup_enabled: e.target.checked })}
                      className="h-4 w-4"
                    />
                  </div>
                  {serverConfig.backup_enabled && (
                    <Select 
                      value={serverConfig.backup_schedule} 
                      onValueChange={(value) => setServerConfig({ ...serverConfig, backup_schedule: value })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="daily">Diario</SelectItem>
                        <SelectItem value="weekly">Semanal</SelectItem>
                        <SelectItem value="monthly">Mensual</SelectItem>
                      </SelectContent>
                    </Select>
                  )}
                </div>
              </TabsContent>

              {/* EMAIL COBRANZA TAB */}
              <TabsContent value="email_cobranza" className="space-y-4 mt-4">
                <div className="flex items-center justify-between p-3 bg-amber-50 rounded-lg border border-amber-200">
                  <div>
                    <span className="font-medium text-sm text-amber-800">Email de Cobranza</span>
                    <p className="text-xs text-amber-600">Para recordatorios de pago y facturas vencidas</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={serverConfig.email_cobranza_enabled}
                    onChange={(e) => setServerConfig({ ...serverConfig, email_cobranza_enabled: e.target.checked })}
                    className="h-5 w-5"
                  />
                </div>

                {serverConfig.email_cobranza_enabled && (
                  <>
                    <div className="grid gap-2">
                      <Label>Proveedor de Correo</Label>
                      <Select 
                        value={serverConfig.email_cobranza_provider} 
                        onValueChange={(value) => applySmtpPreset("cobranza", value)}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Seleccionar proveedor..." />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="custom">Configuración Manual</SelectItem>
                          <SelectItem value="gmail">Gmail / Google Workspace</SelectItem>
                          <SelectItem value="outlook">Outlook / Microsoft 365</SelectItem>
                          <SelectItem value="yahoo">Yahoo Mail</SelectItem>
                          <SelectItem value="zoho">Zoho Mail</SelectItem>
                          <SelectItem value="cpanel">cPanel (Hosting)</SelectItem>
                          <SelectItem value="hostinger">Hostinger</SelectItem>
                          <SelectItem value="godaddy">GoDaddy</SelectItem>
                        </SelectContent>
                      </Select>
                      {smtpPresets[serverConfig.email_cobranza_provider]?.notes && (
                        <p className="text-xs text-blue-600">{smtpPresets[serverConfig.email_cobranza_provider].notes}</p>
                      )}
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div className="grid gap-2">
                        <Label>Correo Electrónico *</Label>
                        <Input
                          type="email"
                          value={serverConfig.email_cobranza_address}
                          onChange={(e) => setServerConfig({ ...serverConfig, email_cobranza_address: e.target.value })}
                          placeholder="cobranza@tudominio.com"
                        />
                      </div>
                      <div className="grid gap-2">
                        <Label>Contraseña *</Label>
                        <Input
                          type="password"
                          value={serverConfig.email_cobranza_password}
                          onChange={(e) => setServerConfig({ ...serverConfig, email_cobranza_password: e.target.value })}
                          placeholder="••••••••"
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div className="grid gap-2">
                        <Label>Servidor SMTP</Label>
                        <Input
                          value={serverConfig.email_cobranza_smtp_host}
                          onChange={(e) => setServerConfig({ ...serverConfig, email_cobranza_smtp_host: e.target.value })}
                          placeholder="smtp.tudominio.com"
                        />
                      </div>
                      <div className="grid gap-2">
                        <Label>Puerto</Label>
                        <Input
                          type="number"
                          value={serverConfig.email_cobranza_smtp_port}
                          onChange={(e) => setServerConfig({ ...serverConfig, email_cobranza_smtp_port: parseInt(e.target.value) || 587 })}
                        />
                      </div>
                    </div>

                    <div className="flex items-center gap-6">
                      <label className="flex items-center gap-2 text-sm">
                        <input
                          type="checkbox"
                          checked={serverConfig.email_cobranza_use_tls}
                          onChange={(e) => setServerConfig({ ...serverConfig, email_cobranza_use_tls: e.target.checked, email_cobranza_use_ssl: false })}
                          className="h-4 w-4"
                        />
                        Usar TLS
                      </label>
                      <label className="flex items-center gap-2 text-sm">
                        <input
                          type="checkbox"
                          checked={serverConfig.email_cobranza_use_ssl}
                          onChange={(e) => setServerConfig({ ...serverConfig, email_cobranza_use_ssl: e.target.checked, email_cobranza_use_tls: false })}
                          className="h-4 w-4"
                        />
                        Usar SSL
                      </label>
                    </div>

                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => handleTestEmail("cobranza")}
                      disabled={testingEmail === "cobranza" || !serverConfig.email_cobranza_address}
                      className="text-amber-600 border-amber-300 hover:bg-amber-50"
                    >
                      <Mail className="mr-2 h-4 w-4" />
                      {testingEmail === "cobranza" ? "Enviando..." : "Enviar Correo de Prueba"}
                    </Button>

                    <Separator />

                    <div className="space-y-3">
                      <h4 className="font-semibold text-sm">Configuración de Notificaciones</h4>
                      <div className="flex items-center justify-between">
                        <div>
                          <Label>Recordatorio de facturas vencidas</Label>
                          <p className="text-xs text-muted-foreground">Enviar correo a clientes con facturas vencidas</p>
                        </div>
                        <input
                          type="checkbox"
                          checked={serverConfig.notify_invoice_overdue}
                          onChange={(e) => setServerConfig({ ...serverConfig, notify_invoice_overdue: e.target.checked })}
                          className="h-4 w-4"
                        />
                      </div>
                      <div className="grid gap-2">
                        <Label>Días antes del vencimiento para notificar</Label>
                        <Select 
                          value={String(serverConfig.notify_invoice_days_before)} 
                          onValueChange={(value) => setServerConfig({ ...serverConfig, notify_invoice_days_before: parseInt(value) })}
                        >
                          <SelectTrigger className="w-full">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="3">3 días antes</SelectItem>
                            <SelectItem value="5">5 días antes</SelectItem>
                            <SelectItem value="7">7 días antes</SelectItem>
                            <SelectItem value="10">10 días antes</SelectItem>
                            <SelectItem value="15">15 días antes</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                  </>
                )}
              </TabsContent>

              {/* EMAIL GENERAL TAB */}
              <TabsContent value="email_general" className="space-y-4 mt-4">
                <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg border border-blue-200">
                  <div>
                    <span className="font-medium text-sm text-blue-800">Email General</span>
                    <p className="text-xs text-blue-600">Para comunicación general y notificaciones del sistema</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={serverConfig.email_general_enabled}
                    onChange={(e) => setServerConfig({ ...serverConfig, email_general_enabled: e.target.checked })}
                    className="h-5 w-5"
                  />
                </div>

                {serverConfig.email_general_enabled && (
                  <>
                    <div className="grid gap-2">
                      <Label>Proveedor de Correo</Label>
                      <Select 
                        value={serverConfig.email_general_provider} 
                        onValueChange={(value) => applySmtpPreset("general", value)}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Seleccionar proveedor..." />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="custom">Configuración Manual</SelectItem>
                          <SelectItem value="gmail">Gmail / Google Workspace</SelectItem>
                          <SelectItem value="outlook">Outlook / Microsoft 365</SelectItem>
                          <SelectItem value="yahoo">Yahoo Mail</SelectItem>
                          <SelectItem value="zoho">Zoho Mail</SelectItem>
                          <SelectItem value="cpanel">cPanel (Hosting)</SelectItem>
                          <SelectItem value="hostinger">Hostinger</SelectItem>
                          <SelectItem value="godaddy">GoDaddy</SelectItem>
                        </SelectContent>
                      </Select>
                      {smtpPresets[serverConfig.email_general_provider]?.notes && (
                        <p className="text-xs text-blue-600">{smtpPresets[serverConfig.email_general_provider].notes}</p>
                      )}
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div className="grid gap-2">
                        <Label>Correo Electrónico *</Label>
                        <Input
                          type="email"
                          value={serverConfig.email_general_address}
                          onChange={(e) => setServerConfig({ ...serverConfig, email_general_address: e.target.value })}
                          placeholder="info@tudominio.com"
                        />
                      </div>
                      <div className="grid gap-2">
                        <Label>Contraseña *</Label>
                        <Input
                          type="password"
                          value={serverConfig.email_general_password}
                          onChange={(e) => setServerConfig({ ...serverConfig, email_general_password: e.target.value })}
                          placeholder="••••••••"
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div className="grid gap-2">
                        <Label>Servidor SMTP</Label>
                        <Input
                          value={serverConfig.email_general_smtp_host}
                          onChange={(e) => setServerConfig({ ...serverConfig, email_general_smtp_host: e.target.value })}
                          placeholder="smtp.tudominio.com"
                        />
                      </div>
                      <div className="grid gap-2">
                        <Label>Puerto</Label>
                        <Input
                          type="number"
                          value={serverConfig.email_general_smtp_port}
                          onChange={(e) => setServerConfig({ ...serverConfig, email_general_smtp_port: parseInt(e.target.value) || 587 })}
                        />
                      </div>
                    </div>

                    <div className="flex items-center gap-6">
                      <label className="flex items-center gap-2 text-sm">
                        <input
                          type="checkbox"
                          checked={serverConfig.email_general_use_tls}
                          onChange={(e) => setServerConfig({ ...serverConfig, email_general_use_tls: e.target.checked, email_general_use_ssl: false })}
                          className="h-4 w-4"
                        />
                        Usar TLS
                      </label>
                      <label className="flex items-center gap-2 text-sm">
                        <input
                          type="checkbox"
                          checked={serverConfig.email_general_use_ssl}
                          onChange={(e) => setServerConfig({ ...serverConfig, email_general_use_ssl: e.target.checked, email_general_use_tls: false })}
                          className="h-4 w-4"
                        />
                        Usar SSL
                      </label>
                    </div>

                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => handleTestEmail("general")}
                      disabled={testingEmail === "general" || !serverConfig.email_general_address}
                      className="text-blue-600 border-blue-300 hover:bg-blue-50"
                    >
                      <Mail className="mr-2 h-4 w-4" />
                      {testingEmail === "general" ? "Enviando..." : "Enviar Correo de Prueba"}
                    </Button>

                    <Separator />

                    <div className="space-y-3">
                      <h4 className="font-semibold text-sm">Recordatorios de Suscripción</h4>
                      <div className="grid gap-2">
                        <Label>Días antes del vencimiento para notificar admins</Label>
                        <Select 
                          value={String(serverConfig.notify_subscription_days_before)} 
                          onValueChange={(value) => setServerConfig({ ...serverConfig, notify_subscription_days_before: parseInt(value) })}
                        >
                          <SelectTrigger className="w-full">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="7">7 días antes</SelectItem>
                            <SelectItem value="10">10 días antes</SelectItem>
                            <SelectItem value="15">15 días antes</SelectItem>
                            <SelectItem value="30">30 días antes</SelectItem>
                          </SelectContent>
                        </Select>
                        <p className="text-xs text-muted-foreground">
                          Los administradores de empresas recibirán un correo recordando renovar su suscripción
                        </p>
                      </div>
                    </div>
                  </>
                )}
              </TabsContent>
            </Tabs>

            <DialogFooter className="mt-6">
              <Button type="button" variant="outline" onClick={() => setServerConfigDialogOpen(false)}>
                Cerrar
              </Button>
              <Button 
                type="submit" 
                className="bg-blue-600 hover:bg-blue-700 text-white"
                disabled={savingServerConfig}
              >
                <Save className="mr-2 h-4 w-4" />
                {savingServerConfig ? "Guardando..." : "Guardar Todo"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Subscription Renewal Dialog */}
      <Dialog open={renewDialogOpen} onOpenChange={setRenewDialogOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <form onSubmit={handleSubmitRenewal}>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <DollarSign className="h-5 w-5 text-purple-500" />
                Renovar Suscripción
              </DialogTitle>
              <DialogDescription>
                {selectedCompany?.business_name} - Renovar o extender la suscripción
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              {selectedCompany?.subscription_end && (
                <div className="p-3 bg-slate-100 rounded-lg">
                  <p className="text-sm text-slate-600">
                    <strong>Vencimiento actual:</strong> {formatDate(selectedCompany.subscription_end)}
                  </p>
                </div>
              )}
              
              <div className="grid gap-2">
                <Label>Meses a agregar *</Label>
                <Select 
                  value={String(renewForm.months)} 
                  onValueChange={(value) => {
                    const months = parseInt(value);
                    setRenewForm({
                      ...renewForm, 
                      months,
                      payment_amount: (selectedCompany?.monthly_fee || 0) * months
                    });
                  }}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="1">1 mes</SelectItem>
                    <SelectItem value="3">3 meses</SelectItem>
                    <SelectItem value="6">6 meses</SelectItem>
                    <SelectItem value="12">12 meses (1 año)</SelectItem>
                    <SelectItem value="24">24 meses (2 años)</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="grid gap-2">
                  <Label>Monto pagado</Label>
                  <Input
                    type="number"
                    value={renewForm.payment_amount}
                    onChange={(e) => setRenewForm({ ...renewForm, payment_amount: parseFloat(e.target.value) || 0 })}
                    placeholder="0.00"
                  />
                </div>
                <div className="grid gap-2">
                  <Label>Método de pago</Label>
                  <Select 
                    value={renewForm.payment_method} 
                    onValueChange={(value) => setRenewForm({ ...renewForm, payment_method: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="transfer">Transferencia</SelectItem>
                      <SelectItem value="cash">Efectivo</SelectItem>
                      <SelectItem value="card">Tarjeta</SelectItem>
                      <SelectItem value="stripe">Stripe</SelectItem>
                      <SelectItem value="other">Otro</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="grid gap-2">
                <Label>Notas</Label>
                <Input
                  value={renewForm.notes}
                  onChange={(e) => setRenewForm({ ...renewForm, notes: e.target.value })}
                  placeholder="Notas adicionales (opcional)"
                />
              </div>

              <div className="p-3 bg-purple-50 rounded-lg border border-purple-200">
                <p className="text-sm text-purple-800">
                  <strong>Resumen:</strong> Se agregarán {renewForm.months} mes(es) a la suscripción.
                  {selectedCompany?.monthly_fee && (
                    <span> Monto sugerido: {formatCurrency(selectedCompany.monthly_fee * renewForm.months)}</span>
                  )}
                </p>
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setRenewDialogOpen(false)}>
                Cancelar
              </Button>
              <Button 
                type="submit" 
                className="bg-purple-600 hover:bg-purple-700 text-white"
                disabled={renewingSubscription}
              >
                <DollarSign className="mr-2 h-4 w-4" />
                {renewingSubscription ? "Procesando..." : "Renovar Suscripción"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Changelog Modal */}
      <ChangelogModal open={changelogOpen} onOpenChange={setChangelogOpen} />

      {/* Footer con versión */}
      <footer className="bg-slate-800 border-t border-slate-700 mt-8">
        <div className="max-w-7xl mx-auto px-6 py-3 flex items-center justify-between">
          <p className="text-xs text-slate-500">
            © 2026 CIA Servicios - Control Integral de Administración
          </p>
          <Button
            variant="ghost"
            size="sm"
            className="text-xs text-slate-400 hover:text-white gap-1"
            onClick={() => setChangelogOpen(true)}
          >
            <Sparkles className="h-3 w-3" />
            v{APP_VERSION} - Ver cambios
          </Button>
        </div>
      </footer>
    </div>
  );
};

export default SuperAdminDashboard;
