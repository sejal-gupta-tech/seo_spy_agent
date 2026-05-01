import React, { useState } from 'react';
import { Outlet, useNavigate } from 'react-router-dom';
import Sidebar from './Sidebar';
import { useProjects } from '../context/ProjectContext';
import { ShieldCheck, Menu } from 'lucide-react';

const MainLayout: React.FC = () => {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);
  const { 
    projects, 
    loadProject, 
    auditResult, 
    resetAudit, 
    isAnalyzing,
    isShareModalOpen,
    setIsShareModalOpen,
    isGeneratingPDF
  } = useProjects();
  const navigate = useNavigate();

  const handleLoadProject = async (id: string) => {
    await loadProject(id);
    navigate('/');
  };

  const handleReset = () => {
    resetAudit();
    navigate('/');
  };

  return (
    <div className="min-h-screen bg-slate-50 flex">
      <Sidebar
        isSidebarCollapsed={isSidebarCollapsed}
        setIsSidebarCollapsed={setIsSidebarCollapsed}
        isMobileSidebarOpen={isMobileSidebarOpen}
        setIsMobileSidebarOpen={setIsMobileSidebarOpen}
        projects={projects}
        loadProject={handleLoadProject}
        isDashboardActive={!!auditResult}
        handleResetAudit={handleReset}
        setIsShareModalOpen={setIsShareModalOpen}
        handleDownloadPDF={() => {
          // Trigger download in SEOStudio via an event or shared state if possible
          // For now, we'll assume SEOStudio will handle its own download button
          // but we provide the state to the Sidebar for consistency.
        }}
        isGeneratingPDF={isGeneratingPDF}
      />
      
      <div className="flex-1 flex flex-col min-w-0">
        {/* Mobile Header */}
        <header className="md:hidden sticky top-0 z-40 bg-white/80 backdrop-blur-xl border-b border-slate-200 px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-6 h-6 text-indigo-600" />
            <span className="font-display font-bold text-lg text-slate-800 tracking-tight">AuditIntelligence</span>
          </div>
          <button
            onClick={() => setIsMobileSidebarOpen(true)}
            className="p-2 hover:bg-slate-100 rounded-lg transition-colors border border-slate-200"
          >
            <Menu className="w-5 h-5 text-slate-600" />
          </button>
        </header>

        <main className={`flex-1 transition-all duration-300 ${isSidebarCollapsed ? 'md:pl-20' : 'md:pl-64'}`}>
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default MainLayout;
