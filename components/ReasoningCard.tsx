"use client";

import React from "react";
import { Sparkles, AlertCircle } from "lucide-react";

interface ReasoningCardProps {
  points: string[];
}

export default function ReasoningCard({ points }: ReasoningCardProps) {
  return (
    <div className="w-full max-w-2xl mx-auto bg-white border border-gray-200 rounded-2xl shadow-sm p-6 space-y-4">
      <div className="flex items-center gap-2 text-teal-700">
        <Sparkles className="w-5 h-5" />
        <h3 className="font-bold text-gray-900">Reasoning</h3>
      </div>
      <ul className="space-y-3">
        {points.map((point, index) => (
          <li key={index} className="flex items-start gap-2.5 text-sm text-gray-600 leading-relaxed">
            <AlertCircle className="w-4 h-4 text-teal-700 mt-0.5 flex-shrink-0" />
            <span>{point}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
