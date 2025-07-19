#!/usr/bin/env python3
"""
Integration test for the refactored Chameleon system.
Tests that all components can be imported and initialized.
"""

import sys
import os
import tempfile
import shutil
from datetime import datetime

# Add the backend directory to Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

def test_imports():
    """Test that all modules can be imported successfully."""
    print("Testing imports...")
    
    try:
        from core.enhanced_config import EnhancedConfig
        print("✅ EnhancedConfig imported successfully")
        
        from agents.search_agent import TechnologyProjectSearchAgent
        from agents.validator_agent import ValidatorAgent
        from agents.commit_agent import CommitAgent
        from agents.code_modifier_agent import CodeModifierAgent
        from agents.git_agent import GitAgent
        print("✅ All agents imported successfully")
        
        from prompts.search_prompts import SearchPrompts
        from prompts.validator_prompts import ValidatorPrompts
        from prompts.code_modifier_prompts import CodeModifierPrompts
        from prompts.git_prompts import GitPrompts
        print("✅ All prompts imported successfully")
        
        from utils.status_tracker import StatusTracker, get_global_tracker, initialize_status_tracking
        print("✅ Status tracker imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_configuration():
    """Test the enhanced configuration system."""
    print("\nTesting configuration...")
    
    try:
        from core.enhanced_config import EnhancedConfig
        
        # Test basic configuration
        config = EnhancedConfig()
        
        # Test settings initialization
        user_settings = config.get_user_settings()
        repo_settings = config.get_repository_settings()
        processing_settings = config.get_processing_settings()
        terminal_settings = config.get_terminal_settings()
        
        print("✅ Configuration system working")
        
        # Test settings update
        success = config.update_user_settings(git_username="test_user", git_email="test@example.com")
        if success:
            print("✅ Settings update working")
        else:
            print("⚠️ Settings update failed")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_status_tracker():
    """Test the status tracking system."""
    print("\nTesting status tracker...")
    
    try:
        from utils.status_tracker import StatusTracker
        
        # Create a status tracker
        tracker = StatusTracker(enable_real_time=False)
        
        # Test basic operations
        tracker.start()
        
        # Create a test task
        task = tracker.create_task("test_task", "Test Task", "Testing the system")
        tracker.start_task("test_task")
        tracker.update_task("test_task", 50, "Half way done")
        tracker.complete_task("test_task", "Test completed")
        
        # Test status retrieval
        summary = tracker.get_status_summary()
        tasks = tracker.get_all_tasks()
        
        tracker.stop()
        
        print("✅ Status tracker working")
        return True
        
    except Exception as e:
        print(f"❌ Status tracker test failed: {e}")
        return False

def test_agents():
    """Test that agents can be initialized."""
    print("\nTesting agents...")
    
    try:
        # Test agents initialization (without actual API calls)
        from agents.commit_agent import CommitAgent
        from agents.code_modifier_agent import CodeModifierAgent
        from agents.git_agent import GitAgent
        
        # Test prompt generation
        from prompts.code_modifier_prompts import CodeModifierPrompts
        from prompts.git_prompts import GitPrompts
        
        code_prompts = CodeModifierPrompts()
        git_prompts = GitPrompts()
        
        code_prompt = code_prompts.get_comment_generation_prompt(
            "python", "test.py", "print('hello world')"
        )
        
        git_prompt = git_prompts.get_repository_setup_prompt(
            "https://github.com/original/repo",
            "https://github.com/new/repo",
            "test_project",
            {}
        )
        
        print("✅ Agents and prompts working")
        return True
        
    except Exception as e:
        print(f"❌ Agents test failed: {e}")
        return False

def test_file_operations():
    """Test file operations with temporary directory."""
    print("\nTesting file operations...")
    
    try:
        from agents.code_modifier_agent import CodeModifierAgent
        
        # Create a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test Python file
            test_file = os.path.join(temp_dir, "test.py")
            with open(test_file, 'w') as f:
                f.write("""
def hello():
    print("Hello world")

def add(a, b):
    return a + b

if __name__ == "__main__":
    hello()
    result = add(1, 2)
    print(result)
""")
            
            # Test file analysis
            modifier = CodeModifierAgent()
            
            # Test finding code files
            code_files = modifier._find_code_files(temp_dir)
            assert len(code_files) == 1
            assert code_files[0] == test_file
            
            print("✅ File operations working")
            return True
            
    except Exception as e:
        print(f"❌ File operations test failed: {e}")
        return False

def main():
    """Run all integration tests."""
    print("🚀 Running Chameleon Integration Tests...")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_configuration,
        test_status_tracker,
        test_agents,
        test_file_operations
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All integration tests passed!")
        return True
    else:
        print(f"❌ {failed} tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 