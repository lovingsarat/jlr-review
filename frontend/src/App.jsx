import React, { useState, useEffect, useRef } from "react";
import "./App.css";

const API_BASE = "http://localhost:8000/api";

function App() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedPlatform, setSelectedPlatform] = useState(null);
  const [selectedSentiment, setSelectedSentiment] = useState(null);
  const [selectedCity, setSelectedCity] = useState(null);

  const [feedItems, setFeedItems] = useState([]);
  const [stats, setStats] = useState({
    totalFeedbackCount: 0,
    sentimentPercentages: { Positive: 0, Neutral: 0, Negative: 0 },
    platformCounts: {},
    cityCounts: {},
  });

  const [chatMessages, setChatMessages] = useState([
    {
      sender: "BOT",
      text: "Hello! I am your RAG-enabled Diaspora Assistant. I have indexed all 2026 social media feedback from Twitter, Facebook, and Quora regarding Indian diaspora community events and upcoming activities in the Midlands. Ask me anything, or run sentiment / trend queries!",
      timestamp: Date.now(),
    },
  ]);
  const [chatInput, setChatInput] = useState("");
  const [isChatLoading, setIsChatLoading] = useState(false);
  const [chatError, setChatError] = useState(null);

  const chatEndRef = useRef(null);

  // Fetch feedback based on current search query and filters
  const fetchFeedback = async () => {
    try {
      let url = `${API_BASE}/feedback?`;
      const params = [];
      if (searchQuery) params.push(`query=${encodeURIComponent(searchQuery)}`);
      if (selectedPlatform) params.push(`platform=${encodeURIComponent(selectedPlatform)}`);
      if (selectedSentiment) params.push(`sentiment=${encodeURIComponent(selectedSentiment)}`);
      if (selectedCity) params.push(`city=${encodeURIComponent(selectedCity)}`);
      
      url += params.join("&");
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        setFeedItems(data);
      }
    } catch (err) {
      console.error("Error fetching feedback:", err);
    }
  };

  // Fetch general stats
  const fetchStats = async () => {
    try {
      const res = await fetch(`${API_BASE}/stats`);
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      }
    } catch (err) {
      console.error("Error fetching stats:", err);
    }
  };

  // Initial fetch and dependency trigger
  useEffect(() => {
    fetchStats();
  }, []);

  useEffect(() => {
    fetchFeedback();
  }, [searchQuery, selectedPlatform, selectedSentiment, selectedCity]);

  // Scroll to bottom of chat
  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [chatMessages, isChatLoading]);

  const handleClearFilters = () => {
    setSearchQuery("");
    setSelectedPlatform(null);
    setSelectedSentiment(null);
    setSelectedCity(null);
  };

  const handleSendChat = async (text) => {
    if (!text.trim() || isChatLoading) return;

    const userMessage = { sender: "USER", text: text.trim(), timestamp: Date.now() };
    setChatMessages((prev) => [...prev, userMessage]);
    setChatInput("");
    setIsChatLoading(true);
    setChatError(null);

    try {
      // Build the request matching ChatRequest schema in main.py
      const payload = {
        message: text.trim(),
        history: chatMessages.map((msg) => ({
          sender: msg.sender,
          text: msg.text,
        })),
      };

      const res = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        throw new Error(`Server returned status: ${res.status}`);
      }

      const data = await res.json();
      setChatMessages((prev) => [
        ...prev,
        {
          sender: "BOT",
          text: data.reply,
          timestamp: Date.now(),
        },
      ]);
    } catch (err) {
      console.error("Chat error:", err);
      setChatError("Failed to connect to AI server: " + err.message);
      setChatMessages((prev) => [
        ...prev,
        {
          sender: "BOT",
          text: "❌ **Error**: Could not connect to Gemini API. " + err.message + "\n\n*Note: If the error persists, verify that the API key provided in the .env file is valid.*",
          timestamp: Date.now(),
        },
      ]);
    } finally {
      setIsChatLoading(false);
    }
  };

  // Donut chart calculations
  const radius = 35;
  const circ = 2 * Math.PI * radius; // ~219.9
  const positivePct = stats.sentimentPercentages.Positive || 0;
  const neutralPct = stats.sentimentPercentages.Neutral || 0;
  const negativePct = stats.sentimentPercentages.Negative || 0;

  const posStroke = (positivePct / 100) * circ;
  const posOffset = 0;

  const neuStroke = (neutralPct / 100) * circ;
  const neuOffset = posStroke;

  const negStroke = (negativePct / 100) * circ;
  const negOffset = posStroke + neuStroke;

  const suggestedQuestions = [
    "What are the main complaints about Holi 2026?",
    "What are upcoming Diwali activities in Leicester?",
    "Consolidate feedback on Coventry Garba.",
    "Which platform has the most negative posts?",
    "Who praised Vaisakhi Langar in Birmingham?",
  ];

  return (
    <div className="app-container">
      {/* 1. Header Toolbar */}
      <header className="app-header">
        <div className="header-brand">
          <div className="brand-avatar">DP</div>
          <div className="brand-text">
            <h1>Midlands Pulse '26</h1>
            <span>INDIAN DIASPORA ENGAGEMENT</span>
          </div>
        </div>
        <button className="reset-button" onClick={handleClearFilters} title="Reset all filters">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67" />
          </svg>
          Reset Filters
        </button>
      </header>

      {/* 2. Navigation Tabs */}
      <nav className="tab-navigation">
        <button className={`nav-tab ${activeTab === "dashboard" ? "active" : ""}`} onClick={() => setActiveTab("dashboard")}>
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="tab-icon">
            <rect x="3" y="3" width="7" height="9" />
            <rect x="14" y="3" width="7" height="5" />
            <rect x="14" y="12" width="7" height="9" />
            <rect x="3" y="16" width="7" height="5" />
          </svg>
          Dashboard
        </button>
        <button className={`nav-tab ${activeTab === "chat" ? "active" : ""}`} onClick={() => setActiveTab("chat")}>
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="tab-icon">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          </svg>
          AI RAG Chat
        </button>
        <button className={`nav-tab ${activeTab === "explorer" ? "active" : ""}`} onClick={() => setActiveTab("explorer")}>
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="tab-icon">
            <circle cx="12" cy="12" r="10" />
            <polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76" />
          </svg>
          Feed Explorer
        </button>
      </nav>

      {/* 3. Main Screen Area */}
      <main className="app-content-body">
        {/* TAB 1: DASHBOARD */}
        {activeTab === "dashboard" && (
          <div className="tab-content fade-in">
            {/* Announcement Banner */}
            <section className="dashboard-banner">
              <div className="banner-top">
                <span className="banner-badge">2026 CONSOLIDATED SUMMARY</span>
                <span className="banner-emoji">🇮🇳</span>
              </div>
              <h2>Midlands Indian Diaspora Community Event Feedback</h2>
              <p>
                Aggregated data from Twitter (X), Facebook groups, and Quora spaces tracking community event engagement and upcoming planned activities across the region.
              </p>
            </section>

            {/* KPI Cards */}
            <section className="kpi-grid">
              <div className="kpi-card positive-kpi">
                <span className="kpi-title">Sentiment</span>
                <span className="kpi-value">{Math.round(positivePct)}%</span>
                <span className="kpi-subtitle">POSITIVE</span>
              </div>
              <div className="kpi-card mentions-kpi">
                <span className="kpi-title">Mentions</span>
                <span className="kpi-value">12.4k</span>
                <span className="kpi-subtitle">SOCIAL AGG</span>
              </div>
              <div className="kpi-card events-kpi">
                <span className="kpi-title">Events</span>
                <span className="kpi-value">18</span>
                <span className="kpi-subtitle">UPCOMING '26</span>
              </div>
            </section>

            {/* Metrics Split Grid */}
            <div className="dashboard-metrics-split">
              {/* Donut Chart Card */}
              <section className="metrics-card chart-card">
                <h3>
                  <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ color: "var(--color-primary)", marginRight: "8px" }}>
                    <line x1="18" y1="20" x2="18" y2="10" />
                    <line x1="12" y1="20" x2="12" y2="4" />
                    <line x1="6" y1="20" x2="6" y2="14" />
                  </svg>
                  Sentiment Breakdown Analysis
                </h3>
                <div className="chart-container">
                  <div className="donut-chart-wrapper">
                    <svg viewBox="0 0 100 100" className="donut-chart">
                      {/* Stacked circles rotated -90 deg */}
                      <g transform="rotate(-90 50 50)">
                        {/* Positive segment (Green) */}
                        {positivePct > 0 && (
                          <circle
                            cx="50"
                            cy="50"
                            r={radius}
                            fill="transparent"
                            stroke="#10b981"
                            strokeWidth="10"
                            strokeDasharray={`${posStroke} ${circ}`}
                            strokeDashoffset={-posOffset}
                            strokeLinecap="round"
                          />
                        )}
                        {/* Neutral segment (Yellow) */}
                        {neutralPct > 0 && (
                          <circle
                            cx="50"
                            cy="50"
                            r={radius}
                            fill="transparent"
                            stroke="#f59e0b"
                            strokeWidth="10"
                            strokeDasharray={`${neuStroke} ${circ}`}
                            strokeDashoffset={-neuOffset}
                            strokeLinecap="round"
                          />
                        )}
                        {/* Negative segment (Red) */}
                        {negativePct > 0 && (
                          <circle
                            cx="50"
                            cy="50"
                            r={radius}
                            fill="transparent"
                            stroke="#ef4444"
                            strokeWidth="10"
                            strokeDasharray={`${negStroke} ${circ}`}
                            strokeDashoffset={-negOffset}
                            strokeLinecap="round"
                          />
                        )}
                      </g>
                    </svg>
                    <div className="donut-chart-center">
                      <span className="donut-pct">{Math.round(positivePct)}%</span>
                      <span className="donut-lbl">Positive</span>
                    </div>
                  </div>

                  <div className="chart-legend">
                    <div className="legend-item">
                      <span className="legend-indicator positive"></span>
                      <span className="legend-name">Positive Review</span>
                      <span className="legend-count">{FEEDBACK_COUNT("Positive")} ({Math.round(positivePct)}%)</span>
                    </div>
                    <div className="legend-item">
                      <span className="legend-indicator neutral"></span>
                      <span className="legend-name">Neutral Comments</span>
                      <span className="legend-count">{FEEDBACK_COUNT("Neutral")} ({Math.round(neutralPct)}%)</span>
                    </div>
                    <div className="legend-item">
                      <span className="legend-indicator negative"></span>
                      <span className="legend-name">Negative Feedback</span>
                      <span className="legend-count">{FEEDBACK_COUNT("Negative")} ({Math.round(negativePct)}%)</span>
                    </div>
                  </div>
                </div>
              </section>

              {/* Counts Split Grid */}
              <div className="counts-cards-subgrid">
                {/* Platform Card */}
                <section className="metrics-card platform-card">
                  <h3 className="primary-text">Platform Feed</h3>
                  <div className="platform-bars-list">
                    <PlatformBar label="Twitter" count={stats.platformCounts.Twitter || 0} total={15} color="#1da1f2" />
                    <PlatformBar label="Facebook" count={stats.platformCounts.Facebook || 0} total={15} color="#1877f2" />
                    <PlatformBar label="Quora" count={stats.platformCounts.Quora || 0} total={15} color="#b92b27" />
                  </div>
                </section>

                {/* Cities Card */}
                <section className="metrics-card cities-card">
                  <h3 className="secondary-text">Regional Cities</h3>
                  <div className="cities-list">
                    <CityItem label="Birmingham" count={stats.cityCounts.Birmingham || 0} />
                    <CityItem label="Leicester" count={stats.cityCounts.Leicester || 0} />
                    <CityItem label="Coventry" count={stats.cityCounts.Coventry || 0} />
                    <CityItem label="Nottingham" count={stats.cityCounts.Nottingham || 0} />
                  </div>
                </section>
              </div>
            </div>

            {/* Insights and Trends section */}
            <div className="dashboard-insights-grid">
              <section className="metrics-card insights-card">
                <div className="card-header-row">
                  <h3>
                    <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ color: "var(--color-primary)", marginRight: "8px" }}>
                      <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
                      <line x1="16" y1="2" x2="16" y2="6" />
                      <line x1="8" y1="2" x2="8" y2="6" />
                      <line x1="3" y1="10" x2="21" y2="10" />
                    </svg>
                    2026 Trend Intelligence
                  </h3>
                  <span className="sync-badge">RAG-Sync: 2m ago</span>
                </div>
                <div className="insights-list">
                  <InsightItem
                    emoji="✨"
                    bgColor="rgba(240, 230, 140, 0.35)"
                    title="Leicester Diwali Switch-On (October 2026)"
                    description="Major buzz around the introduction of a massive, eco-friendly drone light show instead of fireworks. However, the local diaspora is raising deep concerns about Belgrave Road traffic closures and is requesting the council to organize park-and-ride shuttle buses."
                  />
                  <InsightItem
                    emoji="🥁"
                    bgColor="var(--color-primary-container)"
                    title="Coventry Navratri Garba (October 2026)"
                    description="Moving to a larger, premium venue to accommodate the surging diaspora. Tickets sold out in 10 minutes, triggering severe community complaints about ticket scalping and reselling on social media. Suggestion made to implement secure ID-linked ticketing."
                  />
                </div>
              </section>

              <section className="metrics-card insights-card">
                <div className="card-header-row">
                  <h3>
                    <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ color: "var(--color-secondary)", marginRight: "8px" }}>
                      <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z" />
                    </svg>
                    Retrospective 2026 Trends
                  </h3>
                  <span className="sync-badge sec">Consolidated</span>
                </div>
                <div className="insights-list">
                  <InsightItem
                    emoji="🎨"
                    bgColor="rgba(255, 242, 175, 0.5)"
                    title="Midlands Holi Festival (Birmingham)"
                    description="Praised for vibrant dhol players, colorful crowd and strong community engagement. Criticized heavily for expensive family tickets (£25/person) and extremely long, 1-hour lines for food stalls."
                  />
                  <InsightItem
                    emoji="🌾"
                    bgColor="#d0e4ff"
                    title="Birmingham Vaisakhi Mela"
                    description="Very large attendance. Langar (free kitchen) praised with stellar reviews for organization. The core complaints relate to parking nightmares in Handsworth Park and lack of trash bins leading to littering."
                  />
                  <InsightItem
                    emoji="🏆"
                    bgColor="rgba(255, 215, 0, 0.2)"
                    title="Midlands Indian Sports Day (Leicester)"
                    description="High nostalgia for traditional sports like Kabaddi and Kho-Kho. However, severe criticism regarding weather planning: summer rain caused a 3-hour delay due to a lack of an indoor backup plan."
                  />
                </div>
              </section>
            </div>
          </div>
        )}

        {/* TAB 2: AI RAG CHAT */}
        {activeTab === "chat" && (
          <div className="tab-content chat-tab fade-in">
            {/* Chat Area */}
            <div className="chat-messages-container">
              {chatMessages.map((msg, idx) => (
                <div key={idx} className={`chat-bubble-row ${msg.sender === "USER" ? "user-row" : "bot-row"}`}>
                  <div className="chat-bubble">
                    <span className="bubble-sender">{msg.sender === "USER" ? "YOU" : "DIASPORA BOT (RAG)"}</span>
                    <p className="bubble-text">{msg.text}</p>
                  </div>
                </div>
              ))}
              
              {isChatLoading && (
                <div className="chat-bubble-row bot-row">
                  <div className="chat-bubble loading-bubble">
                    <div className="typing-loader">
                      <span></span><span></span><span></span>
                    </div>
                    <span className="loading-text">RAG Agent analyzing diaspora feed...</span>
                  </div>
                </div>
              )}

              {chatError && (
                <div className="chat-error-card">
                  <p>{chatError}</p>
                </div>
              )}
              
              <div ref={chatEndRef} />
            </div>

            {/* Quick Suggestions Chips */}
            <div className="quick-suggestions-section">
              <span className="suggestions-title">⚡ QUICK ANALYTICS COMMANDS</span>
              <div className="suggestions-chips-container">
                {suggestedQuestions.map((q, idx) => (
                  <button key={idx} className="suggestion-chip" onClick={() => handleSendChat(q)}>
                    {q}
                  </button>
                ))}
              </div>
            </div>

            {/* Chat Input Bar */}
            <div className="chat-input-bar">
              <input
                type="text"
                placeholder="Ask Diaspora RAG chatbot..."
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSendChat(chatInput)}
              />
              <button
                className="chat-send-btn"
                onClick={() => handleSendChat(chatInput)}
                disabled={!chatInput.trim() || isChatLoading}
              >
                <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="22" y1="2" x2="11" y2="13" />
                  <polygon points="22 2 15 22 11 13 2 9 22 2" />
                </svg>
              </button>
            </div>
          </div>
        )}

        {/* TAB 3: FEED EXPLORER */}
        {activeTab === "explorer" && (
          <div className="tab-content explorer-tab fade-in">
            {/* Search inputs */}
            <div className="explorer-search-bar">
              <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="search-icon">
                <circle cx="11" cy="11" r="8" />
                <line x1="21" y1="21" x2="16.65" y2="16.65" />
              </svg>
              <input
                type="text"
                placeholder="Search by event, comment text, user..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
              {searchQuery && (
                <button className="clear-search-btn" onClick={() => setSearchQuery("")}>
                  ✕
                </button>
              )}
            </div>

            {/* Filters Row */}
            <section className="explorer-filters-panel">
              {/* Platform selection */}
              <div className="filter-group">
                <span className="filter-label">Platform:</span>
                <div className="filter-options">
                  <button className={`filter-btn ${selectedPlatform === null ? "active" : ""}`} onClick={() => setSelectedPlatform(null)}>All</button>
                  <button className={`filter-btn ${selectedPlatform === "Twitter" ? "active" : ""}`} onClick={() => setSelectedPlatform("Twitter")}>Twitter</button>
                  <button className={`filter-btn ${selectedPlatform === "Facebook" ? "active" : ""}`} onClick={() => setSelectedPlatform("Facebook")}>Facebook</button>
                  <button className={`filter-btn ${selectedPlatform === "Quora" ? "active" : ""}`} onClick={() => setSelectedPlatform("Quora")}>Quora</button>
                </div>
              </div>

              {/* Sentiment selection */}
              <div className="filter-group">
                <span className="filter-label">Sentiment:</span>
                <div className="filter-options">
                  <button className={`filter-btn ${selectedSentiment === null ? "active" : ""}`} onClick={() => setSelectedSentiment(null)}>All</button>
                  <button className={`filter-btn pos ${selectedSentiment === "Positive" ? "active" : ""}`} onClick={() => setSelectedSentiment("Positive")}>Positive</button>
                  <button className={`filter-btn neu ${selectedSentiment === "Neutral" ? "active" : ""}`} onClick={() => setSelectedSentiment("Neutral")}>Neutral</button>
                  <button className={`filter-btn neg ${selectedSentiment === "Negative" ? "active" : ""}`} onClick={() => setSelectedSentiment("Negative")}>Negative</button>
                </div>
              </div>

              {/* City selection */}
              <div className="filter-group">
                <span className="filter-label">City:</span>
                <div className="filter-options flex-wrap">
                  <button className={`filter-btn sec ${selectedCity === null ? "active" : ""}`} onClick={() => setSelectedCity(null)}>All</button>
                  <button className={`filter-btn sec ${selectedCity === "Birmingham" ? "active" : ""}`} onClick={() => setSelectedCity("Birmingham")}>Birmingham</button>
                  <button className={`filter-btn sec ${selectedCity === "Leicester" ? "active" : ""}`} onClick={() => setSelectedCity("Leicester")}>Leicester</button>
                  <button className={`filter-btn sec ${selectedCity === "Coventry" ? "active" : ""}`} onClick={() => setSelectedCity("Coventry")}>Coventry</button>
                  <button className={`filter-btn sec ${selectedCity === "Nottingham" ? "active" : ""}`} onClick={() => setSelectedCity("Nottingham")}>Nottingham</button>
                </div>
              </div>
            </section>

            {/* Results header */}
            <div className="explorer-results-header">
              <span className="results-count">{feedItems.length} Feed items matched</span>
              {(selectedPlatform || selectedSentiment || selectedCity || searchQuery) && (
                <button className="clear-filters-link" onClick={handleClearFilters}>
                  Clear filters
                </button>
              )}
            </div>

            {/* Feed Cards list */}
            <div className="explorer-cards-list">
              {feedItems.length === 0 ? (
                <div className="no-results-state">
                  <svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" style={{ color: "var(--color-primary)", opacity: 0.5 }}>
                    <circle cx="12" cy="12" r="10" />
                    <line x1="12" y1="8" x2="12" y2="12" />
                    <line x1="12" y1="16" x2="12.01" y2="16" />
                  </svg>
                  <h4>No diaspora feed items match your criteria.</h4>
                  <p>Try clearing filters or search query to see full consolidated 2026 data.</p>
                  <button className="btn-primary" onClick={handleClearFilters}>Reset Search</button>
                </div>
              ) : (
                feedItems.map((item) => (
                  <div key={item.id} className="feedback-feed-card">
                    {/* Top Row: Author, platform logo, date */}
                    <div className="card-top-row">
                      <div className="card-author-info">
                        <div className={`platform-badge ${item.platform.toLowerCase()}`}>
                          {item.platform.charAt(0)}
                        </div>
                        <span className="author-name">{item.author}</span>
                      </div>
                      <span className="card-date">{item.date}</span>
                    </div>

                    {/* Event name row with potential Planned tag */}
                    <div className="card-event-row">
                      <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="event-icon">
                        <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
                        <line x1="16" y1="2" x2="16" y2="6" />
                        <line x1="8" y1="2" x2="8" y2="6" />
                        <line x1="3" y1="10" x2="21" y2="10" />
                      </svg>
                      <span className="event-name">{item.event}</span>
                      {item.isUpcoming && <span className="planned-badge">PLANNED</span>}
                    </div>

                    {/* Feedback content text */}
                    <p className="card-text">{item.text}</p>

                    {/* Bottom Row: City location tag and Sentiment Badge */}
                    <div className="card-bottom-row">
                      <div className="city-tag">
                        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="location-icon">
                          <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
                          <circle cx="12" cy="10" r="3" />
                        </svg>
                        {item.city}
                      </div>

                      <span className={`sentiment-badge ${item.sentiment.toLowerCase()}`}>
                        {item.sentiment.toUpperCase()}
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );

  // Simple feedback count helpers based on local static items for UI layout matching
  function FEEDBACK_COUNT(sentiment) {
    // Total static items is 15
    const items = [
      { sentiment: "Positive" }, { sentiment: "Negative" }, { sentiment: "Neutral" },
      { sentiment: "Positive" }, { sentiment: "Negative" }, { sentiment: "Positive" },
      { sentiment: "Negative" }, { sentiment: "Neutral" }, { sentiment: "Positive" },
      { sentiment: "Neutral" }, { sentiment: "Negative" }, { sentiment: "Positive" },
      { sentiment: "Positive" }, { sentiment: "Neutral" }, { sentiment: "Positive" }
    ];
    return items.filter(i => i.sentiment === sentiment).length;
  }
}

function PlatformBar({ label, count, total, color }) {
  const percentage = total > 0 ? (count / total) * 100 : 0;
  return (
    <div className="platform-bar-row">
      <div className="bar-labels">
        <span className="bar-title">{label}</span>
        <span className="bar-count">{count} entries</span>
      </div>
      <div className="bar-track" style={{ backgroundColor: `${color}26` }}>
        <div className="bar-fill" style={{ width: `${percentage}%`, backgroundColor: color }} />
      </div>
    </div>
  );
}

function CityItem({ label, count }) {
  return (
    <div className="city-list-row">
      <div className="city-label-group">
        <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="city-loc-icon">
          <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
          <circle cx="12" cy="10" r="3" />
        </svg>
        <span className="city-name">{label}</span>
      </div>
      <span className="city-count-badge">{count}</span>
    </div>
  );
}

function InsightItem({ emoji, bgColor, title, description }) {
  return (
    <div className="insight-row-item">
      <div className="insight-emoji-box" style={{ backgroundColor: bgColor }}>
        {emoji}
      </div>
      <div className="insight-content">
        <h4>{title}</h4>
        <p>{description}</p>
      </div>
    </div>
  );
}

export default App;
