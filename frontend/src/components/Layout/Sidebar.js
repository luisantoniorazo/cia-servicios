import React from "react";
import { NavLink, useNavigate, useParams } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { cn } from "../../lib/utils";
import {
  LayoutDashboard,
  FolderKanban,
  Users,
  FileText,
  Receipt,
  ShoppingCart,
  Building2,
  FileBox,
  ClipboardList,
  BarChart3,
  Sparkles,
  Settings,
  LogOut,
  ChevronLeft,
  Menu,
  Crown,
  TicketIcon,
} from "lucide-react";
import { Button } from "../ui/button";
import { ScrollArea } from "../ui/scroll-area";
import { Separator } from "../ui/separator";
import { Avatar, AvatarFallback } from "../ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "../ui/dropdown-menu";

const LOGO_URL = "https://customer-assets.emergentagent.com/job_cia-operacional/artifacts/0bkwa552_Logo%20CIA.jpg";

const menuItems = [
  { path: "/dashboard", label: "Dashboard", icon: LayoutDashboard, moduleId: "dashboard" },
  { path: "/projects", label: "Proyectos", icon: FolderKanban, moduleId: "projects" },
  { path: "/crm", label: "CRM", icon: Users, moduleId: "crm" },
  { path: "/quotes", label: "Cotizaciones", icon: FileText, moduleId: "quotes" },
  { path: "/invoices", label: "Facturación", icon: Receipt, moduleId: "invoices" },
  { path: "/purchases", label: "Compras", icon: ShoppingCart, moduleId: "purchases" },
  { path: "/suppliers", label: "Proveedores", icon: Building2, moduleId: "suppliers" },
  { path: "/documents", label: "Documentos", icon: FileBox, moduleId: "documents" },
  { path: "/field-reports", label: "Reportes de Campo", icon: ClipboardList, moduleId: "field-reports" },
  { path: "/kpis", label: "Indicadores", icon: BarChart3, moduleId: "kpis" },
  { path: "/intelligence", label: "Inteligencia IA", icon: Sparkles, moduleId: "intelligence" },
  { path: "/tickets", label: "Soporte", icon: TicketIcon, moduleId: "tickets" },
  { path: "/settings", label: "Configuración", icon: Settings, moduleId: "settings" },
];

export const Sidebar = ({ isOpen, onToggle }) => {
  const { user, company, logout, isSuperAdmin, companySlug } = useAuth();
  const navigate = useNavigate();
  const { slug } = useParams();
  
  // Use slug from URL params or from auth context
  const currentSlug = slug || companySlug;
  const basePath = `/empresa/${currentSlug}`;

  const handleLogout = () => {
    logout();
    if (currentSlug) {
      navigate(`/empresa/${currentSlug}/login`);
    } else {
      navigate("/");
    }
  };

  const getInitials = (name) => {
    if (!name) return "U";
    return name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);
  };

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-30 lg:hidden"
          onClick={onToggle}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          "fixed left-0 top-0 z-40 h-screen bg-slate-900 transition-transform duration-300 lg:translate-x-0",
          isOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0",
          "w-64"
        )}
        data-testid="sidebar"
      >
        <div className="flex h-full flex-col">
          {/* Logo */}
          <div className="flex items-center justify-between p-4 border-b border-slate-800">
            <div className="flex items-center gap-3">
              <img src={LOGO_URL} alt="CIA" className="h-10 w-auto" />
              <div className="flex flex-col">
                <span className="text-white font-bold text-sm font-[Chivo]">CIA SERVICIOS</span>
                <span className="text-slate-400 text-xs">Control Integral</span>
              </div>
            </div>
            <Button
              variant="ghost"
              size="icon"
              className="lg:hidden text-slate-400 hover:text-white"
              onClick={onToggle}
            >
              <ChevronLeft className="h-5 w-5" />
            </Button>
          </div>

          {/* Company info */}
          {company && (
            <div className="p-4 border-b border-slate-800">
              <div className="flex items-center gap-2 text-slate-300">
                <Building2 className="h-4 w-4" />
                <span className="text-sm truncate">{company.business_name}</span>
              </div>
            </div>
          )}

          {/* Navigation */}
          <ScrollArea className="flex-1 py-4">
            <nav className="px-3 space-y-1">
              {isSuperAdmin() && (
                <>
                  <NavLink
                    to="/admin-portal/dashboard"
                    className={({ isActive }) =>
                      cn("sidebar-item", isActive && "sidebar-item-active")
                    }
                    data-testid="nav-super-admin"
                  >
                    <Crown className="h-5 w-5" />
                    <span>Super Admin</span>
                  </NavLink>
                  <Separator className="my-3 bg-slate-800" />
                </>
              )}
              
              {menuItems
                .filter((item) => {
                  // If user has module_permissions, filter by them
                  // If null/undefined, show all modules (admin default)
                  if (!user?.module_permissions) return true;
                  return user.module_permissions.includes(item.moduleId);
                })
                .map((item) => (
                <NavLink
                  key={item.path}
                  to={`${basePath}${item.path}`}
                  className={({ isActive }) =>
                    cn("sidebar-item", isActive && "sidebar-item-active")
                  }
                  data-testid={`nav-${item.path.slice(1)}`}
                >
                  <item.icon className="h-5 w-5" />
                  <span>{item.label}</span>
                </NavLink>
              ))}
            </nav>
          </ScrollArea>

          {/* User menu */}
          <div className="p-4 border-t border-slate-800">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  className="w-full justify-start gap-3 text-slate-300 hover:text-white hover:bg-slate-800"
                  data-testid="user-menu-trigger"
                >
                  <Avatar className="h-8 w-8">
                    <AvatarFallback className="bg-primary text-white text-xs">
                      {getInitials(user?.full_name)}
                    </AvatarFallback>
                  </Avatar>
                  <div className="flex flex-col items-start text-left">
                    <span className="text-sm font-medium truncate max-w-[140px]">
                      {user?.full_name}
                    </span>
                    <span className="text-xs text-slate-400 truncate max-w-[140px]">
                      {user?.email}
                    </span>
                  </div>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                <DropdownMenuLabel>Mi Cuenta</DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => navigate(`${basePath}/settings`)}>
                  <Settings className="mr-2 h-4 w-4" />
                  Configuración
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleLogout} className="text-red-600">
                  <LogOut className="mr-2 h-4 w-4" />
                  Cerrar Sesión
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </aside>

      {/* Mobile menu button */}
      <Button
        variant="ghost"
        size="icon"
        className="fixed top-4 left-4 z-50 lg:hidden bg-white shadow-md"
        onClick={onToggle}
        data-testid="mobile-menu-btn"
      >
        <Menu className="h-5 w-5" />
      </Button>
    </>
  );
};

export default Sidebar;
