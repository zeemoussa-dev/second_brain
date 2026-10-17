import { ActionExplorer } from './Explorer';
import { type ActionCenterSummary } from './client';

/** Completed actions, each with the evidence that closed it. The evidence is
 *  the point: "done" with nothing behind it is a guess, and this screen is
 *  where a wrong judgment becomes visible.
 *
 *  It searches, filters and groups exactly like the open list (operator,
 *  2026-09-25) -- by owner, by customer, by source, or by when it closed. What
 *  was done is a record worth asking questions of, and a flat list of the most
 *  recent hundred answers none of them.
 */
export function CompletedPanel({ summary, onChanged }: {
  summary: ActionCenterSummary | null;
  onChanged: () => void;
}) {
  return (
    <>
      <p className="text-muted">
        What was closed, and what showed it. A wrong judgment is visible here rather
        than hidden behind a tick.
      </p>
      <ActionExplorer status="Completed" summary={summary} onChanged={onChanged} />
    </>
  );
}
