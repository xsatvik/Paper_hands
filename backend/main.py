import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

from goldrush import extract_roast_data, extract_solana_roast_data
from roaster import roast_wallet

logger = logging.getLogger(__name__)

app = FastAPI(title="Paper Hands Therapy API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class RoastRequest(BaseModel):
    wallet: str
    chain: str = "eth-mainnet"


@app.get("/health")
async def health():
    return {"status": "Dr. Claude is in."}


@app.post("/roast")
async def roast(req: RoastRequest):
    wallet = req.wallet.strip()

    if not wallet:
        raise HTTPException(status_code=400, detail="Wallet address is required.")

    is_evm = wallet.startswith("0x") and len(wallet) == 42
    is_ens = wallet.endswith(".eth")
    is_solana = not wallet.startswith("0x") and 32 <= len(wallet) <= 44 and wallet.isalnum()

    if not (is_evm or is_ens or is_solana):
        raise HTTPException(status_code=400, detail="Invalid wallet address.")

    # Auto-set chain for Solana addresses
    if is_solana and req.chain == "eth-mainnet":
        req.chain = "solana-mainnet"

    try:
        if req.chain == "solana-mainnet":
            roast_data = await extract_solana_roast_data(wallet)
        else:
            roast_data = await extract_roast_data(wallet, req.chain)
    except Exception as e:
        logger.error(f"Data fetch/extraction failed for {wallet}: {type(e).__name__}: {e}")
        raise HTTPException(status_code=502, detail=f"GoldRush API error: {type(e).__name__}: {str(e)}")

    if not roast_data["tokens"] and roast_data["transaction_count"] == 0:
        raise HTTPException(status_code=404, detail="No on-chain activity found for this wallet.")

    try:
        result = await roast_wallet(wallet, roast_data)
    except Exception as e:
        logger.error(f"Roasting failed: {e}")
        raise HTTPException(status_code=502, detail=f"Roasting failed: {str(e)}")

    return result
