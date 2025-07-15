from crewai.tools import BaseTool
import re
from typing import Dict, List, Optional, Type
import logging
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContactInfoInput(BaseModel):
    text: str = Field(..., description="Raw text containing contact information")

class ContactInfoTool(BaseTool):
    name: str = "extract_contact_info"
    description: str = "Extract contact information from raw text with improved patterns"
    args_schema: Type[BaseModel] = ContactInfoInput
    
    def _run(self, text: str) -> Dict[str, str]:
        """Extract contact information from raw text."""
        try:
            contact_info = {
                'name': '',
                'email': '',
                'phone': '',
                'address': '',
                'linkedin': '',
                'github': ''
            }
            
            # Extract email
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            email_match = re.search(email_pattern, text, re.IGNORECASE)
            if email_match:
                contact_info['email'] = email_match.group()
            
            # Extract phone number
            phone_patterns = [
                r'(\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
                r'(\+?\d{1,3}[-.\s]?)?\(?\d{3,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{4}',
                r'(\+?\d{1,3}[-.\s]?)?\d{10}',
            ]
            
            for pattern in phone_patterns:
                phone_match = re.search(pattern, text)
                if phone_match:
                    contact_info['phone'] = phone_match.group()
                    break
            
            # Extract LinkedIn
            linkedin_pattern = r'linkedin\.com/in/[\w-]+'
            linkedin_match = re.search(linkedin_pattern, text, re.IGNORECASE)
            if linkedin_match:
                contact_info['linkedin'] = linkedin_match.group()
            
            # Extract GitHub
            github_pattern = r'github\.com/[\w-]+'
            github_match = re.search(github_pattern, text, re.IGNORECASE)
            if github_match:
                contact_info['github'] = github_match.group()
            
            # Extract name
            lines = text.strip().split('\n')
            for line in lines[:10]:
                line = line.strip()
                if line and not re.search(r'[@\d]|\.com|\.org|\.net', line):
                    if len(line.split()) >= 2 and len(line.split()) <= 4:
                        words = line.split()
                        if all(word[0].isupper() for word in words if word):
                            contact_info['name'] = line
                            break
            
            # Extract address
            address_patterns = [
                r'\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd)',
                r'[A-Za-z\s]+,\s*[A-Za-z\s]+\s+\d{5}',
            ]
            
            for pattern in address_patterns:
                address_match = re.search(pattern, text, re.IGNORECASE)
                if address_match:
                    contact_info['address'] = address_match.group()
                    break
            
            return contact_info
            
        except Exception as e:
            logger.error(f"Error extracting contact info: {str(e)}")
            return {
                'name': '',
                'email': '',
                'phone': '',
                'address': '',
                'linkedin': '',
                'github': ''
            }

class ExperienceInput(BaseModel):
    text: str = Field(..., description="Raw text containing work experience")

class ExperienceTool(BaseTool):
    name: str = "analyze_work_experience"
    description: str = "Analyze and structure work experience from raw text"
    args_schema: Type[BaseModel] = ExperienceInput
    
    def _run(self, text: str) -> List[Dict[str, str]]:
        """Analyze and structure work experience from raw text."""
        try:
            experiences = []
            
            experience_headers = [
                'work experience', 'professional experience', 'employment history',
                'career history', 'employment', 'experience', 'work history',
                'professional background', 'career'
            ]
            
            text_lower = text.lower()
            experience_section = ""
            
            for header in experience_headers:
                if header in text_lower:
                    start_idx = text_lower.find(header)
                    next_sections = ['education', 'skills', 'projects', 'certifications', 'awards']
                    end_idx = len(text)
                    
                    for next_section in next_sections:
                        section_idx = text_lower.find(next_section, start_idx + len(header))
                        if section_idx != -1:
                            end_idx = min(end_idx, section_idx)
                    
                    experience_section = text[start_idx:end_idx]
                    break
            
            if not experience_section:
                experience_section = text
            
            company_patterns = [
                r'at\s+[A-Za-z][A-Za-z\s&.,]+(?:Inc|Corp|LLC|Ltd|Company|Co\.|Technologies|Tech|Solutions|Systems|Group|Associates|Partners)',
                r'[A-Za-z][A-Za-z\s&.,]+(?:Inc|Corp|LLC|Ltd|Company|Co\.|Technologies|Tech|Solutions|Systems|Group|Associates|Partners)',
                r'[A-Za-z][A-Za-z\s&.,]+\s*-\s*[A-Za-z][A-Za-z\s]+'
            ]
            
            lines = experience_section.split('\n')
            current_experience = {}
            
            for i, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue
                
                for pattern in company_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        if current_experience:
                            experiences.append(current_experience)
                        
                        current_experience = {
                            'company': line,
                            'position': '',
                            'duration': '',
                            'description': '',
                            'achievements': []
                        }
                        
                        if i > 0:
                            prev_line = lines[i-1].strip()
                            if prev_line and not re.search(r'\d{4}', prev_line):
                                current_experience['position'] = prev_line
                        
                        break
                
                date_pattern = r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)?\s*\d{4}\s*[-–]\s*(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)?\s*\d{4}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)?\s*\d{4}\s*[-–]\s*Present'
                if re.search(date_pattern, line, re.IGNORECASE):
                    if current_experience:
                        current_experience['duration'] = line
                
                if line.startswith('•') or line.startswith('-') or line.startswith('*'):
                    if current_experience:
                        current_experience['achievements'].append(line)
                        current_experience['description'] += line + '\n'
            
            if current_experience:
                experiences.append(current_experience)
            
            return experiences
            
        except Exception as e:
            logger.error(f"Error analyzing work experience: {str(e)}")
            return []

