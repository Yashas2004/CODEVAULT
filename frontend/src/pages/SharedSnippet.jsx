import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import axios from "axios";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";

const API_BASE = "http://127.0.0.1:8000";

export default function SharedSnippet() {
  const { slug } = useParams();
  const [snippet, setSnippet] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios
      .get(`${API_BASE}/public/snippets/${slug}`)
      .then((res) => setSnippet(res.data))
      .catch(() => setError("This snippet doesn't exist or is no longer shared."))
      .finally(() => setLoading(false));
  }, [slug]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-paper">
        <p className="text-comment font-mono text-sm">loading snippet...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-paper gap-4 px-4">
        <p className="text-danger font-mono text-sm text-center">{error}</p>
        <Link to="/login" className="text-accent underline text-sm">
          Go to CodeVault
        </Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-paper px-4 py-10">
      <div className="max-w-3xl mx-auto space-y-4">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-ink">{snippet.title}</h1>
          <span className="text-sm font-mono text-accent bg-accent/10 border border-accent/30 px-2 py-1 rounded">
            {snippet.language}
          </span>
        </div>

        {snippet.tags && (
          <p>
            {snippet.tags.split(",").filter(Boolean).map((t) => (
              <span
                key={t}
                className="inline-block bg-success/10 text-success font-mono text-xs px-2 py-0.5 rounded mr-2"
              >
                {t.trim()}
              </span>
            ))}
          </p>
        )}

        <SyntaxHighlighter
          language={snippet.language?.toLowerCase() || "text"}
          style={oneDark}
          customStyle={{ borderRadius: "8px", fontSize: "0.875rem", border: "1px solid rgba(139,141,152,0.15)" }}
          showLineNumbers
        >
          {snippet.code}
        </SyntaxHighlighter>

        <p className="text-xs font-mono text-comment text-center pt-4">
          shared via CodeVault
        </p>
      </div>
    </div>
  );
}