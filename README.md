# OneBuy

OneBuy is a premium, minimal, real-time AI commerce aggregator that compares prices, delivery estimates, and availability across major quick commerce and grocery delivery platforms. 

## Features

- Real-Time Price Comparison: Scrapes and compares prices across Blinkit, Zepto, Swiggy Instamart, Flipkart Minutes, and Amazon Fresh.
- Dynamic Hyperlocal Targeting: Sanitizes user-defined locations (e.g. Bangalore, Kolkata, Delhi) or 6-digit pincodes, automatically setting target delivery addresses using simulated suggestion click-throughs.
- LLM-Driven Data Extraction: Leverages the Gemini 2.5 Flash API to perform structured JSON extraction over raw unstructured browser DOM data, ensuring parsing resilience.
- Comparative Analysis Board: Shows full serviceable matrices, flagging unserviceable providers clearly instead of displaying negative rates or hiding stores.
- Premium UX: Built on an Apple x Linear design aesthetic featuring smooth micro-animations, clean Notion-style comparisons, and zero branding fluff.

## Technology Stack

- Frontend: Next.js 15, TypeScript, TailwindCSS, Framer Motion, Lucide Icons
- Backend: FastAPI, LangGraph, Playwright, Gemini 2.5 Flash

## Repository Structure

- `app/`: Next.js pages and globals
- `components/`: Modular frontend cards, search controls, and comparison tables
- `backend/`: FastAPI router and server configuration
- `planner/`: LangGraph execution flow nodes (Decompose -> Execute -> Aggregate -> Reason)
- `tools/`: Playwright scraping classes for target platforms and Gemini parsing helper
- `memory/`: User profile state store manager

## Installation & Setup

### Prerequisites

Ensure you have Python 3.10+ and Node.js 18+ installed on your system.

### 1. Environment Configuration

Create a `.env` file in the root directory:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### 2. Backend Setup

Initialize the virtual environment and install packages:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
playwright install chromium
```

Run the backend server:

```bash
python backend/main.py
```
The backend service will run on `http://localhost:8000`.

### 3. Frontend Setup

Install Node packages:

```bash
npm install
```

Run the development server:

```bash
npm run dev
```
Open `http://localhost:3000` in your browser.
