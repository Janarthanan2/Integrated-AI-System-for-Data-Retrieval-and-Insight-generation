from langchain_community.llms import CTransformers

from langchain_core.prompts import PromptTemplate
import os


# Model Registry: All available models
MODEL_REGISTRY = {
    "tinyllama": {
        "name": "TinyLlama-1.1B",
        "repo": "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF",
        "file": "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
        "type": "llama",
        "description": "Fast, lightweight model optimized for speed"
    },
    "mistral": {
        "name": "Mistral-7B",
        "repo": "TheBloke/Mistral-7B-Instruct-v0.2-GGUF",
        "file": "mistral-7b-instruct-v0.2.Q4_K_M.gguf",
        "type": "mistral",
        "description": "High-accuracy model for deep analysis"
    }
}


class GenerationManager:
    """
    Manages LLM loading and response generation.
    Supports hot-swapping between models with zero-downtime caching.
    """

    # Shared config for all models
    MODEL_CONFIG = {
        'max_new_tokens': 512,
        'temperature': 0.2,
        'repetition_penalty': 1.05,
        'context_length': 2048,
        'batch_size': 16,
        'gpu_layers': 22,
        'threads': 2,
        'stream': True,
        'stop': ['</s>', '<|user|>', 'User:']
    }

    def __init__(self, default_model="tinyllama"):
        print("Initializing Generation Manager with Model Caching...")

        # Cache: stores loaded model instances for instant switching
        self._models_cache = {}
        self._current_model_id = None
        self.llm = None

        # Load the default model
        self.load_model(default_model)

    def load_model(self, model_id: str) -> bool:
        """
        Load a model by its ID. If already cached, switch instantly.
        Returns True on success, False on failure.
        """
        if model_id not in MODEL_REGISTRY:
            print(f"ERROR: Unknown model ID '{model_id}'. Available: {list(MODEL_REGISTRY.keys())}")
            return False

        # If already the active model, do nothing
        if model_id == self._current_model_id:
            print(f"Model '{model_id}' is already active.")
            return True

        # Check cache for instant switch
        if model_id in self._models_cache:
            print(f"Switching to cached model: {MODEL_REGISTRY[model_id]['name']}...")
            self.llm = self._models_cache[model_id]
            self._current_model_id = model_id
            print(f"{MODEL_REGISTRY[model_id]['name']} activated instantly from cache.")
            return True

        # Load fresh
        model_info = MODEL_REGISTRY[model_id]
        print(f"Loading {model_info['name']} for the first time (this may take a moment)...")

        try:
            llm_instance = CTransformers(
                model=model_info["repo"],
                model_file=model_info["file"],
                model_type=model_info["type"],
                config=self.MODEL_CONFIG
            )
            # Store in cache
            self._models_cache[model_id] = llm_instance
            self.llm = llm_instance
            self._current_model_id = model_id
            print(f"{model_info['name']} loaded and cached successfully.")
            return True
        except Exception as e:
            print(f"CRITICAL WARNING: Failed to load {model_info['name']}. {e}")
            return False

    def get_current_model(self) -> dict:
        """Returns info about the currently active model."""
        if self._current_model_id and self._current_model_id in MODEL_REGISTRY:
            info = MODEL_REGISTRY[self._current_model_id].copy()
            info["id"] = self._current_model_id
            info["cached"] = self._current_model_id in self._models_cache
            return info
        return {"id": None, "name": "None", "description": "No model loaded"}

    def get_available_models(self) -> list:
        """Returns list of all available models with their status."""
        models = []
        for model_id, info in MODEL_REGISTRY.items():
            models.append({
                "id": model_id,
                "name": info["name"],
                "description": info["description"],
                "is_active": model_id == self._current_model_id,
                "is_cached": model_id in self._models_cache
            })
        return models

    def _get_strict_template(self, mode: str) -> str:
        """
        Returns a strict, mode-specific prompt template.
        """
        # Common strict rules
        base_rules = """You are a fast, concise assistant optimized for low-latency responses.
Your priority is SPEED.
Data usage:
- If factual data is provided, use only that data.
- Do not analyze or infer beyond the given data.
- If the required data is missing, respond with one short sentence stating that clearly.
Response style:
- IF the data contains multiple rows/items, YOU MUST USE A MARKDOWN TABLE.
- Otherwise, respond with one short paragraph.
- Plain conversational language.
- NO bullet points. NO lists. NO bold headings.
- If a chart is generated, do NOT describe the chart details. Just summarize the key insight in one sentence.

Stop generation immediately after answering."""

        # Intent-Specific Tweaks
        specific_instr = ""
        if mode == "AGGREGATE":
            specific_instr = "Give the final number directly."
            answer_prefix = "ANSWER:"
        elif mode == "LIST" or mode == "DIRECT":
            specific_instr = """7. Present the provided data exactly as a table.
                                8. Do not analyze or calculate.
                                9. Do not add explanations.
                                10. Do not modify values.
                                11. Stop after the table."""
            answer_prefix = "ANSWER:\n"
        elif mode == "TREND" or mode == "CHART":
            specific_instr = "7. For 'Significant Changes' or detailed monthly data, YOU MAY USE A MARKDOWN TABLE. Otherwise, summarize the key trend in a single, continuous sentence. Do NOT use bullet points."
            answer_prefix = "ANSWER (Summary or Table):"
        else:
            specific_instr = ""
            answer_prefix = "ANSWER:"

        # Construct the final template string
        return f"""<|system|>
{base_rules}
{specific_instr}</s>
<|user|>
CONTEXT DATA:
{{context_str}}

QUESTION:
{{query}}</s>
<|assistant|>
{answer_prefix}"""

    def generate_response(self, query: str, context_str: str, intent: str):
        """
        Generates a response (Non-streaming).
        """
        if not self.llm:
            return {"reply": "System: Model not loaded.", "follow_up_questions": []}

        # SHORT-CIRCUIT: Empty Context
        if not context_str or "I don't see sufficient data" in context_str:
             return {"reply": "I don't see sufficient data to answer this question.", "follow_up_questions": []}

        # Truncate context to avoid overflow
        if len(context_str) > 6000:
            context_str = context_str[:6000] + "...(truncated)"

        template = self._get_strict_template(intent)

        formatted_prompt = PromptTemplate(
            template=template,
            input_variables=["context_str", "query"]
        ).format(
            context_str=context_str,
            query=query
        )

        response_text = self.llm.invoke(formatted_prompt)

        # Cleanup
        reply = response_text.strip()

        return {"reply": reply, "follow_up_questions": []}

    def generate_response_stream(self, query: str, context_str: str, intent: str, history: list = []):
        """
        Yields tokens for the response as they are generated.
        """
        if not self.llm:
            yield "System: Model not loaded."
            return

        # SHORT-CIRCUIT: Empty Context
        if not context_str or not context_str.strip() or "I don't see sufficient data" in context_str:
            yield "I don't see sufficient data to answer this question."
            return

        # Truncate context to avoid overflow
        if len(context_str) > 6000:
            context_str = context_str[:6000] + "...(truncated)"

        # Select Template
        template = self._get_strict_template(intent)

        formatted_prompt = PromptTemplate(
            template=template,
            input_variables=["context_str", "query"]
        ).format(
            context_str=context_str,
            query=query
        )

        for chunk in self.llm.stream(formatted_prompt):
            yield chunk