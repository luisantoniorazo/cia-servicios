import React, { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import { Switch } from "../components/ui/switch";
import { Separator } from "../components/ui/separator";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import { toast } from "sonner";
import { FileText, Save, Palette } from "lucide-react";

const FONT_OPTIONS = [
  { value: "Helvetica", label: "Helvetica" },
  { value: "Times-Roman", label: "Times Roman" },
  { value: "Courier", label: "Courier" },
];

export const DocumentSettings = () => {
  const { api } = useAuth();
  const [settings, setSettings] = useState({
    primary_color: "#004e92",
    secondary_color: "#1e293b",
    font_family: "Helvetica",
    show_logo: true,
    show_company_info: true,
    footer_text: "",
    terms_and_conditions: "",
    quote_validity_days: 30,
    invoice_payment_terms: "",
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const response = await api.get("/document-settings");
      setSettings(response.data);
    } catch (error) {
      console.error("Error fetching settings:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.patch("/document-settings", settings);
      toast.success("Configuración guardada");
    } catch (error) {
      toast.error("Error al guardar configuración");
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
    <div className="space-y-6 animate-fade-in" data-testid="document-settings-page">
      <div>
        <h1 className="text-2xl sm:text-3xl font-bold font-[Chivo]">Configuración de Documentos</h1>
        <p className="text-muted-foreground">Personaliza el formato de tus cotizaciones, facturas y órdenes de compra</p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Appearance */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Palette className="h-5 w-5 text-primary" />
              Apariencia
            </CardTitle>
            <CardDescription>Colores y tipografía de los documentos</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Color Principal</Label>
                <div className="flex gap-2">
                  <Input
                    type="color"
                    value={settings.primary_color}
                    onChange={(e) => setSettings({ ...settings, primary_color: e.target.value })}
                    className="w-12 h-10 p-1 cursor-pointer"
                  />
                  <Input
                    value={settings.primary_color}
                    onChange={(e) => setSettings({ ...settings, primary_color: e.target.value })}
                    className="flex-1"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label>Color Secundario</Label>
                <div className="flex gap-2">
                  <Input
                    type="color"
                    value={settings.secondary_color}
                    onChange={(e) => setSettings({ ...settings, secondary_color: e.target.value })}
                    className="w-12 h-10 p-1 cursor-pointer"
                  />
                  <Input
                    value={settings.secondary_color}
                    onChange={(e) => setSettings({ ...settings, secondary_color: e.target.value })}
                    className="flex-1"
                  />
                </div>
              </div>
            </div>

            <div className="space-y-2">
              <Label>Fuente</Label>
              <Select
                value={settings.font_family}
                onValueChange={(value) => setSettings({ ...settings, font_family: value })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {FONT_OPTIONS.map((font) => (
                    <SelectItem key={font.value} value={font.value}>
                      {font.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <Separator />

            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label>Mostrar Logo</Label>
                  <p className="text-sm text-muted-foreground">Incluir el logo de la empresa en documentos</p>
                </div>
                <Switch
                  checked={settings.show_logo}
                  onCheckedChange={(checked) => setSettings({ ...settings, show_logo: checked })}
                />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <Label>Mostrar Datos de Empresa</Label>
                  <p className="text-sm text-muted-foreground">RFC, dirección y contacto en encabezado</p>
                </div>
                <Switch
                  checked={settings.show_company_info}
                  onCheckedChange={(checked) => setSettings({ ...settings, show_company_info: checked })}
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Content Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-primary" />
              Contenido
            </CardTitle>
            <CardDescription>Textos predeterminados para documentos</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Vigencia de Cotizaciones (días)</Label>
              <Select
                value={String(settings.quote_validity_days)}
                onValueChange={(value) => setSettings({ ...settings, quote_validity_days: parseInt(value) })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="7">7 días</SelectItem>
                  <SelectItem value="15">15 días</SelectItem>
                  <SelectItem value="30">30 días</SelectItem>
                  <SelectItem value="45">45 días</SelectItem>
                  <SelectItem value="60">60 días</SelectItem>
                  <SelectItem value="90">90 días</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Condiciones de Pago (Facturas)</Label>
              <Textarea
                value={settings.invoice_payment_terms || ""}
                onChange={(e) => setSettings({ ...settings, invoice_payment_terms: e.target.value })}
                placeholder="Ej: Pago a 30 días, transferencia bancaria..."
                rows={2}
              />
            </div>

            <div className="space-y-2">
              <Label>Pie de Página</Label>
              <Textarea
                value={settings.footer_text || ""}
                onChange={(e) => setSettings({ ...settings, footer_text: e.target.value })}
                placeholder="Texto que aparece al final de cada documento"
                rows={2}
              />
            </div>

            <div className="space-y-2">
              <Label>Términos y Condiciones</Label>
              <Textarea
                value={settings.terms_and_conditions || ""}
                onChange={(e) => setSettings({ ...settings, terms_and_conditions: e.target.value })}
                placeholder="Términos legales para cotizaciones..."
                rows={4}
              />
              <p className="text-xs text-muted-foreground">Se incluirán al final de las cotizaciones</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Preview */}
      <Card>
        <CardHeader>
          <CardTitle>Vista Previa</CardTitle>
          <CardDescription>Así se verá el encabezado de tus documentos</CardDescription>
        </CardHeader>
        <CardContent>
          <div 
            className="border rounded-lg p-6 max-w-2xl"
            style={{ borderColor: settings.primary_color }}
          >
            <div 
              className="flex justify-between items-start pb-4 border-b"
              style={{ borderColor: settings.secondary_color }}
            >
              <div>
                {settings.show_logo && (
                  <div 
                    className="w-16 h-16 rounded flex items-center justify-center text-white text-xl font-bold mb-2"
                    style={{ backgroundColor: settings.primary_color }}
                  >
                    LOGO
                  </div>
                )}
                {settings.show_company_info && (
                  <div className="text-sm text-muted-foreground">
                    <p className="font-medium" style={{ color: settings.primary_color }}>Tu Empresa S.A. de C.V.</p>
                    <p>RFC: XXX000000XX0</p>
                    <p>Calle Ejemplo #123</p>
                  </div>
                )}
              </div>
              <div className="text-right">
                <h2 
                  className="text-2xl font-bold"
                  style={{ color: settings.primary_color, fontFamily: settings.font_family }}
                >
                  COTIZACIÓN
                </h2>
                <p className="text-sm text-muted-foreground">COT-2026-001</p>
                <p className="text-sm text-muted-foreground">Fecha: 14/03/2026</p>
              </div>
            </div>
            <div className="pt-4 text-sm text-muted-foreground">
              <p>Vigencia: {settings.quote_validity_days} días</p>
              {settings.footer_text && <p className="mt-2 text-xs italic">{settings.footer_text}</p>}
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-end">
        <Button onClick={handleSave} disabled={saving} className="btn-industrial">
          <Save className="h-4 w-4 mr-2" />
          {saving ? "Guardando..." : "Guardar Configuración"}
        </Button>
      </div>
    </div>
  );
};

export default DocumentSettings;
