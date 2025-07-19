import { FileNode, TeamMember } from "./types";
import { Folder, FolderOpen, File, Code2, FileText, Image as ImageIcon, Settings } from "lucide-react";
import { LANGUAGE_MAP, DEFAULT_LANGUAGE } from "./constants/languageMap";
import { CODE_EXTENSIONS, IMAGE_EXTENSIONS, CONFIG_EXTENSIONS, README_PATTERNS, JSX_ELEMENT_PATTERN } from "./constants/fileExtensions";

// Team member management utilities
export const createAddTeamMember = (teamMembers: TeamMember[]): TeamMember[] => {
  return [...teamMembers, { username: '', email: '', name: '' }];
};

export const createRemoveTeamMember = (teamMembers: TeamMember[], index: number): TeamMember[] => {
  return teamMembers.filter((_, i) => i !== index);
};

export const createUpdateTeamMember = (
  teamMembers: TeamMember[], 
  index: number, 
  field: keyof TeamMember, 
  value: string
): TeamMember[] => {
  const updated = [...teamMembers];
  updated[index] = { ...updated[index], [field]: value };
  return updated;
};

// Folder state management utilities
export const toggleFolder = (expandedFolders: Set<string>, folderPath: string): Set<string> => {
  const newExpanded = new Set(expandedFolders);
  if (newExpanded.has(folderPath)) {
    newExpanded.delete(folderPath);
  } else {
    newExpanded.add(folderPath);
  }
  return newExpanded;
};

// Strip markdown code block wrappers from content
export const stripMarkdownWrapper = (content: string): string => {
  // Check if content starts with ```language and ends with ```
  const startMatch = content.match(/^```[\w]*\n([\s\S]*?)(?:\n```)?$/);
  
  if (startMatch) {
    let innerContent = startMatch[1];
    // Remove trailing ``` if present
    if (innerContent.endsWith('\n```')) {
      innerContent = innerContent.slice(0, -4);
    } else if (innerContent.endsWith('```')) {
      innerContent = innerContent.slice(0, -3);
    }
    return innerContent;
  }
  
  return content; // Return original if no wrapper found
};

// Map file extensions to syntax highlighter language identifiers
export const getSyntaxLanguage = (extension: string, content?: string): string => {
  const ext = extension.toLowerCase().replace('.', '');
  
  // Special handling for TSX files - detect if it contains JSX elements
  if (ext === 'tsx') {
    if (content && JSX_ELEMENT_PATTERN.test(content)) {
      return 'jsx'; // Contains JSX elements, use JSX highlighting
    }
    return 'typescript'; // No JSX elements, use TypeScript highlighting
  }
  
  return LANGUAGE_MAP[ext] || DEFAULT_LANGUAGE;
};

export const getFileIcon = (file: FileNode, expandedFolders: Set<string>) => {
  if (file.type === 'directory') {
    return expandedFolders.has(file.path) ? (
      <FolderOpen className="h-4 w-4 text-blue-400" />
    ) : (
      <Folder className="h-4 w-4 text-blue-500" />
    );
  }

  const extension = file.extension?.toLowerCase() || '';
  const fileName = file.name.toLowerCase();

  if (README_PATTERNS.some(pattern => fileName.includes(pattern))) {
    return <FileText className="h-4 w-4 text-green-400" />;
  }
  
  if (CODE_EXTENSIONS.includes(extension)) {
    return <Code2 className="h-4 w-4 text-yellow-400" />;
  }
  
  if (IMAGE_EXTENSIONS.includes(extension)) {
    return <ImageIcon className="h-4 w-4 text-purple-400" />;
  }
  
  if (CONFIG_EXTENSIONS.includes(extension)) {
    return <Settings className="h-4 w-4 text-orange-400" />;
  }

  return <File className="h-4 w-4 text-zinc-400" />;
}; 