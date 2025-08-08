import json
import google.generativeai as genai
from typing import List
from config.settings import settings
from schemas.ai import QuestionGenerationRequest, GeneratedQuestion, GeneratedChoice, QuestionGenerationResponse

class AIService:
    def __init__(self):
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
        else:
            self.model = None
        
    
    def generate_questions(self, topic:str,difficulty:str,count:str) -> list:
        """Generate questions using AI"""
        if not self.model:
            raise ValueError("Gemini API key not configured")
        
        try:
            # Create prompt for question generation
            prompt = self._create_question_prompt(topic,difficulty,count)
            
            # Generate response
            response = self.model.generate_content(prompt)
            
            # Parse response
            questions = self._parse_ai_response(response.text,topic, difficulty)
            
            return questions
            
        except Exception as e:
            raise Exception(f"Failed to generate questions: {str(e)}")
        


    def _create_question_prompt(self,topic:str,difficulty:str,count:int) -> str:
        """Create a prompt for question generation"""
        prompt = f"""
        Generate {count} multiple choice questions about "{topic}" with {difficulty} difficulty level.
        
        Requirements:
        - topic: {topic}
        - Difficulty: {difficulty}
        - Number of questions: {count}
        - Each question should have exactly 4 choices
        - Only one choice should be correct
        - Questions should be educational and accurate
        
        Return the response in the following JSON format:
        [
            {{
                "question_text": "Question here?",
                "topic": "{topic}",
                "level": "{difficulty}",
                "choices": [
                    {{"choice_text": "Option A", "is_correct": false}},
                    {{"choice_text": "Option B", "is_correct": true}},
                    {{"choice_text": "Option C", "is_correct": false}},
                    {{"choice_text": "Option D", "is_correct": false}}
                ]
            }}
        ]
        
        Make sure the questions are appropriate for the specified difficulty level and topic.
        """
        return prompt
    
    def _parse_ai_response(self, response_text: str, topic: str, difficulty: str) -> List[GeneratedQuestion]:
        """Parse the AI response into structured data"""
        try:
            # Clean the response text
            cleaned_text = response_text.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]
            
            # Parse JSON
            questions_data = json.loads(cleaned_text)
            
            # Convert to GeneratedQuestion objects
            questions = []
            for q_data in questions_data:
                choices = [
                    GeneratedChoice(
                        choice_text=choice["choice_text"],
                        is_correct=choice["is_correct"]
                    )
                    for choice in q_data["choices"]
                ]
                
                question = GeneratedQuestion(
                    question_text=q_data["question_text"],
                    topic=q_data.get("topic", topic),
                    level=q_data.get("level", difficulty),
                    choices=choices
                )
                questions.append(question)
            
            return questions
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse AI response: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error processing AI response: {str(e)}")
    
    def generate_question_variations(self, topic: str, difficulty: str = "medium", count: int = 5) -> List[GeneratedQuestion]:
        """Generate question variations for a topic"""
        request = QuestionGenerationRequest(
            topic=topic,
            difficulty=difficulty,
            count=count
        )
        
        response = self.generate_questions(request)
        return response.questions