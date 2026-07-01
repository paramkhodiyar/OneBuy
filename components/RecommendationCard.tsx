"use client";

import React from "react";
import { ArrowRight, ExternalLink } from "lucide-react";

interface RecommendationCardProps {
  storeName: string;
  price: number;
  deliveryTime: string;
  savings: number;
  productUrl?: string;
  matchedItem?: string;
  currency?: string;
}

export default function RecommendationCard({
  storeName,
  price,
  deliveryTime,
  savings,
  productUrl,
  matchedItem,
  currency = "₹",
}: RecommendationCardProps) {
  return (
    <div className="w-full max-w-2xl mx-auto bg-white border border-gray-200 rounded-2xl shadow-sm hover:shadow-md transition-all duration-300 p-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
      <div className="space-y-2">
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-teal-50 text-teal-700">
          Recommended Choice
        </span>
        <h3 className="text-xl font-bold text-gray-900">Best verified price on {storeName}</h3>
        {matchedItem && (
          <p className="text-sm font-medium text-gray-600 max-w-md">{matchedItem}</p>
        )}
        <div className="flex flex-wrap items-center gap-x-6 gap-y-1 text-sm text-gray-500">
          <div>
            Delivery: <span className="font-semibold text-gray-900">{deliveryTime}</span>
          </div>
          <div>
            Savings: <span className="font-semibold text-teal-700">{currency}{savings}</span>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-4 w-full sm:w-auto justify-between sm:justify-end">
        <div className="text-right">
          <div className="text-3xl font-extrabold text-gray-900">
            {currency}{price}
          </div>
          <div className="text-xs text-gray-400">Listed cost</div>
        </div>
        {productUrl && (
          <a
            href={productUrl}
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-2 px-5 py-3 rounded-xl bg-teal-700 hover:bg-teal-800 text-white font-medium shadow-sm hover:shadow transition-all duration-200"
          >
            <ExternalLink className="w-4 h-4" />
            <span>Open store</span>
            <ArrowRight className="w-4 h-4" />
          </a>
        )}
      </div>
    </div>
  );
}
