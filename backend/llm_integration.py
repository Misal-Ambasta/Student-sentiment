import os
import enum
from typing import Dict, List, Any, Optional, Union, Callable
from loguru import logger
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.schema import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq

class LLMProvider(enum.Enum):
    GEMINI = "gemini"
    GROQ = "groq"
    OPENAI = "openai"

class MultiLLMManager:
    def __init__(self):
        # Initialize API keys from environment variables
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        
        # Initialize LLM models
        self.llm_models = {}
        self._init_llm_models()
        
        # Initialize RAG templates
        self.rag_templates = {}
        self._init_rag_templates()
        
        logger.info("LLM Manager initialized successfully")
    
    def _init_llm_models(self):
        """Initialize LLM models"""
        try:
            # Initialize Gemini model
            if self.google_api_key:
                self.llm_models[LLMProvider.GEMINI] = ChatGoogleGenerativeAI(
                    model="gemini-1.5-flash",
                    google_api_key=self.google_api_key,
                    temperature=0.7,
                    max_output_tokens=2048
                )
                logger.info("Gemini model initialized")
            else:
                logger.warning("Google API key not found, Gemini model not initialized")
            
            # Initialize Groq model
            if self.groq_api_key:
                self.llm_models[LLMProvider.GROQ] = ChatGroq(
                    model="llama3-70b-8192",
                    api_key=self.groq_api_key,
                    temperature=0.7,
                    top_p=0.95,
                    max_tokens=2048,
                    streaming=True
                )
                logger.info("Groq model initialized")
            else:
                logger.warning("Groq API key not found, Groq model not initialized")
            
            # Initialize OpenAI model
            if self.openai_api_key:
                self.llm_models[LLMProvider.OPENAI] = ChatOpenAI(
                    model="gpt-4o",
                    api_key=self.openai_api_key,
                    temperature=0.7,
                    top_p=0.95,
                    max_tokens=2048,
                    streaming=True
                )
                logger.info("OpenAI model initialized")
            else:
                logger.warning("OpenAI API key not found, OpenAI model not initialized")
        except Exception as e:
            logger.error(f"Error initializing LLM models: {e}")
            raise
    
    def _init_rag_templates(self):
        """Initialize RAG templates"""
        try:
            # Student analysis template
            student_analysis_template = """
            You are an expert educational analyst tasked with providing insights about student performance and satisfaction.
            
            Use the following context information to provide a detailed analysis about the student:
            
            {context}
            
            Based on the above context, please provide a comprehensive analysis addressing the following aspects:
            1. Overall satisfaction level and trends over time
            2. Key strengths and areas of improvement in the student's experience
            3. Specific recommendations for instructors and support staff
            4. Risk assessment for potential dropout or disengagement
            5. Suggested interventions to improve student experience
            
            Current question: {question}
            """
            
            self.rag_templates["student_analysis"] = PromptTemplate(
                template=student_analysis_template,
                input_variables=["context", "question"]
            )
            
            # General RAG template
            general_rag_template = """
            You are an AI assistant for an educational platform. Use the following pieces of context to answer the question at the end.
            If you don't know the answer, just say that you don't know, don't try to make up an answer.
            
            {context}
            
            Question: {question}
            """
            
            self.rag_templates["general"] = PromptTemplate(
                template=general_rag_template,
                input_variables=["context", "question"]
            )
            
            # Summarization template
            summarization_template = """
            You are an expert data analyst tasked with summarizing educational survey data.
            
            Use the following documents to create a comprehensive summary:
            
            {context}
            
            Provide a detailed summary that includes:
            1. Key trends and patterns in the data
            2. Notable insights about student satisfaction
            3. Areas of strength and opportunities for improvement
            4. Recommendations based on the data
            
            Summary request: {question}
            """
            
            self.rag_templates["summarization"] = PromptTemplate(
                template=summarization_template,
                input_variables=["context", "question"]
            )
            
            # Individual Student Analysis template
            individual_analysis_template = """
            You are an expert educational analyst. Analyze the provided student data and return a structured JSON response.
            
            Context: {context}
            Question: {question}
            
            Return ONLY a valid JSON object in this exact format:
            {{
              "type": "individual_analysis",
              "content": "👤 STUDENT PROFILE: [student_id]\nDemographic: [demographic] | Grade: [grade] | Attendance: [attendance]%\n\nJourney Overview:\n• Overall NPS: [score]/10 → '[comment]'\n• Course A Performance: [analysis]\n• Course B Performance: [analysis]\n• CSBT Readiness: [analysis]\n• Support Systems: [analysis]\n\n📊 DETAILED ASPECT BREAKDOWN:\nCourse A: [detailed scores]\nCourse B: [detailed scores]\nCSBT: [detailed scores]\nSupport: [detailed scores]\n\n🧠 HISTORICAL COMPARISON:\nFound [number] similar [demographic] patterns:\n• [success rate]% successfully complete program\n• [placement rate]% achieve job placement within 3 months\n• Typical challenge: [challenge]\n• Risk Level: [level] ([dropout probability]% dropout probability)\n\n💡 RECOMMENDED ACTIONS:\n• [action 1]\n• [action 2]\n• [action 3]\n• [action 4]",
              "student_id": "[extracted_student_id]",
              "risk_level": "[very_low|low|medium|high|very_high]",
              "aspect_scores": {{}},
              "recommended_actions": []
            }}
            """
            
            self.rag_templates["individual_analysis"] = PromptTemplate(
                template=individual_analysis_template,
                input_variables=["context", "question"]
            )
            
            # Weekly Report template
            weekly_report_template = """
            You are an expert educational analyst. Generate a comprehensive weekly report based on the provided data.
            
            Context: {context}
            Question: {question}
            
            Return ONLY a valid JSON object in this exact format:
            {{
              "type": "weekly_report",
              "content": "📊 NPS Intelligence Report - Week Ending [Date]\n════════════════════════════════════════════\n📈 OVERALL METRICS\nCurrent NPS: [score] (↓[change] from last week) ⚠\nPromoters: [%]% | Passives: [%]% | Detractors: [%]%\nResponse Rate: [%]%\nData Richness: 20+ aspects analyzed per student\n\n🧠 INSIGHTS FROM PAST COHORTS\nThis Week [number] dip happened in [%]% of previous batches\n• Course A→B transition challenges: [%]% of students affected\n• CSBT readiness concerns: [%]% mention career preparation anxiety\n• Teams that acted now: [%]% recovered\n• Teams that waited: Only [%]% recovered\n• What worked best: [interventions]\n\n📚 ASPECT-SPECIFIC ANALYSIS\nCourse A Performance:\n• Lecture Experience: [score]/10 (↑[change])\n• Instructor Delivery: [score]/10 (stable)\n• Sherpa Support: [score]/10 (↓[change]) ⚠\n\nCourse B Performance:\n• Lecture Experience: [score]/10 (↓[change]) ⚠\n• Content Complexity Jump: [%]% mention difficulty\n• Historical Pattern: Normal Week [range] challenge\n\nCSBT Readiness:\n• Curriculum Design: [score]/10 (↑[change])\n• Career Preparation Anxiety: [%]% express concerns\n• Job Market Readiness: [%]% feel underprepared\n\n...[continue with full analysis]",
              "metadata": {{
                "confidence_score": 0.92,
                "data_sources": ["comprehensive_survey", "historical_cohorts", "aspect_analysis"],
                "aspects_analyzed": 20,
                "response_richness": "high",
                "generated_at": "[timestamp]"
              }}
            }}
            """
            
            self.rag_templates["weekly_report"] = PromptTemplate(
                template=weekly_report_template,
                input_variables=["context", "question"]
            )
            
            # Segmentation Analysis template
            segmentation_analysis_template = """
            You are an expert educational analyst. Perform demographic segmentation analysis based on the provided data.
            
            Context: {context}
            Question: {question}
            
            IMPORTANT: When calculating course averages, use the following approach:
            - Course A Average: Calculate from all Course A related ratings (columns 5-9 in survey data: Lecture experience, Instructor content delivery, Sherpa Support, Ask & Learn Hour effectiveness, PP session)
            - Course B Average: Calculate from all Course B related ratings (columns 10-14 in survey data: Lecture Experience, Instructor content delivery, Course B Sherpa Support, Ask & Learn Hour effectiveness, PP Session)
            - CSBT Average: Calculate from all CSBT related ratings (columns 15-17 in survey data: CSBT Curriculum design, CSBT Instructor support, CSBT Support)
            
            If any course section has no data or all values are empty/null, display "N/A" for that course average.
            
            Return ONLY a valid JSON object in this exact format:
            {{
              "type": "segmentation_analysis",
              "content": "📊 COMPREHENSIVE DEMOGRAPHIC ANALYSIS\n\nWorking Professionals (n=[count] in sample)\n• Average Overall NPS: [score]\n• Course A Average: [score]/5 ([description])\n• Course B Average: [score]/5 ([description])\n• CSBT Average: [score]/5 ([description])\n• Main Challenge: [challenge] (mentioned in [%]% of feedback)\n• Support Needs: [needs]\n• Historical Success Rate: [%]% with targeted interventions\n\nFresh Graduates (n=[count] in sample)\n• Average Overall NPS: [score] ([description])\n• Course A Average: [score]/5 ([description])\n• Course B Average: [score]/5 ([description])\n• CSBT Average: [score]/5 ([description])\n• Strength: [strengths]\n• Challenge: [challenges]\n• Historical Success Rate: [%]% completion, [%]% placement\n\nCareer Switchers (n=[count] in sample)\n• Average Overall NPS: [score]\n• Course A Average: [score]/5 ([description])\n• Course B Average: [score]/5 ([description])\n• CSBT Average: [score]/5 ([description])\n• Main Need: [needs]\n• Support Focus: [focus]\n• Historical Success Rate: [%]% with mentorship support\n\n🎯 TARGETED RECOMMENDATIONS:\nWorking Professionals: [recommendations]\nFresh Graduates: [recommendations]\nCareer Switchers: [recommendations]",
              "segments": {{}}
            }}
            """
            
            self.rag_templates["segmentation_analysis"] = PromptTemplate(
                template=segmentation_analysis_template,
                input_variables=["context", "question"]
            )
            
            # Aspect Analysis template
            aspect_analysis_template = """
            You are an expert educational analyst. Perform detailed aspect-specific analysis based on the provided data.
            
            Context: {context}
            Question: {question}
            
            Return ONLY a valid JSON object in this exact format:
            {{
              "type": "aspect_analysis",
              "content": "📚 [ASPECT NAME] ANALYSIS\n\nCurrent Performance: [score]/5 average (↓[change] from last period)\n\n🔍 DETAILED BREAKDOWN:\nFresh Graduates: [score]/5 - [description]\nWorking Professionals: [score]/5 - [description]\nCareer Switchers: [score]/5 - [description]\n\n📋 FEEDBACK THEMES:\n• Positive ([%]%): '[themes]'\n• Concerns ([%]%): '[themes]'\n\n🧠 HISTORICAL CONTEXT:\n[Aspect] typically [pattern] in Week [range] as [reason]\n• Similar pattern in [%]% of past cohorts\n• Recovery strategies that worked:\n  - [strategy 1] (improved scores by [amount] points)\n  - [strategy 2] ([%]% positive response)\n  - [strategy 3]: [%]% satisfaction\n\n💡 RECOMMENDED INTERVENTIONS:\n1. [intervention 1]\n2. [intervention 2]\n3. [intervention 3]\nExpected Impact: +[amount] point improvement within [timeframe]",
              "aspect": "[aspect_name]",
              "current_score": 0.0,
              "trend": "[improving|stable|declining]",
              "interventions": []
            }}
            """
            
            self.rag_templates["aspect_analysis"] = PromptTemplate(
                template=aspect_analysis_template,
                input_variables=["context", "question"]
            )
            
            logger.info("RAG templates initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing RAG templates: {e}")
            raise
    
    def get_langchain_llm(self, preferred_provider: Optional[LLMProvider] = None):
        """Get LangChain LLM model with fallback mechanism"""
        try:
            # If preferred provider is specified and available, use it
            if preferred_provider and preferred_provider in self.llm_models:
                return self.llm_models[preferred_provider]
            
            # Otherwise, try providers in order: Gemini -> Groq -> OpenAI
            provider_order = [LLMProvider.GEMINI, LLMProvider.GROQ, LLMProvider.OPENAI]
            
            for provider in provider_order:
                if provider in self.llm_models:
                    return self.llm_models[provider]
            
            # If no providers are available, raise an exception
            raise ValueError("No LLM providers available")
        except Exception as e:
            logger.error(f"Error getting LangChain LLM: {e}")
            raise
    
    async def rag_chat_response(
        self,
        question: str,
        documents: List[Document],
        template_type: str = "general",
        preferred_provider: Optional[LLMProvider] = None,
        streaming_callback: Optional[Callable[[str], None]] = None
    ) -> str:
        """Generate a response using RAG"""
        try:
            # Get LLM model
            llm = self.get_langchain_llm(preferred_provider)
            
            # Get template
            if template_type not in self.rag_templates:
                template_type = "general"
            
            template = self.rag_templates[template_type]
            
            # Format documents into context string
            context = "\n\n".join([doc.page_content for doc in documents])
            
            # Create RAG chain
            chain = (
                {"context": lambda _: context, "question": RunnablePassthrough()}
                | template
                | llm
                | StrOutputParser()
            )
            
            # Generate response
            if streaming_callback:
                response = ""
                async for chunk in chain.astream(question):
                    response += chunk
                    streaming_callback(chunk)
                return response
            else:
                return await chain.ainvoke(question)
        except Exception as e:
            logger.error(f"Error generating RAG response: {e}")
            raise
    
    async def summarize_documents(
        self,
        documents: List[Document],
        question: str = "Summarize these documents",
        preferred_provider: Optional[LLMProvider] = None
    ) -> str:
        """Summarize a collection of documents"""
        try:
            return await self.rag_chat_response(
                question=question,
                documents=documents,
                template_type="summarization",
                preferred_provider=preferred_provider
            )
        except Exception as e:
            logger.error(f"Error summarizing documents: {e}")
            raise
    
    async def generate_response(
        self,
        prompt: str,
        preferred_provider: Optional[LLMProvider] = None,
        streaming_callback: Optional[Callable[[str], None]] = None
    ) -> str:
        """Generate a response using a simple prompt"""
        try:
            # Get LLM model
            llm = self.get_langchain_llm(preferred_provider)
            
            # Create chain
            chain = llm | StrOutputParser()
            
            # Generate response
            if streaming_callback:
                response = ""
                async for chunk in chain.astream(prompt):
                    response += chunk
                    streaming_callback(chunk)
                return response
            else:
                return await chain.ainvoke(prompt)
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise

# Singleton instance
_llm_manager = None

def get_llm_manager() -> MultiLLMManager:
    global _llm_manager
    if _llm_manager is None:
        _llm_manager = MultiLLMManager()
    return _llm_manager