class SkillsInput(BaseModel):
    text: str = Field(..., description="Raw text containing skills information")

class SkillsTool(BaseTool):
    name: str = "extract_skills"
    description: str = "Extract skills from raw text with improved categorization"
    args_schema: Type[BaseModel] = SkillsInput
    
    def _run(self, text: str) -> List[str]:
        """Extract skills from raw text."""
        try:
            skills = {
                'technical': [],
                'programming': [],
                'soft': [],
                'tools': [],
                'other': []
            }
            
            skill_headers = [
                'skills', 'technical skills', 'core competencies', 'technologies',
                'programming languages', 'tools', 'software', 'expertise',
                'proficiencies', 'qualifications'
            ]
            
            text_lower = text.lower()
            skills_section = ""
            
            for header in skill_headers:
                if header in text_lower:
                    start_idx = text_lower.find(header)
                    next_sections = ['experience', 'education', 'projects', 'certifications']
                    end_idx = len(text)
                    
                    for next_section in next_sections:
                        section_idx = text_lower.find(next_section, start_idx + len(header))
                        if section_idx != -1:
                            end_idx = min(end_idx, section_idx)
                    
                    skills_section = text[start_idx:end_idx]
                    break
            
            if not skills_section:
                skills_section = text
            
            programming_languages = [
                'python', 'javascript', 'java', 'c++', 'c#', 'c', 'ruby', 'php',
                'go', 'rust', 'swift', 'kotlin', 'scala', 'r', 'matlab', 'sql',
                'html', 'css', 'typescript', 'dart', 'perl', 'bash', 'powershell'
            ]
            
            frameworks_tools = [
                'react', 'angular', 'vue', 'django', 'flask', 'spring', 'nodejs',
                'express', 'laravel', 'rails', 'docker', 'kubernetes', 'aws',
                'azure', 'gcp', 'git', 'jenkins', 'terraform', 'ansible'
            ]
            
            soft_skills = [
                'leadership', 'communication', 'teamwork', 'problem solving',
                'analytical', 'creative', 'adaptable', 'organized', 'detail-oriented',
                'collaborative', 'innovative', 'strategic', 'mentoring'
            ]
            
            lines = skills_section.split('\n')
            for line in lines:
                line = line.strip()
                if not line or any(header in line.lower() for header in skill_headers):
                    continue
                
                skill_items = re.split(r'[,;|•·\n]', line)
                
                for item in skill_items:
                    item = item.strip()
                    if len(item) > 1:
                        item_lower = item.lower()
                        
                        if item_lower in programming_languages:
                            skills['programming'].append(item)
                        elif item_lower in frameworks_tools:
                            skills['tools'].append(item)
                        elif item_lower in soft_skills:
                            skills['soft'].append(item)
                        elif any(tech in item_lower for tech in ['web', 'mobile', 'database', 'cloud', 'api']):
                            skills['technical'].append(item)
                        else:
                            skills['other'].append(item)
            
            all_skills = []
            for category, skill_list in skills.items():
                all_skills.extend(list(set(skill_list)))
            
            return list(set(all_skills))
            
        except Exception as e:
            logger.error(f"Error extracting skills: {str(e)}")
            return []

class EducationInput(BaseModel):
    text: str = Field(..., description="Raw text containing education information")

