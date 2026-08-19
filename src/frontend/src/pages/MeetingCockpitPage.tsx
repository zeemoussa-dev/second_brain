import { useParams, Link } from 'react-router';
import { Cockpit } from '../features/cockpit/Cockpit';

export function MeetingCockpitPage() {
  const { stem } = useParams<{ stem: string }>();
  if (!stem) return null;
  return (
    <>
      <p className="text-muted"><Link className="text-muted" to="/my-day/calendar">&larr; Calendar</Link></p>
      <Cockpit
        subjectKind="meeting"
        subjectNoteStem={stem}
        subjectTitleFields={[{ label: 'Time', key: 'start' }, { label: 'Customer', key: 'customer' }]}
      />
    </>
  );
}
