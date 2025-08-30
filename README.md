# AI Resume Builder 📄

A professional AI-powered resume generator that transforms raw resume information into polished, professional resumes using OpenAI's GPT models. The application provides both a web interface using Streamlit and a REST API using FastAPI.

## Features

- **AI-Powered Resume Generation**: Converts unstructured resume text into professional, formatted resumes
- **Multiple Interfaces**: 
  - Streamlit web app for easy user interaction
  - FastAPI REST API for programmatic access
- **Professional Formatting**: Generates resumes following the popular "Chicago" template
- **PDF Export**: Download generated resumes as PDF files
- **Batch Processing**: API supports generating multiple resumes in a single request
- **Production Ready**: Dockerized with proper logging, error handling, and health checks

## Tech Stack

- **Backend**: FastAPI, Python 3.11
- **Frontend**: Streamlit
- **AI**: OpenAI GPT-4o-mini via LangChain
- **PDF Generation**: FPDF
- **Deployment**: Docker with Gunicorn
- **Database**: SQLite (for future enhancements)

## Prerequisites

- Python 3.11+
- Docker (optional, for containerized deployment)
- OpenAI API key

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/Kartavya-AI/Resume-Builder
cd Resume-Builder
```

### 2. Set Up Environment
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Create a `.env` file in the project root:
```env
OPENAI_API_KEY=your_openai_api_key_here
PORT=8080
```

## Usage

### Streamlit Web App

Run the Streamlit application for an interactive web interface:

```bash
streamlit run app.py
```

The app will be available at `http://localhost:8501`

**How to use the web app:**
1. Enter your raw resume details in the text area
2. Include your full name, contact info, work experience, education, and skills
3. Click "✨ Generate Resume"
4. Review the generated resume
5. Download as PDF

### FastAPI REST API

Run the FastAPI server:

```bash
uvicorn api:app --host 0.0.0.0 --port 8080 --reload
```

The API will be available at `http://localhost:8080`

**API Documentation:**
- Swagger UI: `http://localhost:8080/docs`
- ReDoc: `http://localhost:8080/redoc`

#### API Endpoints

##### Generate Single Resume
```http
POST /generate-resume
Content-Type: application/json

{
  "user_input": "John Doe, Software Engineer with 5 years experience at Google working on cloud infrastructure..."
}
```

**Response:**
```json
{
  "resume": "Generated resume in markdown format",
  "processing_time": 2.34,
  "timestamp": "2024-01-01T12:00:00.000000"
}
```

##### Batch Resume Generation
```http
POST /generate-resume/batch
Content-Type: application/json

[
  {
    "user_input": "Resume details for person 1..."
  },
  {
    "user_input": "Resume details for person 2..."
  }
]
```

##### Health Check
```http
GET /health
```

##### API Statistics
```http
GET /api/stats
```

## Docker Deployment

### Build and Run with Docker

```bash
# Build the image
docker build -t ai-resume-builder .

# Run the container
docker run -p 8080:8080 -e OPENAI_API_KEY=your_api_key_here ai-resume-builder
```

### Docker Compose (Optional)

Create a `docker-compose.yml` file:

```yaml
version: '3.8'
services:
  resume-builder:
    build: .
    ports:
      - "8080:8080"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - PORT=8080
    restart: unless-stopped
```

Run with:
```bash
docker-compose up -d
```

## Resume Input Guidelines

For best results, include the following information in your raw input:

### Required Information
- **Full Name**
- **Contact Information** (phone, email, LinkedIn, location)
- **Professional Summary** or objective
- **Work Experience** with:
  - Company names
  - Job titles
  - Employment dates
  - Key achievements and responsibilities

### Optional but Recommended
- **Education** (degree, university, graduation date, GPA if high)
- **Skills** (technical and soft skills)
- **Certifications**
- **Awards or achievements**

