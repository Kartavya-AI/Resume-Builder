from crewai import Agent, Task, Crew, Process
from crewai.tools import tool
from langchain_openai import ChatOpenAI
import os
import time
import logging
from typing import Dict, List, Optional
from tenacity import retry, stop_after_attempt, wait_exponential
from src.resume_builder.tools.custom_tool import (
    extract_contact_info,
    analyze_work_experience,
    extract_skills,
    extract_education,
    generate_professional_summary
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@tool
def validate_resume_content(resume_content: str) -> str:
    """
    Validate resume content for completeness and formatting.
    
    Args:
        resume_content: The resume content to validate
        
    Returns:
        Validation feedback or the content if valid
    """
    required_sections = ['contact', 'summary', 'experience', 'skills', 'education']
    content_lower = resume_content.lower()
    
    missing_sections = []
    for section in required_sections:
        if section not in content_lower:
            missing_sections.append(section)
    
    if missing_sections:
        return f"Resume is missing the following sections: {', '.join(missing_sections)}"
    
    return "Resume content is complete and well-formatted."

class ResumeBuilderCrew:
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        """
        Initialize the Resume Builder Crew with improved error handling.
        
        Args:
            api_key: OpenAI API key
            model: Model to use (default: gpt-3.5-turbo)
        """
        if not api_key:
            raise ValueError("OpenAI API key is required")
        
        os.environ['OPENAI_API_KEY'] = api_key
        
        # Test API key validity
        try:
            test_llm = ChatOpenAI(
                model_name=model,
                temperature=0.3,
                openai_api_key=api_key,
                request_timeout=30,
                max_retries=2
            )
            # Simple test call
            test_llm.invoke("Hello")
        except Exception as e:
            logger.error(f"API key validation failed: {str(e)}")
            raise ValueError("Invalid OpenAI API key or insufficient permissions")
        
        self.llm = ChatOpenAI(
            model_name=model,
            temperature=0.3,
            openai_api_key=api_key,
            request_timeout=60,
            max_retries=2
        )
        
        self.request_delay = 8  # Reduced delay
        self.max_retries = 2
    
    def create_agents(self):
        """Create the resume building agents with simplified configuration"""
        
        # Resume Content Analyst Agent
        content_analyst = Agent(
            role='Resume Content Analyst',
            goal='Analyze user information and extract key professional highlights',
            backstory="""You are an expert at analyzing career information and identifying 
            the most impactful achievements, skills, and experiences that should be highlighted 
            in a professional resume.""",
            tools=[extract_contact_info, analyze_work_experience, extract_skills, extract_education],
            llm=self.llm,
            verbose=True,
            max_iter=2,
            allow_delegation=False
        )
        
        # Resume Writer Agent
        resume_writer = Agent(
            role='Professional Resume Writer',
            goal='Create compelling, ATS-friendly resume content',
            backstory="""You are a certified professional resume writer with expertise in 
            crafting compelling bullet points and creating resumes that get interviews.""",
            tools=[generate_professional_summary],
            llm=self.llm,
            verbose=True,
            max_iter=2,
            allow_delegation=False
        )
        
        # Resume Formatter Agent
        resume_formatter = Agent(
            role='Resume Formatter',
            goal='Format the resume content into a clean, professional structure',
            backstory="""You are a document formatting specialist who ensures resumes are 
            well-structured, easy to read, and professionally presented.""",
            tools=[validate_resume_content],
            llm=self.llm,
            verbose=True,
            max_iter=1,
            allow_delegation=False
        )
        
        return content_analyst, resume_writer, resume_formatter
    
    def create_tasks(self, user_info: str, job_role: str, content_analyst, resume_writer, resume_formatter):
        """Create simplified tasks for resume building"""
        
        # Task 1: Analyze Content
        analyze_task = Task(
            description=f"""
            Analyze the user information for the target role: {job_role}
            
            Extract and organize:
            1. Contact information
            2. Professional experiences
            3. Relevant skills
            4. Educational background
            
            User Information:
            {user_info}
            
            Focus on information most relevant to: {job_role}
            """,
            expected_output="""Structured analysis with contact info, work experiences, skills, and education.""",
            agent=content_analyst
        )
        
        # Task 2: Write Resume Content
        write_task = Task(
            description=f"""
            Create professional resume content for a {job_role} position based on the analysis.
            
            Include:
            1. Professional summary (2-3 sentences)
            2. Work experience with bullet points
            3. Skills section
            4. Education section
            
            Use action verbs and quantifiable achievements where possible.
            """,
            expected_output="""Complete resume content with all sections properly formatted.""",
            agent=resume_writer,
            context=[analyze_task]
        )
        
        # Task 3: Format Resume
        format_task = Task(
            description="""
            Format the resume content into a clean, professional structure.
            
            Ensure:
            1. Clear section headers
            2. Consistent formatting
            3. Proper spacing
            4. ATS compatibility
            """,
            expected_output="""Final formatted resume ready for submission.""",
            agent=resume_formatter,
            context=[write_task]
        )
        
        return [analyze_task, write_task, format_task]
    
    def run(self, user_info: str, job_role: str = "Professional") -> str:
        """
        Run the resume building process with fallback handling
        
        Args:
            user_info: User's professional information
            job_role: Target job role for tailoring
            
        Returns:
            Final formatted resume content
        """
        try:
            logger.info("Starting resume building process...")
            
            # Create agents
            content_analyst, resume_writer, resume_formatter = self.create_agents()
            
            # Create tasks
            tasks = self.create_tasks(user_info, job_role, content_analyst, resume_writer, resume_formatter)
            
            # Create crew with conservative settings
            crew = Crew(
                agents=[content_analyst, resume_writer, resume_formatter],
                tasks=tasks,
                process=Process.sequential,
                verbose=True,
                max_rpm=3,  # Very conservative rate limiting
                memory=False  # Disable memory to avoid embedding issues
            )
            
            # Execute the crew
            logger.info("Executing crew...")
            result = crew.kickoff()
            
            logger.info("Resume building completed successfully!")
            return str(result)
            
        except Exception as e:
            logger.error(f"Error in resume building process: {str(e)}")
            logger.info("Attempting fallback resume creation...")
            return self._create_fallback_resume(user_info, job_role)
    
    def _create_fallback_resume(self, user_info: str, job_role: str) -> str:
        """Create a basic resume using tools directly when AI agents fail"""
        try:
            logger.info("Creating fallback resume...")
            
            # Extract information using tools directly
            contact_info = extract_contact_info._run(user_info)
            skills = extract_skills._run(user_info)
            experiences = analyze_work_experience._run(user_info)
            education = extract_education._run(user_info)
            
            # Generate professional summary
            professional_summary = generate_professional_summary._run(user_info, job_role)
            
            # Create basic resume structure
            resume_content = []
            
            # Contact Information
            resume_content.append("=" * 60)
            if contact_info.get('name'):
                resume_content.append(f"  {contact_info['name']}")
            resume_content.append("=" * 60)
            
            contact_line = []
            if contact_info.get('email'):
                contact_line.append(f"Email: {contact_info['email']}")
            if contact_info.get('phone'):
                contact_line.append(f"Phone: {contact_info['phone']}")
            if contact_line:
                resume_content.append(" | ".join(contact_line))
            
            if contact_info.get('linkedin'):
                resume_content.append(f"LinkedIn: {contact_info['linkedin']}")
            if contact_info.get('github'):
                resume_content.append(f"GitHub: {contact_info['github']}")
            
            resume_content.append("")
            
            # Professional Summary
            resume_content.append("PROFESSIONAL SUMMARY")
            resume_content.append("-" * 30)
            resume_content.append(professional_summary)
            resume_content.append("")
            
            # Skills
            if skills:
                resume_content.append("SKILLS")
                resume_content.append("-" * 30)
                # Group skills in rows of 4
                skill_rows = [skills[i:i+4] for i in range(0, len(skills), 4)]
                for row in skill_rows:
                    resume_content.append(" • ".join(row))
                resume_content.append("")
            
            # Work Experience
            if experiences:
                resume_content.append("WORK EXPERIENCE")
                resume_content.append("-" * 30)
                
                for exp in experiences:
                    if exp.get('position') and exp.get('company'):
                        resume_content.append(f"{exp['position']} | {exp['company']}")
                    elif exp.get('company'):
                        resume_content.append(f"{exp['company']}")
                    
                    if exp.get('duration'):
                        resume_content.append(f"Duration: {exp['duration']}")
                    
                    if exp.get('achievements'):
                        for achievement in exp['achievements'][:3]:  # Limit to 3 achievements
                            clean_achievement = achievement.strip('•-* ')
                            resume_content.append(f"  • {clean_achievement}")
                    
                    resume_content.append("")
            
            # Education
            if education:
                resume_content.append("EDUCATION")
                resume_content.append("-" * 30)
                
                for edu in education:
                    edu_line = []
                    if edu.get('degree'):
                        edu_line.append(edu['degree'])
                    if edu.get('institution'):
                        edu_line.append(edu['institution'])
                    if edu_line:
                        resume_content.append(" | ".join(edu_line))
                    
                    if edu.get('year'):
                        resume_content.append(f"Year: {edu['year']}")
                    if edu.get('gpa'):
                        resume_content.append(f"GPA: {edu['gpa']}")
                    
                    resume_content.append("")
            
            final_resume = "\n".join(resume_content)
            logger.info("Fallback resume created successfully!")
            return final_resume
            
        except Exception as e:
            logger.error(f"Error in fallback resume creation: {str(e)}")
            return f"""
RESUME GENERATION ERROR
=====================

An error occurred while generating your resume: {str(e)}

Please check:
1. Your OpenAI API key is valid and has sufficient credits
2. Your input data is properly formatted
3. Try using a simpler model like gpt-3.5-turbo

Raw user information provided:
{user_info}
"""