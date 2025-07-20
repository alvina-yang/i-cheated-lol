#!/usr/bin/env python3
"""
Test script for dependency graph analysis using the outlined prompts.
Run this to test the dependency parsing functionality on a project.
"""

import sys
import os
import asyncio
import json

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.dependancy_graph_builder import DependancyGraphBuilder
from core.enhanced_config import EnhancedConfig


async def test_dependency_analysis(project_name: str | None = None):
    """Test the dependency graph analysis on a project."""
    
    if not project_name:
        # Use a project from HackathonProject or ask user
        available_projects = []
        hackathon_dir = os.path.expanduser("~/HackathonProject")
        
        if os.path.exists(hackathon_dir):
            available_projects = [d for d in os.listdir(hackathon_dir) 
                                if os.path.isdir(os.path.join(hackathon_dir, d)) 
                                and not d.startswith('.')]
        
        if available_projects:
            print("Available projects in HackathonProject:")
            for i, proj in enumerate(available_projects, 1):
                print(f"  {i}. {proj}")
            
            choice = input(f"\nEnter project number (1-{len(available_projects)}) or project name: ").strip()
            
            if choice.isdigit() and 1 <= int(choice) <= len(available_projects):
                project_name = available_projects[int(choice) - 1]
            else:
                project_name = choice
        else:
            project_name = input("Enter project name: ").strip()
    
    print(f"\n🔍 Starting dependency analysis for: {project_name}")
    print("=" * 60)
    
    # Initialize the dependency graph builder
    dependency_builder = DependancyGraphBuilder()
    
    # Set project path
    project_path = os.path.join(os.path.expanduser("~"), "HackathonProject", project_name)
    
    if not os.path.exists(project_path):
        print(f"❌ Project not found: {project_path}")
        return
    
    # Execute dependency analysis
    task_data = {"project_path": project_path}
    result = dependency_builder.execute(task_data)
    
    print("\n📊 ANALYSIS RESULTS:")
    print("=" * 60)
    
    if result.get("success", False):
        dependancy_graph = result.get("dependancy_graph", {})
        summary = result.get("summary", {})
        
        print(f"✅ {result.get('message', 'Analysis completed')}")
        print(f"\n📈 SUMMARY:")
        print(f"  • Total files analyzed: {summary.get('total_files_analyzed', 0)}")
        print(f"  • Total imports found: {summary.get('total_imports_found', 0)}")
        print(f"  • Files with imports: {summary.get('files_with_imports', 0)}")
        
        # Show detailed dependency graph
        print(f"\n🗂️  DEPENDENCY GRAPH:")
        print("=" * 60)
        
        if dependancy_graph:
            for file_path, imports in dependancy_graph.items():
                print(f"\n📁 {file_path}")
                if imports:
                    for import_file in imports:
                        print(f"  └─ imports: {import_file}")
                else:
                    print(f"  └─ (no local imports)")
        
        # Generate and show visualization
        visualization = dependency_builder.get_dependency_graph_visualization(dependancy_graph)
        
        print(f"\n📋 TEXT VISUALIZATION:")
        print("=" * 60)
        print(visualization)
        
        # Save the results
        graph_file = dependency_builder.save_dependency_graph(project_path, dependancy_graph)
        if graph_file:
            print(f"\n💾 Results saved to: {graph_file}")
        
        # Show some example API usage
        print(f"\n🌐 API USAGE EXAMPLES:")
        print("=" * 60)
        print(f"curl -X POST http://localhost:8000/api/dependency/analyze \\")
        print(f"  -H 'Content-Type: application/json' \\")
        print(f"  -d '{{\"project_name\": \"{project_name}\"}}'")
        print()
        print(f"curl http://localhost:8000/api/dependency/graph/{project_name}")
        
    else:
        print(f"❌ {result.get('message', 'Analysis failed')}")


def main():
    """Main function to run the test."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test dependency graph analysis")
    parser.add_argument("--project", "-p", help="Project name to analyze")
    parser.add_argument("--list", "-l", action="store_true", help="List available projects")
    
    args = parser.parse_args()
    
    if args.list:
        hackathon_dir = os.path.expanduser("~/HackathonProject")
        if os.path.exists(hackathon_dir):
            projects = [d for d in os.listdir(hackathon_dir) 
                       if os.path.isdir(os.path.join(hackathon_dir, d)) 
                       and not d.startswith('.')]
            print("Available projects:")
            for proj in projects:
                print(f"  - {proj}")
        else:
            print("No HackathonProject directory found")
        return
    
    # Run the test
    asyncio.run(test_dependency_analysis(args.project))


if __name__ == "__main__":
    main() 