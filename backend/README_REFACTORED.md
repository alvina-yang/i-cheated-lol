# Chameleon Hackathon Project Discovery System - Refactored

## 🚀 Overview

This is the refactored version of the Chameleon system with enhanced organization, AI-powered features, and real-time capabilities. The system is now much more modular, maintainable, and feature-rich.

## ✨ New Features

### 🤖 AI-Powered Enhancements
- **AI-generated commit messages**: Realistic commit messages generated using LLM
- **Smart code modification**: AI adds comments and improves variable names
- **Intelligent git operations**: AI assists with repository setup and operations

### 📊 Real-time Monitoring
- **Live status tracking**: Real-time progress updates for all operations
- **Terminal output streaming**: Live git command output in the frontend
- **File change monitoring**: Real-time file system change detection

### ⚙️ Enhanced Configuration
- **User settings**: Configurable git username, email, and preferences
- **Repository settings**: Flexible repository URL configuration
- **Processing settings**: Customizable code modification options
- **Terminal settings**: Configurable output and progress display

### 🎯 Better Organization
- **Modular agents**: Separate agents for different tasks
- **Organized prompts**: Centralized prompt management
- **Clean architecture**: Well-structured codebase with clear separation of concerns

## 📁 Project Structure

```
backend/
├── agents/                     # AI Agents
│   ├── __init__.py
│   ├── search_agent.py        # Project search functionality
│   ├── validator_agent.py     # Project validation
│   ├── commit_agent.py        # AI commit message generation
│   ├── code_modifier_agent.py # Code modification with AI
│   └── git_agent.py           # Git operations and monitoring
├── core/                      # Core system components
│   ├── __init__.py
│   ├── base_agent.py         # Base agent class
│   ├── config.py             # Original configuration
│   └── enhanced_config.py    # Enhanced configuration system
├── prompts/                   # AI Prompts
│   ├── __init__.py
│   ├── search_prompts.py     # Search-related prompts
│   ├── validator_prompts.py  # Validation prompts
│   ├── commit_prompts.py     # Commit message prompts
│   ├── code_modifier_prompts.py # Code modification prompts
│   └── git_prompts.py        # Git operation prompts
├── utils/                     # Utility modules
│   ├── __init__.py
│   ├── github_client.py      # GitHub API client
│   ├── project_cloner.py     # Project cloning utilities
│   └── status_tracker.py     # Real-time status tracking
├── workflows/                 # Workflow definitions
│   ├── __init__.py
│   └── discovery_chain.py    # Discovery workflow
├── main.py                    # Original main file
├── main_refactored.py        # New refactored main file
├── test_integration.py       # Integration tests
└── requirements.txt          # Dependencies
```

## 🔧 API Endpoints

### Core Endpoints
- `GET /` - Health check with feature list
- `POST /api/search` - Search for hackathon projects
- `POST /api/clone` - Clone selected project
- `POST /api/project/{name}/make-untraceable` - Enhanced untraceable process

### New Status & Monitoring
- `GET /api/status` - Get current operation status
- `GET /api/status/stream` - Stream real-time status updates
- `GET /api/project/{name}/terminal-output` - Get terminal output
- `GET /api/project/{name}/stream-terminal` - Stream terminal output
- `POST /api/project/{name}/execute-git-command` - Execute git commands
- `GET /api/project/{name}/file-changes` - Get file changes
- `GET /api/project/{name}/monitor-changes` - Monitor file changes

### Configuration Management
- `GET /api/settings` - Get all settings
- `POST /api/settings` - Update settings

## 🤖 AI Agents

### CommitAgent
Generates realistic commit messages and manages git history:
- Creates chronological commit sequences
- Generates context-aware commit messages
- Rewrites git history with realistic timestamps
- Supports different hackathon themes and technologies

### CodeModifierAgent
Intelligently modifies code using AI:
- Adds meaningful comments to code
- Improves variable names for better readability
- Adds documentation to functions
- Analyzes code complexity and suggests improvements

### GitAgent
Handles git operations and repository management:
- Validates repository URLs
- Sets up new repository destinations
- Executes git commands with progress tracking
- Monitors file changes in real-time

## 📝 Configuration System

### User Settings
```json
{
  "git_username": "your-username",
  "git_email": "your-email@example.com",
  "preferred_branch": "main",
  "hackathon_duration_hours": 48,
  "auto_backup": true,
  "verbose_output": true
}
```

### Repository Settings
```json
{
  "original_url": "https://github.com/original/repo",
  "target_url": "https://github.com/your/repo",
  "target_branch": "main",
  "preserve_history": false,
  "auto_push": true
}
```

