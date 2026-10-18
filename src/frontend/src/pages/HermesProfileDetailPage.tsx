import { useEffect, useState, type ReactNode } from 'react';
import { useParams } from 'react-router';
import { ApiError } from '../api/client';
import { Breadcrumbs } from '../components/Breadcrumbs';
import {
  fetchHermesProfileDetail,
  type HermesProfileConfigKey,
  type HermesProfileCronJob,
  type HermesProfileDetail,
  type HermesProfileSkillRow,
} from '../features/agents-map/agentsApiClient';

/**
 * What one Hermes profile really is on disk right now -- its soul verbatim,
 * every skill it carries with a verdict against the framework catalog, both
 * config layers unmerged, the cron jobs bound to it, and the toolsets it has
 * enabled (`REQ-SB-99-US-01`, `ADR-043`).
 *
 * Its own page rather than an eighth tab on the agent panel: strictly
 * read-only, deliberately expensive, and worth a URL that can be pasted into
 * an incident note. The panel gains only the way in; `ADR-042`'s breadcrumbs
 * give the way back.
 *
 * **The whole point of this screen is that it shows what is really there.**
 * Three failures are three different renderings, and none of them is an empty
 * panel: the install being unreadable hides every region rather than drawing
 * five empty ones, a region that could not be read shows the backend's own
 * message naming the file, and `.empty-state` appears only where a read
 * genuinely succeeded and found nothing. Rendering an unread region as an
 * empty one is the exact dishonesty `BUG-085`/`BUG-088` were about, and the
 * backend went to real trouble (`read` flag + `null` payload per region) to
 * keep the two apart -- flattening that here would throw it away.
 *
 * No merged or "effective" config value is shown anywhere, deliberately: a key
 * set in both files is reported as set in both, with both occurrences, because
 * Hermes' own precedence between them is not readable from this repository.
 *
 * Nothing on this page writes, and there is no edit, save, deploy or run
 * control anywhere on it.
 */

const SKILL_VERDICT_LABELS: Record<string, string> = {
  current: 'current',
  stale: 'stale',
  modified: 'modified',
  missing: 'missing',
  unknown_to_framework: 'unknown to the framework',
};

const SKILL_VERDICT_BADGE_VARIANTS: Record<string, string> = {
  current: 'badge-success',
  stale: 'badge-warning',
  modified: 'badge-danger',
  missing: 'badge-danger',
};

const CONFIG_SOURCE_LABELS: Record<string, string> = {
  profile: 'set here',
  install_root: 'inherited from the install root',
  not_set: 'not set',
  set_in_more_than_one_layer: 'set in more than one layer',
  unknown: 'unknown — a config layer could not be read',
};

const CONFIG_LAYER_LABELS: Record<string, string> = {
  profile: "This profile's own config.yaml",
  install_root: "The install root's config.yaml",
};

// A verdict/source/layer name this build has never heard of renders as itself.
// A debug view that silently drops an answer it does not recognise is worse
// than one that shows a raw string the operator can go and look up.
function labelled(labels: Record<string, string>, value: string): string {
  return labels[value] ?? value;
}

/** A config value exactly as the YAML parsed, with its type still visible --
 *  `""` and `(not set)` are different answers, and so are `"40"` and `40`. */
function formatConfigValue(value: unknown): string {
  return value === undefined ? 'undefined' : JSON.stringify(value);
}

/** One region that could not be read, in the backend's own words.
 *
 * Deliberately NOT `.empty-state`: that family means "this was read and holds
 * nothing", which is a different fact and the one this screen exists to stop
 * conflating with a failed read. */
function RegionCouldNotBeRead({ testId, message }: { testId: string; message: string }) {
  return (
    <div className="item-row" data-testid={testId}>
      <div className="item-row-main">
        <span className="item-row-title">
          <span className="badge badge-danger">Could not be read</span>
        </span>
        <span className="item-row-meta mono">{message}</span>
      </div>
    </div>
  );
}

function RegionWasReadAndIsEmpty({ children }: { children: ReactNode }) {
  return (
    <div className="empty-state">
      <p className="text-muted" style={{ margin: 0 }}>{children}</p>
    </div>
  );
}

