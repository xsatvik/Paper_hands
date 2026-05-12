import { useState } from "react";
import DrRektSVG from "./DrRektSVG";

const CHAINS = [
  { value: "eth-mainnet", label: "Ethereum" },
  { value: "solana-mainnet", label: "Solana" },
];

export default function WaitingRoom({ onSubmit, error }) {
  const [wallet, setWallet] = useState("");
  const [chain, setChain] = useState("eth-mainnet");

  function handleSubmit(e) {
    e.preventDefault();
    if (wallet.trim()) onSubmit(wallet.trim(), chain);
  }

  return (
    <div className="waiting-room">
      <div className="wr-content">
        <div className="pill">Psychiatric Services</div>
        <h1 className="title">
          <span className="pill-emoji">💊</span> Paper Hands<br />Therapy
        </h1>
        <p className="subtitle">
          Welcome. Please take a seat.<br />
          Dr. Rekt will see your wallet now.
        </p>

        <form onSubmit={handleSubmit} className="form">
          <input
            className="wallet-input"
            type="text"
            placeholder="0x... or yourname.eth"
            value={wallet}
            onChange={(e) => setWallet(e.target.value)}
            autoFocus
          />
          <select
            className="chain-select"
            value={chain}
            onChange={(e) => setChain(e.target.value)}
          >
            {CHAINS.map((c) => (
              <option key={c.value} value={c.value}>{c.label}</option>
            ))}
          </select>
          <button className="btn-submit" type="submit" disabled={!wallet.trim()}>
            Begin Session →
          </button>
        </form>

        {error && <div className="error-box">⚠️ {error}</div>}
        <p className="warning">⚠️ Warning: The truth may hurt.</p>
      </div>

      <div className="wr-character">
        <DrRektSVG className="dr-rekt-hero" />
        <div className="character-caption">"I've seen worse.<br />No I haven't."</div>
      </div>
    </div>
  );
}
