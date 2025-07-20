"use client";

import { useState, useEffect } from "react";
import { useParams, useSearchParams } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { AlertDialog, AlertDialogAction, AlertDialogContent, AlertDialogDescription, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from "@/components/ui/alert-dialog";
import { 
  ArrowLeft, 
  Folder,
  Code2, 
  Image as ImageIcon,
  Terminal,
  Search,
  ChevronRight,
  Copy,
  Download,
  Eye,
  GitBranch,
  Shield,
  Calendar,
  Clock,
  User,
  MessageCircle,
  Variable,
  Loader2,
  Presentation
} from "lucide-react";
import { useRouter } from "next/navigation";
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import GitHistoryViewer from "@/components/GitHistoryViewer";
import EditableCodeEditor from "@/components/EditableCodeEditor";
import { DatePicker } from "@/components/ui/date-picker";
import { TimePicker } from "@/components/ui/time-picker";
import { FileNode, ProjectData, TeamMember, DiffData } from "./types";
import { 
  getFileIcon, 
  stripMarkdownWrapper, 
  getSyntaxLanguage,
  createAddTeamMember, 
  createRemoveTeamMember, 
  createUpdateTeamMember,
  toggleFolder
} from "./utils";
import { API_ENDPOINTS } from "./constants/api";

export default function ProjectPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const router = useRouter();
  const projectName = params.name as string;
  const githubUrl = searchParams.get('github_url');
  
  const [project, setProject] = useState<ProjectData | null>(null);
  const [selectedFile, setSelectedFile] = useState<FileNode | null>(null);
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Untraceability modal state
  const [showUntraceabilityModal, setShowUntraceabilityModal] = useState(false);
  const [untraceabilityLoading, setUntraceabilityLoading] = useState(false);
  const [hackathonDate, setHackathonDate] = useState<Date | undefined>(undefined);
  const [hackathonStartTime, setHackathonStartTime] = useState('');
  const [hackathonDuration, setHackathonDuration] = useState('48');
  const [teamMembers, setTeamMembers] = useState<TeamMember[]>([]);
  const [targetRepositoryUrl, setTargetRepositoryUrl] = useState('');

  
  // File operation state
  const [fileOperationLoading, setFileOperationLoading] = useState<string | null>(null);
  const [showDiffModal, setShowDiffModal] = useState(false);
  const [diffData, setDiffData] = useState<DiffData | null>(null);
  
  // Progress tracking state (simplified)
  const [showProgressModal, setShowProgressModal] = useState(false);
  
  // Git history viewer state
  const [showGitHistory, setShowGitHistory] = useState(false);
  
  // Editor reference for undo functionality
  const [editorRef, setEditorRef] = useState<any>(null);
  
  // PANIC button state
  const [panicLoading, setPanicLoading] = useState(false);
  const [showPanicResultModal, setShowPanicResultModal] = useState(false);
  const [panicResult, setPanicResult] = useState<any>(null);
  
  // Removed all streaming functions

  // Team member management handlers
  const handleAddTeamMember = () => {
    setTeamMembers(createAddTeamMember(teamMembers));
  };

  const handleRemoveTeamMember = (index: number) => {
    setTeamMembers(createRemoveTeamMember(teamMembers, index));
  };

  const handleUpdateTeamMember = (index: number, field: keyof TeamMember, value: string) => {
    setTeamMembers(createUpdateTeamMember(teamMembers, index, field, value));
  };

  // PANIC button handler
  const handlePanicMode = async () => {
    try {
      setPanicLoading(true);
      
      const panicRequest = {
        project_name: projectName,
        start_command: 'python -m http.server 3000'
      };
      
      // Call panic endpoint
      const panicResponse = await fetch('http://localhost:8000/api/panic', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(panicRequest)
      });
      
      const panicResult = await panicResponse.json();

      if (!panicResponse.ok) {
        throw new Error(panicResult.detail || 'Panic mode failed');
      }
      
      if (panicResult.success && panicResult.index_file_path) {
        // Refresh the project files immediately
        await fetchProjectFiles();
        
        // Try to open the local index.html file in a new tab
        const fileUrl = `file://${panicResult.index_file_path}`;
        const newWindow = window.open(fileUrl, '_blank', 'noopener,noreferrer');
        
        // Store result for modal
        setPanicResult({
          ...panicResult,
          fileUrl,
          openedSuccessfully: !!newWindow
        });
        setShowPanicResultModal(true);
        
        // Try to copy URL to clipboard as backup
        if (navigator.clipboard) {
          navigator.clipboard.writeText(fileUrl).catch(() => {});
        }
      } else {
        setPanicResult(panicResult);
        setShowPanicResultModal(true);
      }
      
    } catch (error: any) {
      console.error('Panic mode failed:', error);
      alert(`Panic mode failed: ${error.message}`);
    } finally {
      setPanicLoading(false);
    }
  };

  // File operation handlers
  const handleFileOperation = async (operation: 'add-comments' | 'rename-variables') => {
    if (!selectedFile) return;
    
    setFileOperationLoading(operation);
    
    try {
      const operationEndpoint = operation === 'add-comments' 
        ? API_ENDPOINTS.FILE_OPERATIONS.ADD_COMMENTS 
        : API_ENDPOINTS.FILE_OPERATIONS.RENAME_VARIABLES;
      
      const response = await fetch(operationEndpoint, {
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
        const newContent = stripMarkdownWrapper(result.modified_content);
        const updatedFile = {
          ...selectedFile,
          content: newContent
        };
        setSelectedFile(updatedFile);
        
        // Update the editor with the new content and add to history
        if (editorRef) {
          const operationName = operation === 'add-comments' ? 'add_comments' : 'rename_variables';
          const description = operation === 'add-comments' 
            ? `Added ${result.lines_added} comment lines` 
            : `Renamed ${result.variables_changed} variables`;
          editorRef.updateContent(newContent, operationName, description);
        }
        
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

  // Handle file save from the editor
  const handleFileSave = async (content: string) => {
    if (!selectedFile) return;
    
    const response = await fetch(`http://localhost:8000/api/file/save/${projectName}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        file_path: selectedFile.path,
        content: content
      })
    });

    if (!response.ok) {
      throw new Error('Failed to save file');
    }

    // Update the selected file with the new content
    setSelectedFile(prev => prev ? { ...prev, content } : null);
  };

  useEffect(() => {
    if (projectName) {
      fetchProjectFiles();
    }
  }, [projectName]);

  const fetchProjectFiles = async () => {
    try {
      setLoading(true);
      
      // If we have a GitHub URL, clone the repository first
      if (githubUrl) {
        setError('Cloning repository...');
        const cloneResponse = await fetch(`http://localhost:8000/api/clone`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            project_name: projectName,
            project_url: githubUrl,
            clone_url: githubUrl.endsWith('.git') ? githubUrl : `${githubUrl}.git`
          })
        });
        
        if (!cloneResponse.ok) {
          throw new Error('Failed to clone repository');
        }
        
        setError(null);
      }
      
      const response = await fetch(API_ENDPOINTS.PROJECT_FILES(projectName));
      
      if (!response.ok) {
        throw new Error('Failed to fetch project files');
      }
      
      const data = await response.json();
      setProject(data);
    } catch (err) {
      console.error('Error fetching project files:', err);
      setError(err instanceof Error ? err.message : 'Failed to load project');
    } finally {
      setLoading(false);
    }
  };






  const handleUntraceability = async () => {
    // Validate required fields
    if (!hackathonDate || !hackathonStartTime || !hackathonDuration) {
      alert('Please fill in hackathon date, time, and duration');
      return;
    }

    setUntraceabilityLoading(true);
    setShowUntraceabilityModal(false);
    setShowProgressModal(true);
    
    try {
      const response = await fetch(API_ENDPOINTS.PROJECT_UNTRACEABLE(projectName), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          hackathon_date: hackathonDate?.toISOString().split('T')[0],
          hackathon_start_time: hackathonStartTime,
          hackathon_duration: parseInt(hackathonDuration),
          team_members: teamMembers,
          target_repository_url: targetRepositoryUrl,
          generate_commit_messages: true
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
        alert('Project successfully made untraceable!');
        
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

  // Other utility functions remain the same...
  const selectFile = async (file: FileNode) => {
    if (file.type === 'file') {
      try {
        const response = await fetch(API_ENDPOINTS.FILE_CONTENT(projectName, file.path));
        if (response.ok) {
          const content = await response.text();
          setSelectedFile({ ...file, content });
        }
      } catch (err) {
        console.error('Failed to load file content:', err);
      }
    }
  };

  const handleToggleFolder = (folderPath: string) => {
    setExpandedFolders(toggleFolder(expandedFolders, folderPath));
  };

  const renderFileTree = (files: FileNode[], level = 0) => {
    return files.map((file) => (
      <div key={file.path}>
        <div
          className={`flex items-center space-x-2 px-2 py-1 hover:bg-zinc-800 rounded cursor-pointer ${
            selectedFile?.path === file.path ? 'bg-zinc-800' : ''
          }`}
          style={{ paddingLeft: `${level * 16 + 8}px` }}
          onClick={() => {
            if (file.type === 'directory') {
              handleToggleFolder(file.path);
            } else {
              selectFile(file);
            }
          }}
        >
          {file.type === 'directory' && (
            <ChevronRight 
              className={`h-3 w-3 transition-transform ${
                expandedFolders.has(file.path) ? 'rotate-90' : ''
              }`} 
            />
          )}
          {getFileIcon(file, expandedFolders)}
          <span className="text-sm text-zinc-300 truncate">{file.name}</span>
        </div>
        
        {file.type === 'directory' && expandedFolders.has(file.path) && file.children && (
          <div className="ml-4">
              {renderFileTree(file.children, level + 1)}
          </div>
        )}
      </div>
    ));
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-black text-white flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p>Loading project...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-black text-white flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-400 mb-4">{error}</p>
          <Button onClick={() => router.push('/')}>Go Back</Button>
        </div>
      </div>
    );
  }

  if (!project) {
    return (
      <div className="min-h-screen bg-black text-white flex items-center justify-center">
        <p>Project not found</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-white">
      {/* Header */}
      <div className="border-b border-zinc-800 bg-zinc-900/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="flex items-center justify-between p-4">
          <div className="flex items-center space-x-4">
            <Button 
              variant="ghost" 
              onClick={() => router.push('/')}
              className="text-zinc-400 hover:text-white"
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back
            </Button>
            
            <div>
              <h1 className="text-xl font-bold">{project.name}</h1>
              <p className="text-sm text-zinc-400">{project.description}</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-3">
            
            {/* Presentation Script Button */}
            <Button 
              variant="outline"
              onClick={() => router.push(`/presentation/${encodeURIComponent(projectName)}`)}
              className="border-orange-600 text-orange-400 hover:bg-orange-600 hover:text-white"
            >
              <Presentation className="h-4 w-4 mr-2" />
              View Pitch Script
            </Button>
            
            {/* Git History Button */}
            <Button 
              variant="outline"
              onClick={() => setShowGitHistory(true)}
              className="border-green-600 text-green-400 hover:bg-green-600 hover:text-white"
            >
              <GitBranch className="h-4 w-4 mr-2" />
              Git History
            </Button>
            
            {/* Untraceable Button */}
            <AlertDialog open={showUntraceabilityModal} onOpenChange={setShowUntraceabilityModal}>
              <AlertDialogTrigger asChild>
                <Button 
                  variant="outline"
                  className="border-2 border-purple-500 text-purple-400 hover:bg-purple-500/10 hover:text-purple-300 hover:border-purple-400"
                  disabled={untraceabilityLoading}
                >
                  <Shield className="h-4 w-4 mr-2" />
                  {untraceabilityLoading ? 'Processing...' : 'Begin Untraceability'}
                </Button>
              </AlertDialogTrigger>
              
              <AlertDialogContent className="bg-zinc-900 border-zinc-700 max-w-2xl">
                <AlertDialogHeader>
                  <AlertDialogTitle className="text-white flex items-center">
                    <Shield className="h-5 w-5 mr-2" />
                    Make Project Untraceable
                  </AlertDialogTitle>
                  <AlertDialogDescription className="text-zinc-300">
                    This will rewrite git history to make your project appear as if it was created during a hackathon timeframe. You can also clone the project to your own repository.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                
                <div className="py-4 space-y-4">
                  {/* Git Info and Hackathon Details */}
                  <div className="space-y-4">
                      <h3 className="text-lg font-semibold text-zinc-200">Hackathon Timeline</h3>
                      
                      <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-zinc-300 flex items-center">
                      <Calendar className="h-4 w-4 mr-2" />
                      Hackathon Date
                    </label>
                    <DatePicker
                      date={hackathonDate}
                      onDateChange={setHackathonDate}
                      placeholder="Select hackathon date"
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-zinc-300 flex items-center">
                      <Clock className="h-4 w-4 mr-2" />
                      Start Time
                    </label>
                    <TimePicker
                      value={hackathonStartTime}
                      onChange={setHackathonStartTime}
                      placeholder="Select start time"
                    />
                  </div>
                      </div>

                      <div className="space-y-2">
                        <label className="text-sm font-medium text-zinc-300">Duration (hours)</label>
                        <Input
                          type="number"
                          value={hackathonDuration}
                          onChange={(e) => setHackathonDuration(e.target.value)}
                          className="bg-zinc-800 border-zinc-700 text-white"
                          min="12"
                          max="168"
                          placeholder="48"
                    />
                  </div>

                      {/* Team Members */}
                      <div className="space-y-4">
                        <div className="flex items-center justify-between">
                    <label className="text-sm font-medium text-zinc-300 flex items-center">
                      <User className="h-4 w-4 mr-2" />
                            Team Members
                    </label>
                          <Button
                            type="button"
                            onClick={handleAddTeamMember}
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
                                onClick={() => handleRemoveTeamMember(index)}
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
                                onChange={(e) => handleUpdateTeamMember(index, 'username', e.target.value)}
                                className="bg-zinc-900 border-zinc-600 text-white"
                                placeholder="username"
                              />
                              <Input
                                type="email"
                                value={member.email}
                                onChange={(e) => handleUpdateTeamMember(index, 'email', e.target.value)}
                                className="bg-zinc-900 border-zinc-600 text-white"
                                placeholder="email@example.com"
                              />
                    <Input
                      type="text"
                                value={member.name}
                                onChange={(e) => handleUpdateTeamMember(index, 'name', e.target.value)}
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
                          Target Repository URL (optional)
                    </label>
                    <Input
                          type="url"
                          value={targetRepositoryUrl}
                          onChange={(e) => setTargetRepositoryUrl(e.target.value)}
                      className="bg-zinc-800 border-zinc-700 text-white"
                          placeholder="https://github.com/username/new-repo.git (optional)"
                    />
                        <p className="text-xs text-zinc-500">
                          If provided, the project will be cloned to this new repository
                        </p>
                  </div>
                    </div>
                </div>
                    
                <div className="flex justify-end space-x-3 border-t border-zinc-700 pt-4">
                  <AlertDialogAction
                    onClick={() => setShowUntraceabilityModal(false)}
                    className="bg-zinc-700 hover:bg-zinc-600 text-white"
                  >
                    Cancel
                  </AlertDialogAction>
                  <AlertDialogAction
                    onClick={handleUntraceability}
                    className="border-2 border-purple-500 text-purple-400 hover:bg-purple-500/10 hover:text-purple-300 hover:border-purple-400 bg-transparent"
                    disabled={untraceabilityLoading}
                  >
                    {untraceabilityLoading ? 'Processing...' : 'Begin Untraceability'}
                  </AlertDialogAction>
                    </div>
              </AlertDialogContent>
            </AlertDialog>

            {/* PANIC Button */}
            <Button 
              variant="outline"
              onClick={handlePanicMode}
              disabled={panicLoading}
              className="border-red-600 text-red-400 hover:bg-red-600 hover:text-white animate-pulse"
            >
              {panicLoading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  PANIC MODE...
                </>
              ) : (
                '🚨 PANIC'
              )}
            </Button>

            {/* Progress Modal - Simple Loading */}
            <AlertDialog open={showProgressModal} onOpenChange={setShowProgressModal}>
              <AlertDialogContent className="bg-zinc-900 border-zinc-700">
                <AlertDialogHeader>
                  <AlertDialogTitle className="text-white flex items-center">
                    <Shield className="h-5 w-5 mr-2" />
                    Making Project Untraceable
                  </AlertDialogTitle>
                </AlertDialogHeader>
                
                <div className="py-8 flex flex-col items-center space-y-4">
                  <Loader2 className="h-12 w-12 animate-spin text-blue-500" />
                  <div className="text-center space-y-2">
                    <p className="text-lg font-medium text-zinc-300">
                      Rewriting Git History on All Branches
                    </p>
                  </div>
                </div>

                <div className="flex justify-end border-t border-zinc-700 pt-4">
                  <Button
                    onClick={() => {
                      setShowProgressModal(false);
                      setUntraceabilityLoading(false);
                    }}
                    variant="outline"
                    className="border-zinc-600 text-zinc-300 hover:bg-zinc-800"
                    disabled={untraceabilityLoading}
                  >
                    {untraceabilityLoading ? 'Processing...' : 'Cancel'}
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
                    {getFileIcon(selectedFile, expandedFolders)}
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
                  <EditableCodeEditor
                    value={stripMarkdownWrapper(selectedFile.content)}
                    language={getSyntaxLanguage(selectedFile.extension || '', selectedFile.content)}
                    fileName={selectedFile.name}
                    projectName={projectName}
                    filePath={selectedFile.path}
                    onSave={handleFileSave}
                    onReady={setEditorRef}
                    height="100%"
                  />
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
      
      {/* Git History Viewer */}
      <GitHistoryViewer 
        projectName={projectName}
        isVisible={showGitHistory}
        onClose={() => setShowGitHistory(false)}
      />
      
      {/* PANIC Result Modal */}
      <AlertDialog open={showPanicResultModal} onOpenChange={setShowPanicResultModal}>
        <AlertDialogContent className="bg-zinc-900 border-zinc-800 max-w-2xl">
          <AlertDialogHeader>
            <AlertDialogTitle className={`text-xl flex items-center ${panicResult?.success ? 'text-green-400' : 'text-red-400'}`}>
              {panicResult?.success ? '🚨 PANIC MODE COMPLETE! 🚨' : '❌ PANIC MODE FAILED'}
            </AlertDialogTitle>
            <AlertDialogDescription asChild>
              <div className="text-zinc-300 space-y-4">
                {panicResult?.success ? (
                  <>
                    <div className="bg-green-900/20 border border-green-800 rounded-lg p-4">
                      <div className="font-bold text-green-300 mb-2">✅ Emergency tic-tac-toe project deployed!</div>
                      <div className="text-sm space-y-1">
                        <div>Commit: <code className="bg-zinc-800 px-1 rounded text-green-300">{panicResult.commit_hash}</code></div>
                        <div>Project: <code className="bg-zinc-800 px-1 rounded text-blue-300">{panicResult.project_name}</code></div>
                      </div>
                    </div>
                    
                    <div className="bg-blue-900/20 border border-blue-800 rounded-lg p-4">
                      <div className="font-bold text-blue-300 mb-2">🎮 Open Your Emergency Project:</div>
                      {panicResult.openedSuccessfully ? (
                        <div className="text-green-300">✅ Project opened in new tab automatically!</div>
                      ) : (
                        <div className="space-y-2">
                          <div className="text-amber-300">⚠️ Popup blocked. Click the link below to open manually:</div>
                          <div className="flex items-center space-x-2">
                            <a 
                              href={panicResult.fileUrl} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="flex-1 bg-zinc-800 p-2 rounded border border-blue-600 text-blue-300 hover:bg-zinc-700 hover:border-blue-500 transition-colors break-all"
                            >
                              🔗 {panicResult.fileUrl}
                            </a>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => {
                                navigator.clipboard.writeText(panicResult.fileUrl);
                                // Optional: Show a temporary toast or feedback
                              }}
                              className="border-zinc-600 text-zinc-300 hover:bg-zinc-700 px-3"
                            >
                              <Copy className="h-4 w-4" />
                            </Button>
                          </div>
                          <div className="text-xs text-zinc-500">💡 Click the copy button to copy URL to clipboard</div>
                        </div>
                      )}
                    </div>
                    
                    <div className="bg-amber-900/20 border border-amber-800 rounded-lg p-3">
                      <div className="text-amber-300 text-sm">
                        💡 <strong>Recovery Info:</strong> Original author information saved to{' '}
                        <code className="bg-zinc-800 px-1 rounded">.panic_recovery_info.json</code>
                      </div>
                    </div>
                  </>
                ) : (
                  <div className="bg-red-900/20 border border-red-800 rounded-lg p-4">
                    <div className="font-bold text-red-300 mb-2">❌ Error:</div>
                    <div className="text-red-200">{panicResult?.message || 'Unknown error occurred'}</div>
                  </div>
                )}
              </div>
            </AlertDialogDescription>
          </AlertDialogHeader>
          
          <div className="flex justify-end mt-6">
            <Button 
              onClick={() => setShowPanicResultModal(false)}
              className="bg-zinc-700 hover:bg-zinc-600 text-white"
            >
              Close
            </Button>
          </div>
        </AlertDialogContent>
      </AlertDialog>

    </div>
  );
} 