class EducationTool(BaseTool):
    name: str = "extract_education"
    description: str = "Extract education information from raw text"
    args_schema: Type[BaseModel] = EducationInput
    
    def _run(self, text: str) -> List[Dict[str, str]]:
        """Extract education information from raw text."""
        try:
            education = []
            
            education_headers = [
                'education', 'academic background', 'qualifications', 'degrees',
                'academic qualifications', 'educational background'
            ]
            
            text_lower = text.lower()
            education_section = ""
            
            for header in education_headers:
                if header in text_lower:
                    start_idx = text_lower.find(header)
                    next_sections = ['experience', 'skills', 'projects', 'certifications']
                    end_idx = len(text)
                    
                    for next_section in next_sections:
                        section_idx = text_lower.find(next_section, start_idx + len(header))
                        if section_idx != -1:
                            end_idx = min(end_idx, section_idx)
                    
                    education_section = text[start_idx:end_idx]
                    break
            
            if not education_section:
                education_section = text
            
            degree_patterns = [
                r'(?:bachelor|master|phd|doctorate|associate|diploma|certificate)(?:\s+of\s+(?:science|arts|engineering|business|fine arts))?(?:\s+in\s+[\w\s]+)?',
                r'b\.?[sa]\.?(?:\s+in\s+[\w\s]+)?',
                r'm\.?[sa]\.?(?:\s+in\s+[\w\s]+)?',
                r'ph\.?d\.?(?:\s+in\s+[\w\s]+)?',
                r'(?:bs|ba|ms|ma|mba|phd)(?:\s+in\s+[\w\s]+)?'
            ]
            
            institution_patterns = [
                r'(?:university|college|institute|school)(?:\s+of\s+[\w\s]+)?',
                r'[\w\s]+(?:university|college|institute|school)',
                r'[\w\s]+(?:tech|technological|polytechnic)'
            ]
            
            lines = education_section.split('\n')
            current_education = {}
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                for pattern in degree_patterns:
                    degree_match = re.search(pattern, line, re.IGNORECASE)
                    if degree_match:
                        if current_education:
                            education.append(current_education)
                        
                        current_education = {
                            'degree': degree_match.group(),
                            'institution': '',
                            'year': '',
                            'gpa': '',
                            'location': '',
                            'description': line
                        }
                        break
                
                for pattern in institution_patterns:
                    institution_match = re.search(pattern, line, re.IGNORECASE)
                    if institution_match:
                        if current_education:
                            current_education['institution'] = institution_match.group()
                        else:
                            current_education = {
                                'degree': '',
                                'institution': institution_match.group(),
                                'year': '',
                                'gpa': '',
                                'location': '',
                                'description': line
                            }
                        break
                
                year_match = re.search(r'(?:graduated|class of|received)?\s*(19|20)\d{2}', line, re.IGNORECASE)
                if year_match:
                    if current_education:
                        current_education['year'] = year_match.group(1)
                
                gpa_match = re.search(r'gpa:?\s*(\d+\.?\d*)', line, re.IGNORECASE)
                if gpa_match:
                    if current_education:
                        current_education['gpa'] = gpa_match.group(1)
            
            if current_education:
                education.append(current_education)
            
            return education
            
        except Exception as e:
            logger.error(f"Error extracting education: {str(e)}")
            return []

class SummaryInput(BaseModel):
    user_info: str = Field(..., description="Raw text containing user's background information")
    target_role: str = Field(..., description="The role or position the user is targeting")
    years_exp: Optional[int] = Field(None, description="Optional years of experience to emphasize")

