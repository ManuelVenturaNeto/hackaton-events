import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { ArrowLeft, MapPin, Calendar, Users, Building2, ExternalLink, Globe, Clock } from 'lucide-react';
import { Badge } from '../components/Badge';
import { useEvent } from '../hooks/useEvent';

export function EventDetails() {
  const { id } = useParams<{ id: string }>();
  const { event, loading, error } = useEvent(id);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error || !event) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-gray-50">
        <h2 className="text-2xl font-bold text-gray-900">
          {error ? 'Erro ao carregar evento' : 'Evento não encontrado'}
        </h2>
        {error && <p className="mt-2 text-red-500">{error.message}</p>}
        <Link to="/" className="mt-4 text-blue-600 hover:underline">Voltar para Eventos</Link>
      </div>
    );
  }

  const roleLabels: Record<string, string> = {
    organizer: 'Organizador',
    sponsor: 'Patrocinador',
    exhibitor: 'Expositor',
    partner: 'Parceiro',
    featured: 'Destaque',
  };

  return (
    <div className="min-h-screen bg-gray-50 pb-12">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <Link to="/" className="inline-flex items-center text-sm text-gray-500 hover:text-gray-900 transition-colors">
            <ArrowLeft className="h-4 w-4 mr-1" /> Voltar para Eventos
          </Link>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 mt-8">
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
          {/* Hero Section */}
          <div className="p-8 md:p-12 border-b border-gray-100">
            <div className="flex flex-wrap gap-3 mb-6">
              {event.status === 'upcoming' && <Badge variant="success">Próximo</Badge>}
              {event.status === 'canceled' && <Badge variant="danger">Cancelado</Badge>}
              {event.status === 'postponed' && <Badge variant="warning">Adiado</Badge>}
              {event.status === 'completed' && <Badge variant="default">Concluído</Badge>}
              <Badge variant="info">{event.format === 'in-person' ? 'Presencial' : event.format === 'hybrid' ? 'Híbrido' : 'Online'}</Badge>
              <Badge variant="default">{event.category}</Badge>
            </div>

            <h1 className="text-3xl md:text-5xl font-bold text-gray-900 mb-4">{event.name}</h1>
            <p className="text-lg text-gray-600 max-w-3xl leading-relaxed">
              {event.briefDescription}
            </p>

            <div className="mt-8 flex flex-wrap gap-4">
              <a
                href={event.officialWebsiteUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center justify-center px-6 py-3 border border-transparent text-base font-medium rounded-lg text-white bg-blue-600 hover:bg-blue-700 transition-colors"
              >
                Site Oficial <ExternalLink className="ml-2 h-4 w-4" />
              </a>
            </div>
          </div>

          {/* Details Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 divide-y md:divide-y-0 md:divide-x divide-gray-100">
            {/* Left Column: Key Info */}
            <div className="p-8 md:col-span-2 space-y-8">
              <section>
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                  <Calendar className="h-5 w-5 mr-2 text-blue-600" /> Data
                </h3>
                <div className="bg-gray-50 rounded-xl p-4 border border-gray-100">
                  <p className="font-medium text-gray-900">
                    {format(new Date(event.startDate), "EEEE, d 'de' MMMM 'de' yyyy", { locale: ptBR })} - {format(new Date(event.endDate), "EEEE, d 'de' MMMM 'de' yyyy", { locale: ptBR })}
                  </p>
                  <p className="text-sm text-gray-500 mt-1 flex items-center">
                    <Clock className="h-4 w-4 mr-1" /> Duração: {event.durationDays} {event.durationDays === 1 ? 'dia' : 'dias'}
                  </p>
                </div>
              </section>

              <section>
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                  <MapPin className="h-5 w-5 mr-2 text-blue-600" /> Localização
                </h3>
                <div className="bg-gray-50 rounded-xl p-4 border border-gray-100">
                  <p className="font-medium text-gray-900">{event.location.venueName}</p>
                  <p className="text-gray-600 mt-1">{event.location.fullStreetAddress}</p>
                  <p className="text-gray-600">{event.location.city}, {event.location.stateProvince} {event.location.postalCode}</p>
                  <p className="text-gray-600">{event.location.country}</p>
                </div>
              </section>

              <section>
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                  <Building2 className="h-5 w-5 mr-2 text-blue-600" /> Empresas Envolvidas
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {event.companiesInvolved.map((company, idx) => (
                    <div key={idx} className="flex items-center justify-between bg-white border border-gray-200 rounded-lg p-3">
                      <span className="font-medium text-gray-900">{company.name}</span>
                      <Badge variant="outline" className="text-[10px] uppercase tracking-wider">{roleLabels[company.role] || company.role}</Badge>
                    </div>
                  ))}
                </div>
              </section>
            </div>

            {/* Right Column: Networking Stats */}
            <div className="p-8 bg-gray-50/50">
              <h3 className="text-lg font-semibold text-gray-900 mb-6">Potencial de Networking</h3>

              <div className="space-y-6">
                <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm text-center">
                  <div className="text-4xl font-bold text-blue-600 mb-1">{event.networkingRelevanceScore}</div>
                  <div className="text-sm font-medium text-gray-500 uppercase tracking-wide">Pontuação de Relevância</div>
                </div>

                <div className="flex items-start gap-3">
                  <div className="p-2 bg-blue-100 rounded-lg text-blue-600">
                    <Users className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="font-semibold text-gray-900">~{event.expectedAudienceSize.toLocaleString('pt-BR')}</p>
                    <p className="text-sm text-gray-500">Participantes Esperados</p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <div className="p-2 bg-purple-100 rounded-lg text-purple-600">
                    <Globe className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="font-semibold text-gray-900">{event.organizer}</p>
                    <p className="text-sm text-gray-500">Organizador Principal</p>
                  </div>
                </div>
              </div>

              <div className="mt-8 pt-6 border-t border-gray-200">
                <p className="text-xs text-gray-400 text-center">
                  Última atualização: {format(new Date(event.lastUpdated), "d 'de' MMM yyyy HH:mm", { locale: ptBR })}
                </p>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
