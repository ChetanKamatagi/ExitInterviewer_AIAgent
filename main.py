import json
import os
from audio.stt import speech_to_text
from audio.tts import text_to_speech
from llm.conversation import GroqConversationService
from llm.summarizer import GroqSummaryService

class ExitInterviewAgent:
    def __init__(self):
        self.base_questions = [
            "What is the primary reason for leaving the organization?",
            "How would you describe your overall experience with the company?",
            "What did you like most about working here?",
            "What could the company improve?",
            "How was your relationship with your manager and team?",
            "Would you recommend this company to others? Why or why not?"
        ]
        self.interview_data = {}
        self.current_question_index = 0
        
        # Initialize modular services
        self.conversation_service = GroqConversationService()
        self.summary_service = GroqSummaryService()

    def start_interview(self):
        intro_text = "Hello! Thank you for taking the time for this exit interview. I want this to be a safe space to share your thoughts."
        print("Agent: Hello! Thank you for taking the time for this exit interview. I want this to be a safe space to share your thoughts.\n")
        text_to_speech(intro_text)
        
        last_user_response = ""
        
        while self.current_question_index < len(self.base_questions):
            current_question = self.base_questions[self.current_question_index]
            
            # 1. STRONGER SKIPPING LOGIC (via Groq)
            if self.interview_data:
                if self.conversation_service.should_skip_question(self.interview_data, current_question):
                    print(f"[System: Agent realized you already addressed the topic of '{current_question}'. Skipping.]")
                    self.interview_data[current_question] = {"status": "Answered previously in conversation"}
                    self.current_question_index += 1
                    continue
            
            # 2. EMPATHETIC TRANSITION ENGINE (via Groq)
            if self.current_question_index == 0:
                agent_speech = current_question 
            else:
                agent_speech = self.conversation_service.generate_transition(last_user_response, current_question)

            print(f"Agent: {agent_speech}")
            text_to_speech(agent_speech)

            user_response = speech_to_text() or ""
            last_user_response = user_response 
            
            # 3. DYNAMIC FOLLOW-UP LOOP (via Groq)
            follow_ups = []
            follow_up_count = 0
            max_follow_ups = 2
            current_context = user_response

            while follow_up_count < max_follow_ups:
                llm_decision = self.conversation_service.generate_follow_up(current_question, current_context)
                
                if "NONE" in llm_decision.upper():
                    break 
                
                print(f"Agent (Follow-up): {llm_decision}")
                text_to_speech(llm_decision)

                follow_up_answer = speech_to_text() or ""
                
                follow_ups.append({
                    "ai_question": llm_decision,
                    "user_answer": follow_up_answer
                })
                
                current_context = follow_up_answer
                last_user_response = follow_up_answer
                follow_up_count += 1
            
            # Store the final data for this question
            self.interview_data[current_question] = {
                "primary_response": user_response,
                "follow_up_qa": follow_ups
            }
            
            self.current_question_index += 1
            print("-" * 40)
            
        self.finish_interview()

    def finish_interview(self):
        # Generate final sign-off (via Groq)
        final_message = self.conversation_service.generate_sign_off()
        
        print(f"\nAgent: {final_message}")
        text_to_speech(final_message)
        
        # Save raw data and trigger summary (via Gemini)
        self.save_data()
        self.generate_summary()

    def save_data(self):
        json_dir = os.path.join(os.path.dirname(__file__), "Json")
        os.makedirs(json_dir, exist_ok=True)
        filepath = os.path.join(json_dir, "exit_interview_data.json")
        with open(filepath, "w") as f:
            json.dump(self.interview_data, f, indent=4)
        print(f"\n[System: Data saved to {os.path.abspath(filepath)}. Compiling HR Report...]")

    def generate_summary(self):
        print(f"\n[System: Compiling HR Report...]")
        report_json = self.summary_service.generate_summary(self.interview_data)
        
        if report_json:
            json_dir = os.path.join(os.path.dirname(__file__), "Json")
            os.makedirs(json_dir, exist_ok=True)
            filepath = os.path.join(json_dir, "interview_summary.json")
            with open(filepath, "w") as f:
                json.dump(report_json, f, indent=4)
            print(f"[System: HR Executive Summary successfully saved to {os.path.abspath(filepath)}]")

if __name__ == "__main__":
    agent = ExitInterviewAgent()
    agent.start_interview()