import { HomePage } from './pages/HomePage';

export default function App() {
  return (
    <div className="min-h-screen flex flex-col">
      <HomePage />

      {/* Footer */}
      <footer className="bg-brand-navy text-white py-8 sm:py-12 px-4 sm:px-6 relative overflow-hidden">
        <div className="absolute inset-0 hero-grid opacity-50" />
        <div className="hidden sm:block absolute bottom-0 right-0 w-96 h-96 bg-brand-bright/5 rounded-full blur-[120px]" />

        <div className="max-w-7xl mx-auto relative z-10">
          <div className="flex flex-col items-center gap-5 sm:gap-8 md:flex-row md:justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 sm:w-9 sm:h-9 bg-gradient-to-br from-brand-bright to-brand-cta rounded-xl flex items-center justify-center text-white font-extrabold text-sm shadow-lg shadow-brand-cta/20">
                O
              </div>
              <div>
                <span className="text-base sm:text-lg font-bold tracking-tight">OnEvents</span>
                <span className="text-white/30 text-[10px] sm:text-xs ml-1.5 sm:ml-2 font-medium">by Onfly</span>
              </div>
            </div>

            <div className="flex flex-wrap justify-center gap-4 sm:gap-8 text-xs sm:text-sm text-white/40">
              <a href="#" className="hover:text-white transition-colors duration-200">Sobre</a>
              <a href="#" className="hover:text-white transition-colors duration-200">Fontes</a>
              <a href="#" className="hover:text-white transition-colors duration-200">Privacidade</a>
              <a href="#" className="hover:text-white transition-colors duration-200">Termos</a>
            </div>

            <p className="text-[10px] sm:text-[11px] text-white/20 font-medium text-center">
              2026 OnEvents. Dados de fontes oficiais.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
