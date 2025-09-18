// Lightweight Markdown -> HTML -> PDF using Edge (print to PDF)
// Requires Windows + Microsoft Edge installed.
// No headless browser download; uses system Edge via command line.

const { execFileSync, spawnSync } = require('child_process');
const { readFileSync, writeFileSync, mkdirSync } = require('fs');
const { resolve, dirname } = require('path');
const os = require('os');
const { marked } = require('marked');

const inFile = resolve(__dirname, '..', 'docs', '评审版-项目说明-初稿.md');
const outPdf = resolve(__dirname, '..', 'docs', '评审版-项目说明-初稿.pdf');
const tempHtml = resolve(os.tmpdir(), `magent_export_${Date.now()}.html`);

function ensureDir(p) { try { mkdirSync(p, { recursive: true }); } catch { /* noop */ } }

function wrapHtml(bodyHtml) {
  const css = readFileSync(resolve(__dirname, '..', 'docs', 'pdf-style.css'), 'utf-8');
  return `<!doctype html><html><head><meta charset="utf-8"><style>${css}</style></head><body>${bodyHtml}</body></html>`;
}

function mdToHtml(md) {
  marked.setOptions({ mangle: false, headerIds: true });
  return marked.parse(md);
}

function printWithEdge(htmlPath, outPath) {
  // Use Edge's print-to-pdf. On recent versions: --headless=new --print-to-pdf
  const edgePaths = [
    'C\\\x3a\\\x5cProgram Files\\\x5cMicrosoft\\\x5cEdge\\\x5cApplication\\\x5cmsedge.exe',
    'C\\\x3a\\\x5cProgram Files (x86)\\\x5cMicrosoft\\\x5cEdge\\\x5cApplication\\\x5cmsedge.exe'
  ];
  let edge = null;
  for (const p of edgePaths) {
    try { execFileSync(p, ['--version'], { stdio: 'ignore' }); edge = p; break; } catch (_) {}
  }
  if (!edge) throw new Error('未找到 Microsoft Edge，可手动安装或调整脚本中的路径。');

  const args = [
    '--headless=new',
    `--print-to-pdf=${outPath}`,
    htmlPath
  ];
  const res = spawnSync(edge, args, { stdio: 'inherit' });
  if (res.status !== 0) throw new Error('Edge 打印 PDF 失败');
}

(function main() {
  const md = readFileSync(inFile, 'utf-8');
  const html = wrapHtml(mdToHtml(md));
  writeFileSync(tempHtml, html, 'utf-8');
  printWithEdge(tempHtml, outPdf);
  console.log(`PDF 已生成: ${outPdf}`);
})();
