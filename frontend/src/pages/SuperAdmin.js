import React, { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { formatCurrency, formatDate, getStatusColor, getStatusLabel } from "../lib/utils";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Badge } from "../components/ui/badge";
import { Skeleton } from "../components/ui/skeleton";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
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
  DropdownMenuTrigger,
} from "../components/ui/dropdown-menu";
import { toast } from "sonner";
import {
  Building2,
  Plus,
  MoreVertical,
  CheckCircle,
  XCircle,
  Pause,
  DollarSign,
  Users,
  TrendingUp,
  Crown,
} from "lucide-react";

export const SuperAdmin = () => {
  const { api } = useAuth();
  const [companies, setCompanies] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [formData, setFormData] = useState({
    business_name: "",
    rfc: "",
    address: "",
    phone: "",
    email: "",
    monthly_fee: "",
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [companiesRes, summaryRes] = await Promise.all([
        api.get("/companies"),
        api.get("/super-admin/subscription-summary"),
      ]);
      setCompanies(companiesRes.data);
      setSummary(summaryRes.data);
    } catch (error) {
      toast.error("Error al cargar datos");
    } finally {
      setLoading(false);
    }
  };

  const handleCreateCompany = async (e) => {
    e.preventDefault();
    try {
      await api.post("/companies", {
        ...formData,
        monthly_fee: parseFloat(formData.monthly_fee) || 0,
      });
      toast.success("Empresa creada exitosamente");
      setDialogOpen(false);
      setFormData({
        business_name: "",
        rfc: "",
        address: "",
        phone: "",
        email: "",
        monthly_fee: "",
      });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al crear empresa");
    }
  };

  const handleStatusChange = async (companyId, status) => {
    try {
      await api.patch(`/companies/${companyId}/status?status=${status}`);
      toast.success("Estado actualizado");
      fetchData();
    } catch (error) {
      toast.error("Error al actualizar estado");
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-64" />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
        <Skeleton className="h-96" />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in" data-testid="super-admin-page">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Crown className="h-8 w-8 text-amber-500" />
            <h1 className="text-3xl font-bold font-[Chivo] text-slate-900">Super Administrador</h1>
          </div>
          <p className="text-muted-foreground">Gestión de empresas y suscripciones</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button className="btn-industrial" data-testid="add-company-btn">
              <Plus className="mr-2 h-4 w-4" />
              Nueva Empresa
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[500px]">
            <form onSubmit={handleCreateCompany}>
              <DialogHeader>
                <DialogTitle>Registrar Nueva Empresa</DialogTitle>
                <DialogDescription>
                  Ingresa los datos de la empresa para crear su suscripción
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="grid gap-2">
                  <Label htmlFor="business_name">Razón Social *</Label>
                  <Input
                    id="business_name"
                    value={formData.business_name}
                    onChange={(e) => setFormData({ ...formData, business_name: e.target.value })}
                    placeholder="Empresa S.A. de C.V."
                    required
                    data-testid="company-name-input"
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="rfc">RFC *</Label>
                  <Input
                    id="rfc"
                    value={formData.rfc}
                    onChange={(e) => setFormData({ ...formData, rfc: e.target.value.toUpperCase() })}
                    placeholder="ABC123456XYZ"
                    required
                    data-testid="company-rfc-input"
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="email">Correo Electrónico</Label>
                  <Input
                    id="email"
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    placeholder="contacto@empresa.com"
                    data-testid="company-email-input"
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="phone">Teléfono</Label>
                  <Input
                    id="phone"
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    placeholder="+52 55 1234 5678"
                    data-testid="company-phone-input"
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="address">Dirección</Label>
                  <Input
                    id="address"
                    value={formData.address}
                    onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                    placeholder="Av. Principal 123, Ciudad"
                    data-testid="company-address-input"
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="monthly_fee">Mensualidad (MXN) *</Label>
                  <Input
                    id="monthly_fee"
                    type="number"
                    value={formData.monthly_fee}
                    onChange={(e) => setFormData({ ...formData, monthly_fee: e.target.value })}
                    placeholder="2500"
                    required
                    data-testid="company-fee-input"
                  />
                </div>
              </div>
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
                  Cancelar
                </Button>
                <Button type="submit" className="btn-industrial" data-testid="save-company-btn">
                  Crear Empresa
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="stat-card">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Empresas</CardTitle>
            <Building2 className="h-5 w-5 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold font-[Chivo]">{summary?.total_companies || 0}</div>
          </CardContent>
        </Card>
        <Card className="stat-card">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Activas</CardTitle>
            <CheckCircle className="h-5 w-5 text-emerald-500" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold font-[Chivo] text-emerald-600">{summary?.active || 0}</div>
          </CardContent>
        </Card>
        <Card className="stat-card">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Pendientes</CardTitle>
            <Pause className="h-5 w-5 text-amber-500" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold font-[Chivo] text-amber-600">{summary?.pending || 0}</div>
          </CardContent>
        </Card>
        <Card className="stat-card">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Ingresos Mensuales</CardTitle>
            <DollarSign className="h-5 w-5 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold font-[Chivo]">
              {formatCurrency(summary?.total_monthly_revenue || 0)}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Companies Table */}
      <Card data-testid="companies-table-card">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Building2 className="h-5 w-5 text-primary" />
            Empresas Registradas
          </CardTitle>
          <CardDescription>
            Gestiona las suscripciones y estados de las empresas
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="rounded-sm border overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow className="bg-slate-50">
                  <TableHead>Empresa</TableHead>
                  <TableHead>RFC</TableHead>
                  <TableHead>Contacto</TableHead>
                  <TableHead>Mensualidad</TableHead>
                  <TableHead>Estado</TableHead>
                  <TableHead>Fecha Registro</TableHead>
                  <TableHead className="w-[50px]"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {companies.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center py-8 text-muted-foreground">
                      No hay empresas registradas
                    </TableCell>
                  </TableRow>
                ) : (
                  companies.map((company) => (
                    <TableRow key={company.id} data-testid={`company-row-${company.id}`}>
                      <TableCell>
                        <div>
                          <div className="font-medium">{company.business_name}</div>
                          <div className="text-sm text-muted-foreground">{company.email}</div>
                        </div>
                      </TableCell>
                      <TableCell className="font-mono text-sm">{company.rfc}</TableCell>
                      <TableCell>{company.phone || "-"}</TableCell>
                      <TableCell className="font-medium">
                        {formatCurrency(company.monthly_fee)}
                      </TableCell>
                      <TableCell>
                        <Badge className={getStatusColor(company.subscription_status)}>
                          {getStatusLabel(company.subscription_status)}
                        </Badge>
                      </TableCell>
                      <TableCell>{formatDate(company.created_at)}</TableCell>
                      <TableCell>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon" data-testid={`company-menu-${company.id}`}>
                              <MoreVertical className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem
                              onClick={() => handleStatusChange(company.id, "active")}
                              className="text-emerald-600"
                            >
                              <CheckCircle className="mr-2 h-4 w-4" />
                              Activar
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              onClick={() => handleStatusChange(company.id, "suspended")}
                              className="text-amber-600"
                            >
                              <Pause className="mr-2 h-4 w-4" />
                              Suspender
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              onClick={() => handleStatusChange(company.id, "cancelled")}
                              className="text-red-600"
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

      {/* Payment Reminder */}
      <Card className="border-primary/20 bg-primary/5">
        <CardContent className="flex items-center gap-3 py-4">
          <DollarSign className="h-5 w-5 text-primary" />
          <p className="text-sm text-slate-700">
            <strong>Recordatorio de cobranza:</strong> Las mensualidades deben pagarse dentro de los
            primeros 5 días del mes. Total a cobrar este mes:{" "}
            <strong>{formatCurrency(summary?.total_monthly_revenue || 0)}</strong>
          </p>
        </CardContent>
      </Card>
    </div>
  );
};

export default SuperAdmin;
