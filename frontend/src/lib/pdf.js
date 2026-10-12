// Local PDF fallback for consultant report export.
const PAGE_WIDTH = 595.28; // A4 portrait, points
const PAGE_HEIGHT = 841.89;
const MARGIN_X = 52;
const MARGIN_TOP = 96;
const MARGIN_BOTTOM = 64;
const BODY_SIZE = 10;
const TITLE_SIZE = 18;
const HEADING_SIZE = 12;

const BODY_FONT = "/F1";
const BOLD_FONT = "/F2";

// Escape PDF literal special characters.
function escapePdfText(value) {
  return String(value ?? "")
    .replace(/\\/g, "\\\\")
    .replace(/\(/g, "\\(")
    .replace(/\)/g, "\\)");
}

function wrapText(text, maxChars) {
  const words = String(text ?? "").split(/\s+/).filter(Boolean);
  if (words.length === 0) return [""];
  const lines = [];
  let current = "";
  words.forEach((word) => {
    // Split long tokens so lines never overflow.
    let token = word;
    while (token.length > maxChars) {
      if (current) {
        lines.push(current);
        current = "";
      }
      lines.push(token.slice(0, maxChars));
      token = token.slice(maxChars);
    }
    if (!current.length) {
      current = token;
    } else if (`${current} ${token}`.length <= maxChars) {
      current = `${current} ${token}`;
    } else {
      lines.push(current);
      current = token;
    }
  });
  if (current) lines.push(current);
  return lines;
}

