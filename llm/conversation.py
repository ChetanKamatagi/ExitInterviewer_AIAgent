import json
from groq import Groq
from config import config

SKIP_PROMPT = """You are an incredibly observant HR Exit Interview Agent.
Interview history:
{history_text}

Next mandatory question: "{current_question}"

Task: Read the history carefully. Has the employee ALREADY provided enough information to answer the core topic of this next question?
CRITICAL RULES:
1. Connect the dots! If the next question is about their manager, and they ALREADY complained about their manager earlier, output "SKIP".
2. If the next question is about their overall experience, and they already gave a summary of their experience, output "SKIP".
3. ONLY output "ASK" if the topic is completely untouched.
4. Output EXACTLY the word "SKIP" or "ASK" and absolutely nothing else."""


TRANSITION_PROMPT = """You are an empathetic HR Exit Interviewer.
Employee said: "{last_user_response}"
Next mandatory question: "{current_question}"

Task: Acknowledge their statement naturally, then smoothly ask the next mandatory question.
CRITICAL RULES:
1. NEVER repeat generic, robotic HR phrases like "Your input is valued," "Thank you for your feedback," or "I have noted your comment."
2. Vary your acknowledgments! React directly to what they said (e.g., say "I understand," "That makes sense," "I'm glad you had that experience," or just transition directly into the question without an acknowledgment if it flows better).
3. Output exactly 1 to 2 sentences. Keep it extremely brief and human-sounding."""


FOLLOW_UP_PROMPT = """You are an HR Exit Interviewer. 
Original Question: "{current_question}"
Discussion so far on this topic:
{current_context}

Task: Determine if a follow-up is necessary based on the conversation history.
CRITICAL RULES:
1. DIG DEEPER IF NEEDED: Ask ONE brief follow-up question if the employee mentions issues (e.g. manager, toxicity, workload) but hasn't fully elaborated, or if their answer is vague or incomplete. Be conversational, natural, and directly reference what they just said. Do not ask for information they have already provided.
2. DEFAULT TO NONE IF SATISFIED: If the employee has provided enough detail or reason, output EXACTLY the word "NONE". Do NOT ask repetitive questions.
3. STRICT FORMAT: Output ONLY the follow-up question or the word "NONE". No reasoning, no filler text, and no preambles."""

REPEAT_CHECK_PROMPT = """The user just said: "{user_input}"
Task: Is the user asking you to repeat the question, asking what you said, or saying they didn't hear you?
Reply EXACTLY with "YES" if they want you to repeat, or "NO" if they are answering the question or saying something else."""

SIGN_OFF_PROMPT = """You are an HR Exit Interviewer. The interview has concluded.
Task: Write a warm, professional closing statement. 
CRITICAL RULE: Max 3 sentences. Output only the statement."""


class GroqConversationService:
    def __init__(self):
        try:
            self.client = Groq(api_key=config.GROQ_API_KEY)
            self.primary_model = config.PRIMARY_MODEL
            self.fallback_models = config.FALLBACK_MODELS
        except Exception:
            self.client = None

    def _generate_with_fallback(self, messages, temperature):
        if not self.client:
            return "NONE"
            
        models_to_try = [self.primary_model] + self.fallback_models
        
        for model in models_to_try:
            try:
                response = self.client.chat.completions.create(
                    messages=messages,
                    model=model,
                    temperature=temperature,
                )
                return response.choices[0].message.content.strip()
            except Exception:
                continue
                
        return "NONE"

    def should_skip_question(self, interview_data, current_question):
        try:
            history_text = json.dumps(interview_data, indent=2)
            skip_prompt = SKIP_PROMPT.format(
                history_text=history_text,
                current_question=current_question
            )
            
            response_text = self._generate_with_fallback(
                messages=[{"role": "user", "content": skip_prompt}],
                temperature=config.TEMP_DETERMINISTIC,
            )
            return "SKIP" in response_text.upper()
        except Exception:
            return False
    
    def is_repeat_request(self, user_input):
        if not user_input:
            return False
            
        text = user_input.lower()
        
        repeat_phrases = [
            "repeat", "say that again", "come again", "pardon", 
            "what was that", "didn't hear", "didn't get", "once again"
        ]
        
        return any(phrase in text for phrase in repeat_phrases)

    def generate_transition(self, last_user_response, current_question):
        try:
            transition_prompt = TRANSITION_PROMPT.format(
                last_user_response=last_user_response,
                current_question=current_question
            )
            
            response_text = self._generate_with_fallback(
                messages=[{"role": "user", "content": transition_prompt}],
                temperature=config.TEMP_DEFAULT,
            )
            return response_text if response_text != "NONE" else current_question
        except Exception:
            return current_question

    def generate_follow_up(self, current_question, current_context, follow_ups=None):
        try:
            context_str = f"Employee's Initial Answer: {current_context}\n"
            if follow_ups:
                for i, fu in enumerate(follow_ups):
                    context_str += f"Follow-up {i+1} Question: {fu['ai_question']}\n"
                    if fu.get('user_answer'):
                        context_str += f"Employee's Answer: {fu['user_answer']}\n"

            follow_up_prompt = FOLLOW_UP_PROMPT.format(
                current_question=current_question,
                current_context=context_str
            )
            
            return self._generate_with_fallback(
                messages=[{"role": "user", "content": follow_up_prompt}],
                temperature=config.TEMP_STRICT, 
            )
        except Exception:
            return "NONE"

    def generate_sign_off(self):
        try:
            response_text = self._generate_with_fallback(
                messages=[{"role": "user", "content": SIGN_OFF_PROMPT}],
                temperature=config.TEMP_DEFAULT,
            )
            return response_text if response_text != "NONE" else "Thank you for your time. We wish you the best in your future endeavors."
        except Exception:
            return "Thank you for your time. We wish you the best in your future endeavors."
