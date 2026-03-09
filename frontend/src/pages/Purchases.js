import React, { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { formatCurrency, formatDate, getStatusColor, getStatusLabel, generatePONumber } from "../lib/utils";
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
  ShoppingCart,
  Plus,
  MoreVertical,
  Package,
  Truck,
  CheckCircle,
  Clock,
  Trash2,
} from "lucide-react";

const PO_STATUSES = [
  { value: "requested", label: "Solicitada" },
  { value: "quoted", label: "Cotizada" },
  { value: "approved", label: "Aprobada" },
  { value: "ordered", label: "Ordenada" },
  { value: "received", label: "Recibida" },
  { value: "cancelled", label: "Cancelada" },
];

export const Purchases = () => {
  const { api, company } = useAuth();
  const [purchaseOrders, setPurchaseOrders] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [formData, setFormData] = useState({
    order_number: "",
    project_id: "",
    supplier_id: "",
    description: "",
    subtotal: "",
    tax: "",
    total: "",
  });

  useEffect(() => {
    if (company?.id) {
      fetchData();
    }
  }, [company]);

  const fetchData = async () => {
    try {
      const [posRes, suppliersRes, projectsRes] = await Promise.all([
        api.get(`/purchase-orders?company_id=${company.id}`),
        api.get(`/suppliers?company_id=${company.id}`),
        api.get(`/projects?company_id=${company.id}`),
      ]);
      setPurchaseOrders(posRes.data);
      setSuppliers(suppliersRes.data);
      setProjects(projectsRes.data);
    } catch (error) {
      toast.error("Error al cargar órdenes de compra");
    } finally {
      setLoading(false);
    }
  };

  const calculateFromSubtotal = (subtotal) => {
    const sub = parseFloat(subtotal) || 0;
    const tax = sub * 0.16;
    const total = sub + tax;
    return { tax: tax.toFixed(2), total: total.toFixed(2) };
  };

  const handleSubtotalChange = (value) => {
    const { tax, total } = calculateFromSubtotal(value);
    setFormData({ ...formData, subtotal: value, tax, total });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await api.post("/purchase-orders", {
        company_id: company.id,
        ...formData,
        subtotal: parseFloat(formData.subtotal) || 0,
        tax: parseFloat(formData.tax) || 0,
        total: parseFloat(formData.total) || 0,
      });
      toast.success("Orden de compra creada");
      setDialogOpen(false);
      resetForm();
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al crear orden");
    }
  };

  const handleStatusChange = async (poId, status) => {
    try {
      await api.patch(`/purchase-orders/${poId}/status?status=${status}`);
      toast.success("Estado actualizado");
      fetchData();
    } catch (error) {
      toast.error("Error al actualizar estado");
    }
  };

  const handleDelete = async (poId) => {
    if (!window.confirm("¿Estás seguro de eliminar esta orden?")) return;
    try {
      await api.delete(`/purchase-orders/${poId}`);
      toast.success("Orden eliminada");
      fetchData();
    } catch (error) {
      toast.error("Error al eliminar orden");
    }
  };

  const resetForm = () => {
    setFormData({
      order_number: generatePONumber(),
      project_id: "",
      supplier_id: "",
      description: "",
      subtotal: "",
      tax: "",
      total: "",
    });
  };

  const openNewPODialog = () => {
    resetForm();
    setDialogOpen(true);
  };

  const getSupplierName = (supplierId) => {
    const supplier = suppliers.find((s) => s.id === supplierId);
    return supplier?.name || "N/A";
  };

  const getProjectName = (projectId) => {
    const project = projects.find((p) => p.id === projectId);
    return project?.name || "N/A";
  };

  const stats = {
    total: purchaseOrders.length,
    pending: purchaseOrders.filter((po) => ["requested", "quoted", "approved"].includes(po.status)).length,
    inTransit: purchaseOrders.filter((po) => po.status === "ordered").length,
    received: purchaseOrders.filter((po) => po.status === "received").length,
    totalValue: purchaseOrders.reduce((acc, po) => acc + po.total, 0),
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
    <div className="space-y-6 animate-fade-in" data-testid="purchases-page">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold font-[Chivo] text-slate-900">Control de Compras</h1>
          <p className="text-muted-foreground">Órdenes de compra y seguimiento</p>
        </div>
        <Button className="btn-industrial" onClick={openNewPODialog} data-testid="add-po-btn">
          <Plus className="mr-2 h-4 w-4" />
          Nueva Orden de Compra
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="stat-card">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Órdenes</CardTitle>
            <ShoppingCart className="h-5 w-5 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold font-[Chivo]">{stats.total}</div>
          </CardContent>
        </Card>
        <Card className="stat-card">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Pendientes</CardTitle>
            <Clock className="h-5 w-5 text-amber-500" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold font-[Chivo] text-amber-600">{stats.pending}</div>
          </CardContent>
        </Card>
        <Card className="stat-card">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">En Tránsito</CardTitle>
            <Truck className="h-5 w-5 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold font-[Chivo] text-blue-600">{stats.inTransit}</div>
          </CardContent>
        </Card>
        <Card className="stat-card">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Recibidas</CardTitle>
            <CheckCircle className="h-5 w-5 text-emerald-500" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold font-[Chivo] text-emerald-600">{stats.received}</div>
          </CardContent>
        </Card>
      </div>

      {/* Purchase Orders Table */}
      <Card data-testid="po-table-card">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <ShoppingCart className="h-5 w-5 text-primary" />
            Órdenes de Compra
          </CardTitle>
          <CardDescription>
            Valor total: {formatCurrency(stats.totalValue)}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="rounded-sm border overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow className="bg-slate-50">
                  <TableHead>Folio</TableHead>
                  <TableHead>Proveedor</TableHead>
                  <TableHead>Proyecto</TableHead>
                  <TableHead>Descripción</TableHead>
                  <TableHead>Total</TableHead>
                  <TableHead>Estado</TableHead>
                  <TableHead className="w-[50px]"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {purchaseOrders.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center py-8 text-muted-foreground">
                      No hay órdenes de compra registradas
                    </TableCell>
                  </TableRow>
                ) : (
                  purchaseOrders.map((po) => (
                    <TableRow key={po.id} data-testid={`po-row-${po.id}`}>
                      <TableCell className="font-mono text-sm">{po.order_number}</TableCell>
                      <TableCell>{getSupplierName(po.supplier_id)}</TableCell>
                      <TableCell>{getProjectName(po.project_id)}</TableCell>
                      <TableCell className="max-w-[200px] truncate">{po.description}</TableCell>
                      <TableCell className="font-medium">{formatCurrency(po.total)}</TableCell>
                      <TableCell>
                        <Badge className={getStatusColor(po.status)}>
                          {getStatusLabel(po.status)}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon">
                              <MoreVertical className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            {PO_STATUSES.map((s) => (
                              <DropdownMenuItem
                                key={s.value}
                                onClick={() => handleStatusChange(po.id, s.value)}
                              >
                                {s.label}
                              </DropdownMenuItem>
                            ))}
                            <DropdownMenuSeparator />
                            <DropdownMenuItem
                              onClick={() => handleDelete(po.id)}
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

      {/* Create PO Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <form onSubmit={handleSubmit}>
            <DialogHeader>
              <DialogTitle>Nueva Orden de Compra</DialogTitle>
              <DialogDescription>
                Registra una solicitud de compra
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="grid gap-2">
                  <Label htmlFor="order_number">Folio</Label>
                  <Input
                    id="order_number"
                    value={formData.order_number}
                    onChange={(e) => setFormData({ ...formData, order_number: e.target.value })}
                    required
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="supplier_id">Proveedor</Label>
                  <Select
                    value={formData.supplier_id}
                    onValueChange={(value) => setFormData({ ...formData, supplier_id: value })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Seleccionar" />
                    </SelectTrigger>
                    <SelectContent>
                      {suppliers.map((supplier) => (
                        <SelectItem key={supplier.id} value={supplier.id}>
                          {supplier.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="grid gap-2">
                <Label htmlFor="project_id">Proyecto</Label>
                <Select
                  value={formData.project_id}
                  onValueChange={(value) => setFormData({ ...formData, project_id: value })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Seleccionar proyecto" />
                  </SelectTrigger>
                  <SelectContent>
                    {projects.map((project) => (
                      <SelectItem key={project.id} value={project.id}>
                        {project.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="grid gap-2">
                <Label htmlFor="description">Descripción *</Label>
                <Textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Materiales para proyecto..."
                  required
                  rows={3}
                  data-testid="po-description-input"
                />
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div className="grid gap-2">
                  <Label htmlFor="subtotal">Subtotal</Label>
                  <Input
                    id="subtotal"
                    type="number"
                    value={formData.subtotal}
                    onChange={(e) => handleSubtotalChange(e.target.value)}
                    placeholder="0"
                    data-testid="po-subtotal-input"
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="tax">IVA</Label>
                  <Input id="tax" type="number" value={formData.tax} disabled className="bg-slate-50" />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="total">Total</Label>
                  <Input id="total" type="number" value={formData.total} disabled className="bg-slate-50 font-bold" />
                </div>
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
                Cancelar
              </Button>
              <Button type="submit" className="btn-industrial" data-testid="save-po-btn">
                Crear Orden
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Purchases;
