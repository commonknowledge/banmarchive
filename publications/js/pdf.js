import "react-pdf/dist/esm/Page/AnnotationLayer.css";

import React, { useCallback, useState, useRef, useMemo } from "react";
import { render } from "react-dom";
import { times, memoize } from "lodash";
import { Document, Page } from "react-pdf/dist/esm/entry.webpack";
import Autosizer from "react-virtualized-auto-sizer";
import InfiniteLoader from "react-window-infinite-loader";
import { VariableSizeList } from "react-window";

const PDFViewer = ({ src }) => {
  const [state, setState] = useState();
  const stateRef = useRef();
  const handleLoader = useCallback(async (pdf) => {
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
  });

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
      nextCache[i] = "pending";
      nextCache[i] = await page;
    }

    setState((state) => {
      stateRef.current = {
        ...state,
        cache: nextCache,
      };
      return stateRef.current;
    });
  }, []);

  const isItemLoaded = useCallback((index) => {
    const { cache } = stateRef.current;
    return index in cache && cache[index] !== "pending";
  }, []);

  const calcPageHeight = useMemo(
    () =>
      memoize((viewportWidth) => (i) => {
        if (!state) {
          throw Error("Pdf not yet loaded");
        }

        const { estAspectRatio, cache } = state;

        const aspectRatio = isItemLoaded(i)
          ? getAspectRatio(cache[i])
          : estAspectRatio;

        return projectHeight({ viewportWidth, aspectRatio });
      }),
    [isItemLoaded, state]
  );

  return (
    <Autosizer className="pdf-document">
      {({ height, width }) => (
        <Document
          loading={<LoadingIndicator />}
          file={src}
          onLoadSuccess={handleLoader}
        >
          {state && (
            <InfiniteLoader
              isItemLoaded={isItemLoaded}
              itemCount={state.pdf.numPages}
              loadMoreItems={loadMore}
            >
              {({ onItemsRendered, ref }) => (
                <VariableSizeList
                  onItemsRendered={onItemsRendered}
                  ref={ref}
                  estimatedItemSize={projectHeight({
                    viewportWidth: width,
                    aspectRatio: state.estAspectRatio,
                  })}
                  itemSize={calcPageHeight(width)}
                  itemCount={state.pdf.numPages}
                  width={width}
                  height={height}
                >
                  {({ index, style }) => {
                    if (typeof state.cache[index] === "object") {
                      return (
                        <div style={style}>
                          <Page width={width} pageNumber={index + 1} />
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
  );
};

const getAspectRatio = (page) => {
  return page.getViewport().viewBox[3] / page.getViewport().viewBox[2];
};

const projectHeight = ({ viewportWidth, zoom = 1, aspectRatio }) => {
  return aspectRatio * zoom * viewportWidth;
};

const LoadingIndicator = () => (
  <div className="center-screen">
    <div className="spinner-grow text-primary" role="status">
      <span className="visually-hidden">Loading...</span>
    </div>
  </div>
);

for (const target of document.querySelectorAll("[data-pdf]")) {
  const pdf = target.dataset.pdf;
  render(<PDFViewer src={pdf} />, target);
}
