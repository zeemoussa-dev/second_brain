// One screen's failure stays one screen's failure (BUG-089).
//
// React unmounts the whole tree when a render throws and nothing catches it,
// so before this a single bad page took the sidebar with it and left no way to
// navigate away except editing the URL. The backend has given plugins this
// guarantee from the start -- "a plugin that fails is isolated", a `register`
// that raises disables that plugin and leaves every other one loaded -- and
// this is the frontend's half of the same promise.
//
// What it does NOT catch, because React boundaries cannot: errors thrown in
// event handlers, and rejected promises from a fetch. A screen whose data
// fails to load has to say so itself; see BUG-088 for the case that prompted
// this one.

import { Component, type ErrorInfo, type ReactNode } from 'react';

interface Props {
  children: ReactNode;
  /** What failed, named for the reader -- "This page", "Action Center". */
  label?: string;
}

interface State {
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    // The component stack is the only part that says WHICH screen broke, and
    // it is not in the Error itself, so it is logged rather than discarded.
    console.error('[ErrorBoundary] a screen failed to render', error, info.componentStack);
  }

  private retry = () => this.setState({ error: null });

  render() {
    const { error } = this.state;
    if (!error) return this.props.children;

    const label = this.props.label ?? 'This page';
    return (
      <section className="screen-error" role="alert">
        <h1 className="screen-error-title">{label} stopped working</h1>
        <p className="text-muted">
          The rest of the app is still running — use the sidebar to go somewhere else,
          or try this page again.
        </p>
        {/* The message is shown rather than hidden behind the console: this is
            a tool its own operator develops, and "something went wrong" would
            cost a round trip to find out what. */}
        <pre className="screen-error-detail">{error.message || String(error)}</pre>
        <button type="button" className="screen-error-retry" onClick={this.retry}>
          Try this page again
        </button>
      </section>
    );
  }
}
