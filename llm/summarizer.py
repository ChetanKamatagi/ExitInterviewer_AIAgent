import json
from groq import Groq
from config import config

class GroqSummaryService:
    def __init__(self):
        self.client = Groq(api_key=config.GROQ_API_KEY)
        self.primary_model = config.PRIMARY_MODEL
        self.fallback_models = config.FALLBACK_MODELS

    def _generate_with_fallback(self, messages, temperature=0):
        """Attempts to generate content with the primary model, falling back if it fails."""
        models_to_try = [self.primary_model] + self.fallback_models
        
        for model in models_to_try:
            try:
                response = self.client.chat.completions.create(
                    messages=messages,
                    model=model,
                    temperature=temperature,
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                print(f"[Warning] Summarization failed for model '{model}': {e}")
                continue
                
        raise RuntimeError("All LLM summarization attempts failed across primary and fallback models.")

    def generate_summary(self, interview_data):
        summary_prompt = f"""
        You are an Expert HR Analyst. 
        Review the following raw exit interview data captured from a departing employee:
        
        {json.dumps(interview_data, indent=2)}
        
        Task: Generate a concise Executive Summary of this exit interview.
        
        You MUST output your response EXCLUSIVELY as a valid JSON object. Do not include any conversational text before or after the JSON. 
        Use the exact following keys:
        - "primary_reason_for_leaving"
        - "key_positives"
        - "areas_for_improvement"
        - "overall_sentiment"
        """
        
        report_text = self._generate_with_fallback(
            messages=[{"role": "user", "content": summary_prompt}],
            temperature=0,
        )
        
        # Clean up the response in case the LLM adds markdown formatting
        if report_text.startswith("```json"):
            report_text = report_text.strip("```json").strip("```").strip()
        elif report_text.startswith("```"):
            report_text = report_text.strip("```").strip()
            
        try:
            return json.loads(report_text)
        except json.JSONDecodeError:
            print("\n[Error] The AI did not return valid JSON. Here is the raw output instead:")
            print(report_text)
            return None
