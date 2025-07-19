"use client"

import * as React from "react"
import { Clock } from "lucide-react"
import { cn } from "@/lib/utils"
import { Input } from "@/components/ui/input"

interface TimePickerProps {
  value: string
  onChange: (value: string) => void
  placeholder?: string
  disabled?: boolean
  className?: string
}

export function TimePicker({
  value,
  onChange,
  placeholder = "Select time",
  disabled = false,
  className
}: TimePickerProps) {
  return (
    <div className="relative">
      <Clock className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-zinc-400 pointer-events-none z-10" />
      <Input
        type="time"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        disabled={disabled}
        className={cn(
          "pl-10 bg-zinc-800 border-zinc-700 text-white hover:bg-zinc-700 focus:bg-zinc-700 focus:border-purple-500",
          className
        )}
      />
    </div>
  )
} 