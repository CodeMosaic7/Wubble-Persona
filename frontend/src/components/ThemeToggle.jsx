
export default function ThemeToggle({ isDark, setIsDark }) {
  return (
    <button
      className="theme-toggle"
      onClick={() => setIsDark(!isDark)}
      title="Toggle theme"
    >
      {isDark ? '☀' : '☽'}
    </button>
  );
}