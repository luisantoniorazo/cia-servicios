import React, { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
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
  Alert,
  AlertDescription,
  AlertTitle,
} from "../components/ui/alert";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { toast } from "sonner";
import {
  FileText,
  Settings,
  CheckCircle,
  XCircle,
  AlertTriangle,
  RefreshCw,
  Building2,
  Key,
  Globe,
  Zap,
  BarChart3,
  Eye,
  EyeOff,
  TestTube,
  Save,
  Info,
  ArrowLeft,
} from "lucide-react";

export const FacturamaConfig = () => {
  const { api } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [config, setConfig] = useState(null);
  const [stats, setStats] = useState(null);
  const [companies, setCompanies] = useState([]);
  const [showPassword, setShowPassword] = useState(false);
  const [configDialogOpen, setConfigDialogOpen] = useState(false);
  const [form, setForm] = useState({
    api_user: "",
    api_password: "",
    environment: "sandbox",
    rfc_emisor: "",
    nombre_emisor: "",
    regimen_fiscal_emisor: "",
    lugar_expedicion: "",
    serie: "S",
    auto_generate_on_payment: false,
  });

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const [configRes, statsRes, companiesRes] = await Promise.all([
        api.get("/super-admin/facturama/config"),
        api.get("/super-admin/facturama/stats"),
        api.get("/super-admin/companies"),
      ]);
      
      setConfig(configRes.data);
      setStats(statsRes.data);
      setCompanies(companiesRes.data || []);
      
      if (configRes.data.configured) {
        setForm({
          api_user: configRes.data.api_user || "",
          api_password: "",
          environment: configRes.data.environment || "sandbox",
          rfc_emisor: configRes.data.rfc_emisor || "",
          nombre_emisor: configRes.data.nombre_emisor || "",
          regimen_fiscal_emisor: configRes.data.regimen_fiscal_emisor || "",
          lugar_expedicion: configRes.data.lugar_expedicion || "",
          serie: configRes.data.serie || "S",
          auto_generate_on_payment: configRes.data.auto_generate_on_payment || false,
        });
      }
    } catch (error) {
      console.error("Error fetching data:", error);
    } finally {
      setLoading(false);
    }
  }, [api]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleSaveConfig = async (e) => {
    e.preventDefault();
    if (!form.api_user) {
      toast.error("El usuario de API es requerido");
      return;
    }
    if (!config?.configured && !form.api_password) {
      toast.error("La contraseña de API es requerida");
      return;
    }

    try {
      setSaving(true);
      const payload = { ...form };
      if (!payload.api_password) {
        delete payload.api_password;
      }
      
      await api.post("/super-admin/facturama/config", payload);
      toast.success("Configuración guardada");
      setConfigDialogOpen(false);
      fetchData();
    } catch (error) {
      toast.error("Error al guardar configuración");
    } finally {
      setSaving(false);
    }
  };

  const handleTestConnection = async () => {
    try {
      setTesting(true);
      const response = await api.post("/super-admin/facturama/test-connection");
      if (response.data.success) {
        toast.success(response.data.message);
      } else {
        toast.error(response.data.message);
      }
    } catch (error) {
      toast.error("Error al probar conexión");
    } finally {
      setTesting(false);
    }
  };

  const handleToggleBilling = async (companyId, currentValue) => {
    try {
      await api.patch(`/super-admin/companies/${companyId}/billing`, null, {
        params: { billing_included: !currentValue }
      });
      toast.success(`Facturación ${!currentValue ? "incluida" : "excluida"}`);
      fetchData();
    } catch (error) {
      toast.error("Error al actualizar facturación");
    }
  };

  if (loading) {
    return (
      <div className="space-y-6 p-6">
        <Skeleton className="h-8 w-64" />
        <div className="grid gap-4 md:grid-cols-3">
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6" data-testid="facturama-config-page">
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
              <FileText className="h-6 w-6 text-primary" />
              Configuración de Facturama
            </h1>
            <p className="text-muted-foreground">
              Configura la cuenta maestra de Facturama para facturación electrónica
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          {config?.configured && (
            <Button variant="outline" onClick={handleTestConnection} disabled={testing}>
              <TestTube className="mr-2 h-4 w-4" />
              {testing ? "Probando..." : "Probar Conexión"}
            </Button>
          )}
          <Button onClick={() => setConfigDialogOpen(true)}>
            <Settings className="mr-2 h-4 w-4" />
            {config?.configured ? "Editar" : "Configurar"}
          </Button>
        </div>
      </div>

      {/* Status Alert */}
      {!config?.configured ? (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>Facturama no configurado</AlertTitle>
          <AlertDescription>
            Configura tus credenciales de Facturama para habilitar la facturación electrónica para tus clientes.
          </AlertDescription>
        </Alert>
      ) : (
        <Alert className="border-emerald-500 bg-emerald-50">
          <CheckCircle className="h-4 w-4 text-emerald-600" />
          <AlertTitle className="text-emerald-800">Facturama configurado</AlertTitle>
          <AlertDescription className="text-emerald-700">
            Modo: <strong>{config.environment === "sandbox" ? "Sandbox (Pruebas)" : "Producción"}</strong>
            {config.environment === "sandbox" && " - Los timbres no tienen validez fiscal"}
          </AlertDescription>
        </Alert>
      )}

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Estado
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              {config?.configured ? (
                <>
                  <CheckCircle className="h-5 w-5 text-emerald-500" />
                  <span className="text-xl font-bold text-emerald-600">Activo</span>
                </>
              ) : (
                <>
                  <XCircle className="h-5 w-5 text-red-500" />
                  <span className="text-xl font-bold text-red-600">Inactivo</span>
                </>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Ambiente
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <Globe className="h-5 w-5 text-blue-500" />
              <span className="text-xl font-bold">
                {config?.environment === "production" ? "Producción" : "Sandbox"}
              </span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Empresas con Facturación
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <Building2 className="h-5 w-5 text-violet-500" />
              <span className="text-xl font-bold">
                {stats?.companies_with_billing || 0}
              </span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Timbres Usados
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <Zap className="h-5 w-5 text-amber-500" />
              <span className="text-xl font-bold">
                {stats?.total_stamps_used || 0}
              </span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="companies" className="space-y-4">
        <TabsList>
          <TabsTrigger value="companies" className="flex items-center gap-2">
            <Building2 className="h-4 w-4" />
            Empresas
          </TabsTrigger>
          <TabsTrigger value="stats" className="flex items-center gap-2">
            <BarChart3 className="h-4 w-4" />
            Estadísticas
          </TabsTrigger>
          <TabsTrigger value="info" className="flex items-center gap-2">
            <Info className="h-4 w-4" />
            Información
          </TabsTrigger>
        </TabsList>

        <TabsContent value="companies">
          <Card>
            <CardHeader>
              <CardTitle>Gestión de Facturación por Empresa</CardTitle>
              <CardDescription>
                Activa o desactiva la facturación incluida para cada empresa
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Empresa</TableHead>
                    <TableHead>RFC</TableHead>
                    <TableHead>Plan</TableHead>
                    <TableHead>Estado</TableHead>
                    <TableHead className="text-center">Facturación Incluida</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {companies.map((company) => (
                    <TableRow key={company.id}>
                      <TableCell className="font-medium">
                        {company.business_name}
                      </TableCell>
                      <TableCell>{company.rfc || "N/A"}</TableCell>
                      <TableCell>
                        <Badge variant="outline">
                          {company.license_type || "Básico"}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={company.subscription_status === "active" ? "default" : "secondary"}
                        >
                          {company.subscription_status === "active" ? "Activa" : company.subscription_status}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-center">
                        <Switch
                          checked={company.billing_included || false}
                          onCheckedChange={() => handleToggleBilling(company.id, company.billing_included)}
                          disabled={!config?.configured}
                        />
                      </TableCell>
                    </TableRow>
                  ))}
                  {companies.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={5} className="text-center text-muted-foreground py-8">
                        No hay empresas registradas
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="stats">
          <Card>
            <CardHeader>
              <CardTitle>Estadísticas de Uso</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="p-4 border rounded-lg">
                  <p className="text-sm text-muted-foreground">Total CFDIs timbrados</p>
                  <p className="text-3xl font-bold">{stats?.total_cfdis_stamped || 0}</p>
                </div>
                <div className="p-4 border rounded-lg">
                  <p className="text-sm text-muted-foreground">CFDIs este mes</p>
                  <p className="text-3xl font-bold">{stats?.month_cfdis_stamped || 0}</p>
                </div>
                <div className="p-4 border rounded-lg">
                  <p className="text-sm text-muted-foreground">Último timbre</p>
                  <p className="text-lg font-medium">
                    {stats?.last_stamp_date 
                      ? new Date(stats.last_stamp_date).toLocaleString()
                      : "Ninguno"}
                  </p>
                </div>
                <div className="p-4 border rounded-lg">
                  <p className="text-sm text-muted-foreground">Empresas con facturación</p>
                  <p className="text-3xl font-bold">{stats?.companies_with_billing || 0}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="info">
          <Card>
            <CardHeader>
              <CardTitle>Información de Facturama</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="prose max-w-none">
                <h3>¿Qué es Facturama?</h3>
                <p>
                  Facturama es un PAC (Proveedor Autorizado de Certificación) que permite generar 
                  comprobantes fiscales digitales (CFDI) válidos ante el SAT.
                </p>
                
                <h3>Modos de operación</h3>
                <ul>
                  <li><strong>Sandbox:</strong> Modo de pruebas. Los CFDIs no tienen validez fiscal.</li>
                  <li><strong>Producción:</strong> Modo real. Los CFDIs son válidos ante el SAT.</li>
                </ul>
                
                <h3>¿Cómo obtener credenciales?</h3>
                <ol>
                  <li>Regístrate en <a href="https://www.facturama.mx" target="_blank" rel="noopener noreferrer">facturama.mx</a></li>
                  <li>Ve a Configuración → API</li>
                  <li>Copia tu Usuario y Contraseña de API</li>
                </ol>
                
                <h3>Facturación incluida vs Propia</h3>
                <ul>
                  <li><strong>Incluida:</strong> La empresa usa TU cuenta de Facturama. Tú pagas los timbres.</li>
                  <li><strong>Propia:</strong> La empresa configura SU cuenta de Facturama. Ellos pagan sus timbres.</li>
                  <li><strong>Manual:</strong> La empresa sube sus CFDIs generados por otro medio.</li>
                </ul>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Config Dialog */}
      <Dialog open={configDialogOpen} onOpenChange={setConfigDialogOpen}>
        <DialogContent className="sm:max-w-[500px] max-h-[90vh] overflow-y-auto">
          <form onSubmit={handleSaveConfig}>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Key className="h-5 w-5" />
                Configurar Facturama
              </DialogTitle>
              <DialogDescription>
                Ingresa las credenciales de tu cuenta de Facturama
              </DialogDescription>
            </DialogHeader>
            
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="api_user">Usuario de API *</Label>
                <Input
                  id="api_user"
                  value={form.api_user}
                  onChange={(e) => setForm({ ...form, api_user: e.target.value })}
                  placeholder="Tu usuario de API de Facturama"
                  required
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="api_password">
                  Contraseña de API {config?.configured ? "(dejar vacío para mantener)" : "*"}
                </Label>
                <div className="relative">
                  <Input
                    id="api_password"
                    type={showPassword ? "text" : "password"}
                    value={form.api_password}
                    onChange={(e) => setForm({ ...form, api_password: e.target.value })}
                    placeholder={config?.configured ? "••••••••" : "Tu contraseña de API"}
                    required={!config?.configured}
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="absolute right-0 top-0 h-full px-3"
                    onClick={() => setShowPassword(!showPassword)}
                  >
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </Button>
                </div>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="environment">Ambiente</Label>
                <Select
                  value={form.environment}
                  onValueChange={(value) => setForm({ ...form, environment: value })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="sandbox">
                      <div className="flex items-center gap-2">
                        <TestTube className="h-4 w-4" />
                        Sandbox (Pruebas)
                      </div>
                    </SelectItem>
                    <SelectItem value="production">
                      <div className="flex items-center gap-2">
                        <Globe className="h-4 w-4" />
                        Producción (Real)
                      </div>
                    </SelectItem>
                  </SelectContent>
                </Select>
                {form.environment === "sandbox" && (
                  <p className="text-xs text-amber-600">
                    En Sandbox los timbres no tienen validez fiscal
                  </p>
                )}
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="rfc_emisor">RFC del Emisor (CIA) *</Label>
                <Input
                  id="rfc_emisor"
                  value={form.rfc_emisor}
                  onChange={(e) => setForm({ ...form, rfc_emisor: e.target.value.toUpperCase() })}
                  placeholder="RFC de tu empresa (ej: XXXX000000XXX)"
                  maxLength={13}
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="nombre_emisor">Nombre del Emisor *</Label>
                <Input
                  id="nombre_emisor"
                  value={form.nombre_emisor}
                  onChange={(e) => setForm({ ...form, nombre_emisor: e.target.value.toUpperCase() })}
                  placeholder="Razón Social (ej: LUIS ANTONIO GARCIA LOPEZ)"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="regimen_fiscal_emisor">Régimen Fiscal</Label>
                  <Select
                    value={form.regimen_fiscal_emisor}
                    onValueChange={(value) => setForm({ ...form, regimen_fiscal_emisor: value })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Seleccionar..." />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="601">601 - General de Ley PM</SelectItem>
                      <SelectItem value="603">603 - Personas Morales sin Fines de Lucro</SelectItem>
                      <SelectItem value="612">612 - Personas Físicas con Act. Emp.</SelectItem>
                      <SelectItem value="621">621 - Incorporación Fiscal</SelectItem>
                      <SelectItem value="626">626 - Régimen Simplificado de Confianza</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="lugar_expedicion">C.P. Expedición *</Label>
                  <Input
                    id="lugar_expedicion"
                    value={form.lugar_expedicion}
                    onChange={(e) => setForm({ ...form, lugar_expedicion: e.target.value })}
                    placeholder="44100"
                    maxLength={5}
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="serie">Serie de Facturas</Label>
                  <Input
                    id="serie"
                    value={form.serie}
                    onChange={(e) => setForm({ ...form, serie: e.target.value.toUpperCase() })}
                    placeholder="S"
                    maxLength={3}
                  />
                </div>
              </div>

              <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg border border-green-200">
                <div>
                  <p className="font-medium text-green-800">Auto-generar CFDI al pagar</p>
                  <p className="text-xs text-green-600">Genera automáticamente el CFDI cuando el cliente paga su suscripción</p>
                </div>
                <Switch
                  checked={form.auto_generate_on_payment}
                  onCheckedChange={(checked) => setForm({ ...form, auto_generate_on_payment: checked })}
                />
              </div>
            </div>
            
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setConfigDialogOpen(false)}>
                Cancelar
              </Button>
              <Button type="submit" disabled={saving}>
                <Save className="mr-2 h-4 w-4" />
                {saving ? "Guardando..." : "Guardar"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default FacturamaConfig;
