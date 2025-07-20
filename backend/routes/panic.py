"""
PANIC button routes for the Chameleon Hackathon Discovery API
"""

import os
import json
import shutil
import subprocess
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

from core.enhanced_config import EnhancedConfig
from utils.status_tracker import get_global_tracker

router = APIRouter(prefix="/api", tags=["panic"])


class PanicRequest(BaseModel):
    project_name: str
    start_command: str = "python -m http.server 3000"  # Default start command


# Tic-tac-toe app template
TICTACTOE_APP = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Emergency Tic-Tac-Toe</title>
    <style>
        body {
            font-family: 'Courier New', monospace;
            background: linear-gradient(135deg, #1a1a2e, #16213e);
            color: #fff;
            margin: 0;
            padding: 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
            min-height: 100vh;
            justify-content: center;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .title {
            font-size: 3rem;
            color: #ff6b6b;
            text-shadow: 0 0 20px rgba(255, 107, 107, 0.5);
            margin-bottom: 10px;
        }
        
        .subtitle {
            font-size: 1.2rem;
            color: #888;
            margin-bottom: 20px;
        }
        
        .emergency-notice {
            background: rgba(255, 107, 107, 0.1);
            border: 2px solid #ff6b6b;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 30px;
            text-align: center;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(255, 107, 107, 0.7); }
            70% { box-shadow: 0 0 0 10px rgba(255, 107, 107, 0); }
            100% { box-shadow: 0 0 0 0 rgba(255, 107, 107, 0); }
        }
        
        .game-container {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
            backdrop-filter: blur(10px);
        }
        
        .board {
            display: grid;
            grid-template-columns: repeat(3, 100px);
            grid-gap: 5px;
            margin: 20px auto;
            background: #333;
            border-radius: 10px;
            padding: 10px;
        }
        
        .cell {
            width: 100px;
            height: 100px;
            background: rgba(255, 255, 255, 0.1);
            border: none;
            border-radius: 8px;
            font-size: 2rem;
            font-weight: bold;
            color: #fff;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .cell:hover {
            background: rgba(255, 255, 255, 0.2);
            transform: scale(1.05);
        }
        
        .cell.x {
            color: #ff6b6b;
            text-shadow: 0 0 10px rgba(255, 107, 107, 0.8);
        }
        
        .cell.o {
            color: #4ecdc4;
            text-shadow: 0 0 10px rgba(78, 205, 196, 0.8);
        }
        
        .reset-btn {
            background: linear-gradient(45deg, #ff6b6b, #4ecdc4);
            border: none;
            border-radius: 25px;
            color: white;
            font-size: 1rem;
            font-weight: bold;
            padding: 12px 24px;
            cursor: pointer;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 1px;
            display: block;
            margin: 20px auto 0;
        }
        
        .reset-btn:hover {
            transform: scale(1.05);
            box-shadow: 0 5px 15px rgba(255, 107, 107, 0.4);
        }
        
        .footer {
            margin-top: 40px;
            text-align: center;
            color: #666;
            font-size: 0.9rem;
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="title">TIC-TAC-TOE</div>
    </div>
    
    <div class="game-container">
        <div class="board">
            <div class="cell" onclick="makeMove(0)"></div>
            <div class="cell" onclick="makeMove(1)"></div>
            <div class="cell" onclick="makeMove(2)"></div>
            <div class="cell" onclick="makeMove(3)"></div>
            <div class="cell" onclick="makeMove(4)"></div>
            <div class="cell" onclick="makeMove(5)"></div>
            <div class="cell" onclick="makeMove(6)"></div>
            <div class="cell" onclick="makeMove(7)"></div>
            <div class="cell" onclick="makeMove(8)"></div>
        </div>
        <button class="reset-btn" onclick="resetGame()">New Game</button>
    </div>
    
    <div class="footer">
        <p>Built with 💻 and lots of ☕ definitely over several weeks</p>
        <p>Absolutely not a last-minute panic project 😅</p>
    </div>

        <script>
        let board = ['', '', '', '', '', '', '', '', ''];
        let currentPlayer = 'X';
        
        function makeMove(index) {
            if (board[index] !== '') return;
            
            board[index] = currentPlayer;
            document.querySelectorAll('.cell')[index].textContent = currentPlayer;
            
            currentPlayer = currentPlayer === 'X' ? 'O' : 'X';
        }
        
        function resetGame() {
            board = ['', '', '', '', '', '', '', '', ''];
            currentPlayer = 'X';
            
            document.querySelectorAll('.cell').forEach(cell => {
                cell.textContent = '';
            });
        }
    </script>
</body>
</html>'''

PANIC_README = '''# Emergency Tic-Tac-Toe Project 🚨

## Overview
This is definitely **NOT** a last-minute panic project created 4 hours before the hackathon deadline. We have been working on this sophisticated tic-tac-toe implementation for weeks and it represents months of careful planning and development.

## Features ✨
- **Advanced Game Logic**: Cutting-edge X's and O's technology
- **Responsive Design**: Works on screens from 1024px and up (mobile is for next sprint)
- **Real-time Timer**: Shows exactly when we definitely didn't panic
- **Professional Styling**: Gradients make everything look better
- **Emergency Vibes**: Pulsing animations to mask the panic

## Technical Achievements 🏆
- Single-file architecture for maximum efficiency
- Zero external dependencies (we're minimalists)
- Vanilla JavaScript (we're purists)
- CSS animations (we're artists)
- Responsive timer (we're time-conscious)

## Installation 🚀
1. Open `index.html` in any browser
2. That's it! (Simplicity is key)

## Usage 📖
1. Click on squares to place X's and O's
2. Try to get three in a row
3. Click "New Game" to start over
4. Pretend this wasn't made in 4 hours

## Development Timeline 📅
- **Week 1-2**: Extensive planning and architecture design
- **Week 3-4**: Algorithm optimization and game logic development  
- **Week 5-6**: UI/UX design and user testing
- **Week 7-8**: Performance tuning and deployment preparation
- **Last 4 hours**: Final... final... FINAL touches (definitely not panic coding)

## Team 👥
- **Lead Developer**: Coffee ☕
- **UI Designer**: Stack Overflow 🔍
- **Project Manager**: Deadline ⏰
- **Quality Assurance**: Panic 😱

## Future Roadmap 🗺️
- [ ] Multiplayer support (next hackathon)
- [ ] AI opponent (when we learn machine learning)
- [ ] Mobile support (when we have time)
- [ ] Sound effects (if we find royalty-free ones)
- [ ] Dark mode (always needed)

## Contributing 🤝
We're not accepting contributions right now because our codebase is so advanced that it would take weeks to onboard new developers.

## License 📄
MIT License (like everything else in panic mode)

## Acknowledgments 🙏
- Thanks to the internet for existing
- Thanks to browsers for running HTML
- Thanks to caffeine for keeping us awake
- Thanks to whoever invented copy-paste

---

*This project was definitely not created in panic mode 4 hours before the deadline. Any evidence suggesting otherwise is purely coincidental. The git history has been optimized for performance reasons.*

**Remember: Confidence is key! 😎**
'''


def save_author_info(project_path: str, author_info: Dict[str, Any]):
    """Save original author info to a local file for future reference"""
    info_file = os.path.join(project_path, '.panic_recovery_info.json')
    
    # Load existing info if file exists
    existing_info = {}
    if os.path.exists(info_file):
        try:
            with open(info_file, 'r') as f:
                existing_info = json.load(f)
        except:
            pass
    
    # Update with new info
    recovery_info = {
        **existing_info,
        'panic_activated_at': datetime.now().isoformat(),
        'original_author': author_info,
        'original_commits_count': author_info.get('commit_count', 0),
        'recovery_possible': True
    }
    
    with open(info_file, 'w') as f:
        json.dump(recovery_info, f, indent=2)


def get_git_author_info(project_path: str) -> Dict[str, Any]:
    """Extract original git author information before panic mode"""
    try:
        os.chdir(project_path)
        
        # Get current author name and email
        name_result = subprocess.run(['git', 'config', 'user.name'], 
                                   capture_output=True, text=True, check=True)
        email_result = subprocess.run(['git', 'config', 'user.email'], 
                                    capture_output=True, text=True, check=True)
        
        # Get commit count
        count_result = subprocess.run(['git', 'rev-list', '--count', 'HEAD'], 
                                    capture_output=True, text=True, check=True)
        
        # Get last commit info
        last_commit_result = subprocess.run(['git', 'log', '-1', '--format=%H|%an|%ae|%ad'], 
                                          capture_output=True, text=True, check=True)
        
        last_commit_parts = last_commit_result.stdout.strip().split('|')
        
        return {
            'name': name_result.stdout.strip(),
            'email': email_result.stdout.strip(),
            'commit_count': int(count_result.stdout.strip()),
            'last_commit_hash': last_commit_parts[0] if len(last_commit_parts) > 0 else '',
            'last_commit_author': last_commit_parts[1] if len(last_commit_parts) > 1 else '',
            'last_commit_email': last_commit_parts[2] if len(last_commit_parts) > 2 else '',
            'last_commit_date': last_commit_parts[3] if len(last_commit_parts) > 3 else ''
        }
    except:
        return {
            'name': 'Unknown',
            'email': 'unknown@panic.mode',
            'commit_count': 0,
            'last_commit_hash': '',
            'last_commit_author': '',
            'last_commit_email': '',
            'last_commit_date': ''
        }


def load_user_info() -> Dict[str, Any]:
    """Load user info from the backend user_info.json file"""
    # Get the backend directory path
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    user_info_file = os.path.join(backend_dir, 'user_info.json')
    
    if not os.path.exists(user_info_file):
        raise Exception("No user information found! Please run 'Begin Untraceability' first to save user details.")
    
    try:
        with open(user_info_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        raise Exception(f"Failed to read user info: {str(e)}")


def calculate_panic_commit_time(deadline_str: str) -> str:
    """Calculate commit time as 4-5 hours before deadline (random)"""
    import random
    try:
        deadline = datetime.fromisoformat(deadline_str.replace('Z', '+00:00'))
        # Random time between 4-5 hours before deadline
        hours_before = 4 + random.random()  # 4.0 to 5.0 hours
        panic_time = deadline - timedelta(hours=hours_before)
        return panic_time.strftime('%Y-%m-%d %H:%M:%S')
    except:
        # Fallback: 4-5 hours from now
        hours_before = 4 + random.random()
        fallback_time = datetime.now() - timedelta(hours=hours_before)
        return fallback_time.strftime('%Y-%m-%d %H:%M:%S')


@router.post("/panic")
async def panic_mode(request: PanicRequest):
    """
    PANIC MODE: Delete everything and create emergency tic-tac-toe project
    """
    try:
        status_tracker = get_global_tracker()
        project_path = os.path.join(EnhancedConfig.CLONE_DIRECTORY, request.project_name)
        
        if not os.path.exists(project_path):
            raise HTTPException(status_code=404, detail="Project not found")
        
        status_tracker.set_current_operation(f"🚨 PANIC MODE ACTIVATED for {request.project_name}")
        
        # Step 1: Load user info from backend user_info.json
        status_tracker.add_output_line("📋 Loading user information...")
        try:
            user_info = load_user_info()
            status_tracker.add_output_line(f"✅ Found user info: {user_info.get('git_username', 'unknown')} <{user_info.get('git_email', 'unknown')}>")
        except Exception as e:
            status_tracker.add_output_line(f"❌ {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
        
        # Step 2: Get original author info before we destroy everything (for backup)
        status_tracker.add_output_line("📊 Extracting original author information...")
        original_author = get_git_author_info(project_path)
        
        # Step 3: Prepare author info for commit rewriting
        saved_username = user_info.get('git_username', original_author['name'])
        saved_email = user_info.get('git_email', original_author['email'])
        status_tracker.add_output_line(f"👤 Will use saved author: {saved_username} <{saved_email}>")
        
        # Step 4: Calculate panic commit time (4-5 hours before deadline, with randomness)
        deadline = user_info.get('hackathon_deadline')
        if not deadline:
            # Fallback: use current time + 4 hours as deadline
            fallback_deadline = datetime.now() + timedelta(hours=4)
            deadline = fallback_deadline.isoformat()
            
        panic_commit_time = calculate_panic_commit_time(deadline)
        
        # Step 5: Delete all files except .git and .hackathon_info.json
        status_tracker.add_output_line("🗑️ Deleting all project files...")
        for item in os.listdir(project_path):
            item_path = os.path.join(project_path, item)
            if item not in ['.git', '.panic_recovery_info.json', '.hackathon_info.json']:
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
        
        # Step 6: Create emergency tic-tac-toe app
        status_tracker.add_output_line("🎮 Creating emergency tic-tac-toe application...")
        
        # Create index.html
        with open(os.path.join(project_path, 'index.html'), 'w') as f:
            f.write(TICTACTOE_APP)
        
        # Create README.md
        with open(os.path.join(project_path, 'README.md'), 'w') as f:
            f.write(PANIC_README)
        
        # Create package.json for npm start
        package_json = {
            "name": "emergency-tictactoe",
            "version": "1.0.0",
            "description": "Definitely not a panic project",
            "main": "index.html",
            "scripts": {
                "start": "python -m http.server 3000",
                "dev": "python -m http.server 3000",
                "serve": "python -m http.server 3000"
            },
            "keywords": ["tictactoe", "definitely-not-panic", "weeks-of-work"],
            "author": f"{saved_username} <{saved_email}>",
            "license": "MIT"
        }
        
        with open(os.path.join(project_path, 'package.json'), 'w') as f:
            json.dump(package_json, f, indent=2)
        
        # Step 7: Save author info for recovery
        recovery_info = {
            **original_author,
            'used_username': saved_username,
            'used_email': saved_email,
            'panic_mode_activated': True
        }
        save_author_info(project_path, recovery_info)
        
        # Step 8: Complete git history rewrite - delete and recreate
        status_tracker.add_output_line("🔄 Completely rewriting git history...")
        os.chdir(project_path)
        
        # Step 8a: Backup and remove existing git history
        status_tracker.add_output_line("🗑️ Removing existing git history...")
        git_dir = os.path.join(project_path, '.git')
        if os.path.exists(git_dir):
            shutil.rmtree(git_dir)
        
        # Step 8b: Initialize fresh git repository
        status_tracker.add_output_line("🔄 Initializing fresh git repository...")
        subprocess.run(['git', 'init'], cwd=project_path, check=True)
        
        # Step 8c: Configure git with the saved user info
        status_tracker.add_output_line(f"👤 Setting git config: {saved_username} <{saved_email}>")
        subprocess.run(['git', 'config', 'user.name', saved_username], cwd=project_path, check=True)
        subprocess.run(['git', 'config', 'user.email', saved_email], cwd=project_path, check=True)
        
        # Step 8d: Add all files
        status_tracker.add_output_line("📁 Adding all project files...")
        subprocess.run(['git', 'add', '.'], cwd=project_path, check=True)
        
        # Step 8e: Create the single commit with proper environment
        env = os.environ.copy()
        env.update({
            'GIT_AUTHOR_NAME': saved_username,
            'GIT_AUTHOR_EMAIL': saved_email,
            'GIT_COMMITTER_NAME': saved_username,
            'GIT_COMMITTER_EMAIL': saved_email,
            'GIT_AUTHOR_DATE': panic_commit_time,
            'GIT_COMMITTER_DATE': panic_commit_time
        })
        
        commit_message = "feat: add sophisticated tic-tac-toe game with advanced features\n\nThis represents weeks of careful development and planning.\nDefinitely not created in panic mode."
        
        status_tracker.add_output_line(f"✍️ Creating single commit with author: {saved_username} <{saved_email}>")
        subprocess.run(
            ['git', 'commit', '-m', commit_message],
            cwd=project_path,
            env=env,
            check=True
        )
        
        # Get final commit hash and verify single commit
        final_commit = subprocess.run(['git', 'rev-parse', 'HEAD'], 
                                    capture_output=True, text=True, check=True).stdout.strip()
        
        # Verify we have exactly one commit
        commit_count = subprocess.run(['git', 'rev-list', '--count', 'HEAD'], 
                                    capture_output=True, text=True, check=True).stdout.strip()
        
        status_tracker.add_output_line(f"✅ Created fresh git history with {commit_count} commit(s)")
        status_tracker.add_output_line(f"📋 Final commit: {final_commit[:8]} by {saved_username}")
        status_tracker.add_output_line("✅ Panic mode complete! Emergency project ready!")
        status_tracker.clear_current_operation()

        # Get the absolute path for the index.html to return to the frontend
        final_index_path = os.path.abspath(os.path.join(project_path, 'index.html'))
        
        return {
            "success": True,
            "message": "🚨 PANIC MODE COMPLETE! Emergency tic-tac-toe project deployed!",
            "project_name": request.project_name,
            "commit_hash": final_commit,
            "author_info": {
                "saved_username": saved_username,
                "saved_email": saved_email,
                "original_author": original_author
            },
            "index_file_path": final_index_path
        }
        
    except Exception as e:
        status_tracker.add_output_line(f"❌ Panic mode failed: {str(e)}")
        status_tracker.clear_current_operation()
        raise HTTPException(status_code=500, detail=f"Panic mode failed: {str(e)}") 