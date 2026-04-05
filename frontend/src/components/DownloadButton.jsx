export default function DownloadButton({ url }) {
  if (!url) return null;

  const handleDownload = async () => {
    try {
      const res = await fetch(url);
      const blob = await res.blob();
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = `echopersona-story-${Date.now()}.mp3`;
      a.click();
    } catch {
      window.open(url, '_blank');
    }
  };

  return (
    <button className="download-btn" onClick={handleDownload}>
      ↓ Download Story
    </button>
  );
}