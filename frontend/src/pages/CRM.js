import React, { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { formatCurrency, formatDate, getStatusColor, getStatusLabel } from "../lib/utils";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
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
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "../components/ui/dropdown-menu";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { toast } from "sonner";
import {
  Users,
  Plus,
  MoreVertical,
  Mail,
  Phone,
  Building2,
  UserPlus,
  UserCheck,
  Eye,
  Edit,
  Trash2,
  TrendingUp,
  Percent,
} from "lucide-react";

export const CRM = () => {
  const { api, company } = useAuth();
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingClient, setEditingClient] = useState(null);
  const [activeTab, setActiveTab] = useState("all");
  const [formData, setFormData] = useState({
    name: "",
    contact_name: "",
    email: "",
    phone: "",
    address: "",
    rfc: "",
    is_prospect: true,
    probability: 0,
    notes: "",
  });

  useEffect(() => {
    if (company?.id) {
      fetchClients();
    }
  }, [company]);

  const fetchClients = async () => {
    try {
      const response = await api.get(`/clients?company_id=${company.id}`);
      setClients(response.data);
    } catch (error) {
      toast.error("Error al cargar clientes");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingClient) {
        await api.put(`/clients/${editingClient.id}`, {
          company_id: company.id,
          ...formData,
          probability: parseInt(formData.probability) || 0,
        });
        toast.success("Cliente actualizado");
      } else {
        await api.post("/clients", {
          company_id: company.id,
          ...formData,
          probability: parseInt(formData.probability) || 0,
        });
        toast.success("Cliente creado exitosamente");
      }
      setDialogOpen(false);
      resetForm();
      fetchClients();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al guardar cliente");
    }
  };

  const handleEdit = (client) => {
    setEditingClient(client);
    setFormData({
      name: client.name,
      contact_name: client.contact_name || "",
      email: client.email || "",
      phone: client.phone || "",
      address: client.address || "",
      rfc: client.rfc || "",
      is_prospect: client.is_prospect,
      probability: client.probability || 0,
      notes: client.notes || "",
    });
    setDialogOpen(true);
  };

  const handleDelete = async (clientId) => {
    if (!window.confirm("¿Estás seguro de eliminar este cliente?")) return;
    try {
      await api.delete(`/clients/${clientId}`);
      toast.success("Cliente eliminado");
      fetchClients();
    } catch (error) {
      toast.error("Error al eliminar cliente");
    }
  };

  const handleConvertToClient = async (client) => {
    try {
      await api.put(`/clients/${client.id}`, {
        ...client,
        is_prospect: false,
        probability: 100,
      });
      toast.success("Prospecto convertido a cliente");
      fetchClients();
    } catch (error) {
      toast.error("Error al convertir prospecto");
    }
  };

  const resetForm = () => {
    setEditingClient(null);
    setFormData({
      name: "",
      contact_name: "",
      email: "",
      phone: "",
      address: "",
      rfc: "",
      is_prospect: true,
      probability: 0,
      notes: "",
    });
  };

  const filteredClients = clients.filter((c) => {
    if (activeTab === "prospects") return c.is_prospect;
    if (activeTab === "clients") return !c.is_prospect;
    return true;
  });

  const stats = {
    total: clients.length,
    prospects: clients.filter((c) => c.is_prospect).length,
    clients: clients.filter((c) => !c.is_prospect).length,
    highProbability: clients.filter((c) => c.is_prospect && c.probability >= 60).length,
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
        <Skeleton className="h-96" />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in" data-testid="crm-page">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold font-[Chivo] text-slate-900">CRM Comercial</h1>
          <p className="text-muted-foreground">Gestión de clientes y prospectos</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={(open) => { setDialogOpen(open); if (!open) resetForm(); }}>
          <DialogTrigger asChild>
            <Button className="btn-industrial" data-testid="add-client-btn">
              <Plus className="mr-2 h-4 w-4" />
              Nuevo Cliente/Prospecto
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[500px]">
            <form onSubmit={handleSubmit}>
              <DialogHeader>
                <DialogTitle>{editingClient ? "Editar" : "Nuevo"} Cliente/Prospecto</DialogTitle>
                <DialogDescription>
                  Ingresa los datos del contacto comercial
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="grid gap-2">
                  <Label htmlFor="name">Nombre de la Empresa *</Label>
                  <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="Empresa S.A. de C.V."
                    required
                    data-testid="client-name-input"
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="grid gap-2">
                    <Label htmlFor="contact_name">Nombre de Contacto</Label>
                    <Input
                      id="contact_name"
                      value={formData.contact_name}
                      onChange={(e) => setFormData({ ...formData, contact_name: e.target.value })}
                      placeholder="Juan Pérez"
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="rfc">RFC</Label>
                    <Input
                      id="rfc"
                      value={formData.rfc}
                      onChange={(e) => setFormData({ ...formData, rfc: e.target.value.toUpperCase() })}
                      placeholder="ABC123456XYZ"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="grid gap-2">
                    <Label htmlFor="email">Correo Electrónico</Label>
                    <Input
                      id="email"
                      type="email"
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      placeholder="contacto@empresa.com"
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="phone">Teléfono</Label>
                    <Input
                      id="phone"
                      value={formData.phone}
                      onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                      placeholder="+52 55 1234 5678"
                    />
                  </div>
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="address">Dirección</Label>
                  <Input
                    id="address"
                    value={formData.address}
                    onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                    placeholder="Av. Principal 123, Ciudad"
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="grid gap-2">
                    <Label>Tipo</Label>
                    <Select
                      value={formData.is_prospect ? "prospect" : "client"}
                      onValueChange={(value) => setFormData({ ...formData, is_prospect: value === "prospect" })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="prospect">Prospecto</SelectItem>
                        <SelectItem value="client">Cliente</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  {formData.is_prospect && (
                    <div className="grid gap-2">
                      <Label htmlFor="probability">Probabilidad de Cierre (%)</Label>
                      <Input
                        id="probability"
                        type="number"
                        min="0"
                        max="100"
                        value={formData.probability}
                        onChange={(e) => setFormData({ ...formData, probability: e.target.value })}
                        placeholder="50"
                      />
                    </div>
                  )}
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="notes">Notas</Label>
                  <Textarea
                    id="notes"
                    value={formData.notes}
                    onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                    placeholder="Notas adicionales..."
                    rows={3}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
                  Cancelar
                </Button>
                <Button type="submit" className="btn-industrial" data-testid="save-client-btn">
                  {editingClient ? "Actualizar" : "Crear"}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="stat-card">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Contactos</CardTitle>
            <Users className="h-5 w-5 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold font-[Chivo]">{stats.total}</div>
          </CardContent>
        </Card>
        <Card className="stat-card">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Prospectos</CardTitle>
            <UserPlus className="h-5 w-5 text-amber-500" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold font-[Chivo] text-amber-600">{stats.prospects}</div>
          </CardContent>
        </Card>
        <Card className="stat-card">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Clientes Activos</CardTitle>
            <UserCheck className="h-5 w-5 text-emerald-500" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold font-[Chivo] text-emerald-600">{stats.clients}</div>
          </CardContent>
        </Card>
        <Card className="stat-card">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Alta Probabilidad</CardTitle>
            <TrendingUp className="h-5 w-5 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold font-[Chivo] text-blue-600">{stats.highProbability}</div>
          </CardContent>
        </Card>
      </div>

      {/* Clients Table */}
      <Card data-testid="clients-table-card">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5 text-primary" />
                Directorio Comercial
              </CardTitle>
              <CardDescription>
                {filteredClients.length} contacto(s) encontrado(s)
              </CardDescription>
            </div>
            <Tabs value={activeTab} onValueChange={setActiveTab}>
              <TabsList>
                <TabsTrigger value="all">Todos</TabsTrigger>
                <TabsTrigger value="prospects">Prospectos</TabsTrigger>
                <TabsTrigger value="clients">Clientes</TabsTrigger>
              </TabsList>
            </Tabs>
          </div>
        </CardHeader>
        <CardContent>
          <div className="rounded-sm border overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow className="bg-slate-50">
                  <TableHead>Empresa</TableHead>
                  <TableHead>Contacto</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>Teléfono</TableHead>
                  <TableHead>Tipo</TableHead>
                  <TableHead>Probabilidad</TableHead>
                  <TableHead className="w-[50px]"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredClients.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center py-8 text-muted-foreground">
                      No hay contactos registrados
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredClients.map((client) => (
                    <TableRow key={client.id} data-testid={`client-row-${client.id}`}>
                      <TableCell>
                        <div className="font-medium">{client.name}</div>
                        {client.rfc && (
                          <div className="text-sm text-muted-foreground font-mono">{client.rfc}</div>
                        )}
                      </TableCell>
                      <TableCell>{client.contact_name || "-"}</TableCell>
                      <TableCell>
                        {client.email ? (
                          <a href={`mailto:${client.email}`} className="text-primary hover:underline">
                            {client.email}
                          </a>
                        ) : (
                          "-"
                        )}
                      </TableCell>
                      <TableCell>{client.phone || "-"}</TableCell>
                      <TableCell>
                        <Badge className={client.is_prospect ? "bg-amber-100 text-amber-800" : "bg-emerald-100 text-emerald-800"}>
                          {client.is_prospect ? "Prospecto" : "Cliente"}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {client.is_prospect ? (
                          <div className="flex items-center gap-1">
                            <Percent className="h-3 w-3" />
                            <span className={client.probability >= 60 ? "text-emerald-600 font-medium" : ""}>
                              {client.probability}%
                            </span>
                          </div>
                        ) : (
                          <span className="text-emerald-600">100%</span>
                        )}
                      </TableCell>
                      <TableCell>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon">
                              <MoreVertical className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => handleEdit(client)}>
                              <Edit className="mr-2 h-4 w-4" />
                              Editar
                            </DropdownMenuItem>
                            {client.is_prospect && (
                              <DropdownMenuItem onClick={() => handleConvertToClient(client)}>
                                <UserCheck className="mr-2 h-4 w-4 text-emerald-500" />
                                Convertir a Cliente
                              </DropdownMenuItem>
                            )}
                            <DropdownMenuSeparator />
                            <DropdownMenuItem
                              onClick={() => handleDelete(client.id)}
                              className="text-red-600"
                            >
                              <Trash2 className="mr-2 h-4 w-4" />
                              Eliminar
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
  );
};

export default CRM;
