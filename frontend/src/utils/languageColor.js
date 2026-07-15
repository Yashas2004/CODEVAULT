const LANGUAGE_COLORS = {
  javascript: "#E8B339",
  js: "#E8B339",
  typescript: "#5646E8",
  ts: "#5646E8",
  python: "#1C8C5A",
  java: "#D64545",
  html: "#E8674A",
  css: "#5B8DEF",
  sql: "#9B59B6",
  go: "#4FD1C5",
  rust: "#DD6B4E",
  c: "#7A93A6",
  "c++": "#7A93A6",
  cpp: "#7A93A6",
  bash: "#4A4A4A",
  shell: "#4A4A4A",
};

const FALLBACK_PALETTE = ["#5646E8", "#1C8C5A", "#D64545", "#E8674A", "#5B8DEF", "#9B59B6"];

export function languageColor(language = "") {
  const key = language.trim().toLowerCase();
  if (LANGUAGE_COLORS[key]) return LANGUAGE_COLORS[key];
  let hash = 0;
  for (let i = 0; i < key.length; i++) hash = key.charCodeAt(i) + ((hash << 5) - hash);
  return FALLBACK_PALETTE[Math.abs(hash) % FALLBACK_PALETTE.length];
}