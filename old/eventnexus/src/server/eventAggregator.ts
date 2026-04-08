import { Event, SearchFilters } from "../types.ts";
import { processEvents } from "./eventProcessor.ts";

// This would normally call external APIs or scrapers
// For this app, we simulate the aggregation from "reliable sources"
export async function getEvents(filters: SearchFilters): Promise<Event[]> {
  // Mocking the "raw" data from multiple sources
  const rawEvents: Partial<Event>[] = [
    {
      name: "AWS re:Invent 2026",
      location: {
        venueName: "The Venetian",
        city: "Las Vegas",
        state: "NV",
        country: "USA",
        streetAddress: "3355 S Las Vegas Blvd"
      },
      startDate: "2026-11-30",
      endDate: "2026-12-04",
      organizer: "Amazon Web Services",
      category: "Technology",
      format: "in-person",
      websiteUrl: "https://reinvent.awsevents.com/",
      description: "AWS re:Invent is a learning conference for the global cloud computing community.",
      companies: [
        { name: "AWS", role: "organizer" },
        { name: "Databricks", role: "sponsor" },
        { name: "Snowflake", role: "sponsor" }
      ],
      audienceSize: 50000,
      status: "upcoming",
      sourceUrl: "https://reinvent.awsevents.com/"
    },
    {
      name: "Google I/O 2026",
      location: {
        venueName: "Shoreline Amphitheatre",
        city: "Mountain View",
        state: "CA",
        country: "USA"
      },
      startDate: "2026-05-12",
      endDate: "2026-05-14",
      organizer: "Google",
      category: "Technology",
      format: "hybrid",
      websiteUrl: "https://io.google/",
      description: "Google's flagship developer conference.",
      companies: [
        { name: "Google", role: "organizer" }
      ],
      audienceSize: 5000,
      status: "upcoming",
      sourceUrl: "https://io.google/"
    },
    {
      name: "NVIDIA GTC 2026",
      location: {
        venueName: "San Jose Convention Center",
        city: "San Jose",
        state: "CA",
        country: "USA"
      },
      startDate: "2026-03-16",
      endDate: "2026-03-19",
      organizer: "NVIDIA",
      category: "Technology",
      format: "in-person",
      websiteUrl: "https://www.nvidia.com/gtc/",
      description: "The conference for the era of AI.",
      companies: [
        { name: "NVIDIA", role: "organizer" },
        { name: "Microsoft", role: "partner" }
      ],
      audienceSize: 15000,
      status: "completed",
      sourceUrl: "https://www.nvidia.com/gtc/"
    },
    {
      name: "Web Summit 2026",
      location: {
        venueName: "Altice Arena",
        city: "Lisbon",
        country: "Portugal"
      },
      startDate: "2026-11-01",
      endDate: "2026-11-04",
      organizer: "Web Summit",
      category: "Business / Entrepreneurship",
      format: "in-person",
      websiteUrl: "https://websummit.com/",
      description: "The best technology conference in the world.",
      companies: [
        { name: "Web Summit", role: "organizer" },
        { name: "Microsoft", role: "sponsor" },
        { name: "Meta", role: "sponsor" }
      ],
      audienceSize: 70000,
      status: "upcoming",
      sourceUrl: "https://websummit.com/"
    },
    {
      name: "Money20/20 Europe",
      location: {
        venueName: "RAI Amsterdam",
        city: "Amsterdam",
        country: "Netherlands"
      },
      startDate: "2026-06-02",
      endDate: "2026-06-04",
      organizer: "Ascential",
      category: "Banking / Financial",
      format: "in-person",
      websiteUrl: "https://europe.money2020.com/",
      description: "Where the future of money comes to life.",
      companies: [
        { name: "Stripe", role: "sponsor" },
        { name: "Adyen", role: "sponsor" },
        { name: "Visa", role: "sponsor" }
      ],
      audienceSize: 8000,
      status: "upcoming",
      sourceUrl: "https://europe.money2020.com/"
    },
    {
      name: "Agrishow 2026",
      location: {
        venueName: "Polo Regional de Desenvolvimento Tecnológico",
        city: "Ribeirão Preto",
        state: "SP",
        country: "Brazil"
      },
      startDate: "2026-04-27",
      endDate: "2026-05-01",
      organizer: "Informa Markets",
      category: "Agribusiness / Agriculture",
      format: "in-person",
      websiteUrl: "https://www.agrishow.com.br/",
      description: "The largest agricultural technology trade show in Latin America.",
      companies: [
        { name: "John Deere", role: "exhibitor" },
        { name: "Case IH", role: "exhibitor" },
        { name: "New Holland", role: "exhibitor" }
      ],
      audienceSize: 190000,
      status: "upcoming",
      sourceUrl: "https://www.agrishow.com.br/"
    },
    {
      name: "HIMSS Global Health Conference 2026",
      location: {
        venueName: "Las Vegas Convention Center",
        city: "Las Vegas",
        state: "NV",
        country: "USA"
      },
      startDate: "2026-03-02",
      endDate: "2026-03-06",
      organizer: "HIMSS",
      category: "Medical / Healthcare",
      format: "in-person",
      websiteUrl: "https://www.himss.org/global-conference",
      description: "The most influential health information technology event of the year.",
      companies: [
        { name: "Epic", role: "sponsor" },
        { name: "Oracle Health", role: "sponsor" },
        { name: "Microsoft Health", role: "sponsor" }
      ],
      audienceSize: 40000,
      status: "upcoming",
      sourceUrl: "https://www.himss.org/global-conference"
    },
    {
      name: "SXSW 2026",
      location: {
        venueName: "Austin Convention Center",
        city: "Austin",
        state: "TX",
        country: "USA"
      },
      startDate: "2026-03-13",
      endDate: "2026-03-21",
      organizer: "SXSW, LLC",
      category: "Technology",
      format: "in-person",
      websiteUrl: "https://www.sxsw.com/",
      description: "An essential destination for global professionals, featuring sessions, showcases, and screenings.",
      companies: [
        { name: "Porsche", role: "sponsor" },
        { name: "Delta", role: "sponsor" },
        { name: "Slack", role: "sponsor" }
      ],
      audienceSize: 300000,
      status: "upcoming",
      sourceUrl: "https://www.sxsw.com/"
    },
    {
      name: "CES 2026",
      location: {
        venueName: "Las Vegas Convention Center",
        city: "Las Vegas",
        state: "NV",
        country: "USA"
      },
      startDate: "2026-01-06",
      endDate: "2026-01-09",
      organizer: "Consumer Technology Association",
      category: "Technology",
      format: "in-person",
      websiteUrl: "https://www.ces.tech/",
      description: "The most influential tech event in the world — the proving ground for breakthrough technologies.",
      companies: [
        { name: "Samsung", role: "exhibitor" },
        { name: "Sony", role: "exhibitor" },
        { name: "LG", role: "exhibitor" }
      ],
      audienceSize: 130000,
      status: "upcoming",
      sourceUrl: "https://www.ces.tech/"
    }
  ];

  // In a real app, this would be the result of multiple scrapers
  return processEvents(rawEvents as Event[], filters);
}
