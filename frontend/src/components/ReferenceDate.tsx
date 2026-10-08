type ReferenceDateProps = { asOf: string | null };

export function ReferenceDate({ asOf }: ReferenceDateProps) {
  return (
    <div
      style={{
        background: "#eef4ff",
        border: "1px solid #c3d4f5",
        borderRadius: 6,
        padding: "0.6rem 0.9rem",
        marginBottom: "1rem",
        fontSize: "0.9rem",
      }}
    >
      <strong>Reference date (as-of):</strong>{" "}
      {asOf ? <code>{asOf}</code> : "loading..."}
      <div style={{ color: "#44506b", marginTop: "0.25rem" }}>
        All eligibility, risk tiers, A1C windows, and visit-cadence tasks are
        evaluated relative to this date. Reference date defaults to the latest
        lab result date in the dataset.
      </div>
    </div>
  );
}