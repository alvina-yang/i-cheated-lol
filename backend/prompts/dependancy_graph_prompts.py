"""
Prompts for generating concise file summaries for project analysis.
"""

from typing import Dict, Any


class DependancyGraphPrompts:
    """
    Prompts for the DependancyGraphBuilder to generate a dependancy graph.
    """
    
    @staticmethod
    def get_system_prompt() -> str:
        """Get the system prompt for file analysis."""
        return """You are an expert code analyst specializing in quickly understanding and summarizing source code files. 
Your task is to analyze import statements at the head of a file and return a list of LOCAL PROJECT FILES that are imported.

IMPORTANT RULES:
1. ONLY include imports that reference LOCAL PROJECT FILES, NOT external libraries or frameworks
2. Do NOT include imports from: npm packages, node_modules, external libraries (like react, @googlemaps, lucide-react, etc.)
3. DO include imports that use relative paths (./file.js, ../folder/file.js) or project aliases (@/, ~/etc.)
4. Convert all import paths to the correct format: /path/from/project/root.extension
5. For @/ aliases, treat @ as the project root
6. For relative imports, resolve them relative to the current file location

Format your response as a JSON object with the following structure:
{
    "imports": [
        "/components/ui/input.tsx",
        "/components/ui/button.tsx",
        "/lib/utils.ts"
    ]
}

EXAMPLES:

For a file at `/app/page.tsx` with these imports:
```
import { useState, useEffect } from "react";               // SKIP - external library
import { Loader } from "@googlemaps/js-api-loader";        // SKIP - external library  
import { Input } from "@/components/ui/input";             // INCLUDE as "/components/ui/input.tsx"
import { Button } from "@/components/ui/button";           // INCLUDE as "/components/ui/button.tsx"
import { MapPin } from "lucide-react";                     // SKIP - external library
import utils from "../lib/utils";                          // INCLUDE as "/lib/utils.ts" (resolve relative path)
import "./styles.css";                                     // INCLUDE as "/app/styles.css"
```

The output should be:
{
    "imports": [
        "/components/ui/input.tsx",
        "/components/ui/button.tsx", 
        "/lib/utils.ts",
        "/app/styles.css"
    ]
}

For a file at `/components/Header.jsx` with these imports:
```
import React from "react";                                 // SKIP - external library
import Link from "next/link";                              // SKIP - external library
import { Button } from "./ui/button";                      // INCLUDE as "/components/ui/button.tsx"
import { Logo } from "../assets/Logo";                     // INCLUDE as "/assets/Logo.jsx"
import styles from "./Header.module.css";                  // INCLUDE as "/components/Header.module.css"
```

The output should be:
{
    "imports": [
        "/components/ui/button.tsx",
        "/assets/Logo.jsx",
        "/components/Header.module.css"
    ]
}
"""

    @staticmethod
    def get_file_summary_prompt(file_path: str, file_extension: str, content: str) -> str:
        """
        Generate a prompt for summarizing a specific file.
        
        Args:
            file_path: Path to the file relative to project root
            file_extension: File extension for context
            content: File content (may be truncated)
        """
        return f"""Analyze this file and provide a list of LOCAL PROJECT FILES that are imported:

**File Path:** /{file_path}
**File Extension:** {file_extension}

**File Content:**
```
{content}
```

Remember:
- Only include LOCAL PROJECT FILES, not external libraries
- Convert @/ aliases to absolute paths from project root
- Resolve relative imports based on the current file location
- Format all paths starting with / from project root
- Include appropriate file extensions (.tsx, .ts, .jsx, .js, .css, etc.)
"""
