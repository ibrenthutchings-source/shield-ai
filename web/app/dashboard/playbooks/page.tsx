"use client";

import { useEffect, useState, type FormEvent } from "react";

import { ApiError, createIncident, listIncidents } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import type { Incident, PlaybookPhase } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

const PHASE_LABELS: Record<PlaybookPhase["phase"], string> = {
  emergency_triage: "Emergency Triage",
  forensics: "Forensics",
  recovery: "Recovery",
};

export default function PlaybooksPage() {
  const { token } = useAuth();
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [view, setView] = useState<"executive" | "technical">("executive");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [incidentType, setIncidentType] = useState("");
  const [affectedSystems, setAffectedSystems] = useState("");
  const [environment, setEnvironment] = useState("Google Workspace");
  const [description, setDescription] = useState("");

  function refresh() {
    if (!token) return;
    listIncidents(token).then((data) => {
      setIncidents(data);
      if (!selectedId && data.length > 0) setSelectedId(data[0].id);
    });
  }

  useEffect(refresh, [token]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!token) return;
    setError(null);
    setIsSubmitting(true);
    try {
      const incident = await createIncident(token, {
        incident_type: incidentType,
        affected_systems: affectedSystems
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean),
        environment,
        description,
      });
      setIncidents((prev) => [incident, ...prev]);
      setSelectedId(incident.id);
      setIncidentType("");
      setAffectedSystems("");
      setDescription("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to generate the playbook.");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function copyCommand(command: string) {
    try {
      await navigator.clipboard.writeText(command);
    } catch {
      // Clipboard access may be unavailable; the command remains selectable text.
    }
  }

  const selectedIncident = incidents.find((i) => i.id === selectedId) ?? null;

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-[320px_1fr]">
      <div className="flex flex-col gap-4">
        <Card>
          <CardHeader>
            <CardTitle>New incident</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="flex flex-col gap-3">
              <div>
                <Label htmlFor="incident_type">Incident type</Label>
                <Input
                  id="incident_type"
                  value={incidentType}
                  onChange={(e) => setIncidentType(e.target.value)}
                  required
                  placeholder="Ransomware"
                />
              </div>
              <div>
                <Label htmlFor="affected_systems">Affected systems (comma separated)</Label>
                <Input
                  id="affected_systems"
                  value={affectedSystems}
                  onChange={(e) => setAffectedSystems(e.target.value)}
                  placeholder="fileserver01, student-portal"
                />
              </div>
              <div>
                <Label htmlFor="environment">Environment</Label>
                <select
                  id="environment"
                  value={environment}
                  onChange={(e) => setEnvironment(e.target.value)}
                  className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-950"
                >
                  <option>Google Workspace</option>
                  <option>Microsoft 365</option>
                  <option>Azure</option>
                </select>
              </div>
              <div>
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={3}
                  placeholder="What happened, when it was noticed, what's affected."
                />
              </div>
              {error && <p className="text-xs text-red-600 dark:text-red-400">{error}</p>}
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? "Generating playbook…" : "Generate playbook"}
              </Button>
            </form>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Incidents</CardTitle>
          </CardHeader>
          <CardContent>
            {incidents.length === 0 ? (
              <p className="text-sm text-slate-500 dark:text-slate-400">None yet.</p>
            ) : (
              <ul className="flex flex-col gap-1">
                {incidents.map((incident) => (
                  <li key={incident.id}>
                    <button
                      onClick={() => setSelectedId(incident.id)}
                      className={`w-full rounded-md px-2 py-1.5 text-left text-sm ${
                        incident.id === selectedId
                          ? "bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900"
                          : "hover:bg-slate-100 dark:hover:bg-slate-800"
                      }`}
                    >
                      {incident.incident_type}
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>

      <div>
        {!selectedIncident ? (
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Select or generate an incident to view its containment playbook.
          </p>
        ) : (
          <div className="flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">{selectedIncident.incident_type}</h2>
              <div className="flex gap-1 rounded-md border border-slate-300 p-0.5 dark:border-slate-700">
                <button
                  onClick={() => setView("executive")}
                  className={`rounded px-3 py-1 text-xs font-medium ${
                    view === "executive" ? "bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900" : ""
                  }`}
                >
                  Executive Summary
                </button>
                <button
                  onClick={() => setView("technical")}
                  className={`rounded px-3 py-1 text-xs font-medium ${
                    view === "technical" ? "bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900" : ""
                  }`}
                >
                  Technical Remediation
                </button>
              </div>
            </div>

            {!selectedIncident.playbook ? (
              <p className="text-sm text-slate-500 dark:text-slate-400">Playbook still generating…</p>
            ) : (
              selectedIncident.playbook.phases.map((phase) => (
                <Card key={phase.phase}>
                  <CardHeader className="flex flex-row items-center justify-between">
                    <CardTitle>{PHASE_LABELS[phase.phase]}</CardTitle>
                    <Badge tone="neutral">{phase.phase.replace("_", " ")}</Badge>
                  </CardHeader>
                  <CardContent>
                    {view === "executive" ? (
                      <p className="text-sm text-slate-700 dark:text-slate-300">{phase.executive_summary}</p>
                    ) : (
                      <div className="flex flex-col gap-3">
                        <ul className="list-inside list-disc text-sm text-slate-700 dark:text-slate-300">
                          {phase.technical_steps.map((step, i) => (
                            <li key={i}>{step}</li>
                          ))}
                        </ul>
                        {phase.commands.length > 0 && (
                          <div className="flex flex-col gap-2">
                            {phase.commands.map((command, i) => (
                              <div
                                key={i}
                                className="flex items-center justify-between gap-2 rounded-md bg-slate-900 px-3 py-2 font-mono text-xs text-slate-100"
                              >
                                <code className="overflow-x-auto whitespace-pre">{command}</code>
                                <button
                                  onClick={() => copyCommand(command)}
                                  className="shrink-0 text-slate-400 hover:text-white"
                                >
                                  Copy
                                </button>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
}