function SkillRow({ skill }: { skill: HermesProfileSkillRow }) {
  return (
    <div className="item-row" data-testid="profile-skill-row">
      <div className="item-row-main">
        <span className="item-row-title">
          <span className="mono">{skill.skill_id}</span>{' '}
          <span
            className={`badge ${SKILL_VERDICT_BADGE_VARIANTS[skill.status] ?? ''}`.trim()}
            data-testid="profile-skill-verdict"
          >
            {labelled(SKILL_VERDICT_LABELS, skill.status)}
          </span>
        </span>
        <span className="item-row-meta">
          deployed version{' '}
          <span className="mono" data-testid="profile-skill-deployed-version">
            {skill.deployed_version ?? 'could not be read'}
          </span>
          {' — framework catalog '}
          <span className="mono">
            {skill.catalog_version ?? 'has no skill with this slug'}
          </span>
        </span>
      </div>
    </div>
  );
}

function ConfigKeyRow({ row }: { row: HermesProfileConfigKey }) {
  return (
    <div className="kv-row" data-testid="profile-config-row">
      <span className="kv-key mono">{row.key}</span>
      <span>
        {row.occurrences.length === 0 ? (
          <span className="badge">{labelled(CONFIG_SOURCE_LABELS, row.source)}</span>
        ) : (
          <>
            {row.occurrences.map((occurrence) => (
              <span
                key={occurrence.path}
                data-testid="profile-config-occurrence"
                style={{ display: 'block' }}
              >
                <span className="mono">{formatConfigValue(occurrence.value)}</span>{' '}
                <span className="badge">{labelled(CONFIG_SOURCE_LABELS, occurrence.source)}</span>{' '}
                <span className="text-muted mono">{occurrence.path}</span>
              </span>
            ))}
            {row.occurrences.length > 1 && (
              <span className="badge badge-warning">
                {labelled(CONFIG_SOURCE_LABELS, row.source)} — both are shown, neither is
                presented as the one in effect
              </span>
            )}
          </>
        )}
      </span>
    </div>
  );
}

function CronJobRow({ job, testId }: { job: HermesProfileCronJob; testId: string }) {
  return (
    <div className="item-row" data-testid={testId}>
      <div className="item-row-main">
        <span className="item-row-title">
          {job.name}{' '}
          <span className="badge" data-testid="profile-job-last-status">
            {job.last_status ?? 'no run recorded'}
          </span>
          {!job.enabled && <span className="badge"> disabled</span>}
        </span>
        <span className="item-row-meta">
          <span data-testid="profile-job-schedule">{job.schedule_display}</span>
          {' — last run '}
          {job.last_run_at ?? 'never'}
          {' — skill '}
          <span className="mono">{job.skill}</span>
          {job.last_error ? ` — ${job.last_error}` : ''}
        </span>
      </div>
    </div>
  );
}

