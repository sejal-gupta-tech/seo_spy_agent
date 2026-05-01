import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import SEOStudio from './components/seo-studio';
import AuditDetails from './components/AuditDetails';
import ProjectsPage from './components/ProjectsPage';
import ProjectDetailPage from './components/ProjectDetailPage';
import MainLayout from './components/MainLayout';
import { ProjectProvider } from './context/ProjectContext';

export default function App() {
  return (
    <ProjectProvider>
      <Router>
        <Routes>
          <Route element={<MainLayout />}>
            <Route path="/" element={<SEOStudio />} />
            <Route path="/:section" element={<SEOStudio />} />
            <Route path="/projects" element={<ProjectsPage />} />
            <Route path="/projects/:id" element={<ProjectDetailPage />} />
            <Route path="/audit-details" element={<AuditDetails />} />
          </Route>
        </Routes>
      </Router>
    </ProjectProvider>
  );
}
