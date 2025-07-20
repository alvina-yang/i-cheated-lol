"use client"

import React, { useState, useEffect } from 'react'

interface WinningChancesBarProps {
  className?: string
  initialPercentage?: number
  currentPercentage?: number
}

export function WinningChancesBar({ 
  className = "", 
  initialPercentage,
  currentPercentage 
}: WinningChancesBarProps) {
  const [percentage, setPercentage] = useState(0)

  useEffect(() => {
    if (currentPercentage !== undefined) {
      setPercentage(Math.min(100, currentPercentage))
    } else if (initialPercentage !== undefined) {
      setPercentage(initialPercentage)
    } else {
      // Generate random percentage between 70-80 as fallback
      const randomPercentage = Math.floor(Math.random() * 11) + 70 // 70-80
      setPercentage(randomPercentage)
    }
  }, [initialPercentage, currentPercentage])

  return (
    <div className={`bg-gray-900/50 border border-gray-700 rounded-lg p-4 ${className}`}>
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-medium text-gray-200">🏆 Winning Chances</h3>
        <span className="text-sm font-bold text-green-400">{percentage}%</span>
      </div>
      
      <div className="w-full bg-gray-700 rounded-full h-3 overflow-hidden">
        <div 
          className="h-full bg-gradient-to-r from-green-500 to-emerald-400 rounded-full transition-all duration-1000 ease-out relative"
          style={{ width: `${percentage}%` }}
        >
          {/* Animated shine effect */}
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-pulse" />
        </div>
      </div>
      
      {/* Status indicator */}
      <div className="mt-2 flex items-center text-xs text-gray-400">
        <div className="flex items-center">
          <div className={`w-2 h-2 rounded-full mr-2 ${
            percentage >= 75 ? 'bg-green-400' : 'bg-yellow-400'
          }`} />
          <span>
            {percentage >= 75 ? 'Strong contender' : 'Good chance'}
          </span>
        </div>
      </div>
    </div>
  )
} 