import { Outlet } from 'react-router-dom';

export default function AuthLayout() {
  return (
    <div className="flex min-h-screen">
      {/* Left branding panel */}
      <div className="hidden lg:flex lg:w-1/2 bg-primary-600 items-center justify-center p-12">
        <div className="max-w-md text-white">
          <h1 className="text-4xl font-bold mb-4">AI Voice Agent Platform</h1>
          <p className="text-lg text-primary-100">
            Create intelligent voice agents, automate calls, extract data, and export insights — all from one dashboard.
          </p>
          <div className="mt-8 space-y-3 text-primary-100">
            <div className="flex items-center gap-3">
              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-primary-500 text-white text-sm font-bold">1</span>
              <span>Build & configure voice agents</span>
            </div>
            <div className="flex items-center gap-3">
              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-primary-500 text-white text-sm font-bold">2</span>
              <span>Real-time AI-powered conversations</span>
            </div>
            <div className="flex items-center gap-3">
              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-primary-500 text-white text-sm font-bold">3</span>
              <span>Auto-extract & export call data</span>
            </div>
          </div>
        </div>
      </div>

      {/* Right form panel */}
      <div className="flex flex-1 items-center justify-center p-8">
        <div className="w-full max-w-md">
          <Outlet />
        </div>
      </div>
    </div>
  );
}
