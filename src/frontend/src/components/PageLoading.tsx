/** Shared, generic "this page's own data is still loading" panel --
 * reuses BootGate's exact visual language (styles/boot.css) so a refresh
 * reads as one continuous loading experience (backend boot, then this
 * page's own fetch) rather than a boot screen that vanishes into a blank
 * canvas while the real data is still in flight (operator: "when I
 * refresh it normally takes time for the data to load, We need to have
 * the bootGate to tell me data is loading"). Deliberately NOT
 * position:fixed/full-viewport like BootGate itself -- this renders
 * INSIDE an already-visible app shell (sidebar/topbar stay put), filling
 * whatever content area the caller places it in. */
export function PageLoading({ title }: { title: string }) {
  return (
    <div className="page-loading">
      <span className="material-symbols-outlined boot-spin page-loading-spinner">progress_activity</span>
      <p className="page-loading-title">{title}</p>
    </div>
  );
}
