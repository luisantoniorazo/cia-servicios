import React, { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { formatCurrency, formatDate, getStatusColor, getStatusLabel, generateInvoiceNumber, getApiErrorMessage } from "../lib/utils";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Badge } from "../components/ui/badge";
import { Skeleton } from "../components/ui/skeleton";
import { Progress } from "../components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { Textarea } from "../components/ui/textarea";
import { SATProductSearch, SATUnitSearch } from "../components/SATSearch";
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
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "../components/ui/dropdown-menu";
import { toast } from "sonner";
import {
  Receipt,
  Plus,
  PlusCircle,
  MinusCircle,
  MoreVertical,
  DollarSign,
  CheckCircle,
  Clock,
  AlertTriangle,
  CreditCard,
  Trash2,
  Download,
  Upload,
  FileText,
  User,
  Calendar,
  Eye,
  Search,
  X,
  Stamp,
  FileCode,
  Loader2,
} from "lucide-react";

const PAYMENT_METHODS = [
  { value: "transferencia", label: "Transferencia Bancaria" },
  { value: "efectivo", label: "Efectivo" },
  { value: "cheque", label: "Cheque" },
  { value: "tarjeta", label: "Tarjeta" },
];

// Catálogo SAT c_FormaPago para CFDI
const SAT_FORMAS_PAGO = [
  { value: "01", label: "01 - Efectivo" },
  { value: "02", label: "02 - Cheque nominativo" },
  { value: "03", label: "03 - Transferencia electrónica de fondos" },
  { value: "04", label: "04 - Tarjeta de crédito" },
  { value: "05", label: "05 - Monedero electrónico" },
  { value: "06", label: "06 - Dinero electrónico" },
  { value: "08", label: "08 - Vales de despensa" },
  { value: "12", label: "12 - Dación en pago" },
  { value: "13", label: "13 - Pago por subrogación" },
  { value: "14", label: "14 - Pago por consignación" },
  { value: "15", label: "15 - Condonación" },
  { value: "17", label: "17 - Compensación" },
  { value: "23", label: "23 - Novación" },
  { value: "24", label: "24 - Confusión" },
  { value: "25", label: "25 - Remisión de deuda" },
  { value: "26", label: "26 - Prescripción o caducidad" },
  { value: "27", label: "27 - A satisfacción del acreedor" },
  { value: "28", label: "28 - Tarjeta de débito" },
  { value: "29", label: "29 - Tarjeta de servicios" },
  { value: "30", label: "30 - Aplicación de anticipos" },
  { value: "31", label: "31 - Intermediario pagos" },
  { value: "99", label: "99 - Por definir" },
];

const MONEDAS = [
  { value: "MXN", label: "MXN - Peso Mexicano" },
  { value: "USD", label: "USD - Dólar Americano" },
  { value: "EUR", label: "EUR - Euro" },
];

const PAYMENT_TERMS_OPTIONS = [
  { value: "contado", label: "Contado" },
  { value: "15_dias", label: "15 días" },
  { value: "30_dias", label: "30 días" },
  { value: "45_dias", label: "45 días" },
  { value: "60_dias", label: "60 días" },
  { value: "90_dias", label: "90 días" },
];

