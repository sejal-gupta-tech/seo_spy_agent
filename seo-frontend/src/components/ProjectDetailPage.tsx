import React, { useEffect, useState } from 'react';

// Safely convert anything to a displayable string
const safeStr = (v: any): string => {
  if (v === null || v === undefined) return '—';
  if (typeof v === 'string') return v;
  if (typeof v === 'number' || typeof v === 'boolean') return String(v);
  if (Array.isArray(v)) return v.map(safeStr).join(', ');
  if (typeof v === 'object') return JSON.stringify(v);
  return String(v);
};
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft, Globe, Shield, Zap, TrendingUp, Search, Link2, FileText,
  CheckCircle, AlertCircle, XCircle, Clock, BarChart3, Target, Lightbulb,
  ChevronDown, ChevronUp, ExternalLink, Cpu, BookOpen, Map
} from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// ── helpers ──────────────────────────────────────────────────────────────────
const scoreColor = (s: number) =>
  s >= 80 ? 'text-emerald-600' : s >= 50 ? 'text-amber-500' : 'text-rose-500';
const scoreBg = (s: number) =>
  s >= 80 ? 'bg-emerald-50 border-emerald-200' : s >= 50 ? 'bg-amber-50 border-amber-200' : 'bg-rose-50 border-rose-200';
const scoreRing = (s: number) =>
  s >= 80 ? '#10b981' : s >= 50 ? '#f59e0b' : '#ef4444';
const priorityBadge = (p: string) =>
  p === 'High' ? 'bg-rose-100 text-rose-700 border-rose-200'
    : p === 'Medium' ? 'bg-amber-100 text-amber-700 border-amber-200'
    : 'bg-slate-100 text-slate-600 border-slate-200';
const statusIcon = (s: string) =>
  s === 'Good' ? <CheckCircle className="w-4 h-4 text-emerald-500" />
    : s === 'At Benchmark' ? <CheckCircle className="w-4 h-4 text-sky-500" />
    : s === 'Needs Improvement' ? <AlertCircle className="w-4 h-4 text-amber-500" />
    : <XCircle className="w-4 h-4 text-rose-500" />;

// ── sub-components ────────────────────────────────────────────────────────────
const ScoreGauge: React.FC<{ score: number; label: string }> = ({ score, label }) => {
  const r = 52, circ = 2 * Math.PI * r;
  const dash = circ * (score / 100);
  return (
    <div className="flex flex-col items-center gap-2">
      <svg width="130" height="130" viewBox="0 0 130 130">
        <circle cx="65" cy="65" r={r} fill="none" stroke="#e2e8f0" strokeWidth="10" />
        <circle cx="65" cy="65" r={r} fill="none" stroke={scoreRing(score)} strokeWidth="10"
          strokeDasharray={`${dash} ${circ}`} strokeLinecap="round"
          transform="rotate(-90 65 65)" style={{ transition: 'stroke-dasharray 1s ease' }} />
        <text x="65" y="60" textAnchor="middle" fontSize="26" fontWeight="800" fill={scoreRing(score)}>{score}</text>
        <text x="65" y="78" textAnchor="middle" fontSize="11" fill="#94a3b8">/ 100</text>
      </svg>
      <span className="text-xs font-bold text-slate-500 uppercase tracking-widest">{label}</span>
    </div>
  );
};

const SectionCard: React.FC<{ title: string; icon: React.ReactNode; children: React.ReactNode; accent?: string }> =
  ({ title, icon, children, accent = 'from-indigo-500 to-violet-500' }) => (
    <div className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
      <div className={`bg-gradient-to-r ${accent} px-6 py-4 flex items-center gap-3`}>
        <div className="p-2 bg-white/20 rounded-xl text-white">{icon}</div>
        <h2 className="text-white font-bold text-lg">{title}</h2>
      </div>
      <div className="p-6">{children}</div>
    </div>
  );

const MetricRow: React.FC<{ label: string; value: string; status?: string }> = ({ label, value, status }) => (
  <div className="flex items-center justify-between py-3 border-b border-slate-100 last:border-0">
    <span className="text-slate-500 text-sm font-medium">{safeStr(label)}</span>
    <div className="flex items-center gap-2">
      {status && statusIcon(status)}
      <span className="text-slate-900 font-bold text-sm">{safeStr(value)}</span>
    </div>
  </div>
);

