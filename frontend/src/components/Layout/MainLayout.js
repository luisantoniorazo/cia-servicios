import React, { useState } from "react";
import { Outlet } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { Toaster } from "../ui/sonner";
import { AppVersion } from "../AppVersion";

export const MainLayout = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <Sidebar isOpen={sidebarOpen} onToggle={() => setSidebarOpen(!sidebarOpen)} />
      
      <main className="lg:ml-64 flex-1 flex flex-col">
        <div className="p-4 lg:p-8 flex-1">
          <Outlet />
        </div>
        
        {/* Footer con versión */}
        <footer className="lg:ml-0 border-t border-slate-200 bg-white">
          <AppVersion className="text-slate-500" />
        </footer>
      </main>
      
      <Toaster position="top-right" richColors />
    </div>
  );
};

export default MainLayout;