export const Invoices = () => {
  const { api, company } = useAuth();
  const [invoices, setInvoices] = useState([]);
  const [clients, setClients] = useState([]);
  const [projects, setProjects] = useState([]);
  const [payments, setPayments] = useState([]);
  const [overdueData, setOverdueData] = useState({ overdue: [], upcoming: [] });
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [paymentDialogOpen, setPaymentDialogOpen] = useState(false);
  const [statementDialogOpen, setStatementDialogOpen] = useState(false);
  const [creditNoteDialogOpen, setCreditNoteDialogOpen] = useState(false);
  const [cfdiDialogOpen, setCfdiDialogOpen] = useState(false);
  const [selectedInvoice, setSelectedInvoice] = useState(null);
  const [selectedClient, setSelectedClient] = useState(null);
  const [clientStatement, setClientStatement] = useState(null);
  const [activeTab, setActiveTab] = useState("all");
  const [creditNotes, setCreditNotes] = useState([]);
  const [motivosNC, setMotivosNC] = useState([]);
  const [billingStatus, setBillingStatus] = useState(null);
  const [stamping, setStamping] = useState(false);
  const [cfdiForm, setCfdiForm] = useState({
    xml_file: null,
    pdf_file: null,
  });
  
  const [formData, setFormData] = useState({
    client_id: "",
    project_id: "",
    invoice_number: "",
    reference: "",  // OC Cliente / Orden de Trabajo
    payment_terms: "contado",
    forma_pago: "99",  // SAT c_FormaPago - default: Por definir
    items: [{ description: "", quantity: 1, unit: "pza", unit_price: 0, total: 0, clave_prod_serv: "", clave_unidad: "" }],
    subtotal: 0,
    tax: 0,
    total: 0,
    invoice_date: new Date().toISOString().split("T")[0],
    due_date: "",
    custom_field: "",
    custom_field_label: "",
  });
  
  const [paymentForm, setPaymentForm] = useState({
    // Datos básicos del pago
    amount: "",
    payment_date: new Date().toISOString().split("T")[0],
    payment_method: "transferencia",
    reference: "",
    notes: "",
    proof_file: null,
    // Datos SAT para complemento de pago CFDI
    sat_forma_pago: "03", // Default: Transferencia electrónica
    moneda_pago: "MXN",
    tipo_cambio: "1",
    num_operacion: "",
    // Datos bancarios ordenante (quien paga)
    rfc_banco_ordenante: "",
    nombre_banco_ordenante: "",
    cuenta_ordenante: "",
    // Datos bancarios beneficiario (quien recibe)
    rfc_banco_beneficiario: "",
    cuenta_beneficiaria: "",
    // Control de parcialidades
    num_parcialidad: "1",
  });
  
  const [creditNoteForm, setCreditNoteForm] = useState({
    invoice_id: "",
    credit_note_number: "",
    issue_date: new Date().toISOString().split("T")[0],
    concept: "",
    reason: "",
    items: [{ description: "", quantity: 1, unit: "pza", unit_price: 0, total: 0, clave_prod_serv: "", clave_unidad: "" }],
    subtotal: 0,
    tax: 0,
    total: 0,
    sat_tipo_relacion: "01",
    status: "applied",
  });
  
  const [searchFilter, setSearchFilter] = useState("");

  // Filter invoices based on search
  const getFilteredInvoices = (invoiceList) => {
    if (!searchFilter) return invoiceList;
    const search = searchFilter.toLowerCase();
    return invoiceList.filter((inv) => {
      const clientName = getClientName(inv.client_id)?.toLowerCase() || "";
      const projectName = getProjectName(inv.project_id)?.toLowerCase() || "";
      return (
        inv.invoice_number?.toLowerCase().includes(search) ||
        inv.concept?.toLowerCase().includes(search) ||
        clientName.includes(search) ||
        projectName.includes(search) ||
        inv.sat_uuid?.toLowerCase().includes(search) ||
        formatCurrency(inv.total).includes(search)
      );
    });
  };

  useEffect(() => {
    if (company?.id) {
      fetchData();
    }
  }, [company]);

  const fetchData = async () => {
    try {
      const [invoicesRes, clientsRes, projectsRes, paymentsRes, overdueRes, creditNotesRes, motivosRes, billingRes] = await Promise.all([
        api.get(`/invoices?company_id=${company.id}`),
        api.get(`/clients?company_id=${company.id}`),
        api.get(`/projects?company_id=${company.id}`),
        api.get(`/payments?company_id=${company.id}`),
        api.get(`/invoices/overdue?company_id=${company.id}`),
        api.get(`/credit-notes?company_id=${company.id}`),
        api.get(`/sat/motivos-nota-credito`),
        api.get(`/company/billing-status`).catch(() => ({ data: null })),
      ]);
      setInvoices(invoicesRes.data);
      setClients(clientsRes.data);
      setProjects(projectsRes.data);
      setPayments(paymentsRes.data);
      setOverdueData(overdueRes.data);
      setCreditNotes(creditNotesRes.data);
      setMotivosNC(motivosRes.data);
      setBillingStatus(billingRes.data);
    } catch (error) {
      toast.error("Error al cargar datos");
    } finally {
      setLoading(false);
    }
  };

  const calculateTotals = (items) => {
    const subtotal = items.reduce((acc, item) => acc + (item.quantity * item.unit_price), 0);
    const tax = subtotal * 0.16;
    const total = subtotal + tax;
    return { subtotal, tax, total };
  };

  const handleItemChange = (index, field, value) => {
    const newItems = [...formData.items];
    newItems[index][field] = value;
    if (field === "quantity" || field === "unit_price") {
      newItems[index].total = newItems[index].quantity * newItems[index].unit_price;
    }
    const { subtotal, tax, total } = calculateTotals(newItems);
    setFormData({ ...formData, items: newItems, subtotal, tax, total });
  };

  const addItem = () => {
    setFormData({
      ...formData,
      items: [...formData.items, { description: "", quantity: 1, unit: "pza", unit_price: 0, total: 0, clave_prod_serv: "", clave_unidad: "" }],
    });
  };

  const removeItem = (index) => {
    if (formData.items.length === 1) return;
    const newItems = formData.items.filter((_, i) => i !== index);
    const { subtotal, tax, total } = calculateTotals(newItems);
    setFormData({ ...formData, items: newItems, subtotal, tax, total });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const { subtotal, tax, total } = calculateTotals(formData.items);
      const concept = formData.items.map(i => i.description).filter(Boolean).join(", ") || "Factura";
      
      const invoicePayload = {
        company_id: company.id,
        ...formData,
        concept,
        subtotal,
        tax,
        total,
        invoice_date: formData.invoice_date || new Date().toISOString().split("T")[0],
        due_date: formData.due_date || null,
      };
      
      let response;
      if (selectedInvoice) {
        // Editing existing invoice
        response = await api.put(`/invoices/${selectedInvoice.id}`, invoicePayload);
        toast.success("Factura actualizada");
      } else {
        // Creating new invoice
        response = await api.post("/invoices", invoicePayload);
        toast.success("Factura registrada");
        
        // Send email notification only for new invoices
        const client = clients.find(c => c.id === formData.client_id);
        if (client?.email) {
          try {
            await api.post("/send-document-email", {
              company_id: company.id,
              document_type: "invoice",
              document_id: response.data.id,
              recipient_email: client.email,
              recipient_name: client.trade_name || client.name,
            });
          } catch (emailError) {
            console.log("Email notification failed:", emailError);
          }
        }
      }
      
      setDialogOpen(false);
      resetForm();
      setSelectedInvoice(null);
      fetchData();
    } catch (error) {
      toast.error(getApiErrorMessage(error, selectedInvoice ? "Error al actualizar factura" : "Error al registrar factura"));
    }
  };

  // Credit Note Functions
  const handleCreditNoteItemChange = (index, field, value) => {
    const newItems = [...creditNoteForm.items];
    newItems[index][field] = value;
    if (field === "quantity" || field === "unit_price") {
      newItems[index].total = newItems[index].quantity * newItems[index].unit_price;
    }
    const { subtotal, tax, total } = calculateTotals(newItems);
    setCreditNoteForm({ ...creditNoteForm, items: newItems, subtotal, tax, total });
  };

  const addCreditNoteItem = () => {
    setCreditNoteForm({
      ...creditNoteForm,
      items: [...creditNoteForm.items, { description: "", quantity: 1, unit: "pza", unit_price: 0, total: 0, clave_prod_serv: "", clave_unidad: "" }],
    });
  };

  const removeCreditNoteItem = (index) => {
    if (creditNoteForm.items.length === 1) return;
    const newItems = creditNoteForm.items.filter((_, i) => i !== index);
    const { subtotal, tax, total } = calculateTotals(newItems);
    setCreditNoteForm({ ...creditNoteForm, items: newItems, subtotal, tax, total });
  };

  const openCreditNoteDialog = (invoice) => {
    setSelectedInvoice(invoice);
    const ncNumber = `NC-${new Date().getFullYear()}-${String(creditNotes.length + 1).padStart(3, '0')}`;
    const saldoPendiente = (invoice.total || 0) - (invoice.paid_amount || 0);
    
    setCreditNoteForm({
      invoice_id: invoice.id,
      credit_note_number: ncNumber,
      issue_date: new Date().toISOString().split("T")[0],
      concept: `Nota de crédito para factura ${invoice.invoice_number}`,
      reason: "",
      items: [{ 
        description: invoice.concept || "Ajuste según factura original", 
        quantity: 1, 
        unit: "pza", 
        unit_price: saldoPendiente, 
        total: saldoPendiente, 
        clave_prod_serv: "", 
        clave_unidad: "ACT" 
      }],
      subtotal: saldoPendiente / 1.16,
      tax: (saldoPendiente / 1.16) * 0.16,
      total: saldoPendiente,
      sat_tipo_relacion: "01",
      status: "applied",
    });
    setCreditNoteDialogOpen(true);
  };

  const handleCreditNoteSubmit = async (e) => {
    e.preventDefault();
    if (!selectedInvoice) return;
    
    try {
      const client = clients.find(c => c.id === selectedInvoice.client_id);
      const concept = creditNoteForm.items.map(i => i.description).filter(Boolean).join(", ") || "Nota de crédito";
      
      await api.post("/credit-notes", {
        company_id: company.id,
        client_id: selectedInvoice.client_id,
        invoice_id: selectedInvoice.id,
        credit_note_number: creditNoteForm.credit_note_number,
        issue_date: creditNoteForm.issue_date,
        concept,
        reason: creditNoteForm.reason,
        items: creditNoteForm.items,
        subtotal: creditNoteForm.subtotal,
        tax: creditNoteForm.tax,
        total: creditNoteForm.total,
        sat_tipo_relacion: creditNoteForm.sat_tipo_relacion,
        sat_uuid_relacionado: selectedInvoice.sat_invoice_uuid || null,
        status: creditNoteForm.status,
      });
      
      toast.success("Nota de crédito registrada y aplicada");
      setCreditNoteDialogOpen(false);
      fetchData();
      
      // Send email notification
      if (client?.email) {
        try {
          await api.post("/send-document-email", {
            company_id: company.id,
            document_type: "credit_note",
            document_id: creditNoteForm.credit_note_number,
            recipient_email: client.email,
            recipient_name: client.name,
          });
        } catch (emailError) {
          console.log("Email notification failed:", emailError);
        }
      }
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Error al registrar nota de crédito"));
    }
  };

  const handlePayment = async (e) => {
    e.preventDefault();
    if (!selectedInvoice) return;
    
    try {
      let proofBase64 = null;
      if (paymentForm.proof_file) {
        proofBase64 = await fileToBase64(paymentForm.proof_file);
      }
      
      // Calcular saldo anterior e insoluto
      const saldoAnterior = (selectedInvoice.total || 0) - (selectedInvoice.paid_amount || 0);
      const saldoInsoluto = saldoAnterior - parseFloat(paymentForm.amount);
      
      await api.post("/payments", {
        company_id: company.id,
        invoice_id: selectedInvoice.id,
        client_id: selectedInvoice.client_id,
        amount: parseFloat(paymentForm.amount),
        payment_date: paymentForm.payment_date,
        payment_method: paymentForm.payment_method,
        reference: paymentForm.reference,
        notes: paymentForm.notes,
        proof_file: proofBase64,
        // Datos SAT para Complemento de Pago
        sat_forma_pago: paymentForm.sat_forma_pago,
        moneda_pago: paymentForm.moneda_pago,
        tipo_cambio: parseFloat(paymentForm.tipo_cambio) || 1,
        num_operacion: paymentForm.num_operacion,
        rfc_banco_ordenante: paymentForm.rfc_banco_ordenante,
        nombre_banco_ordenante: paymentForm.nombre_banco_ordenante,
        cuenta_ordenante: paymentForm.cuenta_ordenante,
        rfc_banco_beneficiario: paymentForm.rfc_banco_beneficiario,
        cuenta_beneficiaria: paymentForm.cuenta_beneficiaria,
        num_parcialidad: parseInt(paymentForm.num_parcialidad) || 1,
        saldo_anterior: saldoAnterior,
        saldo_insoluto: Math.max(0, saldoInsoluto),
      });
      
      toast.success("Abono registrado exitosamente");
      setPaymentDialogOpen(false);
      resetPaymentForm();
      fetchData();
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Error al registrar abono"));
    }
  };

  const handleViewStatement = async (clientId) => {
    try {
      const response = await api.get(`/clients/${clientId}/statement`);
      setClientStatement(response.data);
      setStatementDialogOpen(true);
    } catch (error) {
      toast.error("Error al cargar estado de cuenta");
    }
  };

  const handleDelete = async (invoiceId) => {
    if (!window.confirm("¿Estás seguro de eliminar esta factura?")) return;
    try {
      await api.delete(`/invoices/${invoiceId}`);
      toast.success("Factura eliminada");
      fetchData();
    } catch (error) {
      toast.error("Error al eliminar factura");
    }
  };

  const handleDownloadPDF = async (invoiceId) => {
    try {
      toast.info("Generando PDF...");
      const response = await api.get(`/pdf/invoice/${invoiceId}`);
      const { filename, content } = response.data;
      
      const byteCharacters = atob(content);
      const byteNumbers = new Array(byteCharacters.length);
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
      }
      const byteArray = new Uint8Array(byteNumbers);
      const blob = new Blob([byteArray], { type: 'application/pdf' });
      
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      toast.success("PDF descargado");
    } catch (error) {
      toast.error("Error al generar PDF");
    }
  };

  const handleDownloadStatementPDF = async (clientId) => {
    try {
      toast.info("Generando estado de cuenta PDF...");
      const response = await api.get(`/clients/${clientId}/statement/pdf`);
      const { filename, content } = response.data;
      
      const byteCharacters = atob(content);
      const byteNumbers = new Array(byteCharacters.length);
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
      }
      const byteArray = new Uint8Array(byteNumbers);
      const blob = new Blob([byteArray], { type: 'application/pdf' });
      
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      toast.success("Estado de cuenta descargado");
    } catch (error) {
      toast.error("Error al generar estado de cuenta PDF");
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

  const resetForm = () => {
    setFormData({
      client_id: "",
      project_id: "",
      invoice_number: generateInvoiceNumber(),
      reference: "",
      payment_terms: "contado",
      items: [{ description: "", quantity: 1, unit: "pza", unit_price: 0, total: 0, clave_prod_serv: "", clave_unidad: "" }],
      subtotal: 0,
      tax: 0,
      total: 0,
      invoice_date: new Date().toISOString().split("T")[0],
      due_date: "",
      custom_field: "",
      custom_field_label: "",
    });
  };

  const resetPaymentForm = () => {
    setPaymentForm({
      amount: "",
      payment_date: new Date().toISOString().split("T")[0],
      payment_method: "transferencia",
      reference: "",
      notes: "",
      proof_file: null,
    });
    setSelectedInvoice(null);
  };

  const openNewInvoiceDialog = () => {
    resetForm();
    setFormData((prev) => ({ ...prev, invoice_number: generateInvoiceNumber() }));
    setDialogOpen(true);
  };

  const openEditInvoiceDialog = (invoice) => {
    // Check if invoice is already stamped
    if (invoice.cfdi_status === "stamped") {
      toast.error("No se puede editar una factura ya timbrada");
      return;
    }
    
    setSelectedInvoice(invoice);
    setFormData({
      client_id: invoice.client_id || "",
      project_id: invoice.project_id || "",
      invoice_number: invoice.invoice_number || "",
      reference: invoice.reference || "",
      payment_terms: invoice.payment_terms || "contado",
      forma_pago: invoice.forma_pago || "99",
      items: invoice.items && invoice.items.length > 0 
        ? invoice.items 
        : [{ description: "", quantity: 1, unit: "pza", unit_price: 0, total: 0, clave_prod_serv: "", clave_unidad: "" }],
      subtotal: invoice.subtotal || 0,
      tax: invoice.tax || 0,
      total: invoice.total || 0,
      invoice_date: invoice.invoice_date ? invoice.invoice_date.split("T")[0] : new Date().toISOString().split("T")[0],
      due_date: invoice.due_date ? invoice.due_date.split("T")[0] : "",
      custom_field: invoice.custom_field || "",
      custom_field_label: invoice.custom_field_label || "",
    });
    setDialogOpen(true);
  };

  const openPaymentDialog = (invoice) => {
    setSelectedInvoice(invoice);
    
    // Calcular número de parcialidad automáticamente
    // Contar pagos existentes para esta factura
    const pagosFactura = payments.filter(p => p.invoice_id === invoice.id);
    const numParcialidad = pagosFactura.length + 1;
    
    setPaymentForm(prev => ({
      ...prev,
      amount: (invoice.total - invoice.paid_amount).toFixed(2),
      num_parcialidad: numParcialidad.toString(),
      // Resetear otros campos
      payment_date: new Date().toISOString().split("T")[0],
      sat_forma_pago: "03",
      moneda_pago: "MXN",
      tipo_cambio: "1",
      num_operacion: "",
      rfc_banco_ordenante: "",
      nombre_banco_ordenante: "",
      cuenta_ordenante: "",
      rfc_banco_beneficiario: "",
      cuenta_beneficiaria: "",
      reference: "",
      notes: "",
      proof_file: null,
    }));
    setPaymentDialogOpen(true);
  };

  // openSatDialog removed - SAT upload will be handled through Facturama integration

  const getClientName = (clientId) => {
    const client = clients.find((c) => c.id === clientId);
    if (!client) return "N/A";
    const displayName = client.trade_name || client.name;
    return client.reference ? `${displayName} (${client.reference})` : displayName;
  };

  const stats = {
    total: invoices.reduce((acc, inv) => acc + inv.total, 0),
    collected: invoices.reduce((acc, inv) => acc + inv.paid_amount, 0),
    pending: invoices.reduce((acc, inv) => acc + (inv.total - inv.paid_amount), 0),
    overdue: overdueData.overdue?.length || 0,
  };

  // ===== CFDI FUNCTIONS =====
  const handleStampInvoice = async (invoiceId) => {
    if (!billingStatus?.can_stamp) {
      toast.error(billingStatus?.message || "No puedes timbrar facturas");
      return;
    }
    
    try {
      setStamping(true);
      const response = await api.post(`/invoices/${invoiceId}/stamp`);
      if (response.data.success) {
        toast.success("Factura timbrada exitosamente");
        fetchData();
      } else {
        toast.error(response.data.message || "Error al timbrar");
      }
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Error al timbrar factura"));
    } finally {
      setStamping(false);
    }
  };

  const handleDownloadXML = async (invoiceId) => {
    try {
      const response = await api.get(`/invoices/${invoiceId}/cfdi/xml`);
      if (response.data.content) {
        const blob = new Blob([atob(response.data.content)], { type: 'application/xml' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = response.data.filename || 'cfdi.xml';
        a.click();
        window.URL.revokeObjectURL(url);
      }
    } catch (error) {
      toast.error("Error al descargar XML");
    }
  };

  const handleDownloadCFDIPDF = async (invoiceId) => {
    try {
      const response = await api.get(`/invoices/${invoiceId}/cfdi/pdf`);
      if (response.data.content) {
        const blob = new Blob([Uint8Array.from(atob(response.data.content), c => c.charCodeAt(0))], { type: 'application/pdf' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = response.data.filename || 'cfdi.pdf';
        a.click();
        window.URL.revokeObjectURL(url);
      }
    } catch (error) {
      toast.error("Error al descargar PDF del CFDI");
    }
  };

  const handleCancelCFDI = async (invoiceId) => {
    if (!window.confirm("¿Estás seguro de cancelar este CFDI? Esta acción puede tener implicaciones fiscales.")) {
      return;
    }
    
    try {
      const response = await api.post(`/invoices/${invoiceId}/cancel-cfdi`);
      if (response.data.success) {
        toast.success("CFDI cancelado");
        fetchData();
      } else {
        toast.error(response.data.message || "Error al cancelar");
      }
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Error al cancelar CFDI"));
    }
  };

  const openCfdiDialog = (invoice) => {
    setSelectedInvoice(invoice);
    setCfdiForm({ xml_file: null, pdf_file: null });
    setCfdiDialogOpen(true);
  };

  const handleUploadManualCFDI = async (e) => {
    e.preventDefault();
    
    // Validar que ambos archivos estén presentes
    if (!cfdiForm.xml_file) {
      toast.error("El archivo XML es obligatorio");
      return;
    }
    if (!cfdiForm.pdf_file) {
      toast.error("El archivo PDF es obligatorio");
      return;
    }
    
    try {
      const xmlContent = await fileToBase64(cfdiForm.xml_file);
      const pdfContent = await fileToBase64(cfdiForm.pdf_file);
      
      await api.post(`/invoices/${selectedInvoice.id}/upload-cfdi`, {
        xml_content: xmlContent,
        pdf_content: pdfContent,
      });
      
      toast.success("CFDI vinculado correctamente. UUID extraído del XML.");
      setCfdiDialogOpen(false);
      fetchData();
    } catch (error) {
      toast.error(getApiErrorMessage(error, "Error al subir CFDI"));
    }
  };

  const baseFilteredInvoices = activeTab === "all" 
    ? invoices 
    : activeTab === "overdue"
    ? overdueData.overdue
    : activeTab === "upcoming"
    ? overdueData.upcoming
    : invoices.filter(inv => inv.status === activeTab);
  
  const filteredInvoices = getFilteredInvoices(baseFilteredInvoices);

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => <Skeleton key={i} className="h-24" />)}
        </div>
        <Skeleton className="h-96" />
      </div>
    );
  }

  return (
    <div className="space-y-4 sm:space-y-6 animate-fade-in" data-testid="invoices-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 sm:gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl lg:text-3xl font-bold font-[Chivo] text-slate-900">Control de Facturación</h1>
          <p className="text-sm sm:text-base text-muted-foreground">Gestión de facturas y cobranza</p>
        </div>
        <Button className="btn-industrial" size="sm" onClick={openNewInvoiceDialog} data-testid="new-invoice-btn">
          <Plus className="mr-1 sm:mr-2 h-4 w-4" />
          Nueva Factura
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-2 sm:gap-4">
        <Card>
          <CardContent className="p-3 sm:p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs sm:text-sm text-muted-foreground">Facturado</p>
                <p className="text-lg sm:text-2xl font-bold">{formatCurrency(stats.total)}</p>
              </div>
              <Receipt className="h-6 w-6 sm:h-8 sm:w-8 text-primary/50" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-3 sm:p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs sm:text-sm text-muted-foreground">Cobrado</p>
                <p className="text-lg sm:text-2xl font-bold text-emerald-600">{formatCurrency(stats.collected)}</p>
              </div>
              <CheckCircle className="h-6 w-6 sm:h-8 sm:w-8 text-emerald-500/50" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-3 sm:p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs sm:text-sm text-muted-foreground">Por Cobrar</p>
                <p className="text-lg sm:text-2xl font-bold text-amber-600">{formatCurrency(stats.pending)}</p>
              </div>
              <Clock className="h-6 w-6 sm:h-8 sm:w-8 text-amber-500/50" />
            </div>
            <Progress value={(stats.collected / stats.total) * 100 || 0} className="mt-2" />
          </CardContent>
        </Card>
        <Card className={stats.overdue > 0 ? "border-red-200 bg-red-50" : ""}>
          <CardContent className="p-3 sm:p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs sm:text-sm text-muted-foreground">Vencidas</p>
                <p className={`text-lg sm:text-2xl font-bold ${stats.overdue > 0 ? "text-red-600" : ""}`}>
                  {stats.overdue}
                </p>
              </div>
              <AlertTriangle className={`h-6 w-6 sm:h-8 sm:w-8 ${stats.overdue > 0 ? "text-red-500" : "text-slate-300"}`} />
            </div>
            {overdueData.total_overdue_amount > 0 && (
              <p className="text-xs text-red-600 mt-1">
                {formatCurrency(overdueData.total_overdue_amount)}
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Overdue Alert */}
      {overdueData.overdue?.length > 0 && (
        <Card className="border-red-300 bg-red-50">
          <CardContent className="p-3 sm:p-4">
            <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-3">
              <AlertTriangle className="h-5 w-5 text-red-600 hidden sm:block" />
              <div className="flex-1">
                <p className="font-semibold text-red-800 text-sm sm:text-base">¡Facturas Vencidas!</p>
                <p className="text-xs sm:text-sm text-red-700">
                  {overdueData.overdue.length} factura(s) - {formatCurrency(overdueData.total_overdue_amount)}
                </p>
              </div>
              <Button 
                variant="outline" 
                size="sm"
                className="border-red-300 text-red-700 hover:bg-red-100 text-xs sm:text-sm"
                onClick={() => setActiveTab("overdue")}
              >
                Ver Vencidas
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="w-full sm:w-auto overflow-x-auto flex-nowrap">
          <TabsTrigger value="all" className="text-xs sm:text-sm">Todas ({invoices.length})</TabsTrigger>
          <TabsTrigger value="pending" className="text-xs sm:text-sm">Pendientes</TabsTrigger>
          <TabsTrigger value="partial" className="text-xs sm:text-sm">Parciales</TabsTrigger>
          <TabsTrigger value="paid" className="text-xs sm:text-sm">Pagadas</TabsTrigger>
          <TabsTrigger value="overdue" className="text-red-600">
            Vencidas ({overdueData.overdue?.length || 0})
          </TabsTrigger>
          <TabsTrigger value="upcoming" className="text-amber-600">
            Próx. Vencer ({overdueData.upcoming?.length || 0})
          </TabsTrigger>
          <TabsTrigger value="credit_notes" className="text-violet-600 text-xs sm:text-sm">
            N. Crédito ({creditNotes.length})
          </TabsTrigger>
          <TabsTrigger value="payments" className="text-emerald-600 text-xs sm:text-sm">
            Pagos ({payments.length})
          </TabsTrigger>
        </TabsList>

        <TabsContent value={activeTab} className="mt-4">
          <Card data-testid="invoices-table-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Receipt className="h-5 w-5 text-primary" />
                Listado de Facturas
              </CardTitle>
            </CardHeader>
            <CardContent>
              {/* Search Filter */}
              <div className="flex items-center gap-2 mb-4">
                <div className="relative flex-1 max-w-sm">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Buscar por folio, cliente, concepto, UUID SAT..."
                    value={searchFilter}
                    onChange={(e) => setSearchFilter(e.target.value)}
                    className="pl-9"
                    data-testid="invoices-search-filter"
                  />
                  {searchFilter && (
                    <button
                      onClick={() => setSearchFilter("")}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  )}
                </div>
                {searchFilter && (
                  <Badge variant="secondary" className="flex items-center gap-1">
                    Filtro activo: "{searchFilter}"
                  </Badge>
                )}
              </div>
              <div className="rounded-sm border overflow-hidden">
                <Table>
                  <TableHeader>
                    <TableRow className="bg-slate-50">
                      <TableHead>Folio</TableHead>
                      <TableHead>Cliente</TableHead>
                      <TableHead>Concepto</TableHead>
                      <TableHead>Fecha Factura</TableHead>
                      <TableHead>Total</TableHead>
                      <TableHead>Pagado</TableHead>
                      <TableHead>Saldo</TableHead>
                      <TableHead>Vencimiento</TableHead>
                      <TableHead>Estado</TableHead>
                      <TableHead className="w-[50px]"></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredInvoices.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={10} className="text-center py-8 text-muted-foreground">
                          No hay facturas
                        </TableCell>
                      </TableRow>
                    ) : (
                      filteredInvoices.map((invoice) => (
                        <TableRow key={invoice.id} data-testid={`invoice-row-${invoice.id}`}>
                          <TableCell className="font-mono text-sm">
                            {invoice.invoice_number}
                            {invoice.sat_invoice_uuid && (
                              <Badge variant="outline" className="ml-2 text-xs">SAT</Badge>
                            )}
                          </TableCell>
                          <TableCell>
                            <Button 
                              variant="link" 
                              className="p-0 h-auto"
                              onClick={() => handleViewStatement(invoice.client_id)}
                            >
                              {invoice.client_name || getClientName(invoice.client_id)}
                            </Button>
                          </TableCell>
                          <TableCell className="max-w-[200px] truncate">{invoice.concept}</TableCell>
                          <TableCell className="text-slate-600">
                            {invoice.invoice_date ? formatDate(invoice.invoice_date) : formatDate(invoice.created_at)}
                          </TableCell>
                          <TableCell className="font-medium">{formatCurrency(invoice.total)}</TableCell>
                          <TableCell className="text-emerald-600">{formatCurrency(invoice.paid_amount)}</TableCell>
                          <TableCell className="text-amber-600">
                            {formatCurrency(invoice.total - invoice.paid_amount)}
                          </TableCell>
                          <TableCell>
                            {invoice.due_date ? (
                              <div className="flex items-center gap-1">
                                <Calendar className="h-3 w-3" />
                                <span className={invoice.days_overdue > 0 ? "text-red-600 font-medium" : ""}>
                                  {formatDate(invoice.due_date)}
                                </span>
                                {invoice.days_overdue > 0 && (
                                  <Badge variant="destructive" className="ml-1 text-xs">
                                    +{invoice.days_overdue}d
                                  </Badge>
                                )}
                              </div>
                            ) : "-"}
                          </TableCell>
                          <TableCell>
                            <div className="flex flex-col gap-1">
                              <Badge className={getStatusColor(invoice.status)}>
                                {getStatusLabel(invoice.status)}
                              </Badge>
                              {invoice.cfdi_status === "stamped" && (
                                <Badge variant="outline" className="text-xs bg-green-50 text-green-700 border-green-300">
                                  CFDI Timbrado
                                </Badge>
                              )}
                              {invoice.cfdi_status === "cancellation_pending" && (
                                <Badge variant="outline" className="text-xs bg-amber-50 text-amber-700 border-amber-300 animate-pulse">
                                  Cancelación Pendiente
                                </Badge>
                              )}
                              {invoice.cfdi_status === "cancelled" && (
                                <Badge variant="outline" className="text-xs bg-red-50 text-red-700 border-red-300">
                                  CFDI Cancelado
                                </Badge>
                              )}
                            </div>
                          </TableCell>
                          <TableCell>
                            <DropdownMenu>
                              <DropdownMenuTrigger asChild>
                                <Button variant="ghost" size="icon">
                                  <MoreVertical className="h-4 w-4" />
                                </Button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end">
                                <DropdownMenuItem onClick={() => handleDownloadPDF(invoice.id)}>
                                  <Download className="mr-2 h-4 w-4 text-blue-500" />
                                  Descargar PDF
                                </DropdownMenuItem>
                                
                                {/* Edit option - only if not stamped */}
                                {invoice.cfdi_status !== "stamped" && (
                                  <DropdownMenuItem onClick={() => openEditInvoiceDialog(invoice)}>
                                    <FileText className="mr-2 h-4 w-4 text-amber-500" />
                                    Editar Factura
                                  </DropdownMenuItem>
                                )}
                                
                                {/* CFDI Options */}
                                {invoice.cfdi_status !== "stamped" && (
                                  <>
                                    <DropdownMenuItem onClick={() => handleStampInvoice(invoice.id)} disabled={stamping}>
                                      <Stamp className="mr-2 h-4 w-4 text-green-500" />
                                      {stamping ? "Timbrando..." : "Timbrar CFDI"}
                                    </DropdownMenuItem>
                                    <DropdownMenuItem onClick={() => openCfdiDialog(invoice)}>
                                      <Upload className="mr-2 h-4 w-4 text-orange-500" />
                                      Subir CFDI Manual
                                    </DropdownMenuItem>
                                  </>
                                )}
                                
                                {invoice.cfdi_status === "stamped" && (
                                  <>
                                    <DropdownMenuItem onClick={() => handleDownloadXML(invoice.id)}>
                                      <FileCode className="mr-2 h-4 w-4 text-orange-500" />
                                      Descargar XML
                                    </DropdownMenuItem>
                                    <DropdownMenuItem onClick={() => handleDownloadCFDIPDF(invoice.id)}>
                                      <Download className="mr-2 h-4 w-4 text-red-500" />
                                      Descargar PDF CFDI
                                    </DropdownMenuItem>
                                    <DropdownMenuItem onClick={() => handleCancelCFDI(invoice.id)} className="text-red-600">
                                      <X className="mr-2 h-4 w-4" />
                                      Cancelar CFDI
                                    </DropdownMenuItem>
                                    <DropdownMenuSeparator />
                                  </>
                                )}
                                
                                {invoice.cfdi_status === "cancellation_pending" && (
                                  <>
                                    <DropdownMenuItem disabled>
                                      <Loader2 className="mr-2 h-4 w-4 text-amber-500 animate-spin" />
                                      Cancelación en proceso...
                                    </DropdownMenuItem>
                                    <DropdownMenuItem onClick={() => handleDownloadXML(invoice.id)}>
                                      <FileCode className="mr-2 h-4 w-4 text-orange-500" />
                                      Descargar XML
                                    </DropdownMenuItem>
                                    <DropdownMenuSeparator />
                                  </>
                                )}
                                
                                <DropdownMenuItem onClick={() => openPaymentDialog(invoice)}>
                                  <CreditCard className="mr-2 h-4 w-4 text-emerald-500" />
                                  Registrar Abono
                                </DropdownMenuItem>
                                <DropdownMenuItem onClick={() => openCreditNoteDialog(invoice)}>
                                  <FileText className="mr-2 h-4 w-4 text-violet-500" />
                                  Nota de Crédito
                                </DropdownMenuItem>
                                <DropdownMenuItem onClick={() => handleViewStatement(invoice.client_id)}>
                                  <User className="mr-2 h-4 w-4 text-purple-500" />
                                  Estado de Cuenta
                                </DropdownMenuItem>
                                <DropdownMenuSeparator />
                                <DropdownMenuItem
                                  onClick={() => handleDelete(invoice.id)}
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
        </TabsContent>

        {/* Credit Notes Tab */}
        <TabsContent value="credit_notes" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-violet-700">
                <FileText className="h-5 w-5" />
                Notas de Crédito
              </CardTitle>
              <CardDescription>Historial de notas de crédito emitidas</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Folio NC</TableHead>
                      <TableHead>Fecha</TableHead>
                      <TableHead>Factura Rel.</TableHead>
                      <TableHead>Cliente</TableHead>
                      <TableHead>Concepto</TableHead>
                      <TableHead className="text-right">Monto</TableHead>
                      <TableHead>Estado</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {creditNotes.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={7} className="text-center py-8 text-muted-foreground">
                          No hay notas de crédito registradas
                        </TableCell>
                      </TableRow>
                    ) : (
                      creditNotes.map((nc) => {
                        const client = clients.find(c => c.id === nc.client_id);
                        const invoice = invoices.find(i => i.id === nc.invoice_id);
                        return (
                          <TableRow key={nc.id}>
                            <TableCell className="font-medium text-violet-700">{nc.credit_note_number}</TableCell>
                            <TableCell>{formatDate(nc.issue_date || nc.created_at)}</TableCell>
                            <TableCell>{invoice?.invoice_number || '-'}</TableCell>
                            <TableCell>{client?.name || '-'}</TableCell>
                            <TableCell className="max-w-xs truncate">{nc.concept}</TableCell>
                            <TableCell className="text-right font-medium">{formatCurrency(nc.total)}</TableCell>
                            <TableCell>
                              <Badge variant={nc.status === 'applied' ? 'default' : nc.status === 'cancelled' ? 'destructive' : 'secondary'}>
                                {nc.status === 'applied' ? 'Aplicada' : nc.status === 'cancelled' ? 'Cancelada' : 'Borrador'}
                              </Badge>
                            </TableCell>
                          </TableRow>
                        );
                      })
                    )}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Payments (Complementos de Pago) Tab */}
        <TabsContent value="payments" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-emerald-700">
                <CreditCard className="h-5 w-5" />
                Complementos de Pago
              </CardTitle>
              <CardDescription>Historial de pagos/abonos recibidos (listos para timbrar como complemento de pago)</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Fecha</TableHead>
                      <TableHead>Factura</TableHead>
                      <TableHead>Cliente</TableHead>
                      <TableHead>Forma Pago SAT</TableHead>
                      <TableHead>Parcialidad</TableHead>
                      <TableHead className="text-right">Monto</TableHead>
                      <TableHead>Referencia</TableHead>
                      <TableHead>UUID Complemento</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {payments.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={8} className="text-center py-8 text-muted-foreground">
                          No hay pagos registrados
                        </TableCell>
                      </TableRow>
                    ) : (
                      payments.map((payment) => {
                        const invoice = invoices.find(i => i.id === payment.invoice_id);
                        const client = clients.find(c => c.id === payment.client_id);
                        const formaPago = SAT_FORMAS_PAGO.find(f => f.value === payment.sat_forma_pago);
                        return (
                          <TableRow key={payment.id}>
                            <TableCell>{formatDate(payment.payment_date)}</TableCell>
                            <TableCell className="font-medium">{invoice?.invoice_number || '-'}</TableCell>
                            <TableCell>{client?.name || '-'}</TableCell>
                            <TableCell className="text-xs">{formaPago?.label || payment.sat_forma_pago || '-'}</TableCell>
                            <TableCell className="text-center">
                              <Badge variant="outline">#{payment.num_parcialidad || 1}</Badge>
                            </TableCell>
                            <TableCell className="text-right font-medium text-emerald-600">
                              {formatCurrency(payment.amount)}
                            </TableCell>
                            <TableCell className="text-xs text-muted-foreground">{payment.reference || '-'}</TableCell>
                            <TableCell>
                              {payment.cfdi_complemento_uuid ? (
                                <Badge variant="default" className="text-xs">Timbrado</Badge>
                              ) : (
                                <Badge variant="secondary" className="text-xs">Pendiente</Badge>
                              )}
                            </TableCell>
                          </TableRow>
                        );
                      })
                    )}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Create Invoice Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="sm:max-w-[750px] max-h-[90vh] overflow-y-auto">
          <form onSubmit={handleSubmit}>
            <DialogHeader>
              <DialogTitle>{selectedInvoice ? "Editar Factura" : "Nueva Factura"}</DialogTitle>
              <DialogDescription>
                {selectedInvoice 
                  ? "Modifica los datos de la factura (no disponible para facturas timbradas)" 
                  : "Registra una nueva factura con datos fiscales para CFDI"}
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid grid-cols-3 gap-4">
                <div className="grid gap-2">
                  <Label>Folio</Label>
                  <Input
                    value={formData.invoice_number}
                    onChange={(e) => setFormData({ ...formData, invoice_number: e.target.value })}
                    required
                  />
                </div>
                <div className="grid gap-2">
                  <Label>Fecha de Factura *</Label>
                  <Input
                    type="date"
                    value={formData.invoice_date}
                    onChange={(e) => setFormData({ ...formData, invoice_date: e.target.value })}
                    required
                  />
                </div>
                <div className="grid gap-2">
                  <Label>Fecha Vencimiento</Label>
                  <Input
                    type="date"
                    value={formData.due_date}
                    onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
                  />
                </div>
              </div>
              <div className="grid gap-2">
                <Label>Cliente * <span className="text-xs text-muted-foreground">(Solo clientes, no prospectos)</span></Label>
                <Select
                  value={formData.client_id}
                  onValueChange={(value) => setFormData({ ...formData, client_id: value })}
                >
                  <SelectTrigger className="truncate"><SelectValue placeholder="Seleccionar cliente" /></SelectTrigger>
                  <SelectContent>
                    {clients.filter(c => !c.is_prospect).length === 0 ? (
                      <div className="p-2 text-sm text-muted-foreground text-center">
                        No hay clientes disponibles. Convierte un prospecto a cliente desde el CRM.
                      </div>
                    ) : (
                      clients.filter(c => !c.is_prospect).map((c) => (
                        <SelectItem key={c.id} value={c.id} className="truncate">
                          <span className="truncate block max-w-[400px]">
                            {c.trade_name || c.name} {c.rfc && `- ${c.rfc}`}
                          </span>
                        </SelectItem>
                      ))
                    )}
                  </SelectContent>
                </Select>
              </div>
              <div className="grid gap-2">
                <Label>Proyecto (opcional)</Label>
                <Select
                  value={formData.project_id}
                  onValueChange={(value) => setFormData({ ...formData, project_id: value })}
                >
                  <SelectTrigger><SelectValue placeholder="Seleccionar proyecto" /></SelectTrigger>
                  <SelectContent>
                    {projects.map((p) => (
                      <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="grid gap-2">
                  <Label>Referencia (OC Cliente / Orden de Trabajo)</Label>
                  <Input
                    value={formData.reference}
                    onChange={(e) => setFormData({ ...formData, reference: e.target.value })}
                    placeholder="Ej: OC-2024-001, OT-123"
                  />
                </div>
                <div className="grid gap-2">
                  <Label>Condiciones de Pago</Label>
                  <Select
                    value={formData.payment_terms || "contado"}
                    onValueChange={(value) => setFormData({ ...formData, payment_terms: value })}
                  >
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {PAYMENT_TERMS_OPTIONS.map(opt => (
                        <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="grid gap-2">
                  <Label>Forma de Pago SAT</Label>
                  <Select
                    value={formData.forma_pago || "99"}
                    onValueChange={(value) => setFormData({ ...formData, forma_pago: value })}
                  >
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {SAT_FORMAS_PAGO.map(fp => (
                        <SelectItem key={fp.value} value={fp.value}>{fp.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid gap-2">
                  <Label>{formData.custom_field_label || "Campo Libre"} <span className="text-xs text-muted-foreground">(Número de Orden)</span></Label>
                  <Input
                    value={formData.custom_field || ""}
                    onChange={(e) => setFormData({ ...formData, custom_field: e.target.value })}
                    placeholder="Ej: ORD-001"
                  />
                </div>
              </div>

              {/* Items Section */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <Label className="text-sm font-medium">Conceptos / Partidas</Label>
                  <Button type="button" variant="outline" size="sm" onClick={addItem}>
                    <PlusCircle className="mr-1 h-4 w-4" />
                    Agregar
                  </Button>
                </div>
                {formData.items.map((item, index) => (
                  <div key={index} className="p-3 bg-slate-50 rounded-lg space-y-3 border">
                    <div className="grid grid-cols-12 gap-2 items-end">
                      <div className="col-span-12 md:col-span-5">
                        <Label className="text-xs">Descripción *</Label>
                        <Input
                          value={item.description}
                          onChange={(e) => handleItemChange(index, "description", e.target.value)}
                          placeholder="Descripción del servicio/producto"
                          required
                        />
                      </div>
                      <div className="col-span-3 md:col-span-2">
                        <Label className="text-xs">Cantidad</Label>
                        <Input
                          type="number"
                          value={item.quantity}
                          onChange={(e) => handleItemChange(index, "quantity", parseFloat(e.target.value) || 0)}
                        />
                      </div>
                      <div className="col-span-3 md:col-span-1">
                        <Label className="text-xs">Unidad</Label>
                        <Input
                          value={item.unit}
                          onChange={(e) => handleItemChange(index, "unit", e.target.value)}
                        />
                      </div>
                      <div className="col-span-4 md:col-span-2">
                        <Label className="text-xs">P. Unitario</Label>
                        <Input
                          type="number"
                          value={item.unit_price}
                          onChange={(e) => handleItemChange(index, "unit_price", parseFloat(e.target.value) || 0)}
                        />
                      </div>
                      <div className="col-span-2 md:col-span-2 flex items-end gap-1">
                        <div className="flex-1">
                          <Label className="text-xs">Total</Label>
                          <Input value={formatCurrency(item.quantity * item.unit_price)} disabled className="text-xs" />
                        </div>
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon"
                          onClick={() => removeItem(index)}
                          disabled={formData.items.length === 1}
                          className="h-9 w-9"
                        >
                          <MinusCircle className="h-4 w-4 text-red-500" />
                        </Button>
                      </div>
                    </div>
                    {/* SAT Keys */}
                    <div className="flex flex-wrap gap-3 items-start border-t pt-3 mt-2">
                      <div className="flex-1 min-w-[180px] max-w-[250px]">
                        <Label className="text-xs text-blue-600 mb-1 block">Clave SAT Producto/Servicio</Label>
                        <SATProductSearch
                          value={item.clave_prod_serv || ""}
                          onChange={(val) => handleItemChange(index, "clave_prod_serv", val)}
                          placeholder="Buscar clave SAT..."
                        />
                        {!item.clave_prod_serv && (
                          <p className="text-[10px] text-slate-400 mt-1">Ej: 01010101</p>
                        )}
                      </div>
                      <div className="flex-1 min-w-[150px] max-w-[200px]">
                        <Label className="text-xs text-blue-600 mb-1 block">Clave Unidad SAT</Label>
                        <SATUnitSearch
                          value={item.clave_unidad || ""}
                          onChange={(val) => handleItemChange(index, "clave_unidad", val)}
                        />
                        {!item.clave_unidad && (
                          <p className="text-[10px] text-slate-400 mt-1">Ej: H87</p>
                        )}
                      </div>
                      <div className="flex items-center text-[10px] text-slate-400 pt-5">
                        Requeridos para CFDI
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Totals */}
              <div className="space-y-2 p-4 bg-slate-100 rounded-lg">
                <div className="flex justify-between text-sm">
                  <span>Subtotal:</span>
                  <span className="font-medium">{formatCurrency(formData.subtotal)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>IVA (16%):</span>
                  <span className="font-medium">{formatCurrency(formData.tax)}</span>
                </div>
                <Separator />
                <div className="flex justify-between text-lg font-bold">
                  <span>Total:</span>
                  <span className="text-primary">{formatCurrency(formData.total)}</span>
                </div>
              </div>
              
              {/* Campo Personalizado - Debajo de totales */}
              <div className="grid grid-cols-2 gap-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
                <div className="grid gap-2">
                  <Label className="text-blue-700">Etiqueta del Campo Personalizado</Label>
                  <Input
                    value={formData.custom_field_label}
                    onChange={(e) => setFormData({ ...formData, custom_field_label: e.target.value })}
                    placeholder="Ej: Orden de Trabajo, Pedido, Contrato"
                    className="bg-white"
                  />
                </div>
                <div className="grid gap-2">
                  <Label className="text-blue-700">{formData.custom_field_label || "Campo Personalizado"}</Label>
                  <Input
                    value={formData.custom_field}
                    onChange={(e) => setFormData({ ...formData, custom_field: e.target.value })}
                    placeholder={formData.custom_field_label ? `Ingrese ${formData.custom_field_label}` : "Valor del campo personalizado"}
                    className="bg-white"
                  />
                </div>
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>Cancelar</Button>
              <Button type="submit" className="btn-industrial">Registrar Factura</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Payment Dialog - Complemento de Pago CFDI */}
      <Dialog open={paymentDialogOpen} onOpenChange={setPaymentDialogOpen}>
        <DialogContent className="sm:max-w-[700px] max-h-[90vh] overflow-y-auto">
          <form onSubmit={handlePayment}>
            <DialogHeader>
              <DialogTitle>Registrar Abono / Complemento de Pago</DialogTitle>
              <DialogDescription className="space-y-1">
                <div>
                  Factura: <strong>{selectedInvoice?.invoice_number}</strong> | 
                  Total: {formatCurrency(selectedInvoice?.total || 0)} |
                  Pagado: {formatCurrency(selectedInvoice?.paid_amount || 0)} |
                  <span className="text-primary font-semibold"> Saldo: {formatCurrency((selectedInvoice?.total || 0) - (selectedInvoice?.paid_amount || 0))}</span>
                </div>
                <div className="text-xs">
                  <span className="bg-blue-100 text-blue-700 px-2 py-0.5 rounded">
                    Parcialidad #{paymentForm.num_parcialidad}
                  </span>
                  {selectedInvoice && payments.filter(p => p.invoice_id === selectedInvoice.id).length > 0 && (
                    <span className="ml-2 text-slate-500">
                      ({payments.filter(p => p.invoice_id === selectedInvoice.id).length} pago(s) previo(s))
                    </span>
                  )}
                </div>
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              {/* Sección: Datos del Pago */}
              <div className="space-y-3">
                <h4 className="text-sm font-semibold text-slate-700 flex items-center gap-2">
                  <DollarSign className="h-4 w-4" />
                  Datos del Pago
                </h4>
                <div className="grid grid-cols-3 gap-3">
                  <div className="grid gap-1">
                    <Label className="text-xs">Monto del Abono *</Label>
                    <Input
                      type="number"
                      step="0.01"
                      value={paymentForm.amount}
                      onChange={(e) => setPaymentForm({ ...paymentForm, amount: e.target.value })}
                      placeholder="0.00"
                      required
                      className="h-9"
                    />
                  </div>
                  <div className="grid gap-1">
                    <Label className="text-xs">Fecha de Pago *</Label>
                    <Input
                      type="date"
                      value={paymentForm.payment_date}
                      onChange={(e) => setPaymentForm({ ...paymentForm, payment_date: e.target.value })}
                      required
                      className="h-9"
                    />
                  </div>
                  <div className="grid gap-1">
                    <Label className="text-xs">No. Parcialidad</Label>
                    <Input
                      type="number"
                      min="1"
                      value={paymentForm.num_parcialidad}
                      onChange={(e) => setPaymentForm({ ...paymentForm, num_parcialidad: e.target.value })}
                      className="h-9"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="grid gap-1">
                    <Label className="text-xs">Forma de Pago SAT *</Label>
                    <Select
                      value={paymentForm.sat_forma_pago}
                      onValueChange={(value) => setPaymentForm({ ...paymentForm, sat_forma_pago: value })}
                    >
                      <SelectTrigger className="h-9"><SelectValue /></SelectTrigger>
                      <SelectContent>
                        {SAT_FORMAS_PAGO.map((m) => (
                          <SelectItem key={m.value} value={m.value}>{m.label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="grid gap-1">
                    <Label className="text-xs">Número de Operación</Label>
                    <Input
                      value={paymentForm.num_operacion}
                      onChange={(e) => setPaymentForm({ ...paymentForm, num_operacion: e.target.value })}
                      placeholder="No. transferencia, autorización, etc."
                      className="h-9"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-3">
                  <div className="grid gap-1">
                    <Label className="text-xs">Moneda del Pago</Label>
                    <Select
                      value={paymentForm.moneda_pago}
                      onValueChange={(value) => setPaymentForm({ ...paymentForm, moneda_pago: value })}
                    >
                      <SelectTrigger className="h-9"><SelectValue /></SelectTrigger>
                      <SelectContent>
                        {MONEDAS.map((m) => (
                          <SelectItem key={m.value} value={m.value}>{m.label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="grid gap-1">
                    <Label className="text-xs">Tipo de Cambio</Label>
                    <Input
                      type="number"
                      step="0.0001"
                      value={paymentForm.tipo_cambio}
                      onChange={(e) => setPaymentForm({ ...paymentForm, tipo_cambio: e.target.value })}
                      placeholder="1.0000"
                      disabled={paymentForm.moneda_pago === "MXN"}
                      className="h-9"
                    />
                  </div>
                  <div className="grid gap-1">
                    <Label className="text-xs">Método (interno)</Label>
                    <Select
                      value={paymentForm.payment_method}
                      onValueChange={(value) => setPaymentForm({ ...paymentForm, payment_method: value })}
                    >
                      <SelectTrigger className="h-9"><SelectValue /></SelectTrigger>
                      <SelectContent>
                        {PAYMENT_METHODS.map((m) => (
                          <SelectItem key={m.value} value={m.value}>{m.label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>

              <Separator />

              {/* Sección: Datos Bancarios */}
              <div className="space-y-3">
                <h4 className="text-sm font-semibold text-slate-700 flex items-center gap-2">
                  <CreditCard className="h-4 w-4" />
                  Datos Bancarios <span className="text-xs font-normal text-slate-400">(Opcionales para CFDI)</span>
                </h4>
                
                {/* Banco Ordenante (quien paga) */}
                <div className="p-3 bg-slate-50 rounded-lg space-y-2">
                  <p className="text-xs font-medium text-slate-600">Banco Ordenante (quien paga)</p>
                  <div className="grid grid-cols-3 gap-3">
                    <div className="grid gap-1">
                      <Label className="text-xs">RFC Banco</Label>
                      <Input
                        value={paymentForm.rfc_banco_ordenante}
                        onChange={(e) => setPaymentForm({ ...paymentForm, rfc_banco_ordenante: e.target.value.toUpperCase() })}
                        placeholder="BBA830831LJ2"
                        maxLength={12}
                        className="h-8 text-xs"
                      />
                    </div>
                    <div className="grid gap-1">
                      <Label className="text-xs">Nombre Banco</Label>
                      <Input
                        value={paymentForm.nombre_banco_ordenante}
                        onChange={(e) => setPaymentForm({ ...paymentForm, nombre_banco_ordenante: e.target.value })}
                        placeholder="BBVA México"
                        className="h-8 text-xs"
                      />
                    </div>
                    <div className="grid gap-1">
                      <Label className="text-xs">Cuenta Ordenante</Label>
                      <Input
                        value={paymentForm.cuenta_ordenante}
                        onChange={(e) => setPaymentForm({ ...paymentForm, cuenta_ordenante: e.target.value })}
                        placeholder="Últimos 4 dígitos o CLABE"
                        className="h-8 text-xs"
                      />
                    </div>
                  </div>
                </div>

                {/* Banco Beneficiario (quien recibe) */}
                <div className="p-3 bg-blue-50 rounded-lg space-y-2">
                  <p className="text-xs font-medium text-blue-700">Banco Beneficiario (quien recibe el pago)</p>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="grid gap-1">
                      <Label className="text-xs">RFC Banco</Label>
                      <Input
                        value={paymentForm.rfc_banco_beneficiario}
                        onChange={(e) => setPaymentForm({ ...paymentForm, rfc_banco_beneficiario: e.target.value.toUpperCase() })}
                        placeholder="BNM840515VB1"
                        maxLength={12}
                        className="h-8 text-xs"
                      />
                    </div>
                    <div className="grid gap-1">
                      <Label className="text-xs">Cuenta Beneficiaria</Label>
                      <Input
                        value={paymentForm.cuenta_beneficiaria}
                        onChange={(e) => setPaymentForm({ ...paymentForm, cuenta_beneficiaria: e.target.value })}
                        placeholder="CLABE o No. Cuenta"
                        className="h-8 text-xs"
                      />
                    </div>
                  </div>
                </div>
              </div>

              <Separator />

              {/* Sección: Comprobante y Notas */}
              <div className="space-y-3">
                <h4 className="text-sm font-semibold text-slate-700 flex items-center gap-2">
                  <FileText className="h-4 w-4" />
                  Comprobante y Notas
                </h4>
                <div className="grid grid-cols-2 gap-3">
                  <div className="grid gap-1">
                    <Label className="text-xs">Comprobante de Pago</Label>
                    <Input
                      type="file"
                      accept=".pdf,.png,.jpg,.jpeg"
                      onChange={(e) => setPaymentForm({ ...paymentForm, proof_file: e.target.files?.[0] })}
                      className="h-9 text-xs"
                    />
                    <p className="text-[10px] text-muted-foreground">PDF o imagen del comprobante bancario</p>
                  </div>
                  <div className="grid gap-1">
                    <Label className="text-xs">Referencia</Label>
                    <Input
                      value={paymentForm.reference}
                      onChange={(e) => setPaymentForm({ ...paymentForm, reference: e.target.value })}
                      placeholder="No. de cheque, folio, etc."
                      className="h-9"
                    />
                  </div>
                </div>
                <div className="grid gap-1">
                  <Label className="text-xs">Notas / Observaciones</Label>
                  <Textarea
                    value={paymentForm.notes}
                    onChange={(e) => setPaymentForm({ ...paymentForm, notes: e.target.value })}
                    placeholder="Observaciones adicionales del pago..."
                    rows={2}
                    className="text-xs"
                  />
                </div>
              </div>

              {/* Resumen del documento relacionado */}
              {selectedInvoice?.sat_invoice_uuid && (
                <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                  <p className="text-xs font-medium text-green-700 mb-2">Documento Relacionado (CFDI)</p>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div><span className="text-slate-500">UUID:</span> <span className="font-mono">{selectedInvoice.sat_invoice_uuid}</span></div>
                    <div><span className="text-slate-500">Folio:</span> {selectedInvoice.invoice_number}</div>
                    <div><span className="text-slate-500">Total Factura:</span> {formatCurrency(selectedInvoice.total)}</div>
                    <div><span className="text-slate-500">Saldo Anterior:</span> {formatCurrency((selectedInvoice.total || 0) - (selectedInvoice.paid_amount || 0))}</div>
                  </div>
                </div>
              )}

              {/* Info para CFDI */}
              <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg">
                <p className="text-xs text-amber-700">
                  <strong>Nota:</strong> Los datos bancarios son opcionales pero recomendados para el complemento de pago CFDI 4.0. 
                  El saldo insoluto se calculará automáticamente al registrar el pago.
                </p>
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setPaymentDialogOpen(false)}>Cancelar</Button>
              <Button type="submit" className="btn-industrial">Registrar Abono</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Client Statement Dialog */}
      <Dialog open={statementDialogOpen} onOpenChange={setStatementDialogOpen}>
        <DialogContent className="sm:max-w-[700px] max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Estado de Cuenta</DialogTitle>
            <DialogDescription>
              {clientStatement?.client?.name}
            </DialogDescription>
          </DialogHeader>
          {clientStatement && (
            <div className="space-y-4">
              {/* Summary */}
              <div className="grid grid-cols-3 gap-4">
                <Card>
                  <CardContent className="p-3 text-center">
                    <p className="text-sm text-muted-foreground">Total Facturado</p>
                    <p className="text-xl font-bold">{formatCurrency(clientStatement.summary.total_invoiced)}</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-3 text-center">
                    <p className="text-sm text-muted-foreground">Total Pagado</p>
                    <p className="text-xl font-bold text-emerald-600">{formatCurrency(clientStatement.summary.total_paid)}</p>
                  </CardContent>
                </Card>
                <Card className={clientStatement.summary.balance > 0 ? "border-amber-200 bg-amber-50" : ""}>
                  <CardContent className="p-3 text-center">
                    <p className="text-sm text-muted-foreground">Saldo Pendiente</p>
                    <p className={`text-xl font-bold ${clientStatement.summary.balance > 0 ? "text-amber-600" : "text-emerald-600"}`}>
                      {formatCurrency(clientStatement.summary.balance)}
                    </p>
                  </CardContent>
                </Card>
              </div>

              {/* Overdue Warning */}
              {clientStatement.summary.overdue_count > 0 && (
                <Card className="border-red-200 bg-red-50">
                  <CardContent className="p-3 flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4 text-red-600" />
                    <span className="text-red-800 text-sm">
                      {clientStatement.summary.overdue_count} factura(s) vencida(s) por {formatCurrency(clientStatement.summary.overdue_amount)}
                    </span>
                  </CardContent>
                </Card>
              )}

              {/* Invoices List - Only show invoices with pending balance */}
              <div>
                <h4 className="font-semibold mb-2">Facturas con Saldo Pendiente</h4>
                <div className="border rounded-sm max-h-40 overflow-y-auto">
                  {clientStatement.invoices
                    .filter(inv => inv.status !== 'paid' && inv.status !== 'cancelled' && (inv.total - inv.paid_amount) > 0)
                    .map((inv) => (
                    <div key={inv.id} className="p-2 border-b last:border-b-0 flex items-center justify-between text-sm">
                      <div>
                        <span className="font-mono">{inv.invoice_number}</span>
                        <span className="text-muted-foreground ml-2 truncate max-w-[150px]">{inv.concept}</span>
                      </div>
                      <div className="flex items-center gap-3">
                        <span>{formatCurrency(inv.total - inv.paid_amount)}</span>
                        <Badge className={getStatusColor(inv.status)}>{getStatusLabel(inv.status)}</Badge>
                      </div>
                    </div>
                  ))}
                  {clientStatement.invoices.filter(inv => inv.status !== 'paid' && inv.status !== 'cancelled' && (inv.total - inv.paid_amount) > 0).length === 0 && (
                    <div className="p-4 text-center text-sm text-emerald-600">
                      ✓ No hay facturas con saldo pendiente
                    </div>
                  )}
                </div>
              </div>

              {/* Payments List */}
              {clientStatement.payments.length > 0 && (
                <div>
                  <h4 className="font-semibold mb-2">Pagos Recibidos</h4>
                  <div className="border rounded-sm max-h-40 overflow-y-auto">
                    {clientStatement.payments.map((p) => (
                      <div key={p.id} className="p-2 border-b last:border-b-0 flex items-center justify-between text-sm">
                        <div>
                          <span>{formatDate(p.payment_date)}</span>
                          <span className="text-muted-foreground ml-2">{p.payment_method}</span>
                          {p.reference && <span className="text-muted-foreground ml-1">({p.reference})</span>}
                        </div>
                        <span className="text-emerald-600 font-medium">{formatCurrency(p.amount)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
          <DialogFooter>
            {clientStatement && (
              <Button 
                variant="outline" 
                onClick={() => handleDownloadStatementPDF(clientStatement.client.id)}
                className="mr-auto"
              >
                <Download className="mr-2 h-4 w-4" />
                Descargar PDF
              </Button>
            )}
            <Button variant="outline" onClick={() => setStatementDialogOpen(false)}>Cerrar</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Credit Note Dialog */}
      <Dialog open={creditNoteDialogOpen} onOpenChange={setCreditNoteDialogOpen}>
        <DialogContent className="sm:max-w-[750px] max-h-[90vh] overflow-y-auto">
          <form onSubmit={handleCreditNoteSubmit}>
            <DialogHeader>
              <DialogTitle className="text-violet-700">Nueva Nota de Crédito</DialogTitle>
              <DialogDescription>
                CFDI tipo "E" (Egreso) - Factura relacionada: <strong>{selectedInvoice?.invoice_number}</strong>
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              {/* Header Info */}
              <div className="grid grid-cols-3 gap-3">
                <div className="grid gap-1">
                  <Label className="text-xs">Folio Nota de Crédito</Label>
                  <Input
                    value={creditNoteForm.credit_note_number}
                    onChange={(e) => setCreditNoteForm({ ...creditNoteForm, credit_note_number: e.target.value })}
                    className="h-9"
                    required
                  />
                </div>
                <div className="grid gap-1">
                  <Label className="text-xs">Fecha de Emisión *</Label>
                  <Input
                    type="date"
                    value={creditNoteForm.issue_date}
                    onChange={(e) => setCreditNoteForm({ ...creditNoteForm, issue_date: e.target.value })}
                    className="h-9"
                    required
                  />
                </div>
                <div className="grid gap-1">
                  <Label className="text-xs">Tipo Relación SAT</Label>
                  <Select
                    value={creditNoteForm.sat_tipo_relacion}
                    onValueChange={(value) => setCreditNoteForm({ ...creditNoteForm, sat_tipo_relacion: value })}
                  >
                    <SelectTrigger className="h-9"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="01">01 - Nota de crédito</SelectItem>
                      <SelectItem value="03">03 - Devolución de mercancía</SelectItem>
                      <SelectItem value="04">04 - Sustitución de CFDI</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Related Invoice Info */}
              {selectedInvoice && (
                <div className="p-3 bg-slate-50 rounded-lg border">
                  <p className="text-xs font-medium text-slate-600 mb-2">Factura Relacionada</p>
                  <div className="grid grid-cols-4 gap-2 text-xs">
                    <div><span className="text-slate-400">Folio:</span> <span className="font-medium">{selectedInvoice.invoice_number}</span></div>
                    <div><span className="text-slate-400">Total:</span> <span className="font-medium">{formatCurrency(selectedInvoice.total)}</span></div>
                    <div><span className="text-slate-400">Pagado:</span> <span className="font-medium">{formatCurrency(selectedInvoice.paid_amount)}</span></div>
                    <div><span className="text-slate-400">Saldo:</span> <span className="font-medium text-amber-600">{formatCurrency((selectedInvoice.total || 0) - (selectedInvoice.paid_amount || 0))}</span></div>
                  </div>
                  {selectedInvoice.sat_invoice_uuid && (
                    <p className="text-xs mt-2 text-slate-500">
                      UUID: <span className="font-mono">{selectedInvoice.sat_invoice_uuid}</span>
                    </p>
                  )}
                </div>
              )}

              {/* Reason */}
              <div className="grid gap-1">
                <Label className="text-xs">Motivo de la Nota de Crédito *</Label>
                <Select
                  value={creditNoteForm.reason}
                  onValueChange={(value) => setCreditNoteForm({ ...creditNoteForm, reason: value })}
                >
                  <SelectTrigger><SelectValue placeholder="Seleccionar motivo" /></SelectTrigger>
                  <SelectContent>
                    {motivosNC.map((motivo, idx) => (
                      <SelectItem key={idx} value={motivo}>{motivo}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Items */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <Label className="text-sm font-medium">Conceptos</Label>
                  <Button type="button" variant="outline" size="sm" onClick={addCreditNoteItem}>
                    <PlusCircle className="mr-1 h-4 w-4" />
                    Agregar
                  </Button>
                </div>
                {creditNoteForm.items.map((item, index) => (
                  <div key={index} className="p-3 bg-violet-50 rounded-lg space-y-2 border border-violet-200">
                    <div className="grid grid-cols-12 gap-2 items-end">
                      <div className="col-span-12 md:col-span-5">
                        <Label className="text-xs">Descripción</Label>
                        <Input
                          value={item.description}
                          onChange={(e) => handleCreditNoteItemChange(index, "description", e.target.value)}
                          placeholder="Concepto del crédito"
                          className="h-8"
                        />
                      </div>
                      <div className="col-span-3 md:col-span-2">
                        <Label className="text-xs">Cantidad</Label>
                        <Input
                          type="number"
                          value={item.quantity}
                          onChange={(e) => handleCreditNoteItemChange(index, "quantity", parseFloat(e.target.value) || 0)}
                          className="h-8"
                        />
                      </div>
                      <div className="col-span-3 md:col-span-2">
                        <Label className="text-xs">P. Unitario</Label>
                        <Input
                          type="number"
                          value={item.unit_price}
                          onChange={(e) => handleCreditNoteItemChange(index, "unit_price", parseFloat(e.target.value) || 0)}
                          className="h-8"
                        />
                      </div>
                      <div className="col-span-4 md:col-span-2">
                        <Label className="text-xs">Total</Label>
                        <Input value={formatCurrency(item.quantity * item.unit_price)} disabled className="h-8 text-xs" />
                      </div>
                      <div className="col-span-2 md:col-span-1">
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon"
                          onClick={() => removeCreditNoteItem(index)}
                          disabled={creditNoteForm.items.length === 1}
                          className="h-8 w-8"
                        >
                          <MinusCircle className="h-4 w-4 text-red-500" />
                        </Button>
                      </div>
                    </div>
                    {/* SAT Keys */}
                    <div className="grid grid-cols-2 gap-2">
                      <div className="grid gap-1">
                        <Label className="text-xs text-violet-700">Clave SAT Producto</Label>
                        <SATProductSearch
                          value={item.clave_prod_serv || ""}
                          onChange={(val) => handleCreditNoteItemChange(index, "clave_prod_serv", val)}
                          placeholder="Buscar clave..."
                        />
                      </div>
                      <div className="grid gap-1">
                        <Label className="text-xs text-violet-700">Clave Unidad SAT</Label>
                        <SATUnitSearch
                          value={item.clave_unidad || ""}
                          onChange={(val) => handleCreditNoteItemChange(index, "clave_unidad", val)}
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Totals */}
              <div className="space-y-2 p-4 bg-violet-100 rounded-lg">
                <div className="flex justify-between text-sm">
                  <span>Subtotal:</span>
                  <span className="font-medium">{formatCurrency(creditNoteForm.subtotal)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>IVA (16%):</span>
                  <span className="font-medium">{formatCurrency(creditNoteForm.tax)}</span>
                </div>
                <Separator />
                <div className="flex justify-between text-lg font-bold text-violet-700">
                  <span>Total Nota de Crédito:</span>
                  <span>{formatCurrency(creditNoteForm.total)}</span>
                </div>
              </div>

              {/* Status */}
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="apply_immediately"
                  checked={creditNoteForm.status === "applied"}
                  onChange={(e) => setCreditNoteForm({ ...creditNoteForm, status: e.target.checked ? "applied" : "draft" })}
                  className="h-4 w-4"
                />
                <Label htmlFor="apply_immediately" className="text-sm">
                  Aplicar inmediatamente al saldo de la factura
                </Label>
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setCreditNoteDialogOpen(false)}>Cancelar</Button>
              <Button type="submit" className="bg-violet-600 hover:bg-violet-700">Registrar Nota de Crédito</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* CFDI Manual Upload Dialog */}
      <Dialog open={cfdiDialogOpen} onOpenChange={setCfdiDialogOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <form onSubmit={handleUploadManualCFDI}>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Upload className="h-5 w-5 text-orange-500" />
                Subir CFDI Manual
              </DialogTitle>
              <DialogDescription>
                Sube el CFDI generado externamente para vincularlo a esta factura.
                El UUID se extraerá automáticamente del XML.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>Archivo XML *</Label>
                <Input
                  type="file"
                  accept=".xml"
                  required
                  onChange={(e) => setCfdiForm({ ...cfdiForm, xml_file: e.target.files?.[0] })}
                />
                <p className="text-xs text-muted-foreground">
                  El XML debe contener el TimbreFiscalDigital con el UUID
                </p>
              </div>
              <div className="space-y-2">
                <Label>Archivo PDF *</Label>
                <Input
                  type="file"
                  accept=".pdf"
                  required
                  onChange={(e) => setCfdiForm({ ...cfdiForm, pdf_file: e.target.files?.[0] })}
                />
              </div>
              <p className="text-xs text-amber-600 bg-amber-50 p-2 rounded">
                ⚠️ Ambos archivos son obligatorios. El UUID se extraerá automáticamente del XML.
              </p>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setCfdiDialogOpen(false)}>
                Cancelar
              </Button>
              <Button type="submit" className="bg-orange-600 hover:bg-orange-700">
                Vincular CFDI
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Invoices;
