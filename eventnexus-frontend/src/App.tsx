import { HomePage } from './pages/HomePage';

export default function App() {
  return (
    <div className="min-h-screen flex flex-col">
      <HomePage />

      {/* Footer */}
      <footer className="bg-brand-navy text-white py-12 px-6 relative overflow-hidden">
        <div className="absolute inset-0 hero-grid opacity-50" />
        <div className="absolute bottom-0 right-0 w-96 h-96 bg-brand-bright/5 rounded-full blur-[120px]" />

        <div className="max-w-7xl mx-auto relative z-10">
          <div className="flex flex-col md:flex-row justify-between items-center gap-8">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 bg-gradient-to-br from-brand-bright to-brand-cta rounded-xl flex items-center justify-center text-white font-extrabold text-sm shadow-lg shadow-brand-cta/20">
                O
              </div>
              <div>
                <span className="text-lg font-bold tracking-tight">OnEvents</span>
                <span className="text-white/30 text-xs ml-2 font-medium">by Onfly</span>
              </div>
            </div>

            <div className="flex gap-8 text-sm text-white/40">
              <a href="#" className="hover:text-white transition-colors duration-200">Sobre</a>
              <a href="#" className="hover:text-white transition-colors duration-200">Fontes</a>
              <a href="#" className="hover:text-white transition-colors duration-200">Privacidade</a>
              <a href="#" className="hover:text-white transition-colors duration-200">Termos</a>
            </div>

            <p className="text-[11px] text-white/20 font-medium">
              2026 OnEvents. Dados de fontes oficiais.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
