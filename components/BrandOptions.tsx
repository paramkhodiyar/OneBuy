"use client";

import React from "react";
import { BadgeCheck, Store, Tag } from "lucide-react";
import { ComparisonRow } from "@/components/ComparisonTable";

export interface BrandOption {
  brand: string;
  packSize?: string;
  bestStore: string;
  bestFinalCost: number;
  delivery: string;
  matchedItem?: string;
  storeCount: number;
  priceRange: {
    min: number;
    max: number;
  };
  stores: ComparisonRow[];
  isRecommendedBrand?: boolean;
}

interface BrandOptionsProps {
  options: BrandOption[];
  currency?: string;
}

export default function BrandOptions({ options, currency = "₹" }: BrandOptionsProps) {
  if (!options.length) return null;

  return (
    <div className="w-full max-w-2xl mx-auto bg-white border border-gray-200 rounded-2xl shadow-sm p-5 space-y-4">
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <Tag className="w-5 h-5 text-teal-700" />
          <h3 className="font-bold text-gray-900">Brand Choices</h3>
        </div>
        <span className="text-xs font-semibold text-gray-500">{options.length} detected</span>
      </div>

      <div className="divide-y divide-gray-100">
        {options.map((option) => (
          <div
            key={`${option.brand}-${option.packSize}-${option.bestStore}-${option.bestFinalCost}`}
            className={`py-4 first:pt-1 last:pb-1 space-y-3 ${option.isRecommendedBrand ? "bg-teal-50/30 -mx-3 px-3 rounded-lg" : ""}`}
          >
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <h4 className="font-semibold text-gray-900 truncate">{option.brand}</h4>
                  {option.isRecommendedBrand && (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-semibold bg-teal-100 text-teal-800">
                      <BadgeCheck className="w-3 h-3" />
                      Best value
                    </span>
                  )}
                </div>
                <p className="text-xs text-gray-500 mt-0.5">
                  {option.packSize || option.matchedItem || "Detected variant"}
                </p>
              </div>
              <div className="text-right flex-shrink-0">
                <div className="text-lg font-extrabold text-gray-900">
                  {currency}{option.bestFinalCost}
                </div>
                <div className="text-xs text-gray-500">{option.delivery}</div>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-gray-500">
              <span className="inline-flex items-center gap-1">
                <Store className="w-3.5 h-3.5 text-teal-700" />
                Best at {option.bestStore}
              </span>
              <span>{option.storeCount} store{option.storeCount === 1 ? "" : "s"} found</span>
              <span>
                Range {currency}{option.priceRange.min} to {currency}{option.priceRange.max}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
