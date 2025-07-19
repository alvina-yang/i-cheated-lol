"use client";

import React, { useState, useEffect, useRef, useCallback } from 'react';
import dynamic from 'next/dynamic';
import { Button } from '@/components/ui/button';
import { Save, Undo2, Redo2, Loader2 } from 'lucide-react';

// Dynamically import Monaco Editor with SSR disabled
const Editor = dynamic(() => import('@monaco-editor/react'), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center h-full">
      <div className="text-center">
        <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-blue-500" />
        <p className="text-zinc-400">Loading editor...</p>
      </div>
    </div>
  )
});

interface HistoryEntry {
  content: string;
  timestamp: number;
  operation: 'manual_edit' | 'save' | 'add_comments' | 'rename_variables' | 'untraceable_changes';
  description: string;
}

interface EditableCodeEditorProps {
  value: string;
  language: string;
  fileName: string;
  projectName: string;
  filePath: string;
  onSave?: (content: string) => Promise<void>;
  onChange?: (content: string) => void;
  height?: string;
  onReady?: (editor: EditableCodeEditorRef) => void;
}

interface EditableCodeEditorRef {
  addToHistory: (content: string, operation: HistoryEntry['operation'], description: string) => void;
  updateContent: (content: string, operation: HistoryEntry['operation'], description: string) => void;
  undo: () => void;
  redo: () => void;
  canUndo: () => boolean;
  canRedo: () => boolean;
}

