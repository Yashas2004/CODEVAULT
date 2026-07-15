import { useEffect, useState } from "react";
import api from "../api";
import { useDebounce } from "../hooks/useDebounce";
import { languageColor } from "../utils/languageColor";
import LoadingTransition from "../components/LoadingTransition";
import { useNavigate } from "react-router-dom";

function SkeletonCard() {
  return (
    <div className="relative bg-surface border border-comment/15 rounded-lg overflow-hidden animate-pulse">
      <div className="absolute left-0 top-0 bottom-0 w-1 bg-comment/20" />
      <div className="pl-5 pr-4 py-4 space-y-3">
        <div className="h-4 w-1/3 bg-surface2 rounded" />
        <div className="h-3 w-16 bg-surface2 rounded" />
        <div className="h-20 w-full bg-surface2 rounded" />
      </div>
    </div>
  );
}

export default function Snippets() {
  const navigate = useNavigate();
  const [snippets, setSnippets] = useState([]);
  const [q, setQ] = useState("");
  const debouncedQ = useDebounce(q, 300);
  const [loading, setLoading] = useState(true);
  const [initialLoad, setInitialLoad] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [deletingId, setDeletingId] = useState(null);
  const [cursor, setCursor] = useState(null);
  const [hasMore, setHasMore] = useState(false);
  const [form, setForm] = useState({ title: "", language: "", code: "", tags: "" });
  const [editingId, setEditingId] = useState(null);
  const [shareUrl, setShareUrl] = useState(null);
  const [copied, setCopied] = useState(false);
  const [idempotencyKey, setIdempotencyKey] = useState(() => crypto.randomUUID());
  const [toasts, setToasts] = useState([]);
  const [showEntryTransition, setShowEntryTransition] = useState(true);

  const showToast = (message) => {
    const id = crypto.randomUUID();
    setToasts(prev => [...prev, { id, message }]);
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 3000);
  };

  const load = async () => {
    setLoading(true);
    const res = await api.get(`/snippets/?q=${debouncedQ}`);
    setSnippets(res.data.items);
    setCursor(res.data.next_cursor);
    setHasMore(res.data.has_more);
    setLoading(false);
    setInitialLoad(false);
  };

  const loadMore = async () => {
    setLoadingMore(true);
    const res = await api.get(`/snippets/?q=${debouncedQ}&cursor=${cursor}`);
    setSnippets(prev => [...prev, ...res.data.items]);
    setCursor(res.data.next_cursor);
    setHasMore(res.data.has_more);
    setLoadingMore(false);
  };

  useEffect(() => { load(); }, [debouncedQ]);

  useEffect(() => {
    const timer = setTimeout(() => setShowEntryTransition(false), 2000);
    return () => clearTimeout(timer);
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("token");
    navigate("/login");
  };

  const handleDelete = async (id) => {
    const snapshot = snippets;
    setSnippets(prev => prev.filter(s => s.id !== id));
    if (editingId === id) cancelEdit();

    try {
      await api.delete(`/snippets/${id}`);
    } catch {
      setSnippets(snapshot);
      showToast("Couldn't delete that snippet — restored.");
    }
  };

  const handleEditClick = (snippet) => {
    setEditingId(snippet.id);
    setForm({
      title: snippet.title,
      language: snippet.language,
      code: snippet.code,
      tags: snippet.tags,
    });
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const cancelEdit = () => {
    setEditingId(null);
    setForm({ title: "", language: "", code: "", tags: "" });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (submitting) return;
    setSubmitting(true);

    if (editingId) {
      const editedId = editingId;
      const previous = snippets.find(s => s.id === editedId);
      setSnippets(prev => prev.map(s => (s.id === editedId ? { ...s, ...form } : s)));
      cancelEdit();

      try {
        await api.put(`/snippets/${editedId}`, form);
      } catch {
        setSnippets(prev => prev.map(s => (s.id === editedId ? previous : s)));
        showToast("Couldn't save your edit — reverted.");
      } finally {
        setSubmitting(false);
      }
      return;
    }

    const tempId = `temp-${crypto.randomUUID()}`;
    const optimisticSnippet = {
      ...form, id: tempId, is_public: false, share_slug: null,
      created_at: new Date().toISOString(),
    };
    setSnippets(prev => [optimisticSnippet, ...prev]);
    const savedForm = form;
    const keyUsed = idempotencyKey;
    cancelEdit();
    setIdempotencyKey(crypto.randomUUID());

    try {
      const res = await api.post("/snippets/", savedForm, {
        headers: { "Idempotency-Key": keyUsed },
      });
      setSnippets(prev => prev.map(s => (s.id === tempId ? res.data : s)));
    } catch {
      setSnippets(prev => prev.filter(s => s.id !== tempId));
      showToast("Couldn't create that snippet — please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleShare = async (snippet) => {
    if (snippet.is_public && snippet.share_slug) {
      setShareUrl(`${window.location.origin}/s/${snippet.share_slug}`);
      return;
    }
    try {
      const res = await api.post(`/snippets/${snippet.id}/share`);
      setSnippets(prev => prev.map(s =>
        s.id === snippet.id ? { ...s, is_public: true, share_slug: res.data.share_slug } : s
      ));
      setShareUrl(`${window.location.origin}/s/${res.data.share_slug}`);
    } catch {
      showToast("Couldn't create a share link.");
    }
  };

  const handleUnshare = async (snippet) => {
    setSnippets(prev => prev.map(s => (s.id === snippet.id ? { ...s, is_public: false } : s)));
    try {
      await api.delete(`/snippets/${snippet.id}/share`);
    } catch {
      setSnippets(prev => prev.map(s => (s.id === snippet.id ? { ...s, is_public: true } : s)));
      showToast("Couldn't unshare — restored.");
    }
  };

  const copyLink = () => {
    navigator.clipboard.writeText(shareUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  if (showEntryTransition) {
    return <LoadingTransition />;
  }

  return (
    <div className="min-h-screen bg-paper grid grid-cols-1 lg:grid-cols-[28%_72%]">

      {/* LEFT PANEL */}
      <aside className="lg:h-screen lg:sticky lg:top-0 lg:overflow-y-auto border-b lg:border-b-0 lg:border-r border-comment/15 p-6 space-y-6">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2 font-mono font-bold text-5xl ">
              <span className="text-accent ">&lt;/&gt;</span>
              <span className="text-ink tracking-tight ">CodeVault</span>
            </div>
            <p className="text-xs font-mono text-comment mt-1.5">Store All your Code Snippets here </p>
          </div>
          <button
            onClick={handleLogout}
            className="text-xs font-mono text-comment hover:text-danger border border-comment/20 hover:border-danger/40 rounded px-2 py-1 transition-colors"
          >
            Logout
          </button>
        </div>

        <div className="text-xs font-mono text-comment">
          {snippets.length} snippet{snippets.length !== 1 ? "s" : ""} shown{hasMore ? "+" : ""}
        </div>

        <div className="flex items-center gap-2 bg-surface border border-comment/20 rounded-lg px-3 py-2 focus-within:ring-2 focus-within:ring-accent/50 focus-within:border-accent/50">
          <span className="font-mono text-accent text-sm select-none">❯</span>
          <input
            className="flex-1 font-mono text-sm outline-none bg-transparent text-ink placeholder:text-comment"
            placeholder="search snippets..."
            value={q}
            onChange={e => setQ(e.target.value)}
          />
        </div>

        <form onSubmit={handleSubmit} className="bg-surface border border-comment/20 rounded-lg p-4 space-y-3">
          {editingId && (
            <div className="flex justify-between items-center bg-accent/10 border border-accent/30 rounded p-2 text-xs">
              <span className="font-mono text-accent">Editing snippet</span>
              <button type="button" onClick={cancelEdit} className="text-comment underline">
                Cancel
              </button>
            </div>
          )}
          <input
            className="border border-comment/20 bg-surface2 text-ink rounded px-3 py-2 w-full text-sm outline-none focus:ring-2 focus:ring-accent/50 placeholder:text-comment"
            placeholder="Title"
            value={form.title} onChange={e => setForm({ ...form, title: e.target.value })}
          />
          <input
            className="border border-comment/20 bg-surface2 text-ink rounded px-3 py-2 w-full text-sm outline-none focus:ring-2 focus:ring-accent/50 placeholder:text-comment"
            placeholder="Language"
            value={form.language} onChange={e => setForm({ ...form, language: e.target.value })}
          />
          <textarea
            className="border border-comment/20 bg-surface2 text-ink rounded px-3 py-2 w-full font-mono text-sm outline-none focus:ring-2 focus:ring-accent/50 placeholder:text-comment"
            rows={5}
            placeholder="Code"
            value={form.code} onChange={e => setForm({ ...form, code: e.target.value })}
          />
          <input
            className="border border-comment/20 bg-surface2 text-ink rounded px-3 py-2 w-full text-sm outline-none focus:ring-2 focus:ring-accent/50 placeholder:text-comment"
            placeholder="Tags (comma separated)"
            value={form.tags} onChange={e => setForm({ ...form, tags: e.target.value })}
          />
          <button
            disabled={submitting}
            className="bg-accent text-paper rounded px-4 py-2 w-full text-sm font-semibold hover:brightness-110 transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {submitting ? (editingId ? "Updating..." : "Saving...") : (editingId ? "Update Snippet" : "Save Snippet")}
          </button>
        </form>
      </aside>

      {/* RIGHT PANEL */}
      <main
        className="p-6 lg:p-10 space-y-4"
        style={{
          backgroundImage:
            "linear-gradient(rgba(139,141,152,0.06) 1px, transparent 1px), linear-gradient(90deg, rgba(139,141,152,0.06) 1px, transparent 1px)",
          backgroundSize: "28px 28px",
        }}
      >
        {initialLoad && loading && (
          <>
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
          </>
        )}

        <div className={`space-y-4 transition-opacity duration-200 ${!initialLoad && loading ? "opacity-50" : "opacity-100"}`}>
          {snippets.map((s, i) => (
            <div
              key={s.id}
              className={`group relative bg-surface border border-comment/15 rounded-lg overflow-hidden transition-shadow hover:shadow-[0_0_0_1px_theme(colors.accent),0_0_20px_-4px_theme(colors.accent)] animate-[fadeIn_0.25s_ease-out] ${typeof s.id === "string" ? "opacity-60" : ""}`}
              style={{ animationDelay: `${Math.min(i, 8) * 30}ms`, animationFillMode: "backwards" }}
            >
              <div
                className="absolute left-0 top-0 bottom-0 w-1"
                style={{ backgroundColor: languageColor(s.language) }}
              />
              <div className="pl-5 pr-4 py-4 space-y-2">
                <div className="flex justify-between items-start gap-3">
                  <div>
                    <h3 className="font-semibold text-ink">{s.title}</h3>
                    <span
                      className="font-mono text-xs font-medium"
                      style={{ color: languageColor(s.language) }}
                    >
                      {s.language}
                    </span>
                    {s.is_public && (
                      <span className="ml-2 font-mono text-xs text-comment">
                        👁 {s.view_count} view{s.view_count !== 1 ? "s" : ""}
                      </span>
                    )}
                  </div>
                  <div className="flex gap-3 text-xs font-mono opacity-0 group-hover:opacity-100 transition-opacity">
                    <button onClick={() => handleEditClick(s)} className="text-accent">Edit</button>
                    {s.is_public ? (
                      <>
                        <button onClick={() => handleShare(s)} className="text-success">Copy Link</button>
                        <button onClick={() => handleUnshare(s)} className="text-comment">Unshare</button>
                      </>
                    ) : (
                      <button onClick={() => handleShare(s)} className="text-accent">Share</button>
                    )}
                    <button
                      onClick={() => handleDelete(s.id)}
                      disabled={deletingId === s.id}
                      className="text-danger disabled:opacity-50"
                    >
                      {deletingId === s.id ? "Deleting..." : "Delete"}
                    </button>
                  </div>
                </div>

                <pre className="bg-surface2 border border-comment/10 rounded p-3 overflow-x-auto text-xs font-mono text-ink">{s.code}</pre>

                {s.tags && (
                  <p>
                    {s.tags.split(",").filter(Boolean).map(t => (
                      <span key={t} className="inline-block bg-success/10 text-success font-mono text-xs px-2 py-0.5 rounded mr-1">
                        {t.trim()}
                      </span>
                    ))}
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>

        {!initialLoad && !loading && snippets.length === 0 && (
          <p className="text-sm font-mono text-comment text-center py-10">
            no snippets match "{debouncedQ}"
          </p>
        )}

        {hasMore && (
          <button
            onClick={loadMore}
            disabled={loadingMore}
            className="w-full border border-comment/20 rounded-lg p-2 text-sm font-mono text-comment hover:text-ink hover:border-accent/40 transition-colors disabled:opacity-50"
          >
            {loadingMore ? "loading..." : "load more"}
          </button>
        )}
      </main>

      {/* Share modal */}
      {shareUrl && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 animate-[fadeIn_0.15s_ease-out]">
          <div className="bg-surface border border-comment/20 p-6 rounded-lg max-w-md w-full mx-4 space-y-4">
            <h3 className="font-mono font-semibold text-lg text-ink">Share this snippet</h3>
            <p className="text-sm text-comment">Anyone with this link can view it — no login required.</p>
            <div className="flex gap-2">
              <input
                readOnly
                value={shareUrl}
                className="border border-comment/20 bg-surface2 text-ink rounded p-2 flex-1 text-sm font-mono"
                onFocus={(e) => e.target.select()}
              />
              <button onClick={copyLink} className="bg-accent text-paper px-3 rounded text-sm font-semibold hover:brightness-110 transition">
                {copied ? "Copied!" : "Copy"}
              </button>
            </div>
            <button onClick={() => setShareUrl(null)} className="text-sm text-comment underline">
              Close
            </button>
          </div>
        </div>
      )}

      {toasts.length > 0 && (
        <div className="fixed bottom-4 right-4 z-50 space-y-2">
          {toasts.map(t => (
            <div
              key={t.id}
              className="bg-surface border border-danger/40 text-ink text-sm font-mono px-4 py-2 rounded-lg shadow-lg animate-[fadeIn_0.2s_ease-out]"
            >
              {t.message}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}