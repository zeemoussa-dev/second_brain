import { useParams } from 'react-router';
import { Cockpit } from '../features/cockpit/Cockpit';
import { CockpitBackLink } from '../features/cockpit/CockpitBackLink';

export function MeetingCockpitPage() {
  const { stem } = useParams<{ stem: string }>();
  if (!stem) return null;
  return (
    <>
      <CockpitBackLink />
      <Cockpit
        subjectKind="meeting"
        subjectNoteStem={stem}
        infoFields={[
          { label: 'Time', key: 'start' },
          { label: 'Location', key: 'location' },
          { label: 'Join', key: 'teams_link' },
          { label: 'Organizer', key: 'organizer' },
        ]}
      />
    </>
  );
}
