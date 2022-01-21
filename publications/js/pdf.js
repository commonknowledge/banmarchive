import "@react-pdf-viewer/core/lib/styles/index.css";
import "@react-pdf-viewer/toolbar/lib/styles/index.css";

import { Viewer, Worker } from "@react-pdf-viewer/core";
import { toolbarPlugin } from "@react-pdf-viewer/toolbar";

import React from "react";
import { render } from "react-dom";

const ArticleViewer = ({ src }) => {
  const toolbar = toolbarPlugin();
  const { Toolbar } = toolbar;

  return (
    <Worker workerUrl="https://unpkg.com/pdfjs-dist@2.6.347/build/pdf.worker.min.js">
      <div
        className="rpv-core__viewer"
        style={{ display: "flex", flexDirection: "column", height: "100%" }}
      >
        <div class="p-2 d-flex justify-content-center">
          <Toolbar>
            {(props) => {
              const { EnterFullScreen, ZoomIn, ZoomOut } = props;
              return (
                <>
                  <div className="px-1">
                    <ZoomOut />
                  </div>
                  <div className="px-1">
                    <ZoomIn />
                  </div>
                  <div className="px-1">
                    <EnterFullScreen />
                  </div>
                </>
              );
            }}
          </Toolbar>
        </div>

        <div style={{ flex: 1, overflow: "hidden" }}>
          <Viewer plugins={[toolbar]} fileUrl={src} />
        </div>
      </div>
    </Worker>
  );
};

for (const target of document.querySelectorAll("[data-pdf]")) {
  const pdf = target.dataset.pdf;
  const isHtml = pdf.endsWith(".html") || pdf.endsWith("htm");

  if (isHtml) {
    return <iframe src={pdf} class="w-100 h-100 overflow-y-auto" />;
  } else {
    render(<ArticleViewer logo={target.dataset.logo} src={pdf} />, target);
  }
}
