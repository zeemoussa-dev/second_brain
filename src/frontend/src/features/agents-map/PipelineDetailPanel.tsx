import { useEffect, useState } from 'react';
import { fetchPipelineDetail, type PipelineDetail } from './pipelinesApiClient';
import { fetchSections, type SectionSummary } from '../settings/settingsApiClient';
import { JobSettingsPanel } from './JobSettingsPanel';

interface PipelineDetailPanelProps {
  pipelineId: string;
  onClose: () => void;
  // 2026-08-30 (operator: "when I hover in the panel it puts the agent
  // i am hovering on in the focus... it would follow the path from the
  // previous agent i hovered on to the new one") -- reports which real
  // Step id (if any) is currently hovered in the Steps list below, so
  // AgentsMapPage can drive SectionDrilldown's own existing click-to-
  // focus camera (zoom+pan+ring) from a hover here instead of a click
  // there. Optional so this panel stays usable standalone/in tests with
  // no wiring.
  onHoverStep?: (stepId: string | null) => void;
}

// 2026-08-30 (operator: "Currently we don't have any Access to the
// pipeline... Now we will have an option for having a pipeline Context
// Menu same as agents") -- the Pipeline-level counterpart to
// AgentDetailPanel/SectionDetailPanel, opened by clicking the new
// floating pipeline-title map label (AgentsMapCanvas.tsx). Deliberately
// small and read-only-plus-steps, matching JobSettingsPanel's own
// "genuinely separate, minimal shell" precedent (ADR-044 Decision 3)
// rather than widening AgentDetailPanel's shared tab machinery for an
// entity with no tools/scope/chat of its own. A Step row opens
// JobSettingsPanel itself (self-contained nested state here, not
// threaded back up to AgentsMapPage) -- same real
// GET/PATCH /agents/{pipeline_id}/jobs/{job_id}/settings path a Step
// node's own direct map click already uses.
export function PipelineDetailPanel({ pipelineId, onClose, onHoverStep }: PipelineDetailPanelProps) {
  const [pipeline, setPipeline] = useState<PipelineDetail | null>(null);
  const [sections, setSections] = useState<SectionSummary[] | null>(null);
  const [selectedStepId, setSelectedStepId] = useState<string | null>(null);

  useEffect(() => {
    setPipeline(null);
    setSelectedStepId(null);
    fetchPipelineDetail(pipelineId).then(setPipeline);
  }, [pipelineId]);

  useEffect(() => {
    fetchSections().then(setSections);
  }, []);

  const sectionName = pipeline
    ? sections?.find((section) => section.id === pipeline.section_id)?.name ?? pipeline.section_id
    : null;

  return (
    <>
      <div className="side-panel-overlay" onClick={onClose} />
      <aside className="side-panel" aria-label="Pipeline details">
        <div className="side-panel-header">
          <span className="badge">Pipeline detail</span>
          <button type="button" className="side-panel-close" aria-label="Close panel" onClick={onClose}>
            &times;
          </button>
        </div>
        {!pipeline && (
          <div className="side-panel-body">
            <div className="side-panel-loading" data-testid="pipeline-detail-loading">
              <span className="side-panel-loading-spinner" aria-hidden="true" />
              Loading pipeline…
            </div>
          </div>
        )}
        {pipeline && (
          <>
            <div className="side-panel-title">
              <h2>{pipeline.name} <span className="badge">pipeline</span></h2>
            </div>
            <div className="side-panel-body">
              <div className="side-panel-section" data-testid="pipeline-overview">
                <h3>Overview</h3>
                <div className="kv-list">
                  <div className="kv-row">
                    <span className="kv-key">Description</span>
                    <span>{pipeline.description || 'No description set'}</span>
                  </div>
                  <div className="kv-row">
                    <span className="kv-key">Section</span>
                    <span>{sectionName ?? pipeline.section_id}</span>
                  </div>
                  <div className="kv-row">
                    <span className="kv-key">Schedule</span>
                    <span>{pipeline.cron_schedule || 'No real cron schedule'}</span>
                  </div>
                  <div className="kv-row">
                    <span className="kv-key">Cron status</span>
                    <span>
                      {pipeline.cron_job_id
                        ? pipeline.cron_enabled
                          ? 'Enabled'
                          : 'Disabled'
                        : 'No real cron job wired'}
                    </span>
                  </div>
                  <div className="kv-row">
                    <span className="kv-key">Last run</span>
                    <span>{pipeline.cron_last_run_at || 'Never run yet'}</span>
                  </div>
                  <div className="kv-row">
                    <span className="kv-key">Next run</span>
                    <span>{pipeline.cron_next_run_at || 'Not scheduled'}</span>
                  </div>
                  {pipeline.cron_last_status && (
                    <div className="kv-row">
                      <span className="kv-key">Last status</span>
                      <span>{pipeline.cron_last_status}</span>
                    </div>
                  )}
                </div>
              </div>
              <div className="side-panel-section" data-testid="pipeline-steps">
                <h3>Steps ({pipeline.steps.length})</h3>
                <div className="item-list">
                  {pipeline.steps.map((step) => (
                    <button
                      type="button"
                      key={step.id}
                      className="item-row"
                      // .item-row is a plain <div> everywhere else it's used
                      // (settings.css has no button-reset rules for it) --
                      // resetting native button chrome inline here rather
                      // than widening that shared class for this one caller.
                      style={{
                        width: '100%', border: 'none', textAlign: 'left',
                        font: 'inherit', color: 'inherit', cursor: 'pointer',
                      }}
                      data-testid={`pipeline-step-${step.id}`}
                      onClick={() => setSelectedStepId(step.id)}
                      onMouseEnter={() => onHoverStep?.(step.id)}
                      onMouseLeave={() => onHoverStep?.(null)}
                    >
                      <span className="item-row-main">
                        <span className="item-row-title">{step.name}</span>
                        <span className="item-row-meta">{step.description}</span>
                      </span>
                      <span className="badge">{step.type}</span>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </>
        )}
      </aside>
      {selectedStepId && (
        <JobSettingsPanel
          agentId={pipelineId}
          jobId={selectedStepId}
          onClose={() => setSelectedStepId(null)}
        />
      )}
    </>
  );
}
