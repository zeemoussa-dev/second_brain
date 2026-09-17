import { useParams } from 'react-router';
import { Cockpit } from '../features/cockpit/Cockpit';
import { CockpitBackLink } from '../features/cockpit/CockpitBackLink';

export function InboxCockpitPage() {
  const { stem } = useParams<{ stem: string }>();
  if (!stem) return null;
  return (
    <>
      <CockpitBackLink />
      <Cockpit
        subjectKind="email"
        subjectNoteStem={stem}
        // 'last_message_at', never 'received' -- a real Thread's own
        // frontmatter has no 'received' field at all (found live
        // 2026-08-27, operator: "Fix the People/Received field gap on
        // Threads"). Plugins add their own rows (the Entities plugin adds
        // Customer).
        infoFields={[{ label: 'Received', key: 'last_message_at' }]}
      />
    </>
  );
}
