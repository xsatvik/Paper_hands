import { useEffect, useState } from "react";
import DrRektSVG from "./DrRektSVG";

const STEPS = [
  "Reviewing your transaction history...",
  "Calculating poor life choices...",
  "Measuring diamond hand deficiency...",
  "Assessing FOMO damage...",
  "Counting the times you panic sold...",
  "Locating the exact top you bought at...",
  "Dr. Rekt is shaking his head...",
  "Preparing the diagnosis...",
];

export default function LoadingScreen() {
  const [visibleSteps, setVisibleSteps] = useState([]);

  useEffect(() => {
    let i = 0;
    const interval = setInterval(() => {
      if (i < STEPS.length) {
        setVisibleSteps((prev) => [...prev, STEPS[i]]);
        i++;
      } else {
        clearInterval(interval);
      }
    }, 600);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="loading-screen">
      <DrRektSVG className="dr-rekt-loading" />
      <div className="loading-header">
        <h2>Reviewing your case...</h2>
      </div>
      <div className="steps-list">
        {visibleSteps.map((step, idx) => (
          <div
            key={idx}
            className={`step-item${idx < visibleSteps.length - 1 ? " step-done" : ""}`}
            style={{ animationDelay: `${idx * 0.04}s` }}
          >
            <span className="step-icon">
              {idx === visibleSteps.length - 1 ? "⏳" : "✓"}
            </span>
            {step}
          </div>
        ))}
      </div>
    </div>
  );
}
