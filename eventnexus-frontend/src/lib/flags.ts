/**
 * Maps country names to their flag emoji using ISO 3166-1 regional indicators.
 * Covers full names, common abbreviations, and case variations.
 */

const COUNTRY_CODES: Record<string, string> = {
  // Americas
  'USA': 'US', 'US': 'US', 'United States': 'US', 'United States of America': 'US',
  'Brazil': 'BR', 'Brasil': 'BR', 'BR': 'BR',
  'Canada': 'CA', 'CA': 'CA',
  'Mexico': 'MX', 'México': 'MX', 'MX': 'MX',
  'Argentina': 'AR', 'AR': 'AR',
  'Chile': 'CL', 'CL': 'CL',
  'Colombia': 'CO', 'CO': 'CO',
  'Peru': 'PE', 'PE': 'PE',

  // Europe
  'UK': 'GB', 'GB': 'GB', 'United Kingdom': 'GB', 'England': 'GB', 'Great Britain': 'GB',
  'Germany': 'DE', 'Deutschland': 'DE', 'DE': 'DE',
  'France': 'FR', 'FR': 'FR',
  'Spain': 'ES', 'España': 'ES', 'ES': 'ES',
  'Portugal': 'PT', 'PT': 'PT',
  'Italy': 'IT', 'IT': 'IT',
  'Netherlands': 'NL', 'NL': 'NL',
  'Switzerland': 'CH', 'CH': 'CH',
  'Austria': 'AT', 'AT': 'AT',
  'Belgium': 'BE', 'BE': 'BE',
  'Sweden': 'SE', 'SE': 'SE',
  'Norway': 'NO', 'NO': 'NO',
  'Denmark': 'DK', 'DK': 'DK',
  'Finland': 'FI', 'FI': 'FI',
  'Ireland': 'IE', 'IE': 'IE',
  'Poland': 'PL', 'PL': 'PL',
  'Czech Republic': 'CZ', 'CZ': 'CZ',

  // Asia & Oceania
  'Japan': 'JP', 'JP': 'JP',
  'Singapore': 'SG', 'SG': 'SG',
  'Australia': 'AU', 'AU': 'AU', 'Au': 'AU',
  'New Zealand': 'NZ', 'NZ': 'NZ', 'Nz': 'NZ',
  'South Korea': 'KR', 'KR': 'KR',
  'India': 'IN', 'IN': 'IN',
  'UAE': 'AE', 'AE': 'AE', 'United Arab Emirates': 'AE',
  'Israel': 'IL', 'IL': 'IL',
  'China': 'CN', 'CN': 'CN',

  // Africa
  'South Africa': 'ZA', 'ZA': 'ZA',
  'Nigeria': 'NG', 'NG': 'NG',
};

function codeToFlag(code: string): string {
  const upper = code.toUpperCase();
  return String.fromCodePoint(
    0x1F1E6 + upper.charCodeAt(0) - 65,
    0x1F1E6 + upper.charCodeAt(1) - 65,
  );
}

export function countryFlag(country: string): string {
  if (!country) return '🌍';

  // Direct match
  const direct = COUNTRY_CODES[country];
  if (direct) return codeToFlag(direct);

  // Case-insensitive match
  const lower = country.toLowerCase();
  for (const [name, code] of Object.entries(COUNTRY_CODES)) {
    if (name.toLowerCase() === lower) return codeToFlag(code);
  }

  // If it looks like a 2-letter code already, try converting directly
  if (country.length === 2) {
    return codeToFlag(country.toUpperCase());
  }

  return '🌍';
}
