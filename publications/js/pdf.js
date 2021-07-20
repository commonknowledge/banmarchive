import "react-pdf/dist/esm/Page/AnnotationLayer.css";

import React, { useCallback, useState, useRef, useMemo } from "react";
import { render } from "react-dom";
import { times, memoize } from "lodash";
import { Document, Page } from "react-pdf/dist/esm/entry.webpack";
import Autosizer from "react-virtualized-auto-sizer";
import InfiniteLoader from "react-window-infinite-loader";
import { VariableSizeList } from "react-window";

const zoomLevels = [0.125, 0.25, 0.5, 0.75, 1, 1.25, 1.5, 2, 4];

const PDFViewer = ({ src, logo }) => {
  const [zoom, setZoom] = useState(1);
  const [state, setState] = useState();

  const stateRef = useRef();

  const loadMore = useCallback(async (startIndex, stopIndex) => {
    if (!stateRef.current) {
      return;
    }

    const { pdf, cache } = stateRef.current;
    const range = times(
      stopIndex - startIndex + 1,
      (i) => i + startIndex
    ).filter((i) => !cache[i]);

    const nextCache = Object.assign({}, cache);

    for (const i of range) {
      const page = pdf.getPage(i + 1);
      if (!nextCache[i]) {
        nextCache[i] = "pending";
        nextCache[i] = await page;
      }
    }

    setState((state) => {
      stateRef.current = {
        ...state,
        cache: nextCache,
      };
      return stateRef.current;
    });
  }, []);

  const handleLoader = useCallback(
    async (pdf) => {
      const midpoint = Math.ceil(pdf.numPages / 2);
      const [first, mid, last] = await Promise.all([
        pdf.getPage(1),
        pdf.getPage(midpoint),
        pdf.getPage(pdf.numPages),
      ]);

      const estDocSize =
        getAspectRatio(first) +
        getAspectRatio(last) +
        getAspectRatio(mid) * (pdf.numPages - 2);

      const state = {
        cache: {
          0: first,
          [midpoint - 1]: mid,
          [pdf.numPages - 1]: last,
        },
        pdf,
        estAspectRatio: estDocSize / pdf.numPages,
      };
      stateRef.current = state;
      setState(state);
    },
    [loadMore]
  );

  const isItemLoaded = useCallback((index) => {
    const { cache } = stateRef.current;
    return index in cache && cache[index] !== "pending";
  }, []);

  const calcPageHeight = useMemo(
    () =>
      memoize((viewportWidth) => (i) => {
        const state = stateRef.current;
        if (!state) {
          throw Error("Pdf not yet loaded");
        }

        const { estAspectRatio, cache } = state;

        const aspectRatio = isItemLoaded(i)
          ? getAspectRatio(cache[i])
          : estAspectRatio;

        return projectHeight({ viewportWidth, aspectRatio });
      }),
    [isItemLoaded, zoom]
  );

  const zoomOffset = useMemo(
    () =>
      memoize((offset) => {
        const idx = zoomLevels.findIndex((x) => x === zoom);
        if (idx + offset < 0) {
          return { disabled: true };
        }

        if (idx + offset >= zoomLevels.length) {
          return { disabled: true };
        }

        return {
          onClick: () => setZoom(zoomLevels[idx + offset]),
        };
      }),
    [zoom]
  );

  const scrollOffsetRef = useRef(0);
  const handleScroll = useCallback(
    ({ scrollOffset }) => {
      scrollOffsetRef.current = scrollOffset / zoom;
    },
    [zoom]
  );

  return (
    <>
      <div className="d-flex flex-column h-100">
        <div className="row w-100 gx-0 gx-md-1 p-1">
          <div className="col-4">
            <a class="navbar-brand d-md-none" href="#">
              <img class="logo-tiny" src={logo} />
            </a>
          </div>

          <div className="col-4 d-flex justify-content-center">
            <div
              className="btn-group"
              role="group"
              aria-label="Page zoom controls"
            >
              <button
                {...zoomOffset(-1)}
                className="btn btn-sm btn-outline-secondary"
                aria-label="Zoom out"
              >
                <ZoomOut />
              </button>

              <div className="btn-group" role="group">
                <button
                  id="zoom-menu"
                  type="button"
                  className="btn btn-sm btn-outline-secondary dropdown-toggle"
                  data-bs-toggle="dropdown"
                  aria-expanded="false"
                >
                  {zoom * 100}%
                </button>
                <ul className="dropdown-menu" aria-labelledby="zoom-menu">
                  {zoomLevels.map((zl) => (
                    <li key={zl}>
                      <a
                        className={
                          "dropdown-item" + (zoom === zl ? " active" : "")
                        }
                        aria-current={zoom === zl}
                        onClick={() => setZoom(zl)}
                        href="#"
                      >
                        {zl * 100}%
                      </a>
                    </li>
                  ))}
                </ul>
              </div>

              <button
                {...zoomOffset(+1)}
                className="btn btn-sm btn-outline-secondary"
                aria-label="Zoom in"
              >
                <ZoomIn />
              </button>
            </div>
          </div>

          <div className="col-4 d-flex justify-content-end">
            <a
              {...zoomOffset(-1)}
              href={src}
              download
              aria-label="Download PDF"
              className="btn btn-sm btn-outline-primary"
            >
              <Download width={18} height={18} className="me-md-1" />
              <span class="d-none d-md-inline">Download PDF</span>
            </a>
          </div>
        </div>

        <div className="flex-grow-1 flex-height-0 position-relative">
          <Autosizer>
            {({ height, width }) => (
              <Document
                loading={<LoadingIndicator />}
                file={src}
                onLoadSuccess={handleLoader}
              >
                {state && (
                  <InfiniteLoader
                    key={zoom}
                    isItemLoaded={isItemLoaded}
                    minimumBatchSize={5}
                    threshold={3}
                    itemCount={state.pdf.numPages}
                    loadMoreItems={loadMore}
                  >
                    {({ onItemsRendered, ref }) => (
                      <VariableSizeList
                        initialScrollOffset={scrollOffsetRef.current * zoom}
                        onItemsRendered={onItemsRendered}
                        ref={ref}
                        estimatedItemSize={projectHeight({
                          viewportWidth: width * zoom,
                          aspectRatio: state.estAspectRatio,
                        })}
                        itemSize={calcPageHeight(width * zoom)}
                        itemCount={state.pdf.numPages}
                        onScroll={handleScroll}
                        width={width}
                        height={height}
                      >
                        {({ index, style }) => {
                          if (typeof state.cache[index] === "object") {
                            return (
                              <div style={style}>
                                <Page
                                  className="pdf-page"
                                  scale={zoom}
                                  width={width - 36}
                                  pageNumber={index + 1}
                                />
                              </div>
                            );
                          } else {
                            return <div style={style} />;
                          }
                        }}
                      </VariableSizeList>
                    )}
                  </InfiniteLoader>
                )}
              </Document>
            )}
          </Autosizer>
        </div>
      </div>
    </>
  );
};

