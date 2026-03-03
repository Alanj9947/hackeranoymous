import { Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface SpinnerProps {
  className?: string;
  size?: number;
}

export function Spinner({ className, size = 24 }: SpinnerProps) {
  return <Loader2 className={cn('animate-spin text-primary-500', className)} size={size} />;
}

export function PageLoader() {
  return (
    <div className="flex h-full items-center justify-center py-20">
      <Spinner size={32} />
    </div>
  );
}
