import React, { useState, useEffect } from "react";
import { Badge } from "./ui/badge";
import { Info } from "lucide-react";

// App version - update this with each release
export const APP_VERSION = "1.1.0";
export const BUILD_DATE = "2026-04-07";

export const AppVersion = ({ className = "" }) => {
  return (
    <div className={`flex items-center justify-center gap-2 text-xs text-slate-400 py-2 ${className}`}>
      <Info className="h-3 w-3" />
      <span>CIA Servicios v{APP_VERSION}</span>
    </div>
  );
};

export const AppVersionBadge = ({ onClick }) => {
  return (
    <Badge 
      variant="outline" 
      className="text-xs cursor-pointer hover:bg-slate-700 transition-colors border-slate-600 text-slate-400"
      onClick={onClick}
    >
      v{APP_VERSION}
    </Badge>
  );
};

export default AppVersion;
