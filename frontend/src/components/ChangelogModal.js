import React, { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "./ui/dialog";
import { Badge } from "./ui/badge";
import { ScrollArea } from "./ui/scroll-area";
import { Separator } from "./ui/separator";
import { 
  Sparkles, 
  Bug, 
  Wrench, 
  Shield, 
  Zap,
  Calendar,
  Tag
} from "lucide-react";

// Changelog data - update this with each release
export const CHANGELOG_DATA = [
  {
    version: "1.0.0",
    date: "2026-04-06",
    title: "Lanzamiento Inicial en Producción",
    description: "Primera versión estable del sistema CIA Servicios desplegada en servidor de producción.",
    changes: [
      {
        type: "feature",
        description: "Sistema completo de CRM con gestión de clientes y contactos"
      },
      {
        type: "feature", 
        description: "Módulo de cotizaciones con generación de PDF personalizado"
      },
      {
        type: "feature",
        description: "Facturación integrada con Facturama (CFDI 4.0)"
      },
      {
        type: "feature",
        description: "Gestión de proyectos con diagrama de Gantt"
      },
      {
        type: "feature",
        description: "Portal de Super Administrador para gestión de licencias"
      },
      {
        type: "feature",
        description: "Sistema de tickets de soporte con IA"
      },
      {
        type: "feature",
        description: "Dashboard con indicadores KPI en tiempo real"
      },
      {
        type: "feature",
        description: "Módulo de inteligencia artificial para análisis de datos"
      },
      {
        type: "feature",
        description: "Sistema de suscripciones y pagos con Stripe"
      },
      {
        type: "security",
        description: "Autenticación JWT con roles y permisos"
      },
      {
        type: "security",
        description: "Multi-tenancy completo con aislamiento de datos"
      }
    ]
  }
];

const getChangeIcon = (type) => {
  switch (type) {
    case "feature":
      return <Sparkles className="h-4 w-4 text-emerald-400" />;
    case "fix":
      return <Bug className="h-4 w-4 text-amber-400" />;
    case "improvement":
      return <Wrench className="h-4 w-4 text-blue-400" />;
    case "security":
      return <Shield className="h-4 w-4 text-purple-400" />;
    case "performance":
      return <Zap className="h-4 w-4 text-yellow-400" />;
    default:
      return <Tag className="h-4 w-4 text-slate-400" />;
  }
};

const getChangeLabel = (type) => {
  switch (type) {
    case "feature":
      return "Nueva función";
    case "fix":
      return "Corrección";
    case "improvement":
      return "Mejora";
    case "security":
      return "Seguridad";
    case "performance":
      return "Rendimiento";
    default:
      return "Cambio";
  }
};

const getChangeBadgeColor = (type) => {
  switch (type) {
    case "feature":
      return "bg-emerald-500/20 text-emerald-300 border-emerald-500/30";
    case "fix":
      return "bg-amber-500/20 text-amber-300 border-amber-500/30";
    case "improvement":
      return "bg-blue-500/20 text-blue-300 border-blue-500/30";
    case "security":
      return "bg-purple-500/20 text-purple-300 border-purple-500/30";
    case "performance":
      return "bg-yellow-500/20 text-yellow-300 border-yellow-500/30";
    default:
      return "bg-slate-500/20 text-slate-300 border-slate-500/30";
  }
};

export const ChangelogModal = ({ open, onOpenChange }) => {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px] max-h-[80vh] bg-slate-900 border-slate-700">
        <DialogHeader>
          <DialogTitle className="text-white flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-amber-500" />
            Historial de Cambios
          </DialogTitle>
          <DialogDescription className="text-slate-400">
            Novedades y actualizaciones del sistema CIA Servicios
          </DialogDescription>
        </DialogHeader>
        
        <ScrollArea className="max-h-[60vh] pr-4">
          <div className="space-y-6">
            {CHANGELOG_DATA.map((release, idx) => (
              <div key={release.version} className="space-y-3">
                {idx > 0 && <Separator className="bg-slate-700" />}
                
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Badge className="bg-amber-500/20 text-amber-300 border-amber-500/30 text-sm font-mono">
                      v{release.version}
                    </Badge>
                    <h3 className="text-white font-semibold">{release.title}</h3>
                  </div>
                  <div className="flex items-center gap-1 text-xs text-slate-500">
                    <Calendar className="h-3 w-3" />
                    {new Date(release.date).toLocaleDateString('es-MX', { 
                      year: 'numeric', 
                      month: 'short', 
                      day: 'numeric' 
                    })}
                  </div>
                </div>
                
                {release.description && (
                  <p className="text-sm text-slate-400">{release.description}</p>
                )}
                
                <div className="space-y-2 pl-2">
                  {release.changes.map((change, changeIdx) => (
                    <div 
                      key={changeIdx} 
                      className="flex items-start gap-3 p-2 rounded-lg bg-slate-800/50 hover:bg-slate-800 transition-colors"
                    >
                      <div className="mt-0.5">
                        {getChangeIcon(change.type)}
                      </div>
                      <div className="flex-1">
                        <p className="text-sm text-slate-300">{change.description}</p>
                      </div>
                      <Badge 
                        variant="outline" 
                        className={`text-[10px] ${getChangeBadgeColor(change.type)}`}
                      >
                        {getChangeLabel(change.type)}
                      </Badge>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
};

export default ChangelogModal;
