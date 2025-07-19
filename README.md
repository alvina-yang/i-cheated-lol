# 🕵️ Chameleon - Hackathon Project Stealer

A modern full-stack application that discovers and "steals" innovative hackathon projects using AI-powered search and beautiful human-in-the-loop selection.

## ✨ Features

### 🎯 Smart Project Discovery
- **Technology-Focused Search**: Find hackathon projects by specific technologies (React, Python, AI, etc.)
- **AI-Powered Filtering**: LangChain agents analyze projects for hackathon relevance and innovation
- **Human-in-the-Loop**: Returns 5 carefully curated projects for human selection

### 🎨 Modern UI/UX
- **Beautiful Design**: Gradient backgrounds with animated blob effects
- **shadcn/ui Components**: Modern, accessible component library
- **Glowing Card Effects**: Interactive glow effects that follow mouse movement
- **Multi-Step Loading**: Engaging step-by-step progress indicators
- **Responsive Design**: Works seamlessly on desktop and mobile

### 🚀 Advanced Technology Stack
- **Frontend**: Next.js 15, React 19, TypeScript, Tailwind CSS, Framer Motion
- **Backend**: FastAPI, Python, LangChain, OpenAI GPT-4
- **Components**: shadcn/ui, Custom glowing effects, Multi-step loaders

## 🛠️ Architecture

### Backend (FastAPI)
- **Agents System**: Modular LangChain agents for search and validation
- **GitHub Integration**: Smart GitHub API querying with rate limiting
- **Project Analysis**: Code complexity scoring and innovation detection
- **Human-in-the-Loop**: Returns 5 projects instead of auto-selecting

### Frontend (Next.js)
- **Modern UI**: Glass morphism design with gradient effects
- **Interactive Components**: Glowing cards, animated loaders
- **Real-time Search**: Instant project discovery and display
- **Success Feedback**: Beautiful confirmation dialogs

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ 
- Python 3.9+
- OpenAI API key
- GitHub personal access token

### 1. Environment Setup

Create `backend/.env`:
```env
OPENAI_API_KEY=your_openai_api_key_here
GITHUB_TOKEN=your_github_token_here
```

### 2. Install Dependencies

```bash
# Backend dependencies
cd backend
pip install -r requirements.txt

# Frontend dependencies  
cd ../frontend
npm install
```

### 3. Start the Application

```bash
# Use the convenient startup script
./start.sh

# Or start manually:
# Terminal 1 - Backend
cd backend && python -m uvicorn main_refactored:app --reload

# Terminal 2 - Frontend  
cd frontend && npm run dev
```

### 4. Access the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 🎮 How to Use

1. **Enter Technologies**: Type comma-separated technologies (e.g., "react, nextjs, ai")
2. **Search Projects**: Click search or press Enter to find hackathon projects
3. **Review Options**: Browse 5 curated projects with descriptions, technologies, and READMEs
4. **Steal a Project**: Click "Steal This Project!" to clone it locally
5. **Success**: Get confirmation and location of cloned project

## 🏗️ Project Structure

```
Chameleon-test/
├── backend/                 # FastAPI backend
│   ├── agents/             # LangChain agents
│   ├── core/               # Configuration and base classes
│   ├── prompts/            # AI prompt templates
│   ├── utils/              # GitHub client and utilities
│   ├── workflows/          # Main discovery chain
│   └── main.py            # FastAPI application
├── frontend/               # Next.js frontend
│   ├── src/
│   │   ├── app/           # Next.js app router
│   │   └── components/    # React components
│   │       └── ui/        # shadcn/ui components
│   └── public/            # Static assets
├── HackathonProject/       # Cloned projects destination
└── start.sh               # Startup script
```

## 🎨 UI Components

### Multi-Step Loader
- Engaging step-by-step progress visualization
- Customizable loading states and timing
- Smooth animations with Framer Motion

### Glowing Effect Cards
- Mouse-tracking glow effects
- Customizable colors and intensity
- Smooth gradient animations

### Modern Design System
- Glass morphism effects
- Gradient backgrounds
- Responsive grid layouts
- Accessible color schemes

## 🔧 Configuration

### Backend Settings (`backend/core/config.py`)
```python
MAX_PROJECTS_TO_FIND = 5    # Projects returned to user
MIN_STARS = 5               # Minimum GitHub stars
MAX_STARS = 200             # Maximum GitHub stars  
MAX_FORKS = 30              # Maximum GitHub forks
CLONE_DIRECTORY = "~/HackathonProject"  # Clone destination
```

### Search Criteria
- **Hackathon Focus**: Projects with hackathon context keywords
- **Size Filtering**: Small to medium projects (5-200 stars)
- **Technology Matching**: Projects using specified technologies
- **Innovation Scoring**: AI-powered creativity assessment

## 🛡️ Security & Rate Limiting

- **GitHub API**: Built-in rate limiting and retry logic
- **Environment Variables**: Secure API key management
- **CORS Protection**: Configured for localhost development
- **Input Validation**: Pydantic models for API validation

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 API Endpoints

### `POST /api/search`
Search for hackathon projects by technologies.

**Request:**
```json
{
  "technologies": ["react", "nextjs", "ai"]
}
```

**Response:**
```json
{
  "projects": [...],
  "total_found": 10,
  "search_technologies": ["react", "nextjs", "ai"]
}
```

### `POST /api/clone`
Clone a selected project to local filesystem.

**Request:**
```json
{
  "project_name": "awesome-hackathon-project",
  "project_url": "https://github.com/user/repo",
  "clone_url": "https://github.com/user/repo.git"
}
```

## 🎯 Future Enhancements

- [ ] Authentication system
- [ ] Project bookmarking
- [ ] Advanced filtering options
- [ ] Project comparison features
- [ ] Integration with more code platforms
- [ ] Mobile app version

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **shadcn/ui** for beautiful component library
- **LangChain** for powerful AI agent framework
- **OpenAI** for GPT-4 language model
- **Framer Motion** for smooth animations
- **FastAPI** for modern Python web framework

---

**⚠️ Disclaimer**: This tool is for educational purposes. Always respect repository licenses and give proper attribution when using open-source code.