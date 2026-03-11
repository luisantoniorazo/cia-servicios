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
} from "lucide-react";

const LICENSE_TYPES = [
  { value: "basic", label: "Básica", users: 5 },
  { value: "professional", label: "Profesional", users: 15 },
  { value: "enterprise", label: "Empresarial", users: 50 },
  { value: "unlimited", label: "Ilimitada", users: 999 },
];

export const SuperAdminDashboard = () => {
  const { api, superAdminLogout } = useAuth();
  const navigate = useNavigate();
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [detailDialogOpen, setDetailDialogOpen] = useState(false);
  const [adminDialogOpen, setAdminDialogOpen] = useState(false);
  const [selectedCompany, setSelectedCompany] = useState(null);
  const [selectedAdmin, setSelectedAdmin] = useState(null);
  const [logoFile, setLogoFile] = useState(null);
  const [logoPreview, setLogoPreview] = useState(null);
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
    rfc: "",
    address: "",
    phone: "",
    email: "",
    logo_url: "",
    logo_file: "",
    monthly_fee: "",
    license_type: "basic",
    max_users: 5,
    admin_full_name: "",
    admin_email: "",
    admin_phone: "",
    admin_password: "",
    recovery_email: "",
    recovery_phone: "",
  });

  useEffect(() => {
    fetchDashboard();
  }, []);

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

  const copyLoginUrl = (slug) => {
    const url = `${window.location.origin}/empresa/${slug}/login`;
    navigator.clipboard.writeText(url);
    toast.success("URL copiada al portapapeles");
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
      rfc: "",
      address: "",
      phone: "",
      email: "",
      logo_url: "",
      logo_file: "",
      monthly_fee: "",
      license_type: "basic",
      max_users: 5,
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
            <Shield className="h-8 w-8 text-amber-500" />
            <div>
              <h1 className="text-xl font-bold text-white font-[Chivo]">Portal Super Admin</h1>
              <p className="text-sm text-slate-400">Gestión de Licencias y Empresas</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Button 
              variant="outline" 
              className="border-amber-500 text-amber-400 hover:bg-amber-500/20" 
              onClick={() => navigate("/admin-portal/system-monitor")}
              data-testid="system-monitor-btn"
            >
              <Bot className="mr-2 h-4 w-4" />
              Monitor del Sistema
            </Button>
            <Button variant="outline" className="border-slate-600 text-slate-300" onClick={handleLogout}>
              <LogOut className="mr-2 h-4 w-4" />
              Cerrar Sesión
            </Button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto p-6 space-y-6">
        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <Card className="bg-slate-800 border-slate-700">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400">Total Empresas</p>
                  <p className="text-3xl font-bold text-white">{dashboard?.summary?.total_companies || 0}</p>
                </div>
                <Building2 className="h-8 w-8 text-slate-500" />
              </div>
            </CardContent>
          </Card>
          <Card className="bg-slate-800 border-slate-700">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400">Activas</p>
                  <p className="text-3xl font-bold text-emerald-400">{dashboard?.summary?.active || 0}</p>
                </div>
                <CheckCircle className="h-8 w-8 text-emerald-500/50" />
              </div>
            </CardContent>
          </Card>
          <Card className="bg-slate-800 border-slate-700">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400">Pendientes</p>
                  <p className="text-3xl font-bold text-amber-400">{dashboard?.summary?.pending || 0}</p>
                </div>
                <Pause className="h-8 w-8 text-amber-500/50" />
              </div>
            </CardContent>
          </Card>
          <Card className="bg-slate-800 border-slate-700">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400">En Prueba</p>
                  <p className="text-3xl font-bold text-blue-400">{dashboard?.summary?.trial || 0}</p>
                </div>
                <PlayCircle className="h-8 w-8 text-blue-500/50" />
              </div>
            </CardContent>
          </Card>
          <Card className="bg-gradient-to-br from-amber-500/20 to-amber-600/20 border-amber-500/30">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-amber-200">Ingresos Mensuales</p>
                  <p className="text-2xl font-bold text-amber-100">
                    {formatCurrency(dashboard?.summary?.monthly_revenue || 0)}
                  </p>
                </div>
                <DollarSign className="h-8 w-8 text-amber-500/50" />
              </div>
            </CardContent>
          </Card>
        </div>

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
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-white flex items-center gap-2">
                  <Building2 className="h-5 w-5 text-amber-500" />
                  Empresas Registradas
                </CardTitle>
                <CardDescription className="text-slate-400">
                  Gestión de licencias y suscripciones
                </CardDescription>
              </div>
              <Button
                className="bg-amber-500 hover:bg-amber-600 text-slate-900"
                onClick={() => setDialogOpen(true)}
                data-testid="create-company-btn"
              >
                <Plus className="mr-2 h-4 w-4" />
                Nueva Empresa
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="rounded-sm border border-slate-700 overflow-hidden">
              <Table>
                <TableHeader>
                  <TableRow className="bg-slate-900/50 border-slate-700">
                    <TableHead className="text-slate-300">Empresa</TableHead>
                    <TableHead className="text-slate-300">Admin</TableHead>
                    <TableHead className="text-slate-300">Licencia</TableHead>
                    <TableHead className="text-slate-300">Mensualidad</TableHead>
                    <TableHead className="text-slate-300">Estado</TableHead>
                    <TableHead className="text-slate-300">URL</TableHead>
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
                          <div className="text-white font-medium">{company.business_name}</div>
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
                  <div className="col-span-2 grid gap-2">
                    <Label>Razón Social *</Label>
                    <Input
                      value={formData.business_name}
                      onChange={(e) => setFormData({ ...formData, business_name: e.target.value })}
                      placeholder="Empresa S.A. de C.V."
                      required
                      data-testid="new-company-name"
                    />
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
                    <Label>Máximo Usuarios</Label>
                    <Input
                      type="number"
                      value={formData.max_users}
                      onChange={(e) => setFormData({ ...formData, max_users: e.target.value })}
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label>Mensualidad (MXN) *</Label>
                    <Input
                      type="number"
                      value={formData.monthly_fee}
                      onChange={(e) => setFormData({ ...formData, monthly_fee: e.target.value })}
                      placeholder="2500"
                      required
                      data-testid="new-company-fee"
                    />
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
    </div>
  );
};

export default SuperAdminDashboard;
