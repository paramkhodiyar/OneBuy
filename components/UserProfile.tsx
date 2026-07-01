"use client";

import React from "react";
import { User, MapPin, CreditCard, Award, Clock } from "lucide-react";

export interface LocationMemory {
  label?: string;
  city?: string;
  state?: string;
  country?: string;
  pincode?: string;
  detectedPincode?: string;
  deliveryPincode?: string;
  latitude?: number;
  longitude?: number;
  accuracy?: number;
  source?: string;
}

export interface UserMemory {
  preferredStore: string;
  preferredPayment: string;
  isPrime: boolean;
  location: LocationMemory | string | null;
  ordersEvening: boolean;
  preferredDeliveryTime: string;
}

interface UserProfileProps {
  memory: UserMemory;
  onChange: (updated: UserMemory) => void;
}

export default function UserProfile({ memory, onChange }: UserProfileProps) {
  const locationLabel =
    typeof memory.location === "string"
      ? memory.location
      : memory.location?.label || "Detecting automatically";
  const locationDetail =
    typeof memory.location === "object" && memory.location?.accuracy
      ? `GPS accuracy about ${Math.round(memory.location.accuracy)} m`
      : "Used for local availability and delivery pricing";
  const deliveryPincode =
    typeof memory.location === "object"
      ? memory.location?.deliveryPincode || memory.location?.pincode || ""
      : "";
  const detectedPincode =
    typeof memory.location === "object" ? memory.location?.detectedPincode || memory.location?.pincode || "" : "";

  const handleChange = (key: Exclude<keyof UserMemory, "location">, value: string | boolean) => {
    onChange({
      ...memory,
      [key]: value
    });
  };

  const handleDeliveryPincodeChange = (value: string) => {
    if (!memory.location || typeof memory.location === "string") return;
    const cleanValue = value.replace(/\D/g, "").slice(0, 6);
    onChange({
      ...memory,
      location: {
        ...memory.location,
        deliveryPincode: cleanValue,
        pincode: cleanValue || memory.location.detectedPincode || memory.location.pincode
      }
    });
  };

  return (
    <div className="w-full max-w-sm bg-white border border-gray-200 rounded-2xl shadow-sm p-6 space-y-6">
      <div className="flex items-center gap-2 pb-4 border-b border-gray-100">
        <User className="w-5 h-5 text-teal-700" />
        <h3 className="font-bold text-gray-900">User Profile Memory</h3>
      </div>

      <div className="space-y-4">
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider flex items-center gap-1.5">
            <MapPin className="w-3.5 h-3.5" />
            Automatic Location
          </label>
          <div className="w-full px-3.5 py-2 border border-gray-200 rounded-xl text-sm bg-gray-50 text-gray-700">
            <div className="font-semibold text-gray-900">{locationLabel}</div>
            <div className="text-xs text-gray-500 mt-0.5">{locationDetail}</div>
          </div>
        </div>

        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider flex items-center gap-1.5">
            Delivery Pincode
          </label>
          <input
            type="text"
            inputMode="numeric"
            value={deliveryPincode}
            onChange={(e) => handleDeliveryPincodeChange(e.target.value)}
            placeholder="Auto detected"
            className="w-full px-3.5 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:border-teal-700 transition-colors"
          />
          {detectedPincode && deliveryPincode && detectedPincode !== deliveryPincode && (
            <p className="text-xs text-gray-500">
              GPS detected {detectedPincode}; using {deliveryPincode} for store serviceability.
            </p>
          )}
        </div>

        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider flex items-center gap-1.5">
            Preferred Store
          </label>
          <select
            value={memory.preferredStore}
            onChange={(e) => handleChange("preferredStore", e.target.value)}
            className="w-full px-3.5 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:border-teal-700 bg-white transition-colors"
          >
            <option value="Blinkit">Blinkit</option>
            <option value="Zepto">Zepto</option>
            <option value="Swiggy Instamart">Swiggy Instamart</option>
            <option value="BigBasket Now">BigBasket Now</option>
            <option value="Amazon Fresh">Amazon Fresh</option>
            <option value="Flipkart Minutes">Flipkart Minutes</option>
          </select>
        </div>

        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider flex items-center gap-1.5">
            <CreditCard className="w-3.5 h-3.5" />
            Preferred Payment
          </label>
          <input
            type="text"
            value={memory.preferredPayment}
            onChange={(e) => handleChange("preferredPayment", e.target.value)}
            className="w-full px-3.5 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:border-teal-700 transition-colors"
          />
        </div>

        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5" />
            Preferred Delivery Time
          </label>
          <input
            type="text"
            value={memory.preferredDeliveryTime}
            onChange={(e) => handleChange("preferredDeliveryTime", e.target.value)}
            className="w-full px-3.5 py-2 border border-gray-200 rounded-xl text-sm focus:outline-none focus:border-teal-700 transition-colors"
          />
        </div>

        <div className="flex items-center justify-between pt-2">
          <span className="text-sm font-medium text-gray-700 flex items-center gap-1.5">
            <Award className="w-4 h-4 text-teal-700" />
            Prime Member / Pass
          </span>
          <button
            onClick={() => handleChange("isPrime", !memory.isPrime)}
            className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
              memory.isPrime ? "bg-teal-700" : "bg-gray-200"
            }`}
          >
            <span
              className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                memory.isPrime ? "translate-x-5" : "translate-x-0"
              }`}
            />
          </button>
        </div>

        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-gray-700 flex items-center gap-1.5">
            <Clock className="w-4 h-4 text-teal-700" />
            Usually Orders in Evening
          </span>
          <button
            onClick={() => handleChange("ordersEvening", !memory.ordersEvening)}
            className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
              memory.ordersEvening ? "bg-teal-700" : "bg-gray-200"
            }`}
          >
            <span
              className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                memory.ordersEvening ? "translate-x-5" : "translate-x-0"
              }`}
            />
          </button>
        </div>
      </div>
    </div>
  );
}
