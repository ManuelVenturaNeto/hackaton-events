import express from 'express';
import { createServer as createViteServer } from 'vite';
import path from 'path';
import { fileURLToPath } from 'url';
import { eventsData } from './src/server/data.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function startServer() {
  const app = express();
  const PORT = 3000;

  app.use(express.json());

  // API Routes
  app.get('/api/events', (req, res) => {
    const { 
      category, 
      country, 
      city, 
      status, 
      format, 
      search, 
      sort = 'relevance' 
    } = req.query;

    let filteredEvents = [...eventsData];

    if (category) {
      filteredEvents = filteredEvents.filter(e => e.category.toLowerCase() === String(category).toLowerCase());
    }
    if (country) {
      filteredEvents = filteredEvents.filter(e => e.location.country.toLowerCase() === String(country).toLowerCase());
    }
    if (city) {
      filteredEvents = filteredEvents.filter(e => e.location.city.toLowerCase() === String(city).toLowerCase());
    }
    if (status) {
      filteredEvents = filteredEvents.filter(e => e.status.toLowerCase() === String(status).toLowerCase());
    }
    if (format) {
      filteredEvents = filteredEvents.filter(e => e.format.toLowerCase() === String(format).toLowerCase());
    }
    if (search) {
      const q = String(search).toLowerCase();
      filteredEvents = filteredEvents.filter(e => 
        e.name.toLowerCase().includes(q) || 
        e.organizer.toLowerCase().includes(q) ||
        e.briefDescription.toLowerCase().includes(q)
      );
    }

    // Sorting
    filteredEvents.sort((a, b) => {
      if (sort === 'date') {
        return new Date(a.startDate).getTime() - new Date(b.startDate).getTime();
      }
      if (sort === 'audience') {
        return b.expectedAudienceSize - a.expectedAudienceSize;
      }
      if (sort === 'companies') {
        return b.companiesInvolved.length - a.companiesInvolved.length;
      }
      if (sort === 'updated') {
        return new Date(b.lastUpdated).getTime() - new Date(a.lastUpdated).getTime();
      }
      // default: relevance
      return b.networkingRelevanceScore - a.networkingRelevanceScore;
    });

    res.json(filteredEvents);
  });

  app.get('/api/events/:id', (req, res) => {
    const event = eventsData.find(e => e.id === req.params.id);
    if (event) {
      res.json(event);
    } else {
      res.status(404).json({ error: 'Event not found' });
    }
  });

  // Vite middleware for development
  if (process.env.NODE_ENV !== 'production') {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: 'spa',
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), 'dist');
    app.use(express.static(distPath));
    app.get('*', (req, res) => {
      res.sendFile(path.join(distPath, 'index.html'));
    });
  }

  app.listen(PORT, '0.0.0.0', () => {
    console.log(`Server running on http://localhost:${PORT}`);
  });
}

startServer();
