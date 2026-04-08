import { useState, useEffect } from 'react';
import { Event } from '../types';
import { X, Calendar, MapPin, Users, Building2, Globe, ShieldCheck, Clock, Info, Zap, Plane, Hotel, Loader2 } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { categoryLabels, formatLabels, statusLabels, roleLabels, t } from '../lib/labels';
import { fetchFlightUrl, fetchHotelUrl } from '../api';

interface EventDetailsProps {
  event: Event | null;
  onClose: () => void;
}

function ScoreMeter({ score }: { score: number }) {
  const radius = 36;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;
  const color = score >= 70 ? '#1aad6f' : score >= 40 ? '#0c93f5' : '#3a4f66';

  return (
    <div className="relative inline-flex items-center justify-center w-20 h-20 sm:w-28 sm:h-28">
      <svg width="100%" height="100%" viewBox="0 0 96 96" className="-rotate-90">
        <circle cx="48" cy="48" r={radius} fill="none" stroke="#e1e8ed" strokeWidth="5" />
        <motion.circle
          cx="48" cy="48" r={radius} fill="none"
          stroke={color} strokeWidth="5" strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 1, delay: 0.3, ease: 'easeOut' }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-2xl sm:text-3xl font-extrabold text-brand-navy leading-none">{score}</span>
        <span className="text-[9px] sm:text-[10px] font-bold text-brand-bright uppercase tracking-wider">/100</span>
      </div>
    </div>
  );
}

