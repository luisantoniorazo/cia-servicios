import React, { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { getStatusLabel, getApiErrorMessage, formatDate } from "../lib/utils";
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
import { toast } from "sonner";
import {
  Settings as SettingsIcon,
  Building2,
  Users,
  UserPlus,
  Trash2,
  AlertTriangle,
  Shield,
  Eye,
  Upload,
  Image,
  EyeOff,
  UserX,
  UserCheck,
  Edit,
  Key,
  Bell,
  Send,
} from "lucide-react";
import { Checkbox } from "../components/ui/checkbox";
import { Textarea } from "../components/ui/textarea";

const ROLES = [
  { value: "admin", label: "Administrador" },
  { value: "manager", label: "Gerente" },
  { value: "user", label: "Usuario" },
];

const ALL_MODULES = [
  { id: "dashboard", label: "Dashboard" },
  { id: "projects", label: "Proyectos" },
  { id: "crm", label: "CRM" },
  { id: "quotes", label: "Cotizaciones" },
  { id: "invoices", label: "Facturación" },
  { id: "purchases", label: "Compras" },
  { id: "suppliers", label: "Proveedores" },
  { id: "documents", label: "Documentos" },
  { id: "field-reports", label: "Reportes de Campo" },
  { id: "kpis", label: "Indicadores" },
  { id: "intelligence", label: "Inteligencia IA" },
  { id: "settings", label: "Configuración" },
];

export const Settings = () => {
  const { api, company, user, setCompany, isAdmin } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [userDialogOpen, setUserDialogOpen] = useState(false);
  const [permissionsDialogOpen, setPermissionsDialogOpen] = useState(false);
  const [userDetailDialogOpen, setUserDetailDialogOpen] = useState(false);
  const [broadcastDialogOpen, setBroadcastDialogOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [selectedPermissions, setSelectedPermissions] = useState([]);
  const [showPassword, setShowPassword] = useState(false);
  const [broadcastForm, setBroadcastForm] = useState({
    title: "",
    message: "",
    notification_type: "info",
  });
  const [companyForm, setCompanyForm] = useState({
    business_name: "",
    rfc: "",
    address: "",
    phone: "",
    email: "",
    logo_url: "",
  });
  const [logoFile, setLogoFile] = useState(null);
  const [logoPreview, setLogoPreview] = useState(null);
  const [userForm, setUserForm] = useState({
    email: "",
    full_name: "",
    phone: "",
    password: "",
    role: "user",
  });
  const [editUserForm, setEditUserForm] = useState({
    full_name: "",
    email: "",
    phone: "",
    new_password: "",
  });

  useEffect(() => {
    if (company?.id) {
      setCompanyForm({
        business_name: company.business_name || "",
        rfc: company.rfc || "",
        address: company.address || "",
        phone: company.phone || "",
        email: company.email || "",
        logo_url: company.logo_url || "",
      });
      // Set logo preview from existing logo_file
      if (company.logo_file) {
        setLogoPreview(`data:image/png;base64,${company.logo_file}`);
      }
      fetchUsers();
    } else {
      setLoading(false);
    }
  }, [company]);

  const fetchUsers = async () => {
    try {
      const response = await api.get("/admin/users");
      setUsers(response.data);
    } catch (error) {
      console.error("Error fetching users:", error);
    } finally {
      setLoading(false);
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
      const reader = new FileReader();
      reader.onload = () => setLogoPreview(reader.result);
      reader.readAsDataURL(file);
    }
  };

  const handleUploadLogo = async () => {
    if (!logoFile) return null;
    try {
      const logoBase64 = await fileToBase64(logoFile);
      // Remove data URL prefix - send only the base64 content
      const base64Content = logoBase64.includes(',') ? logoBase64.split(',')[1] : logoBase64;
      const response = await api.post(`/companies/${company.id}/logo`, { logo_data: base64Content });
      toast.success("Logo actualizado");
      setLogoFile(null);
      return response.data; // Return updated company
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Error al subir logo"));
      return null;
    }
  };

  const handleUpdateCompany = async (e) => {
    e.preventDefault();
    try {
      const response = await api.put(`/companies/${company.id}`, companyForm);
      let updatedCompany = response.data;
      
      // Upload logo if changed
      if (logoFile) {
        const logoResponse = await handleUploadLogo();
        if (logoResponse) {
          updatedCompany = logoResponse;
        }
      }
      
      // Update company state with all data including logo
      setCompany(updatedCompany);
      toast.success("Información actualizada");
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Error al actualizar información"));
    }
  };

  const handleCreateUser = async (e) => {
    e.preventDefault();
    try {
      await api.post("/admin/users", userForm);
      toast.success("Usuario creado exitosamente");
      setUserDialogOpen(false);
      setUserForm({ email: "", full_name: "", phone: "", password: "", role: "user" });
      fetchUsers();
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Error al crear usuario"));
    }
  };

  const handleDeleteUser = async (userId) => {
    if (userId === user?.id) {
      toast.error("No puedes eliminar tu propia cuenta");
      return;
    }
    if (!window.confirm("¿Estás seguro de eliminar este usuario?")) return;
    try {
      await api.delete(`/admin/users/${userId}`);
      toast.success("Usuario eliminado");
      fetchUsers();
    } catch (error) {
      toast.error("Error al eliminar usuario");
    }
  };

  const openPermissionsDialog = (userItem) => {
    setSelectedUser(userItem);
    setSelectedPermissions(userItem.module_permissions || ALL_MODULES.map(m => m.id));
    setPermissionsDialogOpen(true);
  };

  const handleSavePermissions = async () => {
    if (!selectedUser) return;
    try {
      await api.put(`/admin/users/${selectedUser.id}/permissions`, selectedPermissions);
      toast.success("Permisos actualizados");
      setPermissionsDialogOpen(false);
      fetchUsers();
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Error al guardar permisos"));
    }
  };

  const togglePermission = (moduleId) => {
    setSelectedPermissions(prev => 
      prev.includes(moduleId) 
        ? prev.filter(id => id !== moduleId)
        : [...prev, moduleId]
    );
  };

  const openUserDetailDialog = (userItem) => {
    setSelectedUser(userItem);
    setEditUserForm({
      full_name: userItem.full_name || "",
      email: userItem.email || "",
      phone: userItem.phone || "",
      new_password: "",
    });
    setShowPassword(false);
    setUserDetailDialogOpen(true);
  };

  const handleUpdateUser = async (e) => {
    e.preventDefault();
    if (!selectedUser) return;
    try {
      await api.put(`/admin/users/${selectedUser.id}`, editUserForm);
      toast.success("Usuario actualizado");
      setUserDetailDialogOpen(false);
      fetchUsers();
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Error al actualizar usuario"));
    }
  };

  const handleToggleUserStatus = async (userId, currentStatus) => {
    const action = currentStatus ? "inhabilitar" : "habilitar";
    if (!window.confirm(`¿Estás seguro de ${action} este usuario?`)) return;
    try {
      await api.patch(`/admin/users/${userId}/toggle-status`);
      toast.success(`Usuario ${currentStatus ? "inhabilitado" : "habilitado"}`);
      fetchUsers();
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Error al cambiar estado"));
    }
  };

  const handleBroadcastNotification = async (e) => {
    e.preventDefault();
    if (!broadcastForm.title.trim() || !broadcastForm.message.trim()) {
      toast.error("El título y mensaje son requeridos");
      return;
    }
    try {
      const response = await api.post("/admin/broadcast-notification", broadcastForm);
      toast.success(response.data.message);
      setBroadcastDialogOpen(false);
      setBroadcastForm({ title: "", message: "", notification_type: "info" });
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Error al enviar notificación"));
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-64" />
        <Skeleton className="h-64" />
      </div>
    );
  }

  if (!company) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <AlertTriangle className="h-12 w-12 text-amber-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold">No hay empresa asignada</h2>
          <p className="text-muted-foreground">Contacta al administrador.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in" data-testid="settings-page">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold font-[Chivo] text-slate-900">Configuración</h1>
        <p className="text-muted-foreground">Administra tu empresa y usuarios</p>
      </div>

      {/* Company Info */}
      <Card data-testid="company-settings-card">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Building2 className="h-5 w-5 text-primary" />
            Información de la Empresa
          </CardTitle>
          <CardDescription>Datos generales de tu organización</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleUpdateCompany} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label htmlFor="business_name">Razón Social</Label>
                <Input
                  id="business_name"
                  value={companyForm.business_name}
                  onChange={(e) => setCompanyForm({ ...companyForm, business_name: e.target.value })}
                  disabled={!isAdmin()}
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="rfc">RFC</Label>
                <Input
                  id="rfc"
                  value={companyForm.rfc}
                  onChange={(e) => setCompanyForm({ ...companyForm, rfc: e.target.value.toUpperCase() })}
                  disabled={!isAdmin()}
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="email">Correo Electrónico</Label>
                <Input
                  id="email"
                  type="email"
                  value={companyForm.email}
                  onChange={(e) => setCompanyForm({ ...companyForm, email: e.target.value })}
                  disabled={!isAdmin()}
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="phone">Teléfono</Label>
                <Input
                  id="phone"
                  value={companyForm.phone}
                  onChange={(e) => setCompanyForm({ ...companyForm, phone: e.target.value })}
                  disabled={!isAdmin()}
                />
              </div>
              <div className="col-span-full grid gap-2">
                <Label htmlFor="address">Dirección</Label>
                <Input
                  id="address"
                  value={companyForm.address}
                  onChange={(e) => setCompanyForm({ ...companyForm, address: e.target.value })}
                  disabled={!isAdmin()}
                />
              </div>
              <div className="col-span-full grid gap-2">
                <Label>Logo de la Empresa</Label>
                <div className="flex items-center gap-4">
                  {/* Logo Preview */}
                  <div className="h-20 w-20 border rounded-lg flex items-center justify-center bg-slate-50 overflow-hidden">
                    {logoPreview ? (
                      <img src={logoPreview} alt="Logo" className="h-16 w-16 object-contain" />
                    ) : company?.logo_file ? (
                      <img src={`data:image/png;base64,${company.logo_file}`} alt="Logo" className="h-16 w-16 object-contain" />
                    ) : company?.logo_url ? (
                      <img src={company.logo_url} alt="Logo" className="h-16 w-16 object-contain" />
                    ) : (
                      <Image className="h-8 w-8 text-slate-300" />
                    )}
                  </div>
                  {/* Upload Button */}
                  {isAdmin() && (
                    <div className="flex-1">
                      <input
                        type="file"
                        id="logo-upload"
                        className="hidden"
                        accept=".png,.jpg,.jpeg,.webp"
                        onChange={handleLogoSelect}
                      />
                      <label htmlFor="logo-upload">
                        <Button type="button" variant="outline" className="cursor-pointer" asChild>
                          <span>
                            <Upload className="mr-2 h-4 w-4" />
                            {logoFile ? logoFile.name : "Subir Logo"}
                          </span>
                        </Button>
                      </label>
                      <p className="text-xs text-muted-foreground mt-1">PNG, JPG o WebP (máx. 2MB)</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
            {isAdmin() && (
              <div className="flex justify-end">
                <Button type="submit" className="btn-industrial" data-testid="save-company-btn">
                  Guardar Cambios
                </Button>
              </div>
            )}
          </form>
        </CardContent>
      </Card>

      {/* Users Management */}
      {isAdmin() && (
        <Card data-testid="users-settings-card">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Users className="h-5 w-5 text-primary" />
                  Usuarios
                </CardTitle>
                <CardDescription>Gestiona los usuarios de tu empresa</CardDescription>
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  onClick={() => setBroadcastDialogOpen(true)}
                  data-testid="broadcast-btn"
                >
                  <Bell className="mr-2 h-4 w-4" />
                  Notificar
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setUserDialogOpen(true)}
                  data-testid="add-user-btn"
                >
                  <UserPlus className="mr-2 h-4 w-4" />
                  Nuevo Usuario
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="rounded-sm border overflow-hidden">
              <Table>
                <TableHeader>
                  <TableRow className="bg-slate-50">
                    <TableHead>Nombre</TableHead>
                    <TableHead>Email</TableHead>
                    <TableHead>Rol</TableHead>
                    <TableHead>Estado</TableHead>
                    <TableHead className="w-[50px]"></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {users.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={5} className="text-center py-8 text-muted-foreground">
                        No hay usuarios registrados
                      </TableCell>
                    </TableRow>
                  ) : (
                    users.map((u) => (
                      <TableRow key={u.id} className={!u.is_active ? "bg-slate-50 opacity-60" : ""}>
                        <TableCell className="font-medium">{u.full_name}</TableCell>
                        <TableCell>{u.email}</TableCell>
                        <TableCell>
                          <Badge variant="outline">{getStatusLabel(u.role)}</Badge>
                        </TableCell>
                        <TableCell>
                          <Badge className={u.is_active !== false ? "bg-emerald-100 text-emerald-800" : "bg-red-100 text-red-800"}>
                            {u.is_active !== false ? "Activo" : "Inhabilitado"}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          {u.id !== user?.id && (
                            <div className="flex items-center gap-1">
                              <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => openUserDetailDialog(u)}
                                className="text-blue-600 hover:text-blue-700"
                                title="Ver detalles / Editar"
                              >
                                <Eye className="h-4 w-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => openPermissionsDialog(u)}
                                className="text-slate-600 hover:text-primary"
                                title="Configurar permisos"
                              >
                                <Shield className="h-4 w-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => handleToggleUserStatus(u.id, u.is_active !== false)}
                                className={u.is_active !== false ? "text-orange-600 hover:text-orange-700" : "text-emerald-600 hover:text-emerald-700"}
                                title={u.is_active !== false ? "Inhabilitar usuario" : "Habilitar usuario"}
                              >
                                {u.is_active !== false ? <UserX className="h-4 w-4" /> : <UserCheck className="h-4 w-4" />}
                              </Button>
                              <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => handleDeleteUser(u.id)}
                                className="text-red-600 hover:text-red-700"
                                title="Eliminar usuario"
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </div>
                          )}
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Storage Reminder */}
      <Card className="border-amber-200 bg-amber-50">
        <CardContent className="flex items-center gap-3 py-4">
          <AlertTriangle className="h-5 w-5 text-amber-600" />
          <p className="text-sm text-amber-800">
            <strong>Recordatorio:</strong> El almacenamiento de archivos está pendiente de configuración.
            Los logos y documentos se almacenan actualmente como URLs externas.
          </p>
        </CardContent>
      </Card>

      {/* Broadcast Notification Dialog */}
      <Dialog open={broadcastDialogOpen} onOpenChange={setBroadcastDialogOpen}>
        <DialogContent className="sm:max-w-[450px]">
          <form onSubmit={handleBroadcastNotification}>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Bell className="h-5 w-5 text-primary" />
                Enviar Notificación Masiva
              </DialogTitle>
              <DialogDescription>
                Envía un mensaje a todos los usuarios de tu empresa
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>Título *</Label>
                <Input
                  value={broadcastForm.title}
                  onChange={(e) => setBroadcastForm({ ...broadcastForm, title: e.target.value })}
                  placeholder="Ej: Aviso importante"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label>Mensaje *</Label>
                <Textarea
                  value={broadcastForm.message}
                  onChange={(e) => setBroadcastForm({ ...broadcastForm, message: e.target.value })}
                  placeholder="Escribe el mensaje que deseas enviar..."
                  rows={4}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label>Tipo</Label>
                <Select
                  value={broadcastForm.notification_type}
                  onValueChange={(value) => setBroadcastForm({ ...broadcastForm, notification_type: value })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="info">Informativo</SelectItem>
                    <SelectItem value="success">Éxito</SelectItem>
                    <SelectItem value="warning">Advertencia</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setBroadcastDialogOpen(false)}>
                Cancelar
              </Button>
              <Button type="submit" className="btn-industrial">
                <Send className="mr-2 h-4 w-4" />
                Enviar a Todos
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Create User Dialog */}
      <Dialog open={userDialogOpen} onOpenChange={setUserDialogOpen}>
        <DialogContent className="sm:max-w-[400px]">
          <form onSubmit={handleCreateUser}>
            <DialogHeader>
              <DialogTitle>Nuevo Usuario</DialogTitle>
              <DialogDescription>
                Crea un nuevo usuario para tu empresa
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid gap-2">
                <Label htmlFor="user_name">Nombre Completo *</Label>
                <Input
                  id="user_name"
                  value={userForm.full_name}
                  onChange={(e) => setUserForm({ ...userForm, full_name: e.target.value })}
                  required
                  data-testid="new-user-name-input"
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="user_email">Correo Electrónico *</Label>
                <Input
                  id="user_email"
                  type="email"
                  value={userForm.email}
                  onChange={(e) => setUserForm({ ...userForm, email: e.target.value })}
                  required
                  data-testid="new-user-email-input"
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="user_phone">Teléfono</Label>
                <Input
                  id="user_phone"
                  value={userForm.phone}
                  onChange={(e) => setUserForm({ ...userForm, phone: e.target.value })}
                  placeholder="+52 55 1234 5678"
                  data-testid="new-user-phone-input"
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="user_password">Contraseña *</Label>
                <Input
                  id="user_password"
                  type="password"
                  value={userForm.password}
                  onChange={(e) => setUserForm({ ...userForm, password: e.target.value })}
                  required
                  data-testid="new-user-password-input"
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="user_role">Rol</Label>
                <Select
                  value={userForm.role}
                  onValueChange={(value) => setUserForm({ ...userForm, role: value })}
                >
                  <SelectTrigger data-testid="new-user-role-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {ROLES.map((role) => (
                      <SelectItem key={role.value} value={role.value}>
                        {role.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setUserDialogOpen(false)}>
                Cancelar
              </Button>
              <Button type="submit" className="btn-industrial" data-testid="create-user-btn">
                Crear Usuario
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Permissions Dialog */}
      <Dialog open={permissionsDialogOpen} onOpenChange={setPermissionsDialogOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5" />
              Permisos de Módulos
            </DialogTitle>
            <DialogDescription>
              {selectedUser?.full_name} - {selectedUser?.email}
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <p className="text-sm text-muted-foreground mb-4">
              Selecciona los módulos a los que este usuario tendrá acceso:
            </p>
            <div className="grid grid-cols-2 gap-3">
              {ALL_MODULES.map((mod) => (
                <div
                  key={mod.id}
                  className={`flex items-center gap-3 p-3 border rounded-sm cursor-pointer transition-colors ${
                    selectedPermissions.includes(mod.id) 
                      ? "border-primary bg-primary/5" 
                      : "hover:bg-slate-50"
                  }`}
                  onClick={() => togglePermission(mod.id)}
                >
                  <Checkbox
                    checked={selectedPermissions.includes(mod.id)}
                    onCheckedChange={() => togglePermission(mod.id)}
                  />
                  <span className="text-sm">{mod.label}</span>
                </div>
              ))}
            </div>
            <div className="flex justify-between mt-4 pt-4 border-t">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setSelectedPermissions(ALL_MODULES.map(m => m.id))}
              >
                Seleccionar todos
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setSelectedPermissions([])}
              >
                Quitar todos
              </Button>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setPermissionsDialogOpen(false)}>
              Cancelar
            </Button>
            <Button className="btn-industrial" onClick={handleSavePermissions}>
              Guardar Permisos
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* User Detail/Edit Dialog */}
      <Dialog open={userDetailDialogOpen} onOpenChange={setUserDetailDialogOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <form onSubmit={handleUpdateUser}>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Eye className="h-5 w-5" />
                Información del Usuario
              </DialogTitle>
              <DialogDescription>
                Ver y editar información del usuario
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              {/* Read-only info */}
              <div className="grid grid-cols-2 gap-4">
                <div className="p-3 bg-slate-50 rounded-sm">
                  <div className="text-xs text-muted-foreground">ID de Usuario</div>
                  <div className="font-mono text-sm truncate">{selectedUser?.id}</div>
                </div>
                <div className="p-3 bg-slate-50 rounded-sm">
                  <div className="text-xs text-muted-foreground">Rol</div>
                  <Badge variant="outline">{getStatusLabel(selectedUser?.role)}</Badge>
                </div>
              </div>
              <div className="p-3 bg-slate-50 rounded-sm">
                <div className="text-xs text-muted-foreground mb-1">Contraseña Actual</div>
                <div className="flex items-center gap-2">
                  <div className="font-mono text-sm flex-1 bg-white border rounded px-2 py-1">
                    {showPassword ? "••••••••" : "********"}
                  </div>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    onClick={() => setShowPassword(!showPassword)}
                    className="h-8 w-8"
                  >
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </Button>
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  Por seguridad, las contraseñas están encriptadas y no se pueden visualizar
                </p>
              </div>
              
              <Separator />
              
              {/* Editable fields */}
              <div className="grid gap-4">
                <div className="grid gap-2">
                  <Label>Nombre Completo</Label>
                  <Input
                    value={editUserForm.full_name}
                    onChange={(e) => setEditUserForm({ ...editUserForm, full_name: e.target.value })}
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="grid gap-2">
                    <Label>Email</Label>
                    <Input
                      type="email"
                      value={editUserForm.email}
                      onChange={(e) => setEditUserForm({ ...editUserForm, email: e.target.value })}
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label>Teléfono</Label>
                    <Input
                      value={editUserForm.phone}
                      onChange={(e) => setEditUserForm({ ...editUserForm, phone: e.target.value })}
                    />
                  </div>
                </div>
                <div className="grid gap-2">
                  <Label className="flex items-center gap-2">
                    <Key className="h-4 w-4" />
                    Nueva Contraseña
                  </Label>
                  <Input
                    type="password"
                    value={editUserForm.new_password}
                    onChange={(e) => setEditUserForm({ ...editUserForm, new_password: e.target.value })}
                    placeholder="Dejar vacío para mantener actual"
                  />
                </div>
              </div>
              
              {/* Status */}
              <div className="flex items-center justify-between p-3 bg-slate-50 rounded-sm">
                <div>
                  <div className="text-sm font-medium">Estado del Usuario</div>
                  <Badge className={selectedUser?.is_active !== false ? "bg-emerald-100 text-emerald-800" : "bg-red-100 text-red-800"}>
                    {selectedUser?.is_active !== false ? "Activo" : "Inhabilitado"}
                  </Badge>
                </div>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    handleToggleUserStatus(selectedUser?.id, selectedUser?.is_active !== false);
                    setUserDetailDialogOpen(false);
                  }}
                  className={selectedUser?.is_active !== false ? "text-orange-600 border-orange-300" : "text-emerald-600 border-emerald-300"}
                >
                  {selectedUser?.is_active !== false ? (
                    <>
                      <UserX className="mr-2 h-4 w-4" />
                      Inhabilitar
                    </>
                  ) : (
                    <>
                      <UserCheck className="mr-2 h-4 w-4" />
                      Habilitar
                    </>
                  )}
                </Button>
              </div>
              
              {/* Created info */}
              <div className="text-xs text-muted-foreground">
                Creado: {selectedUser?.created_at ? formatDate(selectedUser.created_at) : "N/A"}
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setUserDetailDialogOpen(false)}>
                Cancelar
              </Button>
              <Button type="submit" className="btn-industrial">
                Guardar Cambios
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Settings;
