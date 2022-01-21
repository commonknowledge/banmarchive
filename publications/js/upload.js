import { useCallback, useMemo, useReducer } from "react";
import { parse } from "@vanillaes/csv";
import { render } from "react-dom";
import { useDropzone } from "react-dropzone";
import { memoize, fromPairs, groupBy, keyBy, identity } from "lodash";

const ARCHIVE_ROOT = JSON.parse(
  document.getElementById("archive_root").innerText
);
const EXAMPLE_ROWS = JSON.parse(
  document.getElementById("example_rows").innerText
);
const EXAMPLE_COLUMNS = Object.keys(EXAMPLE_ROWS[0]);

const Uploader = () => {
  const [state, dispatch] = useReducer(reducer, initialState);

  const action = useMemo(
    () =>
      memoize((key, next) => {
        if (typeof key === "string") {
          return (value) => dispatch({ type: key, value });
        }

        if (typeof key === "function") {
          return (value) => key(value).then(action(next));
        }
      }),
    []
  );

  const pdfDropzone = useDropzone({
    onDrop: action("loadPdf"),
    accept: "application/pdf",
  });
  const csvDropzone = useDropzone({
    onDrop: action(loadCsv, "loadCsv"),
    accept: "text/csv",
  });

  const status = useMemo(() => {
    const { pdfs, csv } = state;
    const filenameSet = new Set(pdfs.map((p) => p.name));

    const status = {};
    if (!csv) {
      status.noCsv = true;
      return status;
    }

    status.valid = true;

    const error = (error) => {
      status.valid = false;
      return { error };
    };

    const getPdf = (name) => {
      if (!name) {
        return;
      }

      if (filenameSet.has(name)) {
        return { value: name };
      } else {
        return {
          value: name,
          ...error("You have not uploaded a pdf named " + name),
        };
      }
    };

    status.importSpec = Object.keys(csv.data).map((issue) => {
      const articles = csv.data[issue];

      const getValid = (
        key,
        { validator, error: errorMsg, optional, normalize = identity }
      ) => {
        const hit = articles.find((x) => validator(normalize(x[key])));
        if (hit) {
          return { value: normalize(hit[key]) };
        } else {
          if (optional && !articles.some((x) => x[key])) {
            return { value: hit };
          }

          return error(errorMsg);
        }
      };

      const coverRow = articles.find((a) => a.is_cover);

      return {
        title: issue,
        publication: getValid("publication", {
          validator: (x) => !!x,
        }),
        volume_no: getValid("volume_no", {
          optional: true,
          validator: (x) => !isNaN(x),
          normalize: Number,
        }),
        issue_no: getValid("issue_no", {
          optional: true,
          validator: (x) => !isNaN(x),
          normalize: Number,
        }),
        publication_date: getValid("publication_date", {
          error: "No row for this issue has a valid publication_date",
          validator: (x) => x && x.match(/\d\d\d\d-\d\d-\d\d/),
        }),
        articles: articles
          .filter((a) => !a.is_cover)
          .map((article) => {
            return {
              title: article.article_title.trim()
                ? { value: article.article_title }
                : error("You must provide a title for each article"),
              author: article.author ? { value: article.author } : {},
              pdf: getPdf(article.filename),
            };
          }),
        cover: !coverRow
          ? undefined
          : coverRow.article_title.trim()
          ? getPdf(coverRow && coverRow.filename)
          : {
              ...getPdf(coverRow && coverRow.filename),
              ...error(
                "The article_title for the issue cover is blank. Please give it a title (such as “Covers”)"
              ),
            },
      };
    });

    status.articlesMissing;

    return status;
  }, [state]);

  const handleUpload = useCallback(async () => {
    if (!status.valid) {
      return;
    }

    dispatch({ type: "status", value: "pending" });
    try {
      await doUpload(status.importSpec, state.pdfs, action("progress"));
    } catch (error) {
      console.error(error);
      dispatch({ type: "status", value: "error" });
      dispatch({ type: "error", value: String(error) });
      return;
    }

    dispatch({ type: "status", value: "done" });
  }, [status, state.pdfs]);

  console.log(state);

  return (
    <>
      <ul className="fields">
        <li>
          <h2 style={{ paddingfontWeight: 600 }}>PDF files:</h2>
          <div
            className="drop-zone"
            {...pdfDropzone.getRootProps({
              style: { overflowY: "auto", maxHeight: 400 },
            })}
          >
            <input {...pdfDropzone.getInputProps()} />

            {state.pdfs.length === 0 && (
              <div>Drag and drop article pdfs into this area</div>
            )}
            {state.pdfs.length > 0 && (
              <ul>
                {state.pdfs.map((pdf) => (
                  <li key={pdf.name}>{pdf.name}</li>
                ))}
              </ul>
            )}
          </div>
        </li>

        <li>
          <h2 style={{ paddingfontWeight: 600 }}>Metadata sheet:</h2>
          <div
            className="drop-zone"
            {...csvDropzone.getRootProps({
              style: { overflowY: "auto", maxHeight: 400 },
            })}
          >
            <input {...csvDropzone.getInputProps()} />
            {!state.csv && (
              <div>Drop a csv file of article metadata into this area.</div>
            )}
            {state.csv && state.csv.title}
          </div>
        </li>

        <li>
          <ol className="info">
            <li>Add a valid metadata document</li>
            <li>Add a pdf for each article</li>
            <li>
              Check the import preview (below) for any errors or incorrect
              information. Drag any missing pdf files into the upload box or fix
              and re-upload the metadata document to correct errors and add
              missing information.
            </li>
            <li>Press upload</li>
          </ol>
        </li>

        {!["initial", "error"].includes(state.status) && (
          <div
            style={{
              position: "fixed",
              width: "100vw",
              height: "100vh",
              top: 0,
              left: 0,
              background: "rgba(255,255,255,0.7)",
              zIndex: 100,
            }}
          >
            <div
              style={{
                position: "absolute",
                backgroundColor: "white",
                border: "2px solid black",
                width: 600,
                height: 400,
                top: "50vh",
                left: "50vh",
                maxWidth: "100vw",
                maxHeight: "100vh",
                transform: "translateY(-50%)",
                padding: "1em",
                display: "flex",
                flexDirection: "column",
              }}
            >
              <UploadModal
                {...state.progress}
                status={state.status}
                onClose={() => {
                  dispatch({ type: "status", value: "initial" });
                }}
              />
            </div>
          </div>
        )}

        <li>
          <button
            onClick={handleUpload}
            type="button"
            className="button button-longrunning"
            style={{ marginBottom: "2em" }}
            disabled={!status.valid || state.status === "pending"}
          >
            <em>Upload</em>
          </button>
        </li>

        {state.status === "error" && (
          <div style={{ color: "red" }}>
            Sorry, something went wrong with your upload:
            <div style={{ marginTop: "1em", marginBottom: "1em" }}>
              {state.error}
            </div>
            Please let us know:{" "}
            <a href="mailto:hello@commonknowledge.coop">
              hello@commonknowledge.coop
            </a>
          </div>
        )}

        {status.importSpec && (
          <li>
            <h2 style={{ fontWeight: 600 }}>Import preview:</h2>

            <div>
              {status.importSpec.map((issue) => (
                <div
                  key={issue.title}
                  style={{ border: "1px solid lightgrey", padding: "1em" }}
                >
                  <h4
                    style={{
                      fontWeight: 600,
                      padding: 3,
                      margin: 0,
                      margin: 0,
                      paddingBottom: "1em",
                      borderBottom: "1px solid lightgrey",
                    }}
                  >
                    {issue.title}
                  </h4>

                  <table style={{ width: "100%", marginTop: "1em" }}>
                    <tbody>
                      <tr>
                        <td style={{ padding: 3, fontWeight: 600 }}>
                          Publication
                        </td>
                        <td style={{ padding: 3 }}>
                          <SpecValue {...issue.publication} />
                        </td>
                      </tr>
                      <tr>
                        <td style={{ padding: 3, fontWeight: 600 }}>Date</td>
                        <td style={{ padding: 3 }}>
                          <SpecValue {...issue.publication_date} />
                        </td>
                      </tr>
                      <tr>
                        <td style={{ padding: 3, fontWeight: 600 }}>
                          Volume #
                        </td>
                        <td style={{ padding: 3 }}>
                          <SpecValue {...issue.volume_no} />
                        </td>
                      </tr>
                      <tr>
                        <td style={{ padding: 3, fontWeight: 600 }}>Issue #</td>
                        <td style={{ padding: 3 }}>
                          <SpecValue {...issue.issue_no} />
                        </td>
                      </tr>
                      <tr>
                        <td style={{ padding: 3, fontWeight: 600 }}>Cover</td>
                        <td style={{ padding: 3 }}>
                          <SpecValue {...issue.cover} />
                        </td>
                      </tr>
                    </tbody>
                  </table>

                  <table style={{ width: "100%", marginTop: "1em" }}>
                    <thead>
                      <tr>
                        <th>Article</th>
                        <th>Author</th>
                        <th>PDF File</th>
                      </tr>
                    </thead>
                    <tbody>
                      {issue.articles.map((article) => (
                        <tr key={article.title.value}>
                          <td
                            style={{
                              padding: 3,
                              border: "1px solid lightgrey",
                            }}
                          >
                            <SpecValue {...article.title} />
                          </td>
                          <td
                            style={{
                              padding: 3,
                              border: "1px solid lightgrey",
                            }}
                          >
                            <SpecValue {...article.author} />
                          </td>
                          <td
                            style={{
                              padding: 3,
                              border: "1px solid lightgrey",
                            }}
                          >
                            <SpecValue {...article.pdf} />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ))}
            </div>
          </li>
        )}
      </ul>

      <li>
        <h2 style={{ fontWeight: 600 }}>
          Guidance for producing metadata sheets:
        </h2>

        <ul className="info">
          <li>All headings must be exactly as in the example below</li>
          <li>
            <code>author</code>, <code>volume_no</code>, <code>issue_no</code>{" "}
            and <code>is_cover</code> may be left blank. All other fields are
            required.
          </li>
          <li>
            Articles belonging to the same issue must have exactly the same
            issue title. Otherwise you will get duplicate issues with missing
            articles.
          </li>
          <li>
            <code>publication_date</code> must be in YYYY-MM-DD format.
          </li>
          <li>
            <code>publication_date</code>, <code>volume_no</code> and{" "}
            <code>issue_no</code> apply to issues rather than articles. So you
            should take care not to provide conflicting values within the same
            issue. However, it is fine to just define them on one row per issue
            and leave the others blank if that is more convenient.
          </li>
          <li>
            For each issue, you should add a row for the cover (along with
            miscellaneous content such as the introduction) if you have access.
            It should have <code>is_cover</code> set to 1 to indicate that it is
            a cover, not a regular article. If you don't set a cover, the first
            page of the first article will be used in its place.
          </li>
        </ul>

        <h3 style={{ fontWeight: 600 }}>Example metadata sheet:</h3>

        <div style={{ overflowX: "auto", width: "100%" }}>
          <table>
            <thead>
              <tr>
                {EXAMPLE_COLUMNS.map((key) => (
                  <th
                    style={{ padding: 3, border: "1px solid lightgrey" }}
                    key={key}
                  >
                    {key}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {EXAMPLE_ROWS.map((row, i) => (
                <tr key={i}>
                  {EXAMPLE_COLUMNS.map((col) => (
                    <td
                      style={{ padding: 3, border: "1px solid lightgrey" }}
                      key={col}
                    >
                      {row[col]}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </li>
    </>
  );
};

const UploadModal = ({
  status,
  current,
  total,
  currentIssue,
  currentIssueName,
  totalIssues,
  log,
  errors,
  onClose,
}) => {
  if (status === "done") {
    if (errors?.length > 0) {
      return (
        <>
          <h2 style={{ marginBottom: "2em" }}>Upload completed with errors</h2>
          <div
            style={{
              flex: 1,
              overflowY: "auto",
              color: "rgba(255,0,0,0.8)",
            }}
          >
            {errors.map((x, i) => (
              <div key={i}>{x}</div>
            ))}
          </div>

          <div style={{ flex: 1 }}></div>

          <div style={{ marginBottom: "1em" }}>
            Try creating these articles in the{" "}
            <a href="http://localhost:8000/admin">Main admin view</a>. Need
            help? Email us:{" "}
            <a href="mailto:hello@commonknowledge.coop">
              hello@commonknowledge.coop
            </a>
          </div>

          <button
            style={{ alignSelf: "flex-start" }}
            onClick={onClose}
            type="button"
            className="button"
          >
            Close
          </button>
        </>
      );
    }

    return (
      <>
        <h2 style={{ marginBottom: "2em" }}>Upload completed</h2>
        <div
          style={{
            flex: 1,
            overflowY: "auto",
            color: "rgba(0,0,0,0.8)",
            marginBottom: "1em",
          }}
        >
          {log.map((x, i) => (
            <div key={i}>{x}</div>
          ))}
        </div>

        <button
          style={{ alignSelf: "flex-start" }}
          onClick={onClose}
          type="button"
          className="button"
        >
          Close
        </button>
      </>
    );
  }

  return (
    <>
      <h2 style={{ marginBottom: "2em" }}>Uploading…</h2>

      <progress
        style={{ width: "100%", height: "1em" }}
        max={total}
        value={current}
      />

      <div
        style={{
          fontWeight: 600,
          marginTop: "1em",
          textAlign: "start",
          width: "100%",
        }}
      >
        Uploading {currentIssueName} ({currentIssue} / {totalIssues})
      </div>

      <div
        style={{
          flex: 1,
          overflowY: "auto",
          color: "rgba(0,0,0,0.8)",
          fontSize: 11,
          marginTop: "1em",
        }}
      >
        {log.map((x, i) => (
          <div key={i}>{x}</div>
        ))}
      </div>
    </>
  );
};

const SpecValue = ({ error, value }) => {
  let txt = value;
  if (value === "" || typeof value === "undefined" || value === "none") {
    txt = "-";
  }

  return (
    <div style={{ display: "inline-block" }}>
      <div>{txt}</div>
      {error && <div style={{ color: "red" }}>Error: {error}</div>}
    </div>
  );
};

const loadCsv = ([acceptedFile]) => {
  if (!acceptedFile) {
    return;
  }

  return readFileAsText(acceptedFile).then((csv) => {
    const [header, ...rows] = parse(csv);

    const rowObjects = rows.map((row, i) => ({
      ...fromPairs(header.map((key, i) => [key, (row[i] ?? "").trim()])),
      i: i + 1,
    }));

    return {
      title: acceptedFile.name,
      data: groupBy(rowObjects, "issue_title"),
    };
  });
};

const initialState = {
  status: "initial",
  pdfs: [],
  csv: undefined,
  progress: {
    current: 0,
    total: 0,
    currentIssueName: "",
    currentIssue: 0,
    totalIssues: 0,
    log: [],
    errors: [],
  },
};

const reducer = (state, action) => {
  if (action.type === "loadPdf") {
    if (!action.value) {
      return state;
    }

    return {
      ...state,
      pdfs: [...state.pdfs, ...action.value],
    };
  }
  if (action.type === "status") {
    return {
      ...state,
      status: action.value,
      progress:
        action.value === "initial" ? initialState.progress : state.progress,
    };
  }
  if (action.type === "progress") {
    return {
      ...state,
      progress: action.value,
    };
  }
  if (action.type === "error") {
    return {
      ...state,
      error: action.value,
    };
  }
  if (action.type === "loadCsv") {
    if (!action.value) {
      return state;
    }

    return {
      ...state,
      csv: action.value,
    };
  }

  return state;
};

const csrfToken = document.querySelector(
  'input[name="csrfmiddlewaretoken"]'
).value;

const doUpload = async (importSpec, pdfs, onProgress) => {
  pdfs = keyBy(pdfs, "name");

  const postTo = async (resource, { json, data, file }) => {
    const baseHeaders = {
      Accept: "application/json",
      "X-CSRFToken": csrfToken,
    };

    const url = `/api/${resource}/`;

    for (let attempt = 1; attempt <= 5; ++attempt) {
      let res;
      try {
        if (file) {
          const fd = new FormData();
          fd.append("file", file);

          Object.keys(data).forEach((key) => {
            fd.append(key, data[key]);
          });

          res = await fetch(url, {
            method: "POST",
            body: fd,
            headers: baseHeaders,
          });
        } else if (json) {
          res = await fetch(url, {
            method: "POST",
            body: JSON.stringify(json),
            headers: {
              ...baseHeaders,
              "Content-Type": "application/json",
            },
          });
        } else {
          res = await fetch(url, {
            method: "POST",
            headers: baseHeaders,
          });
        }
      } catch {
        await delay(2 ** attempt * 500);
        continue;
      }

      if (!res.ok) {
        if (res.status > 500) {
          await delay(2 ** attempt * 500);
          continue;
        }

        throw Error(res.statusText);
      }

      return res.json();
    }
  };

  const uploadDocument = async (file, title) => {
    const existsRes = await fetch(
      `/api/documents/query/?title=${encodeURIComponent(title)}`
    );
    if (existsRes.ok) {
      const data = await existsRes.json();
      return data.id;
    }

    const docResource = await postTo("documents", {
      data: {
        title,
      },
      file: pdfs[file],
    });

    return docResource.id;
  };

  let totalCount = 0;
  let numUploaded = 0;
  for (const issueSpec of importSpec) {
    totalCount += issueSpec.articles.length;
  }

  const getPublication = memoize((title) => {
    return postTo("publications", {
      json: { parent: ARCHIVE_ROOT, title, tags: [] },
    });
  });

  let progress = {
    current: 1,
    total: 0,
    currentIssueName: "",
    currentIssue: 1,
    totalIssues: importSpec.length,
    log: [],
    errors: [],
  };

  for (const issueSpec of importSpec) {
    progress.total += issueSpec.articles.length;
  }

  for (const issueSpec of importSpec) {
    const issueLogName = `${issueSpec.publication.value} ${issueSpec.title}`;

    try {
      progress = {
        ...progress,
        currentIssueName: issueLogName,
      };
      onProgress(progress);

      const publication = await getPublication(issueSpec.publication.value);

      const coverTitle = [
        issueSpec.publication.value,
        issueSpec.title,
        "Cover",
      ].join(" ");

      const coverDoc =
        issueSpec.cover.value &&
        (await uploadDocument(issueSpec.cover.value, coverTitle));

      const issue = await postTo("issues/multi", {
        json: {
          parent: publication.id,
          title: issueSpec.title,
          publication_date: issueSpec.publication_date.value,
          issue: issueSpec.issue_no.value,
          volume: issueSpec.volume_no.value,
          issue_cover: coverDoc,
          tags: [],
        },
      });

      for (const articleSpec of issueSpec.articles) {
        const articleLogName = `${issueLogName} ${articleSpec.title.value}`;

        try {
          const docTitle = [
            issueSpec.publication.value,
            issueSpec.title,
            articleSpec.title.value,
          ].join(" ");

          const articleDoc = await uploadDocument(
            articleSpec.pdf.value,
            docTitle
          );

          await postTo("articles", {
            json: {
              title: articleSpec.title.value,
              parent: issue.id,
              article_content: articleDoc,
              author_name: articleSpec.author.value,
              tags: [],
            },
          });

          progress = {
            ...progress,
            current: progress.current + 1,
            log: [`Uploaded ${articleLogName}`, ...progress.log],
          };
          onProgress(progress);
        } catch (error) {
          console.error(error);
          const logItem = `Failed to upload article: ${articleLogName}`;

          progress = {
            ...progress,
            current: progress.current + 1,
            errors: [...progress.errors, logItem],
            log: [logItem, ...progress.log],
          };
          onProgress(progress);
        }
      }
      progress = {
        ...progress,
        currentIssue: progress.currentIssue + 1,
      };
      onProgress(progress);
    } catch (error) {
      console.error(error);
      const logItem = `Failed to upload issue: ${issueLogName}`;

      progress = {
        ...progress,
        currentIssue: progress.currentIssue + 1,
        errors: [...progress.errors, logItem],
        log: [logItem, ...progress.log],
      };
      onProgress(progress);
    }
  }
};

const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

const readFileAsText = (file) =>
  new Promise((resolve, reject) => {
    let reader = new FileReader();

    reader.addEventListener("load", (e) => {
      resolve(e.target.result);
    });

    reader.addEventListener("error", reject);

    reader.readAsText(file);
  });

render(<Uploader />, document.getElementById("upload-widget"));
