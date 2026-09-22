// app/src/components/hud/DiffViewer.tsx
// Renders Ultra responses: prose + fenced code blocks with diff coloring.
// Follows docs/DESIGN.md §3 — code block bg #0D0D0D, JetBrains Mono 12px.

export interface ResponseBlock {
  kind: 'prose' | 'code';
  lang: string;
  content: string;
}

/** Split a model response into prose/code blocks on ``` fences. */
export function parseResponse(text: string): ResponseBlock[] {
  const blocks: ResponseBlock[] = [];
  const fence = /```(\w*)\n([\s\S]*?)(?:```|$)/g;
  let last = 0;
  let m: RegExpExecArray | null;
  while ((m = fence.exec(text)) !== null) {
    if (m.index > last) {
      const prose = text.slice(last, m.index).trim();
      if (prose) blocks.push({ kind: 'prose', lang: '', content: prose });
    }
    blocks.push({ kind: 'code', lang: m[1] || 'text', content: m[2].replace(/\n$/, '') });
    last = m.index + m[0].length;
  }
  const tail = text.slice(last).trim();
  if (tail) blocks.push({ kind: 'prose', lang: '', content: tail });
  if (blocks.length === 0 && text.trim()) {
    blocks.push({ kind: 'prose', lang: '', content: text.trim() });
  }
  return blocks;
}

/** Extract the first ```diff block for Apply Fix. Null when no patch present. */
export function extractPatch(text: string): string | null {
  const m = /```diff\n([\s\S]*?)(?:```|$)/.exec(text);
  return m ? m[1].trim() : null;
}

function CodeBlock({ lang, content }: { lang: string; content: string }) {
  const isDiff = lang === 'diff';
  return (
    <pre className="synapse-card__code">
      {content.split('\n').map((line, i) => {
        let cls = 'diff-ctx';
        if (isDiff) {
          if (line.startsWith('+') && !line.startsWith('+++')) cls = 'diff-add';
          else if (line.startsWith('-') && !line.startsWith('---')) cls = 'diff-del';
          else if (line.startsWith('@@')) cls = 'diff-hunk';
        }
        return (
          <span key={i} className={cls}>
            {line || ' '}
            {'\n'}
          </span>
        );
      })}
    </pre>
  );
}

export function DiffViewer({ text }: { text: string }) {
  const blocks = parseResponse(text);
  return (
    <>
      {blocks.map((b, i) =>
        b.kind === 'code' ? (
          <CodeBlock key={i} lang={b.lang} content={b.content} />
        ) : (
          <p key={i} className="synapse-card__prose">
            {b.content}
          </p>
        ),
      )}
    </>
  );
}
