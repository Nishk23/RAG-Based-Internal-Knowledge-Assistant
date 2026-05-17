from langchain_core.prompts import ChatPromptTemplate

ANSWER_PROMPT = ChatPromptTemplate.from_template(
    """
You are an internal knowledge assistant.
Answer the question using only the provided context.
If the answer is not present in context, say that explicitly.

Question:
{question}

Context:
{context}

Return a concise, factual answer. Include no fabricated details.
""".strip()
)
