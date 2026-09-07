import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ImageList } from "../ImageList";

describe("ImageList", () => {
  it("ファイルが空の場合は何も描画しない", () => {
    const { container } = render(<ImageList files={[]} />);
    expect(container.firstChild).toBeNull();
  });

  it("ファイル名の一覧を表示する", () => {
    render(<ImageList files={["page_001.png", "page_002.png", "page_003.png"]} />);

    expect(screen.getByText("アップロードされた画像")).toBeInTheDocument();
    expect(screen.getByText("page_001.png")).toBeInTheDocument();
    expect(screen.getByText("page_002.png")).toBeInTheDocument();
    expect(screen.getByText("page_003.png")).toBeInTheDocument();
  });
});
