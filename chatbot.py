# What this file does?#What this file does?

# 1. Assumes that the data has already been scraped and embeddings generated using demo_scraper.py# 1. Assums that the data has already been scraped and embeddings generated using demo_scraper.py

# 2. Uses the embeddings from pgvector to development a RAG model# 2. Uses the embeddings from pgvector to development a RAG model

# 3. Uses OPENAI API key for the chatbot (4o-mini)# 3. Uses OPENAI API key for the chatbot (4o-mini)

# 4. The chatbot has to act as a student counselor. # 4. The chatbot has to act as a student counceller. 

# 5. The chatbot should be able to handle open ended queries and ask follow up questions about the user's preferences.# 5. The chatbot should be able to handel open ended queries and ask follow up questions about the user's preferences.

# 6. The chatbot should be able to provide information about the universities, courses, fees, accreditations, specializations, etc.# 6. The chatbot should be able to provide information about the universities, courses, fees, accreditations, specializations, etc.

# 7. The chatbot should be able to provide information about the brochures and other documents.# 7. The chatbot should be able to provide information about the brochures and other documents.

# 8. The chatbot should be able to recommend universities based on the user's preferences. (low fees, high placements, or any combination of them. The user should be able to specify their preferences in natural language)# 8. The chatbot should be able to reccomend universities based on the user's preferences. (low fees, high placements, or any combination of them. The user should be able to specify their preferences in natural language)

# 9. The chatbot should dynamically rank the universities based on the user's preferences and the information available in the embeddings.# 9. The chatbot should dynamically rank the universities based on the user's preferences and the information available in the embeddings.

# 10. The chatbot should be able to handle multi-turn conversations and maintain context.# 10. The chatbot should be able to handle multi-turn conversations and maintain context.

# 11. The chatbot should be able to provide pros and cons of each university and help the user make an informed decision.# 11. The chatbot should be able to provide pros and cons of each university and help the user make an informed decision.

# 12. The chatbot should be able to give reason for its recommendations.# 12. The chatbot should be able to give reason for its reccomendations.

# 13. The chatbot should be able to handle edge cases and provide appropriate responses.# 13. The chatbot should be able to handle edge cases and provide appropriate responses.

# Example usage:

import os# User: “I want to do MBA”

import json# Bot: “Great — which specialization are you aiming for (Finance / Marketing / Analytics / General)? Also do you have a rough budget or placement expectation?”

import uuid# User: “Finance, low fees, good placements”

import logging# Bot: then runs filter+retrieve+rank and returns top 5 with pros/cons and trade-offs, and asks “Do you prefer Indian providers or international?”
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
import pandas as pd
import numpy as np
from dataclasses import dataclass

# Database and AI imports
import psycopg2
from psycopg2.extras import RealDictCursor
from azure_embeddings import AzureEmbeddings
from openai import AzureOpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class University:
    """Data class for university information"""
    id: int
    name: str
    specialization: str
    fees_per_semester: float
    subsidy_cashback: str
    accreditations: str
    website: str
    landing_page_url: str
    brochure_url: str
    brochure_file_path: str
    raw_data: Dict
    alumni_status: bool = True
    review_rating: float = 0.0
    review_count: int = 0
    review_sentiment: Optional[List[str]] = None
    review_source: str = "Not Available"
    
    def __post_init__(self):
        if self.review_sentiment is None:
            self.review_sentiment = []

@dataclass
class SearchResult:
    """Data class for search results"""
    university: University
    similarity: float
    content_type: str
    content_source: str
    content_text: str
    reasons: List[str]

