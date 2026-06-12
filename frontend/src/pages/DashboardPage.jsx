/**
 * DashboardPage — placeholder
 *
 * TODO: implement full dashboard UI
 * - Win rate over time chart
 * - Saved predictions table
 * - Top sectors / products breakdown
 * - Average price by outcome
 */
export default function DashboardPage() {
  return (
    <div style={styles.container}>
      <h1>Dashboard</h1>
      <p style={styles.note}>Dashboard UI — placeholder (not implemented yet)</p>
      <div style={styles.cards}>
        {["Win Rate", "Avg. Deal Price", "Total Predictions", "Top Sector"].map((label, i) => (
          <div key={i} style={styles.card}>
            <div style={styles.cardLabel}>{label}</div>
            <div style={styles.cardValue}>—</div>
          </div>
        ))}
      </div>
      <a href="/analysis" style={styles.link}>← Back to Analysis</a>
    </div>
  );
}

const styles = {
  container:  { padding: "3rem 2rem", fontFamily: "sans-serif", maxWidth: 700, margin: "0 auto" },
  note:       { color: "#718096", marginTop: "0.5rem", marginBottom: "2rem" },
  cards:      { display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" },
  card:       { background: "#f7fafc", border: "1px solid #e2e8f0",
                borderRadius: 10, padding: "1.25rem 1.5rem" },
  cardLabel:  { fontSize: "0.8rem", fontWeight: 600, color: "#718096",
                textTransform: "uppercase", letterSpacing: "0.05em" },
  cardValue:  { fontSize: "1.8rem", fontWeight: 700, color: "#2d3748", marginTop: "0.4rem" },
  link:       { marginTop: "2rem", display: "inline-block", color: "#2b6cb0" },
};
