import { Component, ErrorInfo, ReactNode } from 'react';
import GlassCard from './GlassCard';
import Button from './Button';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught React Error:', error, errorInfo);
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null });
    window.location.href = '/';
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh', padding: '2rem' }}>
          <GlassCard style={{ maxWidth: '500px', textAlign: 'center', padding: '2.5rem' }}>
            <h2 style={{ color: 'var(--danger)', marginBottom: '1rem' }}>Simulation View Error</h2>
            <p className="text-muted" style={{ marginBottom: '1.5rem', lineHeight: '1.6' }}>
              An unexpected error occurred while rendering the visualization components.
            </p>
            {this.state.error && (
              <div style={{ background: 'rgba(0,0,0,0.3)', padding: '0.75rem', borderRadius: '8px', marginBottom: '1.5rem', textAlign: 'left', fontSize: '0.85rem', fontFamily: 'monospace', color: 'var(--text-main)', overflowX: 'auto' }}>
                {this.state.error.message}
              </div>
            )}
            <Button onClick={this.handleReset} style={{ margin: '0 auto' }}>
              Reload Dashboard
            </Button>
          </GlassCard>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
