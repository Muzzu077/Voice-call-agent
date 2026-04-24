"""Benchmark: Test the actual system prompt with llama3.2:3b"""
import time, ollama, sys
sys.path.insert(0, ".")

from app.brain.personality import Personality
from app.brain.context_builder import ContextBuilder

cb = ContextBuilder()
system = cb.build_system_prompt()
print(f"System prompt length: {len(system)} chars\n")

tests = [
    "open chrome",
    "search python tutorial on youtube",
    "hello",
    "set a reminder in 2 minutes to drink water",
    "open vs code",
]

for t in tests:
    t0 = time.time()
    r = ollama.chat(model="llama3.2:3b", messages=[
        {"role": "system", "content": system},
        {"role": "user", "content": t}
    ], options={"num_predict": 100, "num_ctx": 2048, "temperature": 0.5})
    t1 = time.time()
    resp = r.message.content.replace("\n", " ").strip()
    print(f"{t1-t0:.2f}s | \"{t}\" => {resp[:120]}")
