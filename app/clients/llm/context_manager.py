import logging
from typing import List, Optional, Any
from uuid import UUID
from app.core.config import settings
from app.core.enums import PromptType, MessageRoleTypes
from app.clients.interfaces.llm import ILLMClient
from app.clients.interfaces.context import IContextManager
from app.schemas.context import LLMMessage, ContextBudget, ContextResult, UnsummarizedMessages

logger = logging.getLogger(__name__)


class ContextManager(IContextManager):
    """Manages LLM context, token budgets, and summarization."""

    def __init__(
        self,
        llm_client: ILLMClient,
        max_context_tokens: Optional[int] = None,
        reserved_output_tokens: int = 1024,
        tokens_per_char: float = None,
        keep_recent_messages: int = 6,
    ):
        self._llm = llm_client
        self._max_tokens = max_context_tokens or settings.LLM_MAX_CONTEXT_LENGTH
        self._reserved_output = reserved_output_tokens
        self._tokens_per_char = tokens_per_char or settings.DEFAULT_TOKENS_PER_CHAR
        self._keep_recent = keep_recent_messages

    # region PUBLIC API

    def extract_unsummarized(
        self,
        all_messages: List[Any],
        summary_up_to_id: Optional[UUID],
    ) -> UnsummarizedMessages:
        """Extract messages not yet included in session summary."""

        messages = all_messages

        # If the session has a summary, return messages after the summary point
        if summary_up_to_id:
            for i, msg in enumerate(all_messages):
                if msg.id == summary_up_to_id:
                    messages = all_messages[i + 1 :]
                    break
            else:
                logger.warning(f"Summary message {summary_up_to_id} not found, workflow issue")

        # Not summarized messages, return all
        return UnsummarizedMessages(
            messages=[LLMMessage(role=m.role.value, content=m.content) for m in messages],
            message_ids=[m.id for m in messages],
        )

    async def build_context(
        self,
        unsummarized: UnsummarizedMessages,
        new_message: str,
        current_summary: Optional[str] = None,
        rag_context: Optional[str] = None,
    ) -> ContextResult:
        """Build context for LLM."""

        history = unsummarized.messages
        message_ids = unsummarized.message_ids

        # Calculate token budget for all components
        budget = self._calculate_budget(history, new_message, current_summary, rag_context)

        logger.debug(f"Budget: {budget}")

        # Within budget, return all messages
        if not budget.is_over_budget:
            return ContextResult(
                messages=self._assemble_messages(history, current_summary, rag_context),
                budget=budget,
            )

        # Over budget, reduce context
        logger.info(f"Over budget ({budget.total_used}/{budget.available_for_input})")
        return await self._reduce_context(history, message_ids, new_message, current_summary, rag_context, budget)

    # endregion PUBLIC API

    # region CONTEXT REDUCTION

    async def _reduce_context(
        self,
        history: List[LLMMessage],
        message_ids: List[UUID],
        new_message: str,
        summary: Optional[str],
        rag_context: Optional[str],
        budget: ContextBudget,
    ) -> ContextResult:
        """Reduce context by truncation or summarization."""
        min_for_summary = self._keep_recent + 2

        # Not enough to summarize - truncate
        if len(history) < min_for_summary:
            available = (
                budget.available_for_input
                - budget.system_prompt_tokens
                - budget.summary_tokens
                - budget.new_message_tokens
                - budget.rag_context_tokens
            )
            fitted = self._fit_to_budget(history, available)
            return ContextResult(
                messages=self._assemble_messages(fitted, new_message, summary, rag_context),
                budget=budget,
            )

        # Summarize older messages
        keep = min(self._keep_recent, len(history) - 2)
        to_summarize, recent = history[:-keep], history[-keep:]
        ids_summarized = message_ids[:-keep]

        new_summary = await self._generate_summary(to_summarize, summary)

        logger.info(f"Summarized {len(to_summarize)} msgs, keeping {len(recent)}")

        return ContextResult(
            messages=self._assemble_messages(recent, new_message, new_summary, rag_context),
            budget=self._calculate_budget(recent, new_message, new_summary, rag_context),
            needs_summary_update=True,
            new_summary=new_summary,
            summary_up_to_message_id=ids_summarized[-1] if ids_summarized else None,
        )

    def _fit_to_budget(self, messages: List[LLMMessage], available: int) -> List[LLMMessage]:
        """Keep most recent messages that fit in budget."""
        result, used = [], 0
        for msg in reversed(messages):
            tokens = self._estimate_tokens(msg.content) + settings.MESSAGE_OVERHEAD_TOKENS
            if used + tokens > available:
                break
            result.insert(0, msg)
            used += tokens
        return result

    def _assemble_messages(
        self,
        history: List[LLMMessage],
        summary: Optional[str],
        rag_context: Optional[str],
    ) -> List[LLMMessage]:
        """Assemble final message list with context."""

        messages: List[LLMMessage] = []

        if summary:
            messages.append(LLMMessage.system(f"[Conversation summary]\n{summary}"))
        if rag_context:
            messages.append(LLMMessage.system(f"[Document context]\n{rag_context}"))

        messages.extend(history)
        return messages

    # endregion CONTEXT REDUCTION

    # region SUMMARIZATION

    async def _generate_summary(
        self,
        messages: List[LLMMessage],
        existing: Optional[str] = None,
    ) -> str:
        """Generate conversation summary using LLM."""
        try:
            parts = []
            if existing:
                parts.append(f"[Previous summary]: {existing}\n")
            parts.append("[Conversation]:")
            parts.extend(f"{'User' if m.role == MessageRoleTypes.USER else 'Assistant'}: {m.content}" for m in messages)

            response = await self._llm.generate(
                prompt=f"{self._llm.get_prompt(PromptType.SUMMARIZER)}\n\n---\n\n{chr(10).join(parts)}",
                temperature=0.3,
                max_tokens=500,
            )
            return response.content.strip()

        except Exception as e:
            logger.warning(f"Summary failed: {e}")
            user_topics = [m.content.split("\n")[0][:80] for m in messages if m.role == MessageRoleTypes.USER]
            fallback = f"Temas: {'; '.join(user_topics[:3])}" if user_topics else ""
            return f"{existing} | {fallback}" if existing else fallback

    # endregion SUMMARIZATION

    # region TOKEN ESTIMATION

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text."""
        return int(len(text) * self._tokens_per_char) if text else 0

    def _calculate_budget(
        self,
        history: List[LLMMessage],
        new_message: str,
        summary: Optional[str],
        rag_context: Optional[str],
    ) -> ContextBudget:
        """Calculate token budget for all components."""

        return ContextBudget(
            max_tokens=self._max_tokens,
            reserved_output=self._reserved_output,
            system_prompt_tokens=self._estimate_tokens(self._llm.system_prompt),
            history_tokens=sum(
                self._estimate_tokens(msg.content) + settings.MESSAGE_OVERHEAD_TOKENS for msg in history
            ),
            new_message_tokens=self._estimate_tokens(new_message) + settings.MESSAGE_OVERHEAD_TOKENS,
            summary_tokens=self._estimate_tokens(summary) + settings.MESSAGE_OVERHEAD_TOKENS if summary else 0,
            rag_context_tokens=(
                self._estimate_tokens(rag_context) + settings.MESSAGE_OVERHEAD_TOKENS if rag_context else 0
            ),
        )

    # endregion TOKEN ESTIMATION