class MBAStudentCounselor:
    """
    Advanced MBA Student Counselor Chatbot using RAG (Retrieval-Augmented Generation)
    """
    
    def __init__(self):
        """Initialize the MBA counselor chatbot"""
        self.session_id = str(uuid.uuid4())
        self.conversation_history = []
        self.user_preferences = {}
        
        # Initialize components
        self._setup_database()
        self._setup_ai_models()
        self._setup_system_prompts()
        
        logger.info("MBA Student Counselor initialized successfully!")
    
    def _setup_database(self):
        """Setup database connection"""
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'mba_data'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD'),
            'port': int(os.getenv('DB_PORT', 5432))
        }
        
        # Test database connection
        try:
            conn = psycopg2.connect(**self.db_config)
            conn.close()
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    def _setup_ai_models(self):
        """Setup AI models (OpenAI and SentenceTransformers)"""
        # Azure OpenAI setup
        self.openai_client = AzureOpenAI(
            azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT'),
            api_key=os.getenv('AZURE_OPENAI_API_KEY'),
            api_version=os.getenv('AZURE_OPENAI_API_VERSION', '2024-12-01-preview')
        )
        self.deployment_name = os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4o')
        
        # Azure OpenAI Embeddings for query embedding
        self.embedding_model = AzureEmbeddings()
        
        logger.info("AI models setup completed (using Azure OpenAI Embeddings)")
    
    def _setup_system_prompts(self):
        """Setup system prompts for the chatbot"""
        self.system_prompt = """
You are a caring and experienced MBA Student Counselor named Alex. You genuinely care about helping students make the best decisions for their career and future. You are NOT a salesperson - you are a trusted advisor who wants what's best for each student.

PERSONALITY & APPROACH:
- Warm, empathetic, and genuinely interested in each student's success
- Professional but approachable - like a supportive mentor or older sibling
- Patient and understanding - students may be confused or overwhelmed
- Honest about both pros and cons - never oversell or hide downsides
- Never highlight online mode as a disadvantage (all courses are online anyway)
- Useful cons include limited international exposure, lacking hands-on experience, outdated curriculum, any negative student sentiment (from reviews), etc.
- High motivation, time management, strong commitment, self-motivated learning, self-discipline requirements are NOT cons - these are expected for any serious MBA student, NEVER mention these as cons
- cons must ONLY include considerations that are specific to each university/program, not general expectations of students.
- cons must NOT include high fees. ( Higher fees compared to other options MUST NEVER BE DISPLAYED) 
- Celebratory of their achievements and supportive during uncertainty
- Remember that choosing an MBA is a major life decision with financial implications

NATURAL CONVERSATION HANDLING:
- Respond naturally to greetings ("Hello!", "Thanks!", "Good morning!")
- Acknowledge gratitude warmly and continue being helpful
- Handle casual conversation while gently steering toward their goals
- Show genuine interest in their background and aspirations
- Use encouraging language: "That's great!", "I understand", "Let me help you with that"

KEY RESPONSIBILITIES:
1. Build rapport and understand the whole person, not just their MBA requirements
2. Listen actively and ask thoughtful follow-up questions
3. Provide honest, balanced information about universities and programs
4. Help students think through their priorities and trade-offs
5. Give clear reasoning for recommendations without being pushy
6. Support students in making informed decisions that align with their goals

CONVERSATION STYLE:
- Start with understanding their situation and goals, not immediately pushing programs
- Ask about their background, career aspirations, and what's driving their MBA interest
- Use conversational language: "I'd love to help you explore...", "Let's think about...", "What matters most to you?"
- Validate their concerns and choices
- Share relevant insights without overwhelming them with data
- End conversations by checking if they need more support

TONE GUIDELINES:
- Sound like a trusted advisor, not a sales representative
- Use "I'm here to help you find..." instead of "We have great programs that..."
- Focus on their needs: "What would work best for your situation?" 
- Be honest about limitations: "This might not be ideal if..." or "You should consider that..."
- Celebrate their progress: "That's a smart question!" or "You're thinking about this really well!"

RESPONSE LENGTH:
- Keep responses concise and conversational - aim for 2-3 sentences for simple questions
- When universities match their query, mention that you've found some great options
- Focus on guidance, encouragement, and next steps
- Be helpful and supportive in your tone

RESPONSE FORMAT FOR UNIVERSITY RECOMMENDATIONS:
When providing university recommendations, first provide your conversational response, then add a structured section with:

RECOMMENDATIONS:
```json
[
    {
        "name": "University Name",
        "specialization": "Finance/Marketing/Analytics/General", 
        "fees": "₹XX,XXX per semester",
        "accreditations": "AICTE, UGC, NAAC A+, ...",
        "alumni_status": true,
        "review_rating": 4.2,
        "review_count": 150,
        "review_sentiment": ["Positive point 1", "Positive point 2", "Consideration 1"],
        "review_source": "Google Reviews",
        "pros": ["Specific advantage 1", "Specific advantage 2", ..., "Specific advantage N"],
        "cons": ["Consideration 1", "Consideration 2", ..., "Consideration N"](DO NOT talk about high fees or problems with online mode in this section), 
        "reasons": ["Why this matches their needs 1", "Why this matches their needs 2", ..., "Why this matches their needs N"]
    }
]
```

IMPORTANT: Include as many pros, cons, and reasons as you feel are relevant and helpful. Don't limit yourself - provide comprehensive analysis.

This structured data will be extracted to create beautiful cards while your conversational text guides the student.

EDGE CASES:
- If a user asks about casual topics (e.g., weather, sports), respond briefly and steer back to MBA counseling.
- If a user asks about something that is not related to MBA counseling, politely inform them that you are specialized in MBA counseling and suggest they seek help elsewhere for that topic.
- If a user asks about a program outside the scope of the 20+ universities you have data on, inform them that you only have information on those universities and suggest they research other programs separately.
- If a user types a very short or vague message, ask a clarifying question to better understand their needs.
- If a user types gibberish or nonsense, respond politely asking them to clarify their message.
- If a user uses cuss words or offensive language, respond politely asking them to maintain a respectful tone.
- If a user expresses frustration or dissatisfaction, acknowledge their feelings and offer to help resolve their concerns.
- If a user expresses a desire to kill themselves or harm others, respond with empathy and provide resources for immediate help, while also informing them that you are not equipped to handle such situations.

Remember: You have detailed information about 20+ universities. Use this to provide personalized, honest guidance that truly serves the student's best interests.
Remember: Follow natural flow of the conversation. Dont repeat the things that are already said in past messages. Give the answers to specific queries, such as asking for a specific program, or asking for links, specifically.mimansajoshi04
"""

    def semantic_search(self, query: str, limit: int = 10, content_types: Optional[List[str]] = None) -> List[SearchResult]:
        """
        Perform semantic search on the embeddings database
        """
        try:
            # Create query embedding
            query_embedding = self.embedding_model.encode(query)
            
            # Build SQL query with content type filtering
            sql_query = """
                SELECT 
                    e.similarity,
                    e.content_type,
                    e.content_source,
                    e.content_text,
                    e.metadata,
                    u.id, u.name, u.specialization, u.fees_per_semester,
                    u.subsidy_cashback, u.accreditations, u.website,
                    u.landing_page_url, u.brochure_url, u.brochure_file_path,
                    u.raw_data, u.alumni_status, u.review_rating, u.review_count,
                    u.review_sentiment, u.review_source
                FROM (
                    SELECT *,
                           1 - (embedding <=> %s::vector) as similarity
                    FROM mba_embeddings
                    WHERE 1=1
            """
            
            params: List[Any] = [query_embedding.tolist()]
            
            # Add content type filtering if specified
            if content_types:
                sql_query += " AND content_type = ANY(%s)"
                params.append(content_types)
            
            sql_query += """
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                ) e
                JOIN universities u ON e.university_id = u.id
                ORDER BY e.similarity DESC;
            """
            
            params.append(query_embedding.tolist())
            params.append(limit)
            
            # Execute query
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(sql_query, params)
            results = cursor.fetchall()
            conn.close()
            
            # Convert to SearchResult objects
            search_results = []
            for row in results:
                university = University(
                    id=row['id'],
                    name=row['name'],
                    specialization=row['specialization'],
                    fees_per_semester=row['fees_per_semester'],
                    subsidy_cashback=row['subsidy_cashback'],
                    accreditations=row['accreditations'],
                    website=row['website'],
                    landing_page_url=row['landing_page_url'],
                    brochure_url=row['brochure_url'],
                    brochure_file_path=row['brochure_file_path'],
                    raw_data=row['raw_data'],
                    alumni_status=row.get('alumni_status', True),
                    review_rating=float(row.get('review_rating', 0.0)),
                    review_count=row.get('review_count', 0),
                    review_sentiment=row.get('review_sentiment', []),
                    review_source=row.get('review_source', 'Not Available')
                )
                
                search_results.append(SearchResult(
                    university=university,
                    similarity=row['similarity'],
                    content_type=row['content_type'],
                    content_source=row['content_source'],
                    content_text=row['content_text'],
                    reasons=[]  # Will be populated by ranking logic
                ))
            
            return search_results
            
        except Exception as e:
            logger.error(f"Semantic search error: {e}")
            return []
    
    def rank_universities(self, search_results: List[SearchResult], user_preferences: Dict) -> List[SearchResult]:
        """
        Rank universities based on user preferences
        """
        ranked_results = []
        
        for result in search_results:
            score = result.similarity  # Base semantic similarity score
            reasons = []
            
            university = result.university
            
            # Budget preference scoring
            if 'budget' in user_preferences:
                budget_pref = user_preferences['budget'].lower()
                fees = university.fees_per_semester or 0
                
                if 'low' in budget_pref or 'affordable' in budget_pref or 'cheap' in budget_pref:
                    if fees < 35000:  # Low fees
                        score += 0.3
                        reasons.append(f"Low fees (₹{fees:,.0f}/semester)")
                    elif fees < 45000:  # Medium fees
                        score += 0.1
                        reasons.append(f"Moderate fees (₹{fees:,.0f}/semester)")
                    else:
                        score -= 0.1
                        reasons.append(f"Higher fees (₹{fees:,.0f}/semester)")
                
                elif 'high' in budget_pref or 'premium' in budget_pref:
                    if fees > 50000:
                        score += 0.2
                        reasons.append(f"Premium program (₹{fees:,.0f}/semester)")
            
            # Specialization preference scoring
            if 'specialization' in user_preferences:
                spec_pref = user_preferences['specialization'].lower()
                uni_spec = (university.specialization or '').lower()
                
                if spec_pref in uni_spec or any(word in uni_spec for word in spec_pref.split()):
                    score += 0.4
                    reasons.append(f"Matches {university.specialization} specialization")
            
            # Accreditation preference scoring
            if 'accreditation' in user_preferences or any('accredit' in str(v).lower() for v in user_preferences.values()):
                accreditations = (university.accreditations or '').lower()
                if 'aicte' in accreditations:
                    score += 0.2
                    reasons.append("AICTE accredited")
                if 'ugc' in accreditations:
                    score += 0.15
                    reasons.append("UGC recognized")
                if 'naac a' in accreditations:
                    score += 0.25
                    reasons.append("NAAC A+ rated")
            
            # Subsidy/cashback bonus
            if university.subsidy_cashback:
                score += 0.1
                reasons.append(f"Offers cashback: {university.subsidy_cashback}")
            
            # Update result with new score and reasons
            result.similarity = score
            result.reasons = reasons
            ranked_results.append(result)
        
        # Sort by updated score
        ranked_results.sort(key=lambda x: x.similarity, reverse=True)
        
        # Remove duplicates (same university from different content sources)
        seen_universities = set()
        unique_results = []
        for result in ranked_results:
            if result.university.id not in seen_universities:
                seen_universities.add(result.university.id)
                unique_results.append(result)
        
        return unique_results
    
    def extract_preferences(self, user_message: str) -> Dict:
        """
        Extract user preferences from their message using AI
        """
        try:
            extraction_prompt = f"""
            Analyze this user message and extract their MBA preferences in JSON format:
            
            User message: "{user_message}"
            
            Extract and categorize these preferences:
            - specialization: (finance, marketing, analytics, hr, operations, general, etc.)
            - budget: (low/affordable, medium, high/premium, or specific amount)
            - career_goal: (their career aspirations)
            - priorities: (fees, placements, accreditation, ranking, etc.)
            - location_preference: (if mentioned)
            - experience_level: (fresher, experienced, years of experience)
            
            IMPORTANT: Return ONLY a valid JSON object with no additional text, explanations, or markdown formatting.
            Example: {{"specialization": "finance", "budget": "low"}}
            If nothing is mentioned, return: {{}}
            """
            
            response = self.openai_client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": "You are a preference extraction assistant. You must return ONLY valid JSON with no additional text or formatting. Never include markdown code blocks or explanations."},
                    {"role": "user", "content": extraction_prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            raw_response = response.choices[0].message.content
            if not raw_response:
                logger.warning("Empty response from OpenAI for preference extraction")
                return {}
                
            raw_response = raw_response.strip()
            
            # Clean the response - remove markdown code blocks if present
            if raw_response.startswith('```json'):
                raw_response = raw_response[7:]  # Remove ```json
            if raw_response.startswith('```'):
                raw_response = raw_response[3:]   # Remove ```
            if raw_response.endswith('```'):
                raw_response = raw_response[:-3]  # Remove trailing ```
            
            raw_response = raw_response.strip()
            
            # Try to parse the cleaned response
            try:
                preferences = json.loads(raw_response)
                if preferences:  # Only log if preferences were actually found
                    logger.info(f"Extracted preferences: {preferences}")
                return preferences
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse preferences as JSON. Raw response: '{raw_response[:200]}...' Error: {e}")
                
                # Try to extract preferences using basic text matching as fallback
                fallback_prefs = self._extract_preferences_fallback(user_message)
                if fallback_prefs:
                    logger.info(f"Using fallback extraction: {fallback_prefs}")
                return fallback_prefs
                
        except Exception as e:
            logger.error(f"Preference extraction error: {e}")
            return {}
    
    def _extract_preferences_fallback(self, user_message: str) -> Dict:
        """
        Fallback preference extraction using simple text matching
        """
        preferences = {}
        message_lower = user_message.lower()
        
        # Specialization detection
        specializations = ['finance', 'marketing', 'analytics', 'hr', 'human resource', 'operations', 'general', 'management']
        for spec in specializations:
            if spec in message_lower:
                preferences['specialization'] = spec
                break
        
        # Budget detection
        if any(word in message_lower for word in ['low', 'cheap', 'affordable', 'budget']):
            preferences['budget'] = 'low'
        elif any(word in message_lower for word in ['high', 'premium', 'expensive']):
            preferences['budget'] = 'high'
        
        # Priority detection
        priorities = []
        if any(word in message_lower for word in ['fees', 'cost', 'price', 'affordable']):
            priorities.append('fees')
        if any(word in message_lower for word in ['placement', 'job', 'career']):
            priorities.append('placements')
        if any(word in message_lower for word in ['accreditation', 'accredited', 'approved']):
            priorities.append('accreditation')
        
        if priorities:
            preferences['priorities'] = priorities
        
        return preferences
    
    def _is_casual_message(self, message: str) -> bool:
        """
        Detect if the message is a casual/social interaction rather than MBA-related query
        """
        message_lower = message.lower().strip()
        
        # Common greetings and social expressions
        casual_patterns = [
            # Greetings
            'hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening',
            # Thanks and appreciation
            'thank you', 'thanks', 'thank u', 'thx', 'appreciate', 'grateful',
            # Politeness
            'please', 'excuse me', 'sorry', 'pardon',
            # Farewells
            'bye', 'goodbye', 'see you', 'take care', 'have a good day',
            # General responses
            'ok', 'okay', 'alright', 'sure', 'yes', 'no', 'maybe',
            # Simple acknowledgments
            'i see', 'understood', 'got it', 'makes sense'
        ]
        
        # Check for exact matches or if message starts with these patterns
        for pattern in casual_patterns:
            if message_lower == pattern or message_lower.startswith(pattern + ' ') or message_lower.startswith(pattern + ','):
                return True
        
        # Check for very short messages that are likely casual
        if len(message_lower.split()) <= 2 and any(word in message_lower for word in casual_patterns):
            return True
        
        return False
    
    def _generate_casual_response(self, user_message: str, conversation_context: str = "") -> str:
        """
        Generate appropriate responses for casual/social messages
        """
        message_lower = user_message.lower().strip()
        
        # Thank you responses
        if any(word in message_lower for word in ['thank', 'thanks', 'thx', 'appreciate', 'grateful']):
            responses = [
                "You're very welcome! I'm so glad I could help you. Is there anything else about MBA programs you'd like to explore?",
                "I'm happy to help! That's what I'm here for. Do you have any other questions about your MBA journey?",
                "You're absolutely welcome! I really enjoy helping students find their perfect MBA program. Anything else I can assist with?",
                "My pleasure! I hope the information was useful. Feel free to ask if you want to dive deeper into any specific programs or topics."
            ]
            return responses[hash(message_lower) % len(responses)]
        
        # Greeting responses
        elif any(word in message_lower for word in ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening']):
            responses = [
                "Hello! It's wonderful to meet you. I'm Alex, and I'm here to help you navigate your MBA journey. What's bringing you to consider an MBA program?",
                "Hi there! I'm excited to help you explore MBA opportunities. Are you just starting to think about business school, or do you have some specific goals in mind?",
                "Good to see you! I'm here to support you in finding the right MBA program. What stage are you at in your career, and what's motivating you to consider an MBA?",
                "Hello! I'm thrilled to help you with your MBA search. Tell me a bit about yourself - what's driving your interest in pursuing an MBA?"
            ]
            return responses[hash(message_lower) % len(responses)]
        
        # Farewell responses
        elif any(word in message_lower for word in ['bye', 'goodbye', 'see you', 'take care']):
            responses = [
                "Take care, and best of luck with your MBA journey! Remember, I'm here whenever you need guidance. You've got this! 🎓",
                "Goodbye! I hope our conversation was helpful. Wishing you all the best as you explore your MBA options. Feel free to come back anytime!",
                "See you later! I'm confident you'll make a great choice. Remember to trust your instincts and choose what aligns with your goals. Good luck! 🌟"
            ]
            return responses[hash(message_lower) % len(responses)]
        
        # General acknowledgment responses
        else:
            responses = [
                "I'm glad we're connecting! How can I best support you in your MBA search today?",
                "Great! I'm here to help however I can. What aspects of MBA programs are you most curious about?",
                "Wonderful! I love helping students find their ideal path. What would you like to explore about MBA programs?",
                "Perfect! Let's dive in. What questions do you have about MBA programs or business schools?"
            ]
            return responses[hash(message_lower) % len(responses)]
    
    def generate_response(self, user_message: str, search_results: List[SearchResult], conversation_context: str = "") -> Dict[str, Any]:
        """
        Generate conversational response using OpenAI with structured university cards
        """
        try:
            logger.info(f"Generating response for query: {user_message}")
            logger.info(f"Found {len(search_results)} search results")
            
            # Prepare university information for AI to analyze
            universities_info = []
            for i, result in enumerate(search_results[:5], 1):  # Use top 5 for AI analysis
                uni = result.university
                formatted_fees = f"₹{uni.fees_per_semester:,.0f} per semester"
                logger.info(f"University {i}: {uni.name} - Raw fees: {uni.fees_per_semester} - Formatted: {formatted_fees}")
                
                universities_info.append({
                    "name": uni.name,
                    "specialization": uni.specialization,
                    "fees": formatted_fees,
                    "accreditations": uni.accreditations if uni.accreditations else "To be verified",
                    "website": uni.website if hasattr(uni, 'website') and uni.website else uni.landing_page_url if hasattr(uni, 'landing_page_url') else "#",
                    "brochure": uni.brochure_url if hasattr(uni, 'brochure_url') and uni.brochure_url else (uni.brochure_file_path if hasattr(uni, 'brochure_file_path') and uni.brochure_file_path else "#"),
                    "subsidy": uni.subsidy_cashback if hasattr(uni, 'subsidy_cashback') else "",
                    "alumni_status": uni.alumni_status if hasattr(uni, 'alumni_status') else True,
                    "review_rating": uni.review_rating if hasattr(uni, 'review_rating') else 0.0,
                    "review_count": uni.review_count if hasattr(uni, 'review_count') else 0,
                    "review_sentiment": uni.review_sentiment if hasattr(uni, 'review_sentiment') and uni.review_sentiment else [],
                    "review_source": uni.review_source if hasattr(uni, 'review_source') else "Not Available"
                })
            
            logger.info(f"Prepared {len(universities_info)} universities for AI analysis")
            
            context = "\n".join([f"{i+1}. {uni['name']} - {uni['specialization']} - {uni['fees']} - {uni['accreditations']}" 
                               for i, uni in enumerate(universities_info)])
            
            # Create prompt for AI to generate recommendations
            prompt = f"""
            As Alex, the MBA counselor, respond to the student's query in a natural, supportive way.
            
            Student's Message: "{user_message}"
            
            Available Universities:
            {context}
            
            Previous Conversation: {conversation_context}
            What I Know About This Student: {json.dumps(self.user_preferences, indent=2)}
            
            SPECIAL CONS GUIDANCE:
            - Useful cons include limited international exposure, lacking hands-on experience, outdated curriculum, any negative student sentiment (from reviews), etc.
            - High motivation, time management, strong commitment, self-motivated learning, self-discipline requirements are NOT cons - these are expected for any serious MBA student, NEVER mention these as cons
            - cons must ONLY include considerations that are specific to each university/program, not general expectations of students.
            - cons must NOT include high fees. ( Higher fees compared to other options MUST NEVER BE DISPLAYED) 
            
            Instructions:
            1. Provide a warm, conversational response (2-3 sentences)
            2. If universities match their needs, follow your response with structured recommendations
            3. Analyze each university thoroughly for pros, cons, and reasons
            4. Be honest and helpful in your assessment
            5. Always ask for specific preferences if not provided before providing recommendations
            
            Format exactly like this if providing recommendations:
            [Your conversational response here]
            
            RECOMMENDATIONS:
            ```json
            [
                {{
                    "name": "University Name",
                    "specialization": "Specialization",
                    "fees": "₹XX,XXX per semester", 
                    "accreditations": "Accreditations",
                    "alumni_status": true,
                    "review_rating": 4.2,
                    "review_count": 150,
                    "review_sentiment": ["Positive aspect 1", "Positive aspect 2", "Area for improvement"],
                    "review_source": "Google Reviews",
                    "pros": ["Advantage 1", "Advantage 2", "More advantages as needed"],
                    "cons": ["Consideration 1", "Consideration 2", "More considerations as needed"],
                    "reasons": ["Why this fits 1", "Why this fits 2", "More reasons as needed"]
                }}
            ]
            ```
            
            Note: Include as many pros, cons, and reasons as relevant. Don't limit to 2 items.
            CONS LOGIC: Never mention online mode issues (all courses are online). 
            - Useful cons include limited international exposure, lacking hands-on experience, outdated curriculum, any negative student sentiment (from reviews), etc.
            - High motivation, time management, strong commitment, self-motivated learning, self-discipline requirements are NOT cons - these are expected for any serious MBA student, NEVER mention these as cons
            - cons must ONLY include considerations that are specific to each university/program, not general expectations of students.
            - cons must NOT include high fees. ( Higher fees compared to other options MUST NEVER BE DISPLAYED) 
            The system will use accurate database fees regardless of what you specify in the JSON.
            """
            
            response = self.openai_client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=1500
            )
            
            content = response.choices[0].message.content
            logger.info(f"AI Response received: {content[:200]}..." if content else "Empty AI response")
            
            if not content:
                return {
                    "response": "I apologize, but I received an empty response. Could you please rephrase your question?",
                    "university_cards": [],
                    "has_recommendations": False
                }
            
            # Parse the response to extract conversational text and structured data
            university_cards = []
            conversational_response = content
            
            if "RECOMMENDATIONS:" in content:
                parts = content.split("RECOMMENDATIONS:")
                conversational_response = parts[0].strip()
                logger.info(f"Split response - Conversational: {conversational_response[:100]}...")
                logger.info(f"JSON section preview: {parts[1][:200]}..." if len(parts) > 1 else "No JSON section")
                
                try:
                    # Extract JSON from the recommendations section
                    json_section = parts[1].strip()
                    json_str = ""
                    if "```json" in json_section:
                        json_start = json_section.find("```json") + 7
                        json_end = json_section.find("```", json_start)
                        json_str = json_section[json_start:json_end].strip()
                        logger.info(f"Extracted JSON: {json_str}")
                        
                        ai_recommendations = json.loads(json_str)
                        logger.info(f"Parsed {len(ai_recommendations)} AI recommendations")
                        
                        # Match AI recommendations with our university data to add missing fields
                        for i, ai_rec in enumerate(ai_recommendations):
                            logger.info(f"Processing AI recommendation {i+1}: {ai_rec.get('name', 'Unknown')}")
                            
                            # Find matching university from search results - use more flexible matching
                            matching_uni = None
                            ai_name_lower = ai_rec["name"].lower()
                            
                            for uni_info in universities_info:
                                uni_name_lower = uni_info["name"].lower()
                                
                                # Exact match first
                                if ai_name_lower == uni_name_lower:
                                    matching_uni = uni_info
                                    logger.info(f"Exact match found: {uni_info['name']}")
                                    break
                                # Partial match if exact doesn't work
                                elif ai_name_lower in uni_name_lower or uni_name_lower in ai_name_lower:
                                    matching_uni = uni_info
                                    logger.info(f"Partial match found: {uni_info['name']}")
                                    break
                            
                            if matching_uni:
                                logger.info(f"Using fees from matching university: {matching_uni['fees']}")
                                university_card = {
                                    "name": ai_rec["name"],
                                    "specialization": ai_rec.get("specialization", matching_uni["specialization"]),
                                    "fees": matching_uni["fees"],  # Always use properly formatted database fees
                                    "accreditations": ai_rec.get("accreditations", matching_uni["accreditations"]),
                                    "website": matching_uni["website"],
                                    "brochure": matching_uni["brochure"],
                                    "alumni_status": matching_uni.get("alumni_status", True),
                                    "review_rating": matching_uni.get("review_rating", 0.0),
                                    "review_count": matching_uni.get("review_count", 0),
                                    "review_sentiment": matching_uni.get("review_sentiment", []),
                                    "review_source": matching_uni.get("review_source", "Not Available"),
                                    "pros": ai_rec.get("pros", ["Good option", "Established institution"]),
                                    "cons": ai_rec.get("cons", ["Requires dedication", "Online format"]),
                                    "reasons": ai_rec.get("reasons", ["Matches your requirements"])
                                }
                                university_cards.append(university_card)
                                logger.info(f"Created card for {ai_rec['name']} with fees: {university_card['fees']}")
                            else:
                                # Fallback if no match found - get original university data
                                logger.warning(f"No matching university found for AI recommendation: {ai_rec['name']}")
                                # Try to find it in search results directly
                                fallback_uni = None
                                for result in search_results[:5]:
                                    if ai_rec["name"].lower() in result.university.name.lower() or result.university.name.lower() in ai_rec["name"].lower():
                                        fallback_uni = result.university
                                        logger.info(f"Found fallback university: {fallback_uni.name}")
                                        break
                                
                                if fallback_uni:
                                    fallback_fees = f"₹{fallback_uni.fees_per_semester:,.0f} per semester"
                                    logger.info(f"Using fallback fees: {fallback_fees}")
                                    university_card = {
                                        "name": ai_rec["name"],
                                        "specialization": ai_rec.get("specialization", fallback_uni.specialization),
                                        "fees": fallback_fees,  # Format fees properly
                                        "accreditations": ai_rec.get("accreditations", fallback_uni.accreditations or "To be verified"),
                                        "website": fallback_uni.website if hasattr(fallback_uni, 'website') and fallback_uni.website else fallback_uni.landing_page_url if hasattr(fallback_uni, 'landing_page_url') else "#",
                                        "brochure": fallback_uni.brochure_url if hasattr(fallback_uni, 'brochure_url') and fallback_uni.brochure_url else (fallback_uni.brochure_file_path if hasattr(fallback_uni, 'brochure_file_path') and fallback_uni.brochure_file_path else "#"),
                                        "alumni_status": fallback_uni.alumni_status if hasattr(fallback_uni, 'alumni_status') else True,
                                        "review_rating": fallback_uni.review_rating if hasattr(fallback_uni, 'review_rating') else 0.0,
                                        "review_count": fallback_uni.review_count if hasattr(fallback_uni, 'review_count') else 0,
                                        "review_sentiment": fallback_uni.review_sentiment if hasattr(fallback_uni, 'review_sentiment') and fallback_uni.review_sentiment else [],
                                        "review_source": fallback_uni.review_source if hasattr(fallback_uni, 'review_source') else "Not Available",
                                        "pros": ai_rec.get("pros", ["Good option", "Established institution"]),
                                        "cons": ai_rec.get("cons", ["Requires dedication", "Online format"]),
                                        "reasons": ai_rec.get("reasons", ["Matches your requirements"])
                                    }
                                    university_cards.append(university_card)
                                    logger.info(f"Created fallback card for {ai_rec['name']} with fees: {fallback_fees}")
                                else:
                                    logger.error(f"Could not find any matching university for: {ai_rec['name']}")
                except (json.JSONDecodeError, KeyError, IndexError) as e:
                    logger.error(f"Failed to parse AI recommendations: {e}")
                    logger.error(f"Raw JSON section: {parts[1][:500]}..." if len(parts) > 1 else "No JSON section found")
                    # Fallback to empty cards if parsing fails
                    university_cards = []
            else:
                logger.info("No RECOMMENDATIONS section found in AI response")
            
            logger.info(f"Final response: {len(university_cards)} cards generated")
            for i, card in enumerate(university_cards):
                logger.info(f"Card {i+1}: {card['name']} - {card['fees']}")
            
            return {
                "response": conversational_response,
                "university_cards": university_cards,
                "has_recommendations": len(university_cards) > 0
            }
            
        except Exception as e:
            logger.error(f"Response generation error: {e}")
            return {
                "response": "I apologize, but I'm having trouble processing your request right now. Could you please rephrase your question?",
                "university_cards": [],
                "has_recommendations": False
            }
    
    def save_conversation(self, user_message: str, bot_response: str):
        """Save conversation to database for context maintenance"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO conversations (session_id, user_message, bot_response, context)
                VALUES (%s, %s, %s, %s)
            """, (
                self.session_id,
                user_message,
                bot_response,
                json.dumps(self.user_preferences)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error saving conversation: {e}")
    
    def get_conversation_context(self, limit: int = 5) -> str:
        """Get recent conversation context"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT user_message, bot_response 
                FROM conversations 
                WHERE session_id = %s 
                ORDER BY created_at DESC 
                LIMIT %s
            """, (self.session_id, limit))
            
            conversations = cursor.fetchall()
            conn.close()
            
            if not conversations:
                return ""
            
            context_parts = []
            for conv in reversed(conversations):  # Reverse to get chronological order
                context_parts.append(f"User: {conv['user_message']}")
                context_parts.append(f"Assistant: {conv['bot_response']}")
            
            return "\n".join(context_parts)
            
        except Exception as e:
            logger.error(f"Error getting conversation context: {e}")
            return ""
    
    def chat(self, user_message: str) -> Dict[str, Any]:
        """
        Main chat function - processes user input and returns structured response
        """
        try:
            logger.info(f"Processing user message: {user_message}")
            
            # Get conversation context first
            conversation_context = self.get_conversation_context()
            
            # Check if this is a casual/social message
            if self._is_casual_message(user_message):
                bot_response = self._generate_casual_response(user_message, conversation_context)
                
                # Save casual conversation too (but don't extract preferences)
                self.save_conversation(user_message, bot_response)
                
                # Add to conversation history
                self.conversation_history.append({
                    'user': user_message,
                    'bot': bot_response,
                    'timestamp': datetime.now().isoformat()
                })
                
                return {
                    "response": bot_response,
                    "university_cards": [],
                    "has_recommendations": False
                }
            
            # For MBA-related queries, proceed with full processing
            # Extract and update user preferences
            new_preferences = self.extract_preferences(user_message)
            self.user_preferences.update(new_preferences)
            
            # Perform semantic search
            search_results = self.semantic_search(user_message, limit=15)
            
            # Rank results based on user preferences
            ranked_results = self.rank_universities(search_results, self.user_preferences)
            
            # Generate structured response
            structured_response = self.generate_response(user_message, ranked_results, conversation_context)
            
            # Save conversation (just the text part)
            self.save_conversation(user_message, structured_response["response"])
            
            # Add to conversation history for this session
            self.conversation_history.append({
                'user': user_message,
                'bot': structured_response["response"],
                'timestamp': datetime.now().isoformat()
            })
            
            return structured_response
            
        except Exception as e:
            logger.error(f"Error in chat function: {e}")
            return {
                "response": "I apologize, but I encountered an issue while processing your request. Could you please try asking your question in a different way?",
                "university_cards": [],
                "has_recommendations": False
            }
    
    def reset_session(self):
        """Reset the current session"""
        self.session_id = str(uuid.uuid4())
        self.conversation_history = []
        self.user_preferences = {}
        logger.info("Session reset completed")

def main():
    """
    Main function to run the chatbot
    """
    print("🎓 Welcome to the MBA Student Counselor Chatbot!")
    print("I'm here to help you find the perfect MBA program.")
    print("Type 'quit' or 'exit' to end the conversation.")
    print("Type 'reset' to start a new session.")
    print("-" * 60)
    
    try:
        # Initialize chatbot
        counselor = MBAStudentCounselor()
        
        # Initial greeting
        initial_response = counselor.chat("Hello, I want to do an MBA")
        print(f"\n🤖 Counselor: {initial_response}\n")
        
        # Chat loop
        while True:
            user_input = input("🧑‍🎓 You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("\n🤖 Counselor: Thank you for using the MBA Counselor! Best of luck with your MBA journey! 🎓")
                break
            elif user_input.lower() == 'reset':
                counselor.reset_session()
                print("\n🔄 Session reset. Let's start fresh!")
                continue
            elif not user_input:
                continue
            
            # Get response from chatbot
            try:
                response = counselor.chat(user_input)
                print(f"\n🤖 Counselor: {response}\n")
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye! Hope I could help you with your MBA search!")
                break
            except Exception as e:
                print(f"\n❌ Error: {str(e)}")
                print("Please try asking your question in a different way.\n")
                
    except Exception as e:
        print(f"❌ Failed to initialize chatbot: {str(e)}")
        print("Please ensure:")
        print("1. PostgreSQL database is running with populated data")
        print("2. Environment variables are set correctly in .env file")
        print("3. Run populate_database.py first to setup the database")

if __name__ == "__main__":
    main()