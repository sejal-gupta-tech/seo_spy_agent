import React, { useEffect, useState, useMemo } from 'react';
import {
  Globe, Search, Calendar, ExternalLink, BarChart3, RefreshCw,
  Shield, FileText, Layers, CheckCircle2, XCircle, Clock, Filter,
  ChevronLeft, ChevronRight, ArrowUpDown, TrendingUp, AlertTriangle, Trash2
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { useProjects } from '../context/ProjectContext';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// ── helpers ──────────────────────────────────────────────────────────────────
const scoreFg = (s: number) =>
  s >= 80 ? '#10b981' : s >= 50 ? '#f59e0b' : '#ef4444';

const scoreLabel = (s: number) =>
  s >= 80 ? 'Good' : s >= 50 ? 'Needs Work' : s > 0 ? 'Critical' : 'No Data';

const scoreLabelCss = (s: number) =>
  s >= 80 ? 'bg-emerald-100 text-emerald-700'
    : s >= 50 ? 'bg-amber-100 text-amber-700'
    : s > 0 ? 'bg-rose-100 text-rose-700'
    : 'bg-slate-100 text-slate-500';

const PAGE_SIZE = 12;

// ── mini SVG gauge ────────────────────────────────────────────────────────────
const MiniGauge: React.FC<{ score: number }> = ({ score }) => {
  const r = 24, circ = 2 * Math.PI * r;
  const dash = circ * ((score || 0) / 100);
  const color = scoreFg(score || 0);
  return (
    <div className="relative flex items-center justify-center w-16 h-16">
      <svg width="64" height="64" viewBox="0 0 64 64" className="absolute inset-0">
        <circle cx="32" cy="32" r={r} fill="none" stroke="#e2e8f0" strokeWidth="5" />
        <circle cx="32" cy="32" r={r} fill="none" stroke={color} strokeWidth="5"
          strokeDasharray={`${dash} ${circ}`} strokeLinecap="round"
          transform="rotate(-90 32 32)"
          style={{ transition: 'stroke-dasharray 0.8s ease' }} />
      </svg>
      <span className="text-xs font-black relative z-10" style={{ color }}>{score || 0}</span>
    </div>
  );
};

// ── stat chip ─────────────────────────────────────────────────────────────────
const Chip: React.FC<{ icon: React.ReactNode; label: string; value: string | number }> = ({ icon, label, value }) => (
  <div className="flex items-center gap-1.5 text-xs text-slate-500">
    <span className="text-slate-400">{icon}</span>
    <span className="font-medium text-slate-700">{String(value)}</span>
    <span>{label}</span>
  </div>
);

// ── status dot ────────────────────────────────────────────────────────────────
const StatusDot: React.FC<{ value: string; label: string }> = ({ value, label }) => {
  const ok = value && !['missing', 'error', '—', '0'].includes(value.toLowerCase());
  return (
    <div className="flex items-center gap-1 text-xs">
      {ok
        ? <CheckCircle2 className="w-3 h-3 text-emerald-500" />
        : <XCircle className="w-3 h-3 text-rose-400" />}
      <span className={ok ? 'text-emerald-700 font-medium' : 'text-rose-500'}>{label}</span>
    </div>
  );
};

// ── project card ──────────────────────────────────────────────────────────────
const ProjectCard: React.FC<{ proj: any; idx: number }> = ({ proj, idx }) => {
  const navigate = useNavigate();
  const { deleteProject } = useProjects();
  const score = proj.seo_score ?? 0;
  const domain = (proj.url || '').replace(/^https?:\/\//, '').replace(/\/$/, '');
  const date = proj.created_at ? new Date(proj.created_at).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }) : '—';

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: (idx % PAGE_SIZE) * 0.03 }}
      onClick={() => navigate(`/projects/${proj.id}`)}
      className="group bg-white rounded-2xl border border-slate-200 shadow-sm hover:shadow-lg hover:shadow-slate-200/60 hover:-translate-y-0.5 transition-all cursor-pointer overflow-hidden flex flex-col"
    >
      {/* ── top bar with score colour ── */}
      <div
        className="h-1.5 w-full"
        style={{ background: `linear-gradient(90deg, ${scoreFg(score)}, ${scoreFg(score)}88)` }}
      />

      {/* ── header ── */}
      <div className="px-5 pt-4 pb-3 flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 mb-0.5">
            <div className="w-7 h-7 bg-indigo-50 rounded-lg flex items-center justify-center shrink-0 group-hover:bg-indigo-100 transition-colors">
              <Globe className="w-3.5 h-3.5 text-indigo-600" />
            </div>
            <h3 className="font-bold text-slate-800 text-sm truncate" title={proj.url}>{domain}</h3>
          </div>
          <div className="flex items-center gap-1.5 ml-9 text-xs text-slate-400">
            <Calendar className="w-3 h-3" />
            <span>{date}</span>
            {proj.business_type && proj.business_type !== 'General' && (
              <>
                <span className="text-slate-200">·</span>
                <span className="capitalize">{proj.business_type}</span>
              </>
            )}
          </div>
        </div>
        <MiniGauge score={score} />
      </div>

      <div className="mx-5 border-t border-slate-100" />

      {/* ── score badge + health label ── */}
      <div className="px-5 py-3 flex items-center justify-between">
        <div className="flex items-baseline gap-1">
          <span className="text-2xl font-black" style={{ color: scoreFg(score) }}>{score}%</span>
          <span className="text-xs text-slate-400 font-medium">SEO score</span>
        </div>
        <span className={`text-xs font-bold px-2.5 py-1 rounded-full ${scoreLabelCss(score)}`}>
          {scoreLabel(score)}
        </span>
      </div>

      {/* ── stats grid ── */}
      <div className="px-5 pb-3 grid grid-cols-2 gap-x-4 gap-y-2">
        <Chip icon={<Layers className="w-3 h-3" />} label="pages crawled" value={proj.pages_analyzed ?? 0} />
        <Chip icon={<Search className="w-3 h-3" />} label="discovered" value={proj.pages_discovered ?? 0} />
        <Chip icon={<Shield className="w-3 h-3" />} label="findings" value={proj.findings_count ?? 0} />
        <Chip icon={<BarChart3 className="w-3 h-3" />} label="metrics" value={proj.metrics_count ?? 0} />
      </div>

      {/* ── robots / sitemap status ── */}
      <div className="px-5 pb-3 flex items-center gap-4">
        <StatusDot value={proj.robots_status ?? ''} label="Robots.txt" />
        <StatusDot value={proj.sitemap_status ?? ''} label="Sitemap" />
      </div>

      {/* ── report url ── */}
      {proj.report_url && (
        <div className="px-5 pb-2">
          <span className="text-xs text-indigo-500 font-medium truncate block">
            📄 Report available
          </span>
        </div>
      )}

      {/* ── footer actions ── */}
      <div className="px-5 pb-4 mt-auto pt-2 flex gap-2 border-t border-slate-100">
        <button
          onClick={e => { e.stopPropagation(); navigate(`/projects/${proj.id}`); }}
          className="flex-1 flex items-center justify-center gap-1.5 py-2.5 bg-slate-900 hover:bg-indigo-600 text-white rounded-xl font-bold text-xs transition-all active:scale-95"
        >
          <BarChart3 className="w-3.5 h-3.5" />
          View Full Report
        </button>
        <a
          href={proj.url} target="_blank" rel="noreferrer"
          onClick={e => e.stopPropagation()}
          className="p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-400 hover:text-indigo-600 hover:border-indigo-200 transition-all"
        >
          <ExternalLink className="w-4 h-4" />
        </a>
        <button
          onClick={e => {
            e.stopPropagation();
            if (window.confirm(`Are you sure you want to delete the audit for ${domain}?`)) {
              deleteProject(proj.id);
            }
          }}
          className="p-2.5 bg-rose-50 border border-rose-100 rounded-xl text-rose-400 hover:text-rose-600 hover:bg-rose-100 hover:border-rose-200 transition-all"
          title="Delete Project"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
    </motion.div>
  );
};

