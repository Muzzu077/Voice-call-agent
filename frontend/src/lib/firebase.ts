import { initializeApp, getApps } from "firebase/app";
import { getAuth, connectAuthEmulator } from "firebase/auth";
import { getFirestore, connectFirestoreEmulator } from "firebase/firestore";

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID
};

const missingVars = Object.entries(firebaseConfig).filter(([, value]) => !value);
if (missingVars.length > 0) {
  const msg = `Missing required Firebase configuration variables: ${missingVars.map(([key]) => key).join(", ")}`;
  if (typeof window !== "undefined") {
    throw new Error(msg);
  } else {
    console.warn(msg);
  }
}

const app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApps()[0];

export const auth = getAuth(app);
export const db = getFirestore(app);

// Connect to emulators if running locally
if (
  process.env.NODE_ENV === "development" || 
  (typeof window !== "undefined" && window.location.hostname === "localhost")
) {
  try {
    // Avoid connecting multiple times during hot-reloads in Next.js development server
    if (!(auth as unknown as Record<string, unknown>)._emulatorConfig) {
      connectAuthEmulator(auth, "http://127.0.0.1:9099", { disableWarnings: true });
      console.log("Connected to Auth Emulator");
    }
    if (!(db as unknown as Record<string, unknown>)._emulatorConfig) {
      connectFirestoreEmulator(db, "127.0.0.1", 8080);
      console.log("Connected to Firestore Emulator");
    }
  } catch (e) {
    console.warn("Firebase emulator connection error:", e);
  }
}

