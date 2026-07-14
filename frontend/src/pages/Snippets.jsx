import { useEffect, useState } from "react";
import api from "../api";
import { useDebounce } from "../hooks/useDebounce";

export default function Snippets() {
  const [snippets, setSnippets] = useState([]);
  const [q, setQ] = useState("");
  const debouncedQ = useDebounce(q, 300);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [cursor, setCursor] = useState(null);
  const [hasMore, setHasMore] = useState(false);
  const [form, setForm] = useState({ title: "", language: "", code: "", tags: "" });
  const [editingId, setEditingId] = useState(null);

  const load = async () => {
    setLoading(true);
    const res = await api.get(`/snippets/?q=${debouncedQ}`);
    setSnippets(res.data.items);
    setCursor(res.data.next_cursor);
    setHasMore(res.data.has_more);
    setLoading(false);
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

  const handleDelete = async (id) => {
    await api.delete(`/snippets/${id}`);
    if (editingId === id) cancelEdit();
    load();
  };

  const handleEditClick = (snippet) => {
    setEditingId(snippet.id);
    setForm({
      title: snippet.title,
      language: snippet.language,
      code: snippet.code,
      tags: snippet.tags,
    });
  };

  const cancelEdit = () => {
    setEditingId(null);
    setForm({ title: "", language: "", code: "", tags: "" });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (editingId) {
      await api.put(`/snippets/${editingId}`, form);
    } else {
      await api.post("/snippets/", form);
    }
    cancelEdit();
    load();
  };

  return (
    <div className="max-w-3xl mx-auto mt-10 space-y-6">
      <input className="border p-2 w-full" placeholder="Search snippets..."
        value={q} onChange={e => setQ(e.target.value)} />

      <form onSubmit={handleSubmit} className="space-y-2 border p-4">
        {editingId && (
          <div className="flex justify-between items-center bg-yellow-50 border border-yellow-200 p-2 text-sm">
            <span>Editing snippet</span>
            <button type="button" onClick={cancelEdit} className="text-gray-600 underline">
              Cancel
            </button>
          </div>
        )}
        <input className="border p-2 w-full" placeholder="Title"
          value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} />
        <input className="border p-2 w-full" placeholder="Language"
          value={form.language} onChange={e => setForm({ ...form, language: e.target.value })} />
        <textarea className="border p-2 w-full font-mono" placeholder="Code"
          value={form.code} onChange={e => setForm({ ...form, code: e.target.value })} />
        <input className="border p-2 w-full" placeholder="Tags (comma separated)"
          value={form.tags} onChange={e => setForm({ ...form, tags: e.target.value })} />
        <button className="bg-black text-white p-2 w-full">
          {editingId ? "Update Snippet" : "Save Snippet"}
        </button>
      </form>

      <div className="space-y-3">
        {loading && <p className="text-sm text-gray-400">Searching...</p>}

        {snippets.map(s => (
          <div key={s.id} className="border p-3">
            <div className="flex justify-between items-start">
                <h3 className="font-bold">{s.title} <span className="text-sm text-gray-500">({s.language})</span></h3>
                <div className="space-x-3">
                  <button onClick={() => handleEditClick(s)} className="text-blue-500 text-sm">Edit</button>
                  <button onClick={() => handleDelete(s.id)} className="text-red-500 text-sm">Delete</button>
                </div>
            </div>
            <pre className="bg-gray-100 p-2 overflow-x-auto text-sm">{s.code}</pre>
            <p className="text-xs text-gray-500">{s.tags}</p>
          </div>
        ))}
      </div>
      {hasMore && (
        <button
          onClick={loadMore}
          disabled={loadingMore}
          className="w-full border p-2 text-sm text-gray-600 hover:bg-gray-50 disabled:opacity-50"
        >
          {loadingMore ? "Loading..." : "Load more"}
        </button>
      )}
    </div>
  );
}