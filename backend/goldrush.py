import httpx
import os
import logging
from datetime import datetime, timedelta

# WETH, WBTC on ETH mainnet
BLUE_CHIPS = {
    "ETH":  ("eth-mainnet", "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"),
    "BTC":  ("eth-mainnet", "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599"),
}

logger = logging.getLogger(__name__)

BASE_URL = "https://api.covalenthq.com/v1"
STREAMING_URL = "https://streaming.goldrushdata.com/graphql"
TIMEOUT = 60

CHAIN_ENUM_MAP = {
    "eth-mainnet":      "ETH_MAINNET",
    "base-mainnet":     "BASE_MAINNET",
    "bsc-mainnet":      "BSC_MAINNET",
    "matic-mainnet":    "POLYGON_MAINNET",
    "optimism-mainnet": "OPTIMISM_MAINNET",
    "gnosis-mainnet":   "GNOSIS_MAINNET",
}

STABLECOINS = {
    "usdc", "usdt", "dai", "busd", "tusd", "frax", "usdd", "usdp",
    "gusd", "lusd", "susd", "fei", "mim", "ust", "cusd", "usdbc",
    "pyusd", "gho", "crvusd", "usdm", "fdusd", "eurc", "eurs", "eurt",
    "usd+", "usdr", "bean", "dola", "usdn", "flex", "ageur", "usdl",
}

STABLECOIN_ADDRESSES = {
    # USDC
    "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
    # USDT
    "0xdac17f958d2ee523a2206206994597c13d831ec7",
    # DAI
    "0x6b175474e89094c44da98b954eedeac495271d0f",
    # BUSD
    "0x4fabb145d64652a948d72533023f6e7a623c7c53",
    # FRAX
    "0x853d955acef822db058eb8505911ed77f175b99e",
    # TUSD
    "0x0000000000085d4780b73119b644ae5ecd22b376",
    # USDP
    "0x8e870d67f660d95d5be530380d0ec0bd388289e1",
    # GUSD
    "0x056fd409e1d7a124bd7017459dfea2f387b6d5cd",
    # LUSD
    "0x5f98805a4e8be255a32880fdec7f6728c6568ba0",
    # PYUSD
    "0x6c3ea9036406852006290770bedfcaba0e23a0e8",
    # GHO
    "0x40d16fc0246ad3160ccc09b8d0d3a2cd28ae6c2f",
    # crvUSD
    "0xf939e0a03fb07f59a73314e73794be0e57ac1b4e",
    # USDC.e / bridged variants handled by symbol check below
}


def is_stablecoin(symbol: str, contract_address: str) -> bool:
    sym = symbol.lower().strip()
    addr = (contract_address or "").lower()
    if addr in STABLECOIN_ADDRESSES:
        return True
    # Exact match
    if sym in STABLECOINS:
        return True
    # Bridged variants: usdc.e, usdt.e, usdc (pos), etc.
    base = sym.split(".")[0].split("(")[0].strip()
    if base in STABLECOINS:
        return True
    # Anything that's just "usd" something short
    if sym.startswith("usd") and len(sym) <= 6:
        return True
    if sym.endswith("usd") and len(sym) <= 6:
        return True
    return False


def get_headers():
    return {"Authorization": f"Bearer {os.getenv('GOLDRUSH_API_KEY')}"}


async def get_transactions(wallet: str, chain: str = "eth-mainnet", page_size: int = 100) -> dict:
    url = f"{BASE_URL}/{chain}/address/{wallet}/transactions_v3/"
    logger.info(f"Fetching transactions for {wallet}")
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.get(url, headers=get_headers(), params={"page-size": page_size})
        logger.info(f"Transactions: {resp.status_code}")
        if not resp.is_success:
            logger.error(resp.text[:300])
        resp.raise_for_status()
        return resp.json()


async def get_historical_prices(chain: str, contract_address: str, from_date: str, to_date: str) -> list:
    url = f"{BASE_URL}/pricing/historical_by_addresses_v2/{chain}/USD/{contract_address}/"
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url, headers=get_headers(), params={"from": from_date, "to": to_date})
        if not resp.is_success:
            return []
        data = resp.json().get("data", [])
        return data[0].get("items", []) if data else []


