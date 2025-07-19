"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { GlowingEffect } from "@/components/ui/glowing-effect";
import { PlaceholdersAndVanishInput } from "@/components/ui/placeholders-and-vanish-input";
import { Search, Github } from "lucide-react";

const searchPlaceholders = [
  "react, nextjs, typescript...",
];

export default function Home() {
  const router = useRouter();
  const [technologies, setTechnologies] = useState("");
  const [githubUrl, setGithubUrl] = useState("");
  const [isNavigating, setIsNavigating] = useState(false);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setTechnologies(e.target.value);
  };

  const handleFormSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (isNavigating) return;

    setIsNavigating(true);
    
    // Allow vanish and overlay animations to complete
    setTimeout(() => {
      const params = new URLSearchParams();
      params.set('technologies', technologies || '');
      router.push(`/results?${params.toString()}`);
    }, 800); 
  };

  const handleGithubSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (isNavigating || !githubUrl.trim()) return;

    setIsNavigating(true);
    
    try {
      // Extract repo name from GitHub URL
      const urlPattern = /github\.com\/([^\/]+)\/([^\/]+)/;
      const match = githubUrl.match(urlPattern);
      
      if (!match) {
        alert('Please enter a valid GitHub repository URL');
        setIsNavigating(false);
        return;
      }
      
      const [, owner, repo] = match;
      const projectName = `${owner}-${repo}`;
      
      // Navigate to results page with the project name
      const params = new URLSearchParams();
      params.set('project', projectName);
      params.set('clone_url', githubUrl);
      router.push(`/results?${params.toString()}`);
    } catch (error) {
      console.error('Error processing GitHub URL:', error);
      alert('Error processing GitHub URL');
      setIsNavigating(false);
    }
  };

  return (
    <div className="min-h-screen bg-black relative">
      <AnimatePresence>
        {isNavigating && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.4, ease: "easeInOut" }}
            className="fixed inset-0 bg-black z-[110]"
          />
        )}
      </AnimatePresence>

      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-purple-500/20 rounded-full mix-blend-screen filter blur-xl animate-blob"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-blue-500/20 rounded-full mix-blend-screen filter blur-xl animate-blob animation-delay-2000"></div>
        <div className="absolute top-40 left-40 w-80 h-80 bg-pink-500/20 rounded-full mix-blend-screen filter blur-xl animate-blob animation-delay-4000"></div>
        <div className="absolute top-1/3 right-1/3 w-60 h-60 bg-cyan-500/15 rounded-full mix-blend-screen filter blur-xl animate-blob animation-delay-6000"></div>
        <div className="absolute bottom-1/4 left-1/2 w-72 h-72 bg-violet-500/15 rounded-full mix-blend-screen filter blur-xl animate-blob animation-delay-8000"></div>
      </div>

      <div className="relative z-10 container mx-auto px-4 py-8 flex flex-col items-center justify-center min-h-screen">
        <div className="text-center mb-12">
          <h1 className="text-6xl font-bold text-white mb-4 bg-gradient-to-r from-purple-400 via-pink-400 to-blue-400 bg-clip-text text-transparent">
            Steal a Hackathon Project
          </h1>
          <p className="text-xl text-zinc-400 max-w-2xl mx-auto">
            Because we love being lazy and stealing other people's work.
          </p>
        </div>

        <div className="max-w-4xl w-full mx-auto mb-12 space-y-8">
          {/* GitHub Repository Option */}
          <div className="relative rounded-2xl border border-zinc-800 p-2 md:rounded-3xl md:p-3">
            <GlowingEffect />
            <div className="relative overflow-hidden rounded-xl bg-zinc-900/50 p-6 border border-zinc-800 backdrop-blur-sm">
              <div className="text-center mb-6">
                <div className="flex items-center justify-center mb-3">
                  <Github className="h-6 w-6 text-purple-400 mr-2" />
                  <h3 className="text-white text-xl font-semibold">Clone a GitHub Repository</h3>
                </div>
                <p className="text-zinc-400">
                  Paste a GitHub repository URL to clone and modify it directly
                </p>
              </div>
              
              <form onSubmit={handleGithubSubmit} className="space-y-4">
                <div className="relative">
                  <Input
                    type="url"
                    value={githubUrl}
                    onChange={(e) => setGithubUrl(e.target.value)}
                    placeholder="https://github.com/username/repository"
                    className="w-full bg-zinc-800 border-zinc-700 text-white placeholder-zinc-500 focus:border-purple-500 focus:ring-purple-500/20 text-lg py-6 pl-12"
                    disabled={isNavigating}
                  />
                  <Github className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 text-zinc-500" />
                </div>
                <Button
                  type="submit"
                  disabled={isNavigating || !githubUrl.trim()}
                  variant="outline"
                  className="w-full border-purple-500 hover:bg-purple-500/10 text-purple-500 font-semibold py-6 text-lg transition-all duration-200"
                >
                  {isNavigating ? 'Cloning Repository...' : 'Clone Repository'}
                </Button>
              </form>
            </div>
          </div>

          {/* OR Divider */}
          <div className="relative flex items-center justify-center">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-zinc-700"></div>
            </div>
            <div className="relative bg-black px-4">
              <span className="text-zinc-500 text-sm font-medium">OR</span>
            </div>
          </div>

          {/* Technology Search Option */}
          <div className="relative rounded-2xl border border-zinc-800 p-2 md:rounded-3xl md:p-3">
            <GlowingEffect />
            <div className="relative overflow-hidden rounded-xl bg-zinc-900/50 p-6 border border-zinc-800 backdrop-blur-sm">
              <div className="text-center mb-6">
                <div className="flex items-center justify-center mb-3">
                  <Search className="h-6 w-6 text-blue-400 mr-2" />
                  <h3 className="text-white text-xl font-semibold">Search by Technologies</h3>
                </div>
                <p className="text-zinc-400">
                  Enter technologies separated by commas, or skip for general hackathon projects
                </p>
              </div>
              
              <PlaceholdersAndVanishInput
                placeholders={searchPlaceholders}
                onChange={handleInputChange}
                onSubmit={handleFormSubmit}
              />
            </div>
          </div>
        </div>
      </div>

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
      `}</style>
    </div>
  );
}

