from __future__ import annotations

from pathlib import Path

from rag.orchestrator.graph import build_graph


def main():
    output_dir = Path("rag/outputs/graph")
    output_dir.mkdir(parents=True, exist_ok=True)

    graph = build_graph()
    drawable_graph = graph.get_graph()

    # 1. Save Mermaid text
    mermaid_text = drawable_graph.draw_mermaid()
    mermaid_path = output_dir / "voltsentinel_rag_graph.mmd"
    mermaid_path.write_text(mermaid_text, encoding="utf-8")

    # 2. Save Markdown preview
    markdown_path = output_dir / "voltsentinel_rag_graph.md"
    markdown_path.write_text(
        f"# VoltSentinel LangGraph RAG Workflow\n\n```mermaid\n{mermaid_text}\n```\n",
        encoding="utf-8",
    )

    # 3. Try saving PNG
    png_path = output_dir / "voltsentinel_rag_graph.png"

    try:
        png_bytes = drawable_graph.draw_mermaid_png()
        png_path.write_bytes(png_bytes)
        print(f"PNG written: {png_path}")
    except Exception as exc:
        print("PNG render failed, but Mermaid files were written.")
        print(f"Reason: {exc}")

    print(f"Mermaid file written: {mermaid_path}")
    print(f"Markdown file written: {markdown_path}")


if __name__ == "__main__":
    main()
