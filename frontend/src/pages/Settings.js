import React, { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { getStatusLabel, getApiErrorMessage } from "../lib/utils";
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
} from "lucide-react";
import { Checkbox } from "../components/ui/checkbox";

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
  const [selectedUser, setSelectedUser] = useState(null);
  const [selectedPermissions, setSelectedPermissions] = useState([]);
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
    if (!logoFile) return;
    try {
      const logoBase64 = await fileToBase64(logoFile);
      await api.post(`/companies/${company.id}/logo`, logoBase64, {
        headers: { 'Content-Type': 'application/json' }
      });
      toast.success("Logo actualizado");
      setLogoFile(null);
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Error al subir logo"));
    }
  };

  const handleUpdateCompany = async (e) => {
    e.preventDefault();
    try {
      const response = await api.put(`/companies/${company.id}`, companyForm);
      setCompany(response.data);
      toast.success("Información actualizada");
      
      // Upload logo if changed
      if (logoFile) {
        await handleUploadLogo();
      }
    } catch (error) {
      toast.error("Error al actualizar información");
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
                  <div className="h-20 w-20 border rounded-lg flex items-center justify-center bg-slate-50">
                    {logoPreview ? (
                      <img src={logoPreview} alt="Logo" className="h-16 w-16 object-contain" />
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
              <Button
                variant="outline"
                onClick={() => setUserDialogOpen(true)}
                data-testid="add-user-btn"
              >
                <UserPlus className="mr-2 h-4 w-4" />
                Nuevo Usuario
              </Button>
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
                      <TableRow key={u.id}>
                        <TableCell className="font-medium">{u.full_name}</TableCell>
                        <TableCell>{u.email}</TableCell>
                        <TableCell>
                          <Badge variant="outline">{getStatusLabel(u.role)}</Badge>
                        </TableCell>
                        <TableCell>
                          <Badge className={u.is_active ? "bg-emerald-100 text-emerald-800" : "bg-red-100 text-red-800"}>
                            {u.is_active ? "Activo" : "Inactivo"}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          {u.id !== user?.id && (
                            <div className="flex items-center gap-1">
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
                                onClick={() => handleDeleteUser(u.id)}
                                className="text-red-600 hover:text-red-700"
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
    </div>
  );
};

export default Settings;