export default function EditableCodeEditor({
  value,
  language,
  fileName,
  projectName,
  filePath,
  onSave,
  onChange,
  height = '100%',
  onReady
}: EditableCodeEditorProps) {
  const [editorValue, setEditorValue] = useState(value);
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  const [isSaving, setIsSaving] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [isClient, setIsClient] = useState(false);
  const [editorMounted, setEditorMounted] = useState(false);
  const editorRef = useRef<any>(null);

  // Ensure we're on the client side
  useEffect(() => {
    setIsClient(true);
  }, []);

  // Initialize history with the original content
  useEffect(() => {
    if (isClient) {
      const initialEntry: HistoryEntry = {
        content: value,
        timestamp: Date.now(),
        operation: 'manual_edit',
        description: 'Initial content'
      };
      setHistory([initialEntry]);
      setHistoryIndex(0);
      setEditorValue(value);
    }
  }, [value, isClient]);

  // External update method for file operations
  const updateContent = useCallback((content: string, operation: HistoryEntry['operation'], description: string) => {
    addToHistory(content, operation, description);
    setEditorValue(content);
    setHasUnsavedChanges(false);
    
    // Update the editor content
    if (editorRef.current && editorMounted) {
      editorRef.current.setValue(content);
    }
  }, [editorMounted]);

  const addToHistory = useCallback((content: string, operation: HistoryEntry['operation'], description: string) => {
    const newEntry: HistoryEntry = {
      content,
      timestamp: Date.now(),
      operation,
      description
    };

    setHistory(prev => {
      // If we're not at the end of history, remove everything after current index
      const newHistory = prev.slice(0, historyIndex + 1);
      newHistory.push(newEntry);
      
      // Limit history to last 50 entries to prevent memory issues
      if (newHistory.length > 50) {
        return newHistory.slice(-50);
      }
      
      return newHistory;
    });
    
    setHistoryIndex(prev => {
      const newIndex = Math.min(prev + 1, 49); // Max index is 49 for 50 entries
      return newIndex;
    });
  }, [historyIndex]);

  // Expose methods to parent component
  useEffect(() => {
    if (onReady && isClient && editorMounted) {
      onReady({
        addToHistory,
        updateContent,
        undo: handleUndo,
        redo: handleRedo,
        canUndo: () => historyIndex > 0,
        canRedo: () => historyIndex < history.length - 1
      });
    }
  }, [onReady, addToHistory, updateContent, historyIndex, history.length, isClient, editorMounted]);

  const handleEditorChange = useCallback((newValue: string | undefined) => {
    if (newValue !== undefined && newValue !== editorValue) {
      setEditorValue(newValue);
      setHasUnsavedChanges(true);
      onChange?.(newValue);
    }
  }, [editorValue, onChange]);

  const handleSave = async () => {
    if (!hasUnsavedChanges || isSaving) return;

    setIsSaving(true);
    try {
      if (onSave) {
        await onSave(editorValue);
      } else {
        // Default save implementation - call the backend API
        const response = await fetch(`http://localhost:8000/api/file/save/${projectName}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            file_path: filePath,
            content: editorValue
          })
        });

        if (!response.ok) {
          throw new Error('Failed to save file');
        }
      }

      addToHistory(editorValue, 'save', `Saved ${fileName}`);
      setHasUnsavedChanges(false);
    } catch (error) {
      console.error('Error saving file:', error);
      alert('Failed to save file. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleUndo = useCallback(() => {
    if (historyIndex > 0) {
      const newIndex = historyIndex - 1;
      const previousEntry = history[newIndex];
      setHistoryIndex(newIndex);
      setEditorValue(previousEntry.content);
      setHasUnsavedChanges(previousEntry.content !== history.find(h => h.operation === 'save')?.content);
      
      // Update the editor content
      if (editorRef.current && editorMounted) {
        editorRef.current.setValue(previousEntry.content);
      }
    }
  }, [historyIndex, history, editorMounted]);

  const handleRedo = useCallback(() => {
    if (historyIndex < history.length - 1) {
      const newIndex = historyIndex + 1;
      const nextEntry = history[newIndex];
      setHistoryIndex(newIndex);
      setEditorValue(nextEntry.content);
      setHasUnsavedChanges(nextEntry.content !== history.find(h => h.operation === 'save')?.content);
      
      // Update the editor content
      if (editorRef.current && editorMounted) {
        editorRef.current.setValue(nextEntry.content);
      }
    }
  }, [historyIndex, history, editorMounted]);

  // Keyboard shortcuts - only on client side
  useEffect(() => {
    if (!isClient) return;

    const handleKeydown = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey)) {
        if (event.key === 's') {
          event.preventDefault();
          handleSave();
        } else if (event.key === 'z' && !event.shiftKey) {
          event.preventDefault();
          handleUndo();
        } else if ((event.key === 'z' && event.shiftKey) || event.key === 'y') {
          event.preventDefault();
          handleRedo();
        }
      }
    };

    document.addEventListener('keydown', handleKeydown);
    return () => document.removeEventListener('keydown', handleKeydown);
  }, [handleSave, handleUndo, handleRedo, isClient]);

  const handleEditorDidMount = (editor: any) => {
    editorRef.current = editor;
    setEditorMounted(true);
    
    // Set editor options
    editor.updateOptions({
      fontSize: 14,
      lineHeight: 1.5,
      minimap: { enabled: true },
      wordWrap: 'on',
      automaticLayout: true,
      scrollBeyondLastLine: false,
      readOnly: false,
      formatOnPaste: true,
      formatOnType: true
    });
  };

  const getLanguageForMonaco = (lang: string): string => {
    const languageMap: { [key: string]: string } = {
      'javascript': 'javascript',
      'typescript': 'typescript',
      'python': 'python',
      'java': 'java',
      'cpp': 'cpp',
      'c': 'c',
      'csharp': 'csharp',
      'html': 'html',
      'css': 'css',
      'scss': 'scss',
      'json': 'json',
      'xml': 'xml',
      'yaml': 'yaml',
      'markdown': 'markdown',
      'bash': 'shell',
      'shell': 'shell',
      'sql': 'sql',
      'php': 'php',
      'ruby': 'ruby',
      'go': 'go',
      'rust': 'rust',
      'swift': 'swift',
      'kotlin': 'kotlin'
    };
    
    return languageMap[lang.toLowerCase()] || 'plaintext';
  };

  const currentHistoryEntry = history[historyIndex];
  const canUndo = historyIndex > 0;
  const canRedo = historyIndex < history.length - 1;

  // Don't render anything on server side
  if (!isClient) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-blue-500" />
          <p className="text-zinc-400">Loading editor...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Editor Toolbar */}
      <div className="flex items-center justify-between px-4 py-2 bg-zinc-900/50 border-b border-zinc-800">
        <div className="flex items-center space-x-2">
          <Button
            onClick={handleUndo}
            disabled={!canUndo}
            variant="ghost"
            size="sm"
            className="h-7 px-2 text-zinc-400 hover:text-white disabled:opacity-50"
            title="Undo (Cmd+Z)"
          >
            <Undo2 className="h-3 w-3 mr-1" />
            Undo
          </Button>
          <Button
            onClick={handleRedo}
            disabled={!canRedo}
            variant="ghost"
            size="sm"
            className="h-7 px-2 text-zinc-400 hover:text-white disabled:opacity-50"
            title="Redo (Cmd+Shift+Z)"
          >
            <Redo2 className="h-3 w-3 mr-1" />
            Redo
          </Button>
          {currentHistoryEntry && (
            <span className="text-xs text-zinc-500 ml-2">
              {currentHistoryEntry.description}
            </span>
          )}
        </div>
        
        <div className="flex items-center space-x-2">
          {hasUnsavedChanges && (
            <span className="text-xs text-orange-400">● Unsaved changes</span>
          )}
          <Button
            onClick={handleSave}
            disabled={!hasUnsavedChanges || isSaving}
            variant="ghost"
            size="sm"
            className="h-7 px-2 bg-green-600/20 text-green-400 hover:bg-green-600/30 border border-green-700 disabled:opacity-50"
            title="Save (Cmd+S)"
          >
            <Save className="h-3 w-3 mr-1" />
            {isSaving ? 'Saving...' : 'Save'}
          </Button>
        </div>
      </div>

      {/* Monaco Editor */}
      <div className="flex-1">
        <Editor
          height={height}
          defaultLanguage={getLanguageForMonaco(language)}
          value={editorValue}
          onChange={handleEditorChange}
          onMount={handleEditorDidMount}
          theme="vs-dark"
          options={{
            fontSize: 14,
            lineHeight: 1.5,
            minimap: { enabled: true },
            wordWrap: 'on',
            automaticLayout: true,
            scrollBeyondLastLine: false,
            readOnly: false,
            formatOnPaste: true,
            formatOnType: true,
            lineNumbers: 'on',
            glyphMargin: true,
            folding: true,
            lineDecorationsWidth: 10,
            lineNumbersMinChars: 3,
            renderWhitespace: 'selection',
            cursorBlinking: 'blink',
            cursorSmoothCaretAnimation: "on",
            smoothScrolling: true,
            mouseWheelZoom: true
          }}
        />
      </div>
    </div>
  );
} 