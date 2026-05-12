# Paper Hands Therapy 💊

A wallet roaster disguised as a psychiatry session. Paste your ETH or Solana wallet and Dr. Rekt, powered by GoldRush's on-chain APIs, delivers a brutally honest psychiatric diagnosis of your trading decisions.

Built for the **GoldRush Hackathon**.

---

## What it does

- Enter any ETH or Solana wallet address
- Dr. Rekt fetches your real on-chain transaction history, portfolio performance, and unrealized P&L via GoldRush APIs
- Gemini AI analyzes your trades and generates a full psychiatric diagnosis — chapter by chapter — roasting your worst decisions
- Results presented as a therapy session report with diagnosis stamps and all

---

## Tech Stack

**Frontend**
- React + Vite
- Animated Matrix-style canvas background
- Space Grotesk font, custom CSS with Covalent green/pink/cyan palette

**Backend**
- FastAPI (Python)
- GoldRush APIs — transaction history, portfolio value, token balances, unrealized P&L
- Gemini AI (`gemini-2.0-flash-lite`) for the roast generation

---

## GoldRush APIs Used

| API | Purpose |
|-----|---------|
| `transactions_v3` | Fetch wallet transaction history |
| `portfolio_v2` | Historical portfolio value over time |
| `balances_v2` | Current token holdings |
| `pricing/historical_by_addresses_v2` | Token price history |
| `GoldRush Streaming` (`upnlForWallet`) | Unrealized P&L via GraphQL |

---

## Running Locally

### Backend
```bash
cd backend
pip install -r requirements.txt

# Create .env file
echo "GOLDRUSH_API_KEY=your_key" > .env
echo "GEMINI_API_KEY=your_key" >> .env

uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`

---

## Environment Variables

```
GOLDRUSH_API_KEY=your_goldrush_api_key
GEMINI_API_KEY=your_gemini_api_key
```

Get your GoldRush API key at [goldrush.dev](https://goldrush.dev)

---

## Demo

Try it live: [Paper Hands Therapy](https://reclivate-monzonitic-romaine.ngrok-free.dev)
