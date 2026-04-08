import { Event } from "../types";
import { X, Calendar, MapPin, Users, Building2, ExternalLink, Globe, ShieldCheck, Clock, Info } from "lucide-react";
import { motion, AnimatePresence } from "motion/react";
import { format } from "date-fns";
import { cn } from "../lib/utils";

interface EventDetailsProps {
  event: Event | null;
  onClose: () => void;
}

export function EventDetails({ event, onClose }: EventDetailsProps) {
  if (!event) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 md:p-8">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
          className="absolute inset-0 bg-brand-navy/60 backdrop-blur-sm"
        />
        
        <motion.div
          initial={{ opacity: 0, scale: 0.9, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.9, y: 20 }}
          className="relative w-full max-w-4xl max-h-[90vh] bg-white rounded-3xl shadow-2xl overflow-hidden flex flex-col"
        >
          <button 
            onClick={onClose}
            className="absolute top-6 right-6 p-2 hover:bg-bg-light rounded-full transition-colors z-10"
          >
            <X className="w-6 h-6 text-brand-navy" />
          </button>

          <div className="overflow-y-auto">
            {/* Header */}
            <div className="p-8 md:p-12 bg-brand-navy text-white relative overflow-hidden">
              <div className="absolute top-0 right-0 w-64 h-64 bg-brand-bright/20 rounded-full blur-3xl -mr-32 -mt-32" />
              <div className="relative z-10">
                <div className="flex flex-wrap gap-2 mb-4">
                  <span className="bg-brand-bright px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-widest">
                    {event.category}
                  </span>
                  <span className="bg-white/20 backdrop-blur-md px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-widest">
                    {event.format}
                  </span>
                  {event.status !== 'upcoming' && (
                    <span className="bg-amber-500 px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-widest">
                      {event.status}
                    </span>
                  )}
                </div>
                <h2 className="text-3xl md:text-5xl font-bold mb-6 leading-tight">
                  {event.name}
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="flex items-center gap-3">
                    <div className="p-3 bg-white/10 rounded-2xl">
                      <Calendar className="w-6 h-6" />
                    </div>
                    <div>
                      <p className="text-white/60 text-xs uppercase font-bold tracking-wider">Date & Duration</p>
                      <p className="font-medium">{format(new Date(event.startDate), 'MMMM d')} - {format(new Date(event.endDate), 'd, yyyy')} ({event.duration})</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="p-3 bg-white/10 rounded-2xl">
                      <MapPin className="w-6 h-6" />
                    </div>
                    <div>
                      <p className="text-white/60 text-xs uppercase font-bold tracking-wider">Location</p>
                      <p className="font-medium">{event.location.venueName || 'Venue TBD'}, {event.location.city}</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Content */}
            <div className="p-8 md:p-12 grid grid-cols-1 lg:grid-cols-3 gap-12">
              <div className="lg:col-span-2 space-y-10">
                <section>
                  <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                    <Info className="w-5 h-5 text-brand-bright" />
                    About the Event
                  </h3>
                  <p className="text-text-body leading-relaxed text-lg">
                    {event.description}
                  </p>
                </section>

                <section>
                  <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                    <Building2 className="w-5 h-5 text-brand-bright" />
                    Companies Involved
                  </h3>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                    {event.companies.map((company, i) => (
                      <div key={i} className="p-4 bg-bg-light rounded-2xl border border-border-gray">
                        <p className="font-bold text-brand-navy text-sm">{company.name}</p>
                        <p className="text-[10px] uppercase text-brand-bright font-bold tracking-wider">{company.role}</p>
                      </div>
                    ))}
                  </div>
                </section>
              </div>

              <div className="space-y-6">
                <div className="p-6 bg-brand-bright/5 rounded-3xl border border-brand-bright/10">
                  <h4 className="text-brand-bright font-bold uppercase text-xs tracking-widest mb-4">Networking Potential</h4>
                  <div className="flex items-end gap-2 mb-6">
                    <span className="text-5xl font-bold text-brand-navy leading-none">{event.networkingScore}</span>
                    <span className="text-brand-bright font-bold mb-1">/ 100</span>
                  </div>
                  <div className="space-y-4">
                    <div className="flex items-center gap-3 text-sm">
                      <Users className="w-5 h-5 text-brand-bright" />
                      <span className="font-medium">{event.audienceSize?.toLocaleString() || 'Large'} Attendees</span>
                    </div>
                    <div className="flex items-center gap-3 text-sm">
                      <ShieldCheck className="w-5 h-5 text-brand-bright" />
                      <span className="font-medium">Verified Official Event</span>
                    </div>
                    <div className="flex items-center gap-3 text-sm">
                      <Clock className="w-5 h-5 text-brand-bright" />
                      <span className="font-medium">Updated {format(new Date(event.lastUpdated), 'MMM d')}</span>
                    </div>
                  </div>
                  <a 
                    href={event.websiteUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn-pill btn-primary w-full mt-8"
                  >
                    Official Website <Globe className="w-4 h-4" />
                  </a>
                </div>

                <div className="p-6 bg-bg-light rounded-3xl border border-border-gray">
                  <h4 className="text-brand-navy font-bold uppercase text-xs tracking-widest mb-4">Venue Details</h4>
                  <p className="text-sm font-medium text-brand-navy mb-1">{event.location.venueName}</p>
                  <p className="text-sm text-text-body mb-4">{event.location.streetAddress}</p>
                  <p className="text-sm text-text-body">{event.location.city}, {event.location.state}</p>
                  <p className="text-sm text-text-body">{event.location.country}</p>
                </div>

                <div className="aspect-video bg-bg-light rounded-3xl border border-border-gray overflow-hidden relative group">
                  <div className="absolute inset-0 flex flex-col items-center justify-center text-text-body/40">
                    <MapPin className="w-8 h-8 mb-2 group-hover:scale-110 transition-transform" />
                    <p className="text-xs font-bold uppercase tracking-widest">Interactive Map</p>
                    <p className="text-[10px]">{event.location.city}, {event.location.country}</p>
                  </div>
                  {/* In a real app, integrate Google Maps or Leaflet here */}
                  <div className="absolute inset-0 bg-brand-bright/5 pointer-events-none" />
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
