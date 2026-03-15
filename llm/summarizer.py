import json
from groq import Groq
from config import config

SUMMARY_PROMPT_TEMPLATE = """You are an Expert HR Analyst. 
Review the following raw exit interview data captured from a departing employee:

{interview_data}

Task: Generate a concise Executive Summary of this exit interview.

You MUST output your response EXCLUSIVELY as a valid JSON object. Do not include any conversational text before or after the JSON. 
Use the exact following keys:
- "primary_reason_for_leaving"
- "key_positives"
- "areas_for_improvement"
- "overall_sentiment" """

class GroqSummaryService:
    def __init__(self):
        try:
            self.client = Groq(api_key=config.GROQ_API_KEY)
            self.primary_model = config.PRIMARY_MODEL
            self.fallback_models = config.FALLBACK_MODELS
        except Exception as e:
            print(f"[Error: Groq Init] {e}")
            self.client = None

    def _generate_with_fallback(self, messages, temperature=0):
        if not self.client:
            raise ValueError("Groq client is not initialized.")
            
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
                print(f"[Warning: LLM Summarization] Model '{model}' failed: {e}")
                continue
                
        raise RuntimeError("All LLM summarization attempts failed.")

    def generate_summary(self, interview_data):
        try:
            history_text = json.dumps(interview_data, indent=2)
            summary_prompt = SUMMARY_PROMPT_TEMPLATE.format(interview_data=history_text)
            
            report_text = self._generate_with_fallback(
                messages=[{"role": "user", "content": summary_prompt}],
                temperature=0,
            )
            
            if report_text.startswith("```json"):
                report_text = report_text.strip("```json").strip("```").strip()
            elif report_text.startswith("```"):
                report_text = report_text.strip("```").strip()
                
            return json.loads(report_text)
            
        except json.JSONDecodeError:
            print("\n[Error: JSON Parse] The AI did not return valid JSON.")
            return {
                "primary_reason_for_leaving": "Data parse error.",
                "key_positives": ["Data parse error."],
                "areas_for_improvement": ["Data parse error."],
                "overall_sentiment": "Data parse error."
            }
        except Exception as e:
            print(f"[Error: Summarization] {e}")
            return {
                "primary_reason_for_leaving": "System error.",
                "key_positives": ["System error."],
                "areas_for_improvement": ["System error."],
                "overall_sentiment": "System error."
            }