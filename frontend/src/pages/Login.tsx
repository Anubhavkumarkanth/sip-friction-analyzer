import { FC, FormEvent, useState } from 'react';
import { TrendingUp } from 'lucide-react';
import GlassCard from '../components/ui/GlassCard';
import Input from '../components/ui/Input';
import Button from '../components/ui/Button';
import { authAPI, handleApiError } from '../services/api';

interface LoginProps {
  onSuccess: () => void;
}

/**
 * Sign-in screen.
 *
 * Simulations are saved per user, so the app needs to know who is running one.
 * The JWT utilities already existed in the backend but nothing ever called
 * them; this is the screen that does.
 */
const Login: FC<LoginProps> = ({ onSuccess }) => {
  const [username, setUsername] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  const handleSubmit = async (e: FormEvent): Promise<void> => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await authAPI.login(username, password);
      onSuccess();
    } catch (err) {
      setError(handleApiError(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '1.5rem',
      }}
    >
      <GlassCard hoverEffect={false} style={{ width: '100%', maxWidth: '380px' }}>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.6rem',
            marginBottom: '1.25rem',
          }}
        >
          <TrendingUp size={28} className="text-accent" />
          <h2 style={{ margin: 0 }}>SIP Friction Analyzer</h2>
        </div>

        <p style={{ marginTop: 0, marginBottom: '1.25rem', fontSize: '0.85rem', opacity: 0.75 }}>
          Sign in to run a simulation and keep a history of your past runs.
        </p>

        <form onSubmit={handleSubmit}>
          <Input
            label="Username"
            id="username"
            type="text"
            autoComplete="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
          <Input
            label="Password"
            id="password"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />

          {error && (
            <p
              role="alert"
              style={{ color: 'var(--danger)', fontSize: '0.85rem', marginBottom: '0.75rem' }}
            >
              {error}
            </p>
          )}

          <Button
            type="submit"
            disabled={loading || !username || !password}
            loading={loading}
            style={{ width: '100%', marginTop: '0.5rem' }}
          >
            Sign in
          </Button>
        </form>
      </GlassCard>
    </div>
  );
};

export default Login;
