"use client";

import { Suspense } from "react";
import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useRouter, useSearchParams } from "next/navigation";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { MultiStepLoader } from "@/components/ui/multi-step-loader";
import { GlowingEffect } from "@/components/ui/glowing-effect";
import { StatefulButton } from "@/components/ui/stateful-button";
import { Star, GitFork, Code, Trophy, ChevronDown, ArrowLeft } from "lucide-react";

interface Project {
  name: string;
  description: string;
  technologies: string[];
  readme: string;
  stars: number;
  forks: number;
  language: string;
  url: string;
  complexity_score: number;
  innovation_indicators: string[];
}

interface SearchResponse {
  projects: Project[];
  total_found: number;
  search_technologies: string[];
}

const searchingStates = [
  { text: "Scanning GitHub repositories..." },
  { text: "Filtering hackathon projects..." },
  { text: "Analyzing project technologies..." },
  { text: "Checking project creativity..." },
  { text: "Evaluating code complexity..." },
  { text: "Finding the perfect steal..." },
  { text: "Preparing your heist options..." },
  { text: "Almost ready to steal! 🏴‍☠️" },
];

function ResultsPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [isSearching, setIsSearching] = useState(true);
  const [projects, setProjects] = useState<Project[]>([]);

  const [error, setError] = useState("");
  const [expandedReadmes, setExpandedReadmes] = useState<Set<string>>(new Set());
  const [searchTechnologies, setSearchTechnologies] = useState<string[]>([]);

  useEffect(() => {
    const technologies = searchParams.get('technologies');
    const projectName = searchParams.get('project');
    const cloneUrl = searchParams.get('clone_url');

    if (cloneUrl && projectName) {
      // If we have a clone URL, directly clone and navigate
      handleDirectClone(projectName, cloneUrl);
    } else if (typeof technologies === 'string') {
      handleSearch(technologies);
    } else {
      setIsSearching(false);
    }
  }, [searchParams, router]);

  const handleSearch = async (technologiesParam: string) => {
    setIsSearching(true);
    setError("");
    setProjects([]);

    try {
      const techArray = technologiesParam
        .split(",")
        .map(tech => tech.trim())
        .filter(tech => tech.length > 0);

      setSearchTechnologies(techArray);

      const response = await axios.post<SearchResponse>("http://localhost:8000/api/search", {
        technologies: techArray
      });

      setProjects(response.data.projects);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to search for projects");
    } finally {
      setTimeout(() => setIsSearching(false), 500);
    }
  };

  const handleDirectClone = async (projectName: string, cloneUrl: string) => {
    try {
      const response = await axios.post("http://localhost:8000/api/clone", {
        project_name: projectName,
        project_url: cloneUrl,
        clone_url: cloneUrl.endsWith('.git') ? cloneUrl : `${cloneUrl}.git`
      });

      // Navigate to the IDE page to view the stolen project
      router.push(`/project/${encodeURIComponent(projectName)}`);
    } catch (err: any) {
      setError(err.response?.data?.message || "Failed to steal project");
      throw err;
    }
  };

  const handleSteal = async (project: Project) => {
    try {
      const cloneUrl = project.url.endsWith('.git') ? project.url : `${project.url}.git`;
      
      const response = await axios.post("http://localhost:8000/api/clone", {
        project_name: project.name,
        project_url: project.url,
        clone_url: cloneUrl
      });

      // Navigate to the IDE page to view the stolen project
      router.push(`/project/${encodeURIComponent(project.name)}`);
    } catch (err: any) {
      setError(err.response?.data?.message || "Failed to steal project");
      throw err;
    }
  };

  const toggleReadme = (projectName: string) => {
    setExpandedReadmes(prev => {
      const newSet = new Set(prev);
      if (newSet.has(projectName)) {
        newSet.delete(projectName);
      } else {
        newSet.add(projectName);
      }
      return newSet;
    });
  };

  const formatReadme = (readme: string) => {
    // First handle triple backtick code blocks
    let formatted = readme.replace(/```[\s\S]*?```/g, (match) => {
      const code = match.replace(/```\w*\n?/g, '').replace(/```$/g, '');
      return `<pre class="bg-zinc-800/70 border border-zinc-700 rounded-md p-3 my-3 overflow-x-auto"><code class="text-zinc-200 font-mono text-xs whitespace-pre-wrap break-words">${code.trim()}</code></pre>`;
    });

    // Handle inline code (single backticks) - but only if not already in a code block
    formatted = formatted.replace(/`([^`\n]+)`/g, '<code class="bg-zinc-700/60 px-1.5 py-0.5 rounded text-zinc-200 font-mono text-xs">$1</code>');

    // Handle headers
    formatted = formatted.replace(/#+\s?(.+)/g, '<h3 class="font-bold text-white mb-2 mt-4 text-sm">$1</h3>');
    
    // Handle bold text
    formatted = formatted.replace(/\*\*(.+?)\*\*/g, '<strong class="font-semibold text-white">$1</strong>');
    
    // Handle italic text
    formatted = formatted.replace(/\*(.+?)\*/g, '<em class="italic text-zinc-300">$1</em>');
    
    // Handle links
    formatted = formatted.replace(/\[(.+?)\]\((.+?)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer" class="text-blue-400 hover:text-blue-300 underline">$1</a>');
    
    // Handle line breaks, but preserve structure within code blocks
    formatted = formatted.replace(/\n/g, '<br />');

    return formatted;
  };

  const goBackToHome = () => {
    router.push('/');
  };

  return (
    <div className="min-h-screen bg-black relative">
      <AnimatePresence>
        {isSearching && (
          <motion.div
            key="loader"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.5 }}
            className="fixed inset-0 z-[100] flex items-center justify-center backdrop-blur-2xl"
          >
            <MultiStepLoader loadingStates={searchingStates} loading={isSearching} duration={1200} />
          </motion.div>
        )}
      </AnimatePresence>

      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-purple-500/20 rounded-full mix-blend-screen filter blur-xl animate-blob"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-blue-500/20 rounded-full mix-blend-screen filter blur-xl animate-blob animation-delay-2000"></div>
        <div className="absolute top-40 left-40 w-80 h-80 bg-pink-500/20 rounded-full mix-blend-screen filter blur-xl animate-blob animation-delay-4000"></div>
        <div className="absolute top-1/3 right-1/3 w-60 h-60 bg-cyan-500/15 rounded-full mix-blend-screen filter blur-xl animate-blob animation-delay-6000"></div>
        <div className="absolute bottom-1/4 left-1/2 w-72 h-72 bg-violet-500/15 rounded-full mix-blend-screen filter blur-xl animate-blob animation-delay-8000"></div>
      </div>

      <AnimatePresence>
        {!isSearching && (
          <motion.div
            key="results"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="relative z-10 container mx-auto px-4 py-8"
          >
            <div className="text-center mb-8">
              <Button 
                onClick={goBackToHome}
                className="mb-6 bg-zinc-800 hover:bg-zinc-700 text-white border border-zinc-600"
              >
                <ArrowLeft className="h-4 w-4 mr-2" />
                Go Back to Steal Other Hackathons
              </Button>
              <h1 className="text-4xl font-bold text-white mb-4 bg-gradient-to-r from-purple-400 via-pink-400 to-blue-400 bg-clip-text text-transparent">
                Results
              </h1>
              {searchTechnologies.length > 0 && (
                <div className="flex flex-wrap gap-2 justify-center mb-4">
                  <span className="text-zinc-400">Searching for:</span>
                  {searchTechnologies.map((tech) => (
                    <Badge key={tech} className="bg-purple-600 text-white">
                      {tech}
                    </Badge>
                  ))}
                </div>
              )}
              <p className="text-lg text-zinc-400">
                Found {projects.length} perfect targets.
              </p>
            </div>

            {error && (
              <div className="text-red-400 text-center mb-8 p-4 bg-red-900/20 rounded-lg border border-red-800">
                {error}
              </div>
            )}

            <motion.div 
              className="grid md:grid-cols-2 lg:grid-cols-3 gap-6"
              variants={{
                hidden: { opacity: 0 },
                visible: {
                  opacity: 1,
                  transition: { staggerChildren: 0.1 },
                },
              }}
              initial="hidden"
              animate="visible"
            >
              {projects.map((project) => {
                const isExpanded = expandedReadmes.has(project.name);
                return (
                  <motion.div
                    key={project.name}
                    variants={{
                      hidden: { opacity: 0, y: 20 },
                      visible: { opacity: 1, y: 0 },
                    }}
                    className="group"
                  >
                    <div className="relative h-full rounded-2xl border border-zinc-800 p-2 md:rounded-3xl md:p-3">
                      <GlowingEffect />
                      <div className="relative flex flex-col h-full overflow-hidden rounded-xl bg-zinc-900/50 p-6 border border-zinc-800 backdrop-blur-sm">
                        {/* Static Content */}
                        <div>
                          <div className="flex items-start justify-between mb-4">
                            <div className="flex-1">
                              <h3 className="text-xl font-semibold text-white mb-2 group-hover:text-purple-300 transition-colors">
                                {project.name}
                              </h3>
                              <div className="flex items-center space-x-4 text-zinc-400 text-sm">
                                <div className="flex items-center space-x-1">
                                  <Star className="h-4 w-4" />
                                  <span>{project.stars}</span>
                                </div>
                                <div className="flex items-center space-x-1">
                                  <GitFork className="h-4 w-4" />
                                  <span>{project.forks}</span>
                                </div>
                                <div className="flex items-center space-x-1">
                                  <Code className="h-4 w-4" />
                                  <span>{project.language}</span>
                                </div>
                              </div>
                            </div>
                            <Badge className="bg-gradient-to-r from-emerald-600 to-teal-600 text-white border-none">
                              <Trophy className="h-3 w-3 mr-1" />
                              {project.complexity_score}/10
                            </Badge>
                          </div>
                          <p className="text-zinc-300 text-sm mb-4">{project.description}</p>
                          <div className="flex flex-wrap gap-2 mb-4">
                            {project.technologies.map((tech) => (
                              <Badge key={tech} className="bg-slate-700 text-slate-200 hover:bg-slate-600 border-slate-600">
                                {tech}
                              </Badge>
                            ))}
                          </div>
                          {project.innovation_indicators.length > 0 && (
                            <div className="space-y-2 mb-4">
                              <p className="text-xs text-zinc-500 font-medium">Innovation Features:</p>
                              <div className="flex flex-wrap gap-1">
                                {project.innovation_indicators.map((indicator) => (
                                  <Badge key={indicator} className="text-xs bg-amber-900/30 text-amber-300 border-amber-700">
                                    {indicator}
                                  </Badge>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>

                        {/* README Section */}
                        <div className="mb-4">
                          <div className="bg-zinc-800/50 p-3 rounded-md border border-zinc-700">
                            <button
                              onClick={() => toggleReadme(project.name)}
                              className="flex items-center justify-between w-full text-left hover:bg-zinc-700/30 rounded p-1 transition-colors"
                            >
                              <p className="text-xs text-zinc-500 font-medium">README Preview:</p>
                              <motion.div animate={{ rotate: isExpanded ? 180 : 0 }} transition={{ duration: 0.2 }}>
                                <ChevronDown className="h-4 w-4 text-zinc-400" />
                              </motion.div>
                            </button>
                            <AnimatePresence initial={false}>
                              {isExpanded && (
                                <motion.div
                                  key="content"
                                  initial="collapsed"
                                  animate="open"
                                  exit="collapsed"
                                  variants={{
                                    open: { opacity: 1, height: "auto" },
                                    collapsed: { opacity: 0, height: 0 },
                                  }}
                                  transition={{ duration: 0.4, ease: [0.04, 0.62, 0.23, 0.98] }}
                                  className="overflow-hidden"
                                >
                                  <div 
                                    className="readme-content text-xs text-zinc-300 pt-2 max-h-60 overflow-y-auto pr-2 w-full"
                                    style={{ wordBreak: 'break-word', overflowWrap: 'break-word' }}
                                    dangerouslySetInnerHTML={{ __html: formatReadme(project.readme) }}
                                  />
                                </motion.div>
                              )}
                            </AnimatePresence>
                          </div>
                        </div>

                        {/* Spacer to push button to the bottom */}
                        <div className="flex-1"></div>

                        {/* Steal Button */}
                        <StatefulButton
                          onClick={() => handleSteal(project)}
                          className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white font-bold"
                        >
                          Steal This Project 🏴‍☠️
                        </StatefulButton>
                      </div>
                    </div>
                  </motion.div>
                );
              })}
            </motion.div>


          </motion.div>
        )}
      </AnimatePresence>

      <style jsx>{`
        @keyframes blob {
          0% { transform: translate(0px, 0px) scale(1); }
          33% { transform: translate(30px, -50px) scale(1.1); }
          66% { transform: translate(-20px, 20px) scale(0.9); }
          100% { transform: translate(0px, 0px) scale(1); }
        }
        .animate-blob { animation: blob 7s infinite; }
        .animation-delay-2000 { animation-delay: 2s; }
        .animation-delay-4000 { animation-delay: 4s; }
        .animation-delay-6000 { animation-delay: 6s; }
        .animation-delay-8000 { animation-delay: 8s; }
        
        /* README code block improvements */
        :global(.readme-content pre) {
          margin: 0.75rem 0;
          border-radius: 0.375rem;
          max-width: 100%;
        }
        
        :global(.readme-content code) {
          font-family: 'SF Mono', Monaco, 'Inconsolata', 'Roboto Mono', Consolas, 'Courier New', monospace;
          font-size: 0.75rem;
          line-height: 1.4;
        }
        
        :global(.readme-content pre code) {
          display: block;
          padding: 0;
          background: transparent;
          border: none;
          white-space: pre-wrap;
          word-wrap: break-word;
        }
      `}</style>
    </div>
  );
}

export default function ResultsPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-black flex items-center justify-center text-white">
        Loading Results...
      </div>
    }>
      <ResultsPageContent />
    </Suspense>
  );
} 