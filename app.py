import streamlit as st
from tool import generate_resume
import os
from fpdf import FPDF
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="AI Resume Builder",
    page_icon="📄",
    layout="centered"
)

st.title("📄 AI Professional Resume Builder")
st.markdown("Enter your resume details below. The AI will generate a polished, professional resume based on the popular 'Chicago' template.")

st.sidebar.header("How to Use")
st.sidebar.info(
    "1.  **Enter Details**: Paste your current resume or write your professional details in the text box on the main page.\n\n"
    "2.  **Be Detailed**: Include your full name, contact info, summary, work experience (company, role, dates, achievements), education, and skills.\n\n"
    "3.  **Generate**: Click the '✨ Generate Resume' button.\n\n"
    "4.  **Review & Download**: The AI-generated resume will appear. You can review it and then download it as a PDF file."
)
st.sidebar.warning(
    "Ensure your `OPENAI_API_KEY` is set in a `.env` file."
)


st.header("Your Raw Resume Details")
raw_text = st.text_area(
    "Paste your details here. The more information you provide, the better the result!", 
    height=350, 
    placeholder="Example: Richard Williams, Senior Financial Advisor. 7+ years experience delivering financial advice..."
)

if st.button("✨ Generate Resume"):
    if not os.getenv("OPENAI_API_KEY"):
        st.error("OpenAI API key not found. Please create a .env file and add your OPENAI_API_KEY.")
    elif not raw_text.strip():
        st.warning("Please enter your resume details in the text box.")
    else:
        with st.spinner("Your professional resume is being crafted by AI..."):
            try:
                generated_resume_md = generate_resume(raw_text)
                st.session_state.generated_resume_md = generated_resume_md
                st.session_state.pdf_bytes = None
                
            except Exception as e:
                st.error(f"An error occurred during generation: {e}")

if 'generated_resume_md' in st.session_state and st.session_state.generated_resume_md:
    st.divider()
    st.subheader("Your Generated Resume")
    resume_md = st.session_state.generated_resume_md
    st.markdown(resume_md)
    st.divider()
    st.subheader("Download as PDF")

    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", size=11)
        pdf.multi_cell(0, 5, txt=resume_md.encode('latin-1', 'replace').decode('latin-1'))
        pdf_bytes = pdf.output(dest='S').encode('latin-1')
        st.session_state.pdf_bytes = pdf_bytes

    except Exception as e:
        st.error(f"Failed to convert to PDF. Error: {e}")

    if st.session_state.get("pdf_bytes"):
        st.download_button(
            label="⬇️ Download as PDF",
            data=st.session_state.pdf_bytes,
            file_name="professional_resume.pdf",
            mime="application/pdf",
            help="Download your resume as a PDF file."
        )
