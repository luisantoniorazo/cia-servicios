import React, { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { formatCurrency, formatDate } from "../lib/utils";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Badge } from "../components/ui/badge";
import { Skeleton } from "../components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { toast } from "sonner";
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  ShoppingCart,
  FileText,
  Calendar,
  BarChart3,
  PieChart,
  RefreshCw,
} from "lucide-react";

export const ProfitabilityReports = () => {
  const { api, company } = useAuth();
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [dateRange, setDateRange] = useState({
    start_date: "",
    end_date: "",
  });

  useEffect(() => {
    if (company?.id) {
      fetchProfitabilityData();
    }
  }, [company]);

  const fetchProfitabilityData = async () => {
    try {
      setLoading(true);
      let url = "/analytics/profitability";
      const params = new URLSearchParams();
      if (dateRange.start_date) params.append("start_date", dateRange.start_date);
      if (dateRange.end_date) params.append("end_date", dateRange.end_date);
      if (params.toString()) url += `?${params.toString()}`;
      
      const response = await api.get(url);
      setData(response.data);
    } catch (error) {
      console.error("Error fetching profitability:", error);
      toast.error("Error al cargar datos de rentabilidad");
    } finally {
      setLoading(false);
    }
  };

  const handleFilter = () => {
    fetchProfitabilityData();
  };

  const clearFilters = () => {
    setDateRange({ start_date: "", end_date: "" });
    setTimeout(fetchProfitabilityData, 100);
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

  const profitMargin = data?.profitability?.profit_margin || 0;
  const isProfitable = (data?.profitability?.gross_profit || 0) >= 0;

  return (
    <div className="space-y-6 animate-fade-in" data-testid="profitability-reports-page">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold font-[Chivo] text-slate-900">Reportes de Rentabilidad</h1>
          <p className="text-muted-foreground">Análisis de ventas vs compras por período</p>
        </div>
        <Button variant="outline" onClick={fetchProfitabilityData} className="gap-2">
          <RefreshCw className="h-4 w-4" />
          Actualizar
        </Button>
      </div>

      {/* Date Filters */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-lg flex items-center gap-2">
            <Calendar className="h-5 w-5 text-blue-500" />
            Filtrar por Período
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap items-end gap-4">
            <div className="grid gap-2">
              <Label>Fecha Inicio</Label>
              <Input
                type="date"
                value={dateRange.start_date}
                onChange={(e) => setDateRange(prev => ({ ...prev, start_date: e.target.value }))}
                className="w-auto"
              />
            </div>
            <div className="grid gap-2">
              <Label>Fecha Fin</Label>
              <Input
                type="date"
                value={dateRange.end_date}
                onChange={(e) => setDateRange(prev => ({ ...prev, end_date: e.target.value }))}
                className="w-auto"
              />
            </div>
            <Button onClick={handleFilter} className="btn-industrial">
              Aplicar Filtro
            </Button>
            {(dateRange.start_date || dateRange.end_date) && (
              <Button variant="ghost" onClick={clearFilters}>
                Limpiar
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Facturado */}
        <Card className="border-blue-200">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Total Facturado</p>
                <p className="text-2xl font-bold text-blue-700">
                  {formatCurrency(data?.sales?.total_invoiced || 0)}
                </p>
                <p className="text-xs text-muted-foreground">
                  {data?.sales?.invoices_count || 0} facturas
                </p>
              </div>
              <div className="p-3 bg-blue-100 rounded-full">
                <FileText className="h-6 w-6 text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Total Cobrado */}
        <Card className="border-green-200">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Total Cobrado</p>
                <p className="text-2xl font-bold text-green-700">
                  {formatCurrency(data?.sales?.total_collected || 0)}
                </p>
                <p className="text-xs text-muted-foreground">
                  Pendiente: {formatCurrency(data?.sales?.pending_collection || 0)}
                </p>
              </div>
              <div className="p-3 bg-green-100 rounded-full">
                <DollarSign className="h-6 w-6 text-green-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Total Compras */}
        <Card className="border-red-200">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Total Compras</p>
                <p className="text-2xl font-bold text-red-700">
                  {formatCurrency(data?.purchases?.total_purchases || 0)}
                </p>
                <p className="text-xs text-muted-foreground">
                  {data?.purchases?.purchase_orders_count || 0} órdenes
                </p>
              </div>
              <div className="p-3 bg-red-100 rounded-full">
                <ShoppingCart className="h-6 w-6 text-red-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Utilidad Bruta */}
        <Card className={isProfitable ? "border-emerald-200" : "border-orange-200"}>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Utilidad Bruta</p>
                <p className={`text-2xl font-bold ${isProfitable ? "text-emerald-700" : "text-orange-700"}`}>
                  {formatCurrency(data?.profitability?.gross_profit || 0)}
                </p>
                <p className="text-xs text-muted-foreground">
                  Margen: {profitMargin.toFixed(2)}%
                </p>
              </div>
              <div className={`p-3 rounded-full ${isProfitable ? "bg-emerald-100" : "bg-orange-100"}`}>
                {isProfitable ? (
                  <TrendingUp className={`h-6 w-6 ${isProfitable ? "text-emerald-600" : "text-orange-600"}`} />
                ) : (
                  <TrendingDown className="h-6 w-6 text-orange-600" />
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Detailed Analysis */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Sales Breakdown */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-blue-500" />
              Desglose de Ventas
            </CardTitle>
            <CardDescription>Facturación y cobranza del período</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between items-center p-3 bg-blue-50 rounded-lg">
                <span className="text-sm font-medium">Total Facturado</span>
                <span className="text-lg font-bold text-blue-700">
                  {formatCurrency(data?.sales?.total_invoiced || 0)}
                </span>
              </div>
              <div className="flex justify-between items-center p-3 bg-green-50 rounded-lg">
                <span className="text-sm font-medium">Total Cobrado</span>
                <span className="text-lg font-bold text-green-700">
                  {formatCurrency(data?.sales?.total_collected || 0)}
                </span>
              </div>
              <div className="flex justify-between items-center p-3 bg-amber-50 rounded-lg">
                <span className="text-sm font-medium">Pendiente por Cobrar</span>
                <span className="text-lg font-bold text-amber-700">
                  {formatCurrency(data?.sales?.pending_collection || 0)}
                </span>
              </div>
              <div className="pt-2 border-t">
                <div className="text-sm text-muted-foreground">
                  Tasa de cobranza: {((data?.sales?.total_collected || 0) / (data?.sales?.total_invoiced || 1) * 100).toFixed(1)}%
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Profitability Summary */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <PieChart className="h-5 w-5 text-purple-500" />
              Resumen de Rentabilidad
            </CardTitle>
            <CardDescription>Comparación de ingresos vs gastos</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between items-center p-3 bg-slate-50 rounded-lg">
                <span className="text-sm font-medium">Ingresos (Facturado)</span>
                <span className="text-lg font-bold text-slate-700">
                  {formatCurrency(data?.sales?.total_invoiced || 0)}
                </span>
              </div>
              <div className="flex justify-between items-center p-3 bg-slate-50 rounded-lg">
                <span className="text-sm font-medium">Egresos (Compras)</span>
                <span className="text-lg font-bold text-slate-700">
                  {formatCurrency(data?.purchases?.total_purchases || 0)}
                </span>
              </div>
              <div className={`flex justify-between items-center p-3 rounded-lg ${isProfitable ? "bg-emerald-50" : "bg-orange-50"}`}>
                <span className="text-sm font-medium">Utilidad Bruta</span>
                <span className={`text-lg font-bold ${isProfitable ? "text-emerald-700" : "text-orange-700"}`}>
                  {formatCurrency(data?.profitability?.gross_profit || 0)}
                </span>
              </div>
              <div className="pt-2 border-t">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Margen de Utilidad</span>
                  <Badge className={isProfitable ? "bg-emerald-100 text-emerald-700" : "bg-orange-100 text-orange-700"}>
                    {profitMargin.toFixed(2)}%
                  </Badge>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Period Info */}
      {(data?.period?.start_date || data?.period?.end_date) && (
        <Card className="bg-slate-50">
          <CardContent className="py-4">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Calendar className="h-4 w-4" />
              <span>
                Período: {data?.period?.start_date ? formatDate(data.period.start_date) : "Sin límite"} - {data?.period?.end_date ? formatDate(data.period.end_date) : "Sin límite"}
              </span>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default ProfitabilityReports;
