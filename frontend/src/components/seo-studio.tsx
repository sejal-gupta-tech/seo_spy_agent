"use client";

import { type ReactNode, useMemo, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import {
  ArrowUpRight,
  Bot,
  Compass,
  Download,
  FileStack,
  Gauge,
  LoaderCircle,
  Radar,
  ScanSearch,
  Sparkles,
  Telescope,
  TriangleAlert,
  WandSparkles,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";
import type {
  AnalysisResponse,
  AnalysisStageId,
  AnalysisStreamEvent,
  CrawlPageEvent,
  FixResponse,
  MarketOpportunity,
  MetricSnapshot,
  PageSummary,
  PdfMetric,
  PdfPriorityAction,
  RoadmapItem,
  TechnicalFinding,
} from "@/lib/types";

const defaultUrl = "https://books.toscrape.com/";

const stageDefinitions = [
  {
    id: "crawl",
    label: "Mapping crawl frontier",
    detail: "Collecting HTML pages, depth, and internal link signals.",
    icon: Radar,
  },
  {
    id: "audit",
    label: "Scoring technical health",
    detail: "Checking titles, canonicals, headings, page speed, and link quality.",
    icon: Compass,
  },
  {
    id: "ai",
    label: "Running AI strategy passes",
    detail: "Generating keyword themes, rewrite angles, and board-facing notes.",
    icon: Bot,
  },
  {
    id: "competition",
    label: "Comparing market coverage",
    detail: "Searching competitor pages and mapping content gaps.",
    icon: Telescope,
  },
  {
    id: "report",
    label: "Rendering final report",
    detail: "Packaging the executive narrative and PDF relay.",
    icon: Sparkles,
  },
] as const;

type StageRailStatus = "pending" | "active" | "completed";

type FeedTone = "teal" | "amber" | "rose" | "ink";

interface FeedItem {
  id: string;
  label: string;
  detail: string;
  tone: FeedTone;
  elapsedSeconds?: number;
}

interface CrawlIssueSummary {
  total: number;
  blocked: number;
  missing: number;
  timeout: number;
  skipped: number;
  other: number;
}

interface AgentDefinition {
  id: AnalysisStageId;
  codename: string;
  mission: string;
  output: string;
  icon: typeof Radar;
}

interface LiveTelemetryState {
  currentStageId: AnalysisStageId;
  stageStatus: Record<AnalysisStageId, StageRailStatus>;
  stageDetail: string;
  analyzedPages: number;
  discoveredPages: number;
  crawlDepth: number;
  crawlBudget: number;
  queueRemaining: number;
  sampleCoverageRatio: string;
  signalValue: string;
  signalHint: string;
  currentUrl: string;
  resources: Record<string, string>;
  competitors: string[];
  crawlIssues: CrawlIssueSummary;
  crawlIssueSamples: FeedItem[];
  aiUpdatesSeen: number;
  competitorUpdatesSeen: number;
  reportUpdatesSeen: number;
  recentPages: CrawlPageEvent[];
  recentFindings: TechnicalFinding[];
  opportunities: MarketOpportunity[];
  activityFeed: FeedItem[];
}

const agentDefinitions: AgentDefinition[] = [
  {
    id: "crawl",
    codename: "Scout Agent",
    mission: "Maps internal architecture, page depth, and crawlable routes.",
    output: "A live map of URLs, depth, and site structure.",
    icon: Radar,
  },
  {
    id: "audit",
    codename: "Audit Agent",
    mission: "Scores metadata, canonicals, headings, links, and speed signals.",
    output: "A technical health score with priority gaps.",
    icon: Compass,
  },
  {
    id: "ai",
    codename: "Strategy Agent",
    mission: "Generates keyword themes, content angles, and executive framing.",
    output: "Actionable AI recommendations and content opportunities.",
    icon: Bot,
  },
  {
    id: "competition",
    codename: "Market Agent",
    mission: "Benchmarks rival domains and spots whitespace in the market.",
    output: "Competitor benchmarks and growth gaps.",
    icon: Telescope,
  },
  {
    id: "report",
    codename: "Narrator Agent",
    mission: "Packages the evidence into a board-facing brief and export.",
    output: "A polished report with PDF download.",
    icon: Sparkles,
  },
] as const;

const stageWeights: Record<AnalysisStageId, number> = {
  crawl: 40,
  audit: 18,
  ai: 18,
  competition: 14,
  report: 10,
};

function createInitialStageStatus(): Record<AnalysisStageId, StageRailStatus> {
  return {
    crawl: "pending",
    audit: "pending",
    ai: "pending",
    competition: "pending",
    report: "pending",
  };
}

function createInitialLiveTelemetry(): LiveTelemetryState {
  return {
    currentStageId: "crawl",
    stageStatus: createInitialStageStatus(),
    stageDetail: stageDefinitions[0].detail,
    analyzedPages: 0,
    discoveredPages: 0,
    crawlDepth: 0,
    crawlBudget: 0,
    queueRemaining: 0,
    sampleCoverageRatio: "0%",
    signalValue: "Waiting",
    signalHint: "Run a crawl to fill the board.",
    currentUrl: "",
    resources: {},
    competitors: [],
    crawlIssues: {
      total: 0,
      blocked: 0,
      missing: 0,
      timeout: 0,
      skipped: 0,
      other: 0,
    },
    crawlIssueSamples: [],
    aiUpdatesSeen: 0,
    competitorUpdatesSeen: 0,
    reportUpdatesSeen: 0,
    recentPages: [],
    recentFindings: [],
    opportunities: [],
    activityFeed: [],
  };
}

function formatElapsed(elapsedSeconds?: number): string {
  if (elapsedSeconds === undefined) {
    return "";
  }

  return `${elapsedSeconds.toFixed(1)}s`;
}

function truncateUrl(value: string, maxLength = 48): string {
  if (value.length <= maxLength) {
    return value;
  }

  return `${value.slice(0, maxLength - 1)}…`;
}

function compactPathLabel(value: string): string {
  try {
    const parsed = new URL(value);
    return parsed.pathname === "/" ? parsed.hostname : `${parsed.hostname}${parsed.pathname}`;
  } catch {
    return value;
  }
}

function feedToneClasses(tone: FeedTone): string {
  return {
    teal: "border-[#1f8c95]/18 bg-[#edf9f8] text-[#14545b]",
    amber: "border-[#d7a14a]/18 bg-[#fff8e5] text-[#8a6617]",
    rose: "border-[#d86a4d]/18 bg-[#fff1eb] text-[#a5481f]",
    ink: "border-white/10 bg-white/6 text-white/78",
  }[tone];
}

function appendLimited<T>(items: T[], value: T, limit: number): T[] {
  return [value, ...items].slice(0, limit);
}

function appendUniqueBy<T>(
  items: T[],
  value: T,
  keyFn: (item: T) => string,
  limit: number,
): T[] {
  const nextKey = keyFn(value);
  const filtered = items.filter((item) => keyFn(item) !== nextKey);
  return [value, ...filtered].slice(0, limit);
}

function buildFeedItem(
  label: string,
  detail: string,
  tone: FeedTone,
  elapsedSeconds?: number,
): FeedItem {
  return {
    id: `${label}-${detail}-${elapsedSeconds ?? "now"}`,
    label,
    detail,
    tone,
    elapsedSeconds,
  };
}

function classifyCrawlIssue(
  event: Extract<AnalysisStreamEvent, { type: "crawl_error" | "crawl_skip" }>,
): keyof Omit<CrawlIssueSummary, "total"> {
  if (event.type === "crawl_skip") {
    return "skipped";
  }

  if (event.category === "blocked" || event.category === "rate_limited") {
    return "blocked";
  }
  if (event.category === "missing" || event.status_code === 404) {
    return "missing";
  }
  if (event.category === "timeout" || event.detail.toLowerCase().includes("timed out")) {
    return "timeout";
  }

  return "other";
}

function getAgentDefinition(stageId: AnalysisStageId): AgentDefinition {
  return (
    agentDefinitions.find((agent) => agent.id === stageId) ?? agentDefinitions[0]
  );
}

function countCompletedStages(
  stageStatus: Record<AnalysisStageId, StageRailStatus>,
): number {
  return Object.values(stageStatus).filter((status) => status === "completed").length;
}

function getNextPendingAgent(
  stageStatus: Record<AnalysisStageId, StageRailStatus>,
): AgentDefinition | null {
  const nextStage = stageDefinitions.find((item) => stageStatus[item.id] === "pending");
  return nextStage ? getAgentDefinition(nextStage.id) : null;
}

function deriveMissionProgress(telemetry: LiveTelemetryState): number {
  let progress = 0;

  for (const stage of stageDefinitions) {
    const status = telemetry.stageStatus[stage.id];
    const weight = stageWeights[stage.id];

    if (status === "completed") {
      progress += weight;
      continue;
    }

    if (status !== "active") {
      continue;
    }

    let partial = 0.2;

    switch (stage.id) {
      case "crawl":
        partial = Math.min(
          telemetry.analyzedPages / Math.max(telemetry.crawlBudget || 12, 1),
          1,
        );
        break;
      case "audit":
        partial =
          telemetry.recentFindings.length > 0 || telemetry.signalValue !== "Calibrating"
            ? 0.82
            : 0.35;
        break;
      case "ai":
        partial = Math.min(telemetry.aiUpdatesSeen / 3, 1);
        break;
      case "competition":
        partial = Math.min(
          (telemetry.competitorUpdatesSeen * 0.45) +
            (telemetry.opportunities.length > 0 ? 0.45 : 0),
          1,
        );
        break;
      case "report":
        partial = Math.min(telemetry.reportUpdatesSeen / 2, 1);
        break;
    }

    progress += weight * partial;
  }

  return Math.max(4, Math.min(Math.round(progress), 100));
}

function buildMissionSummary(telemetry: LiveTelemetryState): string {
  const activeAgent = getAgentDefinition(telemetry.currentStageId);
  const blockerCount = telemetry.crawlIssues.total;

  if (telemetry.stageStatus.report === "completed") {
    return "The agent team has finished the crawl, diagnosis, benchmarking, and report packaging.";
  }

  if (telemetry.currentStageId === "crawl") {
    const blockerSuffix =
      blockerCount > 0
        ? ` ${blockerCount} crawl blockers have been contained without stopping the run.`
        : "";
    return `${activeAgent.codename} is mapping the site, separating real HTML pages from dead ends, gated URLs, and off-template content.${blockerSuffix}`;
  }

  if (telemetry.currentStageId === "audit") {
    return "Audit Agent is turning raw crawl evidence into health scores, benchmark gaps, and priority fixes.";
  }

  if (telemetry.currentStageId === "ai") {
    return "Strategy Agent is translating crawl evidence into keyword opportunities, rewrite angles, and board-ready language.";
  }

  if (telemetry.currentStageId === "competition") {
    return "Market Agent is comparing the site with live competitors to expose whitespace and demand gaps.";
  }

  return "Narrator Agent is packaging the evidence into a sponsor-ready brief and export bundle.";
}

function summarizeIssues(issueSummary: CrawlIssueSummary): string {
  if (issueSummary.total === 0) {
    return "No crawl blockers detected yet.";
  }

  const parts = [
    issueSummary.blocked ? `${issueSummary.blocked} blocked` : null,
    issueSummary.missing ? `${issueSummary.missing} missing` : null,
    issueSummary.timeout ? `${issueSummary.timeout} timed out` : null,
    issueSummary.skipped ? `${issueSummary.skipped} non-HTML` : null,
    issueSummary.other ? `${issueSummary.other} other` : null,
  ].filter(Boolean);

  return `${issueSummary.total} crawl blockers observed: ${parts.join(", ")}.`;
}

function parseReportTaskId(reportUrl: string | null | undefined): string | null {
  if (!reportUrl) {
    return null;
  }

  const match = reportUrl.match(/\/download-report\/(.+)$/);
  return match?.[1] ?? null;
}

async function readErrorMessage(response: Response): Promise<string> {
  try {
    const payload = (await response.json()) as { detail?: string };
    if (payload.detail) {
      return payload.detail;
    }
  } catch {
    // Fall through to text-based fallback.
  }

  try {
    const text = await response.text();
    if (text) {
      return text;
    }
  } catch {
    // Ignore text parsing failures.
  }

  return "The request failed before the frontend could decode a structured error.";
}

async function consumeNdjsonStream(
  response: Response,
  onEvent: (event: AnalysisStreamEvent) => void,
): Promise<void> {
  const body = response.body;
  if (!body) {
    throw new Error("The streamed analysis response did not include a readable body.");
  }

  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    buffer += decoder.decode(value ?? new Uint8Array(), { stream: !done });

    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";

    for (const rawLine of lines) {
      const line = rawLine.trim();
      if (!line) {
        continue;
      }

      onEvent(JSON.parse(line) as AnalysisStreamEvent);
    }

    if (done) {
      break;
    }
  }

  const trailingLine = buffer.trim();
  if (trailingLine) {
    onEvent(JSON.parse(trailingLine) as AnalysisStreamEvent);
  }
}

function priorityStyles(priority: string): string {
  switch (priority) {
    case "High":
      return "border-[#d4683c]/20 bg-[#fff0e8] text-[#a5481f]";
    case "Medium":
      return "border-[#db9c3c]/20 bg-[#fff6dd] text-[#8a6617]";
    default:
      return "border-[#2d7b82]/20 bg-[#eefbfb] text-[#14545b]";
  }
}

function statusStyles(status: string): string {
  const normalized = status.toLowerCase();

  if (
    normalized.includes("critical") ||
    normalized.includes("high") ||
    normalized.includes("risk") ||
    normalized.includes("missing")
  ) {
    return "text-[#a5481f]";
  }

  if (normalized.includes("benchmark") || normalized.includes("strong")) {
    return "text-[#14545b]";
  }

  return "text-[#6c5e4e]";
}

function compactNumber(value: number): string {
  return new Intl.NumberFormat("en-US", { notation: "compact" }).format(value);
}

function toneForRoadmap(priority: RoadmapItem["priority"]): string {
  return {
    High: "from-[#ffd3bf] to-white",
    Medium: "from-[#ffe7b3] to-white",
    Low: "from-[#d9f3f2] to-white",
  }[priority];
}

function buildFixSeed(finding: TechnicalFinding): string {
  return `${finding.metric}: ${finding.recommendation}`;
}

function MetricTile({
  label,
  value,
  hint,
}: {
  label: string;
  value: string;
  hint?: string;
}) {
  return (
    <div className="rounded-[1.6rem] border border-white/55 bg-white/72 p-4 shadow-[0_18px_45px_-35px_rgba(17,48,60,0.55)] backdrop-blur-xl">
      <p className="text-xs font-semibold uppercase tracking-[0.24em] text-[#6a726f]">
        {label}
      </p>
      <p className="mt-3 text-2xl font-semibold text-[#11232d]">{value}</p>
      {hint ? <p className="mt-2 text-sm text-[#66757d]">{hint}</p> : null}
    </div>
  );
}

function SectionHeading({
  eyebrow,
  title,
  blurb,
  action,
}: {
  eyebrow: string;
  title: string;
  blurb: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
      <div className="space-y-1.5">
        <p className="text-xs font-semibold uppercase tracking-[0.28em] text-[#6b7d80]">
          {eyebrow}
        </p>
        <h2 className="font-heading text-3xl leading-none text-[#11232d] md:text-[2.6rem]">
          {title}
        </h2>
        <p className="max-w-2xl text-sm leading-6 text-[#67787d]">{blurb}</p>
      </div>
      {action}
    </div>
  );
}

function LoadingDeck({ telemetry }: { telemetry: LiveTelemetryState }) {
  const activeAgent = getAgentDefinition(telemetry.currentStageId);
  const missionProgress = deriveMissionProgress(telemetry);
  const completedAgents = countCompletedStages(telemetry.stageStatus);
  const nextAgent = getNextPendingAgent(telemetry.stageStatus);
  const issueSummary = summarizeIssues(telemetry.crawlIssues);

  return (
    <motion.section
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -12 }}
      className="mt-10 grid gap-5 xl:grid-cols-[1.1fr_0.9fr]"
    >
      <Card className="rounded-[2rem] border border-white/55 bg-white/72 backdrop-blur-xl">
        <CardHeader>
          <Badge className="w-fit border-[#d7e3df] bg-white/70 text-[#0e5d6f]">
            Live mission control
          </Badge>
          <CardTitle className="text-3xl text-[#11232d]">
            {activeAgent.codename} is live
          </CardTitle>
          <CardDescription className="text-base leading-7 text-[#67787d]">
            {buildMissionSummary(telemetry)}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="rounded-[1.6rem] border border-[#dce6e2] bg-[#fbf7ef]/85 p-4 shadow-[0_18px_40px_-40px_rgba(17,48,60,0.7)]">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.24em] text-[#6b7a7c]">
                  Mission progress
                </p>
                <p className="mt-2 text-2xl font-semibold text-[#11232d]">
                  {missionProgress}% complete
                </p>
              </div>
              <Badge className="border-[#dce6e2] bg-white/85 text-[#0e5d6f]">
                {completedAgents} of 5 agents finished
              </Badge>
            </div>
            <div className="mt-4 h-2.5 overflow-hidden rounded-full bg-[#d7e6e1]">
              <motion.div
                animate={{ width: `${missionProgress}%` }}
                className="h-full rounded-full bg-[linear-gradient(90deg,#0f6775,#e1a66a)]"
                transition={{ type: "spring", stiffness: 110, damping: 18 }}
              />
            </div>
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              <div className="rounded-[1.2rem] border border-[#dce6e2] bg-white/80 p-3">
                <p className="text-[11px] uppercase tracking-[0.22em] text-[#6d7d81]">
                  Active mission
                </p>
                <p className="mt-2 text-sm font-semibold text-[#13333f]">
                  {activeAgent.mission}
                </p>
              </div>
              <div className="rounded-[1.2rem] border border-[#dce6e2] bg-white/80 p-3">
                <p className="text-[11px] uppercase tracking-[0.22em] text-[#6d7d81]">
                  Next handoff
                </p>
                <p className="mt-2 text-sm font-semibold text-[#13333f]">
                  {nextAgent
                    ? `${nextAgent.codename} prepares ${nextAgent.output.toLowerCase()}.`
                    : "The executive brief is being finalized for export."}
                </p>
              </div>
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <MetricTile
              label="Pages Mapped"
              value={`${telemetry.analyzedPages}`}
              hint={`${telemetry.discoveredPages} discovered`}
            />
            <MetricTile
              label="Depth"
              value={`${telemetry.crawlDepth}`}
              hint={`Queue ${telemetry.queueRemaining}`}
            />
            <MetricTile
              label="Coverage"
              value={telemetry.sampleCoverageRatio}
              hint="Live crawl sample ratio"
            />
            <MetricTile
              label="Signal"
              value={telemetry.signalValue}
              hint={telemetry.signalHint}
            />
          </div>

          <div className="rounded-[1.55rem] border border-[#dce6e2] bg-[#fbf7ef]/80 p-4">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.24em] text-[#6b7a7c]">
                  Current target
                </p>
                <p className="mt-2 font-mono text-sm text-[#163843]">
                  {telemetry.currentUrl
                    ? truncateUrl(telemetry.currentUrl, 72)
                    : "Waiting for the first crawl response..."}
                </p>
                <p className="mt-2 text-sm leading-6 text-[#6c7b80]">
                  {telemetry.stageDetail}
                </p>
              </div>
              <div className="rounded-full border border-[#dce6e2] bg-white/85 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-[#0e5d6f]">
                {formatElapsed(telemetry.activityFeed[0]?.elapsedSeconds) || "live"}
              </div>
            </div>
          </div>

          <div className="grid gap-4 xl:grid-cols-[1.08fr_0.92fr]">
            <div className="rounded-[1.6rem] border border-[#dfe7e1] bg-[#f8f4ea]/80 p-4">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.24em] text-[#6b7a7c]">
                    Crawl tape
                  </p>
                  <p className="mt-1 text-sm text-[#6d7b80]">
                    Live pages fetched, their depth, and the next URLs discovered.
                  </p>
                </div>
                <Badge className="border-[#dce6e2] bg-white/80 text-[#0e5d6f]">
                  {telemetry.recentPages.length} recent pages
                </Badge>
              </div>

              <div className="mt-4 space-y-3">
                {telemetry.recentPages.length > 0 ? (
                  telemetry.recentPages.map((page) => (
                    <div
                      key={`${page.url}-${page.elapsed_seconds ?? 0}`}
                      className="rounded-[1.35rem] border border-[#dde6e2] bg-white/82 p-4 shadow-[0_18px_45px_-40px_rgba(17,48,60,0.55)]"
                    >
                      <div className="flex flex-wrap items-center gap-2">
                        <Badge className="border-[#dce6e2] bg-[#eef8f7] text-[#14545b]">
                          Depth {page.depth}
                        </Badge>
                        <Badge className="border-[#ecd8bf] bg-[#fff6e9] text-[#8a6617]">
                          {page.page_type}
                        </Badge>
                        <span className="text-xs uppercase tracking-[0.22em] text-[#718086]">
                          {formatElapsed(page.elapsed_seconds)}
                        </span>
                      </div>
                      <p className="mt-3 font-mono text-sm text-[#163843]">
                        {compactPathLabel(page.url)}
                      </p>
                      <p className="mt-2 text-sm leading-6 text-[#617279]">
                        {page.title || "Untitled page"} · {page.internal_links_count} internal
                        · {page.external_links_count} external
                      </p>
                      {page.new_links_sample.length > 0 ? (
                        <div className="mt-3 flex flex-wrap gap-2">
                          {page.new_links_sample.map((link) => (
                            <span
                              key={link}
                              className="rounded-full border border-[#dce6e2] bg-[#f5f8f6] px-3 py-1 text-xs text-[#4f656d]"
                            >
                              {compactPathLabel(link)}
                            </span>
                          ))}
                        </div>
                      ) : null}
                    </div>
                  ))
                ) : (
                  <div className="grid gap-3 sm:grid-cols-2">
                    {[1, 2, 3, 4].map((slot) => (
                      <div
                        key={slot}
                        className="rounded-[1.35rem] border border-[#dde6e2] bg-white/78 p-4"
                      >
                        <Skeleton className="mb-3 h-5 w-20 rounded-full bg-[#d8e4df]" />
                        <Skeleton className="mb-2 h-4 w-40 rounded-full bg-[#efe0c9]" />
                        <Skeleton className="h-3 w-28 rounded-full bg-[#d8e4df]" />
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <div className="rounded-[1.6rem] border border-[#dfe7e1] bg-[#f8f4ea]/80 p-4">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.24em] text-[#6b7a7c]">
                    Emerging findings
                  </p>
                  <p className="mt-1 text-sm text-[#6d7b80]">
                    Issues and opportunities surfaced as soon as the audit has signal.
                  </p>
                </div>
                <Badge className="border-[#dce6e2] bg-white/80 text-[#0e5d6f]">
                  {telemetry.recentFindings.length} findings
                </Badge>
              </div>

              <div className="mt-4 space-y-3">
                {telemetry.recentFindings.length > 0 ? (
                  telemetry.recentFindings.map((finding) => (
                    <div
                      key={`${finding.metric}-${finding.priority}`}
                      className="rounded-[1.35rem] border border-[#dde6e2] bg-white/82 p-4"
                    >
                      <div className="flex items-center justify-between gap-3">
                        <p className="text-sm font-semibold text-[#173843]">
                          {finding.metric}
                        </p>
                        <Badge className={priorityStyles(finding.priority)}>
                          {finding.priority}
                        </Badge>
                      </div>
                      <p className="mt-2 text-sm leading-6 text-[#64747b]">
                        {finding.recommendation}
                      </p>
                    </div>
                  ))
                ) : (
                  <div className="grid gap-3">
                    {[1, 2, 3].map((slot) => (
                      <div
                        key={slot}
                        className="rounded-[1.35rem] border border-[#dde6e2] bg-white/78 p-4"
                      >
                        <Skeleton className="mb-3 h-4 w-32 rounded-full bg-[#d8e4df]" />
                        <Skeleton className="mb-2 h-3 w-full rounded-full bg-[#efe0c9]" />
                        <Skeleton className="h-3 w-3/4 rounded-full bg-[#d8e4df]" />
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <div className="rounded-[1.6rem] border border-[#dfe7e1] bg-[#f8f4ea]/80 p-4">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.24em] text-[#6b7a7c]">
                    Crawl blockers
                  </p>
                  <p className="mt-1 text-sm text-[#6d7b80]">
                    The agent keeps moving, but these routes slowed or blocked the crawl.
                  </p>
                </div>
                <Badge className="border-[#dce6e2] bg-white/80 text-[#8a4b27]">
                  {telemetry.crawlIssues.total} blockers
                </Badge>
              </div>
              <div className="mt-4 rounded-[1.2rem] border border-[#f0d2c4] bg-[#fff5ef] p-4">
                <p className="text-sm leading-6 text-[#8a4b27]">{issueSummary}</p>
              </div>
              {telemetry.crawlIssueSamples.length > 0 ? (
                <div className="mt-4 space-y-3">
                  {telemetry.crawlIssueSamples.map((item) => (
                    <div
                      key={item.id}
                      className={cn(
                        "rounded-[1.2rem] border px-4 py-3",
                        feedToneClasses(item.tone),
                      )}
                    >
                      <div className="flex items-center justify-between gap-3">
                        <p className="text-sm font-semibold">{item.label}</p>
                        <span className="text-xs uppercase tracking-[0.22em] opacity-70">
                          {formatElapsed(item.elapsedSeconds)}
                        </span>
                      </div>
                      <p className="mt-2 text-sm leading-6 opacity-85">{item.detail}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="mt-4 rounded-[1.2rem] border border-[#dce6e2] bg-white/78 p-4 text-sm text-[#6d7d81]">
                  No blockers yet. The crawler is moving through the site cleanly.
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
      <Card className="rounded-[2rem] border border-[#173340]/10 bg-[#102f3c] text-white shadow-[0_30px_120px_-60px_rgba(9,28,36,0.95)]">
        <CardHeader>
          <Badge className="w-fit border-white/15 bg-white/10 text-white">
            AI agent team
          </Badge>
          <CardTitle className="text-2xl text-[#f7f1e6]">
            The AI agent handoff chain
          </CardTitle>
          <CardDescription className="text-base leading-7 text-white/68">
            Each agent owns one part of the SEO workflow, then passes structured evidence to the next one.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="space-y-3">
            {agentDefinitions.map((agent, index) => {
              const Icon = agent.icon;
              const status = telemetry.stageStatus[agent.id];
              const isActive = telemetry.currentStageId === agent.id;

              return (
                <div
                  key={agent.id}
                  className={cn(
                    "rounded-[1.35rem] border px-4 py-4 backdrop-blur-xl transition-colors",
                    status === "completed"
                      ? "border-[#2d7b82]/28 bg-white/12 text-white"
                      : status === "active"
                        ? "border-[#f3bf88]/40 bg-white/14 text-white"
                        : "border-white/10 bg-white/5 text-white/68",
                  )}
                >
                  <div className="flex items-start gap-3">
                    <div className="mt-0.5 rounded-full border border-white/15 bg-white/10 p-1.5">
                      <Icon className="size-3.5" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <div>
                          <p className="text-[11px] uppercase tracking-[0.26em] text-white/40">
                            Agent {index + 1}
                          </p>
                          <p className="mt-1 text-sm font-semibold text-white">
                            {agent.codename}
                          </p>
                        </div>
                        <Badge
                          className={cn(
                            "border-white/12 bg-white/10",
                            status === "completed"
                              ? "text-[#aee7dd]"
                              : status === "active"
                                ? "text-[#f9d6af]"
                                : "text-white/60",
                          )}
                        >
                          {status === "completed"
                            ? "Completed"
                            : status === "active"
                              ? "Working"
                              : "Queued"}
                        </Badge>
                      </div>
                      <p className="mt-3 text-sm leading-6 text-white/78">
                        {agent.mission}
                      </p>
                      <p className="mt-2 text-sm leading-6 text-white/58">
                        {isActive ? telemetry.stageDetail : agent.output}
                      </p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="grid gap-4 lg:grid-cols-[0.95fr_1.05fr]">
            <div className="rounded-[1.55rem] border border-white/10 bg-white/6 p-4">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.24em] text-white/38">
                    Key moments
                  </p>
                  <p className="mt-1 text-sm text-white/68">
                    A concise trail of the most valuable updates, not every debug event.
                  </p>
                </div>
                <Badge className="border-white/12 bg-white/10 text-white/80">
                  {telemetry.activityFeed.length} notes
                </Badge>
              </div>

              <div className="mt-4 space-y-3">
                {telemetry.activityFeed.length > 0 ? (
                  telemetry.activityFeed.map((item) => (
                    <div
                      key={item.id}
                      className={cn(
                        "rounded-[1.2rem] border px-4 py-3",
                        feedToneClasses(item.tone),
                      )}
                    >
                      <div className="flex items-center justify-between gap-3">
                        <p className="text-sm font-semibold">{item.label}</p>
                        <span className="text-xs uppercase tracking-[0.22em] opacity-70">
                          {formatElapsed(item.elapsedSeconds)}
                        </span>
                      </div>
                      <p className="mt-2 text-sm leading-6 opacity-85">{item.detail}</p>
                    </div>
                  ))
                ) : (
                  <div className="grid gap-3">
                    {[1, 2, 3].map((slot) => (
                      <div
                        key={slot}
                        className="rounded-[1.2rem] border border-white/10 bg-white/5 p-4"
                      >
                        <Skeleton className="mb-3 h-3 w-24 rounded-full bg-white/10" />
                        <Skeleton className="mb-2 h-3 w-full rounded-full bg-white/10" />
                        <Skeleton className="h-3 w-2/3 rounded-full bg-white/10" />
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <div className="space-y-4">
              <div className="grid gap-3 sm:grid-cols-2">
                {Object.entries(telemetry.resources).map(([resource, status]) => (
                  <div
                    key={resource}
                    className="rounded-[1.2rem] border border-white/10 bg-white/6 px-4 py-3"
                  >
                    <p className="text-[11px] uppercase tracking-[0.24em] text-white/38">
                      {resource.replaceAll("_", " ")}
                    </p>
                    <p className="mt-2 text-sm text-white/76">{status}</p>
                  </div>
                ))}
              </div>

              {telemetry.competitors.length > 0 ? (
                <div className="rounded-[1.35rem] border border-white/10 bg-white/6 p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.24em] text-white/38">
                    Comparison set
                  </p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {telemetry.competitors.map((competitor) => (
                      <span
                        key={competitor}
                        className="rounded-full border border-white/10 bg-white/8 px-3 py-1.5 text-xs text-white/74"
                      >
                        {compactPathLabel(competitor)}
                      </span>
                    ))}
                  </div>
                </div>
              ) : null}

              {telemetry.opportunities.length > 0 ? (
                <div className="rounded-[1.35rem] border border-white/10 bg-white/6 p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.24em] text-white/38">
                    Growth angles surfaced
                  </p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {telemetry.opportunities.map((item) => (
                      <span
                        key={item.keyword}
                        className="rounded-full border border-[#f3bf88]/20 bg-[#f3bf88]/10 px-3 py-1.5 text-xs text-[#f6d9b5]"
                      >
                        {item.keyword}
                      </span>
                    ))}
                  </div>
                </div>
              ) : null}
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.section>
  );
}

function EmptyCanvas() {
  return (
    <motion.section
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      className="mt-10"
    >
      <Card className="rounded-[2rem] border border-dashed border-[#1f4d5d]/20 bg-white/60 backdrop-blur-xl">
        <CardHeader>
          <Badge className="w-fit border-[#dce6e2] bg-[#f5f7f2] text-[#0e5d6f]">
            Ready for an AI-led audit
          </Badge>
          <CardTitle className="text-3xl text-[#11232d]">
            Launch a domain and the agent team takes over.
          </CardTitle>
          <CardDescription className="max-w-2xl text-base leading-7 text-[#66757d]">
            The crawl agent maps the site, the audit agent scores SEO health, the
            strategy agents generate opportunities, and the narrator agent turns that
            evidence into a report your sponsor can actually understand.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-3">
          {[
            {
              title: "Agent mission board",
              text: "Clear progress, active agent handoffs, crawl blockers, and the current target URL as the analysis runs.",
            },
            {
              title: "Executive SEO brief",
              text: "A crisp management summary with strongest asset, biggest risk, roadmap, and growth angles.",
            },
            {
              title: "Fix lab",
              text: "Push a finding into the AI fix generator and review the before/after code without leaving the page.",
            },
          ].map((item) => (
            <div
              key={item.title}
              className="rounded-[1.5rem] border border-[#dfe7e1] bg-[#fbf7ef]/80 p-5"
            >
              <p className="text-sm font-semibold uppercase tracking-[0.18em] text-[#0e5d6f]">
                {item.title}
              </p>
              <p className="mt-3 text-sm leading-6 text-[#6b7a7c]">{item.text}</p>
            </div>
          ))}
        </CardContent>
      </Card>
    </motion.section>
  );
}

export function SeoStudio() {
  const [url, setUrl] = useState(defaultUrl);
  const [report, setReport] = useState<AnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [liveTelemetry, setLiveTelemetry] = useState<LiveTelemetryState>(
    createInitialLiveTelemetry,
  );
  const [activeTab, setActiveTab] = useState("findings");
  const [fixIssue, setFixIssue] = useState("");
  const [fixResult, setFixResult] = useState<FixResponse | null>(null);
  const [isFixing, setIsFixing] = useState(false);

  const reportTaskId = useMemo(() => parseReportTaskId(report?.report_url), [report]);
  const heroMetrics = report?.pdf_template_data.hero_metrics.slice(0, 4) ?? [];
  const findings = report?.technical_audit.findings ?? [];
  const highlightedFindings = findings.slice(0, 6);
  const metricSummary = report?.technical_audit.metric_summary.slice(0, 5) ?? [];
  const priorityActions = report?.pdf_template_data.priority_actions.slice(0, 4) ?? [];
  const opportunities = report?.competitive_intelligence.market_opportunities ?? [];
  const pageSummaries = report?.crawl_overview.sampled_pages.slice(0, 8) ?? [];
  const activeAgent = getAgentDefinition(liveTelemetry.currentStageId);
  const missionProgress = deriveMissionProgress(liveTelemetry);
  const completedAgents = countCompletedStages(liveTelemetry.stageStatus);
  const nextAgent = getNextPendingAgent(liveTelemetry.stageStatus);

  function applyStreamEvent(event: AnalysisStreamEvent) {
    setLiveTelemetry((current) => {
      const next: LiveTelemetryState = {
        ...current,
        resources: { ...current.resources },
        stageStatus: { ...current.stageStatus },
      };

      switch (event.type) {
        case "run_started":
          next.currentUrl = event.url;
          next.signalValue = "Calibrating";
          next.signalHint = "The audit score appears after the health agent finishes its first pass.";
          next.activityFeed = appendLimited(
            current.activityFeed,
            buildFeedItem("Run started", event.message, "teal", event.elapsed_seconds),
            8,
          );
          return next;

        case "stage":
          next.currentStageId = event.stage;
          next.stageDetail = event.detail;
          next.stageStatus[event.stage] =
            event.status === "completed" ? "completed" : "active";
          next.activityFeed = appendLimited(
            current.activityFeed,
            buildFeedItem(
              event.label,
              event.detail,
              event.status === "completed" ? "teal" : "ink",
              event.elapsed_seconds,
            ),
            8,
          );
          return next;

        case "crawl_seed":
          next.currentUrl = event.url;
          next.crawlBudget = event.max_pages;
          next.activityFeed = appendLimited(
            current.activityFeed,
            buildFeedItem(
              "Mission seeded",
              `Launching the scout agent from ${compactPathLabel(event.url)} with a ${event.max_pages}-page sample budget.`,
              "ink",
              event.elapsed_seconds,
            ),
            8,
          );
          return next;

        case "crawl_request":
          next.currentUrl = event.url;
          next.queueRemaining = event.queue_remaining;
          return next;

        case "crawl_page":
          next.currentUrl = event.url;
          next.analyzedPages = event.analyzed_pages;
          next.discoveredPages = event.discovered_internal_pages;
          next.queueRemaining = event.queue_remaining;
          next.crawlDepth = Math.max(current.crawlDepth, event.depth);
          if (current.crawlBudget > 0) {
            next.sampleCoverageRatio = `${Math.min(
              Math.round((event.analyzed_pages / current.crawlBudget) * 100),
              100,
            )}%`;
          }
          next.recentPages = appendUniqueBy(
            current.recentPages,
            event,
            (item) => item.url,
            6,
          );
          next.activityFeed = appendLimited(
            current.activityFeed,
            buildFeedItem(
              `Fetched depth ${event.depth}`,
              `${compactPathLabel(event.url)} surfaced ${event.new_links_count} new URLs.`,
              "teal",
              event.elapsed_seconds,
            ),
            8,
          );
          return next;

        case "crawl_resource":
          next.resources[event.resource] = event.status;
          next.activityFeed = appendLimited(
            current.activityFeed,
            buildFeedItem(
              `${event.resource.replaceAll("_", " ")} scanned`,
              event.status,
              "amber",
              event.elapsed_seconds,
            ),
            8,
          );
          return next;

        case "crawl_summary":
          next.analyzedPages = event.analyzed_pages;
          next.discoveredPages = event.discovered_internal_pages;
          next.crawlDepth = event.crawl_depth;
          next.sampleCoverageRatio = `${event.sample_coverage_ratio}%`;
          next.activityFeed = appendLimited(
            current.activityFeed,
            buildFeedItem(
              "Crawl summary ready",
              `${event.analyzed_pages} pages sampled across depth ${event.crawl_depth}.`,
              "teal",
              event.elapsed_seconds,
            ),
            8,
          );
          return next;

        case "crawl_error":
        case "crawl_skip":
          {
            const issueType = classifyCrawlIssue(event);
            next.crawlIssues = {
              ...current.crawlIssues,
              total: current.crawlIssues.total + 1,
              [issueType]: current.crawlIssues[issueType] + 1,
            };
            next.crawlIssueSamples = appendUniqueBy(
              current.crawlIssueSamples,
              buildFeedItem(
                issueType === "blocked"
                  ? "Access barrier"
                  : issueType === "missing"
                    ? "Broken route"
                    : issueType === "timeout"
                      ? "Slow response"
                      : event.type === "crawl_skip"
                        ? "Non-HTML skipped"
                        : "Crawl issue",
                `${compactPathLabel(event.url)} · ${event.detail}`,
                issueType === "timeout" || issueType === "blocked" || issueType === "missing"
                  ? "rose"
                  : "amber",
                event.elapsed_seconds,
              ),
              (item) => item.detail,
              5,
            );

            if (
              next.crawlIssues.total <= 3 ||
              next.crawlIssues.total % 4 === 0
            ) {
              next.activityFeed = appendLimited(
                current.activityFeed,
                buildFeedItem(
                  issueType === "blocked" ? "Barrier detected" : "Crawl issue contained",
                  summarizeIssues(next.crawlIssues),
                  "rose",
                  event.elapsed_seconds,
                ),
                8,
              );
            }

            return next;
          }

        case "health_snapshot":
          next.signalValue = event.overall_seo_health;
          next.signalHint = `${event.analyzed_pages} pages scored across ${event.metric_summary.length} benchmark groups`;
          next.sampleCoverageRatio = `${event.sample_coverage_ratio}%`;
          next.activityFeed = appendLimited(
            current.activityFeed,
            buildFeedItem(
              "Signal snapshot",
              `Board signal moved to ${event.overall_seo_health}.`,
              "teal",
              event.elapsed_seconds,
            ),
            8,
          );
          return next;

        case "finding":
          next.recentFindings = appendUniqueBy(
            current.recentFindings,
            event.finding,
            (item) => item.metric,
            6,
          );
          next.activityFeed = appendLimited(
            current.activityFeed,
            buildFeedItem(
              `Finding: ${event.finding.metric}`,
              event.finding.recommendation,
              "rose",
              event.elapsed_seconds,
            ),
            8,
          );
          return next;

        case "ai_update":
          next.aiUpdatesSeen = current.aiUpdatesSeen + 1;
          next.activityFeed = appendLimited(
            current.activityFeed,
            buildFeedItem(event.label, event.detail, "amber", event.elapsed_seconds),
            8,
          );
          return next;

        case "competitor_update":
          next.competitors = event.competitors.slice(0, 4);
          next.competitorUpdatesSeen = current.competitorUpdatesSeen + 1;
          next.activityFeed = appendLimited(
            current.activityFeed,
            buildFeedItem(
              `Competitor ${event.phase}`,
              `${event.count} domains are in the comparison set.`,
              "ink",
              event.elapsed_seconds,
            ),
            8,
          );
          return next;

        case "opportunity":
          next.opportunities = appendUniqueBy(
            current.opportunities,
            event.opportunity,
            (item) => item.keyword,
            5,
          );
          next.activityFeed = appendLimited(
            current.activityFeed,
            buildFeedItem(
              `Market gap: ${event.opportunity.keyword}`,
              event.opportunity.recommendation,
              "teal",
              event.elapsed_seconds,
            ),
            8,
          );
          return next;

        case "report_status":
          next.reportUpdatesSeen = current.reportUpdatesSeen + 1;
          next.activityFeed = appendLimited(
            current.activityFeed,
            buildFeedItem(
              event.label,
              event.detail,
              "teal",
              event.elapsed_seconds,
            ),
            8,
          );
          return next;

        default:
          return current;
      }
    });
  }

  async function handleAnalyze(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const nextUrl = url.trim();
    if (!nextUrl) {
      setError("Enter a URL before running the audit.");
      return;
    }

    setIsLoading(true);
    setError(null);
    setFixResult(null);
    setActiveTab("findings");
    setReport(null);
    setFixIssue("");
    setLiveTelemetry(createInitialLiveTelemetry());

    try {
      const response = await fetch("/api/analyze-url/stream", {
        method: "POST",
        headers: {
          "content-type": "application/json",
        },
        body: JSON.stringify({ url: nextUrl }),
      });

      if (!response.ok) {
        throw new Error(await readErrorMessage(response));
      }

      let streamError: string | null = null;
      let finalPayload: AnalysisResponse | null = null;

      await consumeNdjsonStream(response, (streamEvent) => {
        if (streamEvent.type === "result") {
          finalPayload = streamEvent.payload;
          setReport(streamEvent.payload);

          if (streamEvent.payload.technical_audit.findings[0]) {
            setFixIssue(buildFixSeed(streamEvent.payload.technical_audit.findings[0]));
          }

          return;
        }

        if (streamEvent.type === "error") {
          streamError = streamEvent.detail;
          return;
        }

        applyStreamEvent(streamEvent);
      });

      if (streamError) {
        throw new Error(streamError);
      }

      if (!finalPayload) {
        throw new Error("The streamed analysis ended before the final report payload arrived.");
      }
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "The analysis request failed unexpectedly.",
      );
    } finally {
      setIsLoading(false);
    }
  }

  async function handleGenerateFix() {
    const issue = fixIssue.trim();
    if (!issue) {
      setError("Describe the issue you want the fix generator to resolve.");
      return;
    }

    setIsFixing(true);
    setError(null);

    try {
      const response = await fetch("/api/generate-fix", {
        method: "POST",
        headers: {
          "content-type": "application/json",
        },
        body: JSON.stringify({ issue }),
      });

      if (!response.ok) {
        throw new Error(await readErrorMessage(response));
      }

      const payload = (await response.json()) as FixResponse;
      setFixResult(payload);
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "The fix generator failed unexpectedly.",
      );
    } finally {
      setIsFixing(false);
    }
  }

  return (
    <div className="relative min-h-screen overflow-hidden">
      <div className="pointer-events-none absolute inset-x-0 top-0 h-64 bg-[radial-gradient(circle_at_top_left,rgba(17,105,122,0.26),transparent_45%),radial-gradient(circle_at_top_right,rgba(217,128,67,0.18),transparent_40%)]" />
      <main className="relative mx-auto flex min-h-screen w-full max-w-7xl flex-col px-4 pb-24 pt-6 md:px-8 md:pt-10">
        <motion.header
          initial={{ opacity: 0, y: -16 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between"
        >
          <div className="space-y-4">
            <Badge className="w-fit border-white/60 bg-white/72 px-4 py-1 text-[11px] uppercase tracking-[0.3em] text-[#0e5d6f] shadow-sm">
              SEO Spy Studio
            </Badge>
            <div className="space-y-4">
              <h1 className="max-w-4xl font-heading text-[3.2rem] leading-[0.9] text-[#10242f] sm:text-[4.4rem] lg:text-[5.4rem]">
                Let AI agents crawl, diagnose, and brief the site in one sponsor-ready flow.
              </h1>
              <p className="max-w-2xl text-base leading-8 text-[#66757d] md:text-lg">
                Scout, Audit, Strategy, Market, and Narrator agents work live against the
                domain, then turn that evidence into a clean executive SEO brief instead
                of a confusing debug log.
              </p>
            </div>
          </div>
          <div className="grid gap-3 sm:grid-cols-3 lg:w-[29rem]">
            {[
              {
                icon: Radar,
                label: "FastAPI engine",
                value: "Live backend proxy",
              },
              {
                icon: FileStack,
                label: "Report export",
                value: "PDF download relay",
              },
              {
                icon: WandSparkles,
                label: "Fix lab",
                value: "Issue-to-code loop",
              },
            ].map((item) => (
              <div
                key={item.label}
                className="rounded-[1.4rem] border border-white/55 bg-white/72 p-4 shadow-[0_18px_50px_-38px_rgba(17,48,60,0.65)] backdrop-blur-xl"
              >
                <item.icon className="size-5 text-[#0e5d6f]" />
                <p className="mt-4 text-xs font-semibold uppercase tracking-[0.24em] text-[#6f7c7e]">
                  {item.label}
                </p>
                <p className="mt-2 text-sm font-medium text-[#11232d]">{item.value}</p>
              </div>
            ))}
          </div>
        </motion.header>

        <section className="mt-10 grid gap-6 xl:grid-cols-[1.12fr_0.88fr]">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
            <Card className="rounded-[2rem] border border-white/60 bg-white/74 shadow-[0_40px_120px_-62px_rgba(17,48,60,0.7)] backdrop-blur-xl">
              <CardHeader className="space-y-4">
                <Badge className="w-fit border-[#d5dfda] bg-[#f8faf8] px-4 py-1 text-[#0e5d6f]">
                  Analysis launchpad
                </Badge>
                <CardTitle className="text-3xl text-[#11232d] md:text-4xl">
                  Run a domain and watch the AI agent team build the SEO case live.
                </CardTitle>
                <CardDescription className="max-w-2xl text-base leading-7 text-[#66757d]">
                  The browser never talks to Python directly. Next.js proxies the crawl,
                  streaming updates back as the agents map the site, score technical
                  health, compare competitors, and draft the final narrative.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <form className="space-y-4" onSubmit={handleAnalyze}>
                  <div className="grid gap-3 md:grid-cols-[1fr_auto]">
                    <Input
                      value={url}
                      onChange={(event) => setUrl(event.target.value)}
                      placeholder="https://example.com"
                      className="h-12 rounded-[1.25rem] border-[#d6e0dc] bg-white/90 px-4 text-base shadow-inner shadow-[#f1e8d7]"
                    />
                    <Button
                      type="submit"
                      className="h-12 rounded-[1.25rem] bg-[#0f6775] px-6 text-white hover:bg-[#0d5561]"
                      disabled={isLoading}
                    >
                      {isLoading ? (
                        <>
                          <LoaderCircle className="size-4 animate-spin" />
                          Auditing
                        </>
                      ) : (
                        <>
                          <ScanSearch className="size-4" />
                          Run audit
                        </>
                      )}
                    </Button>
                  </div>
                  <div className="flex flex-wrap gap-2 text-xs">
                    {[
                      { label: "Use books demo", value: "https://books.toscrape.com/" },
                      { label: "Use example.com", value: "https://example.com/" },
                    ].map((preset) => (
                      <button
                        key={preset.value}
                        type="button"
                        onClick={() => setUrl(preset.value)}
                        className="rounded-full border border-[#dbe4df] bg-white/72 px-3 py-1.5 text-[#5f7277] transition-colors hover:border-[#0f6775]/25 hover:text-[#0f6775]"
                      >
                        {preset.label}
                      </button>
                    ))}
                  </div>
                  <div className="flex flex-wrap gap-2 text-xs text-[#6d7d81]">
                    <span className="rounded-full border border-[#dbe4df] bg-[#f8f4ea] px-3 py-1.5">
                      Live crawl telemetry
                    </span>
                    <span className="rounded-full border border-[#dbe4df] bg-[#f8f4ea] px-3 py-1.5">
                      Board-ready report export
                    </span>
                    <span className="rounded-full border border-[#dbe4df] bg-[#f8f4ea] px-3 py-1.5">
                      AI issue-to-fix loop
                    </span>
                  </div>
                </form>
                <AnimatePresence>
                  {error ? (
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -10 }}
                      className="mt-4 flex items-start gap-3 rounded-[1.4rem] border border-[#efc8bc] bg-[#fff4ef] p-4 text-sm text-[#a5481f]"
                    >
                      <TriangleAlert className="mt-0.5 size-4 shrink-0" />
                      <span>{error}</span>
                    </motion.div>
                  ) : null}
                </AnimatePresence>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }}>
            <Card className="relative overflow-hidden rounded-[2rem] border border-[#143643]/10 bg-[#102f3c] text-white shadow-[0_45px_140px_-70px_rgba(9,28,36,1)]">
              <div className="pointer-events-none absolute -right-20 -top-12 size-56 rounded-full bg-[#e9b47f]/15 blur-3xl" />
              <div className="pointer-events-none absolute -bottom-16 left-8 size-48 rounded-full bg-[#2e8f97]/18 blur-3xl" />
              <CardHeader className="relative z-10">
                <Badge className="w-fit border-white/15 bg-white/10 text-white">
                  Agent mission board
                </Badge>
                <CardTitle className="text-3xl text-[#f7f0e3]">
                  {report
                    ? report.pdf_template_data.report_title
                    : isLoading
                      ? `${activeAgent.codename} is driving the audit`
                      : "What the sponsor sees in real time"}
                </CardTitle>
                <CardDescription className="text-base leading-7 text-white/72">
                  {report
                    ? report.management_summary.board_verdict
                    : isLoading
                      ? buildMissionSummary(liveTelemetry)
                      : "A live command surface that shows which AI agent is active, what evidence it has collected, what blocked it, and what recommendation comes next."}
                </CardDescription>
              </CardHeader>
              <CardContent className="relative z-10 space-y-6">
                {isLoading && !report ? (
                  <div className="rounded-[1.55rem] border border-white/10 bg-white/8 p-4">
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <p className="text-xs font-semibold uppercase tracking-[0.24em] text-white/42">
                          Mission progress
                        </p>
                        <p className="mt-2 text-2xl font-semibold text-[#f7f0e3]">
                          {missionProgress}% complete
                        </p>
                      </div>
                      <Badge className="border-white/12 bg-white/10 text-white/80">
                        {completedAgents} of 5 agents finished
                      </Badge>
                    </div>
                    <div className="mt-4 h-2.5 overflow-hidden rounded-full bg-white/10">
                      <motion.div
                        animate={{ width: `${missionProgress}%` }}
                        className="h-full rounded-full bg-[linear-gradient(90deg,#8de0d6,#f3bf88)]"
                        transition={{ type: "spring", stiffness: 110, damping: 18 }}
                      />
                    </div>
                    <div className="mt-4 grid gap-3 sm:grid-cols-2">
                      <div className="rounded-[1.2rem] border border-white/10 bg-white/6 p-3">
                        <p className="text-[11px] uppercase tracking-[0.22em] text-white/38">
                          Active agent
                        </p>
                        <p className="mt-2 text-sm font-semibold text-white">
                          {activeAgent.mission}
                        </p>
                      </div>
                      <div className="rounded-[1.2rem] border border-white/10 bg-white/6 p-3">
                        <p className="text-[11px] uppercase tracking-[0.22em] text-white/38">
                          Next handoff
                        </p>
                        <p className="mt-2 text-sm font-semibold text-white">
                          {nextAgent
                            ? nextAgent.codename
                            : "Exporting the executive brief"}
                        </p>
                      </div>
                    </div>
                  </div>
                ) : null}

                <div className="grid gap-3 sm:grid-cols-3">
                  <MetricTile
                    label="Signal"
                    value={
                      report
                        ? report.technical_audit.overall_seo_health
                        : isLoading
                          ? liveTelemetry.signalValue
                          : "Waiting"
                    }
                    hint={
                      report
                        ? report.management_summary.confidence_note
                        : isLoading
                          ? liveTelemetry.signalHint
                          : "Run a crawl to fill the board."
                    }
                  />
                  <MetricTile
                    label="Pages"
                    value={
                      report
                        ? compactNumber(report.crawl_overview.discovered_internal_pages)
                        : compactNumber(liveTelemetry.discoveredPages)
                    }
                    hint={
                      report ? "Internal URLs discovered" : `${liveTelemetry.analyzedPages} pages mapped`
                    }
                  />
                  <MetricTile
                    label={report ? "Speed" : "Blockers"}
                    value={
                      report
                        ? `${report.page_speed.score}/100`
                        : `${liveTelemetry.crawlIssues.total}`
                    }
                    hint={
                      report
                        ? report.page_speed.status
                        : isLoading
                          ? summarizeIssues(liveTelemetry.crawlIssues)
                          : "Live once analysis starts"
                    }
                  />
                </div>
                {isLoading && !report ? (
                  <div className="grid gap-3 sm:grid-cols-2">
                    <div className="rounded-[1.25rem] border border-white/10 bg-white/6 px-4 py-3">
                      <p className="text-[11px] uppercase tracking-[0.24em] text-white/38">
                        Current target
                      </p>
                      <p className="mt-2 text-sm text-white/80">
                        {liveTelemetry.currentUrl
                          ? compactPathLabel(liveTelemetry.currentUrl)
                          : "Waiting for the first page"}
                      </p>
                    </div>
                    <div className="rounded-[1.25rem] border border-white/10 bg-white/6 px-4 py-3">
                      <p className="text-[11px] uppercase tracking-[0.24em] text-white/38">
                        Queue health
                      </p>
                      <p className="mt-2 text-sm text-white/80">
                        {liveTelemetry.queueRemaining} URLs waiting · depth {liveTelemetry.crawlDepth}
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {stageDefinitions.map((item, index) => {
                      const Icon = item.icon;
                      const status = report
                        ? "completed"
                        : liveTelemetry.stageStatus[item.id];

                      return (
                        <div
                          key={item.id}
                          className={cn(
                            "flex items-start gap-3 rounded-[1.3rem] border px-4 py-3 text-sm backdrop-blur-xl transition-colors",
                            status === "completed"
                              ? "border-[#2d7b82]/28 bg-white/12 text-white"
                              : status === "active"
                                ? "border-[#f3bf88]/40 bg-white/14 text-white"
                                : "border-white/10 bg-white/6 text-white/72",
                          )}
                        >
                          <div className="mt-0.5 rounded-full border border-white/15 bg-white/10 p-1">
                            <Icon className="size-3.5" />
                          </div>
                          <div>
                            <p className="text-[11px] uppercase tracking-[0.26em] text-white/40">
                              Stage {index + 1}
                            </p>
                            <p className="mt-1 leading-6">{item.label}</p>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>
        </section>

        <AnimatePresence initial={false}>
          {isLoading ? <LoadingDeck telemetry={liveTelemetry} /> : null}
        </AnimatePresence>

        {report ? (
          <motion.div
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-12 space-y-10"
          >
            <section className="grid gap-6 xl:grid-cols-[1.18fr_0.82fr]">
              <Card className="rounded-[2rem] border border-[#133341]/12 bg-[#102f3c] text-white shadow-[0_45px_140px_-74px_rgba(9,28,36,0.98)]">
                <CardHeader className="space-y-4">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <Badge className="border-white/15 bg-white/10 text-white">
                      Executive readout
                    </Badge>
                    {reportTaskId ? (
                      <Button asChild variant="ghost" className="rounded-full border border-white/15 bg-white/10 px-4 text-white hover:bg-white/15 hover:text-white">
                        <a href={`/api/download-report/${reportTaskId}`} target="_blank" rel="noreferrer">
                          <Download className="size-4" />
                          Download report
                        </a>
                      </Button>
                    ) : null}
                  </div>
                  <CardTitle className="text-3xl leading-tight text-[#f8f0e4] md:text-4xl">
                    {report.executive_summary}
                  </CardTitle>
                  <CardDescription className="max-w-3xl text-base leading-7 text-white/72">
                    {report.management_summary.confidence_note}
                  </CardDescription>
                </CardHeader>
                <CardContent className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                  {heroMetrics.map((metric: PdfMetric) => (
                    <div
                      key={metric.label}
                      className="rounded-[1.45rem] border border-white/10 bg-white/8 p-4"
                    >
                      <p className="text-xs font-semibold uppercase tracking-[0.22em] text-white/45">
                        {metric.label}
                      </p>
                      <p className="mt-3 text-2xl font-semibold text-[#fff8ed]">{metric.value}</p>
                    </div>
                  ))}
                </CardContent>
                <CardFooter className="flex flex-wrap items-center justify-between gap-3 border-white/10 bg-white/6 text-white/75">
                  <div className="flex items-center gap-2 text-sm">
                    <Gauge className="size-4 text-[#f3bf88]" />
                    {report.page_speed.score}/100 page speed score
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <ArrowUpRight className="size-4 text-[#8de0d6]" />
                    {report.crawl_overview.sample_coverage_ratio} sample coverage ratio
                  </div>
                </CardFooter>
              </Card>

              <div className="grid gap-4">
                {[
                  [
                    "Strongest asset",
                    report.management_summary.strongest_asset,
                    "Where the site is already winning",
                  ],
                  [
                    "Biggest risk",
                    report.management_summary.biggest_risk,
                    "The issue to neutralize first",
                  ],
                  [
                    "Growth opportunity",
                    report.management_summary.growth_opportunity,
                    "The angle with the cleanest upside",
                  ],
                ].map(([label, value, hint]) => (
                  <div
                    key={label}
                    className="rounded-[1.6rem] border border-white/55 bg-white/72 p-5 shadow-[0_18px_45px_-35px_rgba(17,48,60,0.55)] backdrop-blur-xl"
                  >
                    <p className="text-xs font-semibold uppercase tracking-[0.24em] text-[#6a726f]">
                      {label}
                    </p>
                    <p className="mt-3 text-lg leading-7 font-semibold text-[#11232d]">
                      {value}
                    </p>
                    <p className="mt-2 text-sm text-[#66757d]">{hint}</p>
                  </div>
                ))}
                <div className="grid gap-4 sm:grid-cols-2">
                  <MetricTile
                    label="Crawl depth"
                    value={`${report.crawl_overview.crawl_depth}`}
                    hint={report.crawl_overview.robots_txt_status}
                  />
                  <MetricTile
                    label="Domain authority"
                    value={`${report.crawl_overview.domain_authority}`}
                    hint={report.crawl_overview.sitemap_status}
                  />
                </div>
              </div>
            </section>

            <section className="space-y-5">
              <SectionHeading
                eyebrow="Report deck"
                title="Audit, opportunities, roadmap, and fixes"
                blurb="Every major payload from the FastAPI response is mapped into the interface so the output is readable instead of buried in a single JSON blob."
              />

              <Tabs value={activeTab} onValueChange={setActiveTab} className="gap-5">
                <TabsList
                  variant="line"
                  className="w-full justify-start overflow-x-auto rounded-full border border-white/55 bg-white/70 p-1 backdrop-blur-xl"
                >
                  {[
                    ["findings", "Findings"],
                    ["opportunities", "Opportunities"],
                    ["roadmap", "Roadmap"],
                    ["keywords", "Keywords"],
                    ["pages", "Pages"],
                    ["fix-lab", "Fix Lab"],
                  ].map(([value, label]) => (
                    <TabsTrigger
                      key={value}
                      value={value}
                      className="rounded-full px-4 data-active:bg-[#102f3c] data-active:text-white"
                    >
                      {label}
                    </TabsTrigger>
                  ))}
                </TabsList>

                <TabsContent value="findings" className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
                  <Card className="rounded-[1.9rem] border border-white/60 bg-white/72 backdrop-blur-xl">
                    <CardHeader>
                      <Badge className="w-fit border-[#d6dfda] bg-[#f8faf8] text-[#0e5d6f]">
                        Priority actions
                      </Badge>
                      <CardTitle className="text-2xl text-[#11232d]">
                        The first moves the report would put in front of leadership.
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      {priorityActions.map((action: PdfPriorityAction) => (
                        <div
                          key={`${action.priority}-${action.headline}`}
                          className="rounded-[1.4rem] border border-[#dfe7e1] bg-[#fbf7ef]/80 p-4"
                        >
                          <Badge className={cn("border", priorityStyles(action.priority))}>
                            {action.priority}
                          </Badge>
                          <h3 className="mt-3 text-lg font-semibold text-[#11232d]">
                            {action.headline}
                          </h3>
                          <p className="mt-2 text-sm leading-6 text-[#627379]">{action.action}</p>
                          <p className="mt-3 text-sm leading-6 text-[#0e5d6f]">{action.business_impact}</p>
                        </div>
                      ))}
                    </CardContent>
                  </Card>

                  <Card className="rounded-[1.9rem] border border-white/60 bg-white/72 backdrop-blur-xl">
                    <CardHeader>
                      <Badge className="w-fit border-[#d6dfda] bg-[#f8faf8] text-[#0e5d6f]">
                        Technical findings
                      </Badge>
                      <CardTitle className="text-2xl text-[#11232d]">
                        The frontend sorts the raw audit into action-ready cards.
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      {highlightedFindings.map((finding: TechnicalFinding) => (
                        <div
                          key={`${finding.metric}-${finding.current_value}`}
                          className="rounded-[1.45rem] border border-[#dfe7e1] bg-white/75 p-4"
                        >
                          <div className="flex flex-wrap items-start justify-between gap-3">
                            <div>
                              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[#708185]">
                                {finding.category}
                              </p>
                              <h3 className="mt-2 text-lg font-semibold text-[#11232d]">
                                {finding.metric}
                              </h3>
                            </div>
                            <Badge className={cn("border", priorityStyles(finding.priority))}>
                              {finding.priority}
                            </Badge>
                          </div>
                          <p className={cn("mt-2 text-sm font-medium", statusStyles(finding.status))}>
                            {finding.status}
                          </p>
                          <div className="mt-3 grid gap-3 sm:grid-cols-2">
                            <div className="rounded-[1.2rem] bg-[#f8f2e4] p-3">
                              <p className="text-xs uppercase tracking-[0.22em] text-[#8b7b65]">
                                Current value
                              </p>
                              <p className="mt-2 text-sm leading-6 text-[#394a50]">
                                {finding.current_value}
                              </p>
                            </div>
                            <div className="rounded-[1.2rem] bg-[#eef7f6] p-3">
                              <p className="text-xs uppercase tracking-[0.22em] text-[#5f7c80]">
                                Benchmark
                              </p>
                              <p className="mt-2 text-sm leading-6 text-[#394a50]">
                                {finding.benchmark}
                              </p>
                            </div>
                          </div>
                          <p className="mt-3 text-sm leading-6 text-[#67787d]">
                            {finding.business_impact}
                          </p>
                          <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
                            <p className="max-w-2xl text-sm font-medium text-[#0e5d6f]">
                              {finding.recommendation}
                            </p>
                            <Button
                              variant="outline"
                              size="sm"
                              className="rounded-full border-[#cdd9d5] bg-white"
                              onClick={() => {
                                setFixIssue(buildFixSeed(finding));
                                setActiveTab("fix-lab");
                              }}
                            >
                              <Bot className="size-4" />
                              Send to fix lab
                            </Button>
                          </div>
                          {finding.evidence.length > 0 ? (
                            <div className="mt-4 flex flex-wrap gap-2">
                              {finding.evidence.slice(0, 2).map((item) => (
                                <span
                                  key={`${item.url}-${item.observation}`}
                                  className="rounded-full border border-[#dfe7e1] bg-[#f6f8f5] px-3 py-1.5 text-xs text-[#58686e]"
                                >
                                  {item.observation}
                                </span>
                              ))}
                            </div>
                          ) : null}
                        </div>
                      ))}
                    </CardContent>
                  </Card>
                </TabsContent>

                <TabsContent value="opportunities" className="grid gap-6 xl:grid-cols-[1fr_0.95fr]">
                  <Card className="rounded-[1.9rem] border border-white/60 bg-white/72 backdrop-blur-xl">
                    <CardHeader>
                      <Badge className="w-fit border-[#d6dfda] bg-[#f8faf8] text-[#0e5d6f]">
                        Market opportunities
                      </Badge>
                      <CardTitle className="text-2xl text-[#11232d]">
                        Competitive whitespace the audit thinks you can own next.
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="grid gap-4 md:grid-cols-2">
                      {opportunities.map((item: MarketOpportunity) => (
                        <div
                          key={item.keyword}
                          className="rounded-[1.45rem] border border-[#dfe7e1] bg-white/75 p-4"
                        >
                          <div className="flex items-center justify-between gap-3">
                            <Badge className={cn("border", priorityStyles(item.priority))}>
                              {item.priority}
                            </Badge>
                            <span className="text-xs font-semibold uppercase tracking-[0.24em] text-[#0e5d6f]">
                              {item.market_opportunity_score}/10 score
                            </span>
                          </div>
                          <h3 className="mt-4 text-lg font-semibold text-[#11232d]">
                            {item.keyword}
                          </h3>
                          <p className="mt-2 text-sm leading-6 text-[#67787d]">
                            {item.relevance_to_business}
                          </p>
                          <Separator className="my-4 bg-[#dfe7e1]" />
                          <p className="text-sm leading-6 text-[#0e5d6f]">{item.business_impact}</p>
                          <p className="mt-3 text-sm leading-6 text-[#67787d]">{item.recommendation}</p>
                        </div>
                      ))}
                    </CardContent>
                  </Card>

                  <div className="grid gap-6">
                    <Card className="rounded-[1.9rem] border border-white/60 bg-white/72 backdrop-blur-xl">
                      <CardHeader>
                        <Badge className="w-fit border-[#d6dfda] bg-[#f8faf8] text-[#0e5d6f]">
                          Metric snapshots
                        </Badge>
                        <CardTitle className="text-2xl text-[#11232d]">
                          Key benchmark readouts pulled from the response.
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-3">
                        {metricSummary.map((item: MetricSnapshot) => (
                          <div
                            key={`${item.metric}-${item.current_value}`}
                            className="grid gap-2 rounded-[1.3rem] border border-[#dfe7e1] bg-[#fbf7ef]/80 p-4 sm:grid-cols-[1fr_auto] sm:items-center"
                          >
                            <div>
                              <p className="text-sm font-semibold text-[#11232d]">{item.metric}</p>
                              <p className="mt-1 text-sm text-[#66757d]">
                                {item.current_value} against {item.benchmark}
                              </p>
                            </div>
                            <p className={cn("text-sm font-medium", statusStyles(item.status))}>
                              {item.status}
                            </p>
                          </div>
                        ))}
                      </CardContent>
                    </Card>

                    <Card className="rounded-[1.9rem] border border-white/60 bg-white/72 backdrop-blur-xl">
                      <CardHeader>
                        <Badge className="w-fit border-[#d6dfda] bg-[#f8faf8] text-[#0e5d6f]">
                          Data limitations
                        </Badge>
                        <CardTitle className="text-2xl text-[#11232d]">
                          Where the report is being transparent about missing context.
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        {report.data_limitations.map((item) => (
                          <div
                            key={`${item.data_source}-${item.current_status}`}
                            className="rounded-[1.35rem] border border-[#dfe7e1] bg-white/75 p-4"
                          >
                            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[#708185]">
                              {item.data_source}
                            </p>
                            <p className="mt-2 text-base font-semibold text-[#11232d]">
                              {item.current_status}
                            </p>
                            <p className="mt-2 text-sm leading-6 text-[#67787d]">{item.why_it_matters}</p>
                            <p className="mt-3 text-sm font-medium leading-6 text-[#0e5d6f]">
                              Next step: {item.next_step}
                            </p>
                          </div>
                        ))}
                      </CardContent>
                    </Card>
                  </div>
                </TabsContent>

                <TabsContent value="roadmap" className="grid gap-6 lg:grid-cols-3">
                  {report.recommended_roadmap.map((item: RoadmapItem) => (
                    <Card
                      key={`${item.timeline}-${item.objective}`}
                      className={cn(
                        "rounded-[1.9rem] border border-white/60 bg-gradient-to-b backdrop-blur-xl",
                        toneForRoadmap(item.priority),
                      )}
                    >
                      <CardHeader>
                        <div className="flex items-center justify-between gap-3">
                          <Badge className={cn("border", priorityStyles(item.priority))}>
                            {item.priority}
                          </Badge>
                          <span className="text-xs font-semibold uppercase tracking-[0.24em] text-[#0e5d6f]">
                            {item.timeline}
                          </span>
                        </div>
                        <CardTitle className="text-2xl text-[#11232d]">{item.objective}</CardTitle>
                        <CardDescription className="text-sm leading-6 text-[#66757d]">
                          {item.expected_outcome}
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        <ul className="space-y-3">
                          {item.actions.map((action) => (
                            <li
                              key={action}
                              className="rounded-[1.2rem] border border-white/70 bg-white/70 px-4 py-3 text-sm leading-6 text-[#394a50]"
                            >
                              {action}
                            </li>
                          ))}
                        </ul>
                      </CardContent>
                    </Card>
                  ))}
                </TabsContent>

                <TabsContent value="keywords" className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
                  <div className="grid gap-6">
                    <Card className="rounded-[1.9rem] border border-white/60 bg-white/72 backdrop-blur-xl">
                      <CardHeader>
                        <Badge className="w-fit border-[#d6dfda] bg-[#f8faf8] text-[#0e5d6f]">
                          Keyword strategy
                        </Badge>
                        <CardTitle className="text-2xl text-[#11232d]">
                          Primary and long-tail targets from the analysis response.
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-5">
                        <div>
                          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[#708185]">
                            Primary keywords
                          </p>
                          <div className="mt-3 flex flex-wrap gap-2">
                            {report.keyword_analysis.primary_keywords.map((keyword) => (
                              <span
                                key={keyword}
                                className="rounded-full border border-[#d9e1dc] bg-[#f8faf8] px-3 py-1.5 text-sm text-[#0e5d6f]"
                              >
                                {keyword}
                              </span>
                            ))}
                          </div>
                        </div>
                        <div>
                          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[#708185]">
                            Long-tail keywords
                          </p>
                          <div className="mt-3 flex flex-wrap gap-2">
                            {report.keyword_analysis.long_tail_keywords.map((keyword) => (
                              <span
                                key={keyword}
                                className="rounded-full border border-[#eadbbd] bg-[#fff7ea] px-3 py-1.5 text-sm text-[#8b6224]"
                              >
                                {keyword}
                              </span>
                            ))}
                          </div>
                        </div>
                      </CardContent>
                    </Card>

                    <Card className="rounded-[1.9rem] border border-white/60 bg-white/72 backdrop-blur-xl">
                      <CardHeader>
                        <Badge className="w-fit border-[#d6dfda] bg-[#f8faf8] text-[#0e5d6f]">
                          Intent map
                        </Badge>
                        <CardTitle className="text-2xl text-[#11232d]">
                          Informational, transactional, and navigational buckets.
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="grid gap-4 md:grid-cols-3">
                        {[
                          {
                            label: "Informational",
                            values: report.keyword_analysis.keyword_intent.informational,
                          },
                          {
                            label: "Transactional",
                            values: report.keyword_analysis.keyword_intent.transactional,
                          },
                          {
                            label: "Navigational",
                            values: report.keyword_analysis.keyword_intent.navigational,
                          },
                        ].map(({ label, values }) => (
                          <div
                            key={label}
                            className="rounded-[1.35rem] border border-[#dfe7e1] bg-[#fbf7ef]/80 p-4"
                          >
                            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[#708185]">
                              {label}
                            </p>
                            <div className="mt-3 space-y-2">
                              {values.map((value) => (
                                <div key={value} className="rounded-full bg-white/85 px-3 py-2 text-sm text-[#394a50]">
                                  {value}
                                </div>
                              ))}
                            </div>
                          </div>
                        ))}
                      </CardContent>
                    </Card>
                  </div>

                  <div className="grid gap-6">
                    <Card className="rounded-[1.9rem] border border-white/60 bg-white/72 backdrop-blur-xl">
                      <CardHeader>
                        <Badge className="w-fit border-[#d6dfda] bg-[#f8faf8] text-[#0e5d6f]">
                          AI insights
                        </Badge>
                        <CardTitle className="text-2xl text-[#11232d]">
                          Leadership-facing synthesis from the backend insight block.
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        {report.ai_insights.insights.length > 0 ? (
                          report.ai_insights.insights.map((insight) => (
                            <div
                              key={`${insight.issue}-${insight.priority}`}
                              className="rounded-[1.4rem] border border-[#dfe7e1] bg-white/75 p-4"
                            >
                              <div className="flex flex-wrap items-center justify-between gap-3">
                                <p className="text-lg font-semibold text-[#11232d]">{insight.issue}</p>
                                <Badge className={cn("border", priorityStyles(insight.priority))}>
                                  {insight.priority}
                                </Badge>
                              </div>
                              <p className="mt-2 text-sm font-medium text-[#0e5d6f]">
                                Impact: {insight.impact}
                              </p>
                              <p className="mt-3 text-sm leading-6 text-[#67787d]">{insight.explanation}</p>
                              <p className="mt-3 text-sm font-medium leading-6 text-[#394a50]">
                                {insight.recommendation}
                              </p>
                            </div>
                          ))
                        ) : (
                          <div className="rounded-[1.4rem] border border-[#dfe7e1] bg-[#fbf7ef]/80 p-4 text-sm leading-6 text-[#67787d]">
                            No AI insight block was returned for this run.
                          </div>
                        )}
                      </CardContent>
                    </Card>

                    <Card className="rounded-[1.9rem] border border-white/60 bg-white/72 backdrop-blur-xl">
                      <CardHeader>
                        <Badge className="w-fit border-[#d6dfda] bg-[#f8faf8] text-[#0e5d6f]">
                          Content strategy
                        </Badge>
                        <CardTitle className="text-2xl text-[#11232d]">
                          Blog briefs and guest post angles suggested by the backend.
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        {report.content_strategy.blog_suggestions.map((post) => (
                          <div
                            key={post.title}
                            className="rounded-[1.4rem] border border-[#dfe7e1] bg-white/75 p-4"
                          >
                            <p className="text-lg font-semibold text-[#11232d]">{post.title}</p>
                            <p className="mt-2 text-sm text-[#0e5d6f]">
                              {post.target_audience} · {post.search_intent}
                            </p>
                            <div className="mt-3 space-y-2">
                              {post.outline.map((point) => (
                                <div key={point} className="rounded-full bg-[#f8f4ea] px-3 py-2 text-sm text-[#4f6168]">
                                  {point}
                                </div>
                              ))}
                            </div>
                          </div>
                        ))}
                        <Separator className="bg-[#dfe7e1]" />
                        <div className="flex flex-wrap gap-2">
                          {report.content_strategy.guest_post_titles.map((title) => (
                            <span
                              key={title}
                              className="rounded-full border border-[#d9e1dc] bg-[#f8faf8] px-3 py-1.5 text-sm text-[#0e5d6f]"
                            >
                              {title}
                            </span>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                </TabsContent>

                <TabsContent value="pages" className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
                  <Card className="rounded-[1.9rem] border border-white/60 bg-white/72 backdrop-blur-xl">
                    <CardHeader>
                      <Badge className="w-fit border-[#d6dfda] bg-[#f8faf8] text-[#0e5d6f]">
                        Sampled pages
                      </Badge>
                      <CardTitle className="text-2xl text-[#11232d]">
                        Representative pages surfaced by the crawl.
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="grid gap-4 md:grid-cols-2">
                      {pageSummaries.map((page: PageSummary) => (
                        <div
                          key={page.url}
                          className="rounded-[1.45rem] border border-[#dfe7e1] bg-white/75 p-4"
                        >
                          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[#708185]">
                            {page.page_type}
                          </p>
                          <h3 className="mt-2 line-clamp-2 text-lg font-semibold text-[#11232d]">
                            {page.title || page.url}
                          </h3>
                          <p className="mt-2 text-sm leading-6 text-[#67787d]">{page.key_issue}</p>
                          <div className="mt-4 grid grid-cols-2 gap-3 text-sm text-[#394a50]">
                            <div className="rounded-[1rem] bg-[#fbf7ef] p-3">
                              <p className="text-xs uppercase tracking-[0.22em] text-[#8b7b65]">Words</p>
                              <p className="mt-2 font-medium">{page.word_count}</p>
                            </div>
                            <div className="rounded-[1rem] bg-[#eef7f6] p-3">
                              <p className="text-xs uppercase tracking-[0.22em] text-[#5f7c80]">Authority</p>
                              <p className="mt-2 font-medium">{page.page_authority}</p>
                            </div>
                          </div>
                          <p className="mt-4 text-sm font-medium text-[#0e5d6f]">
                            SEO health: {page.seo_health}
                          </p>
                        </div>
                      ))}
                    </CardContent>
                  </Card>

                  <div className="grid gap-6">
                    <Card className="rounded-[1.9rem] border border-white/60 bg-white/72 backdrop-blur-xl">
                      <CardHeader>
                        <Badge className="w-fit border-[#d6dfda] bg-[#f8faf8] text-[#0e5d6f]">
                          Link profile
                        </Badge>
                        <CardTitle className="text-2xl text-[#11232d]">
                          Internal, external, and backlink context at a glance.
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <div className="grid gap-4 sm:grid-cols-2">
                          <MetricTile
                            label="Internal link score"
                            value={`${report.link_analysis.internal.internal_link_score}/100`}
                            hint="Internal linking strength"
                          />
                          <MetricTile
                            label="Estimated backlinks"
                            value={`${report.link_analysis.backlinks.estimated_backlinks}`}
                            hint={report.link_analysis.backlinks.backlink_strength}
                          />
                        </div>
                        <div className="rounded-[1.4rem] border border-[#dfe7e1] bg-[#fbf7ef]/80 p-4">
                          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[#708185]">
                            External domains sampled
                          </p>
                          <div className="mt-3 flex flex-wrap gap-2">
                            {report.link_analysis.external.domains.slice(0, 10).map((domain) => (
                              <span
                                key={domain}
                                className="rounded-full border border-[#e1d7c4] bg-white/85 px-3 py-1.5 text-sm text-[#6c5b47]"
                              >
                                {domain}
                              </span>
                            ))}
                          </div>
                        </div>
                      </CardContent>
                    </Card>

                    <Card className="rounded-[1.9rem] border border-white/60 bg-white/72 backdrop-blur-xl">
                      <CardHeader>
                        <Badge className="w-fit border-[#d6dfda] bg-[#f8faf8] text-[#0e5d6f]">
                          Appendix notes
                        </Badge>
                        <CardTitle className="text-2xl text-[#11232d]">
                          Crawl caveats and evidence context from the appendix.
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-3">
                        {report.detailed_appendix.evidence_notes.map((note) => (
                          <div
                            key={note}
                            className="rounded-[1.3rem] border border-[#dfe7e1] bg-white/75 px-4 py-3 text-sm leading-6 text-[#67787d]"
                          >
                            {note}
                          </div>
                        ))}
                      </CardContent>
                    </Card>
                  </div>
                </TabsContent>

                <TabsContent value="fix-lab" className="grid gap-6 xl:grid-cols-[0.82fr_1.18fr]">
                  <Card className="rounded-[1.9rem] border border-white/60 bg-white/72 backdrop-blur-xl">
                    <CardHeader>
                      <Badge className="w-fit border-[#d6dfda] bg-[#f8faf8] text-[#0e5d6f]">
                        AI fix lab
                      </Badge>
                      <CardTitle className="text-2xl text-[#11232d]">
                        Hand the backend a precise issue and get back current versus fixed code.
                      </CardTitle>
                      <CardDescription className="text-sm leading-6 text-[#66757d]">
                        Use one of the findings as a seed, or type a more precise engineering task.
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <Textarea
                        value={fixIssue}
                        onChange={(event) => setFixIssue(event.target.value)}
                        className="min-h-40 rounded-[1.4rem] border-[#d6e0dc] bg-white/90 px-4 py-3 text-sm shadow-inner shadow-[#f1e8d7]"
                        placeholder="Example: Meta description is missing on the homepage and should be replaced with a compelling 150-character summary."
                      />
                      <Button
                        onClick={handleGenerateFix}
                        disabled={isFixing}
                        className="h-11 rounded-[1.2rem] bg-[#0f6775] px-6 text-white hover:bg-[#0d5561]"
                      >
                        {isFixing ? (
                          <>
                            <LoaderCircle className="size-4 animate-spin" />
                            Generating
                          </>
                        ) : (
                          <>
                            <Bot className="size-4" />
                            Generate fix
                          </>
                        )}
                      </Button>
                      <div className="rounded-[1.35rem] border border-[#dfe7e1] bg-[#fbf7ef]/80 p-4">
                        <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[#708185]">
                          Quick picks from the audit
                        </p>
                        <div className="mt-3 flex flex-wrap gap-2">
                          {highlightedFindings.slice(0, 4).map((finding) => (
                            <button
                              key={`${finding.metric}-${finding.priority}`}
                              type="button"
                              onClick={() => setFixIssue(buildFixSeed(finding))}
                              className="rounded-full border border-[#dce6e2] bg-white px-3 py-2 text-left text-xs text-[#0e5d6f] transition-colors hover:border-[#0e5d6f]/30 hover:bg-[#f3fbfb]"
                            >
                              {finding.metric}
                            </button>
                          ))}
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="rounded-[1.9rem] border border-white/60 bg-[#102f3c] text-white shadow-[0_45px_140px_-74px_rgba(9,28,36,0.98)]">
                    <CardHeader>
                      <Badge className="w-fit border-white/15 bg-white/10 text-white">
                        Generated output
                      </Badge>
                      <CardTitle className="text-2xl text-[#f8f0e4]">
                        Before and after markup comes back here.
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      {fixResult ? (
                        <div className="space-y-5">
                          <div className="rounded-[1.4rem] border border-white/10 bg-white/8 p-4">
                            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-white/45">
                              Issue
                            </p>
                            <p className="mt-2 text-sm leading-6 text-white/80">{fixResult.issue}</p>
                          </div>
                          <div className="grid gap-4 xl:grid-cols-2">
                            <div className="rounded-[1.5rem] border border-white/10 bg-[#0d2230] p-4">
                              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-white/45">
                                Current code
                              </p>
                              <pre className="mt-3 overflow-x-auto whitespace-pre-wrap font-mono text-[13px] leading-6 text-[#f8f0e4]">
                                {fixResult.current_code}
                              </pre>
                            </div>
                            <div className="rounded-[1.5rem] border border-[#2e8f97]/25 bg-[#103744] p-4">
                              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[#8de0d6]">
                                Fixed code
                              </p>
                              <pre className="mt-3 overflow-x-auto whitespace-pre-wrap font-mono text-[13px] leading-6 text-[#effcf9]">
                                {fixResult.fixed_code}
                              </pre>
                            </div>
                          </div>
                          <div className="rounded-[1.4rem] border border-white/10 bg-white/8 p-4">
                            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-white/45">
                              Why this matters
                            </p>
                            <p className="mt-2 text-sm leading-6 text-white/78">
                              {fixResult.explanation}
                            </p>
                          </div>
                        </div>
                      ) : (
                        <div className="rounded-[1.5rem] border border-dashed border-white/15 bg-white/6 p-8 text-sm leading-7 text-white/72">
                          Generate a fix and the interface will show the current markup,
                          the revised markup, and the explanation from the backend in this
                          panel.
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </TabsContent>
              </Tabs>
            </section>
          </motion.div>
        ) : !isLoading ? (
          <EmptyCanvas />
        ) : null}
      </main>
    </div>
  );
}
