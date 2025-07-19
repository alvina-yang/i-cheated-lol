"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { marked } from 'marked';
import { Button } from "@/components/ui/button";
import { Copy, ArrowLeft } from "lucide-react";

export default function PresentationPage() {
  const params = useParams();
  const router = useRouter();
  const projectName = params.name as string;
  
  const [presentationScript, setPresentationScript] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchPresentationScript = async () => {
      try {
        // First try to get existing script
        let response = await fetch(`http://localhost:8000/api/file/presentation-script/${encodeURIComponent(projectName)}`);
        let data = await response.json();
        
        // If no saved script exists, generate a new one
        if (!data.success || !data.script) {
          response = await fetch(`http://localhost:8000/api/file/generate-presentation-script`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ project_name: projectName })
          });
          
          if (!response.ok) {
            throw new Error('Failed to generate presentation script');
          }
          
          data = await response.json();
        }
        
        if (data.success) {
          setPresentationScript(data.script);
        } else {
          setError(data.message || 'Failed to generate presentation script');
        }
      } catch (err: any) {
        setError(err.message || 'Failed to generate presentation script');
      } finally {
        setLoading(false);
      }
    };

    fetchPresentationScript();
  }, [projectName]);

  if (loading) {
    return (
      <div className="min-h-screen bg-black text-white flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-orange-500 mx-auto mb-4" />
          <p>Generating presentation script...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-black text-white flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-400 mb-4">{error}</p>
          <Button onClick={() => router.back()}>Go Back</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-white">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-zinc-900/80 backdrop-blur-sm border-b border-zinc-800">
        <div className="max-w-5xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Button 
                variant="ghost" 
                onClick={() => router.back()}
                className="text-zinc-400 hover:text-white"
              >
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Project
              </Button>
              <h1 className="text-xl font-semibold">
                Presentation Script: {projectName}
              </h1>
            </div>
            <Button
              variant="outline"
              onClick={() => {
                navigator.clipboard.writeText(presentationScript);
              }}
              className="border-zinc-600 text-zinc-300 hover:bg-zinc-700"
            >
              <Copy className="h-4 w-4 mr-2" />
              Copy Script
            </Button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-5xl mx-auto px-6 py-8">
        <div className="prose prose-invert max-w-none">
          <div 
            className="markdown-content text-zinc-100"
            dangerouslySetInnerHTML={{ 
              __html: marked.parse(presentationScript, {
                breaks: true,
                gfm: true
              })
            }}
          />
        </div>
      </div>

      <style jsx global>{`
        .markdown-content h1 {
          font-size: 2rem;
          font-weight: 700;
          margin-bottom: 1.5rem;
          padding-bottom: 0.75rem;
          border-bottom: 1px solid rgb(63 63 70);
          color: rgb(244 244 245);
        }
        .markdown-content h2 {
          font-size: 1.6rem;
          font-weight: 600;
          margin-top: 2.5rem;
          margin-bottom: 1.25rem;
          color: rgb(228 228 231);
        }
        .markdown-content h3 {
          font-size: 1.3rem;
          font-weight: 600;
          margin-top: 2rem;
          margin-bottom: 1rem;
          color: rgb(212 212 216);
        }
        .markdown-content p {
          margin-bottom: 1.25rem;
          line-height: 1.7;
        }
        .markdown-content ul, .markdown-content ol {
          margin-left: 1.75rem;
          margin-bottom: 1.25rem;
        }
        .markdown-content li {
          margin-bottom: 0.75rem;
        }
        .markdown-content strong {
          color: rgb(244 244 245);
          font-weight: 600;
        }
        .markdown-content hr {
          margin: 2.5rem 0;
          border-color: rgb(63 63 70);
        }
        .markdown-content blockquote {
          border-left: 4px solid rgb(82 82 91);
          padding-left: 1.25rem;
          margin: 1.5rem 0;
          color: rgb(161 161 170);
        }
        .markdown-content code {
          background: rgb(39 39 42);
          padding: 0.2rem 0.4rem;
          border-radius: 0.25rem;
          font-size: 0.9em;
        }
      `}</style>
    </div>
  );
} 