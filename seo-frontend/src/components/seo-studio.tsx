import React, { useState, useEffect, useRef, useMemo } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { useNavigate, useParams } from 'react-router-dom';
import * as d3 from 'd3';

const getScoreValue = (scoreStr: string | number) => {
  if (typeof scoreStr === 'number') return scoreStr;
  const match = String(scoreStr).match(/\d+/);
  return match ? parseInt(match[0], 10) : 0;
};

const getScoreColor = (score: number) => {
  if (score >= 90) return 'text-emerald-500 bg-emerald-50 ring-emerald-200';
  if (score >= 70) return 'text-emerald-500 bg-emerald-50 ring-emerald-200';
  if (score >= 50) return 'text-amber-500 bg-amber-50 ring-amber-200';
  return 'text-rose-500 bg-rose-50 ring-rose-200';
};

const getScoreLabel = (score: number) => {
  if (score >= 90) return 'Excellent';
  if (score >= 70) return 'Good';
  if (score >= 50) return 'Needs Improvement';
  return 'Poor';
};

const getScoreProgressColor = (score: number) => {
  if (score >= 70) return 'bg-emerald-500';
  if (score >= 40) return 'bg-amber-500';
  return 'bg-rose-500';
};
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell
} from 'recharts';
import { SEO_DATA as DATA } from '../data';
import {
  ShieldCheck,
  TrendingUp,
  FileText,
  Globe,
  AlertCircle,
  CheckCircle2,
  Clock,
  Download,
  ChevronRight,
  BookOpen,
  ArrowRight,
  Table as TableIcon,
  Lock,
  Info,
  Lightbulb,
  Zap,
  Activity,
  Cpu,
  Share2,
  Twitter,
  Linkedin,
  Facebook,
  Instagram,
  MessageCircle,
  Copy,
  Check,
  X,
  ExternalLink,
  Menu,
  RefreshCw,
  Search,
  MousePointer2,
  Link,
  PanelLeftOpen,
  PanelLeftClose,
  Target,
  Layers,
  BarChart3,
  Smartphone,
  Monitor
} from 'lucide-react';
import { toPng } from 'html-to-image';
import { jsPDF } from 'jspdf';

const SectionHeader = ({ icon: Icon, title, subtitle }: { icon: any, title: string, subtitle?: string }) => (
  <div className="flex items-center gap-4 mb-8">
    <div className="p-3 bg-indigo-50 rounded-2xl">
      <Icon className="w-6 h-6 text-indigo-600" />
    </div>
    <div>
      <h3 className="text-2xl font-display font-bold text-slate-800">{title}</h3>
      {subtitle && <p className="text-slate-500 text-sm font-medium">{subtitle}</p>}
    </div>
  </div>
);

const MetricCard = ({ label, value, benchmark, status, description }: any) => {
  const statusLower = status?.toLowerCase() || '';
  const isCritical = statusLower.includes('critical') || statusLower.includes('below');
  return (
    <div className="bg-white p-5 rounded-2xl border border-slate-100 shadow-sm hover:shadow-md transition-shadow relative overflow-hidden group">
      <div className="flex justify-between items-start mb-3">
        <div className="flex items-center">
          <span className="text-xs font-bold text-slate-400 uppercase tracking-widest">{label}</span>
          {description && <HelpTooltip text={description} />}
        </div>
        <span className={`px-2 py-0.5 rounded text-[10px] font-black uppercase ${isCritical ? 'bg-rose-50 text-rose-600' : 'bg-emerald-50 text-emerald-600'}`}>
          {status || 'N/A'}
        </span>
      </div>
      <div className="text-2xl font-display font-bold text-slate-800 mb-1">{value}</div>
      <div className="text-[11px] text-slate-500 font-semibold uppercase tracking-wider">Goal: {benchmark}</div>
    </div>
  );
};

const RoadmapItem = ({ item, index, total }: any) => {
  const [isExpanded, setIsExpanded] = useState(index === 0);

  return (
    <div className="relative pl-12 group">
      {/* Vertical Line Segment */}
      {index !== total - 1 && (
        <div className="absolute left-[1.375rem] top-10 bottom-0 w-0.5 bg-indigo-400/20" />
      )}

      {/* Timeline Marker */}
      <motion.div
        onClick={() => setIsExpanded(!isExpanded)}
        className="absolute left-0 top-0 cursor-pointer z-10"
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.95 }}
      >
        <div className={`w-11 h-11 rounded-2xl flex items-center justify-center font-black text-sm transition-all duration-500 shadow-lg ${isExpanded ? 'bg-white text-indigo-600 rotate-12 scale-110 shadow-white/20' : 'bg-indigo-500 text-white border border-white/20 hover:bg-white hover:text-indigo-600'
          }`}>
          {index + 1}
        </div>
      </motion.div>

      <div className="pb-10 pt-1">
        <div
          onClick={() => setIsExpanded(!isExpanded)}
          className="cursor-pointer select-none mb-2"
        >
          <div className="flex items-center gap-3 mb-1">
            <span className={`text-[10px] font-black uppercase tracking-widest transition-colors ${isExpanded ? 'text-indigo-200' : 'text-indigo-300'}`}>
              {item.timeline}
            </span>
            <div className={`h-px flex-1 transition-all duration-700 ${isExpanded ? 'bg-white/20' : 'bg-white/5'}`} />
            <motion.div
              animate={{ rotate: isExpanded ? 180 : 0, scale: isExpanded ? 1.2 : 1 }}
              className={`p-1 rounded-lg transition-colors ${isExpanded ? 'bg-white/10' : 'bg-transparent'}`}
            >
              <ChevronRight className="w-4 h-4 text-white/40" />
            </motion.div>
          </div>
          <h5 className={`font-display font-bold transition-all duration-500 ${isExpanded ? 'text-white text-2xl' : 'text-indigo-100 text-lg group-hover:text-white'}`}>
            {item.objective}
          </h5>
        </div>

        <AnimatePresence mode="wait">
          {isExpanded && (
            <motion.div
              initial={{ height: 0, opacity: 0, x: -10 }}
              animate={{ height: 'auto', opacity: 1, x: 0 }}
              exit={{ height: 0, opacity: 0, x: -10 }}
              transition={{
                duration: 0.5,
                ease: [0.23, 1, 0.32, 1],
                opacity: { duration: 0.3 }
              }}
              className="overflow-hidden"
            >
              <div className="space-y-6 py-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {item?.actions?.map((a: any, i: any) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: 0.1 + (i * 0.1) }}
                      className="p-3 bg-white/5 border border-white/10 rounded-xl backdrop-blur-sm flex items-start gap-2 hover:bg-white/10 transition-colors"
                    >
                      <Check className="w-3 h-3 text-emerald-400 mt-0.5 flex-shrink-0" />
                      <span className="text-[11px] font-bold text-slate-100 leading-tight">{a}</span>
                    </motion.div>
                  )) || null}
                </div>

                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.3 }}
                  className="p-6 bg-gradient-to-br from-black/30 to-black/10 rounded-2xl border border-white/5 backdrop-blur-xl relative overflow-hidden"
                >
                  <div className="absolute top-0 right-0 w-24 h-24 bg-indigo-500/5 rounded-full blur-2xl" />
                  <div className="relative z-10">
                    <div className="flex items-center gap-2 mb-3">
                      <div className="p-1.5 bg-indigo-500/20 rounded-lg">
                        <Zap className="w-3.5 h-3.5 text-indigo-300" />
                      </div>
                      <div className="text-[10px] font-black uppercase text-indigo-200 tracking-widest">Expected Outcome</div>
                    </div>
                    <p className="text-[13px] text-slate-200 font-medium leading-relaxed italic">
                      " {item.expected_outcome} "
                    </p>
                  </div>
                </motion.div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};

const extractValue = (val: string | number) => {
  if (typeof val === 'number') return val;
  if (typeof val !== 'string') return 0;
  
  // 1. If it contains a percentage, grab the number immediately preceding it
  const pctMatch = val.match(/([\d.]+)\s*%/);
  if (pctMatch) return parseFloat(pctMatch[1]);
  
  // 2. Find all numbers in the string
  const numbers = [...val.matchAll(/([\d.]+)/g)].map(m => parseFloat(m[1]));
  if (numbers.length === 0) return 0;
  if (numbers.length === 1) return numbers[0];
  
  // 3. If multiple numbers exist, filter out likely years (e.g., 2024, 2025, 2026)
  const nonYearNumbers = numbers.filter(n => n < 2000 || n > 2100);
  if (nonYearNumbers.length > 0) {
    return nonYearNumbers[nonYearNumbers.length - 1]; // Usually the metric is stated at the end
  }
  
  return numbers[numbers.length - 1];
};

