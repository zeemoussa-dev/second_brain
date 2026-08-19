import { useState } from 'react';
import { useParams, Link } from 'react-router';
import { Cockpit } from '../features/cockpit/Cockpit';
import { AttachmentsPanel } from '../features/cockpit/AttachmentsPanel';

export function InboxCockpitPage() {
  const { stem } = useParams<{ stem: string }>();
  const [refreshKey, setRefreshKey] = useState(0);
  if (!stem) return null;
  return (
    <>
      <p className="text-muted"><Link className="text-muted" to="/my-day/emails">&larr; Emails</Link></p>
      <Cockpit
        key={refreshKey}
        subjectKind="email"
        subjectNoteStem={stem}
        subjectTitleFields={[{ label: 'Received', key: 'received' }, { label: 'Customer', key: 'customer' }]}
        attachmentsSlot={<AttachmentsPanel stem={stem} onHandOff={() => setRefreshKey((k) => k + 1)} />}
        enableDraftCopyAffordance
      />
    </>
  );
}
