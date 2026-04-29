import EditorPane from "./components/EditorPane";

export default function HomePage() {
  return (
    <main style={{ padding: 24 }}>
      <h1>Lecture-to-LaTeX Aid Sheet</h1>
      <section style={{ marginTop: 16 }}>
        {/* [C] TODO: upload UI, progress, and constraints form */}
        <div>Upload lectures and set constraints</div>
      </section>
      <section style={{ marginTop: 16 }}>
        {/* [C] TODO: editor + preview split view */}
        <EditorPane />
      </section>
      <section style={{ marginTop: 16 }}>
        {/* [C] TODO: export controls */}
        <button>Export PDF</button>
      </section>
    </main>
  );
}
