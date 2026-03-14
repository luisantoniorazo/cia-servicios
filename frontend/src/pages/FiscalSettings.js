import React, { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Badge } from "../components/ui/badge";
import { Separator } from "../components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { Alert, AlertDescription } from "../components/ui/alert";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import { toast } from "sonner";
import { 
  FileText, 
  Shield, 
  Upload, 
  Check, 
  X, 
  AlertTriangle, 
  Building2,
  Save,
  Trash2,
  CheckCircle,
  XCircle,
  Info
} from "lucide-react";

const PAC_PROVIDERS = [
  { value: "none", label: "Sin proveedor (solo preparación)", description: "Configura los datos pero no podrás timbrar" },
  { value: "facturama", label: "Facturama", description: "API fácil de usar, ideal para empezar" },
  { value: "finkok", label: "Finkok", description: "Económico, buena documentación" },
  { value: "sw_sapien", label: "SW Sapien", description: "Robusto, alto volumen" },
];

export const FiscalSettings = () => {
  const { api, company } = useAuth();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [cfdiStatus, setCfdiStatus] = useState(null);
  const [regimenes, setRegimenes] = useState([]);
  const [companyData, setCompanyData] = useState({
    regimen_fiscal: "",
    codigo_postal_fiscal: "",
    lugar_expedicion: "",
  });
  const [certificateData, setCertificateData] = useState({
    has_certificate: false,
    pac_provider: "none",
    pac_user: "",
    pac_password: "",
  });
  const [uploadData, setUploadData] = useState({
    certificate_file: null,
    private_key_file: null,
    private_key_password: "",
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      // Load catalogs
      const regimenesRes = await api.get("/sat/regimen-fiscal");
      setRegimenes(regimenesRes.data);

      // Load CFDI status
      const statusRes = await api.get("/company/cfdi-status");
      setCfdiStatus(statusRes.data);

      // Load certificate data
      const certRes = await api.get("/company/csd-certificate");
      if (certRes.data && certRes.data.id) {
        setCertificateData({
          has_certificate: true,
          pac_provider: certRes.data.pac_provider || "none",
          pac_user: certRes.data.pac_user || "",
          pac_password: "",
        });
      }

      // Load company fiscal data
      if (company) {
        setCompanyData({
          regimen_fiscal: company.regimen_fiscal || "",
          codigo_postal_fiscal: company.codigo_postal_fiscal || "",
          lugar_expedicion: company.lugar_expedicion || company.codigo_postal_fiscal || "",
        });
      }
    } catch (error) {
      console.error("Error loading fiscal data:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveCompanyFiscal = async () => {
    setSaving(true);
    try {
      await api.patch("/companies/current", companyData);
      toast.success("Datos fiscales guardados");
      loadData();
    } catch (error) {
      toast.error("Error al guardar datos fiscales");
    } finally {
      setSaving(false);
    }
  };

  const handleFileUpload = (e, type) => {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = () => {
      const base64 = reader.result.split(",")[1];
      setUploadData({ ...uploadData, [type]: base64 });
    };
    reader.readAsDataURL(file);
  };

  const handleUploadCertificate = async () => {
    if (!uploadData.certificate_file || !uploadData.private_key_file || !uploadData.private_key_password) {
      toast.error("Completa todos los campos del certificado");
      return;
    }

    setSaving(true);
    try {
      await api.post("/company/csd-certificate", {
        certificate_file: uploadData.certificate_file,
        private_key_file: uploadData.private_key_file,
        private_key_password: uploadData.private_key_password,
        pac_provider: certificateData.pac_provider,
        pac_user: certificateData.pac_user,
        pac_password: certificateData.pac_password,
      });
      toast.success("Certificado guardado correctamente");
      setUploadData({ certificate_file: null, private_key_file: null, private_key_password: "" });
      loadData();
    } catch (error) {
      toast.error("Error al guardar certificado");
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteCertificate = async () => {
    if (!window.confirm("¿Estás seguro de eliminar el certificado CSD?")) return;
    
    try {
      await api.delete("/company/csd-certificate");
      toast.success("Certificado eliminado");
      setCertificateData({ has_certificate: false, pac_provider: "none", pac_user: "", pac_password: "" });
      loadData();
    } catch (error) {
      toast.error("Error al eliminar certificado");
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
    <div className="space-y-6 animate-fade-in" data-testid="fiscal-settings-page">
      <div>
        <h1 className="text-2xl sm:text-3xl font-bold font-[Chivo]">Configuración Fiscal</h1>
        <p className="text-muted-foreground">Prepara tu empresa para facturación electrónica (CFDI)</p>
      </div>

      {/* Status Card */}
      <Card className={cfdiStatus?.ready ? "border-emerald-300 bg-emerald-50" : "border-amber-300 bg-amber-50"}>
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            {cfdiStatus?.ready ? (
              <CheckCircle className="h-5 w-5 text-emerald-600 mt-0.5" />
            ) : (
              <AlertTriangle className="h-5 w-5 text-amber-600 mt-0.5" />
            )}
            <div className="flex-1">
              <p className={`font-semibold ${cfdiStatus?.ready ? "text-emerald-800" : "text-amber-800"}`}>
                {cfdiStatus?.ready ? "¡Listo para facturar!" : "Configuración incompleta"}
              </p>
              {cfdiStatus?.issues?.length > 0 && (
                <ul className="text-sm text-amber-700 mt-1 space-y-0.5">
                  {cfdiStatus.issues.map((issue, i) => (
                    <li key={i}>• {issue}</li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      <Tabs defaultValue="company" className="space-y-4">
        <TabsList className="grid w-full grid-cols-2 lg:w-[400px]">
          <TabsTrigger value="company">
            <Building2 className="h-4 w-4 mr-2" />
            Datos Fiscales
          </TabsTrigger>
          <TabsTrigger value="certificate">
            <Shield className="h-4 w-4 mr-2" />
            Certificado CSD
          </TabsTrigger>
        </TabsList>

        {/* Company Fiscal Data */}
        <TabsContent value="company">
          <Card>
            <CardHeader>
              <CardTitle>Datos Fiscales de la Empresa</CardTitle>
              <CardDescription>
                Información requerida para emitir CFDI
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>RFC</Label>
                  <Input value={company?.rfc || ""} disabled className="bg-slate-50" />
                  <p className="text-xs text-muted-foreground">Se configura en datos generales de la empresa</p>
                </div>
                <div className="space-y-2">
                  <Label>Razón Social</Label>
                  <Input value={company?.business_name || ""} disabled className="bg-slate-50" />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Régimen Fiscal *</Label>
                  <Select
                    value={companyData.regimen_fiscal}
                    onValueChange={(value) => setCompanyData({ ...companyData, regimen_fiscal: value })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Seleccionar régimen..." />
                    </SelectTrigger>
                    <SelectContent>
                      {regimenes.map((r) => (
                        <SelectItem key={r.clave} value={r.clave}>
                          {r.clave} - {r.descripcion}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Código Postal Fiscal *</Label>
                  <Input
                    value={companyData.codigo_postal_fiscal}
                    onChange={(e) => setCompanyData({ ...companyData, codigo_postal_fiscal: e.target.value })}
                    placeholder="12345"
                    maxLength={5}
                  />
                  <p className="text-xs text-muted-foreground">CP del domicilio fiscal registrado en SAT</p>
                </div>
              </div>

              <div className="space-y-2">
                <Label>Lugar de Expedición</Label>
                <Input
                  value={companyData.lugar_expedicion}
                  onChange={(e) => setCompanyData({ ...companyData, lugar_expedicion: e.target.value })}
                  placeholder="Mismo que CP fiscal o diferente si expide desde otra ubicación"
                  maxLength={5}
                />
              </div>

              <div className="flex justify-end pt-4">
                <Button onClick={handleSaveCompanyFiscal} disabled={saving} className="btn-industrial">
                  <Save className="h-4 w-4 mr-2" />
                  {saving ? "Guardando..." : "Guardar Datos Fiscales"}
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* CSD Certificate */}
        <TabsContent value="certificate">
          <div className="space-y-4">
            {/* Info Alert */}
            <Alert>
              <Info className="h-4 w-4" />
              <AlertDescription>
                El Certificado de Sello Digital (CSD) se obtiene en el portal del SAT.
                Necesitas el archivo .cer, el archivo .key y la contraseña de la llave privada.
              </AlertDescription>
            </Alert>

            {certificateData.has_certificate ? (
              <Card className="border-emerald-200">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="flex items-center gap-2">
                        <CheckCircle className="h-5 w-5 text-emerald-500" />
                        Certificado Configurado
                      </CardTitle>
                      <CardDescription>
                        Tu empresa tiene un certificado CSD activo
                      </CardDescription>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      className="text-red-600 border-red-300 hover:bg-red-50"
                      onClick={handleDeleteCertificate}
                    >
                      <Trash2 className="h-4 w-4 mr-2" />
                      Eliminar
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-muted-foreground">Proveedor PAC:</span>
                    <Badge variant="outline">
                      {PAC_PROVIDERS.find(p => p.value === certificateData.pac_provider)?.label || "Sin configurar"}
                    </Badge>
                  </div>
                </CardContent>
              </Card>
            ) : (
              <Card>
                <CardHeader>
                  <CardTitle>Subir Certificado CSD</CardTitle>
                  <CardDescription>
                    Sube los archivos de tu Certificado de Sello Digital
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Archivo .cer *</Label>
                      <Input
                        type="file"
                        accept=".cer"
                        onChange={(e) => handleFileUpload(e, "certificate_file")}
                        className="cursor-pointer"
                      />
                      {uploadData.certificate_file && (
                        <Badge variant="secondary" className="text-xs">
                          <Check className="h-3 w-3 mr-1" /> Archivo cargado
                        </Badge>
                      )}
                    </div>
                    <div className="space-y-2">
                      <Label>Archivo .key *</Label>
                      <Input
                        type="file"
                        accept=".key"
                        onChange={(e) => handleFileUpload(e, "private_key_file")}
                        className="cursor-pointer"
                      />
                      {uploadData.private_key_file && (
                        <Badge variant="secondary" className="text-xs">
                          <Check className="h-3 w-3 mr-1" /> Archivo cargado
                        </Badge>
                      )}
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label>Contraseña de la llave privada *</Label>
                    <Input
                      type="password"
                      value={uploadData.private_key_password}
                      onChange={(e) => setUploadData({ ...uploadData, private_key_password: e.target.value })}
                      placeholder="••••••••"
                    />
                  </div>

                  <Separator />

                  <div className="space-y-2">
                    <Label>Proveedor PAC</Label>
                    <Select
                      value={certificateData.pac_provider}
                      onValueChange={(value) => setCertificateData({ ...certificateData, pac_provider: value })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {PAC_PROVIDERS.map((p) => (
                          <SelectItem key={p.value} value={p.value}>
                            <div>
                              <span className="font-medium">{p.label}</span>
                              <span className="text-xs text-muted-foreground ml-2">{p.description}</span>
                            </div>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {certificateData.pac_provider !== "none" && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label>Usuario PAC</Label>
                        <Input
                          value={certificateData.pac_user}
                          onChange={(e) => setCertificateData({ ...certificateData, pac_user: e.target.value })}
                          placeholder="Usuario del PAC"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Contraseña PAC</Label>
                        <Input
                          type="password"
                          value={certificateData.pac_password}
                          onChange={(e) => setCertificateData({ ...certificateData, pac_password: e.target.value })}
                          placeholder="••••••••"
                        />
                      </div>
                    </div>
                  )}

                  <div className="flex justify-end pt-4">
                    <Button
                      onClick={handleUploadCertificate}
                      disabled={saving || !uploadData.certificate_file || !uploadData.private_key_file || !uploadData.private_key_password}
                      className="btn-industrial"
                    >
                      <Upload className="h-4 w-4 mr-2" />
                      {saving ? "Guardando..." : "Guardar Certificado"}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default FiscalSettings;
