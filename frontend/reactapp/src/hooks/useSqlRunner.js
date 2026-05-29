import { useCallback, useState } from "react";
import api from "../../axiosConfig";

export function useSqlRunner(defaultProjectId = null) {
  const [isRunning, setIsRunning] = useState(false);
  const [consoleOutput, setConsoleOutput] = useState([]);
  const [errorLine, setErrorLine] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [history, setHistory] = useState([]);
  const [abortController, setAbortController] = useState(null);

  const addResultEntry = useCallback((content, type = "system", timestamp = new Date()) => {
    setConsoleOutput((prev) => [
      ...prev,
      { id: Date.now() + Math.random(), content, type, timestamp },
    ]);
  }, []);

  const clearConsole = useCallback(() => {
    setConsoleOutput([]);
    setResult(null);
    setError(null);
    setErrorLine(null);
  }, []);

  const loadHistory = useCallback(async (projectId) => {
    if (!projectId) return;
    try {
      const response = await api.get(`/api/projects/${projectId}/query-history/?limit=20`);
      setHistory(response.data.queries || []);
    } catch (err) {
      console.error("Failed to load query history", err);
    }
  }, []);

  const runQuery = async (payload) => {
    if (isRunning) return;
    const sql = typeof payload === "string" ? payload : payload?.sql;
    const projectId = payload?.projectId || defaultProjectId;

    if (!projectId) {
      setError({ error_type: "missing_project", error_message: "Open a project before running SQL." });
      return;
    }

    setIsRunning(true);
    setErrorLine(null);
    setError(null);
    setResult(null);
    addResultEntry("Running query...", "input");

    const controller = new AbortController();
    setAbortController(controller);

    try {
      const response = await api.post(
        "/api/query/run/",
        { project_id: Number(projectId), sql },
        { signal: controller.signal }
      );

      if (response.data.status === "success") {
        setResult(response.data);
        addResultEntry(`Query completed in ${response.data.execution_time_ms} ms.`, "system");
      } else {
        setError(response.data);
        addResultEntry(response.data.error_message || "Query failed.", "error");
      }
      await loadHistory(projectId);
    } catch (err) {
      if (err.name === "CanceledError" || err.code === "ERR_CANCELED") {
        setError({ error_type: "cancelled", error_message: "Query request cancelled in the browser." });
        addResultEntry("Query request cancelled in the browser.", "system");
      } else {
        const message = err.response?.data?.error_message || err.response?.data?.error || "Could not run query.";
        setError({ error_type: "request_error", error_message: message });
        addResultEntry(message, "error");
      }
      await loadHistory(projectId);
    } finally {
      setAbortController(null);
      setIsRunning(false);
    }
  };

  const stopQuery = () => {
    if (abortController) {
      abortController.abort();
    }
    setIsRunning(false);
  };

  return {
    isLoading: false,
    isRunning,
    waitingForInput: false,
    consoleOutput,
    result,
    error,
    history,
    loadHistory,
    plotSrc: null,
    errorLine,
    inputRef: null,
    runQuery,
    stopQuery,
    submitInput: () => {},
    setConsoleOutput,
    clearConsole,
    setErrorLine,
    setPlotSrc: () => {},
  };
}