export function HermesProfileDetailPage() {
  const { agentId } = useParams<{ agentId: string }>();
  const [detail, setDetail] = useState<HermesProfileDetail | null>(null);
  const [requestFailure, setRequestFailure] = useState<string | null>(null);

  useEffect(() => {
    if (!agentId) return;
    setDetail(null);
    setRequestFailure(null);
    fetchHermesProfileDetail(agentId)
      .then(setDetail)
      .catch((failure: unknown) => {
        setRequestFailure(
          failure instanceof ApiError
            ? `${failure.status} — ${failure.message}`
            : String(failure),
        );
      });
  }, [agentId]);

  const trail = [
    { label: 'Agents', to: '/' },
    { label: agentId ?? '', to: `/?agent=${agentId ?? ''}` },
    { label: 'Profile detail' },
  ];

  if (requestFailure !== null) {
    return (
      <>
        <Breadcrumbs items={trail} />
        <h1>Profile detail</h1>
        <div className="card">
          <RegionCouldNotBeRead testId="profile-request-error" message={requestFailure} />
        </div>
      </>
    );
  }

  if (detail === null) {
    return (
      <>
        <Breadcrumbs items={trail} />
        <h1>Profile detail</h1>
        <p className="text-muted">Reading this profile off the install...</p>
      </>
    );
  }

  // Not one region is drawn when the install itself could not be read -- five
  // empty panels would read as "this profile is empty", which is the opposite
  // of what happened (`US-01` Scenario 7).
  if (!detail.install.readable) {
    return (
      <>
        <Breadcrumbs items={trail} />
        <h1>Profile detail — {detail.profile_id}</h1>
        <div className="card">
          <div data-testid="profile-install-error">
            <p style={{ marginTop: 0, fontWeight: 600 }}>
              <span className="badge badge-danger">The Hermes install could not be read</span>
            </p>
            <p className="mono" data-testid="profile-install-error-message">
              {detail.install.error}
            </p>
            <p className="text-muted" style={{ marginBottom: 0 }}>
              Nothing below was read, so nothing is shown. Soul, skills, config, cron jobs
              and toolsets all come out of this install.
            </p>
          </div>
        </div>
      </>
    );
  }

  const { soul, skills, config, cron_jobs: cronJobs, toolsets } = detail;

  return (
    <>
      <Breadcrumbs items={trail} />
      <h1>Profile detail — {detail.profile_id}</h1>
      <p className="text-muted">
        What this Hermes profile is actually made of right now, read straight off{' '}
        <span className="mono">{detail.install.path}</span>. Read-only — opening or
        refreshing this page writes nothing.
      </p>

      <section className="card" data-testid="profile-soul-region" style={{ marginBottom: 'var(--space-4)' }}>
        <h2 style={{ marginTop: 0 }}>Soul</h2>
        <p className="text-muted mono" data-testid="profile-soul-path">
          {soul.path ?? 'no path reported'}
        </p>
        {soul.text === null ? (
          <RegionCouldNotBeRead
            testId="profile-soul-error"
            message={soul.error || `SOUL.md status: ${soul.status}`}
          />
        ) : soul.text === '' ? (
          <RegionWasReadAndIsEmpty>
            This SOUL.md was read successfully and is empty — it is not missing.
          </RegionWasReadAndIsEmpty>
        ) : (
          <pre
            className="mono"
            data-testid="profile-soul-text"
            style={{
              // `pre-wrap`, never a truncation: this block is the file, not an
              // excerpt of it (`US-01` Scenario 1). Whitespace and line breaks
              // are preserved exactly as served.
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word',
              fontSize: 'var(--font-size-sm)',
              background: 'var(--color-surface-muted)',
              padding: 'var(--space-3)',
              borderRadius: 'var(--radius-sm)',
              margin: 0,
            }}
          >
            {soul.text}
          </pre>
        )}
      </section>

      <section className="card" data-testid="profile-skills-region" style={{ marginBottom: 'var(--space-4)' }}>
        <h2 style={{ marginTop: 0 }}>Skills</h2>
        <p className="text-muted">
          Every skill really present in this profile's own skills/ tree, at the version it
          carries, verdicted against the framework catalog.
        </p>
        {skills.items === null ? (
          <RegionCouldNotBeRead testId="profile-skills-error" message={skills.error} />
        ) : skills.items.length === 0 ? (
          <RegionWasReadAndIsEmpty>
            This profile's skills/ tree was read successfully and holds no skills.
          </RegionWasReadAndIsEmpty>
        ) : (
          <div className="item-list">
            {skills.items.map((skill) => (
              <SkillRow key={skill.skill_id} skill={skill} />
            ))}
          </div>
        )}
      </section>

      <section className="card" data-testid="profile-config-region" style={{ marginBottom: 'var(--space-4)' }}>
        <h2 style={{ marginTop: 0 }}>Config</h2>
        {config.layers === null || config.keys === null ? (
          <RegionCouldNotBeRead testId="profile-config-error" message={config.error} />
        ) : (
          <>
            <p className="text-muted">
              Two files, shown as two layers exactly as written. No merged or effective
              value is produced anywhere on this page — Hermes' own precedence between
              these files is not readable from this repository, so a single answer would
              be a guess at which file won.
            </p>
            <div className="item-list">
              {config.layers.map((layer) => (
                <div className="item-row" data-testid="profile-config-layer" key={layer.path}>
                  <div className="item-row-main">
                    <span className="item-row-title">
                      {labelled(CONFIG_LAYER_LABELS, layer.source)}{' '}
                      {layer.values === null && (
                        <span className="badge badge-danger">Could not be read</span>
                      )}
                    </span>
                    <span className="item-row-meta mono">{layer.path}</span>
                    {layer.values === null ? (
                      <span className="item-row-meta mono" data-testid="profile-config-layer-error">
                        {layer.error || `status: ${layer.status}`}
                      </span>
                    ) : (
                      <span className="item-row-meta">
                        read — {Object.keys(layer.values).length} top-level keys set in this file
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
            <h3>Keys</h3>
            {/* A key found in only ONE readable layer is labelled as set there.
                If the other layer could not be read, that label is the whole
                truth about what was read and not the whole truth about the
                profile -- the unreadable file may set the key too. Saying so is
                cheaper than a caveat the operator has to infer from the layer
                block above. */}
            {config.layers.some((layer) => layer.values === null) && (
              <p className="text-muted" data-testid="profile-config-partial-read-warning">
                A layer above could not be read, so a key shown below as set in only one
                file may also be set in the layer that failed. Nothing here is inferred
                from a file that was not read.
              </p>
            )}
            {config.keys.length === 0 ? (
              <RegionWasReadAndIsEmpty>
                Both layers were read successfully and set nothing at all.
              </RegionWasReadAndIsEmpty>
            ) : (
              <div className="kv-list">
                {config.keys.map((row) => (
                  <ConfigKeyRow key={row.key} row={row} />
                ))}
              </div>
            )}
          </>
        )}

        <h3>Enabled toolsets</h3>
        {/* Outside the config conditional on purpose: the toolsets are their own
            region on the backend (a subprocess, not a file), so an unreadable
            config.yaml must not take them down with it, and vice versa. */}
        {toolsets.items === null ? (
          <RegionCouldNotBeRead
            testId="profile-toolsets-error"
            message={toolsets.error || 'the toolsets read failed and reported no reason'}
          />
        ) : Object.keys(toolsets.items).length === 0 ? (
          <RegionWasReadAndIsEmpty>
            The toolsets read succeeded and reported no toolsets at all for this profile.
          </RegionWasReadAndIsEmpty>
        ) : (
          <div className="kv-list">
            {Object.entries(toolsets.items).map(([toolsetName, isEnabled]) => (
              <div className="kv-row" data-testid="profile-toolset-row" key={toolsetName}>
                <span className="kv-key mono">{toolsetName}</span>
                <span>
                  <span className={`badge ${isEnabled ? 'badge-success' : ''}`.trim()}>
                    {isEnabled ? 'enabled' : 'disabled'}
                  </span>
                </span>
              </div>
            ))}
          </div>
        )}
      </section>

      <section className="card" data-testid="profile-jobs-region" style={{ marginBottom: 'var(--space-4)' }}>
        <h2 style={{ marginTop: 0 }}>Cron jobs</h2>
        {cronJobs.items === null ? (
          <RegionCouldNotBeRead testId="profile-jobs-error" message={cronJobs.error} />
        ) : (
          <>
            <h3 style={{ marginTop: 0 }}>Bound to this profile</h3>
            <p className="text-muted">
              A job is bound to the profile whose own cron/ directory holds it — the
              binding is a directory, not a field on the job.
            </p>
            {cronJobs.items.length === 0 ? (
              <RegionWasReadAndIsEmpty>
                This profile's own cron/ directory was read successfully and holds no jobs.
              </RegionWasReadAndIsEmpty>
            ) : (
              <div className="item-list">
                {cronJobs.items.map((job) => (
                  <CronJobRow key={job.id} job={job} testId="profile-job-row" />
                ))}
              </div>
            )}

            <h3>Install-level — the jobs that run with no profile flag</h3>
            {cronJobs.install_level_is_this_profile ? (
              <p className="text-muted" data-testid="profile-install-jobs-are-this-profile">
                This profile IS the install root, so the jobs above are the install-level
                jobs. They are not listed a second time here.
              </p>
            ) : cronJobs.install_level === null ? (
              <RegionCouldNotBeRead
                testId="profile-install-jobs-error"
                message={cronJobs.error || 'the install-level cron jobs could not be read'}
              />
            ) : cronJobs.install_level.length === 0 ? (
              <RegionWasReadAndIsEmpty>
                The install root's own cron/ directory was read successfully and holds no
                jobs.
              </RegionWasReadAndIsEmpty>
            ) : (
              <div className="item-list">
                {cronJobs.install_level.map((job) => (
                  <CronJobRow key={job.id} job={job} testId="profile-install-job-row" />
                ))}
              </div>
            )}
          </>
        )}
      </section>
    </>
  );
}
