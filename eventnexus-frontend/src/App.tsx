import { HomePage } from './pages/HomePage';

export default function App() {
  return (
    <div className="min-h-screen flex flex-col">
      <HomePage />

      {/* Footer */}
      <footer className="bg-white border-t border-border-gray py-12 px-6">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-8">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-brand-cta rounded-lg flex items-center justify-center text-white font-bold">E</div>
            <span className="text-xl font-bold text-brand-navy">EventNexus</span>
          </div>
          <div className="flex gap-8 text-sm text-text-body">
            <a href="#" className="hover:text-brand-cta transition-colors">Sobre</a>
            <a href="#" className="hover:text-brand-cta transition-colors">Fontes</a>
            <a href="#" className="hover:text-brand-cta transition-colors">Privacidade</a>
            <a href="#" className="hover:text-brand-cta transition-colors">Termos</a>
          </div>
          <p className="text-xs text-text-body/60">
            © 2026 EventNexus. Dados agregados de fontes oficiais.
          </p>
        </div>
      </footer>
    </div>
  );
}
