"use client";

import { Fragment, useEffect, useState, type FormEvent } from "react";

import { ApiError, createAsset, listAssets } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import type { Asset, Severity } from "@/lib/types";
import { Badge, severityTone } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Kicker } from "@/components/ui/kicker";
import { Label } from "@/components/ui/label";

const SEVERITY_RANK: Record<Severity, number> = { critical: 3, high: 2, medium: 1, low: 0 };

function highestSeverity(asset: Asset): Severity | null {
  const findings = asset.risk_findings ?? [];
  if (findings.length === 0) return null;
  return findings.reduce<Severity>(
    (worst, f) => (SEVERITY_RANK[f.severity] > SEVERITY_RANK[worst] ? f.severity : worst),
    findings[0].severity
  );
}

export default function AssetsPage() {
  const { token } = useAuth();
  const [assets, setAssets] = useState<Asset[]>([]);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [host, setHost] = useState("");
  const [port, setPort] = useState("");
  const [service, setService] = useState("");
  const [tlsValid, setTlsValid] = useState(true);
  const [oauthExcessive, setOauthExcessive] = useState(false);

  useEffect(() => {
    if (!token) return;
    listAssets(token).then(setAssets);
  }, [token]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!token) return;
    setError(null);
    setIsSubmitting(true);
    try {
      const asset = await createAsset(token, {
        host,
        port: port ? Number(port) : undefined,
        service: service || undefined,
        tls_valid: tlsValid,
        oauth_scope_excessive: oauthExcessive,
      });
      setAssets((prev) => [asset, ...prev]);
      setHost("");
      setPort("");
      setService("");
      setTlsValid(true);
      setOauthExcessive(false);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to assess the asset.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <Kicker>Difesa // Asset Surface Map</Kicker>
        <h1 className="text-xl font-semibold">Asset Surface Map</h1>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          Passively observed assets mapped against MITRE ATT&amp;CK — no active exploits are run.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Add discovered asset</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-5">
            <div>
              <Label htmlFor="host">Host</Label>
              <Input id="host" value={host} onChange={(e) => setHost(e.target.value)} required placeholder="rdp.school.org" />
            </div>
            <div>
              <Label htmlFor="port">Port</Label>
              <Input id="port" type="number" value={port} onChange={(e) => setPort(e.target.value)} placeholder="3389" />
            </div>
            <div>
              <Label htmlFor="service">Service</Label>
              <Input id="service" value={service} onChange={(e) => setService(e.target.value)} placeholder="rdp" />
            </div>
            <label className="flex items-center gap-2 self-end pb-2 text-sm">
              <input type="checkbox" checked={tlsValid} onChange={(e) => setTlsValid(e.target.checked)} />
              TLS valid
            </label>
            <label className="flex items-center gap-2 self-end pb-2 text-sm">
              <input
                type="checkbox"
                checked={oauthExcessive}
                onChange={(e) => setOauthExcessive(e.target.checked)}
              />
              Excessive OAuth scope
            </label>
            <div className="sm:col-span-2 lg:col-span-5">
              {error && <p className="mb-2 text-xs text-red-600 dark:text-red-400">{error}</p>}
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? "Assessing…" : "Assess asset"}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Discovered assets</CardTitle>
        </CardHeader>
        <CardContent>
          {assets.length === 0 ? (
            <p className="text-sm text-slate-500 dark:text-slate-400">No assets recorded yet.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-slate-200 text-xs text-slate-500 dark:border-slate-800 dark:text-slate-400">
                    <th className="py-2 pr-4">Host</th>
                    <th className="py-2 pr-4">Port</th>
                    <th className="py-2 pr-4">Service</th>
                    <th className="py-2 pr-4">Findings</th>
                    <th className="py-2 pr-4">Highest severity</th>
                  </tr>
                </thead>
                <tbody>
                  {assets.map((asset) => {
                    const severity = highestSeverity(asset);
                    const isExpanded = expandedId === asset.id;
                    return (
                      <Fragment key={asset.id}>
                        <tr
                          onClick={() => setExpandedId(isExpanded ? null : asset.id)}
                          className="cursor-pointer border-b border-slate-100 hover:bg-slate-50 dark:border-slate-900 dark:hover:bg-slate-900"
                        >
                          <td className="py-2 pr-4">{asset.host}</td>
                          <td className="py-2 pr-4">{asset.port ?? "—"}</td>
                          <td className="py-2 pr-4">{asset.service ?? "—"}</td>
                          <td className="py-2 pr-4">{asset.risk_findings?.length ?? 0}</td>
                          <td className="py-2 pr-4">
                            {severity ? <Badge tone={severityTone(severity)}>{severity}</Badge> : <Badge>none</Badge>}
                          </td>
                        </tr>
                        {isExpanded && asset.risk_findings && asset.risk_findings.length > 0 && (
                          <tr>
                            <td colSpan={5} className="bg-slate-50 p-4 dark:bg-slate-900">
                              <ul className="flex flex-col gap-3">
                                {asset.risk_findings.map((finding, i) => (
                                  <li key={i} className="text-sm">
                                    <div className="flex items-center gap-2">
                                      <Badge tone={severityTone(finding.severity)}>{finding.severity}</Badge>
                                      <span className="font-medium">
                                        {finding.technique_id} — {finding.technique_name}
                                      </span>
                                      <span className="text-xs text-slate-500 dark:text-slate-400">
                                        {finding.tactic}
                                      </span>
                                    </div>
                                    <p className="mt-1 text-slate-700 dark:text-slate-300">
                                      {finding.executive_summary}
                                    </p>
                                    <ul className="mt-1 list-inside list-disc text-xs text-slate-600 dark:text-slate-400">
                                      {finding.technical_remediation.map((step, j) => (
                                        <li key={j}>{step}</li>
                                      ))}
                                    </ul>
                                  </li>
                                ))}
                              </ul>
                            </td>
                          </tr>
                        )}
                      </Fragment>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
