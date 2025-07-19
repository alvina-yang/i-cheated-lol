#!/usr/bin/env python3
"""
Chameleon Hackathon Project Discovery System - Refactored FastAPI Backend

Modular FastAPI backend with organized AI agents and enhanced features.
"""

import os
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add the backend directory to Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

# Import enhanced components
from core.enhanced_config import EnhancedConfig
from agents.search_agent import TechnologyProjectSearchAgent
from agents.validator_agent import ValidatorAgent
from agents.commit_agent import CommitAgent
from agents.code_modifier_agent import CodeModifierAgent
from agents.variable_renaming_agent import VariableRenamingAgent
from agents.git_agent import GitAgent
from agents.presentation_agent import PresentationAgent
from utils.project_cloner import GitHubCloner
from utils.status_tracker import StatusTracker, get_global_tracker, initialize_status_tracking

# Import route modules
from routes import (
    search_router,
    clone_router,
    untraceable_router,
    status_router,
    settings_router,
    project_router
)
from routes.file_operations import router as file_operations_router
from routes.git import router as git_router

# Global instances
agents = {}
status_tracker = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan."""
    global agents, status_tracker
    
    try:
        # Initialize configuration
        EnhancedConfig.initialize()
        EnhancedConfig.validate()
        
        # Initialize status tracking
        status_tracker = initialize_status_tracking(
            enable_real_time=EnhancedConfig.ENABLE_REAL_TIME_OUTPUT,
            update_interval=1.0
        )
        
        # Initialize agents
        agents = {
            'search': TechnologyProjectSearchAgent(),
            'validator': ValidatorAgent(),
            'commit': CommitAgent(),
            'code_modifier': CodeModifierAgent(),
            'variable_renamer': VariableRenamingAgent(),
            'git': GitAgent(),
            'presentation': PresentationAgent(),
            'cloner': GitHubCloner()
        }
        
        print("🚀 Chameleon API Backend initialized successfully!")
        yield
        
    except Exception as e:
        print(f"❌ Failed to initialize backend: {e}")
        raise
    finally:
        # Cleanup
        if status_tracker:
            status_tracker.stop()


# Create FastAPI app with lifespan
app = FastAPI(
    title="Chameleon Hackathon Discovery API",
    description="Enhanced API for discovering and transforming hackathon projects",
    version="2.0.0",
    lifespan=lifespan
)

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include route modules
app.include_router(search_router)
app.include_router(clone_router)
app.include_router(untraceable_router)
app.include_router(status_router)
app.include_router(settings_router)
app.include_router(project_router)
app.include_router(file_operations_router)
app.include_router(git_router)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Enhanced Chameleon Hackathon Discovery API",
        "status": "running",
        "version": "2.0.0",
        "features": [
            "Generic commit messages from predefined bank",
            "Real-time terminal output",
            "Enhanced code modification",
            "Configurable repository destinations",
            "Progress tracking"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 