class SummaryTool(BaseTool):
    name: str = "generate_professional_summary"
    description: str = "Generate a professional summary based on user information and target role"
    args_schema: Type[BaseModel] = SummaryInput
    
    def _run(self, user_info: str, target_role: str, years_exp: Optional[int] = None) -> str:
        """Generate professional summary based on user information and target role."""
        try:
            # Initialize other tools
            contact_tool = ContactInfoTool()
            skills_tool = SkillsTool()
            experience_tool = ExperienceTool()
            education_tool = EducationTool()
            
            # Extract information
            contact_info = contact_tool._run(user_info)
            skills = skills_tool._run(user_info)
            experience = experience_tool._run(user_info)
            education = education_tool._run(user_info)
            
            # Determine experience level
            if years_exp is None:
                current_year = 2024
                years_exp = 0
                
                for exp in experience:
                    if exp.get('duration'):
                        years_in_duration = re.findall(r'(19|20)\d{2}', exp['duration'])
                        if len(years_in_duration) >= 2:
                            start_year = int(years_in_duration[0])
                            end_year = int(years_in_duration[-1]) if 'present' not in exp['duration'].lower() else current_year
                            years_exp += (end_year - start_year)
            
            # Determine level
            if years_exp == 0:
                level = "Entry-level"
            elif years_exp <= 3:
                level = "Junior"
            elif years_exp <= 7:
                level = "Mid-level"
            elif years_exp <= 12:
                level = "Senior"
            else:
                level = "Executive"
            
            # Extract relevant skills
            role_lower = target_role.lower()
            relevant_skills = []
            
            role_skill_mapping = {
                'software': ['python', 'javascript', 'java', 'react', 'nodejs', 'sql', 'git', 'aws'],
                'data': ['python', 'sql', 'machine learning', 'analytics', 'statistics', 'pandas', 'numpy'],
                'marketing': ['digital marketing', 'seo', 'social media', 'analytics', 'content creation'],
                'product': ['product management', 'agile', 'scrum', 'user experience', 'analytics'],
                'sales': ['sales', 'crm', 'negotiation', 'communication', 'relationship building'],
                'design': ['ui/ux', 'figma', 'adobe', 'prototyping', 'user research'],
                'finance': ['financial analysis', 'excel', 'modeling', 'accounting', 'budgeting'],
                'project': ['project management', 'agile', 'scrum', 'leadership', 'communication']
            }
            
            for role_key, role_skills in role_skill_mapping.items():
                if role_key in role_lower:
                    relevant_skills.extend([skill for skill in skills if any(rs in skill.lower() for rs in role_skills)])
                    break
            
            if not relevant_skills:
                relevant_skills = skills[:6]
            
            # Generate opening
            opening_templates = {
                "Entry-level": f"Recent graduate and aspiring {target_role} with strong foundational knowledge",
                "Junior": f"Motivated {target_role} with {years_exp} years of experience",
                "Mid-level": f"Experienced {target_role} with {years_exp} years of proven expertise",
                "Senior": f"Senior {target_role} with {years_exp}+ years of comprehensive experience",
                "Executive": f"Executive-level {target_role} with {years_exp}+ years of strategic leadership"
            }
            
            opening = opening_templates.get(level, f"Skilled {target_role} with extensive experience")
            
            # Skills text
            skills_text = ""
            if relevant_skills:
                skills_list = relevant_skills[:5]
                if len(skills_list) > 1:
                    skills_text = f" Proficient in {', '.join(skills_list[:-1])}, and {skills_list[-1]}."
                else:
                    skills_text = f" Skilled in {skills_list[0]}."
            
            # Experience text
            experience_text = ""
            if experience:
                recent_achievements = []
                for exp in experience[:2]:
                    if exp.get('achievements'):
                        recent_achievements.extend(exp['achievements'][:1])
                
                if recent_achievements:
                    clean_achievements = [achievement.strip('•-* ') for achievement in recent_achievements]
                    experience_text = f" Demonstrated success in {clean_achievements[0].lower()}"
                    if len(clean_achievements) > 1:
                        experience_text += f" and {clean_achievements[1].lower()}"
                    experience_text += "."
            
            # Education text
            education_text = ""
            if education:
                latest_edu = education[0]
                degree = latest_edu.get('degree', '')
                institution = latest_edu.get('institution', '')
                if degree and institution:
                    education_text = f" Holds {degree} from {institution}."
            
            # Value proposition
            value_prop_templates = {
                "Entry-level": "Eager to contribute fresh perspectives and technical skills to drive innovation and growth.",
                "Junior": "Committed to delivering high-quality results and contributing to team success.",
                "Mid-level": "Proven ability to lead projects and mentor junior team members while delivering measurable results.",
                "Senior": "Expert in driving strategic initiatives and leading cross-functional teams to achieve organizational goals.",
                "Executive": "Visionary leader with a track record of transforming organizations and driving sustainable growth."
            }
            
            value_prop = value_prop_templates.get(level, "Dedicated to delivering exceptional results and driving continuous improvement.")
            
            # Combine all parts
            summary = f"{opening}.{skills_text}{experience_text}{education_text} {value_prop}"
            summary = re.sub(r'\s+', ' ', summary).strip()
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating professional summary: {str(e)}")
            return f"Professional with experience in {target_role} seeking to leverage skills and expertise to drive organizational success."

extract_contact_info = ContactInfoTool()
analyze_work_experience = ExperienceTool()
extract_skills = SkillsTool()
extract_education = EducationTool()
generate_professional_summary = SummaryTool()