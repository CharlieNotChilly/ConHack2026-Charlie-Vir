export default function EditorPane() {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
      {/* [C] TODO: Monaco editor with LaTeX */}
      <textarea rows={24} style={{ width: "100%" }} defaultValue="% TODO" />
      {/* [C] TODO: PDF preview iframe */}
      <div style={{ border: "1px solid #ccc", minHeight: 400 }}>
        PDF preview
      </div>
    </div>
  );
}
