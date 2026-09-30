"use client";
import { DocumentList } from "@/components/DocumentList";
import { FileUpload } from "@/components/FileUpload";
import { EmptyState, ErrorState, LoadingState } from "@/components/States";
import { useDocuments } from "@/components/useDocuments";
import { api } from "@/lib/api";
import { useToast } from "@/lib/providers";
import type { DocumentItem } from "@/lib/types";

export default function DocumentsPage() {
  const { docs, loading, error, reload } = useDocuments();
  const toast = useToast();
  const remove = async (d: DocumentItem) => {
    try { await api.deleteDocument(d.id); toast("success", `${d.filename} and its chunks were deleted.`); await reload(); }
    catch (e) { toast("error", e instanceof Error ? e.message : "Could not delete the document."); }
  };
  return (
    <div className="page">
      <h1>Documents</h1>
      <p className="muted">PDFs you have uploaded. Deleting a document also removes its chunks and embeddings.</p>
      <div className="panel"><FileUpload variant="drop" onUploaded={reload} /></div>
      <div className="panel">
        {loading ? <LoadingState label="Loading documents…" /> : error ? <ErrorState message={error} onRetry={reload} />
          : docs.length === 0 ? <EmptyState icon="file" title="No documents yet">Upload a PDF to build your knowledge base.</EmptyState>
          : <DocumentList docs={docs} onDelete={remove} />}
      </div>
    </div>
  );
}