const ZoomIn = (props) => (
  <svg
    fill="currentColor"
    width={16}
    height={16}
    viewBox="0 0 16 16"
    {...props}
  >
    <path
      fillRule="evenodd"
      d="M6.5 12a5.5 5.5 0 1 0 0-11 5.5 5.5 0 0 0 0 11zM13 6.5a6.5 6.5 0 1 1-13 0 6.5 6.5 0 0 1 13 0z"
    />
    <path d="M10.344 11.742c.03.04.062.078.098.115l3.85 3.85a1 1 0 0 0 1.415-1.414l-3.85-3.85a1.007 1.007 0 0 0-.115-.1 6.538 6.538 0 0 1-1.398 1.4z" />
    <path
      fillRule="evenodd"
      d="M6.5 3a.5.5 0 0 1 .5.5V6h2.5a.5.5 0 0 1 0 1H7v2.5a.5.5 0 0 1-1 0V7H3.5a.5.5 0 0 1 0-1H6V3.5a.5.5 0 0 1 .5-.5z"
    />
  </svg>
);

const ZoomOut = (props) => (
  <svg
    fill="currentColor"
    width={16}
    height={16}
    viewBox="0 0 16 16"
    {...props}
  >
    <path
      fillRule="evenodd"
      d="M6.5 12a5.5 5.5 0 1 0 0-11 5.5 5.5 0 0 0 0 11zM13 6.5a6.5 6.5 0 1 1-13 0 6.5 6.5 0 0 1 13 0z"
    />
    <path d="M10.344 11.742c.03.04.062.078.098.115l3.85 3.85a1 1 0 0 0 1.415-1.414l-3.85-3.85a1.007 1.007 0 0 0-.115-.1 6.538 6.538 0 0 1-1.398 1.4z" />
    <path
      fillRule="evenodd"
      d="M3 6.5a.5.5 0 0 1 .5-.5h6a.5.5 0 0 1 0 1h-6a.5.5 0 0 1-.5-.5z"
    />
  </svg>
);

const Download = (props) => (
  <svg
    width="16"
    height="16"
    fill="currentColor"
    viewBox="0 0 16 16"
    {...props}
  >
    <path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z" />
    <path d="M7.646 11.854a.5.5 0 0 0 .708 0l3-3a.5.5 0 0 0-.708-.708L8.5 10.293V1.5a.5.5 0 0 0-1 0v8.793L5.354 8.146a.5.5 0 1 0-.708.708l3 3z" />
  </svg>
);

const getAspectRatio = (page) => {
  return page.getViewport().viewBox[3] / page.getViewport().viewBox[2];
};

const projectHeight = ({ viewportWidth, zoom = 1, aspectRatio }) => {
  return aspectRatio * zoom * viewportWidth;
};

const LoadingIndicator = () => (
  <div className="center-screen">
    <div className="spinner-grow text-brand1" role="status">
      <span className="visually-hidden">Loading...</span>
    </div>
  </div>
);

for (const target of document.querySelectorAll("[data-pdf]")) {
  const pdf = target.dataset.pdf;
  render(<PDFViewer logo={target.dataset.logo} src={pdf} />, target);
}
