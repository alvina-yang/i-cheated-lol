"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { GlowingEffect } from "@/components/ui/glowing-effect";
import { PlaceholdersAndVanishInput } from "@/components/ui/placeholders-and-vanish-input";

const searchPlaceholders = [
  "react, nextjs, typescript...",
];

export default function Home() {
  const router = useRouter();
  const [technologies, setTechnologies] = useState("");
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

        <div className="max-w-2xl w-full mx-auto mb-12">
          <div className="relative rounded-2xl border border-zinc-800 p-2 md:rounded-3xl md:p-3">
            <GlowingEffect />
            <div className="relative overflow-hidden rounded-xl bg-zinc-900/50 p-6 border border-zinc-800 backdrop-blur-sm">
              <div className="text-center mb-6">
                <h3 className="text-white text-xl font-semibold mb-2">Choose Your Target Technologies</h3>
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

