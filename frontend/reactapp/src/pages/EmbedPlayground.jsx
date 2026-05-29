import { useState, useRef, useEffect } from "react";
import { useParams } from "react-router-dom";
import { Play, Square, Terminal, GripVertical, Pencil, Eraser, Highlighter, RotateCcw, RotateCw, Trash2, Eye, EyeOff, RefreshCw } from "lucide-react";
import Anser from "anser";

// CodeMirror
import CodeMirror from "@uiw/react-codemirror";
import { sql } from "@codemirror/lang-sql";
import { oneDark } from "@codemirror/theme-one-dark";
import { StateField, StateEffect } from "@codemirror/state";
import { Decoration, EditorView } from "@codemirror/view";

// API
import api from "../../axiosConfig";

// Hooks
import { useSqlRunner } from "../hooks/useSqlRunner";
import { useLocalCanvas } from "../hooks/useLocalCanvas";

// Error line decoration
const errorLineDeco = Decoration.line({ class: "cm-error-line" });
const addErrorEffect = StateEffect.define();
const removeErrorEffect = StateEffect.define();
const errorLineField = StateField.define({
    create() { return Decoration.none; },
    update(value, tr) {
        value = value.map(tr.changes);
        for (let e of tr.effects) {
            if (e.is(addErrorEffect)) value = Decoration.set([errorLineDeco.range(tr.state.doc.line(e.value).from)]);
            else if (e.is(removeErrorEffect)) value = Decoration.none;
        }
        return value;
    },
    provide: f => EditorView.decorations.from(f)
});

