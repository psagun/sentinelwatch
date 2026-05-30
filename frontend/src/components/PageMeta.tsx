import { useEffect } from 'react';

interface PageMetaProps {
  /** Page name used as the @id slug */
  id: string;
  /** Short page description */
  description: string;
  /** JSON-LD: what features/capabilities this page displays */
  features: string[];
  /** JSON-LD: what API endpoints back this page */
  endpoints: string[];
  /** JSON-LD: technical notes for AI agents (selectors, auth, data shape) */
  technicalNotes?: string;
}

/**
 * Injects JSON-LD structured metadata into <head> so that AI agents
 * navigating the app can discover page purpose, API endpoints, and
 * technical details programmatically.
 *
 * The script tag is auto-removed on unmount.
 */
export default function PageMeta({ id, description, features, endpoints, technicalNotes }: PageMetaProps) {
  useEffect(() => {
    const script = document.createElement('script');
    script.type = 'application/ld+json';
    script.id = `page-meta-${id}`;
    script.textContent = JSON.stringify({
      '@context': 'https://schema.org',
      '@type': 'WebApplication',
      name: `SentinelWatch — ${id}`,
      description,
      applicationCategory: 'SecurityApplication',
      browserRequirements: 'Requires JavaScript. SPA built with React 18 + Vite.',
      offers: { '@type': 'Offer', price: '0', priceCurrency: 'USD' },
      featureList: features,
      apiEndpoints: endpoints,
      technicalNotes: technicalNotes || '',
      pageId: id,
    }, null, 2);
    document.head.appendChild(script);
    return () => { script.remove(); };
  }, [id, description, features, endpoints, technicalNotes]);

  return null;
}
