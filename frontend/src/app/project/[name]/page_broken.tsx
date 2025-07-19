"use client";

import { useState, useEffect, useRef } from "react";
import { useParams } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { AlertDialog, AlertDialogAction, AlertDialogContent, AlertDialogDescription, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from "@/components/ui/alert-dialog";
import { 
  ArrowLeft, 
  Folder, 
  FolderOpen, 
  File, 
  Code2, 
  FileText, 
  Image as ImageIcon,
  Settings,
  Terminal,
  Search,
  ChevronRight,
  ChevronDown,
  Copy,
  Download,
  Eye,
  GitBranch,
  Shield,
  Calendar,
  User,
  Mail,
  MessageCircle,
  Variable,
  Loader2
} from "lucide-react";
import { useRouter } from "next/navigation";
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

interface FileNode {
  name: string;
  type: 'file' | 'directory';
  path: string;
  content?: string;
  size?: number;
  extension?: string;
  children?: FileNode[];
}

interface ProjectData {
  name: string;
  description: string;
  technologies: string[];
  stars: number;
  forks: number;
  language: string;
  files: FileNode[];
  readme?: string;
}

export default function ProjectPage() {
  const params = useParams();
  const router = useRouter();
  const projectName = params.name as string;
  
  const [project, setProject] = useState<ProjectData | null>(null);
  const [selectedFile, setSelectedFile] = useState<FileNode | null>(null);
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Untraceability modal state
  const [showUntraceabilityModal, setShowUntraceabilityModal] = useState(false);
  const [untraceabilityLoading, setUntraceabilityLoading] = useState(false);
  const [hackathonDate, setHackathonDate] = useState('');
  const [hackathonStartTime, setHackathonStartTime] = useState('');
  const [hackathonDuration, setHackathonDuration] = useState('48');
  const [teamMembers, setTeamMembers] = useState<Array<{username: string, email: string, name: string}>>([]);
  const [targetRepositoryUrl, setTargetRepositoryUrl] = useState('');
  const [generateCommitMessages, setGenerateCommitMessages] = useState(false);
  
  // File operation state
  const [fileOperationLoading, setFileOperationLoading] = useState<string | null>(null); // Track which operation is loading
  const [showDiffModal, setShowDiffModal] = useState(false);
  const [diffData, setDiffData] = useState<any>(null);
  
  // Progress tracking state (simplified - no terminal streaming)
  const [showProgressModal, setShowProgressModal] = useState(false);

  // Removed terminal streaming functions

  useEffect(() => {
    if (projectName) {
      fetchProjectFiles();
    }
  }, [projectName]);

  const fetchProjectFiles = async () => {
    try {
      setLoading(true);
      const response = await fetch(`http://localhost:8000/api/project/${encodeURIComponent(projectName)}/files`);
      
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to fetch project files: ${response.status} - ${errorText}`);
      }
      
      const data = await response.json();
      setProject(data);
      
      // Auto-expand first level and select README if available
      const firstLevelFolders = new Set<string>();
      data.files.forEach((file: FileNode) => {
        if (file.type === 'directory') {
          firstLevelFolders.add(file.path);
        }
      });
      setExpandedFolders(firstLevelFolders);
      
      // Auto-select README file
      const readmeFile = findReadmeFile(data.files);
      if (readmeFile) {
        setSelectedFile(readmeFile);
      }
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const findReadmeFile = (files: FileNode[]): FileNode | null => {
    for (const file of files) {
      if (file.type === 'file' && file.name.toLowerCase().includes('readme')) {
        return file;
      }
      if (file.type === 'directory' && file.children) {
        const found = findReadmeFile(file.children);
        if (found) return found;
      }
    }
    return null;
  };

  const toggleFolder = (path: string) => {
    const newExpanded = new Set(expandedFolders);
    if (newExpanded.has(path)) {
      newExpanded.delete(path);
    } else {
      newExpanded.add(path);
    }
    setExpandedFolders(newExpanded);
  };

  const selectFile = async (file: FileNode) => {
    if (file.type === 'file') {
      try {
        const response = await fetch(`http://localhost:8000/api/project/${encodeURIComponent(projectName)}/file?path=${encodeURIComponent(file.path)}`);
        if (response.ok) {
          const content = await response.text();
          setSelectedFile({ ...file, content });
        }
      } catch (err) {
        console.error('Failed to load file content:', err);
      }
    }
  };

  const getFileIcon = (file: FileNode) => {
    if (file.type === 'directory') {
      return expandedFolders.has(file.path) ? (
        <FolderOpen className="h-4 w-4 text-blue-400" />
      ) : (
        <Folder className="h-4 w-4 text-blue-500" />
      );
    }

    const extension = file.extension?.toLowerCase() || '';
    const fileName = file.name.toLowerCase();

    if (fileName.includes('readme')) {
      return <FileText className="h-4 w-4 text-green-400" />;
    }
    
    if (['js', 'ts', 'jsx', 'tsx', 'py', 'java', 'cpp', 'c', 'go', 'rs', 'php'].includes(extension)) {
      return <Code2 className="h-4 w-4 text-yellow-400" />;
    }
    
    if (['png', 'jpg', 'jpeg', 'gif', 'svg', 'webp'].includes(extension)) {
      return <ImageIcon className="h-4 w-4 text-purple-400" />;
    }
    
    if (['json', 'yml', 'yaml', 'toml', 'xml'].includes(extension)) {
      return <Settings className="h-4 w-4 text-orange-400" />;
    }

    return <File className="h-4 w-4 text-zinc-400" />;
  };

  const getLanguageFromExtension = (extension: string): string => {
    const langMap: Record<string, string> = {
      'js': 'javascript',
      'jsx': 'javascript',
      'ts': 'typescript',
      'tsx': 'typescript',
      'py': 'python',
      'java': 'java',
      'cpp': 'cpp',
      'c': 'c',
      'go': 'go',
      'rs': 'rust',
      'php': 'php',
      'html': 'html',
      'css': 'css',
      'scss': 'scss',
      'json': 'json',
      'yml': 'yaml',
      'yaml': 'yaml',
      'md': 'markdown',
      'sh': 'bash',
      'sql': 'sql',
    };
    return langMap[extension.toLowerCase()] || 'text';
  };

  const renderFileTree = (files: FileNode[], level = 0) => {
    return files.map((file) => (
      <div key={file.path} className="select-none">
        <div
          className={`flex items-center space-x-2 px-2 py-1.5 rounded cursor-pointer hover:bg-zinc-800/50 transition-colors ${
            selectedFile?.path === file.path ? 'bg-blue-600/20 border-l-2 border-blue-400' : ''
          }`}
          style={{ paddingLeft: `${level * 16 + 8}px` }}
          onClick={() => {
            if (file.type === 'directory') {
              toggleFolder(file.path);
            } else {
              selectFile(file);
            }
          }}
        >
          {file.type === 'directory' && (
            <motion.div
              animate={{ rotate: expandedFolders.has(file.path) ? 90 : 0 }}
              transition={{ duration: 0.2 }}
            >
              <ChevronRight className="h-3 w-3 text-zinc-500" />
            </motion.div>
          )}
          {getFileIcon(file)}
          <span className="text-sm text-zinc-300 truncate">{file.name}</span>
          {file.type === 'file' && file.size && (
            <span className="text-xs text-zinc-500 ml-auto">
              {(file.size / 1024).toFixed(1)}KB
            </span>
          )}
        </div>
        
        {file.type === 'directory' && file.children && expandedFolders.has(file.path) && (
          <AnimatePresence>
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.2 }}
            >
              {renderFileTree(file.children, level + 1)}
            </motion.div>
          </AnimatePresence>
        )}
      </div>
    ));
  };

  // Strip markdown code block wrappers from AI-modified content
  const stripMarkdownWrapper = (content: string): string => {
    // Remove markdown code block wrappers like ```typescript\n...content...\n```
    const codeBlockRegex = /^```[\w-]*\n([\s\S]*?)\n```$/;
    const match = content.match(codeBlockRegex);
    if (match) {
      return match[1]; // Return just the content inside the code block
    }
    
    // Also handle cases where there might be extra whitespace or no closing ```
    const startRegex = /^```[\w-]*\n([\s\S]*)$/;
    const startMatch = content.match(startRegex);
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
  const getSyntaxLanguage = (extension: string, content?: string): string => {
    const ext = extension.toLowerCase().replace('.', '');
    
    // Special handling for TSX files - detect if it contains JSX elements
    if (ext === 'tsx') {
      if (content && (content.includes('<') && content.includes('>'))) {
        return 'jsx'; // Contains JSX elements, use JSX highlighting
      }
      return 'typescript'; // No JSX elements, use TypeScript highlighting
    }
    
    const languageMap: { [key: string]: string } = {
      'js': 'javascript',
      'mjs': 'javascript',
      'jsx': 'jsx',
      'ts': 'typescript',
      'tsx': 'jsx', // Default for TSX (overridden by logic above)
      'py': 'python',
      'pyw': 'python',
      'java': 'java',
      'c': 'c',
      'cpp': 'cpp',
      'cc': 'cpp',
      'cxx': 'cpp',
      'c++': 'cpp',
      'h': 'c',
      'hpp': 'cpp',
      'hxx': 'cpp',
      'cs': 'csharp',
      'php': 'php',
      'php3': 'php',
      'php4': 'php',
      'php5': 'php',
      'phtml': 'php',
      'rb': 'ruby',
      'ruby': 'ruby',
      'go': 'go',
      'rs': 'rust',
      'swift': 'swift',
      'kt': 'kotlin',
      'kts': 'kotlin',
      'scala': 'scala',
      'sc': 'scala',
      'sh': 'bash',
      'bash': 'bash',
      'zsh': 'bash',
      'fish': 'bash',
      'ps1': 'powershell',
      'psm1': 'powershell',
      'sql': 'sql',
      'mysql': 'sql',
      'pgsql': 'sql',
      'html': 'markup',
      'htm': 'markup',
      'xhtml': 'markup',
      'xml': 'markup',
      'svg': 'markup',
      'css': 'css',
      'scss': 'scss',
      'sass': 'sass',
      'less': 'less',
      'json': 'json',
      'json5': 'json5',
      'jsonc': 'json',
      'yaml': 'yaml',
      'yml': 'yaml',
      'toml': 'toml',
      'ini': 'ini',
      'cfg': 'ini',
      'conf': 'nginx',
      'dockerfile': 'docker',
      'containerfile': 'docker',
      'md': 'markdown',
      'markdown': 'markdown',
      'mdx': 'mdx',
      'tex': 'latex',
      'r': 'r',
      'rmd': 'r',
      'matlab': 'matlab',
      'm': 'objectivec', // Could be Objective-C or MATLAB
      'mm': 'objectivec',
      'pl': 'perl',
      'pm': 'perl',
      'lua': 'lua',
      'vim': 'vim',
      'makefile': 'makefile',
      'mk': 'makefile',
      'cmake': 'cmake',
      'gradle': 'gradle',
      'groovy': 'groovy',
      'clj': 'clojure',
      'cljs': 'clojure',
      'hs': 'haskell',
      'elm': 'elm',
      'dart': 'dart',
      'vue': 'markup', // Vue files are essentially HTML templates
      'svelte': 'markup'
    };
    
    return languageMap[ext] || 'javascript'; // Default to JavaScript for better highlighting than 'text'
  };

  // Removed all streaming functions - replaced with simple loading

  const handleUntraceability = async () => {
    // Only validate git fields if commit generation is enabled
    if (generateCommitMessages && (!hackathonDate || !hackathonStartTime || !hackathonDuration)) {
      alert('Please fill in hackathon date, time, and duration for git commit generation');
      return;
    }
    
    // Ensure git commit generation is selected (since other options are now per-file)
    if (!generateCommitMessages) {
      alert('Please enable git commit generation to make the project untraceable');
      return;
    }

    setUntraceabilityLoading(true);
    setShowUntraceabilityModal(false);
    setShowProgressModal(true);
    
    try {
      const response = await fetch(`http://localhost:8000/api/project/${encodeURIComponent(projectName)}/make-untraceable`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          hackathon_date: hackathonDate,
          hackathon_start_time: hackathonStartTime,
          hackathon_duration: parseInt(hackathonDuration),
          team_members: teamMembers,
          target_repository_url: targetRepositoryUrl,
          generate_commit_messages: generateCommitMessages
        })
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to make project untraceable: ${response.status} - ${errorText}`);
      }

      const result = await response.json();
      
      // Complete the process
      setTimeout(() => {
        setUntraceabilityLoading(false);
        setShowProgressModal(false);
        alert('Project successfully made untraceable! 🕵️‍♂️');
        
        // Refresh the project to show updated files
        fetchProjectFiles();
      }, 3000);
      
    } catch (err) {
      console.error('Error making project untraceable:', err);
      alert(`Failed to make project untraceable: ${err instanceof Error ? err.message : 'Unknown error'}`);
      setUntraceabilityLoading(false);
      setShowProgressModal(false);
    }
  };

  // Removed terminal formatting functions

  const formatFileContent = (content: string, extension: string) => {
    const timestamp = line.match(/\[(\d{2}:\d{2}:\d{2})\]/)?.[1];
    const source = line.match(/\[(\w+)\]/g)?.[1]?.replace(/[\[\]]/g, '');
    const message = line.replace(/\[\d{2}:\d{2}:\d{2}\]/, '').replace(/\[\w+\]/, '').trim();
    
    let colorClass = 'text-zinc-300';
    let icon = '';
    
    switch (source) {
      case 'git':
        colorClass = 'text-green-400';
        icon = '🔗';
        break;
      case 'system':
        colorClass = 'text-blue-400';
        icon = '🖥️';
        break;
      case 'code':
        colorClass = 'text-yellow-400';
        icon = '📝';
        break;
      default:
        colorClass = 'text-zinc-300';
        icon = '📋';
    }
    
    return (
      <div key={index} className={`mb-1 ${colorClass} flex items-start space-x-2`}>
        <span className="text-xs opacity-70">{timestamp}</span>
        <span className="text-xs">{icon}</span>
        <span className="text-xs opacity-70">[{source}]</span>
        <span className="flex-1 text-xs">{message}</span>
      </div>
    );
  };

  // Team member management handlers
  const addTeamMember = () => {
    setTeamMembers([...teamMembers, { username: '', email: '', name: '' }]);
  };

  const removeTeamMember = (index: number) => {
    setTeamMembers(teamMembers.filter((_, i) => i !== index));
  };

  const updateTeamMember = (index: number, field: string, value: string) => {
    const updated = [...teamMembers];
    updated[index] = { ...updated[index], [field]: value };
    setTeamMembers(updated);
  };

  // File operation handlers
  const handleFileOperation = async (operation: 'add-comments' | 'rename-variables') => {
    if (!selectedFile) return;
    
    setFileOperationLoading(operation);
    
    try {
      const response = await fetch(`http://localhost:8000/api/file/${operation}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_name: projectName,
          file_path: selectedFile.path
        })
      });

      if (!response.ok) {
        throw new Error(`Failed to ${operation.replace('-', ' ')}`);
      }

      const result = await response.json();
      
      if (result.success) {
        // Show diff modal with changes
        setDiffData({
          operation: operation.replace('-', ' '),
          fileName: selectedFile.name,
          originalContent: result.original_content,
          modifiedContent: result.modified_content,
          changesSummary: result.changes_summary,
          linesAdded: result.lines_added,
          variablesChanged: result.variables_changed
        });
        setShowDiffModal(true);
        
        // Update the file content in the current view (strip markdown wrapper)
        const updatedFile = {
          ...selectedFile,
          content: stripMarkdownWrapper(result.modified_content)
        };
        setSelectedFile(updatedFile);
        
        // No need to refresh project files since we're updating the content directly
        // This prevents losing the current file selection
      } else {
        alert(`Failed to ${operation.replace('-', ' ')}: ${result.message}`);
      }
      
    } catch (err) {
      console.error(`Error in ${operation}:`, err);
      alert(`Failed to ${operation.replace('-', ' ')}: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setFileOperationLoading(null);
    }
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopStatusStreaming();
    };
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto mb-4"></div>
          <p className="text-zinc-400">Loading project files...</p>
        </div>
      </div>
    );
  }

  if (error || !project) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-red-400 mb-4">Error Loading Project</h1>
          <p className="text-zinc-400 mb-6">{error || 'Project not found'}</p>
          <Button onClick={() => router.push('/results')} className="bg-zinc-800 hover:bg-zinc-700">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Results
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-white">
      {/* Header */}
      <div className="border-b border-zinc-800 bg-zinc-900/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="flex items-center justify-between px-6 py-4">
          <div className="flex items-center space-x-4">
            <Button 
              onClick={() => router.push('/results')} 
              variant="ghost" 
              size="sm"
              className="text-zinc-400 hover:text-white"
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back
            </Button>
            <div className="flex items-center space-x-3">
              <GitBranch className="h-5 w-5 text-purple-400" />
              <h1 className="text-xl font-bold bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent">
                {project.name}
              </h1>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            {/* Always visible Begin Untraceability button */}
            <AlertDialog open={showUntraceabilityModal} onOpenChange={setShowUntraceabilityModal}>
              <AlertDialogTrigger asChild>
                <Button 
                  className="bg-gradient-to-r from-red-600 to-orange-600 hover:from-red-700 hover:to-orange-700 text-white font-medium px-4 py-2 flex items-center space-x-2 transition-all duration-200 hover:shadow-lg"
                  disabled={untraceabilityLoading}
                >
                  <Shield className="h-4 w-4" />
                  <span>Begin Untraceability</span>
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent className="bg-zinc-900 border-zinc-700 max-w-md">
                <AlertDialogHeader>
                  <AlertDialogTitle className="text-white flex items-center">
                    <Shield className="h-5 w-5 mr-2 text-red-400" />
                    Make Project Untraceable
                  </AlertDialogTitle>
                  <AlertDialogDescription className="text-zinc-300">
                    This will rewrite git history to make your project appear as if it was created during a hackathon timeframe. You can also clone the project to your own repository.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                
                <div className="space-y-4 py-4">
                  {/* Hackathon Date and Time */}
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-zinc-300 flex items-center">
                      <Calendar className="h-4 w-4 mr-2" />
                      Hackathon Date {!generateCommitMessages && "(optional)"}
                    </label>
                    <Input
                      type="date"
                      value={hackathonDate}
                      onChange={(e) => setHackathonDate(e.target.value)}
                      className="bg-zinc-800 border-zinc-700 text-white"
                      placeholder={!generateCommitMessages ? "Only needed for git rewriting" : ""}
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-zinc-300">
                      Start Time {!generateCommitMessages && "(optional)"}
                    </label>
                    <Input
                      type="time"
                      value={hackathonStartTime}
                      onChange={(e) => setHackathonStartTime(e.target.value)}
                      className="bg-zinc-800 border-zinc-700 text-white"
                      placeholder={!generateCommitMessages ? "Only needed for git rewriting" : ""}
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-zinc-300">
                      Duration (hours) {!generateCommitMessages && "(optional)"}
                    </label>
                    <Input
                      type="number"
                      value={hackathonDuration}
                      onChange={(e) => setHackathonDuration(e.target.value)}
                      className="bg-zinc-800 border-zinc-700 text-white"
                      placeholder={!generateCommitMessages ? "Only needed for git rewriting" : "48"}
                      min="1"
                      max="168"
                    />
                  </div>

                  {/* Git Info */}
                  {/* Team Members */}
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <label className="text-sm font-medium text-zinc-300 flex items-center">
                        <User className="h-4 w-4 mr-2" />
                        Team Members {!generateCommitMessages && "(optional)"}
                      </label>
                      <Button
                        type="button"
                        onClick={addTeamMember}
                        variant="outline"
                        size="sm"
                        className="border-zinc-600 text-zinc-300 hover:bg-zinc-800"
                      >
                        Add Team Member
                      </Button>
                    </div>
                    
                    {teamMembers.length === 0 && (
                      <div className="text-sm text-zinc-500 italic">
                        No team members added. Click "Add Team Member" to add developers for commit attribution.
                      </div>
                    )}
                    
                    {teamMembers.map((member, index) => (
                      <div key={index} className="space-y-2 p-3 bg-zinc-800 rounded-lg border border-zinc-700">
                        <div className="flex justify-between items-center">
                          <span className="text-sm font-medium text-zinc-300">Team Member {index + 1}</span>
                          <Button
                            type="button"
                            onClick={() => removeTeamMember(index)}
                            variant="ghost"
                            size="sm"
                            className="text-red-400 hover:bg-red-900/20"
                          >
                            Remove
                          </Button>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
                          <Input
                            type="text"
                            value={member.username}
                            onChange={(e) => updateTeamMember(index, 'username', e.target.value)}
                            className="bg-zinc-900 border-zinc-600 text-white"
                            placeholder="username"
                          />
                          <Input
                            type="email"
                            value={member.email}
                            onChange={(e) => updateTeamMember(index, 'email', e.target.value)}
                            className="bg-zinc-900 border-zinc-600 text-white"
                            placeholder="email@example.com"
                          />
                          <Input
                            type="text"
                            value={member.name}
                            onChange={(e) => updateTeamMember(index, 'name', e.target.value)}
                            className="bg-zinc-900 border-zinc-600 text-white"
                            placeholder="Display Name (optional)"
                          />
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Target Repository URL */}
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-zinc-300 flex items-center">
                      <GitBranch className="h-4 w-4 mr-2" />
                      Target Repository URL (Optional)
                    </label>
                    <Input
                      type="url"
                      value={targetRepositoryUrl}
                      onChange={(e) => setTargetRepositoryUrl(e.target.value)}
                      className="bg-zinc-800 border-zinc-700 text-white"
                      placeholder="https://github.com/yourusername/your-empty-repo.git"
                    />
                    <p className="text-xs text-zinc-500">
                      Leave empty to modify the current repository, or provide an empty repository URL to clone the project there
                    </p>
                  </div>

                  {/* Options */}
                  <div className="space-y-3">
                    <div className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        id="generateCommitMessages"
                        checked={generateCommitMessages}
                        onChange={(e) => setGenerateCommitMessages(e.target.checked)}
                        className="rounded border-zinc-600 bg-zinc-800"
                      />
                      <label htmlFor="generateCommitMessages" className="text-sm text-zinc-300 flex items-center">
                        <GitBranch className="h-4 w-4 mr-2" />
                        Generate AI commit messages and rewrite git history
                      </label>
                    </div>
                    
                    <div className="text-sm text-zinc-400 bg-zinc-800 p-3 rounded-lg">
                      <p className="font-medium mb-1">📝 Code Enhancement:</p>
                      <p>Adding comments and renaming variables is now done per-file. Open any file and use the "Add Comments" or "Rename Variables" buttons.</p>
                    </div>

                  </div>
                </div>

                <div className="flex space-x-2">
                  <Button
                    onClick={() => setShowUntraceabilityModal(false)}
                    variant="outline"
                    className="flex-1 border-zinc-600 text-zinc-300 hover:bg-zinc-800"
                    disabled={untraceabilityLoading}
                  >
                    Cancel
                  </Button>
                  <AlertDialogAction
                    onClick={handleUntraceability}
                    className="flex-1 bg-gradient-to-r from-red-600 to-orange-600 hover:from-red-700 hover:to-orange-700 text-white"
                    disabled={untraceabilityLoading}
                  >
                    {untraceabilityLoading ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Processing...
                      </>
                    ) : (
                      <>
                        <Shield className="h-4 w-4 mr-2" />
                        Make Untraceable
                      </>
                    )}
                  </AlertDialogAction>
                </div>
              </AlertDialogContent>
            </AlertDialog>

            {/* Progress Modal */}
            <AlertDialog open={showProgressModal} onOpenChange={() => {}}>
              <AlertDialogContent className="bg-zinc-900 border-zinc-700 max-w-6xl max-h-[90vh] overflow-hidden">
                <AlertDialogHeader>
                  <AlertDialogTitle className="text-white flex items-center">
                    <Terminal className="h-5 w-5 mr-2" />
                    Making Project Untraceable
                    {untraceabilityLoading && (
                      <Loader2 className="h-4 w-4 ml-2 animate-spin" />
                    )}
                  </AlertDialogTitle>
                  <AlertDialogDescription className="text-zinc-300">
                    {currentOperation || 'Processing...'}
                  </AlertDialogDescription>
                </AlertDialogHeader>
                
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 py-4 max-h-[70vh] overflow-y-auto">
                  {/* Left Column - Tasks and Git Info */}
                  <div className="space-y-4">
                    {/* Tasks Progress */}
                    {tasks.length > 0 && (
                      <div className="space-y-3">
                        <h4 className="text-sm font-medium text-zinc-300 flex items-center">
                          <Settings className="h-4 w-4 mr-2" />
                          Tasks Progress:
                        </h4>
                        {tasks.map((task, index) => (
                          <div key={task.id || index} className="space-y-2">
                            <div className="flex items-center justify-between">
                              <span className="text-sm text-zinc-300 flex items-center">
                                {task.status === 'completed' && <span className="text-green-400 mr-2">✅</span>}
                                {task.status === 'running' && <Loader2 className="h-3 w-3 mr-2 animate-spin text-blue-400" />}
                                {task.status === 'pending' && <span className="text-yellow-400 mr-2">⏳</span>}
                                {task.status === 'failed' && <span className="text-red-400 mr-2">❌</span>}
                                {task.name}
                              </span>
                              <span className="text-xs text-zinc-500">
                                {task.progress ? `${Math.round(task.progress)}%` : ''}
                              </span>
                            </div>
                            {task.progress !== undefined && (
                              <div className="w-full bg-zinc-800 rounded-full h-2">
                                <div
                                  className={`h-2 rounded-full transition-all duration-300 ${
                                    task.status === 'completed' ? 'bg-green-500' :
                                    task.status === 'failed' ? 'bg-red-500' :
                                    'bg-blue-500'
                                  }`}
                                  style={{ width: `${task.progress || 0}%` }}
                                ></div>
                              </div>
                            )}
                            {task.message && (
                              <p className="text-xs text-zinc-400">{task.message}</p>
                            )}
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Git Commits Section */}
                    {gitCommits.length > 0 && (
                      <div className="space-y-3">
                        <h4 className="text-sm font-medium text-zinc-300 flex items-center">
                          <GitBranch className="h-4 w-4 mr-2" />
                          Git Commits ({gitCommits.length}):
                        </h4>
                        <div className="space-y-2 max-h-64 overflow-y-auto">
                          {gitCommits.slice(-10).map((commit, index) => (
                            <div key={index} className="bg-zinc-800 rounded-lg p-3 space-y-2">
                              <div className="flex items-center justify-between">
                                <code className="text-xs text-green-400 font-mono">
                                  {commit.hash.substring(0, 8)}
                                </code>
                                <span className="text-xs text-zinc-500">
                                  {new Date(commit.date).toLocaleDateString()}
                                </span>
                              </div>
                              <p className="text-sm text-zinc-300">{commit.message}</p>
                              <div className="flex items-center text-xs text-zinc-400">
                                <User className="h-3 w-3 mr-1" />
                                {commit.author}
                                <Mail className="h-3 w-3 ml-3 mr-1" />
                                {commit.email}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* System Logs */}
                    {systemLogs.length > 0 && (
                      <div className="space-y-2">
                        <h4 className="text-sm font-medium text-zinc-300 flex items-center">
                          <Settings className="h-4 w-4 mr-2" />
                          System Status:
                        </h4>
                        <div className="bg-zinc-800 rounded-lg p-3 max-h-32 overflow-y-auto">
                          {systemLogs.slice(-5).map((log, index) => (
                            <div key={index} className="text-xs text-blue-400 mb-1">
                              {log.replace(/\[\d{2}:\d{2}:\d{2}\]/, '').replace(/\[system\]/, '').trim()}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Code Modification Logs */}
                    {codeLogs.length > 0 && (
                      <div className="space-y-2">
                        <h4 className="text-sm font-medium text-zinc-300 flex items-center">
                          <Code2 className="h-4 w-4 mr-2" />
                          Code Modifications:
                        </h4>
                        <div className="bg-zinc-800 rounded-lg p-3 max-h-32 overflow-y-auto">
                          {codeLogs.slice(-5).map((log, index) => (
                            <div key={index} className="text-xs text-yellow-400 mb-1">
                              {log.replace(/\[\d{2}:\d{2}:\d{2}\]/, '').replace(/\[code\]/, '').trim()}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Right Column - Terminal Output */}
                  <div className="space-y-2">
                    <h4 className="text-sm font-medium text-zinc-300 flex items-center">
                      <Terminal className="h-4 w-4 mr-2" />
                      Live Terminal Output:
                    </h4>
                    <div 
                      ref={terminalRef}
                      className="bg-black border border-zinc-700 rounded-lg p-4 font-mono text-xs max-h-[50vh] overflow-y-auto"
                    >
                      {terminalOutput.length === 0 ? (
                        <div className="text-zinc-500">Waiting for output...</div>
                      ) : (
                        <div className="space-y-1">
                          {terminalOutput.map((line, index) => formatTerminalLine(line, index))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                <div className="flex justify-end border-t border-zinc-700 pt-4">
                  <Button
                    onClick={() => {
                      stopStatusStreaming();
                      setShowProgressModal(false);
                      setUntraceabilityLoading(false);
                    }}
                    variant="outline"
                    className="border-zinc-600 text-zinc-300 hover:bg-zinc-800"
                    disabled={untraceabilityLoading}
                  >
                    {untraceabilityLoading ? 'Processing...' : 'Close'}
                  </Button>
                </div>
              </AlertDialogContent>
            </AlertDialog>

            {/* Diff Modal */}
            <AlertDialog open={showDiffModal} onOpenChange={setShowDiffModal}>
              <AlertDialogContent className="bg-zinc-900 border-zinc-700 max-w-6xl max-h-[90vh] overflow-hidden">
                <AlertDialogHeader>
                  <AlertDialogTitle className="text-white flex items-center">
                    <Code2 className="h-5 w-5 mr-2" />
                    File Modified: {diffData?.fileName}
                  </AlertDialogTitle>
                  <AlertDialogDescription className="text-zinc-300">
                    {diffData?.changesSummary}
                  </AlertDialogDescription>
                </AlertDialogHeader>
                
                <div className="py-4 max-h-[70vh] overflow-y-auto">
                  {diffData && (
                    <div className="space-y-4">
                      <div className="bg-zinc-800 p-4 rounded-lg">
                        <h4 className="text-sm font-medium text-zinc-300 mb-2">Changes Summary:</h4>
                        <div className="flex space-x-4 text-sm">
                          {diffData.linesAdded > 0 && (
                            <span className="text-green-400">+{diffData.linesAdded} lines added</span>
                          )}
                          {diffData.variablesChanged > 0 && (
                            <span className="text-blue-400">{diffData.variablesChanged} variables renamed</span>
                          )}
                        </div>
                      </div>
                      
                      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                        <div>
                          <h4 className="text-sm font-medium text-zinc-300 mb-2">Before:</h4>
                          <div className="bg-zinc-800 rounded-lg border border-zinc-700 overflow-hidden">
                            <SyntaxHighlighter
                              language={getSyntaxLanguage(diffData.fileName?.split('.').pop() || '', diffData.originalContent)}
                              style={vscDarkPlus}
                              customStyle={{
                                margin: 0,
                                padding: '1rem',
                                background: 'transparent',
                                fontSize: '0.75rem',
                                lineHeight: '1.4',
                                maxHeight: '24rem',
                                overflow: 'auto'
                              }}
                              showLineNumbers={true}
                              lineNumberStyle={{
                                color: '#6b7280',
                                borderRight: '1px solid #374151',
                                paddingRight: '0.5rem',
                                marginRight: '0.5rem',
                                minWidth: '2rem'
                              }}
                            >
                              {stripMarkdownWrapper(diffData.originalContent)}
                            </SyntaxHighlighter>
                          </div>
                        </div>
                        <div>
                          <h4 className="text-sm font-medium text-zinc-300 mb-2">After:</h4>
                          <div className="bg-zinc-800 rounded-lg border border-zinc-700 overflow-hidden">
                            <SyntaxHighlighter
                              language={getSyntaxLanguage(diffData.fileName?.split('.').pop() || '', diffData.modifiedContent)}
                              style={vscDarkPlus}
                              customStyle={{
                                margin: 0,
                                padding: '1rem',
                                background: 'transparent',
                                fontSize: '0.75rem',
                                lineHeight: '1.4',
                                maxHeight: '24rem',
                                overflow: 'auto'
                              }}
                              showLineNumbers={true}
                              lineNumberStyle={{
                                color: '#6b7280',
                                borderRight: '1px solid #374151',
                                paddingRight: '0.5rem',
                                marginRight: '0.5rem',
                                minWidth: '2rem'
                              }}
                            >
                              {stripMarkdownWrapper(diffData.modifiedContent)}
                            </SyntaxHighlighter>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                <div className="flex justify-end border-t border-zinc-700 pt-4">
                  <AlertDialogAction
                    onClick={() => setShowDiffModal(false)}
                    className="bg-zinc-700 hover:bg-zinc-600 text-white"
                  >
                    Close
                  </AlertDialogAction>
                </div>
              </AlertDialogContent>
            </AlertDialog>
            
            <Badge className="bg-zinc-800 text-zinc-300">
              {project.language}
            </Badge>
            <Badge className="bg-blue-600/20 text-blue-300 border-blue-700">
              ⭐ {project.stars}
            </Badge>
            <Badge className="bg-purple-600/20 text-purple-300 border-purple-700">
              🍴 {project.forks}
            </Badge>
          </div>
        </div>
      </div>

      <div className="flex h-[calc(100vh-73px)]">
        {/* File Explorer Sidebar */}
        <div className="w-80 bg-zinc-900/30 border-r border-zinc-800 flex flex-col">
          <div className="p-4 border-b border-zinc-800">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold text-sm text-zinc-300 flex items-center">
                <Folder className="h-4 w-4 mr-2" />
                Explorer
              </h2>
              <div className="flex space-x-1">
                <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
                  <Search className="h-3 w-3" />
                </Button>
                <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
                  <Terminal className="h-3 w-3" />
                </Button>
              </div>
            </div>
          </div>
          
          <div className="flex-1 overflow-y-auto p-2">
            <div className="mb-2">
              <div className="text-xs text-zinc-500 uppercase tracking-wide px-2 mb-2">
                {project.name}
              </div>
              {renderFileTree(project.files)}
            </div>
          </div>
        </div>

        {/* Main Content Area */}
        <div className="flex-1 flex flex-col">
          {selectedFile ? (
            <>
              {/* File Tab */}
              <div className="border-b border-zinc-800 bg-zinc-900/20">
                <div className="flex items-center px-4 py-2">
                  <div className="flex items-center space-x-2 bg-zinc-800/50 rounded px-3 py-1.5">
                    {getFileIcon(selectedFile)}
                    <span className="text-sm font-medium">{selectedFile.name}</span>
                  </div>
                  <div className="ml-auto flex space-x-2">
                    {/* File enhancement buttons */}
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      className="h-7 px-2 bg-blue-600/20 text-blue-300 hover:bg-blue-600/30 border border-blue-700"
                      onClick={() => handleFileOperation('add-comments')}
                      disabled={fileOperationLoading !== null}
                    >
                      <MessageCircle className="h-3 w-3 mr-1" />
                      {fileOperationLoading === 'add-comments' ? 'Processing...' : 'Add Comments'}
                    </Button>
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      className="h-7 px-2 bg-purple-600/20 text-purple-300 hover:bg-purple-600/30 border border-purple-700"
                      onClick={() => handleFileOperation('rename-variables')}
                      disabled={fileOperationLoading !== null}
                    >
                      <Variable className="h-3 w-3 mr-1" />
                      {fileOperationLoading === 'rename-variables' ? 'Processing...' : 'Rename Variables'}
                    </Button>
                    
                    {/* Standard file operations */}
                    <Button variant="ghost" size="sm" className="h-7 px-2">
                      <Copy className="h-3 w-3 mr-1" />
                      Copy
                    </Button>
                    <Button variant="ghost" size="sm" className="h-7 px-2">
                      <Download className="h-3 w-3 mr-1" />
                      Download
                    </Button>
                  </div>
                </div>
              </div>

              {/* File Content */}
              <div className="flex-1 overflow-hidden">
                {selectedFile.content ? (
                  <div className="h-full overflow-auto p-6">
                    <SyntaxHighlighter
                      language={getSyntaxLanguage(selectedFile.extension || '', selectedFile.content)}
                      style={vscDarkPlus}
                      customStyle={{
                        margin: 0,
                        padding: '1rem',
                        background: 'transparent',
                        fontSize: '0.875rem',
                        lineHeight: '1.5'
                      }}
                      showLineNumbers={true}
                      lineNumberStyle={{
                        color: '#6b7280',
                        borderRight: '1px solid #374151',
                        paddingRight: '1rem',
                        marginRight: '1rem',
                        minWidth: '3rem'
                      }}
                      wrapLines={true}
                      wrapLongLines={true}
                    >
                      {stripMarkdownWrapper(selectedFile.content)}
                    </SyntaxHighlighter>
                  </div>
                ) : (
                  <div className="h-full flex items-center justify-center text-zinc-500">
                    <div className="text-center">
                      <Eye className="h-12 w-12 mx-auto mb-4 opacity-50" />
                      <p>Select a file to view its contents</p>
                    </div>
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center">
                <Code2 className="h-16 w-16 mx-auto mb-4 text-zinc-600" />
                <h3 className="text-xl font-semibold text-zinc-300 mb-2">
                  Welcome to {project.name}
                </h3>
                <p className="text-zinc-500 mb-6 max-w-md">
                  {project.description}
                </p>
                <div className="flex flex-wrap gap-2 justify-center">
                  {project.technologies.map((tech) => (
                    <Badge key={tech} className="bg-zinc-800 text-zinc-300">
                      {tech}
                    </Badge>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
} 