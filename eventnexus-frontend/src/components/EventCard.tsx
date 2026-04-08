import { Event } from '../types';
import { Calendar, MapPin, Users, Building2, ExternalLink, ArrowRight, Star } from 'lucide-react';
import { motion } from 'motion/react';
import { cn } from '../lib/utils';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';

interface EventCardProps {
  event: Event;
  onClick: (event: Event) => void;
}

export function EventCard({ event, onClick }: EventCardProps) {
  const isCanceled = event.status === 'canceled';

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.95 }}
      className={cn(
        'card-glass overflow-hidden flex flex-col h-full group cursor-pointer',
        isCanceled && 'opacity-75 grayscale'
      )}
      onClick={() => onClick(event)}
    >
      <div className="p-5 flex-1 flex flex-col">
        <div className="flex justify-between items-start mb-3">
          <span className={cn(
            'text-[10px] font-bold uppercase tracking-wider px-2 py-1 rounded-full',
            event.category === 'Technology' ? 'bg-brand-bright/10 text-brand-bright' : 'bg-brand-navy/10 text-brand-navy'
          )}>
            {event.category}
          </span>
          <div className="flex gap-2">
            {event.status !== 'upcoming' && (
              <span className={cn(
                'text-[10px] font-bold uppercase tracking-wider px-2 py-1 rounded-full',
                isCanceled ? 'bg-red-100 text-red-600' : 'bg-amber-100 text-amber-600'
              )}>
                {event.status}
              </span>
            )}
            <span className="bg-green-100 text-green-700 text-[10px] font-bold uppercase tracking-wider px-2 py-1 rounded-full flex items-center gap-1">
              <Star className="w-3 h-3 fill-current" />
              {event.networkingRelevanceScore}
            </span>
          </div>
        </div>

        <h3 className="text-lg font-bold text-brand-navy mb-2 group-hover:text-brand-cta transition-colors">
          {event.name}
        </h3>

        <div className="space-y-2 mb-4 flex-1">
          <div className="flex items-center gap-2 text-sm text-text-body">
            <Calendar className="w-4 h-4 text-brand-bright" />
            <span>
              {event.startDate ? format(new Date(event.startDate), "d 'de' MMM, yyyy", { locale: ptBR }) : 'Data a definir'}
            </span>
          </div>
          <div className="flex items-center gap-2 text-sm text-text-body">
            <MapPin className="w-4 h-4 text-brand-bright" />
            <span className="truncate">{event.location.city}, {event.location.country}</span>
          </div>
          <div className="flex items-center gap-2 text-sm text-text-body">
            <Building2 className="w-4 h-4 text-brand-bright" />
            <span className="truncate">{event.organizer}</span>
          </div>
          {event.expectedAudienceSize > 0 && (
            <div className="flex items-center gap-2 text-sm text-text-body">
              <Users className="w-4 h-4 text-brand-bright" />
              <span>{event.expectedAudienceSize.toLocaleString('pt-BR')}+ participantes</span>
            </div>
          )}
        </div>

        <div className="flex flex-wrap gap-1 mb-4">
          {event.companiesInvolved.slice(0, 3).map((company, i) => (
            <span key={i} className="text-[10px] bg-bg-light px-2 py-0.5 rounded border border-border-gray">
              {company.name}
            </span>
          ))}
          {event.companiesInvolved.length > 3 && (
            <span className="text-[10px] text-brand-bright font-medium">
              +{event.companiesInvolved.length - 3} mais
            </span>
          )}
        </div>

        <div className="pt-4 border-t border-border-gray flex items-center justify-between mt-auto">
          <span className="text-xs font-medium text-brand-bright flex items-center gap-1">
            Ver Detalhes <ArrowRight className="w-3 h-3" />
          </span>
          <a
            href={event.officialWebsiteUrl}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
            className="p-2 hover:bg-bg-light rounded-full transition-colors text-text-body hover:text-brand-cta"
          >
            <ExternalLink className="w-4 h-4" />
          </a>
        </div>
      </div>
    </motion.div>
  );
}
