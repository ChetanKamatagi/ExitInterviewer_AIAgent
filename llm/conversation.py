import json
from groq import Groq
from config import config

class GroqConversationService:
    def __init__(self):
        # Initialize Groq client
        self.client = Groq(api_key=config.GROQ_API_KEY)
        self.primary_model = config.PRIMARY_MODEL
        self.fallback_models = config.FALLBACK_MODELS

    def _generate_with_fallback(self, messages, temperature=0.7):
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
                print(f"[Warning] LLM generation failed for model '{model}': {e}")
                continue
                
        # If all models fail, raise the last exception or a generic fallback
        raise RuntimeError("All LLM generation attempts failed across primary and fallback models.")
        
    def should_skip_question(self, interview_data, current_question):
        history_text = json.dumps(interview_data, indent=2)
        skip_prompt = f"""
        You are an HR Exit Interview Agent.
        Interview history so far:
        {history_text}
        
        The next scheduled question is: "{current_question}"
        
        Task: Analyze the history carefully. Did the employee ALREADY provide an answer that covers the core topic of this next question? 
        For example, if they already complained extensively about their manager, you do NOT need to ask about their manager again.
        Reply EXACTLY with "SKIP" if the topic is already covered, or "ASK" if it is new ground.
        """
        response_text = self._generate_with_fallback(
            messages=[{"role": "user", "content": skip_prompt}],
            temperature=0,
        )
        return "SKIP" in response_text.upper()

    def generate_transition(self, last_user_response, current_question):
        transition_prompt = f"""
        You are an empathetic HR Exit Interviewer.
        The employee just said: "{last_user_response}"
        The next mandatory question you MUST ask is: "{current_question}"
        
        Task: Write your exact next response. Acknowledge their last statement briefly and empathetically, then smoothly ask the mandatory question.
        """
        return self._generate_with_fallback(
            messages=[{"role": "user", "content": transition_prompt}],
            temperature=0.7,
        )

    def generate_follow_up(self, current_question, current_context):
        follow_up_prompt = f"""
        You are an HR Exit Interviewer. 
        Original Question Context: "{current_question}"
        The employee just said: "{current_context}"
        
        Task: Decide if a follow-up is TRULY necessary.
        - If the employee gives a short, closed answer (e.g., "Yes", "Good", "Nothing"), seems annoyed, or says let's move on, reply EXACTLY with "NONE".
        - If the answer is clear and complete, reply EXACTLY with "NONE".
        - If the original question has multiple parts (like "Why or why not?") and the user ignored a part, generate ONE short, polite follow-up to get that missing information.
        - ONLY if the answer is highly ambiguous but introduces an important new topic, generate ONE short, polite follow-up question.
        """
        return self._generate_with_fallback(
            messages=[{"role": "user", "content": follow_up_prompt}],
            temperature=0.7,
        )

    def generate_sign_off(self):
        sign_off_prompt = """
        You are an empathetic HR Exit Interviewer. The interview has just successfully concluded.
        Task: Write a warm, professional, and human-sounding closing statement. 
        Thank the employee for their time, their honesty, and wish them the absolute best in their future endeavors. Keep it to about 2-3 sentences.
        """
        return self._generate_with_fallback(
            messages=[{"role": "user", "content": sign_off_prompt}],
            temperature=0.7,
        )
