"use client";

import React, { useEffect, useState } from "react";
import { 
  RotateCcw, 
  Bookmark, 
  Settings, 
  ChevronRight, 
  TrendingUp,
  Shield,
  HelpCircle,
  AlertCircle
} from "lucide-react";
import SearchBar from "@/components/SearchBar";
import ThinkingCard, { TaskStep } from "@/components/ThinkingCard";
import RecommendationCard from "@/components/RecommendationCard";
import ComparisonTable, { ComparisonRow } from "@/components/ComparisonTable";
import BrandOptions, { BrandOption } from "@/components/BrandOptions";
import ReasoningCard from "@/components/ReasoningCard";
import UserProfile, { LocationMemory, UserMemory } from "@/components/UserProfile";

const API_BASE = "http://localhost:8000";

type LocationStatus = "locating" | "ready" | "error";
type BrandStrategy = {
  mode?: string;
  brandSpecified?: boolean;
  detectedBrand?: string;
  summary?: string;
};

type ProgressState = {
  elapsedSeconds: number;
  etaSeconds: number | null;
  progressPercent: number;
  phaseLabel: string;
};

const initialSteps = (): TaskStep[] => [
  { id: "1", label: "Decomposing query", status: "pending" },
  { id: "2", label: "Searching Blinkit", status: "pending" },
  { id: "3", label: "Searching Zepto", status: "pending" },
  { id: "4", label: "Searching Instamart", status: "pending" },
  { id: "5", label: "Searching BigBasket Now", status: "pending" },
  { id: "6", label: "Searching Flipkart Minutes", status: "pending" },
  { id: "7", label: "Searching Amazon Fresh", status: "pending" },
  { id: "8", label: "Applying Coupons", status: "pending" },
  { id: "9", label: "Optimizing Delivery Fees", status: "pending" },
  { id: "10", label: "Generating Recommendation", status: "pending" }
];

const initialProgress = (): ProgressState => ({
  elapsedSeconds: 0,
  etaSeconds: null,
  progressPercent: 0,
  phaseLabel: "Starting search"
});

const wait = (ms: number) => new Promise((resolve) => window.setTimeout(resolve, ms));

const mergeResolvedLocation = (
  previousLocation: UserMemory["location"],
  resolvedLocation: LocationMemory,
  deliveryPincodeOverride = ""
): LocationMemory => {
  const previous =
    previousLocation && typeof previousLocation === "object" ? previousLocation : null;
  const validOverride = /^\d{6}$/.test(deliveryPincodeOverride) ? deliveryPincodeOverride : "";
  const previousDeliveryPincode =
    previous?.deliveryPincode && /^\d{6}$/.test(previous.deliveryPincode)
      ? previous.deliveryPincode
      : "";
  const deliveryPincode = validOverride || previousDeliveryPincode;
  return {
    ...resolvedLocation,
    detectedPincode: resolvedLocation.detectedPincode || resolvedLocation.pincode,
    deliveryPincode,
    pincode: deliveryPincode || resolvedLocation.pincode
  };
};

const getBrowserLocation = () =>
  new Promise<LocationMemory>((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error("Your browser does not support automatic location."));
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        resolve({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          accuracy: position.coords.accuracy,
          source: "browser"
        });
      },
      () => reject(new Error("Location permission is required for accurate local prices.")),
      {
        enableHighAccuracy: true,
        timeout: 12000,
        maximumAge: 60000
      }
    );
  });

