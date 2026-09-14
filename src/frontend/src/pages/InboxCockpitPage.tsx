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
        // Threads"); 'customer' is now resolved server-side from the
        // real customer/<slug> tag when the raw frontmatter has none
        // (a subject enricher, see cockpit_view.py::_enriched_subject).
        infoFields={[{ label: 'Received', key: 'last_message_at' }, { label: 'Customer', key: 'customer' }]}
      />
    </>
  );
}
