import { useState, useEffect } from 'react';
import { calendarAPI } from '../services/api';
import toast from '../utils/toast';

const VIEWS = ['month', 'week', 'day', 'agenda'];
const DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

export default function Calendar() {
  const [events, setEvents] = useState([]);
  const [view, setView] = useState('month');
  const [currentDate, setCurrentDate] = useState(new Date());
  const [loading, setLoading] = useState(true);
  const [showEventForm, setShowEventForm] = useState(false);
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [eventTypes, setEventTypes] = useState([]);

  const [newEvent, setNewEvent] = useState({
    title: '',
    type: 'custom',
    start: '',
    end: '',
    all_day: true,
    description: ''
  });

  useEffect(() => {
    loadTypes();
  }, []);

  useEffect(() => {
    loadEvents();
  }, [currentDate, view]);

  const loadTypes = async () => {
    try {
      const res = await calendarAPI.getTypes();
      setEventTypes(res.data.types);
    } catch (err) {
      console.error('Failed to load types:', err);
    }
  };

  const loadEvents = async () => {
    setLoading(true);
    const { start, end } = getDateRange();
    try {
      const res = await calendarAPI.getEvents(start, end);
      setEvents(res.data.events);
    } catch (err) {
      console.error('Failed to load events:', err);
    } finally {
      setLoading(false);
    }
  };

  const getDateRange = () => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();

    if (view === 'month') {
      const start = new Date(year, month, 1).toISOString().split('T')[0];
      const end = new Date(year, month + 1, 0).toISOString().split('T')[0];
      return { start, end };
    }

    if (view === 'week') {
      const startOfWeek = new Date(currentDate);
      startOfWeek.setDate(currentDate.getDate() - currentDate.getDay());
      const endOfWeek = new Date(startOfWeek);
      endOfWeek.setDate(startOfWeek.getDate() + 6);
      return {
        start: startOfWeek.toISOString().split('T')[0],
        end: endOfWeek.toISOString().split('T')[0]
      };
    }

    const dayStr = currentDate.toISOString().split('T')[0];
    return { start: dayStr, end: dayStr };
  };

  const navigate = (direction) => {
    const newDate = new Date(currentDate);
    if (view === 'month') {
      newDate.setMonth(newDate.getMonth() + direction);
    } else if (view === 'week') {
      newDate.setDate(newDate.getDate() + (7 * direction));
    } else {
      newDate.setDate(newDate.getDate() + direction);
    }
    setCurrentDate(newDate);
  };

  const goToToday = () => {
    setCurrentDate(new Date());
  };

  const handleCreateEvent = async () => {
    try {
      await calendarAPI.create(newEvent);
      setShowEventForm(false);
      setNewEvent({ title: '', type: 'custom', start: '', end: '', all_day: true, description: '' });
      loadEvents();
    } catch (err) {
      toast.error('Failed to create event');
    }
  };

  const handleDeleteEvent = async (eventId) => {
    if (!confirm('Delete this event?')) return;
    try {
      await calendarAPI.delete(eventId);
      setSelectedEvent(null);
      loadEvents();
    } catch (err) {
      toast.error('Failed to delete');
    }
  };

  const handleGenerateEvents = async () => {
    try {
      const res = await calendarAPI.generate();
      toast.success(`Generated ${res.data.generated} events from payments and projects`);
      loadEvents();
    } catch (err) {
      toast.error('Failed to generate events');
    }
  };

  const renderMonthView = () => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    const firstDay = new Date(year, month, 1).getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();

    const days = [];
    for (let i = 0; i < firstDay; i++) {
      days.push(<div key={`empty-${i}`} className="calendar-day empty"></div>);
    }

    for (let day = 1; day <= daysInMonth; day++) {
      const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
      const dayEvents = events.filter(e => e.start.startsWith(dateStr));
      const isToday = new Date().toISOString().split('T')[0] === dateStr;

      days.push(
        <div key={day} className={`calendar-day ${isToday ? 'today' : ''}`}>
          <div className="day-number">{day}</div>
          <div className="day-events">
            {dayEvents.slice(0, 3).map(event => (
              <div
                key={event.id}
                className="calendar-event"
                style={{ backgroundColor: event.color }}
                onClick={() => setSelectedEvent(event)}
              >
                {event.title}
              </div>
            ))}
            {dayEvents.length > 3 && (
              <div className="more-events">+{dayEvents.length - 3} more</div>
            )}
          </div>
        </div>
      );
    }

    return (
      <div className="calendar-month">
        <div className="calendar-header-row">
          {DAYS.map(day => <div key={day} className="calendar-header-cell">{day}</div>)}
        </div>
        <div className="calendar-grid">
          {days}
        </div>
      </div>
    );
  };

  const renderAgendaView = () => {
    const sortedEvents = [...events].sort((a, b) => a.start.localeCompare(b.start));

    return (
      <div className="calendar-agenda">
        {sortedEvents.length === 0 ? (
          <div className="text-center text-muted p-8">No events</div>
        ) : (
          sortedEvents.map(event => (
            <div
              key={event.id}
              className="agenda-item"
              onClick={() => setSelectedEvent(event)}
            >
              <div className="agenda-date">
                {new Date(event.start).toLocaleDateString()}
              </div>
              <div className="agenda-color" style={{ backgroundColor: event.color }}></div>
              <div className="agenda-content">
                <div className="agenda-title">{event.title}</div>
                <div className="agenda-type">{event.type}</div>
              </div>
            </div>
          ))
        )}
      </div>
    );
  };

  return (
    <>
      <div className="info-banner mb-6">
        View and manage payments, deadlines, and events in one place.
      </div>

      {/* Toolbar */}
      <div className="calendar-toolbar">
        <div className="toolbar-nav">
          <button className="btn btn-secondary" onClick={() => navigate(-1)}>Prev</button>
          <button className="btn btn-secondary" onClick={goToToday}>Today</button>
          <button className="btn btn-secondary" onClick={() => navigate(1)}>Next</button>
          <h3 className="toolbar-title">
            {currentDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
          </h3>
        </div>
        <div className="toolbar-actions">
          <div className="view-tabs">
            {VIEWS.map(v => (
              <button
                key={v}
                className={`tab ${view === v ? 'active' : ''}`}
                onClick={() => setView(v)}
              >
                {v.charAt(0).toUpperCase() + v.slice(1)}
              </button>
            ))}
          </div>
          <button className="btn btn-secondary" onClick={handleGenerateEvents}>
            Generate Events
          </button>
          <button className="btn btn-primary" onClick={() => setShowEventForm(true)}>
            + Add Event
          </button>
        </div>
      </div>

      {/* Calendar View */}
      <div className="section">
        {loading ? (
          <div className="text-center p-8">Loading...</div>
        ) : view === 'agenda' ? (
          renderAgendaView()
        ) : (
          renderMonthView()
        )}
      </div>

      {/* Event Detail Modal */}
      {selectedEvent && (
        <div className="modal-overlay" onClick={() => setSelectedEvent(null)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3 style={{ color: selectedEvent.color }}>{selectedEvent.title}</h3>
              <button className="modal-close" onClick={() => setSelectedEvent(null)}>x</button>
            </div>
            <div className="modal-body">
              <p><strong>Type:</strong> {selectedEvent.type}</p>
              <p><strong>Date:</strong> {new Date(selectedEvent.start).toLocaleDateString()}</p>
              {selectedEvent.description && (
                <p><strong>Description:</strong> {selectedEvent.description}</p>
              )}
              {selectedEvent.entity_type && (
                <p><strong>Related:</strong> {selectedEvent.entity_type} / {selectedEvent.entity_id}</p>
              )}
            </div>
            <div className="modal-footer">
              <button className="btn btn-danger" onClick={() => handleDeleteEvent(selectedEvent.id)}>
                Delete
              </button>
            </div>
          </div>
        </div>
      )}

      {/* New Event Modal */}
      {showEventForm && (
        <div className="modal-overlay" onClick={() => setShowEventForm(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>New Event</h3>
              <button className="modal-close" onClick={() => setShowEventForm(false)}>x</button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label className="form-label">Title *</label>
                <input
                  type="text"
                  className="form-input"
                  value={newEvent.title}
                  onChange={(e) => setNewEvent({ ...newEvent, title: e.target.value })}
                />
              </div>
              <div className="grid-2">
                <div className="form-group">
                  <label className="form-label">Type</label>
                  <select
                    className="form-select"
                    value={newEvent.type}
                    onChange={(e) => setNewEvent({ ...newEvent, type: e.target.value })}
                  >
                    {eventTypes.map(t => (
                      <option key={t} value={t}>{t}</option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Date *</label>
                  <input
                    type="date"
                    className="form-input"
                    value={newEvent.start}
                    onChange={(e) => setNewEvent({ ...newEvent, start: e.target.value, end: e.target.value })}
                  />
                </div>
              </div>
              <div className="form-group">
                <label className="form-label">Description</label>
                <textarea
                  className="form-input"
                  value={newEvent.description}
                  onChange={(e) => setNewEvent({ ...newEvent, description: e.target.value })}
                  rows={3}
                />
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setShowEventForm(false)}>Cancel</button>
              <button
                className="btn btn-primary"
                onClick={handleCreateEvent}
                disabled={!newEvent.title || !newEvent.start}
              >
                Create Event
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
