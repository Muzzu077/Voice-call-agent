import Link from "next/link";

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4 animated-gradient">
      <div className="max-w-3xl text-center space-y-8 glass p-12">
        <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight gradient-text pb-2">
          Voice Call Agent
        </h1>
        <p className="text-xl text-gray-300 max-w-2xl mx-auto leading-relaxed">
          Your personal voice assistant that plans your day, calls your softphone, and logs everything in real-time.
        </p>
        <div className="flex flex-col sm:flex-row justify-center gap-4 mt-8">
          <Link
            href="/login"
            className="btn-glow text-center"
          >
            Get Started
          </Link>
          <Link
            href="/login"
            className="btn-outline text-center"
          >
            Sign In
          </Link>
        </div>
      </div>
    </div>
  );
}
