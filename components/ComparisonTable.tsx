"use client";

import React, { useEffect, useMemo, useState } from "react";
import { Check, ChevronDown, ChevronRight, ExternalLink } from "lucide-react";

export interface ComparisonRow {
  store: string;
  name?: string;
  brand?: string;
  packSize?: string;
  price: number;
  delivery: string;
  coupons: string;
  finalCost: number;
  sourceUrl?: string;
  status?: string;
  note?: string;
  isRecommended?: boolean;
  isExactQueryMatch?: boolean;
  matchScore?: number;
}

interface ComparisonTableProps {
  rows: ComparisonRow[];
  currency?: string;
}

const unavailableLabel = (row: ComparisonRow) =>
  row.status === "not_verified" ? "Not Verified" : "Not Available";

export default function ComparisonTable({ rows, currency = "₹" }: ComparisonTableProps) {
  const groupedRows = useMemo(() => {
    const groups = new Map<string, ComparisonRow[]>();
    rows.forEach((row) => {
      const existing = groups.get(row.store) || [];
      existing.push(row);
      groups.set(row.store, existing);
    });

    return Array.from(groups.entries())
      .map(([store, storeRows]) => {
        const availableRows = storeRows
          .filter((row) => row.finalCost > 0)
          .sort((a, b) => {
            const exactDiff = Number(Boolean(b.isExactQueryMatch)) - Number(Boolean(a.isExactQueryMatch));
            if (exactDiff) return exactDiff;
            const scoreDiff = (b.matchScore || 0) - (a.matchScore || 0);
            if (scoreDiff) return scoreDiff;
            return a.finalCost - b.finalCost;
          });
        const relevantRows = availableRows.some((row) => (row.matchScore || 0) > 0)
          ? availableRows.filter((row) => (row.matchScore || 0) > 0)
          : availableRows;
        const displayRows = relevantRows.length ? relevantRows : availableRows.slice(0, 3);
        const bestRow = relevantRows[0] || availableRows[0] || storeRows[0];
        return { store, rows: [...displayRows, ...storeRows.filter((row) => row.finalCost <= 0)], bestRow };
      })
      .sort((a, b) => {
        const exactDiff = Number(Boolean(b.bestRow?.isExactQueryMatch)) - Number(Boolean(a.bestRow?.isExactQueryMatch));
        if (exactDiff) return exactDiff;
        const scoreDiff = (b.bestRow?.matchScore || 0) - (a.bestRow?.matchScore || 0);
        if (scoreDiff) return scoreDiff;
        const aCost = a.bestRow?.finalCost > 0 ? a.bestRow.finalCost : Number.POSITIVE_INFINITY;
        const bCost = b.bestRow?.finalCost > 0 ? b.bestRow.finalCost : Number.POSITIVE_INFINITY;
        return aCost - bCost;
      });
  }, [rows]);

  const [openStores, setOpenStores] = useState<Record<string, boolean>>(() =>
    Object.fromEntries(groupedRows.slice(0, 2).map((group) => [group.store, true]))
  );

  useEffect(() => {
    setOpenStores(Object.fromEntries(groupedRows.slice(0, 2).map((group) => [group.store, true])));
  }, [groupedRows]);

  const toggleStore = (store: string) => {
    setOpenStores((prev) => ({ ...prev, [store]: !prev[store] }));
  };

  return (
    <div className="w-full max-w-2xl mx-auto bg-white border border-gray-200 rounded-2xl shadow-sm overflow-hidden transition-all duration-300">
      <div className="px-5 py-4 border-b border-gray-100">
        <h3 className="font-bold text-gray-900">Store Comparison</h3>
        <p className="text-xs text-gray-500 mt-1">Open a store to inspect verified matches and nearby alternatives.</p>
      </div>

      <div className="divide-y divide-gray-100">
        {groupedRows.map(({ store, rows: storeRows, bestRow }) => {
          const isOpen = Boolean(openStores[store]);
          return (
            <div key={store}>
              <button
                type="button"
                onClick={() => toggleStore(store)}
                className="w-full px-5 py-4 flex items-center justify-between gap-4 text-left hover:bg-gray-50/60 transition-colors"
              >
                <div className="flex items-start gap-3 min-w-0">
                  {isOpen ? (
                    <ChevronDown className="w-4 h-4 text-gray-400 mt-1 flex-shrink-0" />
                  ) : (
                    <ChevronRight className="w-4 h-4 text-gray-400 mt-1 flex-shrink-0" />
                  )}
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-gray-900">{store}</span>
                      {bestRow?.isRecommended && (
                        <span className="inline-flex items-center gap-0.5 px-2 py-0.5 rounded text-xs font-semibold bg-teal-100 text-teal-800">
                          <Check className="w-3 h-3" />
                          Best
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-gray-500 mt-1 truncate">
                      {bestRow?.finalCost > 0
                        ? bestRow.matchScore
                          ? bestRow.name || "Verified product"
                          : "Verified products found, but no close query match"
                        : bestRow?.note || "No verified match"}
                    </p>
                  </div>
                </div>
                <div className="text-right flex-shrink-0">
                  {bestRow?.finalCost > 0 ? (
                    <>
                      <div className="text-lg font-extrabold text-gray-900">{currency}{bestRow.finalCost}</div>
                      <div className="text-xs text-gray-500">
                        {bestRow.isExactQueryMatch ? "exact match" : bestRow.matchScore ? "closest match" : "no close match"}
                      </div>
                    </>
                  ) : (
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-red-50 text-red-700">
                      {unavailableLabel(bestRow)}
                    </span>
                  )}
                </div>
              </button>

              {isOpen && (
                <div className="px-5 pb-4 space-y-2">
                  {storeRows.slice(0, 8).map((row, idx) => (
                    <div
                      key={`${row.store}-${row.name}-${row.finalCost}-${idx}`}
                      className={`rounded-lg border px-3 py-3 ${
                        row.isRecommended ? "border-teal-200 bg-teal-50/40" : "border-gray-100 bg-gray-50/40"
                      }`}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0">
                          <div className="font-medium text-sm text-gray-900">
                            {row.finalCost > 0 ? row.name || "Matched product" : row.note || "No verified match"}
                          </div>
                          <div className="flex flex-wrap gap-x-3 gap-y-1 text-xs text-gray-500 mt-1">
                            {row.packSize && <span>{row.packSize}</span>}
                            <span>{row.delivery}</span>
                            {row.isExactQueryMatch && <span className="text-teal-700 font-semibold">Exact query match</span>}
                            {typeof row.matchScore === "number" && row.matchScore > 0 && <span>Match {row.matchScore}</span>}
                          </div>
                        </div>
                        <div className="text-right flex-shrink-0">
                          {row.finalCost > 0 ? (
                            <>
                              <div className="font-bold text-gray-900">{currency}{row.finalCost}</div>
                              {row.sourceUrl && (
                                <a
                                  href={row.sourceUrl}
                                  target="_blank"
                                  rel="noreferrer"
                                  className="inline-flex items-center gap-1 text-xs font-semibold text-teal-700 hover:text-teal-800 mt-1"
                                >
                                  Open
                                  <ExternalLink className="w-3 h-3" />
                                </a>
                              )}
                            </>
                          ) : (
                            <span className="text-xs font-semibold text-red-700">{unavailableLabel(row)}</span>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
