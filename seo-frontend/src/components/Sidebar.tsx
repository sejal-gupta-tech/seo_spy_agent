import React from 'react';
import { 
  ShieldCheck, 
  PanelLeftClose, 
  PanelLeftOpen, 
  LayoutDashboard, 
  FolderKanban, 
  RefreshCw, 
  Share2, 
  Download,
  X,
  Globe,
  ArrowRight,
  FileText,
  Cpu,
  TrendingUp,
  Zap,
  BookOpen
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useProjects } from '../context/ProjectContext';

interface SidebarProps {
  isSidebarCollapsed: boolean;
  setIsSidebarCollapsed: (collapsed: boolean) => void;
  isMobileSidebarOpen: boolean;
  setIsMobileSidebarOpen: (open: boolean) => void;
  projects: any[];
  loadProject: (id: string) => void;
  isDashboardActive: boolean;
  handleResetAudit: () => void;
  setIsShareModalOpen: (open: boolean) => void;
  handleDownloadPDF: () => void;
  isGeneratingPDF: boolean;
}

const Sidebar: React.FC<SidebarProps> = ({
  isSidebarCollapsed,
  setIsSidebarCollapsed,
  isMobileSidebarOpen,
  setIsMobileSidebarOpen,
  projects,
  loadProject,
  isDashboardActive,
  handleResetAudit,
  setIsShareModalOpen,
  handleDownloadPDF,
  isGeneratingPDF
}) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { activeSection, setActiveSection } = useProjects();

  const mainMenuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, path: '/' },
    { id: 'projects', label: 'All Projects', icon: FolderKanban, path: '/projects' },
  ];

  const dashboardTabs = [
    { id: 'summary', label: 'Summary', icon: FileText },
    { id: 'technical', label: 'Technical', icon: Cpu },
    { id: 'performance', label: 'Performance', icon: Zap },
    { id: 'growth', label: 'Growth', icon: TrendingUp },
    { id: 'appendix', label: 'Appendix', icon: BookOpen },
  ];

  return (
    <>
      {/* Desktop Sidebar */}
      <aside
        className={`hidden md:flex fixed left-0 top-0 bottom-0 bg-slate-900 text-white flex-col transition-all duration-300 z-50 ${isSidebarCollapsed ? 'w-20' : 'w-64'}`}
      >
        <div className="p-6 flex items-center justify-between border-b border-white/5 h-16">
          {!isSidebarCollapsed && (
            <div className="flex items-center gap-2 overflow-hidden whitespace-nowrap">
              <ShieldCheck className="w-6 h-6 text-indigo-400 shrink-0" />
              <span className="font-display font-bold text-lg tracking-tight">AuditIntel</span>
            </div>
          )}
          <button
            onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
            className={`p-2 hover:bg-white/10 rounded-lg transition-colors ${isSidebarCollapsed ? 'mx-auto' : ''}`}
          >
            {isSidebarCollapsed ? <PanelLeftOpen className="w-5 h-5 text-slate-400" /> : <PanelLeftClose className="w-5 h-5 text-slate-400" />}
          </button>
        </div>

        <div className="flex-1 px-3 py-4 space-y-2 overflow-y-auto custom-scrollbar">
          {/* 1. Main Navigation */}
          <div className="space-y-1">
            {mainMenuItems.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.id}
                  to={item.path}
                  className={`w-full flex items-center gap-3 px-3 py-3 rounded-xl font-bold transition-all group ${location.pathname === item.path
                    ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/20'
                    : 'text-slate-400 hover:bg-white/5 hover:text-white'
                  }`}
                >
                  <Icon className={`w-5 h-5 shrink-0 transition-transform ${location.pathname === item.path ? 'scale-110' : 'group-hover:scale-110'}`} />
                  {!isSidebarCollapsed && <span className="text-sm truncate">{item.label}</span>}
                </Link>
              );
            })}
          </div>

          {/* 2. Audit Sections */}
          <div className="mt-6 pt-6 border-t border-white/5 space-y-1">
            {!isSidebarCollapsed && <h4 className="text-[10px] font-black text-slate-500 uppercase tracking-widest px-3 mb-2">Audit Sections</h4>}
            {dashboardTabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => {
                    setActiveSection(tab.id);
                    navigate(`/${tab.id}`);
                  }}
                  className={`w-full flex items-center gap-3 px-3 py-3 rounded-xl font-bold transition-all group ${activeSection === tab.id && location.pathname === `/${tab.id}`
                    ? 'bg-white/10 text-white'
                    : 'text-slate-400 hover:bg-white/5 hover:text-white'
                  }`}
                >
                  <Icon className={`w-5 h-5 shrink-0 transition-transform ${activeSection === tab.id && location.pathname === `/${tab.id}` ? 'text-indigo-400 scale-110' : 'group-hover:scale-110'}`} />
                  {!isSidebarCollapsed && <span className="text-sm truncate">{tab.label}</span>}
                </button>
              );
            })}
          </div>

          {/* 3. Recent Audits */}
          {!isSidebarCollapsed && projects.length > 0 && (
            <div className="mt-6 pt-6 border-t border-white/5 space-y-4">
              <h4 className="text-[10px] font-black text-slate-500 uppercase tracking-widest px-3">Recent Audits</h4>
              <div className="space-y-1 max-h-[200px] overflow-y-auto scrollbar-thin scrollbar-thumb-white/10 pr-2">
                {projects.slice(0, 5).map((proj) => (
                  <button
                    key={proj.id}
                    onClick={() => loadProject(proj.id)}
                    className="w-full flex flex-col items-start px-3 py-2 rounded-lg hover:bg-white/5 transition-all group"
                  >
                    <span className="text-[11px] font-bold text-slate-300 truncate w-full group-hover:text-white transition-colors">{proj.url.replace(/^https?:\/\//, '')}</span>
                    <span className="text-[9px] text-slate-500 font-medium">{new Date(proj.created_at).toLocaleDateString()}</span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* 4. Action Buttons */}
        <div className="p-4 border-t border-white/5 space-y-2">
          {isDashboardActive && location.pathname === '/' && (
            <button
              onClick={handleResetAudit}
              className="w-full flex items-center gap-3 px-3 py-3 rounded-xl text-rose-400 hover:bg-rose-400/10 font-bold transition-all"
            >
              <RefreshCw className="w-5 h-5 shrink-0" />
              {!isSidebarCollapsed && <span className="text-sm">New Audit</span>}
            </button>
          )}
          {!isSidebarCollapsed && isDashboardActive && location.pathname === '/' && (
            <button
              onClick={() => setIsShareModalOpen(true)}
              className="w-full flex items-center gap-3 px-3 py-3 rounded-xl text-slate-400 hover:bg-white/5 hover:text-white font-bold transition-all overflow-hidden whitespace-nowrap"
            >
              <Share2 className="w-5 h-5 shrink-0" />
              <span className="text-sm">Share Report</span>
            </button>
          )}
          {isDashboardActive && location.pathname === '/' && (
            <button
              onClick={handleDownloadPDF}
              disabled={isGeneratingPDF}
              className={`w-full flex items-center gap-3 px-3 py-3 bg-white/5 hover:bg-white/10 rounded-xl transition-all border border-white/5 ${isSidebarCollapsed ? 'justify-center' : ''} ${isGeneratingPDF ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              <Download className={`w-5 h-5 shrink-0 text-indigo-400 ${isGeneratingPDF ? 'animate-bounce' : ''}`} />
              {!isSidebarCollapsed && <span className="text-sm font-bold">{isGeneratingPDF ? 'Generating...' : 'PDF Report'}</span>}
            </button>
          )}
        </div>
      </aside>

      {/* Mobile Sidebar Overlay */}
      <AnimatePresence>
        {isMobileSidebarOpen && (
          <div className="fixed inset-0 z-[100] md:hidden">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsMobileSidebarOpen(false)}
              className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm"
            />
            <motion.aside
              initial={{ x: '-100%' }}
              animate={{ x: 0 }}
              exit={{ x: '-100%' }}
              transition={{ type: 'spring', damping: 25, stiffness: 200 }}
              className="absolute left-0 top-0 bottom-0 w-72 bg-slate-900 text-white flex flex-col"
            >
              <div className="p-6 flex items-center justify-between border-b border-white/5">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="w-6 h-6 text-indigo-400" />
                  <span className="font-display font-bold text-lg tracking-tight">AuditIntelligence</span>
                </div>
                <button
                  onClick={() => setIsMobileSidebarOpen(false)}
                  className="p-2 hover:bg-white/10 rounded-lg transition-colors"
                >
                  <X className="w-5 h-5 text-slate-400" />
                </button>
              </div>
              <div className="flex-1 px-3 py-4 space-y-2 overflow-y-auto custom-scrollbar">
                {/* Main Navigation */}
                <div className="space-y-1">
                  {mainMenuItems.map((item) => (
                    <Link
                      key={item.id}
                      to={item.path}
                      onClick={() => setIsMobileSidebarOpen(false)}
                      className={`w-full flex items-center gap-3 px-3 py-3 rounded-xl font-bold transition-all ${location.pathname === item.path
                        ? 'bg-indigo-600 text-white'
                        : 'text-slate-400 hover:bg-white/5 hover:text-white'
                      }`}
                    >
                      <item.icon className="w-5 h-5" />
                      <span className="text-sm">{item.label}</span>
                    </Link>
                  ))}
                </div>

                {/* Audit Sections */}
                <div className="mt-4 pt-4 border-t border-white/5 space-y-1">
                  <h4 className="text-[10px] font-black text-slate-500 uppercase tracking-widest px-3 mb-2">Audit Sections</h4>
                  {dashboardTabs.map((tab) => {
                    const Icon = tab.icon;
                    return (
                      <button
                        key={tab.id}
                        onClick={() => {
                          setActiveSection(tab.id);
                          navigate(`/${tab.id}`);
                          setIsMobileSidebarOpen(false);
                        }}
                        className={`w-full flex items-center gap-3 px-3 py-3 rounded-xl font-bold transition-all ${activeSection === tab.id && location.pathname === `/${tab.id}`
                          ? 'bg-white/10 text-white'
                          : 'text-slate-400 hover:bg-white/5 hover:text-white'
                        }`}
                      >
                        <Icon className={`w-5 h-5 ${activeSection === tab.id && location.pathname === `/${tab.id}` ? 'text-indigo-400' : ''}`} />
                        <span className="text-sm">{tab.label}</span>
                      </button>
                    );
                  })}
                </div>

                {/* Recent Audits */}
                {projects.length > 0 && (
                  <div className="mt-4 pt-4 border-t border-white/5 space-y-4">
                    <h4 className="text-[10px] font-black text-slate-500 uppercase tracking-widest px-6">Recent Audits</h4>
                    <div className="space-y-2 px-3">
                      {projects.slice(0, 5).map((proj) => (
                        <button
                          key={proj.id}
                          onClick={() => {
                            loadProject(proj.id);
                            setIsMobileSidebarOpen(false);
                          }}
                          className="w-full flex items-center justify-between p-3 rounded-xl bg-white/5 hover:bg-white/10 transition-all border border-white/5"
                        >
                          <div className="flex flex-col items-start text-left">
                            <span className="text-xs font-bold text-white truncate max-w-[180px]">{proj.url.replace(/^https?:\/\//, '')}</span>
                            <span className="text-[10px] text-slate-500 font-medium">{new Date(proj.created_at).toLocaleDateString()}</span>
                          </div>
                          <ArrowRight className="w-4 h-4 text-slate-500" />
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </motion.aside>
          </div>
        )}
      </AnimatePresence>
    </>
  );
};

export default Sidebar;
