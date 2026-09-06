import { apiFetch } from '../../api/client';

// Blueprints (Settings > Blueprints) -- a thin client over GET /blueprints,
// GET /blueprints/{id}/preflight and POST /blueprints/{id}/install, same
// apiFetch helper every other settings client uses.
//
// preflight and install are deliberately separate calls: preflight creates
// NOTHING, so the card can show exactly what would happen -- and what would
// stop it -- before the operator commits.

export interface BlueprintAgent {
  id: string;
  name: string;
  type: string;
  skill_ids: string[];
  icon: string | null;
  peer: boolean;
}

export interface Blueprint {
  id: string;
  name: string;
  description: string;
  version: number;
  suggested_section_name: string;
  suggested_section_icon: string | null;
  suggested_section_color: string | null;
  agents: BlueprintAgent[];
  // Set only when the Blueprint itself failed to parse. Such a Blueprint is
  // still listed, carrying this, rather than silently dropped.
  error: string | null;
}

export interface BlueprintPreflight {
  blueprint_id: string;
  ok: boolean;
  problems: string[];
  skills: string[];
  templates: string[];
  // Skills with no `writes:` declaration: the Template check could not cover
  // them. Not a failure, but the check is partial and the card says so.
  unchecked_skills: string[];
  peers: string[];
  section_id: string;
  // The Blueprint SUGGESTS a Section; the operator chooses. available_sections
  // is what this install already has, so the picker offers real options rather
  // than forcing a new Section on a machine that has five.
  suggested_section: string;
  available_sections: { id: string; name: string }[];
  already: { section: boolean; agents: string[] };
}

export interface BlueprintInstallResult {
  installed: boolean;
  section_id: string;
  agents: Record<string, string>;
  skills: Record<string, Record<string, string>>;
  peers: Record<string, string>;
  templates: string[];
  problems: string[];
  rolled_back?: Record<string, string>;
  // A running Hermes session is given its prompt once and never re-reads it,
  // so Primary cannot see peers wired mid-conversation.
  primary_session_reset_required?: boolean;
}

export function fetchBlueprints(): Promise<Blueprint[]> {
  return apiFetch('/blueprints');
}

export function preflightBlueprint(id: string, sectionId?: string): Promise<BlueprintPreflight> {
  const query = sectionId ? `?section_id=${encodeURIComponent(sectionId)}` : '';
  return apiFetch(`/blueprints/${encodeURIComponent(id)}/preflight${query}`);
}

export function installBlueprint(
  id: string, sectionId?: string, wirePeers = true,
): Promise<BlueprintInstallResult> {
  const section = sectionId ? `&section_id=${encodeURIComponent(sectionId)}` : '';
  return apiFetch(`/blueprints/${encodeURIComponent(id)}/install?wire_peers=${wirePeers}${section}`, {
    method: 'POST',
  });
}
