"use client"

import * as React from "react"
import { format } from "date-fns"
import { Calendar as CalendarIcon } from "lucide-react"

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Calendar } from "@/components/ui/calendar"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"

interface DatePickerProps {
  date?: Date
  onDateChange: (date: Date | undefined) => void
  placeholder?: string
  disabled?: boolean
  className?: string
}

export function DatePicker({
  date,
  onDateChange,
  placeholder = "Pick a date",
  disabled = false,
  className
}: DatePickerProps) {
  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          className={cn(
            "w-full justify-start text-left font-normal bg-zinc-800 border-zinc-700 text-white hover:bg-zinc-700 hover:text-white",
            !date && "text-zinc-400",
            className
          )}
          disabled={disabled}
        >
          <CalendarIcon className="mr-2 h-4 w-4" />
          {date ? format(date, "PPP") : <span>{placeholder}</span>}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-auto p-0 bg-zinc-900 border-zinc-700" align="start">
        <Calendar
          mode="single"
          selected={date}
          onSelect={onDateChange}
          disabled={(date) =>
            date > new Date() || date < new Date("1900-01-01")
          }
          initialFocus
          className="bg-zinc-900"
          classNames={{
            months: "flex flex-col sm:flex-row space-y-4 sm:space-x-4 sm:space-y-0",
            month: "space-y-4",
            caption: "flex justify-between items-center pt-1 px-2",
            caption_label: "text-sm font-medium text-zinc-200",
            nav: "flex items-center space-x-1",
            nav_button: cn(
              "h-6 w-6 bg-transparent p-0 opacity-70 hover:opacity-100 text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200 rounded-md transition-all duration-200"
            ),
            nav_button_previous: "",
            nav_button_next: "",
            table: "w-full border-collapse space-y-1",
            head_row: "flex",
            head_cell: "text-zinc-500 rounded-md w-9 font-normal text-[0.8rem]",
            row: "flex w-full mt-2",
            cell: "h-9 w-9 text-center text-sm p-0 relative [&:has([aria-selected].day-range-end)]:rounded-r-md [&:has([aria-selected].day-outside)]:bg-zinc-800/50 [&:has([aria-selected])]:bg-zinc-800 first:[&:has([aria-selected])]:rounded-l-md last:[&:has([aria-selected])]:rounded-r-md focus-within:relative focus-within:z-20",
            day: cn(
              "h-9 w-9 p-0 font-normal aria-selected:opacity-100 text-zinc-300 hover:bg-zinc-800 hover:text-zinc-100"
            ),
            day_range_end: "day-range-end",
            day_selected: "bg-purple-600 text-white hover:bg-purple-600 hover:text-white focus:bg-purple-600 focus:text-white",
            day_today: "bg-zinc-800 text-zinc-100",
            day_outside: "day-outside text-zinc-600 opacity-50 aria-selected:bg-zinc-800/50 aria-selected:text-zinc-600 aria-selected:opacity-30",
            day_disabled: "text-zinc-600 opacity-50",
            day_range_middle: "aria-selected:bg-zinc-800 aria-selected:text-zinc-100",
            day_hidden: "invisible",
          }}
        />
      </PopoverContent>
    </Popover>
  )
} 