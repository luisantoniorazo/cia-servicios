import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(amount, currency = "MXN") {
  return new Intl.NumberFormat("es-MX", {
    style: "currency",
    currency: currency,
  }).format(amount);
}

export function formatDate(date) {
  if (!date) return "-";
  const d = new Date(date);
  return d.toLocaleDateString("es-MX", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function formatDateTime(date) {
  if (!date) return "-";
  const d = new Date(date);
  return d.toLocaleDateString("es-MX", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function getStatusColor(status) {
  const colors = {
    active: "bg-emerald-100 text-emerald-800",
    pending: "bg-amber-100 text-amber-800",
    completed: "bg-blue-100 text-blue-800",
    cancelled: "bg-red-100 text-red-800",
    suspended: "bg-red-100 text-red-800",
    quotation: "bg-slate-100 text-slate-800",
    authorized: "bg-emerald-100 text-emerald-800",
    prospect: "bg-slate-100 text-slate-800",
    negotiation: "bg-amber-100 text-amber-800",
    detailed_quote: "bg-blue-100 text-blue-800",
    negotiating: "bg-orange-100 text-orange-800",
    under_review: "bg-purple-100 text-purple-800",
    denied: "bg-red-100 text-red-800",
    paid: "bg-emerald-100 text-emerald-800",
    partial: "bg-amber-100 text-amber-800",
    overdue: "bg-red-100 text-red-800",
    requested: "bg-slate-100 text-slate-800",
    quoted: "bg-blue-100 text-blue-800",
    approved: "bg-emerald-100 text-emerald-800",
    ordered: "bg-purple-100 text-purple-800",
    received: "bg-emerald-100 text-emerald-800",
  };
  return colors[status] || "bg-slate-100 text-slate-800";
}

export function getStatusLabel(status) {
  const labels = {
    active: "Activo",
    pending: "Pendiente",
    completed: "Completado",
    cancelled: "Cancelado",
    suspended: "Suspendido",
    quotation: "Cotización",
    authorized: "Autorizado",
    prospect: "Prospecto",
    negotiation: "Negociación",
    detailed_quote: "Cotización Detallada",
    negotiating: "Negociando",
    under_review: "En Revisión",
    denied: "Negado",
    paid: "Pagado",
    partial: "Pago Parcial",
    overdue: "Vencido",
    requested: "Solicitado",
    quoted: "Cotizado",
    approved: "Aprobado",
    ordered: "Ordenado",
    received: "Recibido",
    invoiced: "Facturado",
    super_admin: "Super Admin",
    admin: "Administrador",
    manager: "Gerente",
    user: "Usuario",
  };
  return labels[status] || status;
}

export function getPhaseLabel(phase) {
  const labels = {
    negotiation: "Negociación e Ingeniería",
    purchases: "Compras",
    process: "Proceso",
    delivery: "Entrega",
  };
  return labels[phase] || phase;
}

export function calculatePercentage(value, total) {
  if (!total || total === 0) return 0;
  return Math.round((value / total) * 100);
}

export function generateQuoteNumber() {
  const now = new Date();
  const year = now.getFullYear();
  const random = Math.floor(Math.random() * 1000).toString().padStart(3, "0");
  return `COT-${year}-${random}`;
}

export function generateInvoiceNumber() {
  const now = new Date();
  const year = now.getFullYear();
  const random = Math.floor(Math.random() * 1000).toString().padStart(3, "0");
  return `FAC-${year}-${random}`;
}

export function generatePONumber() {
  const now = new Date();
  const year = now.getFullYear();
  const random = Math.floor(Math.random() * 1000).toString().padStart(3, "0");
  return `OC-${year}-${random}`;
}

export function getApiErrorMessage(error, fallback = "Ha ocurrido un error") {
  const detail = error?.response?.data?.detail;
  if (typeof detail === "string") {
    return detail;
  }
  if (Array.isArray(detail)) {
    return detail.map(d => d.msg || d.message || JSON.stringify(d)).join(", ");
  }
  if (typeof detail === "object" && detail !== null) {
    return detail.msg || detail.message || JSON.stringify(detail);
  }
  return fallback;
}
