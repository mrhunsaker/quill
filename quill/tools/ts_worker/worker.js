/**
 * QUILL Developer Console — TypeScript/JavaScript worker (Node.js).
 *
 * Protocol: single-line JSON on stdin/stdout.
 *
 * Python → Node stdin:
 *   {"type":"execute","id":"req1","source":"await quill.gotoLine(5);"}
 *   {"type":"return","id":"req1","call":"c1","value":null}
 *   {"type":"return","id":"req1","call":"c1","error":"message"}
 *
 * Node → Python stdout:
 *   {"type":"ready"}
 *   {"type":"invoke","id":"req1","call":"c1","method":"gotoLine","args":[5]}
 *   {"type":"output","id":"req1","stream":"log","text":"hello"}
 *   {"type":"done","id":"req1","value":null,"output":""}
 *   {"type":"error","id":"req1","message":"ReferenceError: x is not defined","stack":"..."}
 */

'use strict';

const readline = require('readline');

const rl = readline.createInterface({ input: process.stdin, terminal: false });

// Per-request pending call resolution: call_id -> {resolve, reject}
const pendingCalls = new Map();

// Write one JSON line to stdout
function send(obj) {
  process.stdout.write(JSON.stringify(obj) + '\n');
}

// Send a host invoke and wait for the return message
function invokeHost(reqId, method, args) {
  return new Promise((resolve, reject) => {
    const callId = Math.random().toString(36).slice(2);
    pendingCalls.set(callId, { resolve, reject });
    send({ type: 'invoke', id: reqId, call: callId, method, args });
  });
}

// Build the quill proxy object for one execution
function makeQuill(reqId, outputLines) {
  const proxy = (method) => (...args) => invokeHost(reqId, method, args);
  return {
    insertText:       proxy('insertText'),
    replaceSelection: proxy('replaceSelection'),
    selectedText:     proxy('selectedText'),
    documentText:     proxy('documentText'),
    setDocumentText:  proxy('setDocumentText'),
    gotoLine:         proxy('gotoLine'),
    gotoOffset:       proxy('gotoOffset'),
    runCommand:       proxy('runCommand'),
    commandExists:    proxy('commandExists'),
    announce:         proxy('announce'),
    activeDocument:   proxy('activeDocument'),
    documentStats:    proxy('documentStats'),
    lastAnnouncement: proxy('lastAnnouncement'),
    getText:          proxy('documentText'),
  };
}

// Execute user source in an async context
async function executeSource(reqId, source) {
  const outputLines = [];

  // Captured console
  const consoleCap = {
    log:   (...a) => { const t = a.join(' '); outputLines.push(t); send({ type: 'output', id: reqId, stream: 'log', text: t }); },
    warn:  (...a) => { const t = a.join(' '); outputLines.push(t); send({ type: 'output', id: reqId, stream: 'warn', text: t }); },
    error: (...a) => { const t = a.join(' '); outputLines.push(t); send({ type: 'output', id: reqId, stream: 'error', text: t }); },
  };

  const quill = makeQuill(reqId, outputLines);

  // Wrap in async IIFE so top-level await works
  const wrapped = `(async function(_quill, _console, _setTimeout, _clearTimeout, _AbortController) {
const quill = _quill;
const console = _console;
const setTimeout = _setTimeout;
const clearTimeout = _clearTimeout;
const AbortController = _AbortController;
${source}
})`;

  let fn;
  try {
    fn = eval(wrapped); // eslint-disable-line no-eval
  } catch (err) {
    return { ok: false, message: String(err.message || err), stack: String(err.stack || '') };
  }

  try {
    const result = await fn(quill, consoleCap, setTimeout, clearTimeout, AbortController);
    return { ok: true, value: result === undefined ? null : result, output: outputLines.join('\n') };
  } catch (err) {
    return { ok: false, message: String(err.message || err), stack: String(err.stack || ''), output: outputLines.join('\n') };
  }
}

// In-flight executions: reqId -> true
const inFlight = new Set();

// Dispatch incoming JSON lines
rl.on('line', (line) => {
  line = line.trim();
  if (!line) return;
  let msg;
  try { msg = JSON.parse(line); } catch { return; }

  const type = msg.type;

  if (type === 'execute') {
    const reqId = msg.id;
    const source = msg.source || '';
    inFlight.add(reqId);
    executeSource(reqId, source).then((result) => {
      inFlight.delete(reqId);
      if (result.ok) {
        send({ type: 'done', id: reqId, value: result.value, output: result.output || '' });
      } else {
        send({ type: 'error', id: reqId, message: result.message, stack: result.stack || '', output: result.output || '' });
      }
    });
    return;
  }

  if (type === 'return') {
    const callId = msg.call;
    const entry = pendingCalls.get(callId);
    if (!entry) return;
    pendingCalls.delete(callId);
    if (msg.error !== undefined) {
      entry.reject(new Error(msg.error));
    } else {
      entry.resolve(msg.value !== undefined ? msg.value : null);
    }
    return;
  }
});

rl.on('close', () => {
  process.exit(0);
});

// Signal ready
send({ type: 'ready' });
