import { useEffect, useState } from 'react';
import { fetchCockpitAttachments, handOffAttachment, type CockpitAttachment } from './cockpitApiClient';

export function AttachmentsPanel({ stem, onHandOff }: { stem: string; onHandOff: () => void }) {
  const [attachments, setAttachments] = useState<CockpitAttachment[] | null>(null);
  useEffect(() => { fetchCockpitAttachments(stem).then(setAttachments); }, [stem]);

  if (!attachments || attachments.length === 0) return null; // Scenario 4b -- nothing rendered, no affordance implies one exists

  return (
    <>
      <h3 style={{ marginTop: 'var(--space-6)' }}>Attachments</h3>
      <div className="item-list">
        {attachments.map((attachment) => (
          <div className="item-row" key={attachment.filename}>
            <div className="item-row-main">
              <span className="item-row-title">{attachment.filename}</span>
              <span className="item-row-meta">{Math.round(attachment.size / 1024)} KB</span>
            </div>
            <div className="item-row-actions">
              <button type="button" className="btn" onClick={() => handOffAttachment(stem, attachment.filename).then(onHandOff)}>
                Hand off to Expert
              </button>
            </div>
          </div>
        ))}
      </div>
    </>
  );
}
