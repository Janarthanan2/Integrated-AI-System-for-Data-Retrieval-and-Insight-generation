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
                'max_new_tokens': 1024,
                'temperature': 0.3,
                'repetition_penalty': 1.1,
                'context_length': 2048,
                'batch_size': 64,  # Optimized for CPU speed
                'gpu_layers': 0,    # Force CPU to avoid any GPU overhead/errors if not present
                'threads': int(os.cpu_count() or 8), # Use physical cores
                'stop': ["</s>", "[/INST]", "QUESTION:", "User:"] # Critical: Stop tokens to prevent hallucination loops
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

    def _format_chat_prompt(self, messages: list) -> str:
        """
        Converts a list of messages (system, tool, user) into a Llama-2/Mistral compliant prompt string.
        Structure:
        [INST] <<SYS>>
        {system_content}
        
        TOOL DATA:
        {tool_content}
        <</SYS>>
        
        {user_content} [/INST]
        """
        system_content = ""
        tool_content = ""
        user_content = ""
        
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content", "")
            
            if role == "system":
                system_content += content + "\n"
            elif role == "tool":
                tool_content += content + "\n"
            elif role == "user":
                user_content += content + "\n"
                
        # Construct the monolithic prompt
        # We merge System and Tool into the System Block for the model
        full_system_block = f"{system_content}\n\nTOOL DATA (Hidden):\n{tool_content}".strip()
        
        formatted_prompt = f"""[INST] <<SYS>>
{full_system_block}
<</SYS>>

{user_content.strip()} [/INST]"""

        return formatted_prompt

    def generate_response(self, query: str, context_str: str, intent: str):
        """
        Generates a response using rigid role separation.
        """
        if not self.llm:
            return {"reply": "System: Model not loaded.", "follow_up_questions": []}

        # SHORT-CIRCUIT: Empty Context
        if not context_str or "I don’t see sufficient data" in context_str:
             return {"reply": "I don’t see sufficient data to answer this question.", "follow_up_questions": []}

        # 1. Construct Messages
        system_rules = """
1. Answer directly and naturally.
2. Use ONLY the 'Tool Data' provided. Do not invent data.
3. If data is missing, say so clearly.
4. No headings, no repetition.
5. Keep it short.
"""
        messages = [
            {"role": "system", "content": f"You are a helpful AI assistant.\nRULES:\n{system_rules}"},
            {"role": "tool", "content": context_str},
            {"role": "user", "content": query}
        ]
        
        # 2. Format Prompt (Replicating llm.chat behavior)
        prompt = self._format_chat_prompt(messages)
        
        # 3. Invoke
        response_text = self.llm.invoke(prompt)
        
        return {"reply": response_text.strip(), "follow_up_questions": []}

    def generate_response_stream(self, query: str, context_str: str, intent: str, history: list = []):
        """
        Yields tokens using rigid role separation.
        """
        if not self.llm:
            yield "System: Model not loaded."
            return

        # SHORT-CIRCUIT
        if not context_str or not context_str.strip() or "I don’t see sufficient data" in context_str:
            yield "I don’t see sufficient data to answer this question."
            return

        # 1. Construct Messages
        system_rules = """
1. Answer directly and naturally.
2. Use ONLY the 'Tool Data' provided. Do not invent data.
3. If data is missing, say so clearly.
4. No headings, no repetition.
5. Keep it short.
"""
        messages = [
            {"role": "system", "content": f"You are a helpful AI assistant.\nRULES:\n{system_rules}"},
            {"role": "tool", "content": context_str},
            {"role": "user", "content": query}
        ]

        # 2. Format
        prompt = self._format_chat_prompt(messages)

        # 3. Stream with Simple Echo Filter
        # The model sometimes echoes markers. We'll strip common ones from the start.
        buffer = ""
        started_output = False
        
        for chunk in self.llm.stream(prompt):
            if not started_output:
                buffer += chunk
                
                # If we accumulate too much without finding a marker, just yield it
                if len(buffer) > 200:
                    started_output = True
                    yield buffer
                    buffer = ""
                    continue
                
                # Check if we've passed the echo markers
                if "[/INST]" in buffer:
                    # Extract content after [/INST]
                    parts = buffer.split("[/INST]", 1)
                    if len(parts) > 1:
                        clean_output = parts[1].strip()
                        if clean_output:
                            yield clean_output
                    buffer = ""
                    started_output = True
                # If no markers found yet, keep buffering
            else:
                # Already past the echo phase, stream normally
                yield chunk