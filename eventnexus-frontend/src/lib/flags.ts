/**
 * Maps country names to their flag emoji using ISO 3166-1 regional indicators.
 */

const COUNTRY_CODES: Record<string, string> = {
  'USA': 'US', 'United States': 'US', 'United States of America': 'US',
  'Brazil': 'BR', 'Brasil': 'BR',
  'Canada': 'CA',
  'Mexico': 'MX', 'México': 'MX',
  'Argentina': 'AR',
  'Chile': 'CL',
  'Colombia': 'CO',
  'Peru': 'PE',
  'UK': 'GB', 'United Kingdom': 'GB', 'England': 'GB',
  'Germany': 'DE', 'Deutschland': 'DE',
  'France': 'FR',
  'Spain': 'ES', 'España': 'ES',
  'Portugal': 'PT',
  'Italy': 'IT',
  'Netherlands': 'NL',
  'Switzerland': 'CH',
  'Austria': 'AT',
  'Belgium': 'BE',
  'Sweden': 'SE',
  'Norway': 'NO',
  'Denmark': 'DK',
  'Finland': 'FI',
  'Ireland': 'IE',
  'Poland': 'PL',
  'Czech Republic': 'CZ',
  'Japan': 'JP',
  'Singapore': 'SG',
  'Australia': 'AU',
  'New Zealand': 'NZ',
  'South Korea': 'KR',
  'India': 'IN',
  'UAE': 'AE', 'United Arab Emirates': 'AE',
  'Israel': 'IL',
  'China': 'CN',
  'South Africa': 'ZA',
  'Nigeria': 'NG',
};

function codeToFlag(code: string): string {
  const chars = code.toUpperCase().split('');
  return chars.map(c => String.fromCodePoint(0x1F1E6 + c.charCodeAt(0) - 65)).join('');
}

export function countryFlag(country: string): string {
  const code = COUNTRY_CODES[country];
  if (code) return codeToFlag(code);

  // Try case-insensitive match
  const lower = country.toLowerCase();
  for (const [name, c] of Object.entries(COUNTRY_CODES)) {
    if (name.toLowerCase() === lower) return codeToFlag(c);
  }

  return '🌍';
}