export default function EmbedPlayground() {
    const { token } = useParams();
    const [code, setCode] = useState("-- Loading snippet...");
    const [projectName, setProjectName] = useState("Loading...");
    const [isLoadingSnippet, setIsLoadingSnippet] = useState(true);
    const [showConsole, setShowConsole] = useState(true);
    const [isMobile, setIsMobile] = useState(false);
    const [editorKey, setEditorKey] = useState(0);

    // Store original snippet code for the restart button
    const originalCodeRef = useRef(null);

    // Console width
    const [consoleWidth, setConsoleWidth] = useState(384);
    const [isDragging, setIsDragging] = useState(false);
    const dragStartX = useRef(0);
    const dragStartWidth = useRef(0);

    // Refs
    const editorViewRef = useRef(null);
    const consoleScrollRef = useRef(null);
    const inputContainerRef = useRef(null);

    // Hooks
    const runner = useSqlRunner();
    const canvas = useLocalCanvas();

    useEffect(() => {
        const style = document.createElement('style');
        style.textContent = `
      .scrollbar-hide::-webkit-scrollbar { display: none; }
      .scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
      .cm-error-line { background-color: rgba(255, 0, 0, 0.2); }
    `;
        document.head.appendChild(style);
        return () => document.head.removeChild(style);
    }, []);

    // Detect mobile
    useEffect(() => {
        const checkMobile = () => setIsMobile(window.innerWidth < 768);
        checkMobile();
        window.addEventListener('resize', checkMobile);
        return () => window.removeEventListener('resize', checkMobile);
    }, []);

    // Fetch snippet on mount
    useEffect(() => {
        if (token) {
            const fetchSnippet = async () => {
                setIsLoadingSnippet(true);
                try {
                    const res = await api.get(`/api/public/snippet/${token}/`);
                    const snippetCode = res.data.code || "-- No content in this project";
                    originalCodeRef.current = snippetCode;
                    setCode(snippetCode);
                    setProjectName(res.data.name || "Snippet");
                    setEditorKey(k => k + 1);
                } catch (err) {
                    console.error("Failed to load snippet", err);
                    const errCode = "-- Error: Could not load snippet. It may be invalid or expired.";
                    setCode(errCode);
                    setProjectName("Error Loading");
                    setEditorKey(k => k + 1);
                } finally {
                    setIsLoadingSnippet(false);
                }
            };
            fetchSnippet();
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [token]);

    // Auto-scroll console
    useEffect(() => {
        if (consoleScrollRef.current) {
            consoleScrollRef.current.scrollTop = consoleScrollRef.current.scrollHeight;
        }
    }, [runner.consoleOutput]);

    // Error line decoration
    useEffect(() => {
        if (runner.errorLine) {
            editorViewRef.current?.dispatch({ effects: addErrorEffect.of(runner.errorLine) });
        } else {
            editorViewRef.current?.dispatch({ effects: removeErrorEffect.of() });
        }
    }, [runner.errorLine]);

    // Drawing undo/redo shortcuts
    useEffect(() => {
        const handleKeyDown = (e) => {
            const isCtrl = e.ctrlKey || e.metaKey;

            if (isCtrl && !e.shiftKey && e.key.toLowerCase() === 'z') {
                if (canvas.drawingMode !== 'none') {
                    e.preventDefault(); e.stopPropagation();
                    canvas.undo();
                }
            }

            const isCtrlY = isCtrl && e.key.toLowerCase() === 'y';
            const isCtrlShiftZ = isCtrl && e.shiftKey && e.key.toLowerCase() === 'z';

            if (isCtrlY || isCtrlShiftZ) {
                if (canvas.drawingMode !== 'none') {
                    e.preventDefault(); e.stopPropagation();
                    canvas.redo();
                }
            }
        };
        window.addEventListener('keydown', handleKeyDown, { capture: true });
        return () => window.removeEventListener('keydown', handleKeyDown, { capture: true });
    }, [canvas.drawingMode, canvas.undo, canvas.redo]);

    const handleMouseDown = (e) => {
        setIsDragging(true);
        dragStartX.current = e.clientX;
        dragStartWidth.current = consoleWidth;
        e.preventDefault();
    };

    useEffect(() => {
        const handleMouseMove = (e) => {
            if (!isDragging) return;
            const deltaX = dragStartX.current - e.clientX;
            const newWidth = Math.max(200, Math.min(800, dragStartWidth.current + deltaX));
            setConsoleWidth(newWidth);
        };
        const handleMouseUp = () => setIsDragging(false);

        if (isDragging) {
            document.addEventListener('mousemove', handleMouseMove);
            document.addEventListener('mouseup', handleMouseUp);
            document.body.style.cursor = 'ew-resize';
            document.body.style.userSelect = 'none';
        }
        return () => {
            document.removeEventListener('mousemove', handleMouseMove);
            document.removeEventListener('mouseup', handleMouseUp);
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
        };
    }, [isDragging]);

    return (
        <div className="h-screen bg-slate-850 text-gray-100 flex flex-col overflow-hidden">

            {/* HEADER */}
            <div className="border-b border-gray-700 bg-gray-850 flex-shrink-0">
                <div className="flex items-center justify-between px-3 py-2 gap-2">

                    <div className="flex items-center space-x-2 flex-shrink-0">
                        <div className="flex items-center gap-2 md:gap-3">
                            <div className="relative bg-gradient-to-br from-gray-800 to-gray-900 p-1.5 rounded-xl border border-gray-700/50">
                                <img src="/sqltogether.svg" alt="Icon" className="h-5 w-5 md:h-6 md:w-6" />
                            </div>
                            <h1 className="text-base md:text-lg font-bold bg-clip-text hidden sm:block">SQLTogether</h1>
                        </div>
                    </div>

                    {/* RIGHT */}
                    <div className="flex items-center space-x-2 flex-shrink-0">
                        {/* Drawing controls (desktop only) */}
                        <div className="hidden md:flex items-center space-x-1 p-1 bg-gray-700 rounded-lg">
                            <input type="color" value={canvas.drawColor} onChange={e => canvas.setDrawColor(e.target.value)} className="w-7 h-7 p-0.5 bg-transparent border-none cursor-pointer hover:bg-gray-600 rounded transition-colors" />
                            <button onClick={() => canvas.setDrawingMode(canvas.drawingMode === 'pen' ? 'none' : 'pen')} className={`p-1.5 rounded ${canvas.drawingMode === 'pen' ? 'bg-blue-500 text-white' : 'hover:bg-gray-600'}`}><Pencil className="h-3.5 w-3.5" /></button>
                            <button onClick={() => canvas.setDrawingMode(canvas.drawingMode === 'highlight' ? 'none' : 'highlight')} className={`p-1.5 rounded ${canvas.drawingMode === 'highlight' ? 'bg-blue-500 text-white' : 'hover:bg-gray-600'}`}><Highlighter className="h-3.5 w-3.5" /></button>
                            <button onClick={() => canvas.setDrawingMode(canvas.drawingMode === 'erase' ? 'none' : 'erase')} className={`p-1.5 rounded ${canvas.drawingMode === 'erase' ? 'bg-blue-500 text-white' : 'hover:bg-gray-600'}`}><Eraser className="h-3.5 w-3.5" /></button>
                            <div className="w-px h-4 bg-gray-600 mx-0.5"></div>
                            <button onClick={canvas.undo} disabled={!canvas.canUndo} className="p-1.5 hover:bg-gray-600 rounded disabled:opacity-30 text-gray-300"><RotateCcw className="h-3.5 w-3.5" /></button>
                            <button onClick={canvas.redo} disabled={!canvas.canRedo} className="p-1.5 hover:bg-gray-600 rounded disabled:opacity-30 text-gray-300"><RotateCw className="h-3.5 w-3.5" /></button>
                            <div className="w-px h-4 bg-gray-600 mx-0.5"></div>
                            <button onClick={() => canvas.setShowDrawings(!canvas.showDrawings)} className="p-1.5 hover:bg-gray-600 rounded text-gray-300">{canvas.showDrawings ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}</button>
                            <button onClick={canvas.clearDrawings} className="p-1.5 hover:bg-red-500/50 rounded text-red-400"><Trash2 className="h-3.5 w-3.5" /></button>
                        </div>

                        <button
                            onClick={() => setShowConsole(!showConsole)}
                            className={`p-1.5 rounded-lg ${showConsole ? 'bg-blue-600' : 'bg-gray-700'} hover:bg-gray-600 text-gray-300`}
                            title={showConsole ? 'Hide Results' : 'Show Results'}
                        >
                            <Terminal className="h-4 w-4" />
                        </button>

                        {/* Restart button */}
                        {originalCodeRef.current && (
                            <button
                                onClick={() => {
                                    setCode(originalCodeRef.current);
                                    setEditorKey(k => k + 1);
                                    runner.clearConsole();
                                    runner.setErrorLine(null);
                                }}
                                className="p-1.5 rounded-lg bg-gray-700 hover:bg-gray-600 text-gray-300 transition-colors"
                                title="Restart — reset to original snippet"
                            >
                                <RefreshCw className="h-4 w-4" />
                            </button>
                        )}

                        {runner.isLoading ? (
                            <div className="flex items-center space-x-2 text-yellow-400">
                                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-yellow-400"></div>
                                <span className="text-xs hidden sm:inline">Loading...</span>
                            </div>
                        ) : runner.isRunning ? (
                            <button onClick={runner.stopQuery} className="flex items-center space-x-1 px-2 py-1.5 bg-red-600 rounded-lg hover:bg-red-700 transition-colors text-sm"><Square className="h-4 w-4" /></button>
                        ) : (
                            <button
                                onClick={() => { setShowConsole(true); runner.runQuery(code); }}
                                disabled={isLoadingSnippet}
                                className="flex items-center space-x-1 px-2 py-1.5 bg-green-600 rounded-lg hover:bg-green-700 disabled:bg-gray-700 disabled:cursor-not-allowed transition-colors text-sm"
                            >
                                <Play className="h-4 w-4" />
                            </button>
                        )}
                    </div>
                </div>
            </div>

            {/* MAIN BODY */}
            <div className={`flex ${isMobile ? 'flex-col' : 'flex-row'} flex-1 min-h-0`}>

                {/* EDITOR AREA */}
                <div className={`flex ${isMobile ? 'flex-1 min-h-0' : 'flex-1'} flex-col ${isMobile ? 'border-b' : 'border-r'} border-gray-700 min-w-0 relative`}>
                    <div className="bg-gray-800 px-3 md:px-4 py-2 border-b border-gray-700 flex items-center justify-between z-20 flex-shrink-0">
                        <h2 className="text-xs md:text-sm font-medium text-gray-300">query.sql</h2>
                        <span className="text-sm font-medium text-gray-400 truncate max-w-[200px]">{projectName}</span>
                    </div>

                    <div className="flex-1 overflow-auto scrollbar-hide relative min-h-0" ref={canvas.containerRef}>
                        {/* Loading Overlay */}
                        {isLoadingSnippet && (
                            <div className="absolute inset-0 z-50 bg-gray-900 flex items-center justify-center">
                                <div className="flex flex-col items-center">
                                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mb-2"></div>
                                    <p className="text-gray-400 text-sm">Loading Snippet...</p>
                                </div>
                            </div>
                        )}

                        {/* CANVAS OVERLAY */}
                        <canvas
                            ref={canvas.canvasRef}
                            {...canvas.handlers}
                            className="absolute inset-0 z-10 w-full h-full"
                            style={{
                                pointerEvents: canvas.drawingMode === 'none' ? 'none' : 'auto',
                                cursor: canvas.drawingMode === 'none' ? 'default' : 'crosshair'
                            }}
                        />

                        <CodeMirror
                            key={editorKey}
                            value={code}
                            height="100%"
                            className="h-full text-sm"
                            theme={oneDark}
                            extensions={[sql(), errorLineField]}
                            onChange={(value) => {
                                setCode(value);
                                if (runner.errorLine) runner.setErrorLine(null);
                            }}
                            onCreateEditor={(view) => { editorViewRef.current = view; }}
                            basicSetup={{
                                lineNumbers: true, foldGutter: true, dropCursor: false, allowMultipleSelections: false, indentOnInput: true, bracketMatching: true, closeBrackets: true, autocompletion: true, highlightSelectionMatches: true, searchKeymap: true,
                            }}
                        />
                    </div>
                </div>

                {/* CONSOLE AREA */}
                <div className={`${!showConsole ? 'hidden' : 'flex'} ${isMobile ? 'w-full flex-1 min-h-0' : 'flex-shrink-0'}`}>
                    {!isMobile && (
                        <div className={`w-1 bg-gray-700 hover:bg-blue-500 cursor-ew-resize flex items-center justify-center group transition-colors duration-200 ${isDragging ? 'bg-blue-500' : ''}`} onMouseDown={handleMouseDown}>
                            <GripVertical className="h-4 w-4 text-gray-500 opacity-0 group-hover:opacity-100 transition-opacity duration-200" />
                        </div>
                    )}

                    <div className="flex flex-col bg-gray-850 h-full" style={{ width: isMobile ? '100%' : `${consoleWidth}px` }}>
                        <div className="bg-gray-800 px-3 md:px-4 py-2 border-b border-gray-700 flex items-center justify-between flex-shrink-0">
                            <div className="flex items-center space-x-2">
                                <Terminal className="h-4 w-4 text-gray-400" />
                                <h2 className="text-xs md:text-sm font-medium text-gray-300">Results</h2>
                            </div>
                            <div className="flex items-center">
                                <button onClick={runner.clearConsole} className="p-1 hover:bg-gray-700 rounded text-gray-400 hover:text-red-400" title="Clear Results">
                                    <Trash2 className="h-4 w-4" />
                                </button>
                            </div>
                        </div>

                        <div ref={consoleScrollRef} className="flex-1 p-3 md:p-4 overflow-y-auto bg-gray-900 font-mono text-xs md:text-sm space-y-1 scrollbar-hide min-h-0" style={{ scrollbarWidth: 'none' }}>
                            {runner.consoleOutput.length === 0 ? (
                                <div className="text-gray-500 italic">Query results will appear here after Phase 4 connects SQL execution.</div>
                            ) : (
                                runner.consoleOutput.map(e => (
                                    <div key={e.id} className="flex items-start space-x-2 py-1">
                                        <span className="text-gray-500 text-xs mt-0.5 min-w-[60px]">
                                            {e.timestamp.toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                                        </span>
                                        <span className="text-xs mt-0.5">
                                            {e.type === 'error' ? '❌' : e.type === 'input' ? '▶️' : e.type === 'system' ? '⚙️' : ''}
                                        </span>
                                        <div className={`flex-1 whitespace-pre-wrap break-words font-mono text-sm 
                      ${e.type === 'error' ? 'text-red-400' :
                                                e.type === 'input' ? 'text-blue-400' :
                                                    e.type === 'system' ? 'text-yellow-400' :
                                                        'text-gray-100'}`}
                                            dangerouslySetInnerHTML={{
                                                __html: Anser.ansiToHtml(e.content.replace(/</g, "&lt;").replace(/>/g, "&gt;"))
                                            }}
                                        />
                                    </div>
                                ))
                            )}
                        </div>

                        <div className="flex-shrink-0" ref={inputContainerRef} />
                    </div>
                </div>
            </div>
        </div>
    );
}
