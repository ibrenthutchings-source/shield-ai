export interface Token {
  access_token: string;
  token_type: string;
}

export type IncidentPhaseName = "emergency_triage" | "forensics" | "recovery";

export interface PlaybookPhase {
  phase: IncidentPhaseName;
  executive_summary: string;
  technical_steps: string[];
  commands: string[];
}

export interface IncidentPlaybook {
  incident_type: string;
  phases: PlaybookPhase[];
}

export interface Incident {
  id: string;
  incident_type: string;
  environment: string;
  description: string;
  status: string;
  playbook: IncidentPlaybook | null;
  created_at: string;
}

export interface IncidentCreateInput {
  incident_type: string;
  affected_systems: string[];
  environment: string;
  description: string;
}

export type Severity = "low" | "medium" | "high" | "critical";

export interface DiscoveredAssetInput {
  host: string;
  port?: number;
  service?: string;
  tls_valid?: boolean;
  oauth_scope_excessive?: boolean;
}

export interface TechniqueMapping {
  asset: DiscoveredAssetInput;
  technique_id: string;
  technique_name: string;
  tactic: string;
  severity: Severity;
  executive_summary: string;
  technical_remediation: string[];
}

export interface Asset {
  id: string;
  host: string;
  port: number | null;
  service: string | null;
  tls_valid: boolean | null;
  oauth_scope_excessive: boolean;
  risk_findings: TechniqueMapping[] | null;
  created_at: string;
}

export interface AgentStreamMessage {
  agent: string;
  status: string;
  [key: string]: unknown;
}
