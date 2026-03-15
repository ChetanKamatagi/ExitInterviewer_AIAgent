import json
import os
import sys
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
        
        try:
            self.conversation_service = GroqConversationService()
            self.summary_service = GroqSummaryService()
        except Exception as e:
            print(f"[Critical Error] Failed to initialize AI services. Check your API keys: {e}")
            sys.exit(1)

    def start_interview(self):
        intro_text = "Hello! Thank you for taking the time for this exit interview. I want this to be a safe space to share your thoughts."
        print(intro_text)
        text_to_speech(intro_text)
        
        last_user_response = ""
        
        while self.current_question_index < len(self.base_questions):
            try:
                current_question = self.base_questions[self.current_question_index]
                
                if self.interview_data:
                    if self.conversation_service.should_skip_question(self.interview_data, current_question):
                        print(f"[System: Agent realized you already addressed the topic of '{current_question}'. Skipping.]")
                        self.interview_data[current_question] = {"status": "Answered previously in conversation"}
                        self.current_question_index += 1
                        continue
                
                if self.current_question_index == 0:
                    agent_speech = current_question 
                else:
                    agent_speech = self.conversation_service.generate_transition(last_user_response, current_question)

                print(f"Agent: {agent_speech}")
                text_to_speech(agent_speech)

                user_response = speech_to_text() or ""

                audio_retries = 0
                max_retries = 3

                while not user_response.strip() and audio_retries < max_retries:
                    clarify_text = "I'm sorry, I didn't quite catch that. Could you please try again?"
                    print(f"Agent: {clarify_text}")
                    text_to_speech(clarify_text)
                    user_response = speech_to_text() or ""
                    audio_retries += 1

                if not user_response.strip():
                    print("[System: Maximum audio retries reached. Skipping to the next question.]")
                    self.interview_data[current_question] = {
                        "primary_response": "No audio detected.",
                        "follow_up_qa": []
                    }
                    self.current_question_index += 1
                    continue
                
                while self.conversation_service.is_repeat_request(user_response):
                    print(f"Agent (Repeating): {agent_speech}")
                    text_to_speech(agent_speech)
                    user_response = speech_to_text() or ""

                    audio_retries = 0
                    while not user_response.strip() and audio_retries < max_retries:
                        clarify_text = "I'm sorry, I didn't quite catch that. Could you please try again?"
                        print(f"Agent: {clarify_text}")
                        text_to_speech(clarify_text)
                        user_response = speech_to_text() or ""
                        audio_retries += 1

                    if not user_response.strip():
                        break
                
                if not user_response.strip():
                    print("[System: Maximum audio retries reached. Skipping to the next question.]")
                    self.interview_data[current_question] = {
                        "primary_response": "No audio detected.",
                        "follow_up_qa": []
                    }
                    self.current_question_index += 1
                    continue
                    
                last_user_response = user_response 
                
                follow_ups = []
                follow_up_count = 0
                max_follow_ups = 2
                current_context = user_response
                last_asked_question = current_question

                while follow_up_count < max_follow_ups:
                    llm_decision = self.conversation_service.generate_follow_up(last_asked_question, current_context)
                    
                    if "NONE" in llm_decision.upper():
                        break 
                    
                    print(f"Agent (Follow-up): {llm_decision}")
                    text_to_speech(llm_decision)

                    follow_up_answer = speech_to_text() or ""

                    follow_up_retries = 0
                    while not follow_up_answer.strip() and follow_up_retries < max_retries:
                        clarify_text = "I'm sorry, I didn't quite catch that. Could you please try again?"
                        print(f"Agent: {clarify_text}")
                        text_to_speech(clarify_text)
                        follow_up_answer = speech_to_text() or ""
                        follow_up_retries += 1

                    if not follow_up_answer.strip():
                        print("[System: Audio failed during follow-up. Moving on.]")
                        break
                    
                    while self.conversation_service.is_repeat_request(follow_up_answer):
                        print(f"Agent (Repeating): {llm_decision}")
                        text_to_speech(llm_decision)
                        follow_up_answer = speech_to_text() or ""

                        follow_up_retries = 0
                        while not follow_up_answer.strip() and follow_up_retries < max_retries:
                            clarify_text = "I'm sorry, I didn't quite catch that. Could you please try again?"
                            print(f"Agent: {clarify_text}")
                            text_to_speech(clarify_text)
                            follow_up_answer = speech_to_text() or ""
                            follow_up_retries += 1

                        if not follow_up_answer.strip():
                            break

                    if not follow_up_answer.strip():
                        break
                    
                    follow_ups.append({
                        "ai_question": llm_decision,
                        "user_answer": follow_up_answer
                    })
                    
                    current_context = follow_up_answer
                    last_user_response = follow_up_answer
                    last_asked_question = llm_decision 
                    follow_up_count += 1
                
                self.interview_data[current_question] = {
                    "primary_response": user_response,
                    "follow_up_qa": follow_ups
                }
                
                self.current_question_index += 1
                print("-" * 40)
                
            except Exception as e:
                print(f"[Error] Something went wrong while processing this question: {e}")
                print("[System: Attempting to recover and move to the next question...]")
                self.current_question_index += 1
                
        self.finish_interview()

    def finish_interview(self):
        try:
            final_message = self.conversation_service.generate_sign_off()
            print(f"\nAgent: {final_message}")
            text_to_speech(final_message)
        except Exception as e:
            print(f"\n[Error] Failed to generate AI sign-off message: {e}")
        
        self.save_data()
        self.generate_summary()

    def save_data(self):
        try:
            json_dir = os.path.join(os.path.dirname(__file__), "Json")
            os.makedirs(json_dir, exist_ok=True)
            filepath = os.path.join(json_dir, "exit_interview_data.json")
            with open(filepath, "w") as f:
                json.dump(self.interview_data, f, indent=4)
            print(f"\n[System: Data saved to {os.path.abspath(filepath)}. Compiling HR Report...]")
        except OSError as e:
            print(f"\n[Error] Could not save the raw interview data to your drive: {e}")

    def generate_summary(self):
        print(f"\n[System: Compiling HR Report...]")
        try:
            report_json = self.summary_service.generate_summary(self.interview_data)
            
            if report_json:
                json_dir = os.path.join(os.path.dirname(__file__), "Json")
                os.makedirs(json_dir, exist_ok=True)
                filepath = os.path.join(json_dir, "interview_summary.json")
                with open(filepath, "w") as f:
                    json.dump(report_json, f, indent=4)
                print(f"[System: HR Executive Summary successfully saved to {os.path.abspath(filepath)}]")
        except Exception as e:
            print(f"[Error] Failed to generate or save the final HR summary: {e}")

if __name__ == "__main__":
    try:
        agent = ExitInterviewAgent()
        agent.start_interview()
    except KeyboardInterrupt:
        print("\n\n[System: Interview forcibly terminated by user. Exiting safely.]")
        sys.exit(0)
    except Exception as e:
        print(f"\n[Critical Error] The application crashed unexpectedly: {e}")