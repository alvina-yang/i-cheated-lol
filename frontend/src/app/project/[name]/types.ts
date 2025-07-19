export interface FileNode {
  name: string;
  type: 'file' | 'directory';
  path: string;
  content?: string;
  size?: number;
  extension?: string;
  children?: FileNode[];
}

export interface ProjectData {
  name: string;
  description: string;
  technologies: string[];
  stars: number;
  forks: number;
  language: string;
  files: FileNode[];
  readme?: string;
}

export interface TeamMember {
  username: string;
  email: string;
  name: string;
}

export interface DiffData {
  operation: string;
  fileName: string;
  originalContent: string;
  modifiedContent: string;
  changesSummary: string;
  linesAdded: number;
  variablesChanged?: any;
} 