"""Intent classification using LangChain — provider decided by model name."""
import json

from langchain_core.messages import HumanMessage, SystemMessage

from backend.config import get_settings
from backend.core.llm_factory import get_llm
from backend.models.api_schemas import IntentResult

settings = get_settings()

INTENT_SYSTEM_PROMPT = """You are an intent classifier for an enterprise sales training search system.

Classify the user's query into exactly one of these 5 intents:

1. **assigned_knowledge** — Query about product information, training materials, plays, or knowledge content
   Examples: "What are the benefits of Amproxin?", "How does Hexenon-S work?", "What is GridMaster?"

2. **performance_history** — Query about the user's own submissions, practice sessions, scores, or AI feedback
   Examples: "How did I do on my last pitch?", "What score did I get?", "Show me my feedback"

3. **combined** — Query that spans both knowledge content AND personal performance history
   Examples: "How did I explain Amproxin and what feedback did I get?", "Compare my pitch to the official guide"

4. **general_professional** — Professional question not tied to specific assigned materials
   Examples: "How do I handle price objections?", "What makes a good sales pitch?"

5. **out_of_scope** — Completely unrelated to sales training, professional development, or work
   Examples: "What's the weather?", "Write me a poem", "Book a flight"

Respond with ONLY a JSON object (no markdown fences):
{"intent": "<one of the 5 above>", "confidence": <0.0-1.0>, "reasoning": "<brief reasoning>"}"""


def classify_intent(query: str) -> IntentResult:
    llm = get_llm(settings.model, max_tokens=256, temperature=0)
    
    # Few-shot examples to guide the LLM
    few_shot_examples = """
Example 1:
Query: "What is the eradication rate for Streptococcus pneumoniae?"
Response: {"intent": "assigned_knowledge", "confidence": 0.95, "reasoning": "Query asks about clinical efficacy data for a pathogen, which is product knowledge."}

Example 2:
Query: "Tell me a joke"
Response: {"intent": "out_of_scope", "confidence": 0.99, "reasoning": "Request for entertainment, unrelated to sales training."}

Example 3:
Query: "How do I handle objections?"
Response: {"intent": "general_professional", "confidence": 0.90, "reasoning": "General sales technique question, not about specific assigned materials."}

Now classify this query:"""
    
    messages = [
        SystemMessage(content=INTENT_SYSTEM_PROMPT),
        HumanMessage(content=f"{few_shot_examples}\nQuery: {query}"),
    ]
    response = llm.invoke(messages)
    raw = response.content.strip()

    # Strip markdown fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        parsed = json.loads(raw)
        return IntentResult(
            intent=parsed["intent"],
            confidence=float(parsed.get("confidence", 0.9)),
            reasoning=parsed.get("reasoning", ""),
        )
    except Exception:
        return IntentResult(
            intent="assigned_knowledge",
            confidence=0.5,
            reasoning="Classification failed, defaulting to knowledge search.",
        )