### Processing Settings
```json
{
  "add_comments": true,
  "rename_variables": true,
  "add_documentation": false,
  "modify_commit_messages": true,
  "obfuscate_author_info": true
}
```

### Terminal Settings
```json
{
  "show_progress": true,
  "show_file_changes": true,
  "show_git_output": true,
  "update_interval_seconds": 1.0,
  "max_output_lines": 1000
}
```

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Git
- OpenAI API key
- GitHub token (optional)

### Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
export OPENAI_API_KEY="your-openai-api-key"
export GITHUB_TOKEN="your-github-token"  # Optional
```

### Running the System
```bash
# Run the refactored version
python main_refactored.py

# Or use uvicorn directly
uvicorn main_refactored:app --host 0.0.0.0 --port 8000 --reload
```

### Testing
```bash
# Run integration tests
python test_integration.py
```

## 📊 Status Tracking

The system now includes comprehensive status tracking:

### Task States
- **pending**: Task created but not started
- **running**: Task currently executing
- **completed**: Task finished successfully
- **failed**: Task encountered an error
- **cancelled**: Task was cancelled

### Real-time Updates
- Progress bars for long-running operations
- Live terminal output streaming
- File change notifications
- Operation duration tracking

## 🎯 Enhanced Untraceable Process

The new untraceable process includes:

1. **Repository Setup**: Configure new destination repository
2. **Code Modification**: AI-powered code enhancement
3. **Git History Rewriting**: Generate realistic commit history
4. **Final Commit**: Create final commit with AI-generated message

### Process Flow
```
Start → Repository Setup → Code Analysis → 
Code Modification → Commit Generation → 
History Rewriting → Final Commit → Complete
```

## 🔧 Advanced Features

### AI-Generated Commit Messages
- Context-aware message generation
- Hackathon-appropriate language
- Realistic development progression
- Technology-specific references

### Smart Code Modification
- Intelligent comment placement
- Variable name improvements
- Function documentation
- Code complexity analysis

### Real-time Terminal Output
- Live git command execution
- Progress tracking
- Error handling
- Command history

## 📈 Performance Improvements

- **Modular Architecture**: Better separation of concerns
- **Parallel Processing**: Background task execution
- **Efficient Monitoring**: Optimized status tracking
- **Caching**: Improved response times
- **Resource Management**: Better memory usage

## 🔒 Security Enhancements

- **Input Validation**: Comprehensive request validation
- **Command Sanitization**: Safe git command execution
- **Path Validation**: Secure file system operations
- **Error Handling**: Graceful error recovery

## 📖 Usage Examples

### Basic Project Search
```bash
curl -X POST "http://localhost:8000/api/search" \
  -H "Content-Type: application/json" \
  -d '{"technologies": ["python", "react"]}'
```

### Clone Project
```bash
curl -X POST "http://localhost:8000/api/clone" \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "awesome-project",
    "project_url": "https://github.com/user/project",
    "clone_url": "https://github.com/user/project.git"
  }'
```

### Make Project Untraceable
```bash
curl -X POST "http://localhost:8000/api/project/awesome-project/make-untraceable" \
  -H "Content-Type: application/json" \
  -d '{
    "hackathon_date": "2024-01-15",
    "hackathon_start_time": "09:00",
    "git_username": "hackathon-dev",
    "git_email": "dev@hackathon.com",
    "target_repository_url": "https://github.com/your/new-repo",
    "add_comments": true,
    "change_variables": true,
    "generate_commit_messages": true
  }'
```

### Stream Status Updates
```bash
curl -N "http://localhost:8000/api/status/stream"
```

## 🐛 Troubleshooting

### Common Issues
1. **Import Errors**: Make sure all dependencies are installed
2. **API Key Issues**: Verify OpenAI API key is set correctly
3. **Git Errors**: Ensure git is installed and configured
4. **Permission Errors**: Check file system permissions

### Debug Mode
Set `verbose_output: true` in terminal settings for detailed logging.

## 🤝 Contributing

The refactored system is much more maintainable and extensible. To contribute:

1. Follow the modular architecture
2. Add appropriate tests
3. Update documentation
4. Use the existing agent patterns

## 📄 License

This project is part of the Chameleon Hackathon Discovery System.

## 🎉 What's Next?

Future enhancements could include:
- Web-based configuration interface
- Advanced AI code analysis
- Multi-language support
- Distributed processing
- Enhanced security features

---

**Note**: This refactored version maintains all original functionality while adding significant new features and improvements. The system is now much more organized, maintainable, and feature-rich. 