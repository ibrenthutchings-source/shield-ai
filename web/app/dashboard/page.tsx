"use client";

import { useEffect, useState } from "react";

import { listAssets, listIncidents } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import type { Asset, Incident, Severity, TechniqueMapping } from "@/lib/types";
import { Badge, severityTone } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Kicker } from "@/components/ui/kicker";

const SEVERITY_WEIGHT: Record<Severity, number> = { low: 25, medium: 50, high: 75, critical: 100 };

function overallRiskScore(findings: TechniqueMapping[]): number {
  if (findings.length === 0) return 0;
  const total = findings.reduce((sum, f) => sum + SEVERITY_WEIGHT[f.severity], 0);
  return Math.round(total / findings.length);
}

export default function ExecutiveOverviewPage() {
  const { token } = useAuth();
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [assets, setAssets] = useState<Asset[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!token) return;
    Promise.all([listIncidents(token), listAssets(token)])
      .then(([incidentData, assetData]) => {
        setIncidents(incidentData);
        setAssets(assetData);
      })
      .finally(() => setIsLoading(false));
  }, [token]);

  const findings = assets.flatMap((a) => a.risk_findings ?? []);
  const riskScore = overallRiskScore(findings);
  const openIncidents = incidents.filter((i) => i.status !== "resolved").length;
  const criticalFindings = findings.filter((f) => f.severity === "critical").length;

  if (isLoading) {
    return <p className="text-sm text-slate-500 dark:text-slate-400">Loading risk overview…</p>;
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <Kicker>Difesa // Executive Overview</Kicker>
        <h1 className="text-xl font-semibold">Executive Risk Overview</h1>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          A business-level summary of your organization&apos;s security posture — no technical background required.
        </p>
      </div>

      <div className="flex gap-8 overflow-x-auto rounded-lg border border-slate-200 bg-white px-5 py-3 dark:border-slate-800 dark:bg-slate-900">
        <StatStripItem label="Overall risk score" value={`${riskScore} / 100`} tone={riskTone(riskScore)} />
        <StatStripItem label="Open incidents" value={String(openIncidents)} tone="neutral" />
        <StatStripItem label="Assets monitored" value={String(assets.length)} tone="neutral" />
        <StatStripItem label="Critical findings" value={String(criticalFindings)} tone={criticalFindings > 0 ? "critical" : "low"} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Top risk findings</CardTitle>
        </CardHeader>
        <CardContent>
          {findings.length === 0 ? (
            <p className="text-sm text-slate-500 dark:text-slate-400">No risk findings yet.</p>
          ) : (
            <ul className="flex flex-col gap-3">
              {findings
                .slice()
                .sort((a, b) => SEVERITY_WEIGHT[b.severity] - SEVERITY_WEIGHT[a.severity])
                .slice(0, 5)
                .map((finding, index) => (
                  <li key={index} className="flex items-start justify-between gap-4 text-sm">
                    <span className="text-slate-700 dark:text-slate-300">{finding.executive_summary}</span>
                    <Badge tone={severityTone(finding.severity)}>{finding.severity}</Badge>
                  </li>
                ))}
            </ul>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Recent incidents</CardTitle>
        </CardHeader>
        <CardContent>
          {incidents.length === 0 ? (
            <p className="text-sm text-slate-500 dark:text-slate-400">No incidents reported.</p>
          ) : (
            <ul className="flex flex-col gap-2">
              {incidents.slice(0, 5).map((incident) => (
                <li key={incident.id} className="flex items-center justify-between text-sm">
                  <span>{incident.incident_type}</span>
                  <Badge tone="neutral">{incident.status}</Badge>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

type StatTone = "neutral" | "low" | "critical";

const STAT_TONE_CLASSES: Record<StatTone, string> = {
  neutral: "text-slate-900 dark:text-slate-100",
  low: "text-emerald-600 dark:text-emerald-400",
  critical: "text-red-600 dark:text-red-400",
};

function riskTone(score: number): StatTone {
  if (score >= 75) return "critical";
  if (score === 0) return "low";
  return "neutral";
}

function StatStripItem({ label, value, tone }: { label: string; value: string; tone: StatTone }) {
  return (
    <div className="flex flex-shrink-0 flex-col gap-0.5">
      <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
        {label}
      </span>
      <span className={`text-lg font-bold ${STAT_TONE_CLASSES[tone]}`}>{value}</span>
    </div>
  );
}