async def get_upnl_for_wallet(wallet: str, chain: str = "eth-mainnet") -> list:
    """Fetch PnL data for all tokens in a wallet via GoldRush Streaming API."""
    chain_enum = CHAIN_ENUM_MAP.get(chain, "ETH_MAINNET")
    query = f"""
    query {{
      upnlForWallet(chain_name: {chain_enum}, wallet_address: "{wallet}") {{
        token_address
        cost_basis
        current_price
        pnl_realized_usd
        pnl_unrealized_usd
        net_balance_change
        contract_metadata {{
          contract_ticker_symbol
          contract_name
        }}
      }}
    }}
    """
    logger.info(f"Fetching upnlForWallet for {wallet} on {chain_enum}")
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(
                STREAMING_URL,
                json={"query": query},
                headers={**get_headers(), "Content-Type": "application/json"},
            )
            logger.info(f"upnlForWallet: {resp.status_code}")
            if not resp.is_success:
                logger.error(resp.text[:300])
                return []
            body = resp.json()
            if "errors" in body:
                logger.error(f"GraphQL errors: {body['errors']}")
                return []
            return body.get("data", {}).get("upnlForWallet") or []
    except Exception as e:
        logger.warning(f"upnlForWallet failed ({type(e).__name__}), will use fallback")
        return []


async def get_solana_balances(wallet: str) -> dict:
    url = f"{BASE_URL}/solana-mainnet/address/{wallet}/balances_v2/"
    logger.info(f"Fetching Solana balances for {wallet}")
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.get(url, headers=get_headers())
        logger.info(f"Solana balances: {resp.status_code}")
        resp.raise_for_status()
        return resp.json()


async def extract_solana_roast_data(wallet: str) -> dict:
    data = await get_solana_balances(wallet)
    items = data.get("data", {}).get("items", [])

    tokens = []
    for item in items:
        symbol = item.get("contract_ticker_symbol") or ""
        contract_addr = item.get("contract_address") or ""
        if is_stablecoin(symbol, contract_addr):
            continue
        balance_raw = float(item.get("balance") or 0)
        decimals = item.get("contract_decimals") or 9
        amount = balance_raw / (10 ** decimals)
        quote = float(item.get("quote") or 0)
        quote_rate = float(item.get("quote_rate") or 0)
        if quote < 0.01:
            continue
        tokens.append({
            "symbol": symbol,
            "name": item.get("contract_name", symbol),
            "amount": round(amount, 4),
            "current_price": quote_rate,
            "current_value_usd": round(quote, 2),
        })

    tokens.sort(key=lambda t: t["current_value_usd"])

    sol_item = next((i for i in items if i.get("contract_ticker_symbol") == "SOL"), None)
    sol_price = float(sol_item.get("quote_rate") or 0) if sol_item else 0
    total_value = sum(t["current_value_usd"] for t in tokens)

    what_if = []
    if sol_price and total_value > 0:
        sol_equiv = total_value / sol_price
        what_if.append({
            "symbol": "SOL",
            "note": f"If this portfolio were all SOL, you'd hold {round(sol_equiv, 3)} SOL worth ${round(total_value, 2)}"
        })

    return {
        "wallet": wallet,
        "chain": "solana-mainnet",
        "transaction_count": len(items),
        "first_tx_date": None,
        "tokens": tokens,
        "what_if": what_if,
        "mode": "solana_balances",
    }


async def get_what_if(buy_date: str, total_spent: float) -> list:
    """Given a buy date and amount spent, calculate what it'd be worth if they'd bought ETH/BTC instead."""
    if not buy_date or total_spent <= 0:
        return []

    today = datetime.utcnow().strftime("%Y-%m-%d")
    date_from = buy_date
    date_to = (datetime.strptime(buy_date, "%Y-%m-%d") + timedelta(days=2)).strftime("%Y-%m-%d")

    results = []
    import asyncio

    async def fetch_coin(symbol, chain, contract):
        prices_then = await get_historical_prices(chain, contract, date_from, date_to)
        prices_now = await get_historical_prices(chain, contract, today, today)

        # API returns dates descending — use the entry closest to buy date (last item = oldest)
        price_then = prices_then[-1]["price"] if prices_then else None
        price_now = prices_now[0]["price"] if prices_now else None

        if not price_then or not price_now:
            return None

        tokens_bought = total_spent / price_then
        value_now = tokens_bought * price_now
        gain = value_now - total_spent
        pct = ((price_now - price_then) / price_then) * 100

        return {
            "symbol": symbol,
            "price_then": round(price_then, 2),
            "price_now": round(price_now, 2),
            "pct_change": round(pct, 1),
            "value_now": round(value_now, 2),
            "gain_usd": round(gain, 2),
        }

    fetched = await asyncio.gather(*[fetch_coin(sym, chain, addr) for sym, (chain, addr) in BLUE_CHIPS.items()])
    return [r for r in fetched if r is not None]


