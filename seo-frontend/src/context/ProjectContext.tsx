import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';

interface ProjectContextType {
  projects: any[];
  auditResult: any;
  isAnalyzing: boolean;
  error: string | null;
  targetUrl: string;
  setTargetUrl: (url: string) => void;
  isShareModalOpen: boolean;
  setIsShareModalOpen: (open: boolean) => void;
  isGeneratingPDF: boolean;
  setIsGeneratingPDF: (generating: boolean) => void;
  activeSection: string;
  setActiveSection: (section: string) => void;
  fetchProjects: () => Promise<void>;
  loadProject: (id: string) => Promise<void>;
  startAudit: (url: string) => Promise<void>;
  resetAudit: () => void;
  setAuditResult: (result: any) => void;
  deleteProject: (id: string) => Promise<void>;
}

const ProjectContext = createContext<ProjectContextType | undefined>(undefined);

export const ProjectProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [projects, setProjects] = useState<any[]>([]);
  const [auditResult, setAuditResult] = useState<any>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [targetUrl, setTargetUrl] = useState('');
  const [isShareModalOpen, setIsShareModalOpen] = useState(false);
  const [isGeneratingPDF, setIsGeneratingPDF] = useState(false);
  const [activeSection, setActiveSection] = useState('summary');

  const fetchProjects = useCallback(async () => {
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      console.log('Fetching projects from:', `${apiUrl}/projects`);
      const response = await fetch(`${apiUrl}/projects`);
      console.log('Fetch response status:', response.status);
      if (response.ok) {
        const data = await response.json();
        console.log('Fetched projects count:', data.length);
        setProjects(data);
      }
    } catch (err) {
      console.error('Failed to fetch project history:', err);
    }
  }, []);

  const loadProject = useCallback(async (projectId: string) => {
    setIsAnalyzing(true);
    setError(null);
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/projects/${projectId}`);
      if (!response.ok) throw new Error('Failed to load project details');
      const data = await response.json();
      setAuditResult(data);
      setTargetUrl(data?.pdf_template_data?.website || '');
      setActiveSection('summary');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsAnalyzing(false);
    }
  }, []);

  const startAudit = useCallback(async (url: string) => {
    setIsAnalyzing(true);
    setError(null);
    setAuditResult(null);
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/analyze-url`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, business_type: 'general' }),
      });
      
      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'Analysis failed');
      }
      
      const data = await response.json();
      setAuditResult(data);
      setTargetUrl(url);
      setActiveSection('summary');
      fetchProjects(); // Refresh history
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsAnalyzing(false);
    }
  }, [fetchProjects]);

  const deleteProject = useCallback(async (projectId: string) => {
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const url = `${apiUrl}/projects/${projectId}`;
      console.log('Attempting to delete project at:', url);
      
      const response = await fetch(url, {
        method: 'DELETE',
      });
      if (response.ok) {
        setProjects(prev => prev.filter(p => p.id !== projectId));
      } else {
        let errorDetail = 'Failed to delete project';
        try {
          const data = await response.json();
          errorDetail = data.detail || errorDetail;
        } catch (e) {
          const text = await response.text();
          errorDetail = text || errorDetail;
        }
        throw new Error(errorDetail);
      }
    } catch (err: any) {
      console.error('Delete failed:', err);
      setError(err.message);
    }
  }, []);

  const resetAudit = useCallback(() => {
    setAuditResult(null);
    setError(null);
    setTargetUrl('');
    setActiveSection('summary');
  }, []);

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  return (
    <ProjectContext.Provider value={{
      projects,
      auditResult,
      isAnalyzing,
      error,
      targetUrl,
      setTargetUrl,
      isShareModalOpen,
      setIsShareModalOpen,
      isGeneratingPDF,
      setIsGeneratingPDF,
      activeSection,
      setActiveSection,
      fetchProjects,
      loadProject,
      startAudit,
      resetAudit,
      setAuditResult,
      deleteProject
    }}>
      {children}
    </ProjectContext.Provider>
  );
};

export const useProjects = () => {
  const context = useContext(ProjectContext);
  if (context === undefined) {
    throw new Error('useProjects must be used within a ProjectProvider');
  }
  return context;
};
