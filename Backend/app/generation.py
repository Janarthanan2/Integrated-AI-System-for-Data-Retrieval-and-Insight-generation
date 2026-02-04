from langchain_community.llms import CTransformers

from langchain_core.prompts import PromptTemplate
import os


class GenerationManager:
    """

    Manages LLM loading and response generation using Mistral-7B via LangChain.
    """
    

    def __init__(self):

        print("Initializing Generation Manager (Mistral-7B - LangChain)...")

        # Mistral-7B provides better quality than TinyLlama, but optimized for speed

        self.model_repo = "TheBloke/Mistral-7B-Instruct-v0.2-GGUF"

        self.model_file = "mistral-7b-instruct-v0.2.Q4_K_M.gguf"
        

        self.llm = None

        try:

            # Load using LangChain's CTransformers wrapper
            config = {
                'max_new_tokens': 512,
                'temperature': 0.2,
                'repetition_penalty': 1.05,
                'context_length': 2048, # Increased from 2048
                'batch_size': 16,  # Optimized for CPU speed
                'gpu_layers': 22,    # Force CPU to avoid any GPU overhead/errors if not present
                'threads': 2, # Use physical cores
                'stream': True, # Enable streaming explicitly
                'stop': ['</s>', '<|user|>', 'User:'] # Stop tokens to prevent looping
            }
            
            # Use TinyLlama for speed as requested
            self.model_repo = "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF"
            self.model_file = "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
            self.llm = CTransformers(
                model=self.model_repo,
                model_file=self.model_file,
                model_type="llama",
                config=config
            )
            print("TinyLlama-1.1B loaded successfully via LangChain.")

        except Exception as e:
            print(f"CRITICAL WARNING: Failed to load Model via LangChain. {e}")
            self.llm = None

    def _get_strict_template(self, mode: str) -> str:
        """
        Returns a strict, mode-specific prompt template formatted for TinyLlama.
        Format: <|system|>\n{system}</s>\n<|user|>\n{user}</s>\n<|assistant|>
        """
        # Common strict rules
        # 0. User-Provided Speed & Conciseness Rules
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

        # 1. Intent-Specific Tweaks (Optional overrides or additions)
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
        if not context_str or "I don’t see sufficient data" in context_str:
             return {"reply": "I don’t see sufficient data to answer this question.", "follow_up_questions": []}

        # Truncate context to avoid overflow (approx 6000 chars ~ 1500 tokens for 2k limit)
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
        # Check against common "empty" markers or actual empty string
        if not context_str or not context_str.strip() or "I don’t see sufficient data" in context_str:
            yield "I don’t see sufficient data to answer this question."
            return

        # Truncate context to avoid overflow (approx 6000 chars ~ 1500 tokens for 2k limit)
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