def _parse_transfers_from_txs(wallet: str, tx_items: list) -> dict:
    from collections import defaultdict
    wallet_lower = wallet.lower()
    trades = defaultdict(lambda: {
        "symbol": "", "name": "", "contract_address": "", "decimals": 18,
        "buys": [], "sells": [],
    })
    for tx in tx_items:
        ts = tx.get("block_signed_at", "")
        date = ts[:10] if ts else ""
        for le in tx.get("log_events", []):
            dec = le.get("decoded") or {}
            if dec.get("name") != "Transfer":
                continue
            params = {p["name"]: p["value"] for p in dec.get("params", [])}
            from_addr = str(params.get("from", "")).lower()
            to_addr = str(params.get("to", "")).lower()
            raw_value = params.get("value", 0)
            contract_addr = (le.get("sender_address") or "").lower()
            symbol = le.get("sender_contract_ticker_symbol") or "UNKNOWN"
            name = le.get("sender_name") or symbol
            decimals = le.get("sender_contract_decimals") or 18
            if not contract_addr or not raw_value:
                continue
            try:
                amount = float(raw_value) / (10 ** decimals)
            except Exception:
                continue
            trades[contract_addr]["symbol"] = symbol
            trades[contract_addr]["name"] = name
            trades[contract_addr]["contract_address"] = contract_addr
            trades[contract_addr]["decimals"] = decimals
            if to_addr == wallet_lower:
                trades[contract_addr]["buys"].append({"date": date, "amount": amount, "timestamp": ts})
            elif from_addr == wallet_lower:
                trades[contract_addr]["sells"].append({"date": date, "amount": amount, "timestamp": ts})
    return trades


async def get_portfolio_balances(wallet: str, chain: str = "eth-mainnet") -> dict:
    """Current token prices from portfolio_v2."""
    url = f"{BASE_URL}/{chain}/address/{wallet}/portfolio_v2/"
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.get(url, headers=get_headers())
        if not resp.is_success:
            return {}
        prices = {}
        for item in (resp.json().get("data", {}).get("items", []) or []):
            addr = (item.get("contract_address") or "").lower()
            holdings = item.get("holdings", [])
            if holdings:
                prices[addr] = float(holdings[0].get("quote_rate") or 0)
        return prices


async def _extract_from_transfers(wallet: str, tx_items: list, chain: str) -> list:
    import asyncio

    trades = _parse_transfers_from_txs(wallet, tx_items)
    interesting = sorted(
        [t for t in trades.values() if t["buys"] and not is_stablecoin(t["symbol"], t["contract_address"])],
        key=lambda t: len(t["buys"]) + len(t["sells"]),
        reverse=True,
    )[:3]

    # Get current prices from portfolio in one call
    current_prices = await get_portfolio_balances(wallet, chain)

    async def enrich_token(t):
        symbol = t["symbol"]
        contract = t["contract_address"]
        buys = t["buys"]
        sells = t["sells"]
        if not buys:
            return None

        # Fetch prices for a short window around first buy only (avoid huge date ranges)
        first_buy_date = min(b["date"] for b in buys)
        window_end = (datetime.strptime(first_buy_date, "%Y-%m-%d") + timedelta(days=5)).strftime("%Y-%m-%d")
        try:
            prices_raw = await asyncio.wait_for(
                get_historical_prices(chain, contract, first_buy_date, window_end),
                timeout=15,
            )
        except Exception:
            prices_raw = []

        buy_price = float(prices_raw[0]["price"] or 0) if prices_raw else 0
        current_price = float(current_prices.get(contract) or 0)

        total_bought = sum(b["amount"] for b in buys)
        total_sold = sum(s["amount"] for s in sells)
        still_holding = max(0, total_bought - total_sold)

        buy_value_usd = total_bought * buy_price
        current_value_usd = still_holding * current_price
        # total_pnl = what it's worth now minus what was spent — always correct
        total_pnl = current_value_usd - buy_value_usd

        return {
            "symbol": symbol,
            "name": t["name"],
            "avg_buy_price": buy_price,
            "current_price": current_price,
            "buy_value_usd": buy_value_usd,
            "current_value_usd": current_value_usd,
            "total_pnl": total_pnl,
            "still_holding": still_holding > 0,
            "num_buys": len(buys),
            "num_sells": len(sells),
        }

    results = await asyncio.gather(*[enrich_token(t) for t in interesting])
    summaries = [r for r in results if r is not None]
    summaries.sort(key=lambda t: t["total_pnl"])
    return summaries


