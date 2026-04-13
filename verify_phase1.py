"""Quick verification script for Phase 1 components."""
import asyncio
import json
import os
import sys

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

async def main():
    print("=" * 50)
    print("Phase 1 Verification")
    print("=" * 50)

    # 1. Config
    print("\n[1] Config...")
    from app.config import settings
    print(f"  Model: {settings.OLLAMA_MODEL}")
    print(f"  DB: {settings.SQLITE_DB_PATH}")
    print(f"  [OK] Config")

    # 2. Tool Parser
    print("\n[2] Tool Parser...")
    from app.brain.tool_parser import ToolParser
    p = ToolParser()
    print(f"  Supported actions: {p.get_supported_actions()}")
    assert not p.is_tool_call("Hello there"), "Text should NOT be tool call"
    test_json = json.dumps({"action": "create_task", "task": "Buy groceries"})
    assert p.is_tool_call(test_json), "JSON should be tool call"
    parsed = p.parse_tool_call(test_json)
    assert parsed is not None
    assert parsed["action"] == "create_task"
    print(f"  Parsed: {parsed}")
    # Test markdown-wrapped JSON
    md_json = '```json\n{"action": "create_reminder", "message": "test", "trigger_time": "18:00"}\n```'
    assert p.is_tool_call(md_json), "Markdown JSON should be tool call"
    print(f"  [OK] Tool Parser")

    # 3. SQLite
    print("\n[3] SQLite Structured Store...")
    settings.ensure_data_dirs()
    from app.memory.structured_store import StructuredStore
    store = StructuredStore(db_path="./data/test_verify.db")
    await store.init_db()
    from app.memory.models import TaskCreate, ReminderCreate
    task = await store.create_task(TaskCreate(task="Test task", deadline="tomorrow"))
    print(f"  Created task: {task.id} - {task.task}")
    tasks = await store.get_tasks()
    print(f"  Total tasks: {len(tasks)}")
    reminder = await store.create_reminder(ReminderCreate(message="Test reminder", trigger_time="18:00"))
    print(f"  Created reminder: {reminder.id} - {reminder.message}")
    mem_id = await store.save_memory_log("Test conversation", "sess1")
    print(f"  Saved memory log: {mem_id}")
    memories = await store.get_recent_memories(5)
    print(f"  Recent memories: {len(memories)}")
    await store.close()
    print(f"  [OK] SQLite")

    # 4. ChromaDB
    print("\n[4] ChromaDB Vector Store...")
    from app.memory.vector_store import VectorStore
    vs = VectorStore(persist_dir="./data/test_chroma")
    vs.init()
    vs.store_memory("The user likes coffee and works at Google")
    vs.store_memory("The user has a meeting tomorrow at 3 PM")
    vs.store_memory("The user's favorite color is blue")
    results = vs.search_similar("What does the user drink?", top_k=2)
    print(f"  Stored 3 memories, searched 'What does the user drink?':")
    for r in results:
        print(f"    - {r['text'][:60]}... (dist: {r['distance']:.3f})")
    print(f"  Total memories: {vs.get_count()}")
    print(f"  [OK] ChromaDB")

    # 5. Memory Service
    print("\n[5] Memory Service...")
    from app.memory.memory_service import MemoryService
    ms = MemoryService()
    ms.vector_store = VectorStore(persist_dir="./data/test_chroma_ms")
    ms.structured_store = StructuredStore(db_path="./data/test_verify_ms.db")
    await ms.initialize()
    await ms.save_conversation("Hello!", "Hi there, how can I help?")
    context = await ms.recall_context("greeting")
    print(f"  Recalled {len(context)} memories for 'greeting'")
    stats = ms.get_stats()
    print(f"  Stats: {stats}")
    await ms.shutdown()
    print(f"  [OK] Memory Service")

    # 6. Context Builder
    print("\n[6] Context Builder...")
    from app.brain.context_builder import ContextBuilder
    cb = ContextBuilder()
    prompt = cb.build_system_prompt()
    print(f"  System prompt length: {len(prompt)} chars")
    assert "assistant" in prompt.lower()
    assert "action" in prompt.lower()
    cb.add_turn("user", "Hello")
    cb.add_turn("assistant", "Hi!")
    history = cb.get_history()
    print(f"  History turns: {len(history)}")
    print(f"  [OK] Context Builder")

    # 7. Action Dispatcher
    print("\n[7] Action Dispatcher...")
    from app.execution.action_dispatcher import ActionDispatcher
    d = ActionDispatcher()
    print(f"  Supported: {d.get_supported_actions()}")
    print(f"  [OK] Action Dispatcher")

    # 8. LLM Engine (import check only)
    print("\n[8] LLM Engine...")
    from app.brain.llm_engine import LLMEngine
    e = LLMEngine()
    print(f"  Model: {e.model}, URL: {e.base_url}")
    print(f"  [OK] LLM Engine (import)")

    # 9. Agent Service (import check only)
    print("\n[9] Agent Service...")
    from app.brain.agent_service import AgentService
    a = AgentService()
    print(f"  [OK] Agent Service (import)")

    # 10. FastAPI App (import check)
    print("\n[10] FastAPI App...")
    from app.api.main import app
    print(f"  Title: {app.title}")
    print(f"  Routes: {len(app.routes)}")
    print(f"  [OK] FastAPI App")

    print("\n" + "=" * 50)
    print("ALL PHASE 1 COMPONENTS VERIFIED SUCCESSFULLY")
    print("=" * 50)

    # Cleanup test files
    for f in ["./data/test_verify.db", "./data/test_verify_ms.db"]:
        if os.path.exists(f):
            os.remove(f)
    import shutil
    for d in ["./data/test_chroma", "./data/test_chroma_ms"]:
        if os.path.exists(d):
            shutil.rmtree(d)

if __name__ == "__main__":
    asyncio.run(main())