const resolveLocation = async (location: LocationMemory) => {
  const res = await fetch(`${API_BASE}/api/location/resolve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ location })
  });

  if (!res.ok) {
    throw new Error("Could not resolve current location.");
  }

  return (await res.json()) as LocationMemory;
};

export default function Home() {
  const [searchTriggered, setSearchTriggered] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [query, setQuery] = useState("");
  const [showSettings, setShowSettings] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [locationStatus, setLocationStatus] = useState<LocationStatus>("locating");
  const [locationError, setLocationError] = useState<string | null>(null);
  const [deliveryPincodeOverride, setDeliveryPincodeOverride] = useState("");

  const [memory, setMemory] = useState<UserMemory>({
    preferredStore: "Blinkit",
    preferredPayment: "UPI",
    isPrime: true,
    location: null,
    ordersEvening: true,
    preferredDeliveryTime: "Immediate"
  });

  const [steps, setSteps] = useState<TaskStep[]>(initialSteps);
  const [progress, setProgress] = useState<ProgressState>(initialProgress);

  const [recommendation, setRecommendation] = useState({
    storeName: "",
    price: 0,
    deliveryTime: "",
    savings: 0,
    productUrl: "",
    matchedItem: ""
  });

  const [comparisons, setComparisons] = useState<ComparisonRow[]>([]);
  const [brandOptions, setBrandOptions] = useState<BrandOption[]>([]);
  const [brandStrategy, setBrandStrategy] = useState<BrandStrategy>({});
  const [reasoning, setReasoning] = useState<string[]>([]);
  const [recentSearches, setRecentSearches] = useState<string[]>([
    "iPhone 17 Pro",
    "Groceries for Pasta",
    "Milk, Eggs and Bread"
  ]);
  const savedLists = [
    { id: "1", name: "Weekly Groceries", items: ["Milk", "Eggs", "Bread", "Butter"] },
    { id: "2", name: "Pasta Dinner", items: ["Pasta", "Tomato Sauce", "Parmesan", "Basil"] }
  ];

  const hasOnlyUnverifiedRows =
    comparisons.length > 0 && comparisons.every((row) => row.status === "not_verified");

  useEffect(() => {
    const savedDeliveryPincode = window.localStorage.getItem("onebuy.deliveryPincode") || "";
    if (/^\d{6}$/.test(savedDeliveryPincode)) {
      setDeliveryPincodeOverride(savedDeliveryPincode);
    }

    if (!navigator.geolocation) {
      setLocationStatus("error");
      setLocationError("Your browser does not support automatic location.");
      return;
    }

    let cancelled = false;
    const watchId = navigator.geolocation.watchPosition(
      async (position) => {
        const browserLocation: LocationMemory = {
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          accuracy: position.coords.accuracy,
          source: "browser"
        };

        setLocationStatus("locating");
        setLocationError(null);
        try {
          const resolved = await resolveLocation(browserLocation);
          if (cancelled) return;
          setMemory((prev) => ({
            ...prev,
            location: mergeResolvedLocation(prev.location, resolved, savedDeliveryPincode)
          }));
          setLocationStatus("ready");
        } catch {
          if (cancelled) return;
          setMemory((prev) => ({ ...prev, location: browserLocation }));
          setLocationStatus("ready");
        }
      },
      () => {
        if (cancelled) return;
        setLocationStatus("error");
        setLocationError("Allow location access so OneBuy can fetch accurate prices for your delivery area.");
      },
      {
        enableHighAccuracy: true,
        timeout: 12000,
        maximumAge: 60000
      }
    );

    return () => {
      cancelled = true;
      navigator.geolocation.clearWatch(watchId);
    };
  }, []);

  useEffect(() => {
    if (deliveryPincodeOverride && !/^\d{6}$/.test(deliveryPincodeOverride)) return;
    if (deliveryPincodeOverride) {
      window.localStorage.setItem("onebuy.deliveryPincode", deliveryPincodeOverride);
    } else {
      window.localStorage.removeItem("onebuy.deliveryPincode");
    }
    setMemory((prev) => {
      if (!prev.location || typeof prev.location === "string") return prev;
      return {
        ...prev,
        location: {
          ...prev.location,
          deliveryPincode: deliveryPincodeOverride,
          pincode: deliveryPincodeOverride || prev.location.detectedPincode || prev.location.pincode
        }
      };
    });
  }, [deliveryPincodeOverride]);

  useEffect(() => {
    const profilePincode =
      memory.location && typeof memory.location === "object" ? memory.location.deliveryPincode || "" : "";
    if (/^\d{6}$/.test(profilePincode) && profilePincode !== deliveryPincodeOverride) {
      setDeliveryPincodeOverride(profilePincode);
    }
  }, [memory.location, deliveryPincodeOverride]);

  const ensureResolvedLocation = async () => {
    if (memory.location && typeof memory.location === "object" && memory.location.latitude && memory.location.longitude) {
      return memory.location;
    }

    setLocationStatus("locating");
    setLocationError(null);
    const browserLocation = await getBrowserLocation();
    const resolved = await resolveLocation(browserLocation);
    const mergedLocation = mergeResolvedLocation(memory.location, resolved, deliveryPincodeOverride);
    setMemory((prev) => ({ ...prev, location: mergeResolvedLocation(prev.location, resolved, deliveryPincodeOverride) }));
    setLocationStatus("ready");
    return mergedLocation;
  };

  const handleSearch = async (searchQuery: string) => {
    setError(null);
    setIsLoading(true);
    setSearchTriggered(true);
    setQuery(searchQuery);
    setSteps(initialSteps());
    setProgress(initialProgress());
      setRecommendation({ storeName: "", price: 0, deliveryTime: "", savings: 0, productUrl: "", matchedItem: "" });
    setComparisons([]);
    setBrandOptions([]);
    setBrandStrategy({});
    setReasoning([]);

    if (!recentSearches.includes(searchQuery)) {
      setRecentSearches((prev) => [searchQuery, ...prev.slice(0, 4)]);
    }

    try {
      const resolvedLocation = await ensureResolvedLocation();

      const requestMemory = { ...memory, location: resolvedLocation };
      const startRes = await fetch(`${API_BASE}/api/search/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: searchQuery, memory: requestMemory })
      });

      if (!startRes.ok) {
        throw new Error("Backend server error");
      }

      const { jobId } = await startRes.json();
      let data = null;

      while (true) {
        const statusRes = await fetch(`${API_BASE}/api/search/status/${jobId}`);
        if (!statusRes.ok) {
          throw new Error("Backend server error");
        }

        const statusData = await statusRes.json();
        setSteps(statusData.steps || []);
        if (statusData.progress) {
          setProgress({
            elapsedSeconds: statusData.progress.elapsedSeconds || 0,
            etaSeconds: statusData.progress.etaSeconds ?? null,
            progressPercent: statusData.progress.progressPercent || 0,
            phaseLabel: statusData.progress.phaseLabel || "Checking stores"
          });
        }

        if (statusData.status === "failed") {
          throw new Error(statusData.error || "Backend server error");
        }

        if (statusData.status === "complete") {
          data = statusData.result;
          break;
        }

        await wait(1000);
      }

      if (!data) {
        throw new Error("Backend server error");
      }

      setSteps(data.steps || []);
      setRecommendation(data.recommendation);
      setComparisons(data.comparisons);
      setBrandOptions(data.brandOptions || []);
      setBrandStrategy(data.brandStrategy || {});
      setReasoning(data.reasoning);
      if (data.location) {
        setMemory((prev) => ({ ...prev, location: mergeResolvedLocation(prev.location, data.location, deliveryPincodeOverride) }));
      }
      setIsLoading(false);
    } catch (err) {
      const message = err instanceof Error ? err.message : "";
      setError(
        message.includes("Location")
          ? message
          : "Failed to connect to backend server. Make sure the FastAPI service is running on port 8000."
      );
      setRecommendation({ storeName: "None", price: 0, deliveryTime: "", savings: 0, productUrl: "", matchedItem: "" });
      setBrandOptions([]);
      setBrandStrategy({});
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#FAFAF8] text-[#111111] font-sans antialiased selection:bg-teal-50 selection:text-teal-900">
      <header className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between border-b border-gray-200/50">
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 rounded-lg bg-teal-700 flex items-center justify-center text-white font-bold text-lg">
            O
          </div>
          <span className="text-xl font-bold tracking-tight">OneBuy</span>
        </div>
        <div className="flex items-center space-x-4">
          <button 
            onClick={() => setShowSettings(!showSettings)}
            className="p-2 text-gray-500 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <Settings className="w-5 h-5" />
          </button>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-12">
        {!searchTriggered ? (
          <div className="max-w-4xl mx-auto text-center space-y-12 py-16">
            <div className="space-y-4">
              <h1 className="text-5xl md:text-6xl font-extrabold tracking-tight text-gray-900">
                Find the smartest place to buy anything.
              </h1>
              <p className="text-lg text-gray-500 max-w-2xl mx-auto font-medium leading-relaxed">
                One search. Every store. The smartest purchase. OneBuy compares platforms, reasons about prices, delivery fees, and preferences.
              </p>
            </div>

            <SearchBar
              onSearch={handleSearch}
              isLoading={isLoading}
              locationLabel={
                typeof memory.location === "string"
                  ? memory.location
                  : memory.location?.label || "your current location"
              }
              locationStatus={locationStatus}
              locationError={locationError}
              deliveryPincode={
                deliveryPincodeOverride ||
                (typeof memory.location === "object" ? memory.location?.deliveryPincode || memory.location?.pincode || "" : "")
              }
              detectedPincode={
                typeof memory.location === "object" ? memory.location?.detectedPincode || memory.location?.pincode || "" : ""
              }
              onDeliveryPincodeChange={(value) => {
                const cleanValue = value.replace(/\D/g, "").slice(0, 6);
                setDeliveryPincodeOverride(cleanValue);
              }}
            />

            <div className="grid md:grid-cols-2 gap-8 max-w-2xl mx-auto pt-6 text-left">
              <div className="bg-white border border-gray-200 rounded-2xl p-6 space-y-4">
                <h3 className="font-semibold text-gray-900 flex items-center gap-2">
                  <RotateCcw className="w-4 h-4 text-teal-700" />
                  Recent Searches
                </h3>
                <div className="divide-y divide-gray-100">
                  {recentSearches.map((s, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleSearch(s)}
                      className="w-full text-left py-2.5 text-sm text-gray-600 hover:text-teal-700 flex items-center justify-between group transition-colors"
                    >
                      <span>{s}</span>
                      <ChevronRight className="w-4 h-4 text-gray-300 group-hover:text-teal-700 group-hover:translate-x-0.5 transition-all" />
                    </button>
                  ))}
                </div>
              </div>

              <div className="bg-white border border-gray-200 rounded-2xl p-6 space-y-4">
                <h3 className="font-semibold text-gray-900 flex items-center gap-2">
                  <Bookmark className="w-4 h-4 text-teal-700" />
                  Saved Lists
                </h3>
                <div className="divide-y divide-gray-100">
                  {savedLists.map((list) => (
                    <button
                      key={list.id}
                      onClick={() => handleSearch(list.name)}
                      className="w-full text-left py-2.5 text-sm text-gray-600 hover:text-teal-700 flex items-center justify-between group transition-colors"
                    >
                      <div className="flex flex-col">
                        <span className="font-medium text-gray-900 group-hover:text-teal-700">{list.name}</span>
                        <span className="text-xs text-gray-400">{list.items.join(", ")}</span>
                      </div>
                      <ChevronRight className="w-4 h-4 text-gray-300 group-hover:text-teal-700 group-hover:translate-x-0.5 transition-all" />
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="grid lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2 space-y-8">
              <div className="flex items-center justify-between pb-4 border-b border-gray-200">
                <div className="space-y-1">
                  <h2 className="text-2xl font-bold tracking-tight text-gray-900">Search Results</h2>
                  <p className="text-sm text-gray-500">Query: &quot;{query}&quot;</p>
                </div>
                <button
                  onClick={() => setSearchTriggered(false)}
                  className="px-4 py-2 text-sm font-semibold border border-gray-200 rounded-xl hover:bg-gray-50 bg-white transition-all duration-200"
                >
                  New Search
                </button>
              </div>

              {isLoading && (
                <ThinkingCard
                  steps={steps}
                  elapsedSeconds={progress.elapsedSeconds}
                  etaSeconds={progress.etaSeconds}
                  progressPercent={progress.progressPercent}
                  phaseLabel={progress.phaseLabel}
                />
              )}

              {!isLoading && (
                error ? (
                  <div className="w-full max-w-2xl mx-auto bg-white border border-gray-200 rounded-2xl p-8 text-center space-y-4 shadow-sm">
                    <div className="w-12 h-12 rounded-full bg-red-50 flex items-center justify-center mx-auto text-red-600">
                      <AlertCircle className="w-6 h-6" />
                    </div>
                    <h3 className="text-lg font-bold text-gray-900">Connection Error</h3>
                    <p className="text-sm text-gray-500 max-w-sm mx-auto">
                      {error}
                    </p>
                  </div>
                ) : recommendation.storeName && recommendation.storeName !== "None" ? (
                  <>
                    <RecommendationCard
                      storeName={recommendation.storeName}
                      price={recommendation.price}
                      deliveryTime={recommendation.deliveryTime}
                      savings={recommendation.savings}
                      productUrl={recommendation.productUrl}
                      matchedItem={recommendation.matchedItem}
                    />

                    <ReasoningCard points={reasoning} />

                    {!brandStrategy.brandSpecified && <BrandOptions options={brandOptions} />}

                    <ComparisonTable rows={comparisons} />
                  </>
                ) : recommendation.storeName === "None" ? (
                  <div className="space-y-8">
                    <div className="w-full max-w-2xl mx-auto bg-white border border-gray-200 rounded-2xl p-8 text-center space-y-4 shadow-sm">
                      <div className="w-12 h-12 rounded-full bg-gray-50 flex items-center justify-center mx-auto text-gray-400">
                        <AlertCircle className="w-6 h-6" />
                      </div>
                      <h3 className="text-lg font-bold text-gray-900">
                        {hasOnlyUnverifiedRows ? "Prices Could Not Be Verified" : "No Serviceable Matches Found"}
                      </h3>
                      <p className="text-sm text-gray-500 max-w-sm mx-auto">
                        {hasOnlyUnverifiedRows
                          ? `OneBuy could not extract reliable live prices for "${query}" from the scanned stores.`
                          : `None of the scanned stores returned active product matches for "${query}" in this location.`}
                      </p>
                    </div>

                    {!brandStrategy.brandSpecified && <BrandOptions options={brandOptions} />}

                    <ComparisonTable rows={comparisons} />
                  </div>
                ) : null
              )}
            </div>

            <div className="space-y-8">
              <UserProfile memory={memory} onChange={setMemory} />
            </div>
          </div>
        )}
      </main>

      {showSettings && (
        <div className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white border border-gray-200 rounded-2xl max-w-md w-full p-6 space-y-4 shadow-xl">
            <h3 className="text-lg font-bold text-gray-900">Settings</h3>
            <p className="text-sm text-gray-500">
              Configure endpoints or options for your local environment.
            </p>
            <div className="space-y-3">
              <div className="space-y-1">
                <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider">FastAPI Endpoint</label>
                <input
                  type="text"
                  defaultValue="http://localhost:8000"
                  disabled
                  className="w-full px-3 py-2 border border-gray-200 rounded-xl text-sm bg-gray-50 text-gray-400 cursor-not-allowed"
                />
              </div>
            </div>
            <div className="flex justify-end pt-4">
              <button
                onClick={() => setShowSettings(false)}
                className="px-4 py-2 bg-teal-700 hover:bg-teal-800 text-white rounded-xl text-sm font-semibold transition-colors"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}

      <footer className="border-t border-gray-200/50 bg-gray-50/30 mt-24">
        <div className="max-w-7xl mx-auto px-6 py-12 grid grid-cols-2 md:grid-cols-4 gap-8">
          <div className="col-span-2 space-y-4">
            <span className="text-lg font-bold text-gray-900">OneBuy</span>
            <p className="text-sm text-gray-500 max-w-sm">
              The smartest way to search and buy across all online platforms. Zero branding fluff, just the best deals instantly.
            </p>
          </div>
          <div className="space-y-3">
            <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Features</span>
            <div className="flex flex-col space-y-2">
              <span className="text-sm text-gray-600 flex items-center gap-1.5"><Shield className="w-3.5 h-3.5 text-teal-700" /> Store redirects</span>
              <span className="text-sm text-gray-600 flex items-center gap-1.5"><TrendingUp className="w-3.5 h-3.5 text-teal-700" /> Best rate optimization</span>
            </div>
          </div>
          <div className="space-y-3">
            <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Support</span>
            <div className="flex flex-col space-y-2">
              <span className="text-sm text-gray-600 flex items-center gap-1.5"><HelpCircle className="w-3.5 h-3.5 text-teal-700" /> Help desk</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
