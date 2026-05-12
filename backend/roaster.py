import google.generativeai as genai
import json
import os
import logging

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are Dr. Rekt, a blockchain psychiatrist who has reviewed 50,000 wallets and feels nothing anymore.

Your job is to make the patient feel the full weight of what they did — not just financially, but personally. Make them question their judgment, their intelligence, their decisions. This is a roast that should leave a mark.

Rules:
- Use trader language: "paper hands", "exit liquidity", "bought the top", "rug", "diamond hands on a dead coin".
- Every sentence uses exact numbers from the data. "$49.41" not "about $50".
- Make it personal. Attack their decision-making, their timing, their pattern of thinking. Not just the loss — the person behind it.
- Guilt them. "Your family could have used that money." "That was someone's rent." Make the loss feel real and shameful.
- Short, punchy sentences. Every word must land.
- Build to a crescendo — each sentence worse than the last.
- No hedge words. Only verdicts. Only certainties.
- Do not use em-dash inside sentences."""


def _fmt_float(k: str, v: float):
    """Format price fields to readable decimals; round others to 2dp."""
    price_fields = {"avg_buy_price", "avg_sell_price", "current_price", "price_then", "price_now"}
    if k in price_fields and v != 0:
        if abs(v) >= 1:
            return round(v, 2)
        import math
        decimals = max(2, -int(math.floor(math.log10(abs(v)))) + 3)
        # Return as string to avoid JSON scientific notation for micro prices
        return f"{v:.{decimals}f}"
    return round(v, 2)


def _clean_tokens(tokens: list) -> list:
    """Format floats and strip null fields so the LLM isn't confused by None values."""
    cleaned = []
    for t in tokens:
        c = {}
        for k, v in t.items():
            if v is None:
                continue  # omit null fields entirely
            if isinstance(v, float):
                c[k] = _fmt_float(k, v)
            else:
                c[k] = v
        cleaned.append(c)
    return cleaned


def build_prompt(wallet: str, roast_data: dict) -> str:
    tokens_summary = json.dumps(_clean_tokens(roast_data["tokens"]), indent=2)
    what_if_summary = json.dumps(roast_data.get("what_if", []), indent=2)
    active_since = roast_data['first_tx_date'][:10] if roast_data.get('first_tx_date') else "unknown"
    is_solana = roast_data.get("mode") == "solana_balances"
    mode_note = "NOTE: This is a Solana wallet. No trade history available — roast is based on what they are CURRENTLY HOLDING. Shame them for their bag choices, dust tokens, and memecoins. Ask why they're sitting on these instead of just holding SOL." if is_solana else ""

    what_if_block = f"WHAT IF THEY BOUGHT ETH/BTC INSTEAD:\n{what_if_summary}" if roast_data.get("what_if") else ""

    return f"""Wallet: {wallet} | Active since: {active_since} | Txs: {roast_data['transaction_count']}
{mode_note}
TRADES (worst first):
{tokens_summary}

{what_if_block}

Output exactly:

---ROAST_START---

CHAPTER 1 — [TOKEN NAME + THE CRIME, MAKE IT STING]
5-6 sentences. Lead with exact token, exact dollars, exact price collapse. Then make it personal: who could have used that money, what real thing it could have paid for, why this specific decision was uniquely stupid. Attack their judgment directly. Final sentence is the kill shot — so specific and personal it physically hurts to read.

CHAPTER 2 — [WHAT THEY MISSED: MAKE THEM FEEL THE EXACT DOLLAR GAP]
This chapter is ONLY about the what-if data. Hit every number: price_then, price_now, pct_change, value_now, gain_usd for both ETH and BTC. Then calculate the total they could have had vs what they actually have. Make them feel the gap in their chest. End with one sentence about what that missed money represents in real life.

CHAPTER 3 — THE REDEMPTION ARC (THAT ISN'T ONE)
One backhanded compliment — something true but pathetic. Then 3 sentences that use it to make them feel worse. Final line sounds like encouragement but is actually the most devastating thing in the whole roast.

---DIAGNOSIS---
Condition: [4-8 word psychiatric disorder, capitalised, specific to their pattern]
Prognosis: [One sentence. Reference exact numbers. Make them feel judged forever.]
Treatment: [One brutal, specific sentence starting with a verb. No comfort.]

---ROAST_END---

Only use numbers from the data. No invented figures. No "perhaps" or "maybe". Titles must name their specific trade.
If realized_pnl is missing from a token, they are still holding it — the loss is unrealized, not zero.
If all PnL is zero: Condition: Chronic Observer Syndrome | Prognosis: Watched others lose money. Most financially responsible person here. | Treatment: Buy something. Anything.
"""


async def roast_wallet(wallet: str, roast_data: dict) -> dict:
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel(
        model_name="gemini-3.1-flash-lite-preview",
        system_instruction=SYSTEM_PROMPT,
    )

    full_prompt = build_prompt(wallet, roast_data)
    with open("/tmp/last_llm_prompt.txt", "w") as f:
        f.write("=== SYSTEM ===\n")
        f.write(SYSTEM_PROMPT)
        f.write("\n\n=== USER ===\n")
        f.write(full_prompt)

    import asyncio
    response = await asyncio.to_thread(
        model.generate_content,
        full_prompt,
        generation_config=genai.GenerationConfig(
            temperature=0.9,
            max_output_tokens=20000,
        ),
    )

    raw = response.text
    logger.info(f"Gemini raw length={len(raw or '')}")
    result = parse_roast(raw, wallet)
    result["what_if"] = roast_data.get("what_if", [])
    return result


def parse_roast(raw: str, wallet: str) -> dict:
    chapters = []
    diagnosis = {}

    try:
        body = raw or ""
        if "---ROAST_START---" in body:
            body = body.split("---ROAST_START---")[1]
        if "---ROAST_END---" in body:
            body = body.split("---ROAST_END---")[0]
        diag_raw = body.split("---DIAGNOSIS---")

        chapters_raw = diag_raw[0].strip()
        import re
        for block in re.split(r'\n(?=CHAPTER)', chapters_raw):
            block = block.strip()
            if not block.startswith("CHAPTER"):
                continue
            lines = block.split("\n", 1)
            title = re.sub(r'^CHAPTER\s*\d*\s*[\u2014\-]+\s*', '', lines[0]).strip()
            body = lines[1].strip() if len(lines) > 1 else ""
            chapters.append({"title": title, "body": body})

        if len(diag_raw) > 1:
            for line in diag_raw[1].strip().split("\n"):
                line = line.replace("**", "").strip()
                if line.startswith("Condition:"):
                    diagnosis["condition"] = line.replace("Condition:", "").strip()
                elif line.startswith("Prognosis:"):
                    diagnosis["prognosis"] = line.replace("Prognosis:", "").strip()
                elif line.startswith("Treatment:"):
                    diagnosis["treatment"] = line.replace("Treatment:", "").strip()
    except Exception:
        chapters = [{"title": "THE FULL SESSION", "body": raw}]
        diagnosis = {}

    if not diagnosis.get("condition"):
        diagnosis["condition"] = "Unclassifiable Portfolio Disorder"
    if not diagnosis.get("prognosis"):
        diagnosis["prognosis"] = "The blockchain remembers everything. Unfortunately."
    if not diagnosis.get("treatment"):
        diagnosis["treatment"] = "Close the app. Go outside. Touch grass."

    return {
        "wallet": wallet,
        "chapters": chapters,
        "diagnosis": diagnosis,
        "raw": raw,
    }
