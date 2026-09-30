export const fmtDate = (iso: string) =>
  new Date(iso).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
export const fmtSeconds = (ms: number) => `${(ms / 1000).toFixed(1)}s`;
export const preview = (t: string | null, n = 140) =>
  !t ? "" : t.length > n ? `${t.slice(0, n).trimEnd()}…` : t;

export const PDF_MAX = 25 * 1024 * 1024;
export const IMAGE_MAX = 4 * 1024 * 1024; // conservative: vision APIs limit base64 image size
export const IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp", "image/gif"];

export function validatePdf(f: File): string | null {
  if (f.type !== "application/pdf") return "Only PDF files are supported.";
  if (f.size > PDF_MAX) return "PDF is too large (max 25 MB).";
  return null;
}
export function validateImage(f: File): string | null {
  if (!IMAGE_TYPES.includes(f.type)) return "Image format is not supported. Use JPG, PNG, WebP or GIF.";
  if (f.size > IMAGE_MAX) return "Image is too large (max 4 MB).";
  return null;
}
