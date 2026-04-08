export const categoryLabels: Record<string, string> = {
  'Technology': 'Tecnologia',
  'Banking / Financial': 'Bancos / Financeiro',
  'Agribusiness / Agriculture': 'Agronegócio',
  'Medical / Healthcare': 'Saúde / Medicina',
  'Business / Entrepreneurship': 'Negócios / Empreendedorismo',
};

export const formatLabels: Record<string, string> = {
  'in-person': 'Presencial',
  'hybrid': 'Híbrido',
  'online': 'Online',
};

export const statusLabels: Record<string, string> = {
  'upcoming': 'Próximo',
  'canceled': 'Cancelado',
  'postponed': 'Adiado',
  'completed': 'Concluído',
};

export const roleLabels: Record<string, string> = {
  'organizer': 'Organizador',
  'sponsor': 'Patrocinador',
  'exhibitor': 'Expositor',
  'partner': 'Parceiro',
  'featured': 'Destaque',
};

export function t(labels: Record<string, string>, key: string): string {
  return labels[key] || key;
}
