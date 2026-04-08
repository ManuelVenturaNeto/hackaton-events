import { Event } from '../types';
import { Calendar, MapPin, Users, Building2, ExternalLink, ArrowRight } from 'lucide-react';
import { motion } from 'motion/react';
import { cn } from '../lib/utils';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';

interface EventCardProps {
  event: Event;
  onClick: (event: Event) => void;
}

function ScoreRing({ score }: { score: number }) {
  const radius = 18;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;
  const color = score >= 70 ? '#1aad6f' : score >= 40 ? '#0c93f5' : '#3a4f66';

  return (
    <div className="score-ring w-12 h-12">
      <svg width="48" height="48" viewBox="0 0 48 48">
        <circle cx="24" cy="24" r={radius} fill="none" stroke="#e1e8ed" strokeWidth="3" />
        <circle
          cx="24" cy="24" r={radius} fill="none"
          stroke={color} strokeWidth="3" strokeLinecap="round"
          strokeDasharray={circumference} strokeDashoffset={offset}
          className="transition-all duration-700"
        />
      </svg>
      <span className="absolute inset-0 flex items-center justify-center text-[11px] font-bold text-brand-navy">
        {score}
      </span>
    </div>
  );
}

const categoryColors: Record<string, string> = {
  'Technology': 'bg-brand-bright/10 text-brand-bright',
  'Banking / Financial': 'bg-emerald-50 text-emerald-600',
  'Agribusiness / Agriculture': 'bg-amber-50 text-amber-600',
  'Medical / Healthcare': 'bg-rose-50 text-rose-600',
  'Business / Entrepreneurship': 'bg-violet-50 text-violet-600',
};

export function EventCard({ event, onClick }: EventCardProps) {
  const isCanceled = event.status === 'canceled';

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.97 }}
      transition={{ duration: 0.3 }}
      className={cn(
        'card-glass overflow-hidden flex flex-col h-full group cursor-pointer',
        isCanceled && 'opacity-60 grayscale'
      )}
      onClick={() => onClick(event)}
    >
      {/* Top accent line */}
      <div className="h-[3px] bg-gradient-to-r from-brand-bright via-brand-cta to-brand-primary opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

      <div className="p-5 flex-1 flex flex-col">
        <div className="flex justify-between items-start mb-3">
          <span className={cn(
            'text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-full',
            categoryColors[event.category] || 'bg-brand-navy/8 text-brand-navy'
          )}>
            {event.category}
          </span>
          <ScoreRing score={event.networkingRelevanceScore} />
        </div>

        <h3 className="text-[15px] font-bold text-brand-navy mb-3 leading-snug group-hover:text-brand-cta transition-colors duration-200 line-clamp-2">
          {event.name}
        </h3>

        <div className="space-y-1.5 mb-4 flex-1">
          <div className="flex items-center gap-2 text-[13px] text-text-body">
            <Calendar className="w-3.5 h-3.5 text-brand-bright/70 shrink-0" />
            <span>
              {event.startDate ? format(new Date(event.startDate), "d 'de' MMM, yyyy", { locale: ptBR }) : 'Data a definir'}
            </span>
          </div>
          <div className="flex items-center gap-2 text-[13px] text-text-body">
            <MapPin className="w-3.5 h-3.5 text-brand-bright/70 shrink-0" />
            <span className="truncate">{event.location.city}{event.location.country ? `, ${event.location.country}` : ''}</span>
          </div>
          <div className="flex items-center gap-2 text-[13px] text-text-body">
            <Building2 className="w-3.5 h-3.5 text-brand-bright/70 shrink-0" />
            <span className="truncate">{event.organizer}</span>
          </div>
          {event.expectedAudienceSize > 0 && (
            <div className="flex items-center gap-2 text-[13px] text-text-body">
              <Users className="w-3.5 h-3.5 text-brand-bright/70 shrink-0" />
              <span>{event.expectedAudienceSize.toLocaleString('pt-BR')}+ participantes</span>
            </div>
          )}
        </div>

        {event.companiesInvolved.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-4">
            {event.companiesInvolved.slice(0, 3).map((company, i) => (
              <span key={i} className="text-[10px] bg-bg-light/80 px-2 py-0.5 rounded-md border border-border-gray/50 text-text-body/80">
                {company.name}
              </span>
            ))}
            {event.companiesInvolved.length > 3 && (
              <span className="text-[10px] text-brand-bright font-semibold px-1">
                +{event.companiesInvolved.length - 3}
              </span>
            )}
          </div>
        )}

        <div className="pt-3 border-t border-border-gray/50 flex items-center justify-between mt-auto">
          <span className="text-xs font-medium text-brand-bright flex items-center gap-1 group-hover:gap-2 transition-all duration-200">
            Ver Detalhes <ArrowRight className="w-3 h-3" />
          </span>
          {event.officialWebsiteUrl && (
            <a
              href={event.officialWebsiteUrl}
              target="_blank"
              rel="noopener noreferrer"
              onClick={(e) => e.stopPropagation()}
              className="p-1.5 hover:bg-bg-light rounded-full transition-colors text-text-body/50 hover:text-brand-cta"
            >
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          )}
        </div>
      </div>
    </motion.div>
  );
}