const FindingCard: React.FC<{ finding: any }> = ({ finding }) => {
  const [open, setOpen] = useState(false);
  return (
    <div className="border border-slate-200 rounded-2xl overflow-hidden hover:shadow-md transition-shadow">
      <button onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between p-4 bg-slate-50 hover:bg-slate-100 transition-colors text-left">
        <div className="flex items-center gap-3">
          <span className={`text-xs font-black px-2.5 py-1 rounded-full border ${priorityBadge(safeStr(finding.priority))}`}>
            {safeStr(finding.priority)}
          </span>
          <span className="font-semibold text-slate-800 text-sm">{safeStr(finding.metric)}</span>
        </div>
        {open ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
      </button>
      {open && (
        <div className="p-4 space-y-3 bg-white">
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-slate-50 rounded-xl p-3">
              <p className="text-xs text-slate-400 mb-1 font-medium">Current Value</p>
              <p className="text-sm font-bold text-slate-800">{safeStr(finding.current_value)}</p>
            </div>
            <div className="bg-slate-50 rounded-xl p-3">
              <p className="text-xs text-slate-400 mb-1 font-medium">Benchmark</p>
              <p className="text-sm font-bold text-slate-800">{safeStr(finding.benchmark)}</p>
            </div>
          </div>
          {finding.business_impact && (
            <div className="bg-amber-50 border border-amber-100 rounded-xl p-3">
              <p className="text-xs text-amber-600 font-bold mb-1">Business Impact</p>
              <p className="text-sm text-amber-800">{safeStr(finding.business_impact)}</p>
            </div>
          )}
          {finding.recommendation && (
            <div className="bg-emerald-50 border border-emerald-100 rounded-xl p-3">
              <p className="text-xs text-emerald-600 font-bold mb-1">Recommendation</p>
              <p className="text-sm text-emerald-800">{safeStr(finding.recommendation)}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// ── main page ─────────────────────────────────────────────────────────────────
export default function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    fetch(`${API_URL}/projects/${id}`)
      .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
      .then(d => { setData(d); setLoading(false); })
      .catch(e => { setError(e.message); setLoading(false); });
  }, [id]);

  if (loading) return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center space-y-4">
        <div className="w-16 h-16 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin mx-auto" />
        <p className="text-slate-500 font-medium">Loading project data from database…</p>
      </div>
    </div>
  );

  if (error || !data) return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center space-y-4 max-w-sm">
        <XCircle className="w-16 h-16 text-rose-400 mx-auto" />
        <h2 className="text-xl font-bold text-slate-800">Failed to load project</h2>
        <p className="text-slate-500 text-sm">{error || 'No data found'}</p>
        <button onClick={() => navigate('/projects')}
          className="px-6 py-3 bg-indigo-600 text-white rounded-xl font-bold text-sm">Back to Projects</button>
      </div>
    </div>
  );

  const score = data.overall_score ?? 0;
  const techAudit = data.technical_audit ?? {};
  const findings: any[] = techAudit.findings ?? [];
  const metrics: any[] = techAudit.metric_summary ?? [];
  const crawl = data.crawl_overview ?? {};
  const pageSpeed = data.page_speed ?? {};
  const linkAnalysis = data.link_analysis ?? {};
  const keywords = data.keyword_analysis ?? {};
  const competitive = data.competitive_intelligence ?? {};
  const aiInsights: any[] = data.ai_insights?.insights ?? [];
  const roadmap: any[] = data.recommended_roadmap ?? [];
  const strategy = data.content_strategy ?? {};

  return (
    <div className="min-h-screen bg-slate-50/50 pb-16">
      {/* ── sticky header ── */}
      <div className="sticky top-0 z-40 bg-white/90 backdrop-blur-xl border-b border-slate-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button onClick={() => navigate('/projects')}
              className="p-2 hover:bg-slate-100 rounded-xl transition-colors">
              <ArrowLeft className="w-5 h-5 text-slate-600" />
            </button>
            <div>
              <div className="flex items-center gap-2">
                <Globe className="w-4 h-4 text-indigo-500" />
                <h1 className="font-bold text-slate-900 text-base truncate max-w-xs">{data.url}</h1>
                <a href={data.url} target="_blank" rel="noreferrer" className="text-slate-400 hover:text-indigo-500">
                  <ExternalLink className="w-3.5 h-3.5" />
                </a>
              </div>
              <p className="text-xs text-slate-400 font-medium mt-0.5">SEO Audit Report · Full Analysis</p>
            </div>
          </div>
          <div className={`px-5 py-2 rounded-full border font-black text-sm ${scoreBg(score)} ${scoreColor(score)}`}>
            {score}% SEO Health
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 pt-8 space-y-8">

        {/* ── hero overview ── */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Score gauge */}
          <div className="bg-white rounded-3xl border border-slate-200 shadow-sm p-8 flex flex-col items-center justify-center gap-4">
            <ScoreGauge score={score} label="Overall SEO Score" />
            <p className="text-center text-slate-500 text-sm leading-relaxed max-w-xs">
              {safeStr(data.executive_summary) || 'No executive summary available.'}
            </p>
          </div>

          {/* Crawl stats */}
          <div className="bg-white rounded-3xl border border-slate-200 shadow-sm p-6 space-y-1">
            <h3 className="font-bold text-slate-800 mb-4 flex items-center gap-2">
              <Search className="w-4 h-4 text-indigo-500" /> Crawl Overview
            </h3>
            <MetricRow label="Pages Analyzed" value={String(crawl.analyzed_pages ?? '—')} />
            <MetricRow label="Pages Discovered" value={String(crawl.discovered_internal_pages ?? '—')} />
            <MetricRow label="Coverage Ratio" value={crawl.coverage_ratio ?? crawl.sample_coverage_ratio ?? '—'} />
            <MetricRow label="Crawl Depth" value={String(crawl.crawl_depth ?? '—')} />
            <MetricRow label="Robots.txt" value={crawl.robots_txt_status ?? '—'} />
            <MetricRow label="Sitemap" value={crawl.sitemap_status ?? '—'} />
            <MetricRow label="Favicon" value={crawl.favicon_status ?? '—'} />
          </div>

          {/* Page speed & links */}
          <div className="bg-white rounded-3xl border border-slate-200 shadow-sm p-6 space-y-4">
            <h3 className="font-bold text-slate-800 flex items-center gap-2">
              <Zap className="w-4 h-4 text-amber-500" /> Performance & Links
            </h3>
            <div className="grid grid-cols-2 gap-3">
              {[
                { label: 'Desktop Score', value: pageSpeed.desktop?.score != null ? String(pageSpeed.desktop.score) : (pageSpeed.score != null ? String(pageSpeed.score) : '—') },
                { label: 'Mobile Score', value: pageSpeed.mobile?.score != null ? String(pageSpeed.mobile.score) : '—' },
                { label: 'Response Time', value: pageSpeed.response_time != null ? `${pageSpeed.response_time}s` : '—' },
                { label: 'Page Size', value: pageSpeed.page_size_kb != null ? `${pageSpeed.page_size_kb} KB` : '—' },
              ].map(item => (
                <div key={item.label} className="bg-slate-50 rounded-2xl p-4 text-center">
                  <p className="text-2xl font-black text-slate-800">{item.value}</p>
                  <p className="text-xs text-slate-400 mt-1 font-medium">{item.label}</p>
                </div>
              ))}
            </div>
            <div className="border-t border-slate-100 pt-3 space-y-1">
              <MetricRow label="Internal Links Score"
                value={String(linkAnalysis.internal?.internal_link_score ?? '—')} />
              <MetricRow label="External Domains"
                value={String(linkAnalysis.external?.total_external_links ?? '—')} />
            </div>
          </div>
        </div>

        {/* ── metric summary ── */}
        {metrics.length > 0 && (
          <SectionCard title="Metric Summary" icon={<BarChart3 className="w-5 h-5" />} accent="from-sky-500 to-cyan-500">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {metrics.map((m: any, i: number) => (
                <div key={i} className="bg-slate-50 rounded-2xl p-4 border border-slate-100">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-black text-slate-500 uppercase tracking-wider">{safeStr(m.metric)}</span>
                    {statusIcon(m.status)}
                  </div>
                  <p className="text-sm font-bold text-slate-800 mb-1">{safeStr(m.current_value)}</p>
                  <p className="text-xs text-slate-400">{safeStr(m.benchmark)}</p>
                </div>
              ))}
            </div>
          </SectionCard>
        )}

        {/* ── findings ── */}
        {findings.length > 0 && (
          <SectionCard title={`Technical Findings (${findings.length})`} icon={<Shield className="w-5 h-5" />}
            accent="from-violet-500 to-purple-600">
            <div className="space-y-3">
              {findings.map((f: any, i: number) => <FindingCard key={i} finding={f} />)}
            </div>
          </SectionCard>
        )}

        {/* ── AI insights ── */}
        {aiInsights.length > 0 && (
          <SectionCard title="AI Insights" icon={<Lightbulb className="w-5 h-5" />} accent="from-fuchsia-500 to-pink-500">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {aiInsights.map((ins: any, i: number) => (
                <div key={i} className="bg-gradient-to-br from-slate-50 to-indigo-50/30 border border-indigo-100 rounded-2xl p-5">
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 bg-indigo-100 rounded-xl flex items-center justify-center shrink-0 mt-0.5">
                      <Lightbulb className="w-4 h-4 text-indigo-600" />
                    </div>
                    <div>
                      <h4 className="font-bold text-slate-800 text-sm mb-1">{safeStr(ins.issue || ins.title || ins.category)}</h4>
                      <p className="text-slate-600 text-sm leading-relaxed">{safeStr(ins.explanation || ins.insight || ins.description)}</p>
                      {ins.recommendation && (
                        <p className="text-emerald-700 text-xs mt-2 font-medium">💡 {safeStr(ins.recommendation)}</p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </SectionCard>
        )}

        {/* ── keywords ── */}
        {(keywords.primary_keywords?.length > 0 || keywords.long_tail_keywords?.length > 0) && (
          <SectionCard title="Keyword Analysis" icon={<Search className="w-5 h-5" />} accent="from-emerald-500 to-teal-500">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {keywords.primary_keywords?.length > 0 && (
                <div>
                  <h4 className="font-bold text-slate-700 mb-3 text-sm uppercase tracking-wider">Primary Keywords</h4>
                  <div className="flex flex-wrap gap-2">
                    {keywords.primary_keywords.map((kw: any, i: number) => (
                      <span key={i} className="px-3 py-1.5 bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-full text-xs font-semibold">
                        {safeStr(kw)}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {keywords.long_tail_keywords?.length > 0 && (
                <div>
                  <h4 className="font-bold text-slate-700 mb-3 text-sm uppercase tracking-wider">Long-tail Keywords</h4>
                  <div className="flex flex-wrap gap-2">
                    {keywords.long_tail_keywords.map((kw: any, i: number) => (
                      <span key={i} className="px-3 py-1.5 bg-teal-50 text-teal-700 border border-teal-200 rounded-full text-xs font-semibold">
                        {safeStr(kw)}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </SectionCard>
        )}

        {/* ── competitive intelligence ── */}
        {competitive.keyword_overlap_score && (
          <SectionCard title="Competitive Intelligence" icon={<Target className="w-5 h-5" />} accent="from-orange-500 to-rose-500">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              {[
                { label: 'Keyword Overlap', value: competitive.keyword_overlap_score },
                { label: 'Content Gap', value: competitive.content_gap_ratio },
                { label: 'Competitors Sampled', value: String(competitive.competitor_sample_size ?? '—') },
              ].map(stat => (
                <div key={stat.label} className="bg-slate-50 rounded-2xl p-4 text-center border border-slate-100">
                  <p className="text-xl font-black text-slate-800">{safeStr(stat.value)}</p>
                  <p className="text-xs text-slate-400 mt-1 font-medium">{safeStr(stat.label)}</p>
                </div>
              ))}
            </div>
            {competitive.market_opportunities?.length > 0 && (
              <div>
                <h4 className="font-bold text-slate-700 mb-3 text-sm">Market Opportunities</h4>
                <div className="space-y-2">
                  {competitive.market_opportunities.map((opp: any, i: number) => (
                    <div key={i} className="flex items-start gap-2 bg-orange-50 rounded-xl p-3 border border-orange-100">
                      <TrendingUp className="w-4 h-4 text-orange-500 shrink-0 mt-0.5" />
                      <p className="text-sm text-orange-800">{safeStr(opp)}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </SectionCard>
        )}

        {/* ── roadmap ── */}
        {roadmap.length > 0 && (
          <SectionCard title="Recommended Roadmap" icon={<Map className="w-5 h-5" />} accent="from-indigo-600 to-blue-500">
            <div className="space-y-4">
              {roadmap.map((step: any, i: number) => (
                <div key={i} className="flex gap-4">
                  <div className="flex flex-col items-center">
                    <div className="w-8 h-8 bg-indigo-600 rounded-full flex items-center justify-center text-white font-black text-sm shrink-0">
                      {i + 1}
                    </div>
                    {i < roadmap.length - 1 && <div className="w-0.5 flex-1 bg-indigo-100 mt-2" />}
                  </div>
                  <div className="pb-4">
                    <h4 className="font-bold text-slate-800 text-sm">{safeStr(step.action || step.title || step)}</h4>
                    {step.timeline && (
                      <div className="flex items-center gap-1 mt-1">
                        <Clock className="w-3 h-3 text-slate-400" />
                        <span className="text-xs text-slate-400">{safeStr(step.timeline)}</span>
                      </div>
                    )}
                    {step.impact && <p className="text-sm text-slate-500 mt-1">{safeStr(step.impact)}</p>}
                  </div>
                </div>
              ))}
            </div>
          </SectionCard>
        )}

        {/* ── content strategy ── */}
        {(strategy.blog_suggestions?.length > 0 || strategy.guest_post_titles?.length > 0) && (
          <SectionCard title="Content Strategy" icon={<BookOpen className="w-5 h-5" />} accent="from-slate-600 to-slate-800">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {strategy.blog_suggestions?.length > 0 && (
                <div>
                  <h4 className="font-bold text-slate-700 mb-3 text-sm uppercase tracking-wider">Blog Ideas</h4>
                  <ul className="space-y-2">
                    {strategy.blog_suggestions.map((s: any, i: number) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-slate-700">
                        <FileText className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
                        <div>
                          <span className="font-semibold">{safeStr(typeof s === 'object' ? s.title : s)}</span>
                          {typeof s === 'object' && s.target_audience && (
                            <p className="text-xs text-slate-400 mt-0.5">Audience: {safeStr(s.target_audience)}</p>
                          )}
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {strategy.guest_post_titles?.length > 0 && (
                <div>
                  <h4 className="font-bold text-slate-700 mb-3 text-sm uppercase tracking-wider">Guest Post Titles</h4>
                  <ul className="space-y-2">
                    {strategy.guest_post_titles.map((t: any, i: number) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-slate-700">
                        <Link2 className="w-4 h-4 text-violet-400 shrink-0 mt-0.5" />
                        <span>{safeStr(t)}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </SectionCard>
        )}

        {/* ── sampled pages ── */}
        {crawl.sampled_pages?.length > 0 && (
          <SectionCard title={`Sampled Pages (${crawl.sampled_pages.length})`} icon={<Cpu className="w-5 h-5" />}
            accent="from-slate-500 to-slate-700">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-100">
                    {['URL', 'Title Len', 'Meta Len', 'Word Count', 'H1', 'Indexable'].map(h => (
                      <th key={h} className="text-left text-xs font-black text-slate-400 uppercase tracking-wider pb-3 pr-4">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {crawl.sampled_pages.map((p: any, i: number) => (
                    <tr key={i} className="border-b border-slate-50 hover:bg-slate-50 transition-colors">
                      <td className="py-3 pr-4 max-w-xs">
                        <a href={p.url} target="_blank" rel="noreferrer"
                          className="text-indigo-600 hover:underline font-medium truncate block max-w-xs">{p.url}</a>
                      </td>
                      <td className="py-3 pr-4 font-mono text-slate-600">{p.title_length ?? '—'}</td>
                      <td className="py-3 pr-4 font-mono text-slate-600">{p.meta_description_length ?? '—'}</td>
                      <td className="py-3 pr-4 font-mono text-slate-600">{p.word_count ?? '—'}</td>
                      <td className="py-3 pr-4">{p.h1_count != null ? (
                        <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${p.h1_count === 1 ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'}`}>
                          {p.h1_count}
                        </span>
                      ) : '—'}</td>
                      <td className="py-3 pr-4">
                        {p.is_indexable != null ? (
                          p.is_indexable
                            ? <CheckCircle className="w-4 h-4 text-emerald-500" />
                            : <XCircle className="w-4 h-4 text-rose-500" />
                        ) : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </SectionCard>
        )}

        {/* ── report download ── */}
        {data.report_url && (
          <div className="bg-gradient-to-r from-indigo-600 to-violet-600 rounded-3xl p-8 text-center shadow-xl shadow-indigo-200">
            <h3 className="text-white font-bold text-xl mb-2">Full PDF Report Available</h3>
            <p className="text-indigo-200 mb-6 text-sm">Download the complete audit report with all findings and recommendations</p>
            <a href={`${API_URL}${data.report_url}`} target="_blank" rel="noreferrer"
              className="inline-flex items-center gap-2 px-8 py-3 bg-white text-indigo-600 rounded-xl font-black shadow-lg hover:shadow-xl transition-all hover:scale-105">
              <FileText className="w-5 h-5" />
              Download Report
            </a>
          </div>
        )}
      </div>
    </div>
  );
}
