"""
Agent Service — the orchestrator that ties together LLM, memory, tools, and actions.
This is the HEART of the system.
"""

import asyncio
import logging
from typing import Optional, Dict, Any, AsyncGenerator

from app.brain.llm_engine import LLMEngine
from app.brain.context_builder import ContextBuilder
from app.brain.tool_parser import ToolParser
from app.brain.summary_engine import SummaryEngine
from app.memory.memory_service import MemoryService
from app.execution.action_dispatcher import ActionDispatcher
from app.memory.models import ActionResult

logger = logging.getLogger(__name__)


class AgentService:
    """
    Main agent orchestrator — processes user messages through the full pipeline:
    1. Recall relevant context from memory
    2. Build prompt (personality + context + history)
    3. Call LLM
    4. Parse response (text vs tool call)
    5. If tool call → dispatch action → get result
    6. Save conversation to memory
    7. Return response
    """

    def __init__(self, agent_id=None):
        self.agent_id = agent_id
        self.llm = LLMEngine()
        self.context_builder = ContextBuilder()
        self.tool_parser = ToolParser()
        self.summary_engine = SummaryEngine()
        self.memory = MemoryService(self.agent_id)
        self.dispatcher = ActionDispatcher()
        self._initialized = False
        self._session_id = "default"

    async def initialize(self):
        """Initialize all components."""
        if self._initialized:
            return

        # Initialize memory (ChromaDB + SQLite)
        await self.memory.initialize()

        # Initialize action dispatcher with memory
        self.dispatcher.initialize(self.memory)

        # Check LLM connection
        connected = await self.llm.check_connection()
        if not connected:
            logger.warning("Ollama connection failed. LLM features may not work.")

        self._initialized = True
        logger.info("Agent service fully initialized.")

    async def shutdown(self):
        """Gracefully shut down all components."""
        await self.memory.shutdown()
        logger.info("Agent service shut down.")

    async def process_message(self, user_message: str) -> Dict[str, Any]:
        """
        Process a user message through the full pipeline.

        Args:
            user_message: The user's input text.

        Returns:
            Dict with 'response', 'action' (optional), 'action_result' (optional).
        """
        if not self._initialized:
            await self.initialize()

        logger.info(f"Processing message: {user_message[:100]}...")

        # Step 1: Recall relevant context from memory
        relevant_memories = await self.memory.recall_context(user_message, top_k=5)
        logger.debug(f"Retrieved {len(relevant_memories)} relevant memories.")

        # Step 2: Build context (system prompt + history)
        system_prompt, history = self.context_builder.build_context(
            user_message=user_message,
            relevant_memories=relevant_memories,
        )

        # Step 3: Call LLM
        llm_response = await self.llm.chat(
            user_message=user_message,
            system_prompt=system_prompt,
            history=history,
        )
        logger.debug(f"LLM response: {llm_response[:200]}...")

        # Step 4: Check if response is a tool call
        action_data = None
        action_result = None
        final_response = llm_response

        if self.tool_parser.is_tool_call(llm_response):
            action_data = self.tool_parser.parse_tool_call(llm_response)

            if action_data:
                logger.info(f"Tool call detected: {action_data.get('action')}")

                # Step 5: Execute the action
                result: ActionResult = await self.dispatcher.dispatch(action_data)
                action_result = result.message

                # Step 6: Get a natural language confirmation from LLM
                confirmation_prompt = (
                    f"The user asked: '{user_message}'\n"
                    f"You performed the action: {action_data.get('action')}\n"
                    f"Result: {result.message}\n"
                    f"Now respond naturally to confirm what you did. Keep it short (1-2 sentences)."
                )
                final_response = await self.llm.chat(
                    user_message=confirmation_prompt,
                    system_prompt=self.context_builder.build_system_prompt(),
                )

        # Step 7: Save conversation to memory
        self.context_builder.add_turn("user", user_message)
        self.context_builder.add_turn("assistant", final_response)
        await self.memory.save_conversation(
            user_message=user_message,
            ai_response=final_response,
            session_id=self._session_id,
        )

        return {
            "response": final_response,
            "action": action_data,
            "action_result": action_result,
        }

    async def process_message_fast(self, user_message: str) -> Dict[str, Any]:
        """
        FAST path for real-time voice calls — optimized for low latency.

        Differences from process_message():
        - Skips ChromaDB memory recall (saves ~500ms)
        - Uses only last 6 conversation turns (less context = faster LLM)
        - For tool calls, returns a hardcoded confirmation (no second LLM call)
        - Saves to memory in background (non-blocking)
        """
        import time
        if not self._initialized:
            await self.initialize()

        t0 = time.time()
        logger.info(f"[FAST] Processing: '{user_message[:80]}'")

        # Build context with minimal history (no memory recall)
        system_prompt = self.context_builder.build_system_prompt()
        history = self.context_builder.get_history()

        # Rolling summary compression — keeps context lean
        history = await self.summary_engine.maybe_compress(history)
        history = history[-6:]  # Last 6 turns after compression

        # Call LLM
        t1 = time.time()
        llm_response = await self.llm.chat(
            user_message=user_message,
            system_prompt=system_prompt,
            history=history,
        )
        t2 = time.time()
        logger.info(f"[FAST] LLM took {t2-t1:.2f}s")

        # Check for tool call
        action_data = None
        action_result = None
        final_response = llm_response

        if self.tool_parser.is_tool_call(llm_response):
            action_data = self.tool_parser.parse_tool_call(llm_response)

            if action_data:
                action_name = action_data.get("action", "")
                logger.info(f"[FAST] Tool call: {action_name}")

                # Execute action
                t_action = time.time()
                result: ActionResult = await self.dispatcher.dispatch(action_data)
                action_latency = int((time.time() - t_action) * 1000)
                action_result = result.message

                # Log action for observability
                asyncio.create_task(
                    self._log_action(
                        action_name, action_data,
                        "success" if result.success else "failed",
                        result.message, action_latency
                    )
                )

                # Fast confirmation — no second LLM call
                if result.success:
                    final_response = f"Done. {result.message}"
                else:
                    final_response = f"Sorry, that didn't work. {result.message}"

        # Save to memory and history
        self.context_builder.add_turn("user", user_message)
        self.context_builder.add_turn("assistant", final_response)

        # Background save (non-blocking)
        asyncio.create_task(
            self.memory.save_conversation(user_message, final_response, self._session_id)
        )

        t3 = time.time()
        logger.info(f"[FAST] Total: {t3-t0:.2f}s | Response: '{final_response[:60]}'")

        return {
            "response": final_response,
            "action": action_data,
            "action_result": action_result,
        }

    async def process_message_stream(self, user_message: str) -> AsyncGenerator[str, None]:
        """
        Process a user message and stream the response.

        For tool calls, yields the full response after action execution.
        For normal responses, yields tokens as they come from the LLM.
        """
        if not self._initialized:
            await self.initialize()

        # Recall context
        relevant_memories = await self.memory.recall_context(user_message, top_k=5)
        system_prompt, history = self.context_builder.build_context(
            user_message=user_message,
            relevant_memories=relevant_memories,
        )

        # Collect full response first to check for tool calls
        full_response = ""
        async for token in self.llm.chat_stream(user_message, system_prompt, history):
            full_response += token

        # Check for tool call
        if self.tool_parser.is_tool_call(full_response):
            action_data = self.tool_parser.parse_tool_call(full_response)
            if action_data:
                result = await self.dispatcher.dispatch(action_data)
                # Stream confirmation
                confirmation_prompt = (
                    f"The user asked: '{user_message}'\n"
                    f"Action performed: {action_data.get('action')}\n"
                    f"Result: {result.message}\n"
                    f"Respond naturally to confirm. Keep it short."
                )
                async for token in self.llm.chat_stream(confirmation_prompt, system_prompt):
                    yield token
                    full_response = ""  # Reset for memory saving

                # Save with action context
                self.context_builder.add_turn("user", user_message)
                self.context_builder.add_turn("assistant", result.message)
                await self.memory.save_conversation(user_message, result.message, self._session_id)
                return

        # Normal response — re-stream it
        for char_chunk in _chunk_text(full_response, 10):
            yield char_chunk

        # Save conversation
        self.context_builder.add_turn("user", user_message)
        self.context_builder.add_turn("assistant", full_response)
        await self.memory.save_conversation(user_message, full_response, self._session_id)

    def get_conversation_history(self):
        """Get the current conversation history."""
        return self.context_builder.get_history()

    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics."""
        return {
            "memory": self.memory.get_stats(),
            "history_turns": len(self.context_builder.get_history()),
            "session_id": self._session_id,
            "supported_actions": self.dispatcher.get_supported_actions(),
        }


    async def _log_action(self, action_type: str, action_data: dict,
                          status: str, result: str, latency_ms: int):
        """Log an action to the database for observability."""
        try:
            from app.db.database import AsyncSessionLocal
            from app.db.models import ActionLog
            async with AsyncSessionLocal() as session:
                log = ActionLog(
                    agent_id=self.agent_id,
                    action_type=action_type,
                    action_data=action_data,
                    status=status,
                    result=result,
                    latency_ms=latency_ms,
                )
                session.add(log)
                await session.commit()
        except Exception as e:
            logger.error(f"Failed to log action: {e}")


def _chunk_text(text: str, chunk_size: int = 10) -> list:
    """Split text into chunks for simulated streaming."""
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
