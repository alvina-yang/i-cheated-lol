#!/usr/bin/env python3
"""
Chameleon Hackathon Project Discovery System - Main Entry Point

A sophisticated system for discovering, analyzing, and cloning hackathon winner projects
using LangChain agents and deep code analysis.

Usage:
    python main_new.py                    # Interactive mode
    python main_new.py react nextjs      # Search for projects using React and Next.js
    python main_new.py python flask      # Search for projects using Python and Flask
"""

import sys
from typing import List

from core.config import Config
from workflows.discovery_chain import TechnologyProjectDiscoveryChain


def parse_technologies_from_args() -> List[str]:
    """Parse technologies from command line arguments."""
    if len(sys.argv) > 1:
        technologies = [tech.strip() for tech in sys.argv[1:] if tech.strip()]
        return technologies
    return []


def get_technologies_interactive() -> List[str]:
    """Get technologies from user input in interactive mode."""
    print("Technology Project Discovery Tool")
    print("=" * 40)
    print("Enter technologies separated by commas (e.g., 'nextjs, claude, gpt')")
    print("Or just press Enter for general projects")
    print()
    
    user_input = input("Technologies: ").strip()
    
    if not user_input:
        return []
    
    # Parse comma-separated technologies
    technologies = [tech.strip() for tech in user_input.split(',') if tech.strip()]
    return technologies


def print_welcome_banner():
    """Print a welcome banner with system information."""
    print()
    print("🔍 Chameleon Hackathon Project Discovery System")
    print("=" * 50)
    print("🎯 Mission: Find and clone innovative hackathon projects")
    print("🤖 Powered by: LangChain agents with deep code analysis")
    print("🔧 Features: GitHub search, AI validation, automatic cloning")
    print()


def print_technology_info(technologies: List[str]):
    """Print information about the technologies being searched."""
    if technologies:
        print(f"🔎 Searching for hackathon projects using: {', '.join(technologies)}")
    else:
        print("🔎 Searching for general hackathon winner projects")
    print()


def main():
    """Main entry point for the Chameleon discovery system."""
    try:
        # Print welcome banner
        print_welcome_banner()
        
        # Get technologies from command line or interactive input
        technologies = parse_technologies_from_args()
        
        if not technologies:
            technologies = get_technologies_interactive()
        
        # Display search information
        print_technology_info(technologies)
        
        # Validate configuration
        try:
            Config.validate()
        except ValueError as e:
            print(f"❌ Configuration Error: {e}")
            print("Please check your .env file and ensure OPENAI_API_KEY is set.")
            sys.exit(1)
        
        # Initialize and execute the discovery chain
        discovery_chain = TechnologyProjectDiscoveryChain()
        
        print("🚀 Starting discovery workflow...")
        print()
        
        # Execute the workflow
        results = discovery_chain.execute(technologies)
        
        # Handle results
        if results['success']:
            print("✅ Discovery workflow completed successfully!")
            if results['selected_project']:
                project = results['selected_project']
                print(f"🎉 Successfully discovered and cloned: {project['name']}")
                print(f"📂 Location: {results['clone_directory']}")
                print(f"⭐ Stars: {project['stars']}")
                print(f"🔗 URL: {project['url']}")
        else:
            print("❌ Discovery workflow completed with issues.")
            workflow_state = results['workflow_state']
            
            if workflow_state['errors']:
                print("🔧 Issues encountered:")
                for error in workflow_state['errors']:
                    print(f"   • {error}")
            
            print("\n💡 Suggestions:")
            print("   • Try different technologies")
            print("   • Check your internet connection")
            print("   • Verify your GitHub API access")
        
        print()
        print("Thank you for using Chameleon! 🦎")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Discovery interrupted by user.")
        print("Goodbye! 👋")
        sys.exit(0)
    
    except Exception as e:
        print(f"\n💥 Unexpected error occurred: {e}")
        print("Please check your configuration and try again.")
        sys.exit(1)


if __name__ == "__main__":
    main() 