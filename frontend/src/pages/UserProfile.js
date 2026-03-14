import React, { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Switch } from "../components/ui/switch";
import { Separator } from "../components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import { toast } from "sonner";
import { User, Lock, Bell, Palette, Save, Eye, EyeOff } from "lucide-react";

export const UserProfile = () => {
  const { api, user } = useAuth();
  const [profile, setProfile] = useState(null);
  const [preferences, setPreferences] = useState({
    theme: "light",
    language: "es",
    notifications_enabled: true,
    email_notifications: true,
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [passwordForm, setPasswordForm] = useState({
    current_password: "",
    new_password: "",
    confirm_password: "",
  });
  const [showPasswords, setShowPasswords] = useState({
    current: false,
    new: false,
    confirm: false,
  });

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      const response = await api.get("/profile");
      setProfile(response.data.user);
      if (response.data.preferences) {
        setPreferences(response.data.preferences);
      }
    } catch (error) {
      toast.error("Error al cargar perfil");
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateProfile = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await api.patch("/profile", {
        full_name: profile.full_name,
        phone: profile.phone,
      });
      toast.success("Perfil actualizado");
    } catch (error) {
      toast.error("Error al actualizar perfil");
    } finally {
      setSaving(false);
    }
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    if (passwordForm.new_password !== passwordForm.confirm_password) {
      toast.error("Las contraseñas no coinciden");
      return;
    }
    if (passwordForm.new_password.length < 8) {
      toast.error("La contraseña debe tener al menos 8 caracteres");
      return;
    }

    setSaving(true);
    try {
      await api.post("/profile/change-password", {
        current_password: passwordForm.current_password,
        new_password: passwordForm.new_password,
      });
      toast.success("Contraseña actualizada");
      setPasswordForm({ current_password: "", new_password: "", confirm_password: "" });
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al cambiar contraseña");
    } finally {
      setSaving(false);
    }
  };

  const handleUpdatePreferences = async () => {
    setSaving(true);
    try {
      await api.patch("/preferences", preferences);
      toast.success("Preferencias guardadas");
      
      // Apply theme
      if (preferences.theme === "dark") {
        document.documentElement.classList.add("dark");
      } else {
        document.documentElement.classList.remove("dark");
      }
    } catch (error) {
      toast.error("Error al guardar preferencias");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in" data-testid="user-profile-page">
      <div>
        <h1 className="text-2xl sm:text-3xl font-bold font-[Chivo]">Mi Perfil</h1>
        <p className="text-muted-foreground">Administra tu información personal y preferencias</p>
      </div>

      <Tabs defaultValue="profile" className="space-y-4">
        <TabsList className="grid w-full grid-cols-3 lg:w-[400px]">
          <TabsTrigger value="profile" className="text-xs sm:text-sm">
            <User className="h-4 w-4 mr-1 sm:mr-2" />
            Perfil
          </TabsTrigger>
          <TabsTrigger value="security" className="text-xs sm:text-sm">
            <Lock className="h-4 w-4 mr-1 sm:mr-2" />
            Seguridad
          </TabsTrigger>
          <TabsTrigger value="preferences" className="text-xs sm:text-sm">
            <Palette className="h-4 w-4 mr-1 sm:mr-2" />
            Preferencias
          </TabsTrigger>
        </TabsList>

        {/* Profile Tab */}
        <TabsContent value="profile">
          <Card>
            <CardHeader>
              <CardTitle>Información Personal</CardTitle>
              <CardDescription>Actualiza tu información de contacto</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleUpdateProfile} className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Nombre Completo</Label>
                    <Input
                      value={profile?.full_name || ""}
                      onChange={(e) => setProfile({ ...profile, full_name: e.target.value })}
                      placeholder="Tu nombre"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Correo Electrónico</Label>
                    <Input value={profile?.email || ""} disabled className="bg-slate-50" />
                    <p className="text-xs text-muted-foreground">El correo no puede ser modificado</p>
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Teléfono</Label>
                    <Input
                      value={profile?.phone || ""}
                      onChange={(e) => setProfile({ ...profile, phone: e.target.value })}
                      placeholder="(xxx) xxx-xxxx"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Rol</Label>
                    <Input value={profile?.role || ""} disabled className="bg-slate-50 capitalize" />
                  </div>
                </div>

                <div className="flex justify-end">
                  <Button type="submit" disabled={saving} className="btn-industrial">
                    <Save className="h-4 w-4 mr-2" />
                    {saving ? "Guardando..." : "Guardar Cambios"}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Security Tab */}
        <TabsContent value="security">
          <Card>
            <CardHeader>
              <CardTitle>Cambiar Contraseña</CardTitle>
              <CardDescription>Actualiza tu contraseña de acceso</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleChangePassword} className="space-y-4 max-w-md">
                <div className="space-y-2">
                  <Label>Contraseña Actual</Label>
                  <div className="relative">
                    <Input
                      type={showPasswords.current ? "text" : "password"}
                      value={passwordForm.current_password}
                      onChange={(e) =>
                        setPasswordForm({ ...passwordForm, current_password: e.target.value })
                      }
                      placeholder="••••••••"
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      className="absolute right-0 top-0 h-full"
                      onClick={() => setShowPasswords({ ...showPasswords, current: !showPasswords.current })}
                    >
                      {showPasswords.current ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </Button>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>Nueva Contraseña</Label>
                  <div className="relative">
                    <Input
                      type={showPasswords.new ? "text" : "password"}
                      value={passwordForm.new_password}
                      onChange={(e) =>
                        setPasswordForm({ ...passwordForm, new_password: e.target.value })
                      }
                      placeholder="••••••••"
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      className="absolute right-0 top-0 h-full"
                      onClick={() => setShowPasswords({ ...showPasswords, new: !showPasswords.new })}
                    >
                      {showPasswords.new ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </Button>
                  </div>
                  <p className="text-xs text-muted-foreground">Mínimo 8 caracteres</p>
                </div>

                <div className="space-y-2">
                  <Label>Confirmar Nueva Contraseña</Label>
                  <div className="relative">
                    <Input
                      type={showPasswords.confirm ? "text" : "password"}
                      value={passwordForm.confirm_password}
                      onChange={(e) =>
                        setPasswordForm({ ...passwordForm, confirm_password: e.target.value })
                      }
                      placeholder="••••••••"
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      className="absolute right-0 top-0 h-full"
                      onClick={() => setShowPasswords({ ...showPasswords, confirm: !showPasswords.confirm })}
                    >
                      {showPasswords.confirm ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </Button>
                  </div>
                </div>

                <Button type="submit" disabled={saving} className="btn-industrial">
                  <Lock className="h-4 w-4 mr-2" />
                  {saving ? "Actualizando..." : "Actualizar Contraseña"}
                </Button>
              </form>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Preferences Tab */}
        <TabsContent value="preferences">
          <Card>
            <CardHeader>
              <CardTitle>Preferencias de Usuario</CardTitle>
              <CardDescription>Personaliza tu experiencia en el sistema</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Theme */}
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Tema de la Interfaz</Label>
                  <p className="text-sm text-muted-foreground">Selecciona el tema visual</p>
                </div>
                <Select
                  value={preferences.theme}
                  onValueChange={(value) => setPreferences({ ...preferences, theme: value })}
                >
                  <SelectTrigger className="w-32">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="light">Claro</SelectItem>
                    <SelectItem value="dark">Oscuro</SelectItem>
                    <SelectItem value="system">Sistema</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <Separator />

              {/* Language */}
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Idioma</Label>
                  <p className="text-sm text-muted-foreground">Idioma de la interfaz</p>
                </div>
                <Select
                  value={preferences.language}
                  onValueChange={(value) => setPreferences({ ...preferences, language: value })}
                >
                  <SelectTrigger className="w-32">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="es">Español</SelectItem>
                    <SelectItem value="en">English</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <Separator />

              {/* Notifications */}
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Notificaciones en App</Label>
                  <p className="text-sm text-muted-foreground">Recibir notificaciones dentro del sistema</p>
                </div>
                <Switch
                  checked={preferences.notifications_enabled}
                  onCheckedChange={(checked) =>
                    setPreferences({ ...preferences, notifications_enabled: checked })
                  }
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Notificaciones por Email</Label>
                  <p className="text-sm text-muted-foreground">Recibir recordatorios y alertas por correo</p>
                </div>
                <Switch
                  checked={preferences.email_notifications}
                  onCheckedChange={(checked) =>
                    setPreferences({ ...preferences, email_notifications: checked })
                  }
                />
              </div>

              <div className="flex justify-end pt-4">
                <Button onClick={handleUpdatePreferences} disabled={saving} className="btn-industrial">
                  <Save className="h-4 w-4 mr-2" />
                  {saving ? "Guardando..." : "Guardar Preferencias"}
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default UserProfile;
