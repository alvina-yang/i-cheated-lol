"""
Prompts for generating compelling hackathon presentation scripts.
"""

from typing import Dict, Any


class PresentationPrompts:
    """
    Prompts for the PresentationAgent to generate compelling hackathon pitch scripts.
    """
    
    @staticmethod
    def get_system_prompt() -> str:
        """Get the system prompt for the presentation script generator."""
        return """You are an expert hackathon pitch coach and presentation script writer. You specialize in creating compelling, engaging, and professional presentation scripts for hackathon teams to present to judges.

Your goal is to transform technical project information into a narrative that:
- Clearly communicates the problem being solved
- Demonstrates the solution's value and innovation
- Shows technical competency without overwhelming judges
- Follows a logical, engaging flow
- Fits within typical hackathon time constraints (3-5 minutes)
- Uses accessible language that both technical and non-technical judges can understand

You should create scripts that are:
- Well-structured with clear sections
- Engaging and memorable
- Professional yet conversational
- Include speaker notes and timing guidance
- Formatted for easy reading during presentation"""

    @staticmethod
    def get_presentation_script_prompt(context: Dict[str, Any]) -> str:
        """
        Generate a prompt for creating a presentation script based on project context.
        
        Args:
            context: Dictionary containing project information
                - project_name: Name of the project
                - readme_content: Content from README file
                - project_structure: Overview of project structure
                - technologies: List of technologies used
        """
        project_name = context.get("project_name", "Unknown Project")
        readme_content = context.get("readme_content", "No README available")
        project_structure = context.get("project_structure", "Structure unknown")
        technologies = context.get("technologies", "Technologies not detected")
        
        return f"""Create a compelling hackathon presentation script for the project "{project_name}".

**Project Context:**

**README Content:**
{readme_content}

**Project Structure:**
{project_structure}

**Technologies Used:**
{technologies}

**Instructions:**
Generate a professional 3-5 minute hackathon presentation script that includes:

1. **Opening Hook** (30 seconds)
   - Attention-grabbing opening
   - Clear problem statement
   - Why this matters

2. **Solution Overview** (60-90 seconds)
   - What the project does
   - Key features and innovation
   - How it solves the problem

3. **Technical Implementation** (60-90 seconds)
   - Architecture overview (high-level)
   - Key technologies and why chosen
   - Technical challenges overcome
   - Keep it accessible for non-technical judges

4. **Demo Transition** (15-30 seconds)
   - Bridge to demonstration
   - What judges will see
   - Key points to highlight during demo

5. **Impact & Future** (30-60 seconds)
   - Real-world applications
   - Potential impact
   - Scalability and next steps

6. **Closing** (15-30 seconds)
   - Call to action
   - Team appreciation
   - Memorable closing statement

**Formatting Requirements:**
- Use clear section headers
- Include [PAUSE] markers for timing
- Add (Speaker Notes) for delivery guidance
- Suggest timing for each section
- Use conversational, engaging language
- Make it sound natural, not robotic
- Include transition phrases between sections

**Additional Guidelines:**
- If README content is sparse, infer reasonable features based on project structure and technologies
- Focus on solving real problems, not just technical complexity
- Balance technical details with business value
- Make it memorable and differentiate from other projects
- Include specific technical details that show competency
- Use storytelling elements where appropriate

Generate a complete, ready-to-deliver presentation script that will impress hackathon judges and clearly communicate the project's value."""

    @staticmethod
    def get_executive_summary_prompt(context: Dict[str, Any]) -> str:
        """Generate a brief executive summary for quick reference."""
        project_name = context.get("project_name", "Unknown Project")
        readme_content = context.get("readme_content", "No README available")
        
        return f"""Based on this project information for "{project_name}":

{readme_content}

Create a 2-3 sentence executive summary that captures:
1. What the project does
2. The key innovation or value proposition
3. The target audience or use case

Keep it concise, compelling, and suitable for a hackathon elevator pitch.""" 