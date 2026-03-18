import React, { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { formatCurrency, formatDate } from "../lib/utils";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
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
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../components/ui/table";
import { toast } from "sonner";
import {
  Receipt,
  ArrowLeft,
  CheckCircle,
  XCircle,
  Clock,
  Building2,
  FileText,
  Eye,
  RefreshCw,
  Download,
  AlertTriangle,
  Image,
} from "lucide-react";

export const PendingReceipts = () => {
  const { api } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [receipts, setReceipts] = useState([]);
  const [selectedReceipt, setSelectedReceipt] = useState(null);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [rejectDialogOpen, setRejectDialogOpen] = useState(false);
  const [rejectReason, setRejectReason] = useState("");
  const [processing, setProcessing] = useState(false);

  const fetchReceipts = useCallback(async () => {
    try {
      const response = await api.get("/subscriptions/admin/pending-receipts");
      setReceipts(response.data.receipts || []);
    } catch (error) {
      console.error("Error fetching receipts:", error);
      toast.error("Error al cargar comprobantes");
    } finally {
      setLoading(false);
    }
  }, [api]);

  useEffect(() => {
    fetchReceipts();
  }, [fetchReceipts]);

  const handleApprove = async (receipt) => {
    setProcessing(true);
    try {
      await api.post(`/subscriptions/admin/receipts/${receipt.id}/approve`);
      toast.success("Comprobante aprobado y pago registrado");
      fetchReceipts();
      setViewDialogOpen(false);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al aprobar");
    } finally {
      setProcessing(false);
    }
  };

  const handleReject = async () => {
    if (!rejectReason.trim()) {
      toast.error("Ingresa un motivo de rechazo");
      return;
    }
    
    setProcessing(true);
    try {
      await api.post(`/subscriptions/admin/receipts/${selectedReceipt.id}/reject`, {
        reason: rejectReason
      });
      toast.success("Comprobante rechazado");
      setRejectDialogOpen(false);
      setRejectReason("");
      fetchReceipts();
      setViewDialogOpen(false);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al rechazar");
    } finally {
      setProcessing(false);
    }
  };

  const openViewDialog = (receipt) => {
    setSelectedReceipt(receipt);
    setViewDialogOpen(true);
  };

  const getFilePreview = (receipt) => {
    if (!receipt?.file_content) return null;
    
    const isImage = receipt.file_type?.startsWith("image/");
    const isPDF = receipt.file_type === "application/pdf";
    
    if (isImage) {
      return (
        <img 
          src={`data:${receipt.file_type};base64,${receipt.file_content}`}
          alt="Comprobante"
          className="max-w-full max-h-96 rounded-lg border"
        />
      );
    }
    
    if (isPDF) {
      return (
        <div className="bg-slate-100 rounded-lg p-8 text-center">
          <FileText className="h-16 w-16 mx-auto text-slate-400 mb-4" />
          <p className="text-slate-600 mb-4">Archivo PDF: {receipt.file_name}</p>
          <Button
            variant="outline"
            onClick={() => {
              const link = document.createElement('a');
              link.href = `data:application/pdf;base64,${receipt.file_content}`;
              link.download = receipt.file_name || 'comprobante.pdf';
              link.click();
            }}
          >
            <Download className="h-4 w-4 mr-2" />
            Descargar PDF
          </Button>
        </div>
      );
    }
    
    return (
      <div className="bg-slate-100 rounded-lg p-8 text-center">
        <FileText className="h-16 w-16 mx-auto text-slate-400 mb-4" />
        <p className="text-slate-600">Archivo: {receipt.file_name}</p>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="space-y-6 p-6">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-96" />
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6" data-testid="pending-receipts-page">
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
              <Receipt className="h-6 w-6 text-emerald-500" />
              Comprobantes de Pago
            </h1>
            <p className="text-muted-foreground">
              Revisa y aprueba los comprobantes de transferencia
            </p>
          </div>
        </div>
        <Button variant="outline" onClick={fetchReceipts}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Actualizar
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Pendientes de Revisión</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-amber-500">
              {receipts.filter(r => r.status === "pending_review").length}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Monto Total Pendiente</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-emerald-600">
              {formatCurrency(receipts.reduce((sum, r) => sum + (r.invoice_total || 0), 0))}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Empresas</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-blue-500">
              {new Set(receipts.map(r => r.company_id)).size}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Table */}
      <Card>
        <CardHeader>
          <CardTitle>Comprobantes Pendientes</CardTitle>
          <CardDescription>
            Comprobantes de transferencia subidos por los clientes
          </CardDescription>
        </CardHeader>
        <CardContent>
          {receipts.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <CheckCircle className="h-12 w-12 mx-auto mb-4 text-emerald-500 opacity-50" />
              <p className="text-lg font-medium">No hay comprobantes pendientes</p>
              <p className="text-sm">Todos los comprobantes han sido revisados</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Fecha</TableHead>
                  <TableHead>Empresa</TableHead>
                  <TableHead>Factura</TableHead>
                  <TableHead>Referencia</TableHead>
                  <TableHead className="text-right">Monto</TableHead>
                  <TableHead>Estado</TableHead>
                  <TableHead className="text-right">Acciones</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {receipts.map((receipt) => (
                  <TableRow key={receipt.id}>
                    <TableCell>
                      {formatDate(receipt.uploaded_at)}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Building2 className="h-4 w-4 text-muted-foreground" />
                        <span className="font-medium">{receipt.company_name}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <span className="font-mono text-sm">{receipt.invoice_number}</span>
                    </TableCell>
                    <TableCell>
                      {receipt.reference || "-"}
                    </TableCell>
                    <TableCell className="text-right font-bold text-emerald-600">
                      {formatCurrency(receipt.invoice_total)}
                    </TableCell>
                    <TableCell>
                      <Badge variant="warning" className="bg-amber-100 text-amber-700">
                        <Clock className="h-3 w-3 mr-1" />
                        Pendiente
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <Button 
                        size="sm" 
                        onClick={() => openViewDialog(receipt)}
                      >
                        <Eye className="h-4 w-4 mr-1" />
                        Revisar
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* View Receipt Dialog */}
      <Dialog open={viewDialogOpen} onOpenChange={setViewDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Receipt className="h-5 w-5 text-emerald-500" />
              Revisar Comprobante
            </DialogTitle>
            <DialogDescription>
              Verifica que el comprobante corresponda al pago de la factura
            </DialogDescription>
          </DialogHeader>
          
          {selectedReceipt && (
            <div className="space-y-4 py-4">
              {/* Info Cards */}
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-slate-50 rounded-lg p-3">
                  <p className="text-xs text-muted-foreground">Empresa</p>
                  <p className="font-semibold">{selectedReceipt.company_name}</p>
                </div>
                <div className="bg-slate-50 rounded-lg p-3">
                  <p className="text-xs text-muted-foreground">Factura</p>
                  <p className="font-mono font-semibold">{selectedReceipt.invoice_number}</p>
                </div>
                <div className="bg-emerald-50 rounded-lg p-3">
                  <p className="text-xs text-emerald-600">Monto a Verificar</p>
                  <p className="text-xl font-bold text-emerald-700">
                    {formatCurrency(selectedReceipt.invoice_total)}
                  </p>
                </div>
                <div className="bg-slate-50 rounded-lg p-3">
                  <p className="text-xs text-muted-foreground">Referencia del Cliente</p>
                  <p className="font-semibold">{selectedReceipt.reference || "No proporcionada"}</p>
                </div>
              </div>

              {/* Notes */}
              {selectedReceipt.notes && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                  <p className="text-xs text-blue-600 mb-1">Notas del Cliente:</p>
                  <p className="text-sm text-blue-800">{selectedReceipt.notes}</p>
                </div>
              )}

              {/* File Preview */}
              <div className="border rounded-lg p-4">
                <p className="text-sm font-medium mb-3 flex items-center gap-2">
                  <Image className="h-4 w-4" />
                  Comprobante Adjunto
                </p>
                {getFilePreview(selectedReceipt)}
              </div>

              {/* Warning */}
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 flex items-start gap-2">
                <AlertTriangle className="h-5 w-5 text-amber-500 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-amber-800">Antes de aprobar:</p>
                  <ul className="text-xs text-amber-700 mt-1 space-y-1">
                    <li>• Verifica que el monto coincida con {formatCurrency(selectedReceipt.invoice_total)}</li>
                    <li>• Confirma que la transferencia aparece en tu estado de cuenta</li>
                    <li>• Verifica la fecha de la transacción</li>
                  </ul>
                </div>
              </div>
            </div>
          )}

          <DialogFooter className="flex gap-2">
            <Button 
              variant="outline" 
              onClick={() => {
                setSelectedReceipt(selectedReceipt);
                setRejectDialogOpen(true);
              }}
              disabled={processing}
            >
              <XCircle className="h-4 w-4 mr-2" />
              Rechazar
            </Button>
            <Button 
              onClick={() => handleApprove(selectedReceipt)}
              disabled={processing}
              className="bg-emerald-600 hover:bg-emerald-700"
            >
              {processing ? (
                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <CheckCircle className="h-4 w-4 mr-2" />
              )}
              Aprobar y Registrar Pago
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Reject Dialog */}
      <Dialog open={rejectDialogOpen} onOpenChange={setRejectDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-red-600">
              <XCircle className="h-5 w-5" />
              Rechazar Comprobante
            </DialogTitle>
            <DialogDescription>
              El cliente será notificado y podrá subir un nuevo comprobante
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="reject-reason">Motivo del rechazo *</Label>
              <Textarea
                id="reject-reason"
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                placeholder="Ej: El monto no coincide, imagen ilegible, etc."
                rows={3}
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setRejectDialogOpen(false)}>
              Cancelar
            </Button>
            <Button 
              variant="destructive"
              onClick={handleReject}
              disabled={processing || !rejectReason.trim()}
            >
              {processing ? (
                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <XCircle className="h-4 w-4 mr-2" />
              )}
              Rechazar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default PendingReceipts;