export function EventDetails({ event, onClose }: EventDetailsProps) {
  const [flightUrl, setFlightUrl] = useState<string | null>(null);
  const [flightLoading, setFlightLoading] = useState(false);
  const [flightError, setFlightError] = useState<string | null>(null);
  const [hotelUrl, setHotelUrl] = useState<string | null>(null);
  const [hotelLoading, setHotelLoading] = useState(false);
  const [hotelError, setHotelError] = useState<string | null>(null);

  useEffect(() => {
    if (!event) return;
    setFlightUrl(null);
    setFlightError(null);
    setFlightLoading(true);
    fetchFlightUrl(event.id)
      .then(res => { setFlightUrl(res.url); setFlightError(res.error); })
      .catch(() => setFlightError('Serviço indisponível'))
      .finally(() => setFlightLoading(false));

    setHotelUrl(null);
    setHotelError(null);
    setHotelLoading(true);
    fetchHotelUrl(event.id)
      .then(res => { setHotelUrl(res.url); setHotelError(res.error); })
      .catch(() => setHotelError('Serviço indisponível'))
      .finally(() => setHotelLoading(false));
  }, [event?.id]);

  if (!event) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center sm:p-4 md:p-8">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
          className="absolute inset-0 bg-brand-navy/70 backdrop-blur-md"
        />

        <motion.div
          initial={{ opacity: 0, y: 40, scale: 0.97 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 40, scale: 0.97 }}
          transition={{ duration: 0.3, ease: 'easeOut' }}
          className="relative w-full sm:max-w-4xl max-h-[95vh] sm:max-h-[90vh] bg-white rounded-t-3xl sm:rounded-3xl shadow-[0_32px_64px_rgba(25,42,61,0.25)] overflow-hidden flex flex-col"
        >
          <button
            onClick={onClose}
            className="absolute top-4 right-4 sm:top-5 sm:right-5 p-2 bg-white/10 hover:bg-white/20 rounded-full transition-colors z-10 backdrop-blur-sm"
          >
            <X className="w-5 h-5 text-white" />
          </button>

          <div className="overflow-y-auto overscroll-contain">
            {/* Header */}
            <div className="p-5 sm:p-8 md:p-12 hero-gradient text-white relative overflow-hidden">
              <div className="hero-grid absolute inset-0" />
              <div className="absolute top-0 right-0 w-48 sm:w-80 h-48 sm:h-80 bg-brand-bright/15 rounded-full blur-[60px] sm:blur-[80px] -mr-24 sm:-mr-40 -mt-24 sm:-mt-40" />

              <div className="relative z-10">
                <div className="flex flex-wrap gap-1.5 sm:gap-2 mb-4 sm:mb-5">
                  <span className="bg-brand-bright/90 px-2.5 sm:px-3 py-1 rounded-full text-[9px] sm:text-[10px] font-bold uppercase tracking-widest shadow-sm">
                    {t(categoryLabels, event.category)}
                  </span>
                  <span className="bg-white/15 backdrop-blur-md px-2.5 sm:px-3 py-1 rounded-full text-[9px] sm:text-[10px] font-bold uppercase tracking-widest border border-white/10">
                    {t(formatLabels, event.format)}
                  </span>
                  {event.status !== 'upcoming' && (
                    <span className="bg-amber-500/90 px-2.5 sm:px-3 py-1 rounded-full text-[9px] sm:text-[10px] font-bold uppercase tracking-widest">
                      {t(statusLabels, event.status)}
                    </span>
                  )}
                </div>
                <h2 className="text-xl sm:text-3xl md:text-4xl font-extrabold mb-4 sm:mb-6 leading-tight text-white tracking-tight">
                  {event.name}
                </h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-5">
                  <div className="flex items-center gap-2.5 sm:gap-3">
                    <div className="p-2 sm:p-2.5 bg-white/10 rounded-lg sm:rounded-xl border border-white/5 shrink-0">
                      <Calendar className="w-4 h-4 sm:w-5 sm:h-5" />
                    </div>
                    <div className="min-w-0">
                      <p className="text-white/50 text-[9px] sm:text-[10px] uppercase font-bold tracking-wider">Data e Duração</p>
                      <p className="font-medium text-xs sm:text-sm truncate">
                        {event.startDate && format(new Date(event.startDate), "d 'de' MMMM", { locale: ptBR })}
                        {event.endDate && ` - ${format(new Date(event.endDate), "d 'de' MMMM, yyyy", { locale: ptBR })}`}
                        {event.durationDays > 0 && ` (${event.durationDays}d)`}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2.5 sm:gap-3">
                    <div className="p-2 sm:p-2.5 bg-white/10 rounded-lg sm:rounded-xl border border-white/5 shrink-0">
                      <MapPin className="w-4 h-4 sm:w-5 sm:h-5" />
                    </div>
                    <div className="min-w-0">
                      <p className="text-white/50 text-[9px] sm:text-[10px] uppercase font-bold tracking-wider">Local</p>
                      <p className="font-medium text-xs sm:text-sm truncate">
                        {event.location.venueName || 'Local a definir'}, {event.location.city}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Content */}
            <div className="p-5 sm:p-8 md:p-12 grid grid-cols-1 lg:grid-cols-3 gap-6 sm:gap-10">
              <div className="lg:col-span-2 space-y-6 sm:space-y-8">
                <section>
                  <h3 className="text-base sm:text-lg font-bold mb-2 sm:mb-3 flex items-center gap-2">
                    <Info className="w-4 h-4 text-brand-bright shrink-0" />
                    Sobre o Evento
                  </h3>
                  <p className="text-text-body leading-relaxed text-sm sm:text-base">
                    {event.briefDescription || 'Descrição não disponível.'}
                  </p>
                </section>

                {event.companiesInvolved.length > 0 && (
                  <section>
                    <h3 className="text-base sm:text-lg font-bold mb-2 sm:mb-3 flex items-center gap-2">
                      <Building2 className="w-4 h-4 text-brand-bright shrink-0" />
                      Empresas Envolvidas
                    </h3>
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 sm:gap-3">
                      {event.companiesInvolved.map((company, i) => (
                        <motion.div
                          key={i}
                          initial={{ opacity: 0, y: 8 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: i * 0.05 }}
                          className="p-2.5 sm:p-3 bg-bg-light rounded-lg sm:rounded-xl border border-border-gray/50"
                        >
                          <p className="font-bold text-brand-navy text-xs sm:text-sm truncate">{company.name}</p>
                          <p className="text-[9px] sm:text-[10px] uppercase text-brand-bright/80 font-bold tracking-wider">{t(roleLabels, company.role)}</p>
                        </motion.div>
                      ))}
                    </div>
                  </section>
                )}
              </div>

              <div className="space-y-4 sm:space-y-5">
                <div className="p-4 sm:p-6 bg-gradient-to-br from-brand-bright/5 to-brand-primary/5 rounded-xl sm:rounded-2xl border border-brand-bright/10">
                  <h4 className="text-brand-bright font-bold uppercase text-[9px] sm:text-[10px] tracking-widest mb-3 sm:mb-4 flex items-center gap-1.5">
                    <Zap className="w-3 h-3 sm:w-3.5 sm:h-3.5" />
                    Potencial de Networking
                  </h4>
                  <div className="flex justify-center mb-4 sm:mb-5">
                    <ScoreMeter score={event.networkingRelevanceScore} />
                  </div>
                  <div className="space-y-2 sm:space-y-3">
                    <div className="flex items-center gap-2 text-sm">
                      <Users className="w-4 h-4 text-brand-bright/70 shrink-0" />
                      <span className="font-medium text-[12px] sm:text-[13px]">
                        {event.expectedAudienceSize > 0
                          ? `${event.expectedAudienceSize.toLocaleString('pt-BR')} participantes`
                          : 'Público estimado'}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-sm">
                      <ShieldCheck className="w-4 h-4 text-brand-success/70 shrink-0" />
                      <span className="font-medium text-[12px] sm:text-[13px]">Evento verificado</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm">
                      <Clock className="w-4 h-4 text-text-body/40 shrink-0" />
                      <span className="font-medium text-[12px] sm:text-[13px] text-text-body/70">
                        Atualizado em {event.lastUpdated && format(new Date(event.lastUpdated), "d 'de' MMM", { locale: ptBR })}
                      </span>
                    </div>
                  </div>

                  <div className="mt-4 sm:mt-6 space-y-2">
                    <a
                      href={event.officialWebsiteUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn-pill btn-primary w-full text-[13px] sm:text-[14px] py-2.5"
                    >
                      Site Oficial <Globe className="w-4 h-4" />
                    </a>

                    {flightLoading ? (
                      <div className="btn-pill w-full bg-brand-navy/5 text-brand-navy/40 text-[13px] py-2.5 cursor-wait">
                        <Loader2 className="w-4 h-4 animate-spin" /> Buscando voos...
                      </div>
                    ) : flightUrl ? (
                      <a href={flightUrl} target="_blank" rel="noopener noreferrer"
                        className="btn-pill btn-primary w-full text-[13px] sm:text-[14px] py-2.5">
                        <Plane className="w-4 h-4" /> Comprar Passagem
                      </a>
                    ) : flightError ? (
                      <div className="text-center text-[10px] text-text-body/40">{flightError}</div>
                    ) : null}

                    {hotelLoading ? (
                      <div className="btn-pill w-full bg-brand-navy/5 text-brand-navy/40 text-[13px] py-2.5 cursor-wait">
                        <Loader2 className="w-4 h-4 animate-spin" /> Buscando hotéis...
                      </div>
                    ) : hotelUrl ? (
                      <a href={hotelUrl} target="_blank" rel="noopener noreferrer"
                        className="btn-pill btn-primary w-full text-[13px] sm:text-[14px] py-2.5">
                        <Hotel className="w-4 h-4" /> Reservar Hotel
                      </a>
                    ) : hotelError ? (
                      <div className="text-center text-[10px] text-text-body/40">{hotelError}</div>
                    ) : null}
                  </div>
                </div>

                <div className="p-4 sm:p-5 bg-bg-light rounded-xl sm:rounded-2xl border border-border-gray/50">
                  <h4 className="text-brand-navy font-bold uppercase text-[9px] sm:text-[10px] tracking-widest mb-2 sm:mb-3 flex items-center gap-1.5">
                    <MapPin className="w-3 h-3 sm:w-3.5 sm:h-3.5 text-brand-bright/60" />
                    Detalhes do Local
                  </h4>
                  <p className="text-xs sm:text-sm font-semibold text-brand-navy mb-0.5">{event.location.venueName}</p>
                  <p className="text-[11px] sm:text-[13px] text-text-body/70">{event.location.fullStreetAddress}</p>
                  <p className="text-[11px] sm:text-[13px] text-text-body/70">
                    {event.location.city}{event.location.stateProvince ? `, ${event.location.stateProvince}` : ''}
                  </p>
                  <p className="text-[11px] sm:text-[13px] text-text-body/70">{event.location.country}</p>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
