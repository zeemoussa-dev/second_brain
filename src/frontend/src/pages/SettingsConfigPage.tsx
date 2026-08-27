import { Link } from 'react-router';

export function SettingsConfigPage() {
  return (
    <>
      <p className="text-muted"><Link className="text-muted" to="/settings">&larr; Settings</Link></p>
      <h1>Config</h1>
      <div className="card">
        <p className="text-muted">Not built yet.</p>
      </div>
    </>
  );
}
