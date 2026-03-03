import { type FormEvent, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useRegister } from '@/hooks/use-api';
import { useAuthStore } from '@/stores/auth-store';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { AxiosError } from 'axios';
import toast from 'react-hot-toast';

export default function RegisterPage() {
  const [fullName, setFullName] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const register = useRegister();
  const { setTokens, setUser } = useAuthStore();
  const navigate = useNavigate();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    try {
      const data = await register.mutateAsync({
        email,
        password,
        full_name: fullName,
        company_name: companyName,
      });
      setTokens(data.access_token, data.refresh_token);
      if (data.user) setUser(data.user);
      navigate('/');
    } catch (err: unknown) {
      const message = err instanceof AxiosError ? err.response?.data?.detail : 'Registration failed';
      toast.error(message || 'Registration failed');
    }
  };

  return (
    <div>
      <h2 className="text-2xl font-bold mb-2">Create your account</h2>
      <p className="text-gray-500 mb-8">Start building voice agents today</p>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1">Full Name</label>
          <Input value={fullName} onChange={(e) => setFullName(e.target.value)} placeholder="John Doe" required />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Company Name</label>
          <Input value={companyName} onChange={(e) => setCompanyName(e.target.value)} placeholder="Acme Inc." required />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Email</label>
          <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@company.com" required />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Password</label>
          <Input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" required minLength={8} />
        </div>
        <Button type="submit" className="w-full" disabled={register.isPending}>
          {register.isPending ? 'Creating account…' : 'Create account'}
        </Button>
      </form>

      <p className="text-center text-sm text-gray-500 mt-6">
        Already have an account?{' '}
        <Link to="/login" className="text-primary-600 hover:underline font-medium">
          Sign in
        </Link>
      </p>
    </div>
  );
}