// Build a PDF file as a Blob.
export function buildPdfBlob(doc = {}) {
  const { title = "Report", subtitle = "", meta = [], sections = [], footer = "" } = doc;

  // Flatten the document into drawable rows.
  const rows = [
    { text: "MYSTICLENS  •  SPIRITUAL INTELLIGENCE", font: BOLD_FONT, size: 8, gapBefore: 0, color: "0.35 0.35 0.55" },
    { text: title, font: BOLD_FONT, size: TITLE_SIZE, gapBefore: 8 },
  ];
  if (subtitle) rows.push({ text: subtitle, font: BODY_FONT, size: 11, gapBefore: 6 });
  meta.forEach((line) => rows.push({ text: line, font: BODY_FONT, size: 9, gapBefore: 2, color: "0.4 0.45 0.55" }));
  rows.push({ text: "─".repeat(72), font: BODY_FONT, size: 8, gapBefore: 8, color: "0.71 0.32 0.04" });

  sections.forEach((section) => {
    if (section.heading) {
      rows.push({ text: String(section.heading).toUpperCase(), font: BOLD_FONT, size: HEADING_SIZE, gapBefore: 14 });
    }
    (section.lines || []).forEach((line) => {
      const text = String(line ?? "").trim();
      if (!text) return;
      const isBullet = text.startsWith("• ") || text.startsWith("- ") || /^\d+[.)] /.test(text);
      wrapText(isBullet ? text : text, isBullet ? 90 : 94).forEach((wrapped, i) => {
        rows.push({
          text: i === 0 ? wrapped : `   ${wrapped}`,
          font: BODY_FONT,
          size: BODY_SIZE,
          gapBefore: i === 0 ? 3 : 1,
        });
      });
    });
  });

  if (footer) {
    rows.push({ text: "─".repeat(72), font: BODY_FONT, size: 8, gapBefore: 14, color: "0.79 0.83 0.88" });
    wrapText(footer, 94).forEach((wrapped) => {
      rows.push({ text: wrapped, font: BODY_FONT, size: 8, gapBefore: 1, color: "0.4 0.45 0.55" });
    });
  }

  // Paginate by vertical space.
  const usableHeight = PAGE_HEIGHT - MARGIN_TOP - MARGIN_BOTTOM - 30; // reserve footer
  const rowHeight = (row) => (row.size >= 14 ? 24 : row.size >= 12 ? 18 : 14) + (row.gapBefore ? Math.min(row.gapBefore, 10) : 0);
  const pages = [];
  let current = [];
  let used = 0;
  rows.forEach((row) => {
    const height = rowHeight(row);
    if (used + height > usableHeight && current.length) {
      pages.push(current);
      current = [];
      used = 0;
    }
    current.push(row);
    used += height;
  });
  if (current.length) pages.push(current);
  if (pages.length === 0) pages.push([{ text: title, font: BOLD_FONT, size: TITLE_SIZE, gapBefore: 0 }]);

  const encoder = new TextEncoder();
  const chunks = [];
  let length = 0;
  const push = (text) => {
    const bytes = encoder.encode(text);
    chunks.push(bytes);
    length += bytes.length;
  };
  const offsets = {};
  const object = (num, body) => {
    offsets[num] = length;
    push(`${num} 0 obj\n${body}\nendobj\n`);
  };

  push("%PDF-1.4\n");
  object(1, "<< /Type /Catalog /Pages 2 0 R >>");

  // Fixed font ids: 3 regular, 4 bold.
  const pageIds = pages.map((_, index) => 5 + index * 2);
  const kids = pageIds.map((id) => `${id} 0 R`).join(" ");
  object(2, `<< /Type /Pages /Kids [${kids}] /Count ${pages.length} >>`);
  object(3, "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>");
  object(4, "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>");

  pages.forEach((rowsOnPage, pageIndex) => {
    const pageId = pageIds[pageIndex];
    const contentId = pageId + 1;
    const ops = ["BT"];
    let cursorY = PAGE_HEIGHT - MARGIN_TOP;
    rowsOnPage.forEach((row) => {
      if (row.gapBefore) cursorY -= Math.min(row.gapBefore, 10);
      const color = row.color || "0.12 0.16 0.23";
      ops.push(`${color} rg`);
      ops.push(
        `${row.font} ${row.size} Tf 1 0 0 1 ${MARGIN_X} ${cursorY.toFixed(2)} Tm (${escapePdfText(row.text)}) Tj`
      );
      cursorY -= row.size >= 14 ? 24 : row.size >= 12 ? 18 : 14;
    });
    // Footer with page number and brand.
    ops.push("0.58 0.63 0.72 rg");
    ops.push(`${BODY_FONT} 7 Tf 1 0 0 1 ${MARGIN_X} 44.00 Tm (MysticLens  •  Interpretive guidance only — not medical, financial or legal advice.) Tj`);
    const pageLabel = `Page ${pageIndex + 1} of ${pages.length}`;
    ops.push(`${BODY_FONT} 7 Tf 1 0 0 1 ${(PAGE_WIDTH - MARGIN_X - 90).toFixed(2)} 44.00 Tm (${escapePdfText(pageLabel)}) Tj`);
    ops.push("ET");
    const stream = ops.join("\n");

    object(
      pageId,
      `<< /Type /Page /Parent 2 0 R /MediaBox [0 0 ${PAGE_WIDTH} ${PAGE_HEIGHT}] ` +
        `/Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> /Contents ${contentId} 0 R >>`
    );
    offsets[contentId] = length;
    const streamBytes = encoder.encode(stream).length;
    push(`${contentId} 0 obj\n<< /Length ${streamBytes} >>\nstream\n${stream}\nendstream\nendobj\n`);
  });

  const totalObjects = 4 + pages.length * 2;
  const xrefOffset = length;
  push("xref\n");
  push(`0 ${totalObjects + 1}\n`);
  push("0000000000 65535 f \n");
  for (let num = 1; num <= totalObjects; num += 1) {
    push(`${String(offsets[num] || 0).padStart(10, "0")} 00000 n \n`);
  }
  push(`trailer\n<< /Size ${totalObjects + 1} /Root 1 0 R >>\nstartxref\n${xrefOffset}\n%%EOF`);

  return new Blob(chunks, { type: "application/pdf" });
}

// Trigger a browser download for a Blob.
export function downloadBlob(blob, filename) {
  const url = window.URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  setTimeout(() => window.URL.revokeObjectURL(url), 1000);
}
