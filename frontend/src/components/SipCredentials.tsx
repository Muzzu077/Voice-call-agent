import React, { useState } from "react";
import { useAuth } from "../contexts/AuthContext";

export const SipCredentials = () => {
  const { profile } = useAuth();
  const [showPassword, setShowPassword] = useState(false);

  if (!profile?.sip_username) {
    return (
      <div className="bg-yellow-900/30 border-l-4 border-yellow-500 p-4 rounded-md">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-yellow-500" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <p className="text-sm text-yellow-200">
              SIP credentials are not yet provisioned for your account. Please wait a moment or contact support.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="glass border border-gray-700 rounded-lg shadow-sm overflow-hidden">
      <div className="px-4 py-5 sm:px-6 bg-gray-800/60 border-b border-gray-700">
        <h3 className="text-lg leading-6 font-medium text-gray-100">SIP Credentials</h3>
        <p className="mt-1 max-w-2xl text-sm text-gray-400">
          Use these credentials to configure your softphone (e.g., Zoiper, MicroSIP).
        </p>
      </div>
      <div className="px-4 py-5 sm:p-0">
        <dl className="sm:divide-y sm:divide-gray-700">
          <div className="py-4 sm:py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
            <dt className="text-sm font-medium text-gray-400">Username</dt>
            <dd className="mt-1 text-sm text-gray-200 sm:mt-0 sm:col-span-2 font-mono bg-gray-900/50 p-2 rounded border border-gray-700">
              {profile.sip_username}
            </dd>
          </div>
          <div className="py-4 sm:py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
            <dt className="text-sm font-medium text-gray-400">Password</dt>
            <dd className="mt-1 text-sm text-gray-200 sm:mt-0 sm:col-span-2 flex items-center gap-2">
              <span className="font-mono bg-gray-900/50 p-2 rounded flex-1 border border-gray-700">
                {showPassword ? profile.sip_password : "•".repeat(24)}
              </span>
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="inline-flex items-center px-3 py-1.5 border border-gray-600 shadow-sm text-xs font-medium rounded text-gray-300 bg-gray-800 hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                {showPassword ? "Hide" : "Show"}
              </button>
            </dd>
          </div>
          <div className="py-4 sm:py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
            <dt className="text-sm font-medium text-gray-400">SIP URI</dt>
            <dd className="mt-1 text-sm text-gray-200 sm:mt-0 sm:col-span-2 font-mono bg-gray-900/50 p-2 rounded break-all border border-gray-700">
              {profile.sip_uri}
            </dd>
          </div>
        </dl>
      </div>
    </div>
  );
};

export default SipCredentials;
