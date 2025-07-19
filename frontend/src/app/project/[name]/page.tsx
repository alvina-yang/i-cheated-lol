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
  const [gitUsername, setGitUsername] = useState('');
  const [gitEmail, setGitEmail] = useState('');
  const [targetRepositoryUrl, setTargetRepositoryUrl] = useState('');
  const [addComments, setAddComments] = useState(true);
  
  // Progress tracking state
  const [showProgressModal, setShowProgressModal] = useState(false);
  const [currentOperation, setCurrentOperation] = useState<string>('');
  const [tasks, setTasks] = useState<any[]>([]);
  const [terminalOutput, setTerminalOutput] = useState<string[]>([]);
  const [gitCommits, setGitCommits] = useState<any[]>([]);
  const [systemLogs, setSystemLogs] = useState<string[]>([]);
  const [codeLogs, setCodeLogs] = useState<string[]>([]);
  const [statusEventSource, setStatusEventSource] = useState<EventSource | null>(null);
  const terminalRef = useRef<HTMLDivElement>(null);

  const parseGitCommitInfo = (line: string) => {
    // Parse git commit information from terminal output
    // Handle format: "  b241fc62cdf40eec03ebdec96635b5d64f6bcf19 Additional improvements and fixes #9 alvina-yang <alvinay73@gmail.com> 2025-07-11 23:12:42 -0400"
    const cleanLine = line.replace(/\[\d{2}:\d{2}:\d{2}\]/, '').replace(/\[git\]/, '').trim();
    
    // Pattern for commit info with hash, message, author, email, and date
    const commitPattern = /^\s*([a-f0-9]+)\s+(.+?)\s+(\S+)\s+<([^>]+)>\s+(.+)$/;
    const match = cleanLine.match(commitPattern);
    
    if (match) {
      const [, hash, message, author, email, date] = match;
      return {
        hash,
        message: message.trim(),
        author: author.trim(),
        email: email.trim(),
        date: date.trim()
      };
    }
    
    return null;
  };

  const categorizeTerminalOutput = (line: string) => {
    if (line.includes('[git]')) {
      const gitInfo = parseGitCommitInfo(line);
      if (gitInfo) {
        setGitCommits(prev => {
          const exists = prev.find(commit => commit.hash === gitInfo.hash);
          if (!exists) {
            return [...prev, gitInfo];
          }
          return prev;
        });
      }
      return 'git';
    } else if (line.includes('[code]')) {
      setCodeLogs(prev => [...prev, line].slice(-50));
      return 'code';
    } else if (line.includes('[system]')) {
      setSystemLogs(prev => [...prev, line].slice(-50));
      return 'system';
    }
    return 'general';
  };

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

  const formatFileContent = (content: string, extension: string) => {
    const language = getLanguageFromExtension(extension);
    
    // Basic syntax highlighting for common patterns
    let highlighted = content;
    
    if (language === 'javascript' || language === 'typescript') {
      highlighted = highlighted
        .replace(/\b(const|let|var|function|class|import|export|return|if|else|for|while|try|catch)\b/g, '<span class="text-blue-400 font-semibold">$1</span>')
        .replace(/\b(true|false|null|undefined)\b/g, '<span class="text-orange-400">$1</span>')
        .replace(/"([^"]*)"/g, '<span class="text-green-400">"$1"</span>')
        .replace(/'([^']*)'/g, '<span class="text-green-400">\'$1\'</span>')
        .replace(/\/\/.*$/gm, '<span class="text-zinc-500 italic">$&</span>')
        .replace(/\/\*[\s\S]*?\*\//g, '<span class="text-zinc-500 italic">$&</span>');
    } else if (language === 'python') {
      highlighted = highlighted
        .replace(/\b(def|class|import|from|return|if|else|elif|for|while|try|except|with|as)\b/g, '<span class="text-blue-400 font-semibold">$1</span>')
        .replace(/\b(True|False|None)\b/g, '<span class="text-orange-400">$1</span>')
        .replace(/"([^"]*)"/g, '<span class="text-green-400">"$1"</span>')
        .replace(/'([^']*)'/g, '<span class="text-green-400">\'$1\'</span>')
        .replace(/#.*$/gm, '<span class="text-zinc-500 italic">$&</span>');
    } else if (language === 'json') {
      highlighted = highlighted
        .replace(/"([^"]*)":/g, '<span class="text-blue-400">"$1"</span>:')
        .replace(/:\s*"([^"]*)"/g, ': <span class="text-green-400">"$1"</span>')
        .replace(/:\s*(true|false|null)\b/g, ': <span class="text-orange-400">$1</span>');
    }
    
    return highlighted;
  };

  const startStatusStreaming = () => {
    // Clear previous data
    setTerminalOutput([]);
    setGitCommits([]);
    setSystemLogs([]);
    setCodeLogs([]);
    
    // Close existing connection if any
    if (statusEventSource) {
      statusEventSource.close();
    }
    
    // Stream general status
    const eventSource = new EventSource(`http://localhost:8000/api/status/stream`);
    
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setCurrentOperation(data.current_operation || '');
        setTasks(data.tasks || []);
        
        // Add new terminal output
        if (data.recent_output && data.recent_output.length > 0) {
          setTerminalOutput(prev => {
            const newOutput = [...prev, ...data.recent_output];
            // Categorize each line
            data.recent_output.forEach(categorizeTerminalOutput);
            // Keep only last 100 lines to prevent memory issues
            return newOutput.slice(-100);
          });
        }
      } catch (error) {
        console.error('Error parsing status data:', error);
      }
    };
    
    eventSource.onerror = (error) => {
      console.error('Status stream error:', error);
    };
    
    setStatusEventSource(eventSource);
    
    // Also stream project-specific terminal output
    const terminalSource = new EventSource(`http://localhost:8000/api/project/${encodeURIComponent(projectName)}/stream-terminal`);
    
    terminalSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.new_lines && data.new_lines.length > 0) {
          setTerminalOutput(prev => {
            const newOutput = [...prev, ...data.new_lines];
            // Categorize each line
            data.new_lines.forEach(categorizeTerminalOutput);
            return newOutput.slice(-100);
          });
        }
      } catch (error) {
        console.error('Error parsing terminal data:', error);
      }
    };
    
    terminalSource.onerror = (error) => {
      console.error('Terminal stream error:', error);
    };
    
    // Store both sources for cleanup
    setStatusEventSource({
      status: eventSource,
      terminal: terminalSource,
      close: () => {
        eventSource.close();
        terminalSource.close();
      }
    } as any);
  };

  const stopStatusStreaming = () => {
    if (statusEventSource) {
      if (typeof statusEventSource.close === 'function') {
        statusEventSource.close();
      } else {
        // Handle old single EventSource format
        (statusEventSource as EventSource).close();
      }
      setStatusEventSource(null);
    }
  };

  const handleUntraceability = async () => {
    if (!hackathonDate || !hackathonStartTime || !hackathonDuration || !gitUsername || !gitEmail) {
      alert('Please fill in all required fields');
      return;
    }

    setUntraceabilityLoading(true);
    setShowUntraceabilityModal(false);
    setShowProgressModal(true);
    setTerminalOutput([]);
    setCurrentOperation('');
    setTasks([]);
    
    // Start status streaming
    startStatusStreaming();
    
    try {
      const response = await fetch(`http://localhost:8000/api/project/${encodeURIComponent(projectName)}/make-untraceable`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          hackathon_date: hackathonDate,
          hackathon_start_time: hackathonStartTime,
          hackathon_duration: parseInt(hackathonDuration),
          git_username: gitUsername,
          git_email: gitEmail,
          target_repository_url: targetRepositoryUrl,
          add_comments: addComments
        })
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to make project untraceable: ${response.status} - ${errorText}`);
      }

      const result = await response.json();
      
      // Keep monitoring for a bit longer to catch final updates
      setTimeout(() => {
        stopStatusStreaming();
        setUntraceabilityLoading(false);
      alert('Project successfully made untraceable! 🕵️‍♂️');
      
      // Refresh the project to show updated files
      fetchProjectFiles();
      }, 5000);
      
    } catch (err) {
      console.error('Error making project untraceable:', err);
      alert(`Failed to make project untraceable: ${err instanceof Error ? err.message : 'Unknown error'}`);
      stopStatusStreaming();
      setUntraceabilityLoading(false);
      setShowProgressModal(false);
    }
  };

  // Auto-scroll terminal output
  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [terminalOutput]);

  const formatTerminalLine = (line: string, index: number) => {
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
                    This will rewrite git history, modify commit dates, change author info, and optionally add comments and rename variables to make the project appear as if it was created during a hackathon.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                
                <div className="space-y-4 py-4">
                  {/* Hackathon Date and Time */}
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-zinc-300 flex items-center">
                      <Calendar className="h-4 w-4 mr-2" />
                      Hackathon Date
                    </label>
                    <Input
                      type="date"
                      value={hackathonDate}
                      onChange={(e) => setHackathonDate(e.target.value)}
                      className="bg-zinc-800 border-zinc-700 text-white"
                      required
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-zinc-300">
                      Start Time
                    </label>
                    <Input
                      type="time"
                      value={hackathonStartTime}
                      onChange={(e) => setHackathonStartTime(e.target.value)}
                      className="bg-zinc-800 border-zinc-700 text-white"
                      required
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-zinc-300">
                      Duration (hours)
                    </label>
                    <Input
                      type="number"
                      value={hackathonDuration}
                      onChange={(e) => setHackathonDuration(e.target.value)}
                      className="bg-zinc-800 border-zinc-700 text-white"
                      placeholder="48"
                      min="1"
                      max="168"
                      required
                    />
                  </div>

                  {/* Git Info */}
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-zinc-300 flex items-center">
                      <User className="h-4 w-4 mr-2" />
                      Git Username
                    </label>
                    <Input
                      type="text"
                      value={gitUsername}
                      onChange={(e) => setGitUsername(e.target.value)}
                      className="bg-zinc-800 border-zinc-700 text-white"
                      placeholder="john_doe"
                      required
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-zinc-300 flex items-center">
                      <Mail className="h-4 w-4 mr-2" />
                      Git Email
                    </label>
                    <Input
                      type="email"
                      value={gitEmail}
                      onChange={(e) => setGitEmail(e.target.value)}
                      className="bg-zinc-800 border-zinc-700 text-white"
                      placeholder="john@example.com"
                      required
                    />
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
                        id="addComments"
                        checked={addComments}
                        onChange={(e) => setAddComments(e.target.checked)}
                        className="rounded border-zinc-600 bg-zinc-800"
                      />
                      <label htmlFor="addComments" className="text-sm text-zinc-300 flex items-center">
                        <MessageCircle className="h-4 w-4 mr-2" />
                        Add AI-generated comments to code
                      </label>
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
                    <pre className="text-sm leading-relaxed">
                      <code 
                        className="block whitespace-pre-wrap font-mono"
                        dangerouslySetInnerHTML={{
                          __html: formatFileContent(
                            selectedFile.content,
                            selectedFile.extension || ''
                          )
                        }}
                      />
                    </pre>
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