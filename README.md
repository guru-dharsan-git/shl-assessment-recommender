# SHL Assessment Recommendation System

## Overview

The SHL Assessment Recommendation System is a tool designed to help hiring managers and recruiters find the most appropriate SHL assessments for their hiring needs. By analyzing job descriptions or specific queries, the system leverages advanced language models to recommend relevant assessments from SHL's catalog.

## Features

- **Multiple Input Methods**: Submit queries via text input, URLs to job descriptions, or by pasting full job descriptions
- **AI-Powered Recommendations**: Utilizes LLM (Large Language Model) to understand job requirements and match them with appropriate assessments
- **Vector Search**: Implements semantic search to find the most relevant assessments based on skills and requirements
- **Web Interface**: User-friendly web UI for easy access and results display
- **API Endpoints**: RESTful API for integration with other systems
- **CLI Mode**: Command-line interface for quick queries
- **Fallback Mechanisms**: Ensures recommendations even if primary retrieval methods fail

## System Architecture

```
                 ┌─────────────┐
                 │ User Input  │
                 └──────┬──────┘
                        │
                        ▼
┌────────────────────────────────────────┐
│             FastAPI Server             │
├────────────────────────────────────────┤
│  ┌─────────────┐      ┌─────────────┐  │
│  │ Text Parser │ ◄──► │ URL Scraper │  │
│  └──────┬──────┘      └─────────────┘  │
│         │                              │
│         ▼                              │
│  ┌─────────────┐      ┌─────────────┐  │
│  │   Vector    │ ◄──► │ ChromaDB    │  │
│  │  Retriever  │      │             │  │
│  └──────┬──────┘      └─────────────┘  │
│         │                              │
│         ▼                              │
│  ┌─────────────┐                       │
│  │    LLM      │                       │
│  │  (Ollama)   │                       │
│  └──────┬──────┘                       │
│         │                              │
└─────────┼──────────────────────────────┘
          │
          ▼
┌───────────────────────┐
│     JSON Response     │
└───────────────────────┘
```

## Installation

### Prerequisites

- Python 3.8+
- Ollama installed locally (for the LLM)
- Chrome/Chromium (for ChromaDB)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/guru-dharsan-git/shl-assessment-recommender.git
   cd shl-assessment-recommender
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Make sure Ollama is running and has the required models:
   ```bash
   ollama pull llama3.2
   ollama pull mxbai-embed-large
   ```

5. Run the data collection script (if needed):
   ```bash
   python scrape_shl.py
   ```

6. Build the vector database:
   ```bash
   python vector.py
   ```

## Usage

### Web Interface

1. Start the server:
   ```bash
   python main.py
   ```

2. Open your browser and go to `http://localhost:8000`

3. Enter your query, URL, or paste a job description to get recommendations

### Command Line Interface

Run the application in CLI mode:
```bash
python main.py cli
```

### API Endpoints

- **GET /api/recommend**: Get assessment recommendations
  - Query parameters:
    - `query`: Text query for assessment recommendations
    - `url`: URL of a job description
  - Returns JSON with recommendations

- **GET /api/assessments**: Get all assessments in the database (for testing)

## Example Queries

- "I am hiring for Java developers who can also collaborate effectively with my business teams. Looking for an assessment(s) that can be completed in 40 minutes."
- "Looking to hire mid-level professionals who are proficient in Python, SQL and JavaScript. Need an assessment package that can test all skills with max duration of 60 minutes."
- "I need to assess candidates for analytical thinking and personality traits for an analyst position. Time limit is less than 30 minutes."

## Project Structure

```
shl-assessment-recommender/
├── main.py                  # FastAPI server and main application
├── vector.py                # Vector store creation and retrieval
├── scrape_shl.py            # Web scraper for SHL assessment data
├── shl_assessments_with_skills.csv  # Dataset of SHL assessments
├── templates/               # HTML templates
│   └── index.html           # Main web interface
├── chrome_shl_db/           # ChromaDB vector database
└── requirements.txt         # Python dependencies
```

## Technical Details

- **Language Model**: Uses Ollama with Llama 3.2 for generating recommendations
- **Embeddings**: Uses MXBai Embed Large via Ollama for semantic search
- **Vector Database**: ChromaDB for efficient similarity search
- **Web Framework**: FastAPI for the backend API
- **Frontend**: Bootstrap 5 for responsive UI

## Troubleshooting

### Common Issues

1. **No recommendations are returned**:
   - Check that Ollama is running
   - Verify that the required models are installed
   - Make sure the vector database has been built properly

2. **Slow response times**:
   - The LLM processing can take time, especially on slower hardware
   - Consider reducing the temperature parameter for faster (but less creative) responses

3. **URL extraction fails**:
   - Some websites block scraping attempts
   - Try providing the job description text directly

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- SHL for providing a comprehensive catalog of assessments
- Ollama for the local LLM capabilities
- LangChain for the retrieval augmented generation framework