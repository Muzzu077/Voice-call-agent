import Link from "next/link";

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 text-center bg-white p-10 rounded-xl shadow-lg border border-gray-100">
        <div>
          <h2 className="mt-6 text-4xl font-extrabold text-gray-900">404</h2>
          <h3 className="text-xl font-medium text-gray-700 mt-2">Page Not Found</h3>
          <p className="mt-2 text-sm text-gray-500">
            The page you are looking for doesn&apos;t exist or has been moved.
          </p>
        </div>
        <div className="mt-8">
          <Link
            href="/"
            className="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
          >
            Return Home
          </Link>
        </div>
      </div>
    </div>
  );
}
