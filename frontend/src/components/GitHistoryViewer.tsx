"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { 
  GitBranch, 
  GitCommit, 
  Clock, 
  User, 
  Copy, 
  RefreshCw,
  Calendar,
  Hash,
  ChevronDown,
  ChevronRight,
  Filter
} from "lucide-react";

interface Commit {
  hash: string;
  short_hash: string;
  author: {
    name: string;
    email: string;
  };
  date: string;
  relative_date: string;
  message: string;
  branches: string[];
  refs: string;
}

interface Branch {
  name: string;
  current: boolean;
  remote?: boolean;
}

interface GitHistoryData {
  commits: Commit[];
  branches: Branch[];
  current_branch: string;
  total_commits: number;
  repository_path: string;
}

interface GitHistoryViewerProps {
  projectName: string;
  isVisible: boolean;
  onClose: () => void;
}

export default function GitHistoryViewer({ projectName, isVisible, onClose }: GitHistoryViewerProps) {
  const [gitData, setGitData] = useState<GitHistoryData | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedBranch, setSelectedBranch] = useState<string>("");
  const [showAllBranches, setShowAllBranches] = useState(false);
  const [commitLimit, setCommitLimit] = useState(50);

  const fetchGitHistory = async (branch?: string) => {
    setLoading(true);
    try {
      const url = new URL(`http://localhost:8000/api/project/${encodeURIComponent(projectName)}/git/history`);
      if (branch) url.searchParams.append('branch', branch);
      url.searchParams.append('limit', commitLimit.toString());

      const response = await fetch(url.toString());
      if (response.ok) {
        const data = await response.json();
        setGitData(data);
        if (!selectedBranch) {
          setSelectedBranch(data.current_branch);
        }
      } else {
        console.error('Failed to fetch git history');
      }
    } catch (error) {
      console.error('Error fetching git history:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isVisible && projectName) {
      fetchGitHistory();
    }
  }, [isVisible, projectName, commitLimit]);

  const handleBranchChange = (branchName: string) => {
    setSelectedBranch(branchName);
    fetchGitHistory(branchName);
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const getCommitIcon = (commit: Commit) => {
    return <GitCommit className="h-4 w-4 text-pink-400" />;
  };

  const getAuthorInitials = (authorName: string) => {
    return authorName.split(' ').map(n => n[0]).join('').toUpperCase();
  };

  if (!isVisible) return null;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black bg-opacity-60 z-50 flex items-center justify-center p-6"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.95, opacity: 0 }}
        className="bg-gradient-to-br from-zinc-900 to-black rounded-xl shadow-2xl w-full max-w-7xl h-5/6 flex flex-col border border-zinc-800 backdrop-blur-sm"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-zinc-800 bg-gradient-to-r from-zinc-900/80 to-zinc-800/80 rounded-t-xl">
          <div className="flex items-center space-x-4">
            <div className="flex items-center justify-center w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-600 rounded-lg">
              <GitBranch className="h-5 w-5 text-white" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-white">Git History</h2>
              <p className="text-zinc-400 text-sm">Commit timeline for {projectName}</p>
            </div>
            <Badge variant="outline" className="text-zinc-300 border-zinc-600 bg-zinc-800/50">
              {projectName}
            </Badge>
          </div>
          <div className="flex items-center space-x-3">
            <Button
              variant="outline"
              size="sm"
              onClick={() => fetchGitHistory(selectedBranch)}
              disabled={loading}
              className="border-zinc-600 text-zinc-300 hover:bg-zinc-800 bg-zinc-900/50"
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={onClose}
              className="border-zinc-600 text-zinc-300 hover:bg-zinc-800 bg-zinc-900/50"
            >
              Close
            </Button>
          </div>
        </div>

        <div className="flex flex-1 overflow-hidden">
          {/* Sidebar */}
          <div className="w-72 bg-zinc-900/60 border-r border-zinc-800 p-6 overflow-y-auto">
            {/* Branch Selector */}
            <div className="mb-8">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-zinc-200">Branches</h3>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowAllBranches(!showAllBranches)}
                  className="p-2 h-8 w-8 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50"
                >
                  {showAllBranches ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                </Button>
              </div>
              
              {gitData && (
                <div className="space-y-2">
                  {gitData.branches
                    .filter(branch => showAllBranches || branch.current || branch.name === selectedBranch)
                    .map((branch) => (
                      <button
                        key={branch.name}
                        onClick={() => handleBranchChange(branch.name)}
                        className={`w-full text-left px-3 py-3 rounded-lg text-sm flex items-center space-x-3 transition-all duration-200 ${
                          selectedBranch === branch.name
                            ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-lg'
                            : 'text-zinc-300 hover:bg-zinc-800/60 hover:text-zinc-100'
                        }`}
                      >
                        <GitBranch className="h-4 w-4" />
                        <span className="font-medium">{branch.name}</span>
                        {branch.current && (
                          <Badge variant="outline" className="text-xs py-1 px-2 border-purple-400 text-purple-400 bg-purple-400/10">
                            current
                          </Badge>
                        )}
                      </button>
                    ))}
                </div>
              )}
            </div>

            {/* Stats */}
            {gitData && (
              <div className="bg-zinc-900/80 rounded-lg p-4 space-y-3 border border-zinc-800">
                <h4 className="text-sm font-semibold text-zinc-200 mb-3">Repository Stats</h4>
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between items-center">
                    <span className="text-zinc-400">Total Commits:</span>
                    <span className="text-zinc-200 font-semibold">{gitData.total_commits}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-zinc-400">Showing:</span>
                    <span className="text-zinc-200 font-semibold">{gitData.commits.length}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-zinc-400">Current Branch:</span>
                    <span className="text-purple-400 font-semibold">{gitData.current_branch}</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Main Content */}
          <div className="flex-1 flex flex-col overflow-hidden">
            {/* Commit List Header */}
            <div className="bg-zinc-900/60 border-b border-zinc-800 px-6 py-4">
              <div className="grid grid-cols-12 gap-6 text-sm font-semibold text-zinc-300 uppercase tracking-wide">
                <div className="col-span-3">Committer</div>
                <div className="col-span-5">Message</div>
                <div className="col-span-2">Commit Hash</div>
                <div className="col-span-2">Date</div>
              </div>
            </div>

            {/* Commit List */}
            <div className="flex-1 overflow-y-auto bg-black/40">
              {loading ? (
                <div className="flex items-center justify-center h-full">
                  <div className="flex flex-col items-center space-y-4 text-zinc-400">
                    <RefreshCw className="h-8 w-8 animate-spin text-purple-400" />
                    <span className="text-lg">Loading commit history...</span>
                  </div>
                </div>
              ) : gitData?.commits ? (
                <div className="divide-y divide-zinc-800/50">
                  {gitData.commits.map((commit, index) => (
                    <motion.div
                      key={commit.hash}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.01 }}
                      className="grid grid-cols-12 gap-6 px-6 py-4 hover:bg-zinc-900/40 transition-all duration-200 group"
                    >
                      {/* Committer */}
                      <div className="col-span-3 flex items-center space-x-3">
                        <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-600 rounded-full flex items-center justify-center text-sm font-bold text-white shadow-lg group-hover:shadow-xl transition-shadow">
                          {getAuthorInitials(commit.author.name)}
                        </div>
                        <div className="flex flex-col">
                          <span className="text-zinc-200 font-medium text-sm">
                            {commit.author.name}
                          </span>
                          <span className="text-zinc-400 text-xs">
                            {commit.author.email}
                          </span>
                        </div>
                      </div>

                      {/* Message */}
                      <div className="col-span-5 flex items-center">
                        <div className="flex items-center space-x-3">
                          {getCommitIcon(commit)}
                          <span className="text-zinc-200 font-medium text-sm leading-relaxed">
                            {commit.message}
                          </span>
                        </div>
                      </div>

                      {/* Hash */}
                      <div className="col-span-2 flex items-center">
                        <div className="flex items-center space-x-2 bg-zinc-900/60 rounded-lg px-3 py-2 group-hover:bg-zinc-800/60 transition-colors border border-zinc-800">
                          <Hash className="h-3 w-3 text-zinc-500" />
                          <code className="text-xs text-zinc-300 font-mono">
                            {commit.short_hash}
                          </code>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => copyToClipboard(commit.hash)}
                            className="p-1 h-6 w-6 text-zinc-500 hover:text-zinc-300 opacity-0 group-hover:opacity-100 transition-opacity"
                          >
                            <Copy className="h-3 w-3" />
                          </Button>
                        </div>
                      </div>

                      {/* Date */}
                      <div className="col-span-2 flex flex-col items-start justify-center space-y-1">
                        <div className="flex items-center text-xs text-zinc-400">
                          <Calendar className="h-3 w-3 mr-1" />
                          {commit.date}
                        </div>
                        <div className="flex items-center text-xs text-zinc-500">
                          <Clock className="h-3 w-3 mr-1" />
                          {commit.relative_date}
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              ) : (
                <div className="flex items-center justify-center h-full text-zinc-400">
                  <div className="text-center">
                    <GitBranch className="h-16 w-16 mx-auto mb-6 text-zinc-600" />
                    <p className="text-xl font-medium mb-2">No commit history available</p>
                    <p className="text-sm">This project might not be a git repository</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
} 