import { Component, type ErrorInfo, type ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('[ErrorBoundary]', error, info.componentStack);
  }

  private handleRetry = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="flex items-center justify-center min-h-[320px] p-8">
          <div className="widget max-w-md w-full text-center">
            <div className="mb-4 inline-flex items-center justify-center w-12 h-12 rounded-full bg-accent-red/10">
              <svg className="w-6 h-6 text-accent-red" viewBox="0 0 16 16" fill="currentColor">
                <path d="M8 0a8 8 0 110 16A8 8 0 018 0zm3.646 4.646a.5.5 0 00-.708 0L8 7.586l-2.938-2.94a.5.5 0 10-.708.708L7.292 8.29l-2.938 2.938a.5.5 0 00.708.708L8 8.998l2.938 2.938a.5.5 0 00.708-.708L8.708 8.29l2.938-2.938a.5.5 0 000-.708z" />
              </svg>
            </div>
            <h2 className="text-base font-semibold text-text-primary mb-1">
              Something went wrong
            </h2>
            <p className="text-sm text-text-muted mb-6 leading-relaxed max-w-xs mx-auto">
              An unexpected error occurred. Please try again or reload the page.
            </p>
            {this.state.error && (
              <details className="mb-4 text-left">
                <summary className="text-xs text-text-muted cursor-pointer hover:text-text-secondary transition-colors">
                  Error details
                </summary>
                <pre className="mt-2 p-3 rounded-lg bg-surface-200 text-xs text-accent-red font-mono overflow-auto max-h-32 border border-border">
                  {this.state.error.message}
                </pre>
              </details>
            )}
            <button
              onClick={this.handleRetry}
              className="px-5 py-2 rounded-lg text-sm font-medium bg-accent-cyan/10 text-accent-cyan
                         border border-accent-cyan/20 hover:bg-accent-cyan/20 transition-colors"
            >
              Try again
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
