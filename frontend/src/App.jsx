import { useState } from "react";
import WaitingRoom from "./components/WaitingRoom";
import LoadingScreen from "./components/LoadingScreen";
import RoastSession from "./components/RoastSession";
import AnimatedBackground from "./components/AnimatedBackground";
import "./App.css";

export default function App() {
  const [phase, setPhase] = useState("waiting"); // waiting | loading | roast
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  async function handleSubmit(wallet, chain) {
    setError(null);
    setPhase("loading");

    try {
      const res = await fetch("http://localhost:8000/roast", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ wallet, chain }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Something went wrong.");
      }

      const data = await res.json();
      setResult(data);
      setPhase("roast");
    } catch (e) {
      setError(e.message);
      setPhase("waiting");
    }
  }

  function reset() {
    setPhase("waiting");
    setResult(null);
    setError(null);
  }

  return (
    <>
      <AnimatedBackground />
      <div className="bg-vignette" />
      <div className="bg-scanline" />
      <div className="app">
        {phase === "waiting" && <WaitingRoom onSubmit={handleSubmit} error={error} />}
        {phase === "loading" && <LoadingScreen />}
        {phase === "roast" && result && <RoastSession result={result} onReset={reset} />}
      </div>
    </>
  );
}