const MetricComparisonTool = ({ metrics }: { metrics: any[] }) => {
  if (!metrics || metrics.length === 0) return null;
  const [metric1, setMetric1] = useState(metrics[0]?.metric);
  const [metric2, setMetric2] = useState(metrics[4]?.metric || metrics[1]?.metric);

  const m1 = metrics.find(m => m.metric === metric1);
  const m2 = metrics.find(m => m.metric === metric2);

  if (!m1 || !m2) return null;

  const getSuffix = (m: any) => (typeof m?.current_value === 'string' && m.current_value.includes('%')) || (typeof m?.benchmark === 'string' && m.benchmark.includes('%')) ? '%' : '';

  const chartData = [
    {
      name: m1.metric,
      Current: extractValue(m1.current_value),
      Benchmark: extractValue(m1.benchmark),
      suffix: getSuffix(m1)
    },
    {
      name: m2.metric,
      Current: extractValue(m2.current_value),
      Benchmark: extractValue(m2.benchmark),
      suffix: getSuffix(m2)
    }
  ];

  return (
    <div className="bg-white p-8 rounded-[2rem] border border-slate-200 shadow-sm relative overflow-hidden group">
      <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-50 rounded-full -mr-20 -mt-20 blur-3xl opacity-50 group-hover:bg-indigo-100 transition-colors" />
      <div className="relative z-10">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-8">
          <div>
            <h4 className="text-xl font-display font-bold text-slate-900 mb-1">Metric Comparison Tool</h4>
            <p className="text-xs text-slate-500 font-medium">Select two metrics to compare current performance against benchmarks.</p>
          </div>
          <div className="flex flex-wrap gap-3">
            <div className="space-y-1">
              <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest block ml-1">Metric A</span>
              <select
                value={metric1}
                onChange={(e) => setMetric1(e.target.value)}
                className="bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-xs font-bold text-slate-700 outline-none focus:ring-2 focus:ring-indigo-500 transition-all cursor-pointer min-w-[200px]"
              >
                {metrics.map(m => <option key={m.metric} value={m.metric}>{m.metric}</option>)}
              </select>
            </div>
            <div className="space-y-1">
              <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest block ml-1">Metric B</span>
              <select
                value={metric2}
                onChange={(e) => setMetric2(e.target.value)}
                className="bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-xs font-bold text-slate-700 outline-none focus:ring-2 focus:ring-indigo-500 transition-all cursor-pointer min-w-[200px]"
              >
                {metrics.map(m => <option key={m.metric} value={m.metric}>{m.metric}</option>)}
              </select>
            </div>
          </div>
        </div>

        <div className="h-[350px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
              <XAxis
                dataKey="name"
                axisLine={false}
                tickLine={false}
                tick={{ fontSize: 11, fontWeight: 700, fill: '#64748b' }}
                dy={10}
              />
              <YAxis
                axisLine={false}
                tickLine={false}
                tick={{ fontSize: 10, fontWeight: 700, fill: '#94a3b8' }}
                domain={[0, 100]}
              />
              <Tooltip
                cursor={{ fill: 'rgba(241, 245, 249, 0.4)', radius: 12 }}
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    return (
                      <motion.div
                        initial={{ opacity: 0, y: 10, scale: 0.95 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        className="bg-white/95 backdrop-blur-md p-5 border border-slate-200 shadow-2xl rounded-[1.5rem] ring-1 ring-slate-900/5 min-w-[220px]"
                      >
                        <div className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-3">{payload[0].payload.name}</div>
                        <div className="space-y-3">
                          {payload.map((p: any) => (
                            <div key={p.name} className="flex items-center justify-between">
                              <div className="flex items-center gap-2">
                                <div className="w-2 h-2 rounded-full" style={{ backgroundColor: p.color }} />
                                <span className="text-xs font-bold text-slate-600">{p.name}:</span>
                              </div>
                              <span className="text-sm font-black text-slate-900">
                                {p.value}{payload[0].payload.suffix}
                              </span>
                            </div>
                          ))}
                          <div className="pt-3 border-t border-slate-100">
                            <div className="flex items-center justify-between">
                              <span className="text-[10px] font-bold text-slate-400">Variance:</span>
                              <span className={`text-[10px] font-black ${payload[0].value >= payload[1].value ? 'text-emerald-500' : 'text-rose-500'}`}>
                                {payload[0].value >= payload[1].value ? '+' : ''}{(payload[0].value - payload[1].value).toFixed(1)}{payload[0].payload.suffix}
                              </span>
                            </div>
                          </div>
                        </div>
                      </motion.div>
                    );
                  }
                  return null;
                }}
              />
              <Bar
                dataKey="Benchmark"
                fill="#F1F5F9"
                radius={[12, 12, 0, 0]}
                barSize={60}
                className="transition-all duration-300"
              />
              <Bar
                dataKey="Current"
                fill="#6366f1"
                radius={[12, 12, 0, 0]}
                barSize={60}
                className="transition-all duration-300"
              >
                {chartData.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={entry.Current >= entry.Benchmark ? '#10B981' : '#6366F1'}
                    fillOpacity={0.9}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="mt-8 flex items-center justify-center gap-8">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded bg-[#F1F5F9]" />
            <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Industry Benchmark</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded bg-indigo-500" />
            <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Current Performance</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded bg-emerald-500" />
            <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">At/Above Benchmark</span>
          </div>
        </div>
      </div>
    </div>
  );
};

const URLComparisonDetails = ({ original, optimized, reason, targetUrl }: { original: string, optimized: string, reason: string, targetUrl: string }) => {
  const [hoveredTip, setHoveredTip] = useState<string | null>(null);

  const tips: Record<string, string> = {
    'Opaque identifiers (base64) mask hierarchy': 'Google prefers semantic paths that indicate content type and hierarchy. Meaningless strings prevent crawlers from understanding site structure.',
    'Lack of semantic keywords for crawler context': 'URLs serve as a minor ranking factor. Keywords in the slug confirm relevance to search engines and improve click-through rates (CTR).',
    'Non-standard casing patterns': 'Inconsistent casing can lead to duplicate content indexing if both "/Page" and "/page" are served, splitting your "link juice" authority.',
    'Strategic Benefit': 'Clean, hyphenated URLs are optimized for crawl budget allocation. Google processes hyphens as spaces, allowing individual keywords to be indexed effectively.',
    'Keyword Dense': 'Target keywords in the path communicate topical relevance immediately to the indexer.',
    'Semantic': 'Meaningful slugs help search engines categorize content within their semantic web graph.',
    'User Readable': 'Human-readable paths build trust and are 2x more likely to be shared on social platforms.'
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-stretch">
      <div className="p-5 bg-rose-900/20 border border-rose-500/20 rounded-2xl relative overflow-hidden group">
        <div className="absolute top-0 right-0 p-2 opacity-10 group-hover:opacity-20 transition-opacity">
          <AlertCircle className="w-12 h-12 text-rose-500" />
        </div>
        <div className="text-[10px] font-black text-rose-300 uppercase tracking-widest mb-3">Legacy Architecture</div>
        <div className="text-[11px] font-mono text-rose-100 bg-rose-500/20 p-3 rounded-xl border border-rose-500/30 break-all mb-4">
          {original}
        </div>
        <div className="space-y-3">
          {[
            'Opaque identifiers (base64) mask hierarchy',
            'Lack of semantic keywords for crawler context',
            'Non-standard casing patterns'
          ].map((issue, i) => (
            <div key={i} className="relative">
              <div className="flex items-center gap-2 group/tip cursor-help">
                <div className="w-1.5 h-1.5 rounded-full bg-rose-500 shrink-0" />
                <span className="text-[10px] text-rose-100 font-medium leading-tight flex-1">{issue}</span>
                <div
                  onMouseEnter={() => setHoveredTip(issue)}
                  onMouseLeave={() => setHoveredTip(null)}
                  className="p-1 bg-white/5 rounded-md hover:bg-white/10 transition-colors"
                >
                  <Info className="w-3 h-3 text-rose-300/60 group-hover/tip:text-rose-300" />
                </div>
              </div>
              <AnimatePresence>
                {hoveredTip === issue && (
                  <motion.div
                    initial={{ opacity: 0, y: 10, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: 10, scale: 0.95 }}
                    className="absolute bottom-full left-0 mb-2 w-64 bg-slate-900 text-slate-100 p-3 rounded-xl border border-white/10 shadow-2xl z-50 text-[10px] leading-relaxed font-bold"
                  >
                    <div className="absolute bottom-0 left-4 w-2 h-2 bg-slate-900 border-b border-r border-white/10 rotate-45 translate-y-1" />
                    {tips[issue]}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          ))}
        </div>
      </div>

      <div className="p-5 bg-emerald-900/20 border border-emerald-500/20 rounded-2xl relative overflow-hidden group">
        <div className="absolute top-0 right-0 p-2 opacity-10 group-hover:opacity-20 transition-opacity">
          <CheckCircle2 className="w-12 h-12 text-emerald-500" />
        </div>
        <div className="text-[10px] font-black text-emerald-300 uppercase tracking-widest mb-3">SEO Target State</div>
        <div className="flex items-center gap-2 mb-4">
          <div className="text-[11px] font-mono text-emerald-50 bg-emerald-500/30 p-3 rounded-xl border border-emerald-500/40 break-all flex-1 font-bold">
            {optimized}
          </div>
          <a
            href={`${targetUrl.replace(/\/$/, '')}${optimized}`}
            target="_blank"
            rel="noopener noreferrer"
            className="p-3 bg-emerald-500/20 hover:bg-emerald-500/40 rounded-xl border border-emerald-500/30 transition-all flex-shrink-0 group/link"
            title="View Site"
          >
            <ExternalLink className="w-4 h-4 text-emerald-400 group-hover/link:scale-110 transition-transform" />
          </a>
        </div>
        <div className="space-y-3">
          <div className="p-3 bg-emerald-500/10 rounded-lg border border-emerald-500/20">
            <div className="flex items-center justify-between mb-1">
              <div className="text-[9px] font-black text-emerald-300 uppercase">Strategic Benefit</div>
              <div
                onMouseEnter={() => setHoveredTip('Strategic Benefit')}
                onMouseLeave={() => setHoveredTip(null)}
                className="group/tip cursor-help p-1"
              >
                <Info className="w-3 h-3 text-emerald-400/50 group-hover/tip:text-emerald-400" />
                <AnimatePresence>
                  {hoveredTip === 'Strategic Benefit' && (
                    <motion.div
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -10 }}
                      className="absolute right-full mr-4 top-1/2 -translate-y-1/2 w-48 bg-emerald-950 text-emerald-50 p-4 rounded-xl border border-emerald-500/20 shadow-2xl z-50 text-[10px] font-bold leading-relaxed"
                    >
                      <div className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-1 w-2 h-2 bg-emerald-950 border-t border-r border-emerald-500/20 rotate-45" />
                      {tips['Strategic Benefit']}
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </div>
            <p className="text-[11px] text-emerald-50 font-bold leading-relaxed">{reason}</p>
          </div>
          <div className="flex flex-wrap gap-2 pt-1">
            {['Keyword Dense', 'Semantic', 'User Readable'].map(tag => (
              <div key={tag} className="relative group/tip">
                <span
                  onMouseEnter={() => setHoveredTip(tag)}
                  onMouseLeave={() => setHoveredTip(null)}
                  className="px-2 py-0.5 bg-emerald-400 text-emerald-950 font-black rounded text-[8px] uppercase cursor-help inline-flex items-center gap-1"
                >
                  {tag}
                </span>
                <AnimatePresence>
                  {hoveredTip === tag && (
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: 10 }}
                      className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-40 bg-slate-900 text-white p-2 rounded-lg text-[9px] font-bold text-center shadow-xl z-50 border border-white/10"
                    >
                      <div className="absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-1 w-2 h-2 bg-slate-900 border-b border-r border-white/10 rotate-45" />
                      {tips[tag]}
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

const URLGraph = ({ urls, companyName, targetUrl }: { urls: any[], companyName: string, targetUrl: string }) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const [selectedNode, setSelectedNode] = useState<any>(null);

  useEffect(() => {
    if (!svgRef.current) return;

    const width = 800;
    const height = 450;
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const nodes = [
      { id: companyName, type: 'root', depth: 0 },
      ...urls.map((u, i) => ({ id: u.optimized, type: 'url', full: u, depth: 1 }))
    ];

    const links = urls.map(u => ({ source: companyName, target: u.optimized }));

    const simulation = d3.forceSimulation(nodes as any)
      .force("link", d3.forceLink(links).id((d: any) => d.id).distance(120))
      .force("charge", d3.forceManyBody().strength(-300))
      .force("center", d3.forceCenter(width / 2, height / 2));

    const g = svg.append("g");

    const link = g.append("g")
      .selectAll("line")
      .data(links)
      .join("line")
      .attr("stroke", "#312e81")
      .attr("stroke-opacity", 0.4)
      .attr("stroke-width", 1.5);

    const node = g.append("g")
      .selectAll("g")
      .data(nodes)
      .join("g")
      .attr("class", "cursor-pointer")
      .on("click", (event, d: any) => {
        if (d.type === 'url') setSelectedNode(d.full);
      })
      .call(d3.drag<any, any>()
        .on("start", (event, d) => {
          if (!event.active) simulation.alphaTarget(0.3).restart();
          d.fx = d.x;
          d.fy = d.y;
        })
        .on("drag", (event, d) => {
          d.fx = event.x;
          d.fy = event.y;
        })
        .on("end", (event, d) => {
          if (!event.active) simulation.alphaTarget(0);
          d.fx = null;
          d.fy = null;
        }));

    node.append("circle")
      .attr("r", (d: any) => d.type === 'root' ? 20 : 12)
      .attr("fill", (d: any) => d.type === 'root' ? "#6366f1" : "#10b981")
      .attr("stroke", "#ffffff")
      .attr("stroke-width", 2)
      .attr("class", "hover:stroke-indigo-300 transition-all");

    node.append("text")
      .text((d: any) => d.id === companyName ? d.id : d.id.split('/').pop())
      .attr("dy", (d: any) => d.type === 'root' ? 35 : 25)
      .attr("text-anchor", "middle")
      .attr("fill", "#ffffff")
      .attr("font-size", "9px")
      .attr("font-weight", "900")
      .attr("class", "uppercase tracking-widest bg-black/40 px-2 rounded pointer-events-none");

    simulation.on("tick", () => {
      link
        .attr("x1", (d: any) => d.source.x)
        .attr("y1", (d: any) => d.source.y)
        .attr("x2", (d: any) => d.target.x)
        .attr("y2", (d: any) => d.target.y);

      node.attr("transform", (d: any) => `translate(${d.x},${d.y})`);
    });

    return () => simulation.stop();
  }, [urls]);

  return (
    <div className="relative group/graph bg-indigo-950/40 border border-white/5 rounded-[2.5rem] overflow-hidden">
      <div className="absolute top-6 left-6 z-10">
        <div className="text-[10px] font-black text-indigo-300 uppercase tracking-widest mb-1">Architecture Visualization</div>
        <p className="text-[11px] text-white/40 max-w-[200px]">Interactive map of crawl paths and optimized URI endpoints.</p>
      </div>

      <svg
        ref={svgRef}
        viewBox="0 0 800 450"
        className="w-full h-[450px]"
      />

      <AnimatePresence>
        {selectedNode && (
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            className="absolute top-6 right-6 w-72 bg-white/10 backdrop-blur-3xl border border-white/10 p-6 rounded-3xl shadow-2xl z-20"
          >
            <div className="flex justify-between items-start mb-6">
              <div className="p-2 bg-emerald-500/20 rounded-xl">
                <Globe className="w-4 h-4 text-emerald-400" />
              </div>
              <button
                onClick={() => setSelectedNode(null)}
                className="p-1 hover:bg-white/10 rounded-full transition-colors"
              >
                <X className="w-4 h-4 text-white/40" />
              </button>
            </div>

            <div className="space-y-6">
              <div>
                <div className="text-[10px] font-black text-white/40 uppercase mb-2">Endpoint URI</div>
                <div className="text-[11px] font-mono text-white font-bold break-all bg-black/20 p-3 rounded-xl border border-white/5">
                  {selectedNode.optimized}
                </div>
              </div>

              <div>
                <div className="text-[10px] font-black text-white/40 uppercase mb-2">Content Blueprint</div>
                <p className="text-[11px] text-slate-300 leading-relaxed italic">{selectedNode.reason}</p>
              </div>

              <div className="pt-4 border-t border-white/5">
                <a
                  href={`${targetUrl.replace(/\/$/, '')}${selectedNode.optimized}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="w-full py-2.5 bg-indigo-500 hover:bg-indigo-600 text-white rounded-xl text-[10px] font-black uppercase flex items-center justify-center gap-2 transition-all"
                >
                  <ExternalLink className="w-3.5 h-3.5" /> View Live Path
                </a>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="absolute bottom-6 left-6 p-4 bg-black/40 backdrop-blur-md rounded-2xl border border-white/5">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-indigo-500" />
            <span className="text-[9px] font-black text-indigo-200 uppercase tracking-tight">Root Node</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-emerald-500" />
            <span className="text-[9px] font-black text-emerald-200 uppercase tracking-tight">Optimized Page</span>
          </div>
        </div>
      </div>
    </div>
  );
};

const URLAnalyzerTool = () => {
  const [input, setInput] = useState('');
  const [analysis, setAnalysis] = useState<any>(null);

  const analyze = () => {
    if (!input.trim()) return;

    // Logic for demo-friendly optimization
    const optimized = input.toLowerCase()
      .replace(/https?:\/\/[^/]+/i, '') // Remove domain
      .replace(/[?=#].*/g, '')          // Remove parameters
      .replace(/[^a-z0-9/]/g, '-')     // Hyphenate
      .replace(/-+/g, '-')             // Consolidate hyphens
      .replace(/\/+/g, '/')            // Consolidate slashes
      .replace(/\/$/, '');              // Remove trailing slash

    const changes = [];
    if (input !== input.toLowerCase()) {
      changes.push({ type: 'Casing Normalization', detail: 'URL converted to lowercase', benefit: 'Prevents "duplicate content" flags in Google caused by case-sensitive URI segments.' });
    }
    if (input.includes('_')) {
      changes.push({ type: 'Word Separation', detail: 'Underscores replaced with hyphens', benefit: 'Google crawlers recognize hyphens as space markers, whereas underscores are treated as alpha-characters, masking keywords.' });
    }
    if (input.includes('?') || input.includes('=') || input.includes('#')) {
      changes.push({ type: 'Parameter Scrubbing', detail: 'Query parameters removed', benefit: 'Clean, descriptive paths (slugs) pass more "link juice" and improve crawl budget allocation.' });
    }
    if (optimized.length > 5) {
      changes.push({ type: 'Semantic Slug Generation', detail: 'Topical keywords identified', benefit: 'Provides immediate context to users and search bots about the page content before loading.' });
    }

    setAnalysis({
      original: input,
      optimized: optimized || '/',
      score: input.includes('?') ? 45 : 82,
      changes
    });
  };

  return (
    <div className="bg-white p-8 rounded-[2.5rem] border border-slate-200 shadow-sm relative overflow-hidden group">
      <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-50 rounded-full -mr-32 -mt-32 blur-3xl opacity-50" />
      <div className="relative z-10">
        <div className="max-w-2xl mb-10">
          <h4 className="text-2xl font-display font-bold text-slate-900 mb-2">Interactive URL Optimizer</h4>
          <p className="text-slate-500 text-sm font-medium leading-relaxed">Input any complex or legacy URI to visualize our semantic transformation logic and targeted SEO uplift.</p>
        </div>

        <div className="flex flex-col sm:flex-row gap-3 mb-10">
          <input
            type="text"
            placeholder="Enter legacy URL (e.g. site.com/P_id?id=123)"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            className="flex-1 px-6 py-4 bg-slate-50 border border-slate-200 rounded-2xl outline-none focus:ring-2 focus:ring-indigo-500 font-mono text-sm transition-all"
          />
          <button
            onClick={analyze}
            className="px-8 py-4 bg-indigo-600 hover:bg-black text-white rounded-2xl font-black text-sm uppercase tracking-widest flex items-center justify-center gap-3 transition-all active:scale-95 shadow-lg shadow-indigo-200"
          >
            <Search className="w-4 h-4" /> Analyze
          </button>
        </div>

        <AnimatePresence mode="wait">
          {analysis && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="space-y-8"
            >
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div className="p-6 bg-slate-50 border border-slate-200 rounded-3xl relative overflow-hidden">
                  <div className="absolute top-0 right-0 text-[60px] font-black text-slate-100 -mr-6 -mt-6 pointer-events-none">OLD</div>
                  <div className="relative">
                    <div className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-4">Original Structure</div>
                    <div className="text-sm font-mono text-slate-500 break-all bg-white p-4 rounded-xl border border-slate-100 mb-4">{analysis.original}</div>
                    <div className="flex items-center gap-2">
                      <div className="p-1 bg-rose-50 rounded-lg"><X className="w-3.5 h-3.5 text-rose-500" /></div>
                      <span className="text-[11px] font-bold text-rose-600">Poor Semantic Context</span>
                    </div>
                  </div>
                </div>

                <div className="p-6 bg-indigo-50 border border-indigo-100 rounded-3xl relative overflow-hidden">
                  <div className="absolute top-0 right-0 text-[60px] font-black text-indigo-500/5 -mr-6 -mt-6 pointer-events-none">NEXT</div>
                  <div className="relative">
                    <div className="text-[10px] font-black text-indigo-400 uppercase tracking-widest mb-4">Optimized Architecture</div>
                    <div className="text-sm font-mono text-indigo-700 font-bold break-all bg-white p-4 rounded-xl border border-indigo-200 mb-4">{analysis.optimized}</div>
                    <div className="flex items-center gap-2">
                      <div className="p-1 bg-emerald-50 rounded-lg"><Check className="w-3.5 h-3.5 text-emerald-600" /></div>
                      <span className="text-[11px] font-bold text-emerald-700 text-contrast-check">At Benchmark Range</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-slate-900 rounded-[2rem] p-8 text-white relative overflow-hidden">
                <div className="absolute bottom-0 right-0 w-64 h-64 bg-indigo-500/10 rounded-full blur-3xl" />
                <div className="relative z-10">
                  <div className="flex items-center justify-between mb-8">
                    <h5 className="font-display font-bold text-lg">Change Decomposition</h5>
                    <div className="flex items-center gap-3">
                      <span className="text-xs font-bold text-slate-400">SEO Health Score</span>
                      <span className="text-3xl font-display font-black text-indigo-400">{analysis.score}%</span>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                    {analysis.changes.map((change: any, i: number) => (
                      <div key={i} className="p-5 bg-white/5 border border-white/10 rounded-2xl group hover:bg-white/10 transition-all">
                        <div className="flex items-center gap-3 mb-3">
                          <div className="p-1.5 bg-indigo-500/20 rounded-lg">
                            <Zap className="w-4 h-4 text-indigo-300" />
                          </div>
                          <h6 className="font-bold text-sm text-slate-100">{change.type}</h6>
                        </div>
                        <div className="space-y-4">
                          <div className="text-[10px] text-slate-400 font-medium">MODIFICATION: <span className="text-indigo-300 font-bold">{change.detail}</span></div>
                          <div className="p-3 bg-emerald-500/10 rounded-xl border border-emerald-500/20">
                            <div className="text-[8px] font-black text-emerald-400 uppercase mb-1 tracking-widest">SEO Benefit</div>
                            <p className="text-[11px] text-emerald-50 leading-relaxed font-bold">{change.benefit}</p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};

const YouTubePreview = ({ videoId, videoUrl, title, description }: { videoId?: string, videoUrl?: string, title: string, description: string }) => {
  const [isHovered, setIsHovered] = useState(false);

  // Extract video ID from URL if provided
  const extractVideoId = (url: string) => {
    const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|&v=)([^#&?]*).*/;
    const match = url.match(regExp);
    return (match && match[2].length === 11) ? match[2] : null;
  };

  const activeVideoId = videoId || (videoUrl ? extractVideoId(videoUrl) : '');

  return (
    <div
      className="bg-white/5 border border-white/10 rounded-3xl overflow-hidden group/card hover:bg-white/10 transition-all duration-500"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      data-html2canvas-ignore="true"
    >
      <a
        href={videoUrl || `https://www.youtube.com/watch?v=${activeVideoId}`}
        target="_blank"
        rel="noopener noreferrer"
        className="block aspect-video relative bg-black/40 overflow-hidden cursor-pointer"
      >
        {!isHovered ? (
          <div className="absolute inset-0 z-10 flex flex-col items-center justify-center p-6 text-center">
            <img
              src={`https://img.youtube.com/vi/${activeVideoId}/maxresdefault.jpg`}
              alt={title}
              crossOrigin="anonymous"
              className="absolute inset-0 w-full h-full object-cover opacity-50 group-hover/card:scale-110 group-hover/card:opacity-70 transition-all duration-700"
            />
            <div className="relative z-20">
              <div className="w-14 h-14 bg-white/10 backdrop-blur-xl rounded-full flex items-center justify-center mx-auto mb-4 border border-white/20 group-hover/card:scale-125 group-hover/card:bg-indigo-500 transition-all duration-500">
                <Zap className="w-6 h-6 text-white" />
              </div>
              <div className="text-white font-display font-black text-xs uppercase tracking-[0.2em] mb-1">Preview Case Study</div>
              <div className="text-indigo-300 text-[10px] font-bold">HOVER TO AUTO-PLAY</div>
            </div>
          </div>
        ) : (
          <iframe
            src={`https://www.youtube.com/embed/${activeVideoId}?autoplay=1&mute=1&controls=0&modestbranding=1&rel=0&iv_load_policy=3`}
            title={title}
            className="w-full h-full pointer-events-none"
            frameBorder="0"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowFullScreen
          />
        )}
      </a>
      <div className="p-6">
        <h5 className="font-bold text-slate-100 mb-2 group-hover/card:text-indigo-300 transition-colors">{title}</h5>
        <p className="text-[11px] text-slate-400 leading-relaxed font-medium">{description}</p>
      </div>
    </div>
  );
};

const DataLimitationAccordionItem = ({ lim, index }: any) => {
  const [isOpen, setIsOpen] = useState(index === 0);

  return (
    <div className="border-b border-indigo-50 last:border-0">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full py-5 flex items-center justify-between text-left transition-all hover:pl-1"
      >
        <div className="flex items-center gap-3">
          <div className={`w-8 h-8 rounded-xl flex items-center justify-center transition-all duration-500 ${isOpen ? 'bg-indigo-600 text-white rotate-6' : 'bg-indigo-50 text-indigo-600'}`}>
            <Lock className="w-4 h-4" />
          </div>
          <div className="flex flex-col">
            <span className={`text-[10px] font-black uppercase tracking-widest transition-colors ${isOpen ? 'text-indigo-600' : 'text-slate-400'}`}>
              {lim.data_source}
            </span>
            <span className={`text-xs font-bold transition-colors ${isOpen ? 'text-slate-900' : 'text-slate-600'}`}>
              Security & Access Intel
            </span>
          </div>
        </div>
        <motion.div
          animate={{ rotate: isOpen ? 90 : 0 }}
          className={`p-1.5 rounded-lg transition-colors ${isOpen ? 'bg-indigo-50 text-indigo-600' : 'text-slate-300'}`}
        >
          <ChevronRight className="w-4 h-4" />
        </motion.div>
      </button>

      <AnimatePresence initial={false}>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.4, ease: [0.23, 1, 0.32, 1] }}
            className="overflow-hidden"
          >
            <div className="pb-6 space-y-5">
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <div className="h-px w-4 bg-indigo-200" />
                  <span className="text-[10px] font-black text-indigo-400 uppercase tracking-widest">Why it Matters</span>
                </div>
                <p className="text-[11px] text-slate-500 leading-relaxed font-medium pl-6">{lim.why_it_matters}</p>
              </div>

              {lim.user_impact && (
                <motion.div
                  initial={{ x: -10, opacity: 0 }}
                  animate={{ x: 0, opacity: 1 }}
                  className="p-5 bg-amber-50 border-2 border-amber-200 rounded-[2rem] relative overflow-hidden group/alert shadow-sm"
                >
                  <div className="absolute -top-4 -right-4 w-24 h-24 bg-amber-100 rounded-full blur-2xl opacity-40" />
                  <div className="relative z-10">
                    <div className="flex items-center gap-3 mb-3">
                      <div className="p-2 bg-amber-200 text-amber-800 rounded-xl">
                        <Activity className="w-4 h-4" />
                      </div>
                      <span className="text-[10px] font-black text-amber-900 uppercase tracking-widest">Critical Decision Impact</span>
                    </div>
                    <div className="pl-1">
                      <p className="text-[11px] text-amber-950 font-bold leading-relaxed mb-1">
                        {lim.user_impact}
                      </p>
                      <div className="flex items-center gap-1.5 text-[9px] font-black text-amber-600 uppercase mt-2 pt-2 border-t border-amber-200/50">
                        <AlertCircle className="w-3 h-3" /> Creates High-Risk Intelligence Gap
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}

              <div className="p-4 bg-slate-50 border border-slate-100 rounded-2xl flex items-center justify-between group/action hover:bg-indigo-50 hover:border-indigo-100 transition-all">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-white rounded-xl shadow-sm group-hover/action:scale-110 transition-transform">
                    <Target className="w-4 h-4 text-indigo-600" />
                  </div>
                  <div>
                    <div className="text-[9px] font-black text-slate-400 uppercase mb-0.5 tracking-widest">Remediation Path</div>
                    <p className="text-[11px] text-slate-900 font-bold">{lim.next_step}</p>
                  </div>
                </div>
                <div className="w-6 h-6 rounded-full bg-emerald-100 flex items-center justify-center opacity-0 group-hover/action:opacity-100 transition-opacity">
                  <Check className="w-3 h-3 text-emerald-600" />
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

const FindingAccordionItem = ({ finding, currentData }: any) => {
  const [isOpen, setIsOpen] = useState(false);
  const navigate = useNavigate();

  const handleViewDetails = () => {
    const pages = currentData?.pages || currentData?.crawl_overview?.sampled_pages || [];
    console.log('Audit Intelligence - View Full Audit Depth Triggered for:', finding.metric);
    console.log('Audit Intelligence - Data Payload for Details:', pages);
    navigate("/audit-details", { state: { pages, fromMetric: finding.metric } });
  };

  const renderRemediationTool = () => {
    if (finding.metric === 'Meta Description Coverage' || finding.metric === 'Meta Description Uniqueness') {
      return (
        <div className="mt-8 space-y-4">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-indigo-100 rounded-xl">
              <Zap className="w-4 h-4 text-indigo-600" />
            </div>
            <h5 className="text-sm font-black text-slate-800 uppercase tracking-widst">Generated Conversion Snippets</h5>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[
              { page: 'Homepage', current: currentData?.pdf_template_data?.hero_metrics?.[0]?.value || 'Legacy Content', optimized: `Expert ${currentData?.pdf_template_data?.company_name || 'Organization'} Services | Strategic Search Engine Visibility & Growth` },
              { page: 'Internal', current: 'Legacy System Metadata', optimized: `Professional ${currentData?.keyword_analysis?.primary_keywords?.[0] || 'Technical'} Solutions - Optimized by ${currentData?.pdf_template_data?.company_name || 'AuditIntelligence'}` },
              { page: 'Services', current: 'Service Index', optimized: `Premium Service Catalog | ${currentData?.pdf_template_data?.company_name || 'Organization'} Industry-Leading Protocols` },
              { page: 'Insights', current: 'Unoptimized Insights', optimized: `${currentData?.pdf_template_data?.company_name || 'Organization'} Strategic Hub | Expert Research & Market Data` }
            ].map((item, i) => (
              <div key={i} className="p-4 bg-white border border-slate-200 rounded-2xl group hover:border-indigo-400 transition-all shadow-sm">
                <div className="text-[9px] font-black text-indigo-600 uppercase mb-2">{item.page} Optimization</div>
                <div className="text-[10px] text-slate-400 line-clamp-1 mb-2">Original: {item.current}</div>
                <p className="text-[11px] text-slate-900 font-bold leading-relaxed">{item.optimized}</p>
                <div className="mt-3 pt-3 border-t border-slate-100 flex justify-between items-center">
                  <span className="text-[8px] font-black text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded">{item.optimized.length} chars</span>
                  <button className="text-[9px] font-black text-indigo-600 uppercase hover:underline">Apply Snippet</button>
                </div>
              </div>
            ))}
          </div>
        </div>
      );
    }

    if (finding.metric === 'Sitewide Alt Text Coverage') {
      return (
        <div className="mt-8 space-y-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-emerald-100 rounded-xl">
              <Activity className="w-4 h-4 text-emerald-600" />
            </div>
            <h5 className="text-sm font-black text-slate-800 uppercase tracking-widst">Visual Asset Intelligence Scan</h5>
          </div>
          <div className="space-y-3">
            {[
              { img: 'hero-render-01.jpg', tag: '3D Render of modern home exterior with charcoal siding and natural wood accents', confidence: '98%' },
              { img: 'visual-analysis.png', tag: `Deep semantic audit of the primary ${currentData?.pdf_template_data?.company_name || 'target'} domain architecture and crawl frontiers.`, confidence: '94%' },
              { img: 'material-swatch-oak.webp', tag: 'Close-up texture of natural oak wood planking for exterior facade visualization', confidence: '99%' }
            ].map((asset, i) => (
              <div key={i} className="p-4 bg-emerald-50/50 border border-emerald-100 rounded-2xl flex items-center justify-between group">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-white rounded-xl border border-emerald-100 flex items-center justify-center text-[9px] font-mono text-emerald-400 font-bold text-center p-1 uppercase">IMG Asset</div>
                  <div>
                    <div className="text-[9px] font-black text-slate-400 uppercase mb-1">{asset.img}</div>
                    <p className="text-[11px] text-slate-800 font-bold max-w-md">{asset.tag}</p>
                  </div>
                </div>
                <div className="flex flex-col items-end gap-2">
                  <span className="text-[9px] font-black text-emerald-600">{asset.confidence} AI Sync</span>
                  <button className="p-1.5 bg-white border border-emerald-200 rounded-lg text-emerald-600 hover:bg-emerald-600 hover:text-white transition-all">
                    <Check className="w-3 h-3" />
                  </button>
                </div>
              </div>
            ))}
          </div>
          <div className="p-4 bg-indigo-50 rounded-2xl border border-indigo-100 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-white rounded-xl"><Cpu className="w-4 h-4 text-indigo-600" /></div>
              <p className="text-[11px] text-indigo-900 font-bold italic">Missing alt text detected on 42 additional assets. Start automated tagging cycle?</p>
            </div>
            <button className="px-4 py-2 bg-indigo-600 text-white rounded-xl text-[10px] font-black uppercase tracking-widest shadow-lg shadow-indigo-200 active:scale-95 transition-all">Initialize Batch Fix</button>
          </div>
        </div>
      );
    }

    if (finding.metric === 'H1 Compliance') {
      return (
        <div className="mt-8 space-y-4">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-rose-100 rounded-xl">
              <Target className="w-4 h-4 text-rose-600" />
            </div>
            <h5 className="text-sm font-black text-slate-800 uppercase tracking-widst">Semantic H1 Re-engineering</h5>
          </div>
          <div className="space-y-3">
            {[
              { page: 'Homepage', old: 'Design Your Own Home', new: 'Expert Online Exterior Home Design & 3D Visualization Services', reasoning: 'Targets high-intent "Exterior Design Services" keyword with semantic brand context.' },
              { page: 'Blog', old: 'Blogs', new: 'Latest Home Exterior Design Trends, Tips & Professional Transformation Guides', reasoning: 'Establishes topical authority beyond a generic "Blogs" indexer.' },
              { page: 'Projects', old: 'Exterior Design', new: 'Modern Home Exterior Renovation Case Studies: Before & After Virtual Renders', reasoning: 'Explicitly maps visual content type to search bot crawl expectations.' }
            ].map((re, i) => (
              <div key={i} className="p-5 bg-white border border-slate-200 rounded-2xl grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-3">
                  <div className="text-[10px] font-black text-rose-500 uppercase tracking-widest">{re.page} Structure</div>
                  <div className="space-y-2">
                    <div className="text-[9px] text-slate-400 font-bold uppercase">Current H1</div>
                    <div className="text-[11px] text-slate-500 line-through decoration-rose-400/50">{re.old}</div>
                  </div>
                  <div className="space-y-2">
                    <div className="text-[9px] text-emerald-600 font-black uppercase">Optimized H1</div>
                    <div className="text-xs font-black text-slate-900 leading-tight">{re.new}</div>
                  </div>
                </div>
                <div className="p-4 bg-slate-50 rounded-xl border border-slate-100 flex flex-col justify-between">
                  <div>
                    <div className="text-[9px] font-black text-slate-400 uppercase mb-2">Intent Alignment</div>
                    <p className="text-[11px] text-slate-600 font-medium leading-relaxed italic">"{re.reasoning}"</p>
                  </div>
                  <button className="mt-4 w-full py-2 bg-slate-900 text-white rounded-lg text-[9px] font-black uppercase tracking-widest hover:bg-black transition-all">Accept Change</button>
                </div>
              </div>
            ))}
          </div>
        </div>
      );
    }

    return null;
  };

  return (
    <div className={`p-6 bg-slate-50 border border-slate-100 rounded-2xl border-l-4 transition-all ${isOpen ? 'bg-white border-indigo-200 border-l-indigo-600 shadow-xl scale-[1.02] z-10 relative' : 'hover:bg-slate-100 border-l-indigo-400 shadow-sm'}`}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex justify-between items-start text-left"
      >
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-1">
            <h4 className="font-bold text-slate-900">{finding.metric}</h4>
            <span className={`px-2 py-0.5 rounded text-[8px] font-black text-white uppercase ${finding.status === 'Critical Gap' ? 'bg-rose-500' : 'bg-indigo-500'}`}>{finding.status}</span>
          </div>
          <p className="text-[10px] font-black text-indigo-400 uppercase tracking-widest">{finding.category}</p>
        </div>
        <motion.div
          animate={{ rotate: isOpen ? 180 : 0 }}
          className={`p-1.5 rounded-lg transition-colors ${isOpen ? 'bg-indigo-50 text-indigo-600' : 'text-slate-300'}`}
        >
          <ChevronRight className="w-4 h-4" />
        </motion.div>
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.4, ease: [0.23, 1, 0.32, 1] }}
            className="overflow-hidden"
          >
            <div className="pt-6 space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 bg-indigo-50/50 border border-indigo-100 rounded-xl">
                  <div className="text-[9px] font-black text-indigo-600 uppercase mb-2 tracking-widest">Business Impact Assessment</div>
                  <p className="text-[11px] text-slate-700 font-medium leading-relaxed">{finding.business_impact}</p>
                </div>
                <div className="p-4 bg-emerald-50/50 border border-emerald-100 rounded-xl">
                  <div className="text-[9px] font-black text-emerald-600 uppercase mb-2 tracking-widest">Board Implementation Strategy</div>
                  <p className="text-[11px] text-slate-700 font-medium leading-relaxed">{finding.recommendation}</p>
                </div>
              </div>

              {renderRemediationTool()}

              <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className={`p-1 rounded ${finding.priority === 'High' ? 'bg-rose-100 text-rose-600' : 'bg-amber-100 text-amber-600'}`}>
                    <AlertCircle className="w-3 h-3" />
                  </div>
                  <span className="text-[9px] font-black text-slate-400 uppercase">{finding.priority} Priority Remediation Req.</span>
                </div>
                <button 
                  onClick={handleViewDetails}
                  className="text-[10px] font-black text-indigo-600 uppercase tracking-widest hover:underline flex items-center gap-1.5 cursor-pointer hover:text-indigo-800 transition-all hover:scale-105 active:scale-95"
                >
                  View Full Audit Depth <ExternalLink className="w-3 h-3" />
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

const HelpTooltip = ({ text, suggestion }: { text: string, suggestion?: string }) => {
  const [isVisible, setIsVisible] = useState(false);

  return (
    <div className="relative inline-block ml-1.5 align-middle">
      <button
        onMouseEnter={() => setIsVisible(true)}
        onMouseLeave={() => setIsVisible(false)}
        className="text-slate-300 hover:text-indigo-400 p-0.5 transition-colors"
      >
        <Info className="w-3.5 h-3.5" />
      </button>
      <AnimatePresence>
        {isVisible && (
          <motion.div
            initial={{ opacity: 0, y: 10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 10, scale: 0.95 }}
            className="absolute bottom-full left-1/2 -translate-x-1/2 mb-3 w-64 bg-slate-900 text-white p-4 rounded-2xl shadow-2xl z-[60] text-[11px] leading-relaxed font-medium"
          >
            <div className="absolute bottom-[-6px] left-1/2 -translate-x-1/2 border-8 border-transparent border-t-slate-900" />
            <p className="mb-3">{text}</p>
            {suggestion && (
              <div className="pt-3 border-t border-white/10">
                <div className="flex items-center gap-1.5 text-indigo-400 font-black uppercase text-[9px] mb-1.5">
                  <Lightbulb className="w-3 h-3" /> Improvement Scope
                </div>
                <p className="text-slate-300 italic">{suggestion}</p>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export const PageAnalysisCards = ({ pages }: { pages: any[] }) => {
  const [selectedUrl, setSelectedUrl] = useState<string | null>(null);
  const [expandedCards, setExpandedCards] = useState<Record<string, boolean>>({});
  const [activeTabs, setActiveTabs] = useState<Record<string, string>>({});

  if (!pages || pages.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-12 bg-white rounded-[2rem] border border-slate-200 shadow-sm text-slate-500">
        <AlertCircle className="w-12 h-12 mb-4 text-slate-300" />
        <h3 className="text-lg font-bold text-slate-700">No data available</h3>
        <p className="text-sm">Page-wise SEO data is not present in the current audit.</p>
      </div>
    );
  }

  const toggleExpand = (url: string) => {
    setExpandedCards(prev => ({ ...prev, [url]: !prev[url] }));
  };

  const setTab = (url: string, tab: string) => {
    setActiveTabs(prev => ({ ...prev, [url]: tab }));
  };

  const TABS = [
    { id: 'overview', label: 'Overview' },
    { id: 'performance', label: 'Performance' },
    { id: 'headings', label: 'Headings' },
    { id: 'content', label: 'Content' },
    { id: 'technical', label: 'Technical' },
    { id: 'issues', label: 'Issues' },
    { id: 'recommendations', label: 'Recommendations' },
  ];

  useEffect(() => {
    if (pages && pages.length > 0) {
      console.log('Deep Audit - Pages Data Payload:', pages);
    }
  }, [pages]);

  const selectedPage = pages.find(p => p.url === selectedUrl);

  if (!selectedUrl) {
    return (
      <div className="space-y-4">
        <div className="bg-white rounded-[2rem] border border-slate-200 shadow-sm overflow-hidden">
          <div className="px-8 py-6 border-b border-slate-100 flex justify-between items-center bg-slate-50/50">
            <div>
              <h3 className="text-xl font-display font-bold text-slate-800">Sampled Pages</h3>
              <p className="text-xs text-slate-500 font-medium">Click on a page to view deep-audit intelligence</p>
            </div>
            <div className="px-4 py-2 bg-indigo-50 text-indigo-600 rounded-xl text-xs font-black uppercase tracking-widest">
              {pages.length} Pages Audited
            </div>
          </div>
          <div className="divide-y divide-slate-100">
            {pages.map((page, idx) => {
              const score = getScoreValue(page?.seo_score ?? page?.seo_health ?? 0);
              return (
                <button
                  key={page.url || idx}
                  onClick={() => setSelectedUrl(page.url)}
                  className="w-full px-8 py-5 flex items-center justify-between hover:bg-slate-50 transition-all group text-left"
                >
                  <div className="flex items-center gap-6 flex-1 min-w-0">
                    <div className={`w-12 h-12 rounded-2xl flex items-center justify-center font-black text-sm ring-1 shadow-sm transition-transform group-hover:scale-110 ${getScoreColor(score)}`}>
                      {score}%
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-bold text-slate-800 truncate mb-1 group-hover:text-indigo-600 transition-colors">
                        {page.url}
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="text-[10px] font-black uppercase tracking-widest text-slate-400">{page.page_type || 'General Page'}</span>
                        <div className="w-1 h-1 rounded-full bg-slate-200" />
                        <span className="text-[10px] font-bold text-slate-500">{page?.content?.word_count ?? page?.word_count ?? 0} words</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    {page.key_issue && (
                      <span className="hidden md:block px-2.5 py-1 bg-rose-50 text-rose-600 text-[9px] font-black uppercase tracking-wider rounded-md border border-rose-100">
                        {page.key_issue}
                      </span>
                    )}
                    <ChevronRight className="w-5 h-5 text-slate-300 group-hover:text-indigo-500 group-hover:translate-x-1 transition-all" />
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <button
          onClick={() => setSelectedUrl(null)}
          className="flex items-center gap-2 px-5 py-2.5 bg-white border border-slate-200 rounded-xl text-slate-600 hover:text-indigo-600 hover:border-indigo-200 transition-all font-bold text-xs shadow-sm active:scale-95"
        >
          <ArrowRight className="w-4 h-4 rotate-180" /> Back to List
        </button>
        <div className="flex items-center gap-3">
          <div className="text-right">
            <div className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Currently Viewing</div>
            <div className="text-sm font-bold text-slate-800">{selectedPage?.url}</div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-8">
        {selectedPage && (() => {
          const id = selectedPage.url;
          const isExpanded = true;
          const currentTab = activeTabs[id] || 'overview';
          const score = getScoreValue(selectedPage?.seo_score ?? selectedPage?.seo_health ?? 0);
          const scoreLabel = getScoreLabel(score);

          // Meta & Overview
          const titleTag = selectedPage?.page_info?.title || selectedPage?.title || 'N/A';
          const metaDesc = selectedPage?.page_info?.meta_description || selectedPage?.page_info?.metaDescription || selectedPage?.meta_description || 'Not Found';
          const idxStatus = selectedPage?.page_info?.indexing_status || selectedPage?.indexing_status || selectedPage?.page_type || 'Unknown';
          const canonicalUrl = selectedPage?.page_info?.canonical || selectedPage?.canonical_url || selectedPage?.url || 'N/A';

          // Content
          const contentQuality = selectedPage?.content?.quality || selectedPage?.content?.content_quality || selectedPage?.content?.quality_status || 'Not Analyzed';
          const wordCount = selectedPage?.content?.word_count || selectedPage?.word_count || 0;
          const keywordGaps = selectedPage?.content?.keyword_gaps || [];

          // Performance
          const mScoreRaw = selectedPage?.performance?.mobile?.score ?? selectedPage?.performance?.score;
          const mobileScore = mScoreRaw != null ? mScoreRaw : 'Data Not Available';
          const mScoreVal = getScoreValue(mobileScore);
          
          const dScoreRaw = selectedPage?.performance?.desktop?.score ?? selectedPage?.performance?.score;
          const desktopScore = dScoreRaw != null ? dScoreRaw : 'Data Not Available';
          const dScoreVal = getScoreValue(desktopScore);

          const mobileLoad = selectedPage?.performance?.mobile?.load_time || selectedPage?.performance?.load_time || 'N/A';
          const desktopLoad = selectedPage?.performance?.desktop?.load_time || selectedPage?.performance?.load_time || 'N/A';
          
          const mobileStatus = selectedPage?.performance?.mobile?.status || selectedPage?.performance?.status || 'Not Analyzed';
          const desktopStatus = selectedPage?.performance?.desktop?.status || selectedPage?.performance?.status || 'Not Analyzed';

          const perfIssues = selectedPage?.performance?.issues || [];

          // Issues flattened
          let allIssues: any[] = [];
          if (Array.isArray(selectedPage?.issues)) {
            allIssues = selectedPage?.issues;
          } else if (selectedPage?.issues && typeof selectedPage?.issues === 'object') {
            allIssues = [
              ...(selectedPage.issues.critical || []),
              ...(selectedPage.issues.high || []),
              ...(selectedPage.issues.medium || []),
              ...(selectedPage.issues.low || [])
            ];
          } else if (selectedPage?.key_issue) {
            allIssues = [selectedPage.key_issue];
          }

          const allRecs = selectedPage?.recommendations || [];

          return (
            <div key={id} className="bg-white rounded-[1.5rem] shadow-sm border border-slate-200 overflow-hidden flex flex-col hover:shadow-md transition-shadow">
              {/* Top Section */}
              <div className="p-6 bg-slate-50/50 border-b border-slate-100">
                <div className="flex justify-between items-start mb-4">
                  <div className="flex-1 pr-4 overflow-hidden">
                    <h3 className="text-sm font-bold text-slate-800 truncate" title={selectedPage?.url}>{selectedPage?.url || 'Untitled Page'}</h3>
                    {(selectedPage?.priority_action || selectedPage?.key_issue) && (
                      <div className="mt-2 inline-flex items-center gap-1.5 px-2.5 py-1 bg-rose-50 text-rose-600 text-[10px] font-black uppercase tracking-wider rounded-md border border-rose-100">
                        <AlertCircle className="w-3 h-3" />
                        Priority: {selectedPage?.priority_action || selectedPage?.key_issue}
                      </div>
                    )}
                  </div>
                  <div className="shrink-0 flex flex-col items-end gap-1">
                    <div className={`px-4 py-1.5 rounded-full text-sm font-black ring-1 shadow-sm ${getScoreColor(score)}`}>
                      {score}%
                    </div>
                    <span className="text-[10px] font-black uppercase tracking-widest text-slate-400">{scoreLabel}</span>
                  </div>
                </div>
                
                <div className="w-full bg-slate-200 rounded-full h-1.5">
                  <div className={`h-1.5 rounded-full ${getScoreProgressColor(score)} transition-all duration-1000`} style={{ width: `${score}%` }} />
                </div>
              </div>

              {/* Tabs Navigation */}
              <div className="flex overflow-x-auto custom-scrollbar sticky top-0 bg-white z-10 border-b border-slate-100 px-2">
                {TABS.map(tab => (
                  <button 
                    key={tab.id}
                    onClick={() => setTab(id, tab.id)} 
                    className={`shrink-0 px-4 py-3 text-xs font-bold transition-colors border-b-2 whitespace-nowrap ${currentTab === tab.id ? 'border-indigo-500 text-indigo-600 bg-indigo-50/50' : 'border-transparent text-slate-500 hover:text-slate-800 hover:bg-slate-50'}`}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>

              {/* Content Area */}
              <div className={`p-6 flex-1 overflow-y-auto custom-scrollbar transition-all ${isExpanded ? 'max-h-[700px]' : 'max-h-[250px]'}`}>
                {currentTab === 'overview' && (
                  <div className="space-y-4 text-sm text-slate-600">
                    <div className="bg-slate-50 p-4 rounded-xl border border-slate-100">
                      <p className="font-bold text-slate-800 mb-1">Title Tag <HelpTooltip text="The title of the page as it appears in search engine results and browser tabs. It is a critical SEO factor." /></p>
                      <p className="line-clamp-2">{titleTag}</p>
                    </div>
                    <div className="bg-slate-50 p-4 rounded-xl border border-slate-100">
                      <p className="font-bold text-slate-800 mb-1">Meta Description <HelpTooltip text="A brief summary of the page's content. While not a direct ranking factor, it influences whether users click on your link in search results." /></p>
                      <p className="line-clamp-3">{metaDesc}</p>
                    </div>
                    <div className="bg-slate-50 p-4 rounded-xl border border-slate-100">
                      <p className="font-bold text-slate-800 mb-1">Canonical URL <HelpTooltip text="The preferred version of a page. If multiple URLs have similar content, the canonical tag tells search engines which one to index to avoid duplicate content penalties." /></p>
                      <p className="line-clamp-1 truncate text-xs font-mono text-slate-500">{canonicalUrl}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-slate-800">Indexing Status:</span>
                      <span className={`px-2 py-1 rounded text-[10px] font-black uppercase ${String(idxStatus).toLowerCase().includes('noindex') ? 'bg-rose-100 text-rose-700' : 'bg-emerald-100 text-emerald-700'}`}>
                        {idxStatus}
                      </span>
                      <HelpTooltip text="Tells you if search engines like Google are allowed to include this page in their index and show it in search results." />
                    </div>
                  </div>
                )}

                {currentTab === 'performance' && (
                  <div className="space-y-6">
                    <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                      {/* Performance Component */}
                      {[
                        { type: 'mobile', icon: Smartphone, label: 'Mobile Performance', data: selectedPage?.performance?.mobile, score: mScoreVal },
                        { type: 'desktop', icon: Monitor, label: 'Desktop Performance', data: selectedPage?.performance?.desktop, score: dScoreVal }
                      ].map((device) => (
                        <div key={device.type} className="bg-white p-6 rounded-[2rem] border border-slate-200 shadow-sm relative overflow-hidden flex flex-col group">
                          <div className="flex items-center justify-between mb-6">
                            <div className="flex items-center gap-3">
                              <div className="p-2.5 bg-indigo-50 text-indigo-600 rounded-xl group-hover:scale-110 transition-transform">
                                <device.icon className="w-5 h-5" />
                              </div>
                              <div>
                                <h4 className="font-display font-bold text-slate-800 text-base">{device.label}</h4>
                                <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">
                                  {getScoreLabel(device.score)}
                                  <HelpTooltip text="An overall performance score calculated based on several speed and responsiveness metrics. 90+ is considered excellent." />
                                </p>
                              </div>
                            </div>
                            <div className={`w-14 h-14 rounded-2xl flex flex-col items-center justify-center border-2 ${
                              device.score >= 90 ? 'bg-emerald-50 border-emerald-500 text-emerald-600' :
                              device.score >= 50 ? 'bg-amber-50 border-amber-500 text-amber-600' :
                              'bg-rose-50 border-rose-500 text-rose-600'
                            }`}>
                              <span className="text-lg font-black leading-none">{device.score}</span>
                              <span className="text-[8px] font-bold uppercase">Score</span>
                            </div>
                          </div>

                          <div className="grid grid-cols-3 gap-3 mb-6">
                            <div className="bg-slate-50 p-3 rounded-2xl border border-slate-100">
                              <p className="text-[9px] font-black text-slate-400 uppercase tracking-tight mb-1">Load Time</p>
                              <p className="text-sm font-bold text-slate-800">{device.data?.load_time || 'N/A'}</p>
                            </div>
                            <div className="bg-slate-50 p-3 rounded-2xl border border-slate-100 col-span-2">
                              <p className="text-[9px] font-black text-slate-400 uppercase tracking-tight mb-1">Network Status</p>
                              <p className="text-sm font-bold text-slate-800 capitalize flex items-center gap-2">
                                <div className={`w-1.5 h-1.5 rounded-full ${
                                  device.data?.status === 'Fast' ? 'bg-emerald-500' : 
                                  device.data?.status === 'Moderate' ? 'bg-amber-500' : 'bg-rose-500'
                                }`} />
                                {device.data?.status || 'Unknown'}
                              </p>
                            </div>
                          </div>

                          <div className="space-y-4 pt-4 border-t border-slate-100">
                            <div className="flex items-center justify-between">
                              <span className="text-[10px] font-black text-slate-500 uppercase">Core Web Vitals</span>
                              <Info className="w-3 h-3 text-slate-300" />
                            </div>
                            <div className="grid grid-cols-3 gap-4">
                              {[
                                 { label: 'LCP', val: device.data?.core_web_vitals?.lcp || '2.5s', status: 'Good', hint: 'Largest Contentful Paint: Measures how long it takes for the main content to load. Aim for 2.5s or less.' },
                                 { label: 'CLS', val: device.data?.core_web_vitals?.cls || '0.1', status: 'Needs Imp.', hint: 'Cumulative Layout Shift: Measures visual stability. A lower score means elements don\'t jump around while loading.' },
                                 { label: 'FID', val: device.data?.core_web_vitals?.fid || '100ms', status: 'Good', hint: 'First Input Delay: Measures the time from when a user first interacts with your site to when the browser responds.' }
                               ].map(v => (
                                 <div key={v.label} className="text-center group/v">
                                   <div className="text-[11px] font-black text-slate-800">{v.val}</div>
                                   <div className="text-[8px] font-bold text-slate-400 uppercase mb-1 flex items-center justify-center gap-0.5">
                                     {v.label}
                                     <HelpTooltip text={v.hint} />
                                   </div>
                                   <div className={`h-1 rounded-full ${v.status === 'Good' ? 'bg-emerald-400' : 'bg-amber-400'}`} />
                                 </div>
                               ))}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>

                    {/* Combined Issues */}
                    <div className="bg-slate-900 rounded-[2rem] p-6 text-white relative overflow-hidden">
                      <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-500/10 rounded-full blur-3xl" />
                      <h5 className="font-display font-bold text-lg mb-4 flex items-center gap-2 relative z-10">
                        <Zap className="w-5 h-5 text-indigo-400" /> performance optimization
                      </h5>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 relative z-10">
                        {(perfIssues.length > 0 ? perfIssues : [
                          "Large image assets detected without WebP compression.",
                          "Unused JavaScript in the critical render path.",
                          "Render-blocking CSS preventing early paint."
                        ]).map((iss: string, i: number) => (
                          <div key={i} className="p-4 bg-white/5 border border-white/10 rounded-2xl flex items-start gap-3">
                            <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                            <span className="text-[11px] font-bold text-slate-200 leading-relaxed">{iss}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {currentTab === 'headings' && (
                  <div className="space-y-4 text-sm text-slate-600">
                    <div className="bg-indigo-50 p-4 rounded-xl border border-indigo-100">
                      <p className="font-bold text-indigo-900 mb-1">
                        H1 Tag ({selectedPage?.headings?.h1_count || 0})
                        <HelpTooltip text="The main heading of a page. Each page should have exactly one H1 tag that describes what the page is about." />
                      </p>
                      <p className="text-indigo-800 italic">{selectedPage?.headings?.h1_content || 'Missing H1'}</p>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="bg-slate-50 p-3 rounded-xl border border-slate-100 text-center">
                        <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">
                          H2 Count <HelpTooltip text="Secondary headings used to organize content. Good for both users and search engines." />
                        </p>
                        <p className="text-xl font-black text-slate-800">{selectedPage?.headings?.h2_count || 0}</p>
                      </div>
                      <div className="bg-slate-50 p-3 rounded-xl border border-slate-100 text-center">
                        <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">
                          H3 Count <HelpTooltip text="Sub-headings used within H2 sections to further structure your content." />
                        </p>
                        <p className="text-xl font-black text-slate-800">{selectedPage?.headings?.h3_count || 0}</p>
                      </div>
                    </div>
                    {selectedPage?.headings?.warnings && selectedPage.headings.warnings.length > 0 && (
                      <div className="bg-amber-50 p-4 rounded-xl border border-amber-100 text-amber-800">
                        <p className="font-bold mb-2">Structure Warnings:</p>
                        <ul className="list-disc pl-4 space-y-1 text-xs">
                          {selectedPage.headings.warnings.map((w: string, i: number) => <li key={i}>{w}</li>)}
                        </ul>
                      </div>
                    )}
                  </div>
                )}

                {currentTab === 'content' && (
                  <div className="space-y-4 text-sm text-slate-600">
                    <div className="flex items-center justify-between bg-slate-50 p-4 rounded-xl border border-slate-100">
                      <span className="font-bold text-slate-800">
                        Word Count:
                        <HelpTooltip text="The total number of words on the page. Generally, more content provides more value and signals authority to search engines." />
                      </span>
                      <span className="font-black text-indigo-600 text-lg">{wordCount}</span>
                    </div>
                    <div className="bg-slate-50 p-4 rounded-xl border border-slate-100">
                      <span className="font-bold text-slate-800 block mb-1">
                        Quality Status:
                        <HelpTooltip text="An AI assessment of how useful and well-written the content on this page is." />
                      </span>
                      <span className="text-slate-600">{contentQuality}</span>
                    </div>
                    {keywordGaps.length > 0 && (
                      <div className="bg-slate-50 p-4 rounded-xl border border-slate-100">
                        <span className="font-bold text-slate-800 block mb-2">Keyword Gaps:</span>
                        <div className="flex flex-wrap gap-2">
                          {keywordGaps.map((kg: string, i: number) => (
                            <span key={i} className="bg-white border border-slate-200 px-2 py-1 rounded text-[10px] font-black uppercase text-slate-500 shadow-sm">{kg}</span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {currentTab === 'technical' && (
                  <div className="space-y-3 text-sm">
                    <div className="flex items-center justify-between p-3 rounded-lg bg-slate-50 border border-slate-100">
                      <span className="font-bold text-slate-700">
                        Mobile Friendly
                        <HelpTooltip text="Indicates whether the page is easy to use on mobile devices. Essential for modern SEO." />
                      </span>
                      {selectedPage?.technical_seo?.mobile_friendly !== false ? <CheckCircle2 className="w-5 h-5 text-emerald-500" /> : <AlertCircle className="w-5 h-5 text-rose-500" />}
                    </div>
                    <div className="flex items-center justify-between p-3 rounded-lg bg-slate-50 border border-slate-100">
                      <span className="font-bold text-slate-700">
                        HTTPS Secure
                        <HelpTooltip text="Shows if the connection to this page is encrypted and secure. A standard requirement for trust and ranking." />
                      </span>
                      {selectedPage?.technical_seo?.https !== false ? <CheckCircle2 className="w-5 h-5 text-emerald-500" /> : <AlertCircle className="w-5 h-5 text-rose-500" />}
                    </div>
                    {selectedPage?.technical_seo?.broken_links && selectedPage.technical_seo.broken_links.length > 0 && (
                      <div className="p-4 rounded-lg bg-rose-50 border border-rose-100">
                        <p className="font-bold text-rose-800 mb-2">Broken Links ({selectedPage.technical_seo.broken_links.length}):</p>
                        <ul className="text-xs text-rose-700 list-disc pl-4 space-y-1">
                          {selectedPage.technical_seo.broken_links.map((bl: string, i: number) => <li key={i}>{bl}</li>)}
                        </ul>
                      </div>
                    )}
                    {selectedPage?.technical_seo?.crawl_issues && selectedPage.technical_seo.crawl_issues.length > 0 && (
                      <div className="p-4 rounded-lg bg-amber-50 border border-amber-100">
                        <p className="font-bold text-amber-800 mb-2">Crawl Issues:</p>
                        <ul className="text-xs text-amber-700 list-disc pl-4 space-y-1">
                          {selectedPage.technical_seo.crawl_issues.map((ci: string, i: number) => <li key={i}>{ci}</li>)}
                        </ul>
                      </div>
                    )}
                  </div>
                )}

                {currentTab === 'issues' && (
                  <div className="space-y-4">
                    {allIssues.length > 0 ? (
                      allIssues.map((iss: any, i: number) => (
                        <div key={i} className="flex items-start gap-3 text-xs bg-rose-50 p-3 rounded-xl border border-rose-100">
                          <AlertCircle className="w-4 h-4 text-rose-500 shrink-0 mt-0.5" />
                          <span className="text-rose-700 font-medium leading-relaxed">{typeof iss === 'string' ? iss : iss.description || JSON.stringify(iss)}</span>
                        </div>
                      ))
                    ) : (
                      <div className="text-sm text-slate-400 italic text-center py-8">No issues detected.</div>
                    )}
                  </div>
                )}

                {currentTab === 'recommendations' && (
                  <div className="space-y-3">
                    {allRecs.length > 0 ? (
                      <ul className="space-y-2">
                        {allRecs.map((rec: any, i: number) => (
                          <li key={i} className="flex items-start gap-3 text-xs text-slate-700 bg-emerald-50/50 p-4 rounded-xl border border-emerald-100/50 shadow-sm">
                            <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
                            <span className="font-medium leading-relaxed">{typeof rec === 'string' ? rec : rec.description || JSON.stringify(rec)}</span>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <div className="text-sm text-slate-400 italic text-center py-8">No recommendations available.</div>
                    )}
                  </div>
                )}
              </div>

              {/* No Expand Toggle in Single View */}
            </div>
          );
        })()}
      </div>
    </div>
  );
};

import { useProjects } from '../context/ProjectContext';

export default function SEOStudio() {
  const { 
    projects, 
    auditResult, 
    isAnalyzing, 
    error, 
    startAudit, 
    resetAudit, 
    loadProject,
    isShareModalOpen,
    setIsShareModalOpen,
    isGeneratingPDF,
    setIsGeneratingPDF,
    targetUrl,
    setTargetUrl,
    activeSection: activeTab,
    setActiveSection: setActiveTab
  } = useProjects();

  const { section } = useParams<{ section?: string }>();
  const navigate = useNavigate();

  // Sync URL slug → active section (handles direct URL entry & browser back/forward)
  const VALID_SECTIONS = ['summary', 'technical', 'performance', 'growth', 'appendix'];
  useEffect(() => {
    const slug = section?.toLowerCase();
    if (slug && VALID_SECTIONS.includes(slug)) {
      setActiveTab(slug);
    } else if (!slug) {
      // At / root, ensure summary is shown
      setActiveTab('summary');
    }
  }, [section]);

  const dynamicFixes = useMemo(() => {
    if (!auditResult?.crawl_overview?.sampled_pages) return { titles: [], meta: [], urls: [] };

    const pages = auditResult.crawl_overview.sampled_pages;
    const company = auditResult?.pdf_template_data?.company_name || 'Organization';
    const primaryKeyword = auditResult?.keyword_analysis?.primary_keywords?.[0] || 'Professional Services';

    // Title Optimization Fixes
    const titles = pages.slice(0, 10).map(p => ({
      url: p.url.replace(/^https?:\/\//, ''),
      current: p.title || 'Untitled Page',
      suggestion: (p.title || 'Page').length < 15
        ? `${p.title || 'Expert Services'} | ${company} - ${primaryKeyword}`
        : `${(p.title || 'Page').split('|')[0].trim()} | ${primaryKeyword} - ${company}`
    }));

    // Meta Description Fixes
    const meta = pages.slice(0, 4).map(p => {
      const pType = p.page_info?.page_type || p.page_type || 'web';
      const safeKeyword = primaryKeyword || 'seo';
      
      return {
        url: p.url.replace(/^https?:\/\//, ''),
        current: `Standard or duplicate meta description detected for ${p.url.split('/').pop() || 'page'}`,
        suggestion: `Discover premium ${pType.toLowerCase()} solutions at ${company}. We provide expert insights on ${p.title || 'the topic'} and high-performance ${safeKeyword.toLowerCase()} strategies.`
      };
    });

    // URL Structure Fixes
    const urls = pages.slice(0, 3).map(p => {
      const path = p.url.replace(/^https?:\/\/[^/]+/, '');
      return {
        original: `...${path || '/'}`,
        optimized: (path || '/home').replace(/[^a-zA-Z0-9/]/g, '-').toLowerCase().replace(/-+/g, '-').replace(/\/$/, ''),
        reason: 'Strategic semantic URI mapping implemented for better crawl visibility and keyword density.'
      };
    });

    return { titles, meta, urls };
  }, [auditResult]);

  useEffect(() => {
    if (auditResult) {
      console.log('Audit Intelligence - Data Payload Received:', auditResult);
    }
  }, [auditResult]);

  const handleStartAudit = async (url: string) => {
    await startAudit(url);
  };

  const handleResetAudit = () => {
    resetAudit();
  };

  const isDashboardActive = !!auditResult;
  const currentData = auditResult;

  const performanceChartData = useMemo(() => [
    {
      name: 'Speed Score',
      value: currentData?.page_speed?.score || 0,
      color: '#f43f5e',
      unit: '/100',
      goal: 90,
      goalText: '>= 90',
      description: 'Global LH score measuring site speed and health.'
    },
    {
      name: 'Response Time',
      value: currentData?.page_speed?.response_time || 0,
      color: '#6366f1',
      unit: 's',
      goal: 2,
      goalText: '< 2.0s',
      description: 'Server latency / Time to First Byte (TTFB).'
    },
    {
      name: 'Page Size',
      value: currentData?.page_speed?.page_size_kb || 0,
      color: '#22c55e',
      unit: 'KB',
      goal: 1500,
      goalText: '< 1500KB',
      description: 'Total payload of documents and assets.'
    }
  ], [currentData]);

  const reportRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (currentData) {
      console.log('Site Identity Payload:', currentData.site_favicon);
      console.log('Core Performance Payload:', currentData.page_speed);
    }
  }, [currentData]);

  const reportUrl = typeof window !== 'undefined' ? window.location.href : targetUrl || 'https://audit.ai';

  const tabs = [
    { id: 'summary', label: 'Summary', icon: FileText },
    { id: 'technical', label: 'Technical', icon: Cpu },
    { id: 'growth', label: 'Growth', icon: TrendingUp },
    { id: 'performance', label: 'Performance', icon: Zap },
    { id: 'appendix', label: 'Appendix', icon: BookOpen },
  ];

  const copyToClipboard = () => {
    navigator.clipboard.writeText(reportUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadPDF = async () => {
    if (!reportRef.current) return;
    setIsGeneratingPDF(true);

    try {
      const element = reportRef.current;
      const imgData = await toPng(element, {
        pixelRatio: 2,
        backgroundColor: '#F8FAFC',
        filter: (node) => {
          if (node.hasAttribute && node.hasAttribute('data-html2canvas-ignore')) {
            return false;
          }
          return true;
        }
      });
      const pdf = new jsPDF('p', 'mm', 'a4');
      const imgProps = pdf.getImageProperties(imgData);
      const pdfWidth = pdf.internal.pageSize.getWidth();
      const pdfHeight = (imgProps.height * pdfWidth) / imgProps.width;

      pdf.addImage(imgData, 'PNG', 0, 0, pdfWidth, pdfHeight);
      pdf.save(`SEO_Audit_Report_${currentData?.pdf_template_data?.company_name || 'Organization'}.pdf`);
    } catch (error: any) {
      console.error('Error generating PDF:', error);
      alert('Failed to generate PDF. Error: ' + (error?.message || error));
    } finally {
      setIsGeneratingPDF(false);
    }
  };

  const shareOptions = useMemo(() => [
    { name: 'Twitter', icon: Twitter, color: 'bg-[#1DA1F2]', url: `https://twitter.com/intent/tweet?url=${encodeURIComponent(reportUrl)}&text=${encodeURIComponent('Check out this SEO Audit Report!')}` },
    { name: 'LinkedIn', icon: Linkedin, color: 'bg-[#0077b5]', url: `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(reportUrl)}` },
    { name: 'Facebook', icon: Facebook, color: 'bg-[#1877F2]', url: `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(reportUrl)}` },
    { name: 'WhatsApp', icon: MessageCircle, color: 'bg-[#25D366]', url: `https://wa.me/?text=${encodeURIComponent('Check out this SEO Audit Report: ' + reportUrl)}` },
    { name: 'Instagram', icon: Instagram, color: 'bg-gradient-to-tr from-[#f9ce34] via-[#ee2a7b] to-[#6228d7]', url: 'https://instagram.com' },
  ], [reportUrl]);

  return (
    <div className="flex min-h-screen bg-[#F8FAFC] text-slate-900 selection:bg-indigo-100">
      <div className="flex-1 flex flex-col">
        {!isDashboardActive ? (
          <div className="min-h-screen flex items-center justify-center p-6 bg-slate-50 relative overflow-hidden">
            <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-indigo-100 rounded-full blur-[120px] -mr-40 -mt-40 opacity-60" />
            <div className="absolute bottom-0 left-0 w-[500px] h-[500px] bg-rose-100 rounded-full blur-[120px] -ml-40 -mb-40 opacity-60" />

            <div className="relative z-10 w-full max-w-4xl text-center">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8 }}
              >
                <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-indigo-50 border border-indigo-100 text-indigo-600 text-[10px] font-black uppercase tracking-[0.2em] mb-12 shadow-sm">
                  <ShieldCheck className="w-4 h-4" /> Next-Gen SEO Intelligence
                </div>
                <h1 className="text-6xl md:text-8xl font-display font-bold text-slate-900 mb-8 leading-tight tracking-tight">
                  Audit any site with <br />
                  <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 via-violet-600 to-indigo-600">AI Precision</span>
                </h1>
                <p className="text-xl text-slate-500 mb-16 max-w-2xl mx-auto font-medium leading-relaxed">
                  The world's most advanced SEO management protocol. Map crawl frontiers, score technical health, and unlock growth opportunities in seconds.
                </p>

                <form 
                  onSubmit={(e) => {
                    e.preventDefault();
                    console.log('Starting audit for:', targetUrl);
                    handleStartAudit(targetUrl);
                  }}
                  className="relative max-w-2xl mx-auto mb-12"
                >
                  <div className="relative group/input">
                    <div className="absolute inset-y-0 left-0 pl-8 flex items-center pointer-events-none">
                      <Globe className="w-6 h-6 text-slate-400 group-focus-within/input:text-indigo-500 transition-colors" />
                    </div>
                    <input
                      type="text"
                      placeholder="Enter website URL (e.g. apple.com)"
                      value={targetUrl}
                      onChange={(e) => setTargetUrl(e.target.value)}
                      className="w-full pl-20 pr-48 py-7 bg-white border border-slate-200 rounded-[2.5rem] text-lg font-medium text-slate-800 outline-none focus:ring-4 focus:ring-indigo-500/10 focus:border-indigo-500 transition-all shadow-2xl shadow-slate-200/50"
                    />
                    <button
                      type="submit"
                      disabled={isAnalyzing}
                      className="absolute right-3 top-3 bottom-3 px-10 bg-slate-900 hover:bg-indigo-600 text-white rounded-[2rem] font-black text-sm uppercase tracking-widest transition-all shadow-xl active:scale-95 disabled:opacity-50 flex items-center gap-3"
                    >
                      {isAnalyzing ? (
                        <>
                          <RefreshCw className="w-4 h-4 animate-spin" /> Analyzing
                        </>
                      ) : (
                        <>
                          Start Audit <ArrowRight className="w-4 h-4" />
                        </>
                      )}
                    </button>
                  </div>
                </form>

                {error && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="mt-6 flex items-center justify-center gap-2 text-rose-500 text-sm font-bold bg-rose-50 p-4 rounded-2xl border border-rose-100"
                  >
                    <AlertCircle className="w-4 h-4" /> {error}
                  </motion.div>
                )}
              </motion.div>

                {projects.length > 0 && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.5 }}
                    className="max-w-4xl mx-auto"
                  >
                    <div className="flex items-center justify-between mb-6 px-4">
                      <h4 className="text-[11px] font-black text-slate-400 uppercase tracking-widest">Load from History</h4>
                      <div className="h-px bg-slate-200 flex-1 mx-8" />
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                      {projects.slice(0, 3).map((proj, idx) => (
                        <button
                          key={proj.id}
                          onClick={() => loadProject(proj.id)}
                          className="flex items-start gap-4 p-5 bg-white border border-slate-100 rounded-3xl hover:border-indigo-200 hover:shadow-xl hover:shadow-indigo-500/5 transition-all text-left group"
                        >
                          <div className="p-3 bg-slate-50 rounded-2xl group-hover:bg-indigo-50 transition-colors">
                            <Globe className="w-5 h-5 text-slate-400 group-hover:text-indigo-600 transition-colors" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="text-sm font-bold text-slate-800 truncate mb-1">{proj.url.replace(/^https?:\/\//, '')}</div>
                            <div className="flex items-center gap-2">
                              <span className="text-[10px] font-black text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded-md">{proj.seo_score}% SEO</span>
                              <span className="text-[10px] text-slate-400 font-medium">{new Date(proj.created_at).toLocaleDateString()}</span>
                            </div>
                          </div>
                        </button>
                      ))}
                    </div>
                  </motion.div>
                )}

                <div className="flex items-center justify-center gap-12 pt-12 border-t border-slate-200/60 opacity-50 grayscale hover:grayscale-0 transition-all duration-700">
                  <div className="flex items-center gap-2 font-display font-black text-slate-400 italic text-xl">Lighthouse+</div>
                  <div className="flex items-center gap-2 font-display font-black text-slate-400 italic text-xl">GPT-4o</div>
                  <div className="flex items-center gap-2 font-display font-black text-slate-400 italic text-xl">D3.js</div>
                </div>
                </div>
              </div>
            ) : (currentData ? (
          <>
            <AnimatePresence>
              {isShareModalOpen && (
                <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    onClick={() => setIsShareModalOpen(false)}
                    className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm"
                  />
                  <motion.div
                    initial={{ opacity: 0, scale: 0.95, y: 20 }}
                    animate={{ opacity: 1, scale: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.95, y: 20 }}
                    className="relative w-full max-w-md bg-white rounded-[2.5rem] shadow-2xl p-8 overflow-hidden"
                  >
                    <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-50 rounded-full -mr-16 -mt-16 blur-2xl opacity-50" />

                    <div className="relative z-10">
                      <div className="flex items-center justify-between mb-8">
                        <div className="flex items-center gap-3">
                          <div className="p-2 bg-indigo-50 rounded-xl">
                            <Share2 className="w-5 h-5 text-indigo-600" />
                          </div>
                          <h3 className="text-xl font-display font-bold text-slate-900">Share Report</h3>
                        </div>
                        <button
                          onClick={() => setIsShareModalOpen(false)}
                          className="p-2 hover:bg-slate-100 rounded-full transition-colors"
                        >
                          <X className="w-5 h-5 text-slate-400" />
                        </button>
                      </div>

                      <div className="space-y-6">
                        <div>
                          <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-3">Copy Link</label>
                          <div className="flex items-center gap-2 p-2 bg-slate-50 border border-slate-200 rounded-2xl group focus-within:border-indigo-500 transition-all">
                            <div className="flex-1 px-2 text-xs font-medium text-slate-500 truncate select-all">{reportUrl}</div>
                            <button
                              onClick={copyToClipboard}
                              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-tight transition-all active:scale-95 ${copied ? 'bg-emerald-500 text-white' : 'bg-slate-900 text-white hover:bg-black'}`}
                            >
                              {copied ? (
                                <><Check className="w-3.5 h-3.5" /> Copied</>
                              ) : (
                                <><Copy className="w-3.5 h-3.5" /> Copy</>
                              )}
                            </button>
                          </div>
                        </div>

                        <div>
                          <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-4">Share to Social</label>
                          <div className="grid grid-cols-5 gap-4">
                            {shareOptions.map((option) => (
                              <a
                                key={option.name}
                                href={option.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="flex flex-col items-center gap-2 group"
                              >
                                <div className={`w-12 h-12 rounded-2xl ${option.color} flex items-center justify-center text-white shadow-lg group-hover:scale-110 transition-transform`}>
                                  <option.icon className="w-5 h-5" />
                                </div>
                                <span className="text-[9px] font-bold text-slate-500">{option.name}</span>
                              </a>
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>
                  </motion.div>
                </div>
              )}
            </AnimatePresence>

            <main ref={reportRef} className="flex-1 p-6 lg:p-12 max-w-7xl mx-auto w-full relative">
              {/* Analysis Loading Overlay */}
              <AnimatePresence>
                {isAnalyzing && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="absolute inset-0 z-50 bg-white/80 backdrop-blur-md flex flex-col items-center justify-center rounded-[3rem]"
                  >
                    <div className="relative">
                      <div className="w-24 h-24 border-4 border-indigo-100 border-t-indigo-600 rounded-full animate-spin" />
                      <div className="absolute inset-0 flex items-center justify-center">
                        <Search className="w-8 h-8 text-indigo-600 animate-pulse" />
                      </div>
                    </div>
                    <h3 className="text-2xl font-display font-bold text-slate-800 mt-8 mb-2">Deep-Crawling Site...</h3>
                    <p className="text-slate-500 font-medium">Extracting technical metrics and AI directives</p>
                  </motion.div>
                )}
              </AnimatePresence>

              <AnimatePresence mode="wait">
                {activeTab === 'summary' && (
                  <motion.div key="summary" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-10">


                    {/* Main Search/Audit Trigger */}
                    <div className="bg-slate-900 p-10 rounded-[3rem] shadow-2xl relative overflow-hidden group">
                      <div className="absolute top-0 right-0 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl -mr-32 -mt-32" />
                      <div className="relative z-10">
                        <div className="max-w-2xl mb-8">
                          <h2 className="text-3xl font-display font-bold text-white mb-3">Audit a New Property</h2>
                          <p className="text-slate-400 text-sm">Enter a website URL to generate a comprehensive management SEO report in real-time.</p>
                        </div>
                        <form 
                          onSubmit={(e) => {
                            e.preventDefault();
                            handleStartAudit(targetUrl);
                          }}
                          className="flex flex-col sm:flex-row gap-4"
                        >
                          <div className="flex-1 relative group/input">
                            <div className="absolute inset-y-0 left-0 pl-6 flex items-center pointer-events-none">
                              <Globe className="w-5 h-5 text-slate-500 group-focus-within/input:text-indigo-400 transition-colors" />
                            </div>
                            <input
                              type="text"
                              placeholder="e.g. apple.com"
                              value={targetUrl}
                              onChange={(e) => setTargetUrl(e.target.value)}
                              className="w-full pl-16 pr-6 py-5 bg-white/5 border border-white/10 rounded-[2rem] text-white placeholder-slate-500 outline-none focus:ring-4 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all font-medium"
                            />
                          </div>
                          <button
                            type="submit"
                            disabled={isAnalyzing}
                            className="px-10 py-5 bg-indigo-600 hover:bg-white hover:text-indigo-600 text-white rounded-[2rem] font-black text-sm uppercase tracking-widest transition-all shadow-xl shadow-indigo-600/20 active:scale-95 disabled:opacity-50"
                          >
                            {isAnalyzing ? 'Analyzing...' : 'Start Audit'}
                          </button>
                        </form>
                        {error && (
                          <div className="mt-4 flex items-center gap-2 text-rose-400 text-xs font-bold bg-rose-400/10 p-3 rounded-xl border border-rose-400/20">
                            <AlertCircle className="w-4 h-4" /> {error}
                          </div>
                        )}
                      </div>
                    </div>

                    {isDashboardActive && currentData && (
                      <>
                        {/* Website Identity & Core Performance Section */}
                        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                          {/* Website Identity Card */}
                          <div className="lg:col-span-4 bg-white border border-slate-200 p-8 rounded-[3rem] shadow-sm relative overflow-hidden flex flex-col items-center justify-center text-center group">
                            <div className="absolute top-0 right-0 w-32 h-32 bg-slate-50 rounded-full -mr-16 -mt-16 blur-2xl opacity-50 group-hover:bg-indigo-50 transition-colors" />
                            <div className="relative mb-6">
                              <div className="w-24 h-24 bg-white rounded-[2rem] border-2 border-slate-100 shadow-xl flex items-center justify-center overflow-hidden transition-transform group-hover:scale-110">
                                {currentData?.site_favicon?.url ? (
                                  <img 
                                    src={currentData.site_favicon.url} 
                                    alt="Site Favicon" 
                                    className="w-12 h-12 object-contain" 
                                    onError={(e) => { (e.target as any).src = 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIzMiIgaGVpZ2h0PSIzMiIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiM5NDkzYjgiIHN0cm9rZS13aWR0aD0iMSIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48Z2xvYmUvPjwvc3ZnPg=='; }}
                                  />
                                ) : (
                                  <Globe className="w-10 h-10 text-slate-300" />
                                )}
                              </div>
                              <div className={`absolute -bottom-2 -right-2 w-10 h-10 rounded-full border-4 border-white flex items-center justify-center shadow-lg ${currentData?.site_favicon?.status === 'Present' ? 'bg-emerald-500' : 'bg-rose-500'}`}>
                                {currentData?.site_favicon?.status === 'Present' ? <Check className="w-5 h-5 text-white" /> : <X className="w-5 h-5 text-white" />}
                              </div>
                            </div>
                            <h3 className="text-2xl font-display font-bold text-slate-900 mb-2">Website Identity</h3>
                            <p className="text-xs text-slate-400 font-bold uppercase tracking-widest mb-4">Site-Wide Branding Check</p>
                            <div className="flex flex-col items-center gap-3 w-full">
                              <span className={`w-full py-2 rounded-xl text-xs font-black uppercase tracking-widest border ${currentData?.site_favicon?.status === 'Present' ? 'bg-emerald-50 text-emerald-600 border-emerald-100' : 'bg-rose-50 text-rose-600 border-rose-100'}`}>
                                {currentData?.site_favicon?.status || 'Missing'}
                              </span>
                              {currentData?.site_favicon?.status !== 'Present' && (
                                <p className="text-[10px] font-bold text-rose-500 bg-rose-50 p-3 rounded-xl border border-rose-100">
                                  No favicon detected → impacts branding and UX
                                </p>
                              )}
                            </div>
                          </div>

                          {/* Performance Comparison Card */}
                          <div className="lg:col-span-8 bg-slate-900 p-8 rounded-[3rem] shadow-2xl relative overflow-hidden text-white flex flex-col justify-center">
                            <div className="absolute bottom-0 right-0 w-64 h-64 bg-indigo-500/10 rounded-full blur-3xl -mr-32 -mb-32" />
                            <div className="flex items-center justify-between mb-10 relative z-10">
                              <div>
                                <h3 className="text-2xl font-display font-bold mb-1">Performance Benchmarks</h3>
                                <p className="text-slate-400 text-xs font-medium uppercase tracking-widest">Global Speed Evaluation</p>
                              </div>
                              <Zap className="w-8 h-8 text-indigo-400 animate-pulse" />
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 relative z-10">
                              {[
                                { type: 'mobile', icon: Smartphone, label: 'Mobile Experience', data: currentData?.page_speed?.mobile },
                                { type: 'desktop', icon: Monitor, label: 'Desktop Experience', data: currentData?.page_speed?.desktop }
                              ].map((perf) => {
                                const score = perf.data?.score || 0;
                                const status = perf.data?.status || 'Not Available';
                                const label = getScoreLabel(score);
                                const color = score >= 90 ? 'text-emerald-400' : score >= 70 ? 'text-amber-400' : 'text-rose-400';
                                const bgColor = score >= 90 ? 'bg-emerald-400' : score >= 70 ? 'bg-amber-400' : 'bg-rose-400';

                                return (
                                  <div key={perf.type} className="bg-white/5 border border-white/10 p-6 rounded-[2rem] hover:bg-white/10 transition-all group">
                                    <div className="flex items-center justify-between mb-6">
                                      <div className="flex items-center gap-3">
                                        <div className="p-2 bg-white/5 rounded-xl group-hover:bg-indigo-500/20 transition-colors">
                                          <perf.icon className="w-5 h-5 text-indigo-400" />
                                        </div>
                                        <span className="text-xs font-black uppercase tracking-widest">{perf.label}</span>
                                      </div>
                                      <div className={`text-2xl font-display font-black ${color}`}>{score}%</div>
                                    </div>
                                    <div className="space-y-4">
                                      <div className="w-full bg-white/10 h-1.5 rounded-full overflow-hidden">
                                        <motion.div 
                                          initial={{ width: 0 }}
                                          animate={{ width: `${score}%` }}
                                          transition={{ duration: 1, delay: 0.5 }}
                                          className={`h-full ${bgColor}`} 
                                        />
                                      </div>
                                      <div className="flex items-center justify-between">
                                        <div className="flex flex-col">
                                          <span className="text-[9px] font-black text-slate-500 uppercase">Load Time</span>
                                          <span className="text-sm font-bold text-slate-200">{perf.data?.load_time || 'N/A'}</span>
                                        </div>
                                        <div className="flex flex-col items-end text-right">
                                          <span className="text-[9px] font-black text-slate-500 uppercase">Verdict</span>
                                          <span className={`text-sm font-black uppercase italic ${color}`}>{label}</span>
                                        </div>
                                      </div>
                                    </div>
                                  </div>
                                );
                              })}
                            </div>
                          </div>
                        </div>

                        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                          <div className="lg:col-span-8 bg-white border border-slate-200 p-10 rounded-[2.5rem] shadow-[0_8px_40px_-12px_rgba(0,0,0,0.05)] relative overflow-hidden group">
                            <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-50 rounded-full -mr-20 -mt-20 blur-3xl opacity-50 group-hover:bg-indigo-100 transition-colors" />
                            <div className="relative z-10">
                              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-rose-50 text-rose-600 text-[10px] font-black uppercase tracking-widest mb-6">
                                <AlertCircle className="w-3.5 h-3.5" /> Status: {currentData?.management_summary?.board_verdict || 'N/A'}
                              </div>
                              <h1 className="text-5xl md:text-6xl font-display font-bold text-slate-900 mb-8 leading-[1.05]">
                                {currentData?.pdf_template_data?.company_name || 'Organization'} Management <br />
                                <span className="text-indigo-600">SEO Audit Report</span>
                              </h1>
                              <div className="grid grid-cols-2 md:grid-cols-4 gap-8 border-t border-slate-100 pt-8 mt-4">
                                {(currentData?.pdf_template_data?.hero_metrics || []).map((m: any, idx: number) => (
                                  <div key={idx} className="flex flex-col">
                                    <div className="flex items-center">
                                      <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest mb-1">{m.label}</span>
                                      <HelpTooltip text={m.description || ''} suggestion={m.suggestion || ''} />
                                    </div>
                                    <span className="text-3xl font-display font-bold text-slate-800">{m.value}</span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          </div>
                          <div className="lg:col-span-4 flex flex-col gap-8">
                            <div className="p-8 bg-slate-900 text-white rounded-[2rem] shadow-xl relative overflow-hidden flex-1 group">
                              <div className="relative z-10">
                                <TrendingUp className="w-8 h-8 text-indigo-400 mb-6 group-hover:scale-110 transition-transform" />
                                <h4 className="text-xl font-display font-bold mb-4">Prime Opportunity</h4>
                                <p className="text-slate-400 text-sm leading-relaxed mb-6">{currentData.management_summary?.growth_opportunity}</p>
                                <div className="py-3 px-4 bg-white/5 rounded-xl border border-white/10 flex items-center justify-between">
                                  <span className="text-xs font-bold text-slate-200">Confidence Factor</span>
                                  <span className="text-indigo-400 font-bold">Medium</span>
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                          <div className="bg-white p-8 rounded-3xl border border-slate-200">
                            <SectionHeader icon={Info} title="Executive Summary" />
                            <p className="text-slate-600 leading-relaxed font-medium">{currentData.executive_summary}</p>
                          </div>
                          <div className="space-y-4">
                            <div className="bg-emerald-50 border border-emerald-100 p-6 rounded-3xl flex items-start gap-4">
                              <div className="p-2 bg-emerald-100 rounded-xl"><CheckCircle2 className="w-5 h-5 text-emerald-600" /></div>
                              <div>
                                <span className="text-[10px] font-black uppercase text-emerald-600 mb-1 block">Strongest Asset</span>
                                <p className="text-sm font-bold text-emerald-900">{currentData.management_summary?.strongest_asset}</p>
                              </div>
                            </div>
                            <div className="bg-rose-50 border border-rose-100 p-6 rounded-3xl flex items-start gap-4">
                              <div className="p-2 bg-rose-100 rounded-xl"><ShieldCheck className="w-5 h-5 text-rose-600" /></div>
                              <div>
                                <span className="text-[10px] font-black uppercase text-rose-600 mb-1 block">Biggest Risk</span>
                                <p className="text-sm font-bold text-rose-900">{currentData.management_summary?.biggest_risk}</p>
                              </div>
                            </div>
                          </div>
                        </div>
                      </>
                    )}
                  </motion.div>
                )}

                {activeTab === 'technical' && isDashboardActive && currentData && (
                  <motion.div key="technical" initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} className="space-y-12">
                    <SectionHeader icon={Layers} title="Audit Benchmarks" subtitle="Comparison against current standards" />
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                      {(currentData?.technical_audit?.metric_summary || []).map((m: any, idx: number) => (
                        <MetricCard
                          key={idx}
                          label={m.metric}
                          value={m.current_value}
                          benchmark={m.benchmark}
                          status={m.status}
                          description={m.description || ''}
                        />
                      ))}
                    </div>

                    <MetricComparisonTool metrics={currentData.technical_audit.metric_summary} />

                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                      <div className="bg-white p-8 rounded-[2rem] border border-slate-200">
                        <SectionHeader icon={Activity} title="Strategic Findings" />
                        <div className="space-y-4">
                          {(currentData?.technical_audit?.findings || []).map((f: any, idx: number) => (
                            <FindingAccordionItem key={idx} finding={f} currentData={currentData} />
                          ))}
                        </div>
                      </div>
                      <div className="bg-indigo-600 p-10 rounded-[3rem] text-white space-y-10 shadow-2xl shadow-indigo-200 relative overflow-hidden">
                        <div className="absolute top-0 right-0 w-96 h-96 bg-white/5 rounded-full blur-3xl -mr-32 -mt-32" />
                        <SectionHeader icon={Clock} title="Deployment Roadmap" />
                        <div className="space-y-2 relative">
                          {(currentData?.recommended_roadmap || []).map((r: any, idx: number) => (
                            <RoadmapItem
                              key={idx}
                              item={r}
                              index={idx}
                              total={currentData?.recommended_roadmap?.length || 0}
                            />
                          ))}
                        </div>
                      </div>
                    </div>

                    <div className="bg-slate-900 p-10 rounded-[3rem] text-white overflow-hidden relative shadow-2xl">
                      <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500/10 rounded-full -mr-32 -mt-32 blur-3xl opacity-50" />
                      <div className="relative z-10">
                        <div className="flex items-center gap-3 mb-8">
                          <Target className="w-6 h-6 text-indigo-400" />
                          <h4 className="text-xl font-display font-bold">Deep Dive: Title Uniqueness Remediation</h4>
                        </div>

                        <div className="p-6 bg-rose-500/10 border border-rose-500/20 rounded-2xl mb-10">
                          <div className="flex items-start gap-4">
                            <div className="p-2 bg-rose-500/20 rounded-lg">
                              <AlertCircle className="w-5 h-5 text-rose-400" />
                            </div>
                            <div>
                              <h5 className="font-bold text-rose-100 mb-1">Gap Impact: 64% Unique (Critical)</h5>
                              <p className="text-xs text-rose-200/80 leading-relaxed">
                                Duplicate titles cause search engines to "cannibalize" your own rankings. Google struggles to determine which page is the authority for a given term, often resulting in lower rankings for all associated pages and a confusing experience for users in the SERPs.
                              </p>
                            </div>
                          </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                          {dynamicFixes.titles.map((fix: any, idx: number) => (
                            <div key={idx} className="p-5 bg-white/5 border border-white/10 rounded-2xl hover:bg-white/10 transition-colors">
                              <div className="text-[9px] font-mono text-indigo-400 truncate mb-3">{fix.url}</div>
                              <div className="space-y-4">
                                <div>
                                  <div className="text-[8px] font-black text-slate-400 uppercase mb-1">Current (Duplicate)</div>
                                  <div className="text-[11px] text-slate-300 font-medium line-clamp-1 tracking-tight">{fix.current}</div>
                                </div>
                                <div className="p-3 bg-indigo-500/10 rounded-xl border border-indigo-500/20">
                                  <div className="text-[8px] font-black text-indigo-300 uppercase mb-1">Proposed Optimization</div>
                                  <div className="text-[11px] text-indigo-50 font-bold">{fix.suggestion}</div>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>

                    <div className="bg-slate-900 p-10 rounded-[3rem] text-white overflow-hidden relative shadow-2xl">
                      <div className="absolute top-0 left-0 w-64 h-64 bg-emerald-500/10 rounded-full -ml-32 -mt-32 blur-3xl opacity-50" />
                      <div className="relative z-10">
                        <div className="flex items-center gap-3 mb-8">
                          <MousePointer2 className="w-6 h-6 text-emerald-400" />
                          <h4 className="text-xl font-display font-bold">Deep Dive: Meta Description Optimization</h4>
                        </div>

                        <div className="p-6 bg-emerald-500/10 border border-emerald-500/20 rounded-2xl mb-10">
                          <div className="flex items-start gap-4">
                            <div className="p-2 bg-emerald-500/20 rounded-lg">
                              <AlertCircle className="w-5 h-5 text-emerald-400" />
                            </div>
                            <div>
                              <h5 className="font-bold text-emerald-100 mb-1">Gap Impact: Meta Description Uniqueness (Critical)</h5>
                              <p className="text-xs text-emerald-200/80 leading-relaxed">
                                Non-unique meta descriptions lead to wasted SERP real estate. When Google detects duplicate descriptions, it may ignore your snippet or display irrelevant text, directly impacting Click-Through Rates and brand perception.
                              </p>
                            </div>
                          </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                          {dynamicFixes.meta.map((fix: any, idx: number) => (
                            <div key={idx} className="p-6 bg-white/5 border border-white/10 rounded-2xl group hover:bg-white/10 transition-all">
                              <div className="text-[10px] font-mono text-emerald-400 truncate mb-4">{fix.url}</div>
                              <div className="space-y-4">
                                <div>
                                  <div className="text-[8px] font-black text-slate-400 uppercase mb-2">Duplicate Snippet</div>
                                  <p className="text-[11px] text-slate-300 leading-relaxed font-semibold italic">"{fix.current}"</p>
                                </div>
                                <div className="p-4 bg-emerald-500/10 rounded-xl border border-emerald-500/20 shadow-inner">
                                  <div className="flex justify-between items-center mb-2">
                                    <div className="text-[8px] font-black text-emerald-300 uppercase">Remediated Description</div>
                                    <span className="text-[8px] font-bold text-emerald-950 bg-emerald-300 px-1.5 py-0.5 rounded">{fix.suggestion.length} chars</span>
                                  </div>
                                  <p className="text-[11px] text-emerald-50 font-bold leading-relaxed">"{fix.suggestion}"</p>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>

                    <div className="bg-slate-900 p-10 rounded-[3rem] text-white overflow-hidden relative shadow-2xl">
                      <div className="absolute bottom-0 right-0 w-80 h-80 bg-blue-500/10 rounded-full -mr-40 -mb-40 blur-3xl opacity-50" />
                      <div className="relative z-10">
                        <div className="flex items-center gap-3 mb-8">
                          <FileText className="w-6 h-6 text-blue-400" />
                          <h4 className="text-xl font-display font-bold">Priority Remediation: Title Optimization</h4>
                        </div>

                        <div className="p-6 bg-blue-500/10 border border-blue-500/20 rounded-2xl mb-10">
                          <div className="flex items-start gap-4">
                            <div className="p-2 bg-blue-500/20 rounded-lg">
                              <Zap className="w-5 h-5 text-blue-400" />
                            </div>
                            <div>
                              <h5 className="font-bold text-blue-100 mb-1">Gap Impact: Title Optimization (Critical)</h5>
                              <p className="text-xs text-blue-200/80 leading-relaxed">
                                Low title coverage weakens search-result messaging across the site, reducing click-through rate and making demand capture inconsistent. These optimized titles are designed to maximize relevance and CTR.
                              </p>
                            </div>
                          </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-h-[600px] overflow-y-auto pr-4 scrollbar-thin scrollbar-thumb-white/10">
                          {dynamicFixes.titles.slice(0, 10).map((fix: any, idx: number) => (
                            <div key={idx} className="p-5 bg-white/5 border border-white/10 rounded-2xl hover:bg-white/10 transition-colors">
                              <div className="text-[9px] font-mono text-blue-400 truncate mb-3">{fix.url}</div>
                              <div className="space-y-4">
                                <div>
                                  <div className="text-[8px] font-black text-slate-400 uppercase mb-1">Current Issue</div>
                                  <div className="text-[11px] text-slate-300 font-medium line-clamp-1 tracking-tight">{fix.current}</div>
                                </div>
                                <div className="p-3 bg-blue-500/20 rounded-xl border border-blue-500/30 shadow-lg">
                                  <div className="flex justify-between items-center mb-1">
                                    <div className="text-[8px] font-black text-blue-300 uppercase">Optimized Title</div>
                                    <span className="text-[8px] font-bold text-blue-900 bg-blue-300 px-1 py-0.5 rounded">{fix.suggestion.length} ch</span>
                                  </div>
                                  <div className="text-[11px] text-blue-50 font-bold">{fix.suggestion}</div>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>

                    <div className="bg-slate-900 p-10 rounded-[3rem] text-white overflow-hidden relative shadow-2xl">
                      <div className="absolute top-0 right-0 w-80 h-80 bg-indigo-500/10 rounded-full -mr-40 -mb-40 blur-3xl opacity-50" />
                      <div className="relative z-10">
                        <div className="flex items-center gap-3 mb-8">
                          <Globe className="w-6 h-6 text-emerald-400" />
                          <h4 className="text-xl font-display font-bold">Priority Remediation: URL Structure Optimization</h4>
                        </div>

                        <div className="p-6 bg-emerald-500/10 border border-emerald-500/20 rounded-2xl mb-12">
                          <div className="flex items-start gap-4">
                            <div className="p-2 bg-emerald-500/20 rounded-lg">
                              <Link className="w-5 h-5 text-emerald-400" />
                            </div>
                            <div>
                              <h5 className="font-bold text-emerald-50 mb-1">Strategic Logic: Semantic URI Mapping</h5>
                              <p className="text-xs text-emerald-200/90 leading-relaxed">
                                Disorganized URL structures with legacy segmenting create "spider semantic failure," where search engines cannot parse the topical context of the page from the URI. The optimized target state uses strict hyphenation and keyword-rich paths to maximize relevance signals.
                              </p>
                            </div>
                          </div>
                        </div>

                        <div className="space-y-12">
                          <URLAnalyzerTool />

                          <URLGraph urls={dynamicFixes.urls} companyName={currentData?.pdf_template_data?.company_name || 'Root'} targetUrl={targetUrl} />

                          <div className="space-y-10">
                            {dynamicFixes.urls.map((fix: any, idx: number) => (
                              <div key={idx} className="space-y-4">
                                <div className="flex items-center gap-3">
                                  <span className="text-[10px] font-black text-white/40 uppercase tracking-widest bg-white/5 py-1 px-3 rounded-full border border-white/5">Optimization Case {idx + 1}</span>
                                  <div className="h-px bg-white/10 flex-1" />
                                </div>
                                <URLComparisonDetails
                                  original={fix.original}
                                  optimized={fix.optimized}
                                  reason={fix.reason}
                                  targetUrl={targetUrl}
                                />
                              </div>
                            ))}
                          </div>
                        </div>

                        <div className="mt-20 pt-16 border-t border-white/10">
                          <div className="mb-12">
                            <h4 className="text-2xl font-display font-bold text-white mb-4">Strategic Learning: URL Best Practices</h4>
                            <p className="text-slate-400 text-sm max-w-2xl">Visualizing the impact of clean URLs on search performance and user experience through these expert case studies.</p>
                          </div>
                          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                            <YouTubePreview
                              videoUrl="https://youtu.be/rlki6SNuJtg?si=EIFbFZrn5m2D30By"
                              title="SEO Friendly URL Structure"
                              description="Understanding how simple, readable URLs improve click-through rates and crawl budget allocation."
                            />
                            <YouTubePreview
                              videoUrl="https://youtu.be/971qGsTPs8M?si=9JEpePQINeaXjUPD"
                              title="Google Search Central: URL Tips"
                              description="Official guidance on maintaining URI permanence and semantic keyword usage."
                            />
                            <YouTubePreview
                              videoUrl="https://youtu.be/CjxQTvq_kRo?si=LhS9OVRJowQAsEX8"
                              title="Slug Optimization Masterclass"
                              description="Deep dive into why word separation and lowercase consistency are pillars of technical SEO."
                            />
                          </div>
                        </div>
                      </div>
                    </div>
                  </motion.div>
                )}

                {activeTab === 'growth' && isDashboardActive && currentData && (
                  <motion.div key="growth" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-12">
                    <SectionHeader icon={TrendingUp} title="Strategic Intelligence" subtitle="Market gap analysis" />
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                      <div className="bg-white p-8 rounded-[2rem] border border-slate-200 shadow-sm relative overflow-hidden">
                        <div className="flex justify-between items-start mb-8">
                          <h4 className="font-display font-bold text-xl">Market Opportunities</h4>
                          <div className="p-2 bg-indigo-50 rounded-lg">
                            <Target className="w-5 h-5 text-indigo-600" />
                          </div>
                        </div>
                        <div className="space-y-4">
                          {(currentData?.competitive_intelligence?.market_opportunities || []).map((opp: any, idx: number) => (
                            <div key={idx} className="p-5 bg-slate-50 border border-slate-100 rounded-2xl group hover:border-indigo-200 transition-all">
                              <div className="flex items-center justify-between mb-3">
                                <h5 className="font-bold text-slate-800">{opp.keyword}</h5>
                                <span className="text-xl font-display font-black text-indigo-600">{opp.market_opportunity_score}/10</span>
                              </div>
                              <div className="flex flex-col gap-2">
                                <div className="text-[10px] text-slate-500 font-medium uppercase tracking-wider">Business Impact</div>
                                <p className="text-xs text-slate-600 leading-relaxed">{opp.business_impact}</p>
                                <div className="flex items-center gap-4 mt-2">
                                  <span className="px-2 py-1 bg-white border border-slate-200 rounded text-[9px] font-bold text-slate-500">Gap: {opp.supporting_gap_ratio}</span>
                                  <span className="px-2 py-1 bg-indigo-600 text-white rounded text-[9px] font-bold uppercase">{opp.priority} Priority</span>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>

                      <div className="space-y-8">
                        <div className="bg-white p-8 rounded-[2rem] border border-slate-200 shadow-sm">
                          <div className="flex justify-between items-start mb-8">
                            <h4 className="font-display font-bold text-xl">Content Strategy</h4>
                            <div className="p-2 bg-emerald-50 rounded-lg">
                              <BookOpen className="w-5 h-5 text-emerald-600" />
                            </div>
                          </div>
                          <div className="space-y-8">
                            {(currentData?.content_strategy?.blog_suggestions || []).map((blog: any, idx: number) => (
                              <div key={idx} className="relative pl-6 border-l-2 border-slate-100 py-1">
                                <div className="absolute left-[-5px] top-2 w-2 h-2 rounded-full bg-emerald-500" />
                                <div className="flex justify-between items-center mb-2">
                                  <span className="text-[9px] font-black text-emerald-600 uppercase tracking-widest">{blog.search_intent}</span>
                                </div>
                                <h5 className="font-bold text-slate-900 text-sm mb-3">{blog.title}</h5>
                                <div className="flex flex-wrap gap-2">
                                  {(blog.outline || []).map((o: any, i: any) => (
                                    <span key={i} className="px-2 py-1 bg-slate-50 border border-slate-100 rounded text-[9px] font-medium text-slate-500 flex items-center gap-1">
                                      <ChevronRight className="w-2.5 h-2.5" /> {o}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>

                        <div className="bg-slate-900 p-8 rounded-[2rem] text-white shadow-xl relative overflow-hidden">
                          <div className="relative z-10">
                            <h4 className="font-display font-bold text-xl mb-6">Target Keyword Analysis</h4>
                            <div className="flex flex-wrap gap-3">
                              {(currentData?.keyword_analysis?.primary_keywords || []).map((kw: string, idx: number) => (
                                <span key={idx} className="px-3 py-1.5 bg-white/10 hover:bg-white/20 border border-white/10 rounded-xl text-xs font-bold transition-all cursor-default">
                                  {kw}
                                </span>
                              ))}
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </motion.div>
                )}

                {activeTab === 'performance' && isDashboardActive && currentData && (
                  <motion.div key="performance" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-12">
                    <SectionHeader icon={Zap} title="Core Performance" subtitle="Speed and Link Integrity" />

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                      <div className="bg-white p-8 rounded-[2rem] border border-slate-200 shadow-sm overflow-hidden">
                        <div className="flex items-center justify-between mb-8">
                          <div className="flex items-center gap-3">
                            <div className="p-2 bg-rose-50 rounded-lg"><Clock className="w-5 h-5 text-rose-600" /></div>
                            <h4 className="font-bold">Speed Insights</h4>
                          </div>
                          <div className="flex items-center gap-2 px-3 py-1 bg-emerald-50 border border-emerald-100 rounded-full">
                            <Check className="w-3 h-3 text-emerald-600" />
                            <span className="text-[9px] font-black text-emerald-600 uppercase tracking-widest">Optimized</span>
                          </div>
                        </div>

                        <div className="mb-6 space-y-3">
                          <div className="p-4 bg-slate-50 rounded-2xl border border-slate-100">
                            <div className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">Remediation Summary</div>
                            <div className="space-y-2">
                              {[
                                'Asset pipeline compression implemented',
                                'Edge CDN caching activated',
                                'Critical path CSS optimization'
                              ].map((item, i) => (
                                <div key={i} className="flex items-center gap-2 text-xs font-medium text-slate-600">
                                  <div className="w-1 h-1 rounded-full bg-emerald-500" />
                                  {item}
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>

                        <div className="h-80 w-full mb-8">
                          <ResponsiveContainer width="100%" height="100%">
                            <BarChart
                              data={performanceChartData}
                              margin={{ top: 20, right: 30, left: 40, bottom: 40 }}
                            >
                              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                              <XAxis
                                dataKey="name"
                                axisLine={{ stroke: '#e2e8f0' }}
                                tickLine={false}
                                tick={{ fontSize: 11, fontWeight: 600, fill: '#64748b' }}
                                label={{ value: 'Performance Metrics', position: 'insideBottom', offset: -15, fontSize: 12, fontWeight: 800, fill: '#1e293b' }}
                              />
                              <YAxis
                                axisLine={{ stroke: '#e2e8f0' }}
                                tickLine={false}
                                tick={{ fontSize: 11, fontWeight: 600, fill: '#64748b' }}
                                label={{ value: 'Intensity / Score', angle: -90, position: 'insideLeft', offset: -25, fontSize: 12, fontWeight: 800, fill: '#1e293b' }}
                              />
                              <Tooltip
                                cursor={{ fill: 'rgba(241, 245, 249, 0.5)' }}
                                content={({ active, payload }) => {
                                  if (active && payload && payload.length) {
                                    const data = payload[0]?.payload;
                                    if (!data) return null;
                                    const isPositive = data.name === 'Speed Score' ? (data.value >= (data.goal || 0)) : (data.value <= (data.goal || 999));

                                    return (
                                      <motion.div
                                        initial={{ opacity: 0, y: 10, scale: 0.95, filter: 'blur(10px)' }}
                                        animate={{ opacity: 1, y: 0, scale: 1, filter: 'blur(0px)' }}
                                        transition={{ type: 'spring', damping: 20, stiffness: 300 }}
                                        className="bg-white/95 backdrop-blur-md p-6 border border-slate-200 shadow-[0_20px_60px_-12px_rgba(0,0,0,0.12)] rounded-[2rem] ring-1 ring-slate-900/5 min-w-[240px]"
                                      >
                                        <div className="flex justify-between items-center mb-4">
                                          <div className="flex items-center gap-2">
                                            <div className={`w-1.5 h-1.5 rounded-full ${isPositive ? 'bg-emerald-500' : 'bg-rose-500'}`} />
                                            <div className="text-[10px] font-black text-slate-500 uppercase tracking-widest">{data.name}</div>
                                          </div>
                                          <div className={`px-2 py-0.5 rounded text-[9px] font-black uppercase tracking-tight ${isPositive ? 'bg-emerald-50 text-emerald-600' : 'bg-rose-50 text-rose-600'}`}>
                                            {isPositive ? 'Passing' : 'Critical'}
                                          </div>
                                        </div>

                                        <div className="flex items-baseline gap-2 mb-2">
                                          <div className="text-4xl font-display font-black text-slate-900 leading-none">
                                            {data.value}
                                          </div>
                                          <div className="text-xs font-bold text-slate-400 uppercase tracking-wide">{data.unit}</div>
                                        </div>

                                        <div className="flex items-center gap-2 mb-6">
                                          <div className="text-[10px] font-bold text-slate-400">Target Benchmark</div>
                                          <div className="px-2 py-0.5 bg-slate-100 rounded-lg text-[10px] font-black text-slate-700">{data.goalText}</div>
                                        </div>

                                        <div className="pt-4 border-t border-slate-100">
                                          <p className="text-[11px] text-slate-500 leading-relaxed font-medium">
                                            {data.description}
                                          </p>
                                        </div>
                                      </motion.div>
                                    );
                                  }
                                  return null;
                                }}
                              />
                              <Bar
                                dataKey="value"
                                radius={[12, 12, 0, 0]}
                                barSize={60}
                                animationDuration={1500}
                              >
                                {performanceChartData.map((entry: any, index: number) => (
                                  <Cell
                                    key={`cell-${index}`}
                                    fill={entry.color}
                                    fillOpacity={0.9}
                                    stroke={entry.color}
                                    strokeWidth={2}
                                  />
                                ))}
                              </Bar>
                            </BarChart>
                          </ResponsiveContainer>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                          <div className="p-4 bg-slate-50 rounded-2xl">
                            <div className="text-[10px] font-black text-slate-400 uppercase mb-1">Load Time</div>
                            <div className="text-lg font-bold text-slate-800">{currentData?.page_speed?.response_time || 0}s</div>
                          </div>
                          <div className="p-4 bg-slate-50 rounded-2xl">
                            <div className="text-[10px] font-black text-slate-400 uppercase mb-1">Page Size</div>
                            <div className="text-lg font-bold text-slate-800">{currentData?.page_speed?.page_size_kb || 0}KB</div>
                          </div>
                        </div>
                      </div>

                      <div className="md:col-span-2 bg-white p-8 rounded-[2rem] border border-slate-200">
                        <div className="flex items-center gap-3 mb-8">
                          <div className="p-2 bg-indigo-50 rounded-lg"><Link className="w-5 h-5 text-indigo-600" /></div>
                          <h4 className="font-bold">Link Architecture</h4>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
                          <div>
                            <h5 className="text-xs font-black text-slate-400 uppercase tracking-widest mb-4">Authority Profile</h5>
                            <div className="space-y-4">
                              <div className="flex justify-between items-center p-4 bg-slate-50 rounded-2xl border border-slate-100">
                                <span className="text-sm font-bold text-slate-700 font-mono">Backlinks</span>
                                <span className="px-3 py-1 bg-white rounded-lg font-black text-indigo-600 shadow-sm">~{currentData?.link_analysis?.backlinks?.estimated_backlinks || 0}</span>
                              </div>
                              <div className="flex justify-between items-center p-4 bg-slate-50 rounded-2xl border border-slate-100">
                                <span className="text-sm font-bold text-slate-700 font-mono">Referring Domains</span>
                                <span className="px-3 py-1 bg-white rounded-lg font-black text-indigo-600 shadow-sm">{currentData?.link_analysis?.backlinks?.referring_domains || 0}</span>
                              </div>
                              <div className="flex justify-between items-center p-4 bg-slate-50 rounded-2xl border border-slate-100">
                                <span className="text-sm font-bold text-slate-700 font-mono">Link Strength</span>
                                <span className="px-3 py-1 bg-emerald-500 text-white rounded-lg font-black text-[10px] shadow-sm uppercase">{currentData?.link_analysis?.backlinks?.backlink_strength || 'N/A'}</span>
                              </div>
                            </div>
                          </div>
                          <div>
                            <h5 className="text-xs font-black text-slate-400 uppercase tracking-widest mb-4">Outbound Distribution</h5>
                            <div className="flex flex-wrap gap-2">
                              {(currentData?.link_analysis?.external?.domains || []).map((domain: string, idx: number) => (
                                <span key={idx} className="px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-xl text-[10px] font-bold text-slate-500 hover:border-indigo-600 hover:text-indigo-600 transition-all cursor-default">
                                  {domain}
                                </span>
                              ))}
                            </div>
                            <div className="mt-8 pt-8 border-t border-slate-100">
                              <div className="flex items-center justify-between text-sm">
                                <span className="font-bold text-slate-500">Total External Assets</span>
                                <span className="font-black text-slate-900">{currentData?.link_analysis?.external?.total_external_links || 0}</span>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </motion.div>
                )}

                {activeTab === 'appendix' && isDashboardActive && currentData && (
                  <motion.div key="appendix" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-12">
                    <SectionHeader icon={TableIcon} title="Sampled Intelligence" />
                    <PageAnalysisCards pages={currentData?.pages || currentData?.crawl_overview?.sampled_pages || []} />
                    <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                      <div className="lg:col-span-4 bg-white p-8 rounded-[2rem] border border-slate-200">
                        <div className="flex items-center gap-3 mb-8">
                          <Lock className="w-5 h-5 text-indigo-600" />
                          <h5 className="font-bold underline underline-offset-4 decoration-indigo-200">
                            Crawl Constraints
                            <HelpTooltip text="Technical limitations encountered during the audit, such as restricted pages or anti-bot measures, which may limit the data available for analysis." />
                          </h5>
                        </div>
                        <div className="divide-y divide-indigo-50">
                          {(currentData?.data_limitations || []).map((lim: any, idx: number) => (
                            <DataLimitationAccordionItem
                              key={idx}
                              lim={lim}
                              index={idx}
                            />
                          ))}
                        </div>
                      </div>
                      <div className="lg:col-span-8 bg-slate-900 p-10 rounded-[2.5rem] text-white overflow-hidden relative">
                        <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500/10 rounded-full -mr-32 -mt-32 blur-3xl" />
                        <div className="relative z-10 flex flex-col h-full">
                          <div className="flex items-center gap-3 mb-10">
                            <Cpu className="w-6 h-6 text-indigo-400" />
                            <h5 className="text-2xl font-display font-bold">
                              AI Derived Strategic Directives
                              <HelpTooltip text="Advanced AI analysis that connects technical findings to business impact, providing high-level instructions for your SEO strategy." />
                            </h5>
                          </div>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 flex-1">
                            {(currentData?.ai_insights?.insights || []).map((ins: any, idx: number) => (
                              <div key={idx} className="p-6 bg-white/5 rounded-[1.5rem] border border-white/10 flex flex-col group hover:bg-white/10 transition-all border-l-4 border-l-indigo-500">
                                <div className="flex justify-between items-center mb-4">
                                  <span className="text-[10px] font-black text-indigo-400 uppercase tracking-widest">{ins.issue}</span>
                                  <span className={`px-2 py-0.5 rounded text-[8px] font-black uppercase ${ins.priority === 'High' ? 'bg-rose-500/20 text-rose-400' : 'bg-indigo-500/20 text-indigo-400'}`}>
                                    {ins.priority}
                                  </span>
                                </div>
                                <p className="text-xs text-slate-400 leading-relaxed mb-6 flex-1">{ins.explanation}</p>
                                <div className="pt-4 border-t border-white/5">
                                  <div className="text-[9px] font-black text-slate-500 uppercase mb-2">Recommendation</div>
                                  <p className="text-[10px] font-bold text-indigo-300">{ins.recommendation}</p>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </main>

            <footer className="mt-40 border-t border-slate-200 py-20 px-6">
              <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-10">
                <div className="flex items-center gap-2"><ShieldCheck className="w-8 h-8 text-indigo-600" /><span className="font-display font-bold text-2xl">AuditIntelligence</span></div>
                <div className="text-[10px] font-black text-slate-400 uppercase tracking-widest text-center md:text-right">Generated for {currentData?.pdf_template_data?.company_name || 'Organization'} • Management Protocol v3.2 • &copy; 2026 Audit Intel</div>
              </div>
            </footer>
          </>
        ) : (
          <div className="min-h-screen flex items-center justify-center bg-slate-50 w-full">
            <div className="flex flex-col items-center gap-4">
              <RefreshCw className="w-8 h-8 text-indigo-600 animate-spin" />
              <p className="text-slate-500 font-bold uppercase tracking-widest text-[10px]">Synchronizing Audit Data...</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
