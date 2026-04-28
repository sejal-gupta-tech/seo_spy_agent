import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { ArrowLeft, Database } from 'lucide-react';
import { PageAnalysisCards } from './seo-studio';

export default function AuditDetails() {
  const location = useLocation();
  const navigate = useNavigate();
  
  // Accept both 'page' or 'pages' depending on how it was passed
  const rawData = location.state?.page || location.state?.pages || [];
  const pages = Array.isArray(rawData) ? rawData : [rawData];

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header Bar */}
      <div className="bg-white border-b border-slate-200 sticky top-0 z-50 px-6 py-4 flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-4">
          <button 
            onClick={() => navigate(-1)}
            className="p-2 hover:bg-slate-100 rounded-full transition-colors group"
          >
            <ArrowLeft className="w-5 h-5 text-slate-500 group-hover:text-slate-900" />
          </button>
          <div>
            <h1 className="text-xl font-black text-slate-900 flex items-center gap-2">
              <Database className="w-5 h-5 text-indigo-600" />
              Full Page-Wise SEO Details
            </h1>
            <p className="text-xs font-bold text-slate-500 uppercase tracking-widest mt-1">Deep Dive Audit View</p>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-6xl mx-auto p-6 pt-8">
        {pages.length > 0 ? (
          <PageAnalysisCards pages={pages} />
        ) : (
          <div className="flex flex-col items-center justify-center py-20 bg-white rounded-3xl border border-slate-200 shadow-sm">
            <Database className="w-12 h-12 text-slate-300 mb-4" />
            <h3 className="text-lg font-black text-slate-900 mb-2">No audit data available</h3>
            <p className="text-sm text-slate-500 text-center max-w-md">
              We couldn't find any detailed page data for this audit. Return to the dashboard and try running a new scan.
            </p>
            <button 
              onClick={() => navigate(-1)}
              className="mt-6 px-6 py-3 bg-indigo-600 text-white rounded-xl text-xs font-black uppercase tracking-widest shadow-lg shadow-indigo-200 hover:bg-indigo-700 transition-all active:scale-95"
            >
              Back to Dashboard
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
