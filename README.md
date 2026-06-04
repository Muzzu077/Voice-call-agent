# AI Voice Planner Agent

A real-time, interruptible, memory-aware AI voice agent that talks naturally, handles phone calls, executes actions via tool calling, remembers intelligently, and behaves safely.

## Architecture

The system is built on a modern, serverless architecture using Firebase and Next.js:

- **Frontend:** Next.js (React), Tailwind CSS, Firebase Auth
- **Backend:** Firebase Cloud Functions (Python 3.11), Firebase Admin SDK
- **Database:** Cloud Firestore (NoSQL Document Database)
- **Telephony:** Twilio Programmable Voice & SIP
- **AI/LLM:** OpenAI (GPT-4o, Whisper) or OpenRouter (Llama 3.1)
- **Hosting:** Firebase Hosting

See [ARCHITECTURE.md](.gsd/ARCHITECTURE.md) for the full system design.

## Prerequisites

- [Node.js](https://nodejs.org/) (v18+)
- [Python](https://www.python.org/) (3.11+)
- [Firebase CLI](https://firebase.google.com/docs/cli) (`npm install -g firebase-tools`)
- A Firebase Project
- A Twilio Account

## Quick Start (Local Development)

### 1. Environment Setup

Copy the example environment variables and fill them in:

```bash
cp .env.example frontend/.env.local
cp .env.example functions/.env
```

*Note: For local emulation, Firebase automatically uses mock credentials, but you will still need valid API keys for LLM and Twilio services.*

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The Next.js app will be running at `http://localhost:3001`.

### 3. Backend Setup

```bash
cd functions
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Firebase Emulators

In the root directory, start the Firebase Emulator Suite:

```bash
firebase emulators:start --project demo-project
```

This will spin up local versions of:
- Authentication (`localhost:9099`)
- Firestore (`localhost:8080`)
- Cloud Functions (`localhost:5001`)
- Pub/Sub (`localhost:8085`)
- Hosting (`localhost:5000`)
- Emulator UI (`localhost:4000`)

## Deployment

To deploy to production (Firebase):

```bash
firebase deploy --only functions,firestore,hosting
```

The `predeploy` hooks will automatically build the Next.js frontend before deploying it to Firebase Hosting.

## License

MIT
