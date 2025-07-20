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
  operation: 'manual_edit' | 'save' | 'add_comments' | 'rename_variables' | 'refactor_file' | 'untraceable_changes';
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
  const manualEditTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Ensure we're on the client side
  useEffect(() => {
    setIsClient(true);
    
    // Cleanup timeout on unmount
    return () => {
      if (manualEditTimeoutRef.current) {
        clearTimeout(manualEditTimeoutRef.current);
      }
    };
  }, []);

  // Initialize with the first version of the content
  useEffect(() => {
    if (isClient && value !== undefined && history.length === 0) {
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
  }, [value, isClient, history.length]);

  // This is the core logic that updates the editor when undo/redo changes the history index
  useEffect(() => {
    const currentEntry = history[historyIndex];
    if (currentEntry && currentEntry.content !== editorValue) {
      setEditorValue(currentEntry.content);

      // Automatically save the change to the file
      (async () => {
        setIsSaving(true);
        try {
          const response = await fetch(`http://localhost:8000/api/file/save/${projectName}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              file_path: filePath,
              content: currentEntry.content
            })
          });

          if (!response.ok) {
            throw new Error('Failed to save file on history change');
          }
          setHasUnsavedChanges(false);
        } catch (error) {
          console.error('Error saving file on history change:', error);
          setHasUnsavedChanges(true);
        } finally {
          setIsSaving(false);
        }
      })();
    }
  }, [historyIndex, history, projectName, filePath]); // Added dependencies

  // Adds a new state to the history stack
  const addToHistory = useCallback((content: string, operation: HistoryEntry['operation'], description: string) => {
    setHistory(currentHistory => {
      setHistoryIndex(currentIndex => {
        const newHistory = currentHistory.slice(0, currentIndex + 1);
        newHistory.push({
          content,
          timestamp: Date.now(),
          operation,
          description
        });
        
        const finalHistory = newHistory.length > 50 ? newHistory.slice(-50) : newHistory;
        const newIndex = finalHistory.length - 1;

        // Manually update history and index to avoid stale state issues
        queueMicrotask(() => {
          setHistory(finalHistory);
          setHistoryIndex(newIndex);
        });
        
        return currentIndex; // This will be replaced by the microtask
      });
      return currentHistory; // This will be replaced by the microtask
    });
  }, []);
  
  // Expose a method for parent components to update content and history
  const updateContent = useCallback((content: string, operation: HistoryEntry['operation'], description: string) => {
    setEditorValue(content);
    addToHistory(content, operation, description);
  }, [addToHistory]);

  const addManualEditToHistory = useCallback((content: string) => {
    if (manualEditTimeoutRef.current) {
      clearTimeout(manualEditTimeoutRef.current);
    }
    manualEditTimeoutRef.current = setTimeout(() => {
      addToHistory(content, 'manual_edit', 'Manual edit');
    }, 1000);
  }, [addToHistory]);
  
  // When the user types, update the editor value and schedule a history update
  const handleEditorChange = useCallback((newValue: string | undefined) => {
    if (newValue !== undefined && newValue !== editorValue) {
      setEditorValue(newValue);
      setHasUnsavedChanges(true);
      onChange?.(newValue);
      addManualEditToHistory(newValue);
    }
  }, [editorValue, onChange, addManualEditToHistory]);

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
    setHistoryIndex(prevIndex => Math.max(0, prevIndex - 1));
  }, []);

  const handleRedo = useCallback(() => {
    setHistory(currentHistory => {
      setHistoryIndex(prevIndex => Math.min(currentHistory.length - 1, prevIndex + 1));
      return currentHistory;
    });
  }, []);

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
  }, [isClient, editorMounted, addToHistory, updateContent, handleUndo, handleRedo, historyIndex, history.length]);

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
            disabled={historyIndex <= 0}
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
            disabled={historyIndex >= history.length - 1}
            variant="ghost"
            size="sm"
            className="h-7 px-2 text-zinc-400 hover:text-white disabled:opacity-50"
            title="Redo (Cmd+Shift+Z)"
          >
            <Redo2 className="h-3 w-3 mr-1" />
            Redo
          </Button>
          {history[historyIndex] && (
            <span className="text-xs text-zinc-500 ml-2">
              {history[historyIndex].description}
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
            mouseWheelZoom: true,
            // Disable error markers and red underlines
            'semanticHighlighting.enabled': false,
            'occurrencesHighlight': false,
            'renderValidationDecorations': 'off',
            'hideCursorInOverviewRuler': true
          }}
        />
      </div>
    </div>
  );
} 