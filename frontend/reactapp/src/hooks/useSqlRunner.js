import { useCallback, useState } from "react";

export function useSqlRunner() {
  const [isRunning, setIsRunning] = useState(false);
  const [consoleOutput, setConsoleOutput] = useState([]);
  const [errorLine, setErrorLine] = useState(null);

  const addResultEntry = useCallback((content, type = "system", timestamp = new Date()) => {
    setConsoleOutput((prev) => [
      ...prev,
      { id: Date.now() + Math.random(), content, type, timestamp },
    ]);
  }, []);

  const clearConsole = useCallback(() => {
    setConsoleOutput([]);
    setErrorLine(null);
  }, []);

  const runQuery = async () => {
    if (isRunning) return;
    setIsRunning(true);
    setErrorLine(null);
    addResultEntry("SQL execution is not connected yet. Phase 4 will run queries against an isolated project database.", "system");
    setIsRunning(false);
  };

  const stopQuery = () => {
    setIsRunning(false);
    addResultEntry("No query is currently running.", "system");
  };

  return {
    isLoading: false,
    isRunning,
    waitingForInput: false,
    consoleOutput,
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