### Example Input
```
John Smith
Senior Software Engineer
Phone: (555) 123-4567
Email: john.smith@email.com
LinkedIn: linkedin.com/in/johnsmith
Location: San Francisco, CA

Summary: Experienced software engineer with 8+ years developing scalable web applications and leading cross-functional teams.

Experience:
- Google (2020-Present): Senior Software Engineer
  - Led team of 5 engineers developing cloud infrastructure
  - Improved system performance by 40%
  - Implemented microservices architecture serving 10M+ users

- Facebook (2018-2020): Software Engineer
  - Developed React components for news feed
  - Reduced page load time by 25%

Education:
- Bachelor of Science in Computer Science
- Stanford University, 2018
- GPA: 3.8/4.0

Skills: Python, JavaScript, React, AWS, Docker, Kubernetes, System Design
```

## Resume Output Format

The generated resume follows a professional "Chicago" template with these sections:

1. **Header** - Name, title, contact information
2. **Professional Summary** - Brief overview of experience and skills
3. **Professional Experience** - Work history with achievements
4. **Education** - Academic background
5. **Skills** - Technical and soft skills

## API Response Models

### ResumeRequest
```json
{
  "user_input": "string (50-10000 characters)"
}
```

### ResumeResponse
```json
{
  "resume": "string",
  "processing_time": "float",
  "timestamp": "string"
}
```

### ErrorResponse
```json
{
  "error": "string",
  "detail": "string",
  "timestamp": "string"
}
```

## Error Handling

The application includes comprehensive error handling:

- **Validation Errors**: Invalid input length or format
- **API Errors**: OpenAI API failures or rate limits
- **Environment Errors**: Missing API keys or configuration
- **Processing Errors**: Unexpected failures during resume generation

## Logging

The application uses structured logging with:
- Request/response logging
- Error tracking with stack traces
- Performance metrics
- Health check monitoring

## Configuration

### Environment Variables

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `OPENAI_API_KEY` | Yes | OpenAI API key for GPT access | N/A |
| `PORT` | No | Port for FastAPI server | 8080 |

### Model Configuration

The application uses:
- **Model**: GPT-4o-mini
- **Temperature**: 0.5 (balanced creativity/consistency)
- **Max Input**: 10,000 characters
- **Min Input**: 50 characters

## Performance

- **Single Resume Generation**: ~2-5 seconds
- **Batch Processing**: Up to 10 resumes per request
- **Concurrent Requests**: Handled by Gunicorn with 2 workers
- **Timeout**: 240 seconds for complex requests

## Security

- **User Isolation**: Non-root user in Docker container
- **Input Validation**: Strict validation on all inputs
- **CORS Configuration**: Configurable for production
- **Error Sanitization**: No sensitive information in error responses

## Development

### Running in Development Mode

```bash
# Install development dependencies
pip install -r requirements.txt

# Run Streamlit app
streamlit run app.py

# Run FastAPI with auto-reload
uvicorn api:app --reload --port 8080
```

### Testing the API

```bash
# Health check
curl http://localhost:8080/health

# Generate resume
curl -X POST "http://localhost:8080/generate-resume" \
     -H "Content-Type: application/json" \
     -d '{"user_input": "Your resume details here..."}'
```

## Troubleshooting

### Common Issues

1. **"OPENAI_API_KEY not found"**
   - Ensure your `.env` file contains `OPENAI_API_KEY=your_key_here`
   - Check that the `.env` file is in the project root directory

2. **"Failed to generate resume"**
   - Check your OpenAI API key is valid and has sufficient credits
   - Ensure input text is between 50-10,000 characters
   - Check network connectivity

3. **PDF Generation Issues**
   - Some special characters may not render properly in PDF
   - The PDF uses Latin-1 encoding for compatibility

4. **Docker Build Failures**
   - Ensure Docker has sufficient memory (recommended: 2GB+)
   - Check that all files are present in the build context

### Logs

Check application logs for detailed error information:
```bash
# Docker logs
docker logs <container_name>

# Direct Python execution
# Logs will appear in console
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review the API documentation at `/docs`
3. Check OpenAI's status page for API issues
4. Create an issue in the repository

## Roadmap

Potential future enhancements:
- Multiple resume templates
- Resume parsing and editing capabilities
- User accounts and resume storage
- Integration with job boards
- Cover letter generation
- ATS optimization features

---

**Note**: This application requires an active OpenAI API key and internet connection to function properly.
