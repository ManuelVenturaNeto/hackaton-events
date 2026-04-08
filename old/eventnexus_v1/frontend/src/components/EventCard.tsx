import React from 'react';
import { Link } from 'react-router-dom';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { MapPin, Calendar, Users, Building2, ExternalLink } from 'lucide-react';
import { Badge } from './Badge';
import { Event } from '../types/event';

interface EventCardProps {
  event: Event;
  key?: React.Key;
}

export function EventCard({ event }: EventCardProps) {
  const getStatusBadge = (status: Event['status']) => {
    switch (status) {
      case 'upcoming': return <Badge variant="success">Próximo</Badge>;
      case 'canceled': return <Badge variant="danger">Cancelado</Badge>;
      case 'postponed': return <Badge variant="warning">Adiado</Badge>;
      case 'completed': return <Badge variant="default">Concluído</Badge>;
    }
  };

  const getFormatBadge = (fmt: Event['format']) => {
    switch (fmt) {
      case 'in-person': return <Badge variant="info">Presencial</Badge>;
      case 'hybrid': return <Badge variant="outline">Híbrido</Badge>;
      case 'online': return <Badge variant="outline">Online</Badge>;
    }
  };

  return (
    <div className="group relative flex flex-col justify-between rounded-xl border border-gray-200 bg-white p-6 shadow-sm transition-all hover:shadow-md">
      <div>
        <div className="mb-4 flex items-start justify-between">
          <div className="flex flex-wrap gap-2">
            {getStatusBadge(event.status)}
            {getFormatBadge(event.format)}
            <Badge variant="default">{event.category}</Badge>
          </div>
          <div className="flex flex-col items-end">
            <span className="text-2xl font-bold text-blue-600">{event.networkingRelevanceScore}</span>
            <span className="text-xs text-gray-500">Pontuação</span>
          </div>
        </div>

        <Link to={`/event/${event.id}`} className="block">
          <h3 className="mb-2 text-xl font-bold text-gray-900 group-hover:text-blue-600 transition-colors">
            {event.name}
          </h3>
        </Link>

        <p className="mb-4 text-sm text-gray-600 line-clamp-2">
          {event.briefDescription}
        </p>

        <div className="space-y-2 text-sm text-gray-600">
          <div className="flex items-center gap-2">
            <Calendar className="h-4 w-4 text-gray-400" />
            <span>
              {format(new Date(event.startDate), "d 'de' MMM yyyy", { locale: ptBR })} - {format(new Date(event.endDate), "d 'de' MMM yyyy", { locale: ptBR })}
            </span>
          </div>

          <div className="flex items-center gap-2">
            <MapPin className="h-4 w-4 text-gray-400" />
            <span className="truncate">
              {event.location.city}, {event.location.country}
            </span>
          </div>

          <div className="flex items-center gap-2">
            <Users className="h-4 w-4 text-gray-400" />
            <span>~{event.expectedAudienceSize.toLocaleString('pt-BR')} participantes esperados</span>
          </div>

          <div className="flex items-center gap-2">
            <Building2 className="h-4 w-4 text-gray-400" />
            <span className="truncate">
              {event.companiesInvolved.length} empresas envolvidas (incl. {event.organizer})
            </span>
          </div>
        </div>
      </div>

      <div className="mt-6 flex items-center justify-between border-t border-gray-100 pt-4">
        <Link
          to={`/event/${event.id}`}
          className="text-sm font-medium text-blue-600 hover:text-blue-800"
        >
          Ver Detalhes &rarr;
        </Link>

        <a
          href={event.officialWebsiteUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700"
        >
          Site Oficial <ExternalLink className="h-3 w-3" />
        </a>
      </div>
    </div>
  );
}
