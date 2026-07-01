"use client";

import React, { useState } from "react";
import { CheckCircle2, Circle, Loader2, ChevronDown, ChevronUp } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export interface TaskStep {
  id: string;
  label: string;
  status: "pending" | "running" | "completed" | "failed";
}

interface ThinkingCardProps {
  steps: TaskStep[];
  elapsedSeconds?: number;
  etaSeconds?: number | null;
  progressPercent?: number;
  phaseLabel?: string;
}

const formatDuration = (seconds: number) => {
  const safeSeconds = Math.max(0, Math.round(seconds));
  const mins = Math.floor(safeSeconds / 60);
  const secs = safeSeconds % 60;
  return mins > 0 ? `${mins}m ${secs}s` : `${secs}s`;
};

export default function ThinkingCard({
  steps,
  elapsedSeconds = 0,
  etaSeconds = null,
  progressPercent = 0,
  phaseLabel
}: ThinkingCardProps) {
  const [isOpen, setIsOpen] = useState(true);

  const activeStep = steps.find((s) => s.status === "running") || steps.find((s) => s.status === "pending");
  const isCompleted = steps.every((s) => s.status === "completed");
  const displayProgress = Math.max(3, Math.min(isCompleted ? 100 : 96, Math.round(progressPercent)));

  return (
    <div className="w-full max-w-2xl mx-auto bg-white border border-gray-200 rounded-2xl shadow-sm overflow-hidden transition-all duration-300">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-6 py-4 hover:bg-gray-50/50 transition-colors duration-250 text-left"
      >
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center space-x-3 min-w-0">
            {isCompleted ? (
              <CheckCircle2 className="w-5 h-5 text-teal-700 flex-shrink-0" />
            ) : (
              <Loader2 className="w-5 h-5 text-teal-700 animate-spin flex-shrink-0" />
            )}
            <span className="font-medium text-gray-900 truncate">
              {isCompleted
                ? "Analysis completed"
                : phaseLabel || activeStep?.label || "Planning tasks"}
            </span>
          </div>
          <div className="flex items-center gap-3 flex-shrink-0">
            <span className="text-sm font-semibold text-teal-700">{displayProgress}%</span>
            {isOpen ? (
              <ChevronUp className="w-4 h-4 text-gray-500" />
            ) : (
              <ChevronDown className="w-4 h-4 text-gray-500" />
            )}
          </div>
        </div>

        <div className="mt-4 h-2 w-full rounded-full bg-gray-100 overflow-hidden">
          <div
            className="h-full rounded-full bg-teal-700 transition-all duration-700 ease-out"
            style={{ width: `${displayProgress}%` }}
          />
        </div>

        <div className="mt-3 flex flex-wrap items-center justify-between gap-2 text-xs font-medium text-gray-500">
          <span>Elapsed {formatDuration(elapsedSeconds)}</span>
          <span>
            {etaSeconds === null || isCompleted
              ? "ETA calculating from live progress"
              : `About ${formatDuration(etaSeconds)} remaining`}
          </span>
        </div>
      </button>

      <AnimatePresence initial={false}>
        {isOpen && (
          <motion.div
            initial={{ height: 0 }}
            animate={{ height: "auto" }}
            exit={{ height: 0 }}
            transition={{ duration: 0.25, ease: "easeInOut" }}
            className="overflow-hidden"
          >
            <div className="px-6 pb-6 pt-2 border-t border-gray-100 flex flex-col space-y-3.5">
              {steps.map((step) => (
                <div key={step.id} className="flex items-center space-x-3 text-sm">
                  {step.status === "completed" && (
                    <CheckCircle2 className="w-4 h-4 text-teal-700" />
                  )}
                  {step.status === "running" && (
                    <Loader2 className="w-4 h-4 text-teal-700 animate-spin" />
                  )}
                  {step.status === "pending" && (
                    <Circle className="w-4 h-4 text-gray-300" />
                  )}
                  {step.status === "failed" && (
                    <div className="w-4 h-4 rounded-full border border-red-500 flex items-center justify-center text-[10px] text-red-500 font-bold">
                      !
                    </div>
                  )}
                  <span
                    className={`font-medium ${
                      step.status === "completed"
                        ? "text-gray-900"
                        : step.status === "running"
                        ? "text-teal-700 font-semibold"
                        : "text-gray-400"
                    }`}
                  >
                    {step.label}
                  </span>
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