async def extract_roast_data(wallet: str, chain: str = "eth-mainnet") -> dict:
    import asyncio

    upnl_items, tx_data, portfolio_prices = await asyncio.gather(
        get_upnl_for_wallet(wallet, chain),
        get_transactions(wallet, chain),
        get_portfolio_balances(wallet, chain),
    )

    tx_items = tx_data.get("data", {}).get("items", [])
    transaction_count = len(tx_items)
    first_tx_date = None
    if tx_items:
        dates = [tx.get("block_signed_at") for tx in tx_items if tx.get("block_signed_at")]
        if dates:
            first_tx_date = min(dates)

    # Try Streaming API first
    token_summaries = []
    for item in upnl_items:
        meta = item.get("contract_metadata") or {}
        symbol = meta.get("contract_ticker_symbol") or ""
        token_address = (item.get("token_address") or "").lower()
        if is_stablecoin(symbol, token_address):
            continue
        avg_buy_price = float(item.get("cost_basis") or 0)
        # Always use portfolio_v2 price — Streaming API current_price is often stale/zero
        current_price = float(portfolio_prices.get(token_address) or item.get("current_price") or 0)
        pnl_realized = float(item.get("pnl_realized_usd") or 0)
        net_balance = float(item.get("net_balance_change") or 0)
        if avg_buy_price == 0 and pnl_realized == 0:
            continue
        # cost_basis is price-per-token; reconstruct total USD invested
        buy_value_usd = (avg_buy_price * net_balance) + abs(pnl_realized)
        current_value = net_balance * current_price if net_balance > 0 else 0
        cost_of_held = avg_buy_price * net_balance if net_balance > 0 else 0
        unrealized_pnl = current_value - cost_of_held
        total_pnl = pnl_realized + unrealized_pnl
        token_summaries.append({
            "symbol": symbol,
            "name": meta.get("contract_name") or symbol,
            "avg_buy_price": avg_buy_price,
            "current_price": current_price,
            "current_value_usd": current_value,
            "buy_value_usd": buy_value_usd,
            "realized_pnl": pnl_realized if pnl_realized != 0 else None,
            "unrealized_pnl": unrealized_pnl,
            "total_pnl": total_pnl,
            "still_holding_tokens": net_balance if net_balance > 0 else 0,
        })
    token_summaries.sort(key=lambda t: t["total_pnl"])
    logger.info(f"Built {len(token_summaries)} token summaries from upnlForWallet")

    # Fallback: parse ERC20 Transfer events from tx logs
    if not token_summaries and tx_items:
        logger.info("upnlForWallet empty, falling back to transfer parsing")
        token_summaries = await _extract_from_transfers(wallet, tx_items, chain)
        logger.info(f"Fallback built {len(token_summaries)} token summaries")

    what_if = []
    total_spent = sum(t.get("buy_value_usd") or 0 for t in token_summaries)
    if first_tx_date and total_spent > 0:
        first_buy = first_tx_date[:10]
        what_if = await get_what_if(first_buy, total_spent)
        logger.info(f"What-if data: {what_if}")

    return {
        "wallet": wallet,
        "transaction_count": transaction_count,
        "first_tx_date": first_tx_date,
        "tokens": token_summaries,
        "what_if": what_if,
    }
