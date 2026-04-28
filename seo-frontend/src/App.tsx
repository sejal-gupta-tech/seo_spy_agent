import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import SEOStudio from './components/seo-studio';
import AuditDetails from './components/AuditDetails';

export default function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<SEOStudio />} />
        <Route path="/audit-details" element={<AuditDetails />} />
      </Routes>
    </Router>
  );
}
