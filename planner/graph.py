from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List
import re
from langgraph.graph import StateGraph, END
from planner.state import AgentState
from tools import (
    BlinkitTool,
    ZeptoTool,
    InstamartTool,
    AmazonTool,
    BigBasketTool,
    FlipkartTool,
    UberTool,
    RapidoTool,
    CommerceItem
)

GENERIC_PRODUCT_WORDS = {
    "a2", "about", "and", "atta", "baby", "basmati", "bread", "brown", "butter",
    "cheese", "classic", "curd", "daily", "eggs", "extra", "fresh", "full",
    "ghee", "gold", "gram", "green", "hair", "kg", "lite", "milk", "ml",
    "oil", "organic", "pack", "paneer", "pcs", "powder", "premium", "pure",
    "rice", "salt", "shampoo", "soap", "sugar", "tea", "the", "toned",
    "ultra", "white", "whole", "wheat", "yogurt",
}

STOP_QUERY_WORDS = {
    "a", "an", "and", "buy", "for", "fresh", "of", "pack", "packet", "the",
}

MILK_TYPE_WORDS = {
    "toned", "double", "full", "cream", "skimmed", "slim", "trim", "cow",
    "buffalo", "lactose", "free", "taaza", "tetra", "pouch", "organic",
}


def _clean_text(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip()


def _tokens(value: Any) -> List[str]:
    return [token for token in _clean_text(value).split() if token and token not in STOP_QUERY_WORDS]


def _quantity_from_text(value: Any) -> Dict[str, Any] | None:
    text = str(value or "").lower()
    match = re.search(r"\b(\d+(?:\.\d+)?)\s*(ml|l|litre|liter|g|gm|kg)\b", text)
    if not match:
        return None
    amount = float(match.group(1))
    unit = match.group(2)
    if unit in {"l", "litre", "liter"}:
        amount *= 1000
        unit = "ml"
    elif unit == "kg":
        amount *= 1000
        unit = "g"
    elif unit == "gm":
        unit = "g"
    return {"amount": amount, "unit": unit, "raw": match.group(0)}


def _query_intent(query: str, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    query_clean = _clean_text(query)
    quantity = _quantity_from_text(query)
    brand = _query_brand_match(query, rows)
    query_tokens = _tokens(query)
    variant_tokens = [
        token for token in query_tokens
        if token not in _tokens(brand) and token not in {"ml", "ltr", "liter", "litre", "kg", "gm", "g"}
    ]
    product_tokens = [
        token for token in variant_tokens
        if token in GENERIC_PRODUCT_WORDS or token in MILK_TYPE_WORDS
    ]
    is_specific = bool(brand or quantity or len(query_tokens) >= 3)
    return {
        "query": query,
        "queryClean": query_clean,
        "brand": brand,
        "quantity": quantity,
        "variantTokens": variant_tokens,
        "productTokens": product_tokens,
        "isSpecific": is_specific,
    }


def _row_text(row: Dict[str, Any]) -> str:
    return _clean_text(" ".join([
        str(row.get("name") or ""),
        str(row.get("brand") or ""),
        str(row.get("packSize") or ""),
    ]))


def _score_row_against_intent(row: Dict[str, Any], intent: Dict[str, Any]) -> Dict[str, Any]:
    row_text = _row_text(row)
    score = 0
    reasons = []

    brand = intent.get("brand") or ""
    if brand:
        brand_tokens = _tokens(brand)
        if all(token in row_text for token in brand_tokens):
            score += 45
            reasons.append("brand")
        else:
            return {"score": 0, "reasons": reasons, "exact": False, "quantityMatch": False}

    product_tokens = intent.get("productTokens") or []
    matched_product_tokens = [token for token in product_tokens if token in row_text]
    if product_tokens:
        score += int(25 * (len(matched_product_tokens) / len(product_tokens)))
        reasons.extend(matched_product_tokens)

    quantity = intent.get("quantity")
    row_quantity = _quantity_from_text(" ".join([str(row.get("packSize") or ""), str(row.get("name") or "")]))
    quantity_match = False
    if quantity:
        if row_quantity and row_quantity["unit"] == quantity["unit"]:
            diff_ratio = abs(row_quantity["amount"] - quantity["amount"]) / quantity["amount"]
            if diff_ratio <= 0.02:
                score += 40
                quantity_match = True
                reasons.append("quantity")
            elif diff_ratio <= 0.10:
                score += 15
                reasons.append("near quantity")
            else:
                score -= 35
        else:
            score -= 25

    query_tokens = [
        token for token in intent.get("variantTokens", [])
        if token not in {"ml", "l", "litre", "liter", "g", "gm", "kg"}
    ]
    matched_tokens = [token for token in query_tokens if token in row_text]
    if query_tokens:
        score += int(15 * (len(matched_tokens) / len(query_tokens)))

    exact = bool(
        (not brand or "brand" in reasons)
        and (not quantity or quantity_match)
        and (not product_tokens or len(matched_product_tokens) == len(product_tokens))
    )
    return {"score": max(score, 0), "reasons": reasons, "exact": exact, "quantityMatch": quantity_match}


def _annotate_match_scores(rows: List[Dict[str, Any]], intent: Dict[str, Any]) -> List[Dict[str, Any]]:
    annotated = []
    for row in rows:
        scored = dict(row)
        match = _score_row_against_intent(row, intent)
        scored["matchScore"] = match["score"]
        scored["matchReasons"] = match["reasons"]
        scored["isExactQueryMatch"] = match["exact"]
        scored["quantityMatch"] = match["quantityMatch"]
        annotated.append(scored)
    return annotated


def _brand_from_row(row: Dict[str, Any]) -> str:
    parsed_brand = str(row.get("brand") or "").strip()
    if parsed_brand:
        return parsed_brand

    name_tokens = _clean_text(row.get("name")).split()
    brand_tokens = []
    for token in name_tokens:
        if token in GENERIC_PRODUCT_WORDS or token.isdigit():
            if brand_tokens:
                break
            continue
        brand_tokens.append(token)
        if len(brand_tokens) == 2:
            break

    return " ".join(brand_tokens).title() if brand_tokens else "Unspecified Brand"


def _brand_key(value: str) -> str:
    return _clean_text(value)


def _pack_key(row: Dict[str, Any]) -> str:
    pack_size = str(row.get("packSize") or "").strip()
    if pack_size:
        return _clean_text(pack_size)

    name = str(row.get("name") or "")
    match = re.search(r"\b\d+(?:\.\d+)?\s?(?:ml|l|litre|liter|g|gm|kg|pcs|pc|pieces)\b", name, re.I)
    return _clean_text(match.group(0)) if match else ""


def _query_brand_match(query: str, rows: List[Dict[str, Any]]) -> str:
    query_clean = f" {_clean_text(query)} "
    brands = sorted(
        {_brand_from_row(row) for row in rows if _brand_from_row(row) != "Unspecified Brand"},
        key=len,
        reverse=True,
    )
    for brand in brands:
        brand_clean = _brand_key(brand)
        if brand_clean and f" {brand_clean} " in query_clean:
            return brand
    return ""


def _build_brand_options(rows: List[Dict[str, Any]], best: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
    groups: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        brand = _brand_from_row(row)
        pack = str(row.get("packSize") or "").strip()
        key = f"{_brand_key(brand)}::{_pack_key(row)}"
        if key not in groups:
            groups[key] = {"brand": brand, "packSize": pack, "items": []}
        groups[key]["items"].append(row)

    options = []
    for group in groups.values():
        sorted_items = sorted(group["items"], key=lambda item: item["finalCost"])
        best_item = sorted_items[0]
        prices = [item["finalCost"] for item in sorted_items]
        options.append({
            "brand": group["brand"],
            "packSize": group["packSize"],
            "bestStore": best_item["store"],
            "bestFinalCost": best_item["finalCost"],
            "delivery": best_item.get("delivery", "N/A"),
            "matchedItem": best_item.get("name", ""),
            "priceRange": {
                "min": min(prices),
                "max": max(prices),
            },
            "storeCount": len({item["store"] for item in sorted_items}),
            "stores": sorted_items[:4],
            "isRecommendedBrand": bool(
                best
                and best_item.get("store") == best.get("store")
                and best_item.get("finalCost") == best.get("finalCost")
            ),
        })

    return sorted(options, key=lambda option: option["bestFinalCost"])[:8]


def _emit_progress(state: Dict[str, Any], steps: List[Dict[str, Any]], results: List[Dict[str, Any]] | None = None) -> None:
    callback = state.get("progress_callback")
    if callback:
        callback({
            "steps": steps,
            "results": results or state.get("results", []),
        })


def decompose_node(state: AgentState) -> Dict[str, Any]:
    query_lower = state["query"].lower()
    selected = []
    
    if "cab" in query_lower or "airport" in query_lower or "ride" in query_lower:
        selected = ["uber", "rapido"]
    else:
        selected = ["blinkit", "zepto", "instamart", "bigbasket", "flipkart", "amazon"]
        
    steps = [
        {"id": "1", "label": "Decomposing query", "status": "completed"},
        {"id": "2", "label": "Searching Blinkit", "status": "pending" if "blinkit" in selected else "failed"},
        {"id": "3", "label": "Searching Zepto", "status": "pending" if "zepto" in selected else "failed"},
        {"id": "4", "label": "Searching Instamart", "status": "pending" if "instamart" in selected else "failed"},
        {"id": "5", "label": "Searching BigBasket Now", "status": "pending" if "bigbasket" in selected else "failed"},
        {"id": "6", "label": "Searching Flipkart Minutes", "status": "pending" if "flipkart" in selected else "failed"},
        {"id": "7", "label": "Searching Amazon Fresh", "status": "pending" if "amazon" in selected else "failed"},
        {"id": "8", "label": "Applying Coupons", "status": "pending"},
        {"id": "9", "label": "Optimizing Delivery Fees", "status": "pending"},
        {"id": "10", "label": "Generating Recommendation", "status": "pending"}
    ]
    
    _emit_progress(state, steps)
    return {"selected_tools": selected, "steps": steps}

def execute_node(state: AgentState) -> Dict[str, Any]:
    query = state["query"]
    selected = state["selected_tools"]
    location = state["user_profile"].get("location")
    results = []
    steps = list(state["steps"])
    display_names = {
        "blinkit": "Blinkit",
        "zepto": "Zepto",
        "instamart": "Swiggy Instamart",
        "bigbasket": "BigBasket Now",
        "flipkart": "Flipkart Minutes",
        "amazon": "Amazon Fresh",
        "uber": "Uber",
        "rapido": "Rapido"
    }
    
    tool_map = {
        "blinkit": (BlinkitTool(), "2"),
        "zepto": (ZeptoTool(), "3"),
        "instamart": (InstamartTool(), "4"),
        "bigbasket": (BigBasketTool(), "5"),
        "flipkart": (FlipkartTool(), "6"),
        "amazon": (AmazonTool(), "7"),
        "uber": (UberTool(), "2"),
        "rapido": (RapidoTool(), "3")
    }

    if isinstance(location, dict) and not any(name in selected for name in ["uber", "rapido"]):
        country = (location.get("country") or "").strip().lower()
        pincode = str(location.get("pincode") or "")
        if (country and country != "india") or not re.match(r"^\d{6}$", pincode):
            for tool_name in selected:
                results.append({
                    "store": display_names.get(tool_name, tool_name.capitalize()),
                    "price": -1,
                    "delivery": "-",
                    "coupons": "-",
                    "finalCost": -1,
                    "status": "unavailable",
                    "note": "Automatic location is outside the currently supported quick-commerce delivery areas."
                })
            for step in steps:
                if step["id"] != "1":
                    step["status"] = "failed"
            _emit_progress(state, steps, results)
            return {"results": results, "steps": steps}
    
    runnable_tools = [
        (tool_name, tool_map[tool_name][0], tool_map[tool_name][1])
        for tool_name in selected
        if tool_name in tool_map
    ]

    for _, _, step_id in runnable_tools:
        for step in steps:
            if step["id"] == step_id:
                step["status"] = "running"
    _emit_progress(state, steps, results)

    with ThreadPoolExecutor(max_workers=min(len(runnable_tools), 6) or 1) as executor:
        future_map = {
            executor.submit(tool_inst.search, query, location): (tool_name, step_id)
            for tool_name, tool_inst, step_id in runnable_tools
        }

        for future in as_completed(future_map):
            _, step_id = future_map[future]
            try:
                items = future.result()
                if items:
                    for item in items:
                        results.append(item.to_dict())
                else:
                    results.append({
                        "store": display_names.get(future_map[future][0], future_map[future][0].capitalize()),
                        "price": -1,
                        "delivery": "-",
                        "coupons": "-",
                        "finalCost": -1,
                        "status": "not_verified",
                        "note": "The store page did not return parseable products in this automated check."
                    })
                status = "completed"
            except Exception:
                results.append({
                    "store": display_names.get(future_map[future][0], future_map[future][0].capitalize()),
                    "price": -1,
                    "delivery": "-",
                    "coupons": "-",
                    "finalCost": -1,
                    "status": "not_verified",
                    "note": "The automated store check failed before prices could be verified."
                })
                status = "failed"

            for step in steps:
                if step["id"] == step_id:
                    step["status"] = status
            _emit_progress(state, steps, results)
                        
    return {"results": results, "steps": steps}

def aggregate_node(state: AgentState) -> Dict[str, Any]:
    steps = list(state["steps"])
    for step in steps:
        if step["id"] in ["8", "9"] and step.get("status") != "failed":
            step["status"] = "completed"
    _emit_progress(state, steps)
    return {"steps": steps}

def reason_node(state: AgentState) -> Dict[str, Any]:
    results = list(state["results"])
    profile = state["user_profile"]
    selected = state["selected_tools"]
    steps = list(state["steps"])
    
    for step in steps:
        if step["id"] == "10":
            step["status"] = "running"
    _emit_progress(state, steps, results)
            
    valid_results = [r for r in results if r.get("price", 0) > 0]
    
    display_names = {
        "blinkit": "Blinkit",
        "zepto": "Zepto",
        "instamart": "Swiggy Instamart",
        "bigbasket": "BigBasket Now",
        "flipkart": "Flipkart Minutes",
        "amazon": "Amazon Fresh",
        "uber": "Uber",
        "rapido": "Rapido"
    }
    
    scanned_stores = set(r["store"].lower() for r in results)
    for tool_name in selected:
        display_name = display_names.get(tool_name, tool_name.capitalize())
        if display_name.lower() not in scanned_stores:
            results.append({
                "store": display_name,
                "price": -1,
                "delivery": "-",
                "coupons": "-",
                "finalCost": -1,
                "status": "unavailable",
                "note": "No matching serviceable product was found for the resolved location."
            })
            
    if not valid_results:
        not_verified_rows = [r for r in results if r.get("status") == "not_verified"]
        for step in steps:
            if step["id"] == "10":
                step["status"] = "failed"
        if not_verified_rows:
            summary = "Prices could not be verified from the automated store checks."
            detail = "This does not mean the product is unavailable; it means the app could not extract reliable live prices for this search."
        else:
            summary = "No serviceable stores found in this location."
            detail = ""
        _emit_progress(state, steps, results)
        return {
            "recommendation": {"storeName": "None", "price": 0, "deliveryTime": "N/A", "savings": 0},
            "reasoning": [
                summary,
                *([detail] if detail else []),
                *sorted({r.get("note", "") for r in results if r.get("note")})
            ],
            "results": results,
            "steps": steps,
            "brand_options": [],
            "brand_strategy": {
                "mode": "no_results",
                "brandSpecified": False,
                "detectedBrand": "",
                "summary": "No brand choices could be built because no serviceable products were found.",
            },
        }

    intent = _query_intent(state["query"], valid_results)
    detected_brand = intent.get("brand", "")
    brand_specified = bool(detected_brand)
    valid_results = _annotate_match_scores(valid_results, intent)
    results = [
        next(
            (
                scored for scored in valid_results
                if scored.get("store") == row.get("store")
                and scored.get("name") == row.get("name")
                and scored.get("finalCost") == row.get("finalCost")
            ),
            row,
        )
        for row in results
    ]
    candidate_results = valid_results
    if intent["isSpecific"]:
        exact_results = [row for row in valid_results if row.get("isExactQueryMatch")]
        strong_results = [row for row in valid_results if row.get("matchScore", 0) >= 75]
        if exact_results:
            candidate_results = exact_results
        elif strong_results:
            candidate_results = strong_results

    sorted_results = sorted(
        candidate_results,
        key=lambda x: (-int(x.get("isExactQueryMatch", False)), -x.get("matchScore", 0), x["finalCost"])
    )
    best = sorted_results[0]
    
    preferred_store = profile.get("preferredStore")
    if preferred_store:
        for r in sorted_results:
            if r["store"].lower() == preferred_store.lower():
                if r["finalCost"] <= best["finalCost"] * 1.05:
                    best = r
                    break
                    
    rec = {
        "storeName": best["store"],
        "price": best["finalCost"],
        "deliveryTime": best["delivery"],
        "savings": int(best["price"] - best["finalCost"]) if best["price"] > best["finalCost"] else 0,
        "productUrl": best.get("sourceUrl", ""),
        "matchedItem": best.get("name", ""),
    }
    
    for r in results:
        if r["store"] == best["store"] and r["finalCost"] == best["finalCost"]:
            r["isRecommended"] = True

    brand_options = [] if brand_specified else _build_brand_options(valid_results, best)
    brand_strategy = {
        "mode": "brand_specified" if brand_specified else "brand_choices",
        "brandSpecified": brand_specified,
        "detectedBrand": detected_brand,
        "quantitySpecified": bool(intent.get("quantity")),
        "requestedQuantity": intent.get("quantity", {}).get("raw") if intent.get("quantity") else "",
        "summary": (
            f"Brand detected: {detected_brand}. Comparing matching items across stores."
            if brand_specified
            else "No brand was specified. Showing the best local option for each detected brand or variant."
        ),
    }
            
    reasoning = []
    location = profile.get("location") or {}
    location_label = location.get("label") if isinstance(location, dict) else location
    if location_label:
        reasoning.append(f"Prices were checked for {location_label}.")
    if brand_specified:
        reasoning.append(f"Detected brand intent: {detected_brand}. Recommendation is ranked only against matching brand results.")
    else:
        reasoning.append("No brand was specified, so products were grouped by detected brand and pack size before choosing the best value.")
    if intent.get("quantity"):
        reasoning.append(f"Requested quantity detected: {intent['quantity']['raw']}. Non-matching pack sizes are not allowed to win the recommendation.")
    if not best.get("isExactQueryMatch") and intent["isSpecific"]:
        reasoning.append("No exact same-product match was verified, so this recommendation is the closest verified match.")
    reasoning.append(f"{best['store']} is selected using match quality first, then verified final cost.")
    if best.get("name"):
        reasoning.append(f"Matched item: {best['name']}.")
    
    for r in sorted_results[:6]:
        if r["store"] != best["store"]:
            diff = r["finalCost"] - best["finalCost"]
            reasoning.append(f"{r['store']} was Rs. {diff} more expensive overall.")

    unavailable = [r["store"] for r in results if r.get("finalCost") == -1 and r.get("status") != "not_verified"]
    not_verified = [r["store"] for r in results if r.get("status") == "not_verified"]
    if unavailable:
        reasoning.append(f"No serviceable matching result was returned by: {', '.join(unavailable)}.")
    if not_verified:
        reasoning.append(f"Could not verify live prices from: {', '.join(not_verified)}.")
            
    results = sorted(
        results,
        key=lambda row: (
            row.get("finalCost", -1) <= 0,
            -int(bool(row.get("isExactQueryMatch"))),
            -row.get("matchScore", 0),
            row.get("finalCost") if row.get("finalCost", -1) > 0 else float("inf"),
            row.get("store", ""),
        ),
    )

    for step in steps:
        if step["id"] == "10":
            step["status"] = "completed"
    _emit_progress(state, steps, results)
            
    return {
        "recommendation": rec,
        "reasoning": reasoning,
        "results": results,
        "steps": steps,
        "brand_options": brand_options,
        "brand_strategy": brand_strategy,
    }

workflow = StateGraph(AgentState)
workflow.add_node("decompose", decompose_node)
workflow.add_node("execute", execute_node)
workflow.add_node("aggregate", aggregate_node)
workflow.add_node("reason", reason_node)

workflow.set_entry_point("decompose")
workflow.add_edge("decompose", "execute")
workflow.add_edge("execute", "aggregate")
workflow.add_edge("aggregate", "reason")
workflow.add_edge("reason", END)

app_graph = workflow.compile()
