"use client";

import React, { useEffect, useState } from 'react';
import { Loader2 } from 'lucide-react';

interface MonacoWrapperProps {
  value: string;
  language: string;
  onChange?: (value: string | undefined) => void;
  onMount?: (editor: any) => void;
  height?: string;
  theme?: string;
  options?: any;
}

export default function MonacoWrapper({
  value,
  language,
  onChange,
  onMount,
  height = '100%',
  theme = 'vs-dark',
  options = {}
}: MonacoWrapperProps) {
  const [isClient, setIsClient] = useState(false);
  const [Editor, setEditor] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Ensure we're on client side
  useEffect(() => {
    setIsClient(true);
  }, []);

  // Load Monaco Editor dynamically
  useEffect(() => {
    if (!isClient) return;

    const loadMonaco = async () => {
      try {
        setLoading(true);
        setError(null);

        // Dynamic import with better error handling and timeout
        const loadPromise = import('@monaco-editor/react');
        const timeoutPromise = new Promise((_, reject) => 
          setTimeout(() => reject(new Error('Monaco Editor loading timeout')), 10000)
        );

        const result = await Promise.race([loadPromise, timeoutPromise]);
        setEditor(() => (result as any).default);
        setLoading(false);
      } catch (err) {
        console.error('Failed to load Monaco Editor:', err);
        setError(err instanceof Error ? err.message : 'Failed to load code editor');
        setLoading(false);
      }
    };

    loadMonaco();
  }, [isClient]);

  // Don't render on server side
  if (!isClient) {
    return (
      <div className="flex items-center justify-center h-full min-h-[400px]">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-blue-500" />
          <p className="text-zinc-400">Initializing editor...</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full min-h-[400px]">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-blue-500" />
          <p className="text-zinc-400">Loading code editor...</p>
          <p className="text-zinc-500 text-xs mt-2">This may take a moment...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full min-h-[400px] bg-zinc-900 border border-zinc-700 rounded">
        <div className="text-center p-8">
          <div className="text-red-400 mb-2">⚠️ Editor Loading Error</div>
          <p className="text-zinc-400 text-sm mb-4">{error}</p>
          <div className="space-y-2">
            <button 
              onClick={() => window.location.reload()} 
              className="block mx-auto px-4 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 transition-colors"
            >
              Reload Page
            </button>
            <p className="text-zinc-500 text-xs">
              If this persists, try clearing your browser cache
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (!Editor) {
    return (
      <div className="flex items-center justify-center h-full min-h-[400px] bg-zinc-900 border border-zinc-700 rounded">
        <div className="text-center p-8">
          <div className="text-orange-400 mb-2">⚠️ Editor Not Available</div>
          <p className="text-zinc-400 text-sm">Monaco Editor failed to initialize</p>
        </div>
      </div>
    );
  }

  const editorOptions = {
    fontSize: 14,
    lineHeight: 1.5,
    minimap: { enabled: true },
    wordWrap: 'on' as const,
    automaticLayout: true,
    scrollBeyondLastLine: false,
    readOnly: false,
    formatOnPaste: true,
    formatOnType: true,
    lineNumbers: 'on' as const,
    glyphMargin: true,
    folding: true,
    lineDecorationsWidth: 10,
    lineNumbersMinChars: 3,
    renderWhitespace: 'selection' as const,
    cursorBlinking: 'blink' as const,
    cursorSmoothCaretAnimation: 'on' as const,
    smoothScrolling: true,
    mouseWheelZoom: true,
    semanticHighlighting: { enabled: false },
    occurrencesHighlight: false,
    renderValidationDecorations: 'off' as const,
    hideCursorInOverviewRuler: true,
    ...options
  };

  return (
    <Editor
      height={height}
      defaultLanguage={language}
      value={value}
      onChange={onChange}
      onMount={onMount}
      theme={theme}
      options={editorOptions}
      loading={
        <div className="flex items-center justify-center h-full min-h-[400px]">
          <div className="text-center">
            <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-blue-500" />
            <p className="text-zinc-400">Setting up editor...</p>
          </div>
        </div>
      }
    />
  );
} 