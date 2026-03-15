"""Reasoner Agent: synthesize retrieved evidence and draft answer.

Uses LangChain core (langchain_core.messages + BaseChatModel) so the agent
is not tied to langchain_openai; the LLM is provided by the shared factory.
"""

from typing import List

from langchain_core.messages import HumanMessage, SystemMessage

from app.core.llm import get_llm
from app.core.logging import get_logger
from app.models.chunk import DocumentChunk
from app.utils.security import sanitize_for_prompt

logger = get_logger(__name__)

REASONER_SYSTEM = """You are a precise assistant. Your task is to answer the user's question using ONLY the provided context from uploaded documents.
- Base your answer strictly on the retrieved context. Do not add external knowledge.
- Include inline citations (e.g., "According to [filename, page X]...").
- If the context does not support an answer, say: "I could not find enough evidence in the uploaded documents to answer this confidently."
- Be concise and factual."""


class ReasonerAgent:
    """Synthesizes chunks into a grounded answer using a LangChain BaseChatModel."""

    def synthesize(
        self,
        question: str,
        chunks: List[tuple[DocumentChunk, float]],
    ) -> str:
        """Produce answer from question and retrieved chunks."""
        if not chunks:
            return "I could not find enough evidence in the uploaded documents to answer this confidently."
        context_parts = []
        for i, (chunk, _) in enumerate(chunks, 1):
            safe = sanitize_for_prompt(chunk.content, max_length=8000)
            ref = f"{chunk.metadata.file_name}"
            if chunk.metadata.page is not None:
                ref += f", page {chunk.metadata.page}"
            if chunk.metadata.sheet_name:
                ref += f', sheet "{chunk.metadata.sheet_name}"'
            context_parts.append(f"[{i}] ({ref})\n{safe}")
        context = "\n\n---\n\n".join(context_parts)
        user_content = (
            f"Context:\n\n{context}\n\n---\n\nQuestion: {question}\n\n"
            "Answer (cite sources from context):"
        )
        llm = get_llm()
        if not llm:
            return "The answer service is temporarily unavailable. Please check that OPENAI_API_KEY is set."
        messages = [
            SystemMessage(content=REASONER_SYSTEM),
            HumanMessage(content=user_content),
        ]
        try:
            msg = llm.invoke(messages)
            return msg.content if hasattr(msg, "content") else str(msg)
        except Exception as e:
            logger.exception("reasoner_llm_error", error=str(e))
            return "An error occurred while generating the answer. Please try again."
