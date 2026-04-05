import Header from '../components/Header';
import Chatbot from '../components/Chatbot';

export default function Home({ user, isDark, setIsDark, onLogout }) {
  return (
    <div className={`app ${isDark ? 'dark' : 'light'}`}>
      <div className="app-container">
        <Header isDark={isDark} setIsDark={setIsDark} user={user} onLogout={onLogout} />
        <Chatbot user={user} isDark={isDark} />
      </div>
    </div>
  );
}