// ── main page ─────────────────────────────────────────────────────────────────
const ProjectsPage: React.FC = () => {
  const { projects, fetchProjects, error, resetAudit } = useProjects();
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');
  const [sortBy, setSortBy] = useState<'date' | 'score'>('date');
  const [filterScore, setFilterScore] = useState<'all' | 'good' | 'needs_work' | 'critical' | 'no_data'>('all');
  const [page, setPage] = useState(1);

  const handleRefresh = async () => {
    setLoading(true);
    await fetchProjects();
    setLoading(false);
  };

  useEffect(() => {
    if (projects.length === 0) {
      handleRefresh();
    }
  }, []);

  // Reset page when filters change
  useEffect(() => { setPage(1); }, [search, sortBy, filterScore]);

  const filtered = useMemo(() => {
    let list = projects.filter(p =>
      (p.url || '').toLowerCase().includes(search.toLowerCase())
    );
    if (filterScore !== 'all') {
      list = list.filter(p => {
        const s = p.seo_score ?? 0;
        if (filterScore === 'good') return s >= 80;
        if (filterScore === 'needs_work') return s >= 50 && s < 80;
        if (filterScore === 'critical') return s > 0 && s < 50;
        if (filterScore === 'no_data') return s === 0;
        return true;
      });
    }
    if (sortBy === 'score') {
      list = [...list].sort((a, b) => (b.seo_score ?? 0) - (a.seo_score ?? 0));
    }
    return list;
  }, [projects, search, sortBy, filterScore]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const paginated = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  // Stats for banner
  const avgScore = projects.length
    ? Math.round(projects.reduce((s, p) => s + (p.seo_score ?? 0), 0) / projects.length)
    : 0;
  const goodCount = projects.filter(p => (p.seo_score ?? 0) >= 80).length;
  const critCount = projects.filter(p => (p.seo_score ?? 0) > 0 && (p.seo_score ?? 0) < 50).length;

  return (
    <div className="min-h-screen bg-slate-50/60">
      {/* ── header banner ── */}
      <div className="bg-gradient-to-r from-slate-900 to-indigo-900 px-8 py-8">
        <h1 className="text-3xl font-display font-bold text-white mb-1">Project Repository</h1>
        <p className="text-indigo-300 text-sm mb-6">All {projects.length} audited websites from your database</p>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: 'Total Projects', value: projects.length, icon: <Layers className="w-4 h-4" />, color: 'text-white' },
            { label: 'Average Score', value: `${avgScore}%`, icon: <TrendingUp className="w-4 h-4" />, color: 'text-emerald-400' },
            { label: 'Good (80%+)', value: goodCount, icon: <CheckCircle2 className="w-4 h-4" />, color: 'text-emerald-400' },
            { label: 'Critical (<50%)', value: critCount, icon: <AlertTriangle className="w-4 h-4" />, color: 'text-rose-400' },
          ].map(stat => (
            <div key={stat.label} className="bg-white/10 rounded-2xl px-4 py-3 backdrop-blur-sm">
              <div className={`flex items-center gap-1.5 ${stat.color} mb-1`}>{stat.icon}
                <span className="text-xs font-medium opacity-80">{stat.label}</span>
              </div>
              <p className={`text-2xl font-black ${stat.color}`}>{stat.value}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-6">
        {/* ── error display ── */}
        {error && (
          <div className="mb-6 p-4 bg-rose-50 border border-rose-200 rounded-2xl flex items-center gap-3 text-rose-700 animate-in fade-in slide-in-from-top-2">
            <AlertTriangle className="w-5 h-5 shrink-0" />
            <div className="flex-1">
              <p className="text-sm font-bold">Error Occurred</p>
              <p className="text-xs opacity-80">{error}</p>
            </div>
            <button 
              onClick={() => resetAudit()} 
              className="px-3 py-1 bg-white border border-rose-200 rounded-lg text-[10px] font-black uppercase hover:bg-rose-100 transition-colors"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* ── toolbar ── */}
        <div className="flex flex-wrap items-center gap-3 mb-6">
          {/* search */}
          <div className="relative flex-1 min-w-48">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              value={search} onChange={e => setSearch(e.target.value)}
              placeholder="Search by URL…"
              className="w-full pl-9 pr-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-transparent"
            />
          </div>

          {/* score filter */}
          <select
            value={filterScore}
            onChange={e => setFilterScore(e.target.value as any)}
            className="px-3 py-2.5 bg-white border border-slate-200 rounded-xl text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 cursor-pointer"
          >
            <option value="all">All Scores</option>
            <option value="good">Good (80%+)</option>
            <option value="needs_work">Needs Work (50-79%)</option>
            <option value="critical">Critical (&lt;50%)</option>
            <option value="no_data">No Score Data</option>
          </select>

          {/* sort */}
          <button
            onClick={() => setSortBy(s => s === 'date' ? 'score' : 'date')}
            className="flex items-center gap-2 px-3 py-2.5 bg-white border border-slate-200 rounded-xl text-sm shadow-sm hover:bg-slate-50 transition-colors"
          >
            <ArrowUpDown className="w-4 h-4 text-slate-400" />
            Sort: {sortBy === 'date' ? 'Newest first' : 'Highest score'}
          </button>

          {/* refresh */}
          <button onClick={handleRefresh}
            className="flex items-center gap-2 px-3 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-sm font-medium shadow-sm transition-colors">
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>

        {/* ── results count ── */}
        {!loading && (
          <p className="text-sm text-slate-500 mb-4">
            Showing <span className="font-bold text-slate-800">{paginated.length}</span> of{' '}
            <span className="font-bold text-slate-800">{filtered.length}</span> projects
            {search && ` matching "${search}"`}
            {filterScore !== 'all' && ` · filtered`}
          </p>
        )}

        {/* ── grid ── */}
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {[...Array(PAGE_SIZE)].map((_, i) => (
              <div key={i} className="bg-white rounded-2xl border border-slate-200 h-72 animate-pulse" />
            ))}
          </div>
        ) : paginated.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            <AnimatePresence mode="popLayout">
              {paginated.map((proj, idx) => (
                <ProjectCard key={proj.id} proj={proj} idx={idx} />
              ))}
            </AnimatePresence>
          </div>
        ) : (
          <div className="py-24 flex flex-col items-center text-center">
            <div className="w-20 h-20 bg-slate-100 rounded-full flex items-center justify-center mb-5">
              <Search className="w-10 h-10 text-slate-300" />
            </div>
            <h3 className="text-xl font-bold text-slate-700 mb-2">No projects found</h3>
            <p className="text-slate-500 text-sm">{search ? `No URL matches "${search}"` : 'Try a different filter.'}</p>
          </div>
        )}

        {/* ── pagination ── */}
        {totalPages > 1 && !loading && (
          <div className="flex items-center justify-center gap-2 mt-10">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="p-2 bg-white border border-slate-200 rounded-xl text-slate-500 hover:text-indigo-600 hover:border-indigo-200 disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-sm"
            >
              <ChevronLeft className="w-5 h-5" />
            </button>

            {Array.from({ length: totalPages }, (_, i) => i + 1)
              .filter(n => n === 1 || n === totalPages || Math.abs(n - page) <= 2)
              .reduce((acc: (number | '…')[], n, i, arr) => {
                if (i > 0 && n - (arr[i - 1] as number) > 1) acc.push('…');
                acc.push(n);
                return acc;
              }, [])
              .map((n, i) =>
                n === '…' ? (
                  <span key={`ellipsis-${i}`} className="px-2 text-slate-400 text-sm">…</span>
                ) : (
                  <button
                    key={n}
                    onClick={() => setPage(n as number)}
                    className={`w-10 h-10 rounded-xl text-sm font-bold transition-all shadow-sm ${
                      page === n
                        ? 'bg-indigo-600 text-white shadow-indigo-200'
                        : 'bg-white border border-slate-200 text-slate-600 hover:border-indigo-200 hover:text-indigo-600'
                    }`}
                  >
                    {n}
                  </button>
                )
              )}

            <button
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="p-2 bg-white border border-slate-200 rounded-xl text-slate-500 hover:text-indigo-600 hover:border-indigo-200 disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-sm"
            >
              <ChevronRight className="w-5 h-5" />
            </button>

            <span className="ml-3 text-sm text-slate-400">
              Page {page} of {totalPages}
            </span>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProjectsPage;
