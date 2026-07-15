export default function LoadingTransition() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-paper gap-4">
      <div className="w-14 h-14 rounded-full border-4 border-success/20 border-t-success animate-spin" />
      <p className="text-sm font-mono text-comment">loading your vault...</p>
    </div>
  );
}