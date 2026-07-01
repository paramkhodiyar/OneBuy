"use client";

import React, { useState, useEffect } from "react";
import { Search, ArrowRight, MapPin } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface SearchBarProps {
  onSearch: (query: string) => void;
  isLoading: boolean;
  locationLabel?: string;
  locationStatus?: "locating" | "ready" | "error";
  locationError?: string | null;
  deliveryPincode?: string;
  detectedPincode?: string;
  onDeliveryPincodeChange?: (value: string) => void;
}

const placeholders = [
  "Milk, Eggs and Bread",
  "iPhone 17 Pro",
  "Groceries for Pasta"
];

export default function SearchBar({
  onSearch,
  isLoading,
  locationLabel = "Detecting location",
  locationStatus = "locating",
  locationError = null,
  deliveryPincode = "",
  detectedPincode = "",
  onDeliveryPincodeChange
}: SearchBarProps) {
  const [query, setQuery] = useState("");
  const [placeholderIndex, setPlaceholderIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setPlaceholderIndex((prev) => (prev + 1) % placeholders.length);
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && !isLoading && locationStatus === "ready") {
      onSearch(query.trim());
    }
  };

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-2xl mx-auto space-y-3">
      <div className="relative flex items-center bg-white border border-gray-200 rounded-2xl shadow-sm hover:shadow-md hover:border-gray-300 focus-within:border-teal-700 focus-within:ring-1 focus-within:ring-teal-700 transition-all duration-300 px-4 py-3">
        <Search className="w-5 h-5 text-gray-400 mx-3 flex-shrink-0" />
        <div className="relative flex-grow h-6">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={isLoading}
            className="absolute inset-0 w-full bg-transparent text-gray-900 placeholder-transparent focus:outline-none text-base font-medium"
          />
          {query === "" && (
            <div className="absolute inset-0 pointer-events-none text-gray-400 text-base select-none flex items-center overflow-hidden font-medium">
              <AnimatePresence mode="wait">
                <motion.span
                  key={placeholderIndex}
                  initial={{ y: 10, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  exit={{ y: -10, opacity: 0 }}
                  transition={{ duration: 0.25, ease: "easeInOut" }}
                  className="block"
                >
                  {placeholders[placeholderIndex]}
                </motion.span>
              </AnimatePresence>
            </div>
          )}
        </div>
        <button
          type="submit"
          disabled={!query.trim() || isLoading || locationStatus !== "ready"}
          className="ml-2 p-1.5 rounded-lg text-white bg-teal-700 hover:bg-teal-800 disabled:bg-gray-100 disabled:text-gray-400 transition-all duration-200"
          aria-label="Search prices"
        >
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
      <div className={`flex items-center justify-center gap-2 text-xs font-medium ${
        locationStatus === "error" ? "text-red-600" : "text-gray-500"
      }`}>
        <MapPin className={`w-3.5 h-3.5 ${locationStatus === "ready" ? "text-teal-700" : ""}`} />
        <span>
          {locationStatus === "ready"
            ? `Using ${locationLabel}`
            : locationStatus === "error"
            ? locationError || "Location permission is required for accurate local prices."
            : "Detecting your current delivery location..."}
        </span>
      </div>
      {locationStatus === "ready" && onDeliveryPincodeChange && (
        <div className="mx-auto flex max-w-xs items-center gap-2">
          <label className="text-xs font-semibold text-gray-500 whitespace-nowrap">
            Delivery pincode
          </label>
          <input
            type="text"
            inputMode="numeric"
            value={deliveryPincode}
            onChange={(e) => onDeliveryPincodeChange(e.target.value)}
            placeholder={detectedPincode || "Auto"}
            className="w-24 rounded-lg border border-gray-200 bg-white px-2.5 py-1.5 text-sm font-semibold text-gray-900 focus:border-teal-700 focus:outline-none"
          />
        </div>
      )}
    </form>
  );
}
