import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

def generate_resume(user_input: str) -> str:
    load_dotenv()
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in .env file.")

    llm = ChatOpenAI(model_name="gpt-4o-mini", openai_api_key=api_key, temperature=0.5)

    prompt_template_string = """
    Act as an expert career coach and professional resume writer. Your task is to take the user's raw, unstructured resume information below and transform it into a polished, professional resume in Markdown format.

    **IMPORTANT INSTRUCTIONS:**
    - **DO NOT** use any Markdown characters. This means no '#', '*', '***', '**' or '---'.
    - Use capitalization and line breaks for structure.
    - Quantify achievements with numbers and metrics where possible.

    Follow the structure of the provided example precisely. The sections must be in this order:
    1.  **Full Name** (as a large, bold heading)
    2.  **Job Title** (e.g., Senior Financial Advisor)
    3.  **Contact Information** (Phone | Email | LinkedIn | Location)
    4.  **Summary** (A 2-3 sentence professional summary that highlights key experience and skills)
    5.  **PROFESSIONAL EXPERIENCE** (Use a horizontal rule before this section)
        - For each role:
            - **COMPANY NAME** (in bold)
            - *Job Title* (in italics)
            - Location (City, ST) and Dates (Month Year - Present/Month Year) on the same line, right-aligned.
            - Use 3-4 bullet points describing key achievements and responsibilities. Start each bullet point with an action verb. Quantify achievements with numbers and metrics where possible.
    6.  **EDUCATION** (Use a horizontal rule before this section)
        - **DEGREE EARNED** (e.g., BACHELOR OF SCIENCE IN BUSINESS ADMINISTRATION)
        - *University Name*, City, ST
        - GPA (if high) and Graduation Date on the same line.
    7.  **SKILLS** (Use a horizontal rule before this section)
        - Use bullet points to list key technical and soft skills.

    Here is the raw input from the user:
    ---
    {user_input}
    ---

    Generate the complete resume in Markdown. Do not include any introductory text, explanations, or comments.
    """

    prompt = PromptTemplate.from_template(prompt_template_string)
    output_parser = StrOutputParser()
    chain = prompt | llm | output_parser
    try:
        result = chain.invoke({"user_input": user_input})
        return result
    except Exception as e:
        return f"An error occurred while generating the resume: {e}"

