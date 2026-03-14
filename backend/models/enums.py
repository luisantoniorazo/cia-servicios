from enum import Enum

class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"

class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    PENDING = "pending"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"
    TRIAL = "trial"

class ProjectStatus(str, Enum):
    QUOTATION = "quotation"
    AUTHORIZED = "authorized"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class ProjectPhase(str, Enum):
    NEGOTIATION = "negotiation"
    PURCHASES = "purchases"
    PROCESS = "process"
    DELIVERY = "delivery"

class QuoteStatus(str, Enum):
    PROSPECT = "prospect"
    NEGOTIATION = "negotiation"
    DETAILED_QUOTE = "detailed_quote"
    NEGOTIATING = "negotiating"
    UNDER_REVIEW = "under_review"
    AUTHORIZED = "authorized"
    DENIED = "denied"
    INVOICED = "invoiced"

class InvoiceStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    PARTIAL = "partial"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"

class PurchaseOrderStatus(str, Enum):
    REQUESTED = "requested"
    QUOTED = "quoted"
    APPROVED = "approved"
    ORDERED = "ordered"
    RECEIVED = "received"
    CANCELLED = "cancelled"

class ActivityType(str, Enum):
    LOGIN = "login"
    LOGOUT = "logout"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    VIEW = "view"
    EXPORT = "export"
    EMAIL = "email"
    PAYMENT = "payment"
    SUBSCRIPTION = "subscription"
    SYSTEM = "system"

class NotificationType(str, Enum):
    INFO = "info"
    WARNING = "warning"
    SUCCESS = "success"
    ERROR = "error"
    REMINDER = "reminder"
    PAYMENT = "payment"
    SYSTEM = "system"

class TicketPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class TicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"

class CFDIStatus(str, Enum):
    DRAFT = "draft"
    STAMPED = "stamped"
    CANCELLED = "cancelled"
    CANCELLATION_PENDING = "cancellation_pending"
