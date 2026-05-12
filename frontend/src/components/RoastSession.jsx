export default function RoastSession({ result, onReset }) {
  const { wallet, chapters, diagnosis } = result;
  const shortWallet = wallet.length > 12
    ? `${wallet.slice(0, 6)}...${wallet.slice(-4)}`
    : wallet;

  function shareOnX() {
    const text = `I went to therapy for my wallet.\n\nDiagnosis: ${diagnosis.condition}\n\n"${diagnosis.treatment}"\n— Dr. Rekt, Blockchain Psychiatrist\n\n#PaperHandsTherapy @goldrushdev`;
    window.open(`https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}`, "_blank");
  }

  return (
    <div className="roast-session">
      <div className="session-header">
        <div className="pill">DR. REKT'S NOTES — SESSION #1</div>
        <p className="patient-line">Patient: {shortWallet}</p>
        <p className="condition-severity">Condition: <strong>Severe</strong></p>
      </div>

      <div className="opening">
        I've reviewed your complete transaction history.
        I want you to know this is a safe space.<br /><br />
        That said... we need to talk.
      </div>

      <div className="chapters">
        {chapters.map((ch, idx) => (
          <div
            key={idx}
            className="chapter"
            data-num={String(idx + 1).padStart(2, "0")}
          >
            <div className="chapter-title">
              <span>Chapter {idx + 1}</span> — {ch.title}
            </div>
            <p className="chapter-body">{ch.body}</p>
          </div>
        ))}
      </div>

      <div className="diagnosis-card">
        <div className="diagnosis-stamp">DIAGNOSED</div>
        <div className="diagnosis-header">Official Psychiatric Diagnosis</div>
        <div className="diagnosis-divider" />
        <div className="diagnosis-row">
          <span className="diagnosis-label">Patient:</span>
          <span>{shortWallet}</span>
        </div>
        <div className="diagnosis-row">
          <span className="diagnosis-label">Condition:</span>
          <span className="diagnosis-condition">{diagnosis.condition}</span>
        </div>
        <div className="diagnosis-row">
          <span className="diagnosis-label">Prognosis:</span>
          <span>{diagnosis.prognosis}</span>
        </div>
        <div className="diagnosis-row">
          <span className="diagnosis-label">Treatment:</span>
          <span>{diagnosis.treatment}</span>
        </div>
        <div className="diagnosis-footer">
          Dr. Rekt, Blockchain Psychiatrist<br />
          License #0x000...0001
        </div>
      </div>

      <div className="actions">
        <button className="btn-share" onClick={shareOnX}>
          Share on X 🐦
        </button>
        <button className="btn-reset" onClick={onReset}>
          Roast Another Wallet
        </button>
      </div>
    </div>
  );
}
