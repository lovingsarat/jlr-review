import React, { useState, useEffect, useRef } from "react";
import { Analytics } from "@vercel/analytics/react";
import { SpeedInsights } from "@vercel/speed-insights/react";
import "./App.css";

const STATIC_DATA_URL = `${import.meta.env.BASE_URL}data.json`;
const ENV_GEMINI_KEY = import.meta.env.VITE_GEMINI_API_KEY || "";
const GEMINI_MODEL = "gemini-3.1-flash-lite";
const GEMINI_API_URL = (apiKey) =>
  `https://generativelanguage.googleapis.com/v1beta/models/${GEMINI_MODEL}:generateContent?key=${apiKey}`;

// ─── Static Fallback Data (JLR + Tata) ───────────────────────────────────────
const STATIC_FEEDBACK_ITEMS = [
  // ─── JLR Items ──────────────────────────────────────────────
  {
    id: "jlr-1", platform: "Reddit", author: "u/DefenderOwner_UK",
    date: "2026-07-01", event: "Defender 110", text: "Two years with my Defender 110 and it remains the most capable and characterful vehicle I've ever owned. Wade depth, air suspension, configurable terrain modes — it's genuinely unmatched for off-road versatility. The 11.4-inch Pivi Pro screen is slick, though software updates come too infrequently.",
    sentiment: "Positive", city: "Defender", isUpcoming: false, brand: "jlr",
    category_tag: "Off-road", priority_score: 2, action_insight: "Accelerate OTA software update cadence to match the premium ownership experience."
  },
  {
    id: "jlr-2", platform: "Twitter", author: "@RangeRoverLover",
    date: "2026-06-28", event: "Range Rover Sport", text: "Just had my Range Rover Sport in for its 3rd warranty repair in 8 months. Electrical gremlins, a faulty air suspension compressor, and now a leaking sunroof seal. The car is stunning but @LandRover's reliability record is genuinely damaging the brand. Dealer wait times for parts are also weeks, not days.",
    sentiment: "Negative", city: "Range Rover", isUpcoming: false, brand: "jlr",
    category_tag: "After-Sales", priority_score: 5, action_insight: "Prioritise pre-delivery inspection rigour and build a dedicated rapid-response parts logistics channel for warranty claims."
  },
  {
    id: "jlr-3", platform: "AutoExpress", author: "AutoExpress Expert",
    date: "2026-06-15", event: "I-PACE", text: "The Jaguar I-PACE remains an underappreciated electric SUV. Its 292-mile WLTP range holds up well in mixed real-world driving, the interior quality is exceptional for a 2019 design, and handling dynamics are genuinely sporty. Our main gripe is the 11kW AC charging ceiling — rivals now offer 22kW as standard.",
    sentiment: "Positive", city: "Jaguar", isUpcoming: false, brand: "jlr",
    category_tag: "EV Range", priority_score: 3, action_insight: "Upgrade the I-PACE to 22kW AC charging capability via a drivetrain update to stay competitive with BMW iX and Mercedes EQC."
  },
  {
    id: "jlr-4", platform: "Reddit", author: "u/JaguarFPACE_Owner",
    date: "2026-05-20", event: "F-PACE", text: "F-PACE SVR is an absolute rocket. The 5.0 supercharged V8 sounds incredible, 0–60 in 4.0s in a family SUV that can also carry school bags and a dog. Interior is lush with the Meridian sound system. Only complaint is the fuel economy — 17 mpg in mixed driving means weekly fill-ups.",
    sentiment: "Positive", city: "Jaguar", isUpcoming: false, brand: "jlr",
    category_tag: "Performance", priority_score: 2, action_insight: "Highlight the F-PACE SVR's performance-to-practicality ratio in marketing materials targeting premium SUV segment."
  },
  {
    id: "jlr-5", platform: "Trustpilot", author: "Sarah M.",
    date: "2026-06-10", event: "Range Rover Evoque", text: "Bought the Range Rover Evoque PHEV last year hoping for low running costs. Real-world electric range is 25 miles, not the 35 advertised. The dealer told us to 'always keep it charged' which isn't always possible. Overall ride quality is excellent and the design is stunning, but the PHEV promise feels misleading.",
    sentiment: "Neutral", city: "Range Rover", isUpcoming: false, brand: "jlr",
    category_tag: "EV Range", priority_score: 3, action_insight: "Improve transparency in PHEV real-world range communication and offer complimentary home charger installation with PHEV purchases."
  },
  {
    id: "jlr-6", platform: "Reddit", author: "u/DiscoverySportFamily",
    date: "2026-06-05", event: "Discovery Sport", text: "Discovery Sport has been our family car for 3 years. Seven seats, great driving position, kids love the space. The MHEV system genuinely saves fuel on long motorway runs. Infotainment could be more intuitive — the menus are buried. Depreciation is steep but ownership experience compensates.",
    sentiment: "Positive", city: "Discovery", isUpcoming: false, brand: "jlr",
    category_tag: "Comfort", priority_score: 2, action_insight: "Simplify the Pivi Pro menu hierarchy in the next OTA update, focusing on frequently used features within 2 taps."
  },
  {
    id: "jlr-7", platform: "AutoExpress", author: "AutoExpress Expert",
    date: "2026-07-05", event: "Defender OCTA", text: "The Defender OCTA is a statement vehicle — 626bhp, bespoke active dampers with 'Body and Soul Mode', and 32-inch tyre capability from the factory. JLR has created something genuinely unprecedented. Pricing above £130k is stratospheric but the OCTA delivers on its promise with zero compromises.",
    sentiment: "Positive", city: "Defender", isUpcoming: false, brand: "jlr",
    category_tag: "Performance", priority_score: 1, action_insight: "Leverage the OCTA's halo status in broader Defender marketing to elevate the entire Defender family perception."
  },
  {
    id: "jlr-8", platform: "Twitter", author: "@VelarOwner_Ldn",
    date: "2026-05-15", event: "Range Rover Velar", text: "Range Rover Velar interior is the most beautiful car interior I've sat in. Full-length panoramic roof, floating console, and the flush door handles are design perfection. Ride quality on 21-inch wheels can be firm on B-roads though. The P400e PHEV version balances luxury and efficiency well.",
    sentiment: "Positive", city: "Range Rover", isUpcoming: false, brand: "jlr",
    category_tag: "Design", priority_score: 2, action_insight: "Continue the Velar design language into next generation and consider adaptive suspension as standard on higher trims."
  },
  {
    id: "jlr-9", platform: "Reddit", author: "u/JLR_Pricing_Rant",
    date: "2026-04-22", event: "Defender 90", text: "Defender 90 starts at £45k but by the time you spec it properly — air suspension, panoramic roof, proper off-road pack — you're looking at £65k. The options list is predatory. Rival brands include far more as standard. Feels like JLR is nickel-and-diming loyal customers. Walk-away pricing is near Porsche territory.",
    sentiment: "Negative", city: "Defender", isUpcoming: false, brand: "jlr",
    category_tag: "Pricing", priority_score: 4, action_insight: "Introduce a 'Defender Ready Pack' bundling key off-road and comfort options at a 20% bundle discount to improve value perception."
  },
  {
    id: "jlr-10", platform: "Twitter", author: "@JLRElectricFan",
    date: "2026-07-08", event: "Upcoming Jaguar EV", text: "The new Jaguar electric lineup teased at the London reveal looks absolutely jaw-dropping. That GT silhouette with 430-mile range claim and 800V charging — if JLR delivers on this, it could genuinely rival Porsche Taycan. The rebrand to a luxury-only electric Jaguar is a bold and exciting move. Excited!",
    sentiment: "Positive", city: "Jaguar", isUpcoming: true, brand: "jlr",
    category_tag: "EV Range", priority_score: 2, action_insight: "Build pre-launch anticipation with a transparent reveal roadmap and early configurator access to capture deposit interest."
  },
  {
    id: "jlr-11", platform: "AutoExpress", author: "AutoExpress Expert",
    date: "2026-06-20", event: "Range Rover", text: "The long-wheelbase Range Rover remains the definitive statement of British luxury on four wheels. Rear-seat comfort rivals S-Class, the air suspension floats over imperfections, and the 4.4-litre V8 is silky smooth. Its blend of effortless refinement and genuine off-road ability is simply unmatched at any price.",
    sentiment: "Positive", city: "Range Rover", isUpcoming: false, brand: "jlr",
    category_tag: "Comfort", priority_score: 1, action_insight: "Maintain the benchmark standard; amplify rear-passenger experience storytelling in the flagship advertising campaign."
  },
  {
    id: "jlr-12", platform: "Trustpilot", author: "James T.",
    date: "2026-03-18", event: "Discovery", text: "Discovery 5 has been a brilliant all-rounder for our family of 5 plus two dogs. Third-row seats are genuinely usable for adults, towing capacity is class-leading, and the Terrain Response system is confidence-inspiring on muddy campsites. Only issue: the in-car software froze twice and needed a full reboot.",
    sentiment: "Positive", city: "Discovery", isUpcoming: false, brand: "jlr",
    category_tag: "Build Quality", priority_score: 2, action_insight: "Address infotainment stability issues in the next software release; consider a physical reset button as a failsafe."
  },
  {
    id: "jlr-13", platform: "Reddit", author: "u/EPaceOwner2025",
    date: "2026-05-30", event: "E-PACE", text: "E-PACE P300e is a punchy little thing with decent electric-first driving. Interior quality is solid for the segment. Main complaints: small boot with the PHEV battery eating into space, and the 9-speed auto gearbox can be reluctant when cold. Compared to a Volvo XC40 at this price it's a harder sell on practicality.",
    sentiment: "Neutral", city: "Jaguar", isUpcoming: false, brand: "jlr",
    category_tag: "Comfort", priority_score: 2, action_insight: "Repackage the E-PACE PHEV boot space with smarter storage solutions and improve gearbox thermal management calibration."
  },
  {
    id: "jlr-14", platform: "Twitter", author: "@DefenderTD4Dad",
    date: "2026-06-01", event: "Defender 130", text: "Defender 130 8-seater is the answer to our family's needs. Three rows of proper space, best-in-class towing at 3,500kg, and it looks epic on school runs. The reality of ownership: fuel economy at 24mpg diesel is acceptable, servicing is expensive, and parts lead times are too long. Worth it though.",
    sentiment: "Positive", city: "Defender", isUpcoming: false, brand: "jlr",
    category_tag: "Comfort", priority_score: 2, action_insight: "Improve parts availability and set 48-hour standard turnaround commitment for authorised dealers to enhance ownership satisfaction."
  },
  {
    id: "jlr-15", platform: "AutoExpress", author: "AutoExpress Expert",
    date: "2026-07-10", event: "Range Rover Sport", text: "The Range Rover Sport's mid-cycle refresh brings enhanced digital displays, improved acoustic glass throughout, and the addition of the HSE Ultimate trim. Performance remains outstanding — the 530bhp V8 variant is devastatingly quick for a vehicle of this size. Infotainment responsiveness has also been meaningfully improved.",
    sentiment: "Positive", city: "Range Rover", isUpcoming: false, brand: "jlr",
    category_tag: "Infotainment", priority_score: 1, action_insight: "Promote the infotainment upgrade prominently in CRM communications to existing Range Rover Sport owners."
  },

  // ─── Tata Motors Items ───────────────────────────────────────
  {
    id: "tata-1", platform: "Team-BHP", author: "Nexon_EV_Max_Owner",
    date: "2026-07-02", event: "Nexon EV", text: "Completed 40,000 km in my Nexon EV Max. Real-world range on the highway at 100kmph is around 290-310km from a full charge. Charging infrastructure at highways has improved massively — saw 3 working TATA Power chargers at every major toll stop on the Pune-Mumbai expressway. The car is genuinely practical for long trips now.",
    sentiment: "Positive", city: "EV", isUpcoming: false, brand: "tata",
    category_tag: "EV Range", priority_score: 2, action_insight: "Leverage the growing charging network narrative in EV marketing and publish real-world range data from owner communities."
  },
  {
    id: "tata-2", platform: "CarDekho", author: "Deepak Sharma",
    date: "2026-06-25", event: "Punch EV", text: "Tata Punch EV is the perfect city car for our family. At ₹9.9 lakh, the value proposition is hard to beat. Claimed 421km range, real-world I'm getting 280km in AC-heavy city use which is still excellent. Build quality feels premium for this segment. The rear parking camera image is pixelated though — needs an upgrade.",
    sentiment: "Positive", city: "EV", isUpcoming: false, brand: "tata",
    category_tag: "EV Range", priority_score: 2, action_insight: "Upgrade the rear camera resolution on the Punch EV as a quick-win quality improvement for next MY."
  },
  {
    id: "tata-3", platform: "Twitter", author: "@CurvvEV_Waitlist",
    date: "2026-07-12", event: "Curvv EV", text: "Finally saw the Tata Curvv EV at the showroom. That coupe-SUV design is genuinely stunning — stands out in traffic in a way no other Tata ever has. Booking open, delivery timeline given as 6-8 weeks. The 500km range variant at ₹17.5L is aggressively priced against MG ZS EV. Booked it!",
    sentiment: "Positive", city: "EV", isUpcoming: false, brand: "tata",
    category_tag: "Design", priority_score: 2, action_insight: "Capitalise on strong design reception with social media campaigns featuring customer first-delivery videos."
  },
  {
    id: "tata-4", platform: "Team-BHP", author: "Harrier_EV_Spotter",
    date: "2026-07-10", event: "Harrier EV", text: "Spotted the Tata Harrier EV test mule on NH48 near Pune. Looking production-ready with the Omega Arc design language. The spy shots show a new front fascia, no conventional grille, and larger alloys. If range matches the 500km target and pricing undercuts Hyundai Ioniq 5, this could be a game-changer for the segment.",
    sentiment: "Positive", city: "SUV", isUpcoming: true, brand: "tata",
    category_tag: "Design", priority_score: 2, action_insight: "Build pre-launch buzz through strategic spy shot acknowledgements and confirm range specification early to drive booking intent."
  },
  {
    id: "tata-5", platform: "CarDekho", author: "Anil Verma",
    date: "2026-06-18", event: "Safari", text: "Safari 7-seater is the best family road trip vehicle in India at this price. Superb suspension tuning for Indian roads — potholes and bumps are absorbed effortlessly. ADAS on the Adventure Plus trim is a genuine differentiator. Only drawback: the 2.0L Kryotec diesel has a noticeable delay in power delivery below 2000 RPM.",
    sentiment: "Positive", city: "SUV", isUpcoming: false, brand: "tata",
    category_tag: "Comfort", priority_score: 2, action_insight: "Recalibrate the Kryotec diesel torque curve in the low-RPM range to improve drivability in city stop-start traffic."
  },
  {
    id: "tata-6", platform: "Twitter", author: "@TiagoEV_Mumbai",
    date: "2026-05-28", event: "Tiago EV", text: "Tata Tiago EV has been my daily driver for 18 months. 170km real-world range in Mumbai city driving — perfectly adequate for my 40km daily commute with weekend charging only. ₹8.69L on-road is the best EV deal in India. Wish it had wireless CarPlay but at this price you can't complain.",
    sentiment: "Positive", city: "EV", isUpcoming: false, brand: "tata",
    category_tag: "EV Range", priority_score: 2, action_insight: "Add wireless CarPlay/Android Auto in the next Tiago EV refresh to address the most consistent user request."
  },
  {
    id: "tata-7", platform: "Team-BHP", author: "Nexon_EV_Service_Rant",
    date: "2026-06-08", event: "Nexon EV", text: "My Nexon EV (2022 model) has a battery cooling issue flagged since 8 months. The Tata service centre has had the car for 14 days cumulatively and still hasn't resolved it permanently. Battery pack replacement is pending but parts aren't available. Tata's after-sales EV service readiness is woefully inadequate for the fleet size they now have on roads.",
    sentiment: "Negative", city: "EV", isUpcoming: false, brand: "tata",
    category_tag: "After-Sales", priority_score: 5, action_insight: "Establish dedicated EV service centres with guaranteed SLAs and pre-positioned battery pack inventory at top 50 cities."
  },
  {
    id: "tata-8", platform: "CarDekho", author: "Priya Singh",
    date: "2026-05-15", event: "Altroz", text: "Altroz is hands-down the best-built hatchback in India under ₹10 lakh. The steel body rigidity, dual airbags as standard, and 5-star GNCAP rating make it the safety benchmark. My family switched from a Maruti Baleno for safety alone. Turbo petrol variant is peppy in the city. Slight wind noise above 80kmph.",
    sentiment: "Positive", city: "Hatchback", isUpcoming: false, brand: "tata",
    category_tag: "Safety", priority_score: 2, action_insight: "Lead the Altroz marketing with the 5-star GNCAP safety rating — parents and safety-conscious buyers respond strongly to this message."
  },
  {
    id: "tata-9", platform: "Twitter", author: "@PunchSUVOwner",
    date: "2026-06-20", event: "Punch", text: "Tata Punch micro-SUV is the perfect urban runabout. Ground clearance handles Mumbai's monsoon waterlogging beautifully. The AMT gearbox is smooth enough for stop-and-go traffic. Build quality feels solid. It's not the most powerful car — 86bhp — but for city use it's practically ideal. Best-selling Tata for a reason.",
    sentiment: "Positive", city: "SUV", isUpcoming: false, brand: "tata",
    category_tag: "Build Quality", priority_score: 1, action_insight: "Promote the Punch's ground clearance and build quality for monsoon season in regional social media campaigns."
  },
  {
    id: "tata-10", platform: "Team-BHP", author: "HarrierPetrol_Wait",
    date: "2026-04-30", event: "Harrier", text: "Waited 6 weeks for petrol Harrier delivery — finally have it. Compared to the diesel variant, the petrol is noticeably less torquey but more refined NVH-wise. ADAS suite is excellent with lane keep assist, adaptive cruise, and automatic emergency braking all working reliably. The 10.25-inch infotainment with wireless Android Auto is class-leading for this segment.",
    sentiment: "Neutral", city: "SUV", isUpcoming: false, brand: "tata",
    category_tag: "Infotainment", priority_score: 2, action_insight: "Reduce Harrier delivery timelines by increasing production allocation at the Pune plant for petrol variants."
  },
  {
    id: "tata-11", platform: "CarDekho", author: "Rahul Krishnan",
    date: "2026-06-02", event: "Nexon", text: "Tata Nexon is the complete package under ₹15 lakh — 5-star safety, punchy turbo petrol, compact footprint with 5-seat space, and a boot that takes a week's luggage. The Accomplished Plus Variant has ventilated seats which is a revelation in Indian summers. Sales numbers don't lie — this is India's best value compact SUV.",
    sentiment: "Positive", city: "SUV", isUpcoming: false, brand: "tata",
    category_tag: "Comfort", priority_score: 1, action_insight: "Expand ventilated seats to mid-range Nexon trims to broaden the appeal of the feature to a wider buyer base."
  },
  {
    id: "tata-12", platform: "Twitter", author: "@SierraEV_Eager",
    date: "2026-07-11", event: "Sierra EV", text: "Tata Sierra EV concept shown at Bharat Mobility is the nostalgia trip India needed! The retro boxy design with modern EV innards is genius branding. If they keep the unique square wheel arch design in production and price it around ₹30L, this will sell out bookings overnight. Cannot wait for the launch date announcement.",
    sentiment: "Positive", city: "EV", isUpcoming: true, brand: "tata",
    category_tag: "Design", priority_score: 2, action_insight: "Preserve the distinctive design language of the Sierra EV concept in production spec to maximise its nostalgia and brand differentiation premium."
  },
  {
    id: "tata-13", platform: "Team-BHP", author: "TiagoEV_Range_Reality",
    date: "2026-05-05", event: "Tiago EV", text: "Honest Tiago EV review after 12 months: the 315km WLTP range translates to ~180-200km in real-world conditions with AC on. For a ₹8L car this is acceptable, but Tata should communicate realistic range better. Charging from 20-80% takes 57 minutes on a 7.2kW home charger, which fits overnight comfortably. Good value EV overall.",
    sentiment: "Neutral", city: "EV", isUpcoming: false, brand: "tata",
    category_tag: "EV Range", priority_score: 3, action_insight: "Publish real-world range data under Indian AC-on driving conditions in all Tiago EV marketing to manage buyer expectations proactively."
  },
  {
    id: "tata-14", platform: "CarDekho", author: "Vikram Patel",
    date: "2026-06-30", event: "Curvv", text: "Tata Curvv ICE is a compelling buy at ₹11-18L. That coupe roofline actually works in India — the rear headroom is better than expected, and boot space is adequate at 500 litres. The diesel variant returns 20kmpl on highways which is excellent for a segment that tends to prioritise petrol. Might wait for the EV version though.",
    sentiment: "Neutral", city: "SUV", isUpcoming: false, brand: "tata",
    category_tag: "Comfort", priority_score: 2, action_insight: "Use the Curvv diesel's highway efficiency figures prominently in targeting long-distance commuter buyer segments."
  },
  {
    id: "tata-15", platform: "Twitter", author: "@XPRESFleetMgr",
    date: "2026-06-15", event: "XPRES-T EV", text: "Running 20 XPRES-T EVs in our corporate fleet for 14 months. TCO versus equivalent diesel is already positive — electricity cost vs fuel saving is ₹2.8/km cheaper. Uptime has been good with 97% availability. Tata Fleet Management support is responsive. Main ask: a larger battery option — 165km city range sometimes limits the evening shift.",
    sentiment: "Positive", city: "EV", isUpcoming: false, brand: "tata",
    category_tag: "EV Range", priority_score: 3, action_insight: "Develop an extended range XPRES-T variant with 250km+ city cycle battery for corporate fleet operators running extended duty cycles."
  },
];

function App() {
  const [activeBrand, setActiveBrand] = useState("jlr"); // "jlr" | "tata"
  const [activeTab, setActiveTab] = useState("dashboard");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedPlatform, setSelectedPlatform] = useState(null);
  const [selectedSentiment, setSelectedSentiment] = useState(null);
  const [selectedBrandGroup, setSelectedBrandGroup] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState(null);

  const [allItems, setAllItems] = useState([]);
  const [feedItems, setFeedItems] = useState([]);
  const [stats, setStats] = useState({
    totalFeedbackCount: 0,
    sentimentPercentages: { Positive: 0, Neutral: 0, Negative: 0 },
    platformCounts: {},
    cityCounts: {},
  });
  const [analytics, setAnalytics] = useState(null);
  const [jlrAnalytics, setJlrAnalytics] = useState(null);
  const [tataAnalytics, setTataAnalytics] = useState(null);

  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState("");
  const [isChatLoading, setIsChatLoading] = useState(false);
  const [chatError, setChatError] = useState(null);
  const [geminiApiKey, setGeminiApiKey] = useState(ENV_GEMINI_KEY);

  const chatEndRef = useRef(null);

  // Update chat welcome message when brand changes
  useEffect(() => {
    const jlrMsg = "Hello! I'm your JLR Intelligence Assistant. I've indexed customer reviews, owner feedback, and expert opinions across Jaguar, Range Rover, Defender, and Discovery models. Ask me anything — sentiment analysis, model comparisons, common issues, or praise themes!";
    const tataMsg = "Hello! I'm your Tata Motors Intelligence Assistant. I've indexed reviews and owner experiences across Nexon EV, Punch EV, Curvv EV, Harrier, Safari, Tiago EV, and more. Ask about EV range, after-sales quality, model comparisons, or price-value analysis!";
    setChatMessages([{ sender: "BOT", text: activeBrand === "jlr" ? jlrMsg : tataMsg, timestamp: Date.now() }]);
  }, [activeBrand]);

  useEffect(() => {
    if (ENV_GEMINI_KEY) return;
    const savedKey = localStorage.getItem("jlr-tata-review-gemini-key");
    if (savedKey) setGeminiApiKey(savedKey);
  }, []);

  const getStatsForItems = (items) => {
    const total = items.length;
    if (total === 0) return { totalFeedbackCount: 0, sentimentPercentages: { Positive: 0, Neutral: 0, Negative: 0 }, platformCounts: {}, cityCounts: {} };
    const sc = { Positive: 0, Neutral: 0, Negative: 0 };
    const pc = {}, cc = {};
    items.forEach((item) => {
      sc[item.sentiment] = (sc[item.sentiment] || 0) + 1;
      pc[item.platform] = (pc[item.platform] || 0) + 1;
      cc[item.city] = (cc[item.city] || 0) + 1;
    });
    return {
      totalFeedbackCount: total,
      sentimentPercentages: {
        Positive: (sc.Positive / total) * 100,
        Neutral: (sc.Neutral / total) * 100,
        Negative: (sc.Negative / total) * 100,
      },
      platformCounts: pc,
      cityCounts: cc,
    };
  };

  const loadStaticData = async () => {
    let items = STATIC_FEEDBACK_ITEMS;
    let analyticsData = null, jlrA = null, tataA = null;
    try {
      const res = await fetch(STATIC_DATA_URL);
      if (res.ok) {
        const data = await res.json();
        items = data.items || items;
        analyticsData = data.analytics || null;
        jlrA = data.jlrAnalytics || null;
        tataA = data.tataAnalytics || null;
      }
    } catch { /* Fall back to static data */ }
    setAllItems(items);
    setAnalytics(analyticsData);
    setJlrAnalytics(jlrA);
    setTataAnalytics(tataA);
  };

  useEffect(() => { loadStaticData(); }, []);

  // Filter items by active brand + all filters
  useEffect(() => {
    const source = allItems.length ? allItems : STATIC_FEEDBACK_ITEMS;
    let filtered = source.filter((item) => item.brand === activeBrand);
    if (selectedPlatform) filtered = filtered.filter((i) => i.platform === selectedPlatform);
    if (selectedSentiment) filtered = filtered.filter((i) => i.sentiment === selectedSentiment);
    if (selectedBrandGroup) filtered = filtered.filter((i) => i.city === selectedBrandGroup);
    if (selectedCategory) filtered = filtered.filter((i) => i.category_tag === selectedCategory);
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      filtered = filtered.filter((i) => i.text.toLowerCase().includes(q) || i.event.toLowerCase().includes(q) || i.author.toLowerCase().includes(q));
    }
    setFeedItems(filtered);
    setStats(getStatsForItems(filtered.length ? filtered : source.filter((i) => i.brand === activeBrand)));
  }, [searchQuery, selectedPlatform, selectedSentiment, selectedBrandGroup, selectedCategory, allItems, activeBrand]);

  useEffect(() => {
    if (chatEndRef.current) chatEndRef.current.scrollIntoView({ behavior: "smooth" });
  }, [chatMessages, isChatLoading]);

  const handleClearFilters = () => {
    setSearchQuery(""); setSelectedPlatform(null);
    setSelectedSentiment(null); setSelectedBrandGroup(null); setSelectedCategory(null);
  };

  const handleBrandSwitch = (brand) => {
    setActiveBrand(brand);
    handleClearFilters();
    setActiveTab("dashboard");
  };

  // Dynamic follow-up suggestion chips state
  const [activeFollowUps, setActiveFollowUps] = useState([]);

  // AI Chat — Enhanced RAG context builder (weighted TF-IDF approach)
  const buildChatContext = (query, items, limit = 8) => {
    const cleanQuery = query.toLowerCase().replace(/[^a-z0-9\s]/g, "");
    const queryWords = cleanQuery.split(/\s+/).filter(w => w.length > 2);
    
    // Stop words to ignore when matching
    const stops = new Set(["the", "and", "for", "with", "this", "that", "about", "car", "vehicle", "model"]);
    const queryKeywords = queryWords.filter(w => !stops.has(w));
    
    const scored = items.map((item) => {
      const textLower = item.text.toLowerCase();
      const eventLower = item.event.toLowerCase();
      const categoryLower = item.category_tag.toLowerCase();
      let score = 0;
      
      queryKeywords.forEach((word) => {
        // Model match gets very high weight
        if (eventLower.includes(word)) score += 5;
        // Category/theme match gets high weight
        if (categoryLower.includes(word)) score += 3;
        // Text keyword occurrences
        const regex = new RegExp(`\\b${word}\\b`, "g");
        const count = (textLower.match(regex) || []).length;
        score += count;
      });
      return { item, score };
    });

    // Filter out items with 0 score if there are enough matches, else fallback to standard
    const positiveScored = scored.filter(s => s.score > 0);
    const targetList = positiveScored.length > 0 ? positiveScored : scored;
    
    targetList.sort((a, b) => b.score - a.score);
    return targetList.slice(0, limit).map((s) => s.item);
  };

  const buildAnalyticsContext = (analyticsObj) => {
    if (!analyticsObj) return "No analytics summary available.";
    const issues = analyticsObj.keyIssues || [];
    const praises = analyticsObj.topPraises || [];
    const events = analyticsObj.topEvents || [];
    const terms = analyticsObj.trendingTerms || [];
    const pos = analyticsObj.topPositivePosts || [];
    const neg = analyticsObj.topNegativePosts || [];
    const formatList = (arr, key = "theme") => arr.map((x) => x[key]).filter(Boolean).join(", ") || "none";
    return (
      `Analytics: ${analyticsObj.executiveSummary || "No summary."}\n` +
      `Key issues: ${formatList(issues)}\nTop praises: ${formatList(praises)}\n` +
      `Most reviewed models: ${formatList(events, "event")}\nTrending terms: ${formatList(terms, "term")}\n` +
      `Top positive: ${pos.map((p) => p.text).join(" | ") || "none"}\n` +
      `Top negative: ${neg.map((p) => p.text).join(" | ") || "none"}`
    );
  };

  const handleSendChat = async (text) => {
    if (!text.trim() || isChatLoading) return;
    const trimmed = text.trim();
    if (!geminiApiKey.trim()) { setChatError("Please enter your Gemini API key."); return; }

    const userMessage = { sender: "USER", text: trimmed, timestamp: Date.now() };
    setChatMessages((prev) => [...prev, userMessage]);
    setChatInput("");
    setIsChatLoading(true);
    setChatError(null);

    // Cache lookup key
    const cacheKey = `jlr-tata-chat-cache-${activeBrand}-${trimmed.toLowerCase()}`;
    const cachedResponse = sessionStorage.getItem(cacheKey);

    if (cachedResponse) {
      try {
        const parsed = JSON.parse(cachedResponse);
        setChatMessages((prev) => [...prev, { sender: "BOT", text: parsed.answer, timestamp: Date.now() }]);
        setActiveFollowUps(parsed.followUps || []);
        setIsChatLoading(false);
        return;
      } catch (e) {
        sessionStorage.removeItem(cacheKey);
      }
    }

    const source = allItems.length ? allItems : STATIC_FEEDBACK_ITEMS;
    const brandItems = source.filter((i) => i.brand === activeBrand);
    const contextItems = buildChatContext(trimmed, brandItems, 10);
    const contextText = contextItems.map((item) =>
      `- [Sentiment: ${item.sentiment}] Model: ${item.event} | Tag: #${item.category_tag} | Review: ${item.text}`
    ).join("\n");

    const brandLabel = activeBrand === "jlr" ? "JLR (Jaguar Land Rover)" : "Tata Motors";
    const activeAnalytics = activeBrand === "jlr" ? jlrAnalytics : tataAnalytics;
    const analyticsContext = buildAnalyticsContext(activeAnalytics || analytics);

    const prompt = `You are a ${brandLabel} Vehicle Intelligence Assistant. You analyze customer reviews, owner feedback, and expert opinions for ${brandLabel} vehicles.

Your output must be a valid JSON object matching this structure exactly (do not output any markdown wrappers or extra characters):
{
  "answer": "Your detailed, concise response to the user's question, citing models and percentages when appropriate.",
  "followUps": [
    "A short follow-up question the user might want to ask next",
    "Another follow-up question",
    "A third follow-up question"
  ]
}

Make sure the followUps questions are highly relevant, specific, and based on the answer you provided.

ANALYTICS SUMMARY:
${analyticsContext}

REVIEW CONTEXT:
${contextText}

User question: ${trimmed}`;

    try {
      const res = await fetch(GEMINI_API_URL(geminiApiKey), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          contents: [{ role: "user", parts: [{ text: prompt }] }],
          generationConfig: {
            responseMimeType: "application/json",
            temperature: 0.2
          }
        }),
      });
      if (!res.ok) throw new Error("Gemini API request failed.");
      const data = await res.json();
      const rawText = data?.candidates?.[0]?.content?.parts?.[0]?.text || "{}";
      
      const parsed = JSON.parse(rawText);
      const botAnswer = parsed.answer || "No response generated.";
      const followUps = parsed.followUps || [];

      // Save to cache
      sessionStorage.setItem(cacheKey, JSON.stringify({ answer: botAnswer, followUps }));

      setChatMessages((prev) => [...prev, { sender: "BOT", text: botAnswer, timestamp: Date.now() }]);
      setActiveFollowUps(followUps);
    } catch (e) {
      console.error(e);
      setChatError("Gemini API call failed. Check your API key and try again.");
      setChatMessages((prev) => [...prev, { sender: "BOT", text: "❌ Error: Gemini API call failed. Please check your API key.", timestamp: Date.now() }]);
      setActiveFollowUps([]);
    } finally {
      setIsChatLoading(false);
    }
  };

  // Donut chart calculations
  const radius = 35, circ = 2 * Math.PI * radius;
  const positivePct = stats.sentimentPercentages.Positive || 0;
  const neutralPct = stats.sentimentPercentages.Neutral || 0;
  const negativePct = stats.sentimentPercentages.Negative || 0;
  const posStroke = (positivePct / 100) * circ, posOffset = 0;
  const neuStroke = (neutralPct / 100) * circ, neuOffset = posStroke;
  const negStroke = (negativePct / 100) * circ, negOffset = posStroke + neuStroke;

  const isJLR = activeBrand === "jlr";

  // Brand-specific config
  const brandConfig = {
    jlr: {
      label: "Jaguar Land Rover",
      shortLabel: "JLR",
      tagline: "LUXURY · PERFORMANCE · CAPABILITY",
      groups: ["Jaguar", "Range Rover", "Defender", "Discovery"],
      platforms: ["Twitter", "Reddit", "AutoExpress", "Trustpilot"],
      groupLabel: "Brand Family",
      kpi3Label: "EV Models",
      kpi3Value: feedItems.filter((i) => i.event.toLowerCase().includes("pace") || i.event.toLowerCase().includes("electric") || i.event.toLowerCase().includes("ev") || i.event.toLowerCase().includes("phev")).length,
      trends: [
        {
          emoji: "⚡", bgColor: "rgba(74, 124, 89, 0.2)",
          title: "Upcoming Jaguar EV Lineup",
          description: "Massive pre-launch buzz around the all-electric Jaguar GT and SUV models. 430-mile range claims and 800V charging architecture generating strong positive sentiment. Potential to rival Porsche Taycan if delivery matches the promise."
        },
        {
          emoji: "🛡️", bgColor: "rgba(201, 168, 76, 0.15)",
          title: "Defender OCTA — Halo Effect",
          description: "The 626bhp Defender OCTA has been universally praised by media and enthusiasts, elevating the entire Defender family. Owners report strong community pride and aspirational positioning for the broader range."
        },
      ],
      retrospective: [
        {
          emoji: "⚠️", bgColor: "rgba(239, 68, 68, 0.1)",
          title: "Reliability & After-Sales Concerns",
          description: "Recurring complaints about warranty repair frequencies, parts wait times exceeding weeks, and electrical fault patterns across Range Rover Sport and I-PACE models. Brand reputation risk is significant."
        },
        {
          emoji: "✨", bgColor: "rgba(201, 168, 76, 0.12)",
          title: "Pricing & Options Perception",
          description: "Defender and Range Rover options lists are widely criticised as predatory, with base prices understating real acquisition cost by 30-40%. Recommendation: introduce bundled value packs."
        },
        {
          emoji: "🔋", bgColor: "rgba(14, 165, 233, 0.1)",
          title: "PHEV Real-World Range Gap",
          description: "Both Evoque and E-PACE PHEV owners report real-world electric range 25-30% below WLTP figures. Transparent real-world range communication requested by community."
        },
      ],
      suggestedQuestions: [
        "Top 5 reliability issues across JLR models",
        "Compare Range Rover vs Defender sentiment",
        "What do I-PACE owners say about range?",
        "Most praised aspects of Defender ownership",
        "What are the top after-sales complaints?",
        "Which JLR model has the best sentiment score?",
        "Summarise pricing complaints across the lineup",
        "What makes the Defender OCTA stand out?",
      ],
      botName: "JLR INTELLIGENCE BOT",
    },
    tata: {
      label: "Tata Motors",
      shortLabel: "Tata",
      tagline: "INNOVATION · VALUE · EV LEADERSHIP",
      groups: ["EV", "SUV", "Hatchback", "Sedan"],
      platforms: ["Twitter", "Team-BHP", "CarDekho", "Zigwheels"],
      groupLabel: "Segment",
      kpi3Label: "EV Models",
      kpi3Value: feedItems.filter((i) => i.event.toLowerCase().includes("ev") || i.city === "EV").length,
      trends: [
        {
          emoji: "⚡", bgColor: "rgba(0, 97, 213, 0.15)",
          title: "Sierra EV & Harrier EV — Pre-Launch Buzz",
          description: "Strong anticipation around the Sierra EV's retro-modern design and the Harrier EV's 500km range promise. Both models generating significant social media engagement and early booking intent ahead of official launch dates."
        },
        {
          emoji: "🏆", bgColor: "rgba(232, 184, 75, 0.15)",
          title: "Curvv EV — Coupe-SUV Disruption",
          description: "Tata Curvv EV has generated exceptional design reception. Its coupe-SUV form factor is seen as a disruptive move in the Indian EV market, with competitive pricing vs MG ZS EV and Hyundai Ioniq."
        },
      ],
      retrospective: [
        {
          emoji: "🔧", bgColor: "rgba(239, 68, 68, 0.1)",
          title: "EV After-Sales Service Gap",
          description: "Nexon EV battery issue resolution times (14+ days) and parts unavailability are the top complaints. The fleet size has outgrown the EV service infrastructure. Dedicated EV service centres with guaranteed SLAs are urgently needed."
        },
        {
          emoji: "📡", bgColor: "rgba(0, 97, 213, 0.1)",
          title: "Real-World EV Range Communication",
          description: "Both Tiago EV and Nexon EV owners report real-world range 25-35% below WLTP figures with AC on. Community asking for India-specific (AC-on, city cycle) range publishing in all marketing materials."
        },
        {
          emoji: "🌟", bgColor: "rgba(16, 185, 129, 0.1)",
          title: "Value-for-Money Leadership",
          description: "Tata's EV lineup (Tiago EV, Punch EV, Nexon EV) consistently praised for industry-leading value at each price point. The ₹8.69L Tiago EV is widely regarded as India's best-value EV."
        },
      ],
      suggestedQuestions: [
        "Top complaints about Nexon EV ownership",
        "Compare Punch EV vs Tiago EV sentiment",
        "What is the real-world range feedback for Tata EVs?",
        "Harrier EV pre-launch buzz summary",
        "What makes the Altroz stand out for safety?",
        "Most praised Tata model overall",
        "After-sales service issues across Tata EVs",
        "Sierra EV excitement — what are owners saying?",
      ],
      botName: "TATA MOTORS INTELLIGENCE BOT",
    },
  };

  const cfg = brandConfig[activeBrand];

  const brandGroupCounts = {};
  cfg.groups.forEach((g) => {
    const src = allItems.length ? allItems : STATIC_FEEDBACK_ITEMS;
    brandGroupCounts[g] = src.filter((i) => i.brand === activeBrand && i.city === g).length;
  });
  const totalBrandItems = Object.values(brandGroupCounts).reduce((a, b) => a + b, 0) || 1;

  return (
    <div className={`app-container brand-${activeBrand}`}>
      <Analytics />
      <SpeedInsights />

      {/* Brand Switcher Header */}
      <header className="app-header">
        <div className="brand-switcher-container">
          <button
            className={`brand-switch-btn brand-jlr-btn ${activeBrand === "jlr" ? "active" : ""}`}
            onClick={() => handleBrandSwitch("jlr")}
            id="brand-switch-jlr"
          >
            <div className="brand-switch-emblem jlr-emblem">
              <svg viewBox="0 0 32 32" width="22" height="22" fill="none">
                <path d="M16 3L29 9v14L16 29 3 23V9z" stroke="currentColor" strokeWidth="1.5" fill="rgba(74,124,89,0.2)"/>
                <path d="M10 16h12M16 10v12" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
              </svg>
            </div>
            <div className="brand-switch-text">
              <span className="bsw-label">Jaguar Land Rover</span>
              <span className="bsw-sub">JLR · LUXURY & PERFORMANCE</span>
            </div>
            {activeBrand === "jlr" && <span className="bsw-active-dot" />}
          </button>

          <div className="brand-divider">
            <span>|</span>
          </div>

          <button
            className={`brand-switch-btn brand-tata-btn ${activeBrand === "tata" ? "active" : ""}`}
            onClick={() => handleBrandSwitch("tata")}
            id="brand-switch-tata"
          >
            <div className="brand-switch-emblem tata-emblem">
              <svg viewBox="0 0 32 32" width="22" height="22" fill="none">
                <circle cx="16" cy="16" r="12" stroke="currentColor" strokeWidth="1.5" fill="rgba(0,97,213,0.15)"/>
                <path d="M8 16h16M16 8v16" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"/>
                <circle cx="16" cy="16" r="3" fill="currentColor"/>
              </svg>
            </div>
            <div className="brand-switch-text">
              <span className="bsw-label">Tata Motors</span>
              <span className="bsw-sub">INNOVATION · EV LEADERSHIP</span>
            </div>
            {activeBrand === "tata" && <span className="bsw-active-dot" />}
          </button>
        </div>

        <div className="header-actions">
          <button className="reset-button" onClick={handleClearFilters} title="Reset all filters">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67" />
            </svg>
            Reset
          </button>
        </div>
      </header>

      {/* Navigation Tabs */}
      <nav className="tab-navigation">
        {[
          { id: "dashboard", icon: <><rect x="3" y="3" width="7" height="9"/><rect x="14" y="3" width="7" height="5"/><rect x="14" y="12" width="7" height="9"/><rect x="3" y="16" width="7" height="5"/></>, label: "Dashboard" },
          { id: "insights", icon: <><path d="M18 20V10"/><path d="M12 20V4"/><path d="M6 20v-6"/></>, label: "Insights" },
          { id: "chat", icon: <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>, label: "AI Chat" },
          { id: "explorer", icon: <><circle cx="12" cy="12" r="10"/><polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"/></>, label: "Feed Explorer" },
        ].map(({ id, icon, label }) => (
          <button key={id} className={`nav-tab ${activeTab === id ? "active" : ""}`} onClick={() => setActiveTab(id)}>
            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="tab-icon">{icon}</svg>
            {label}
          </button>
        ))}
      </nav>

      {/* Main Content */}
      <main className="app-content-body">

        {/* ── DASHBOARD TAB ── */}
        {activeTab === "dashboard" && (
          <div className="tab-content fade-in">
            {/* Banner */}
            <section className="dashboard-banner">
              <div className="banner-top">
                <span className="banner-badge">{isJLR ? "JLR VEHICLE INTELLIGENCE" : "TATA MOTORS INTELLIGENCE"}</span>
                <span className="banner-emoji">{isJLR ? "🚗" : "⚡"}</span>
              </div>
              <h2>{cfg.label} — Customer Review Intelligence</h2>
              <p>
                {isJLR
                  ? "Aggregated owner reviews, expert opinions, and customer feedback from Reddit, AutoExpress, and Trustpilot across Jaguar, Range Rover, Defender, and Discovery models."
                  : "Aggregated owner reviews and customer feedback from Team-BHP, CarDekho, and Twitter across the full Tata Motors lineup including EV models."}
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
                <span className="kpi-title">Reviews</span>
                <span className="kpi-value">{stats.totalFeedbackCount}</span>
                <span className="kpi-subtitle">INDEXED</span>
              </div>
              <div className="kpi-card events-kpi">
                <span className="kpi-title">{cfg.kpi3Label}</span>
                <span className="kpi-value">{isJLR ? feedItems.filter(i => i.isUpcoming).length : feedItems.filter(i => i.city === "EV").length}</span>
                <span className="kpi-subtitle">{isJLR ? "UPCOMING" : "EV MODELS"}</span>
              </div>
            </section>

            {/* Metrics Split */}
            <div className="dashboard-metrics-split">
              {/* Donut chart */}
              <section className="metrics-card chart-card">
                <h3>
                  <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ color: "var(--color-primary)", marginRight: "8px" }}>
                    <line x1="18" y1="20" x2="18" y2="10" /><line x1="12" y1="20" x2="12" y2="4" /><line x1="6" y1="20" x2="6" y2="14" />
                  </svg>
                  Sentiment Breakdown
                </h3>
                <div className="chart-container">
                  <div className="donut-chart-wrapper">
                    <svg viewBox="0 0 100 100" className="donut-chart">
                      <g transform="rotate(-90 50 50)">
                        {positivePct > 0 && <circle cx="50" cy="50" r={radius} fill="transparent" stroke="#10b981" strokeWidth="10" strokeDasharray={`${posStroke} ${circ}`} strokeDashoffset={-posOffset} strokeLinecap="round" />}
                        {neutralPct > 0 && <circle cx="50" cy="50" r={radius} fill="transparent" stroke="#f59e0b" strokeWidth="10" strokeDasharray={`${neuStroke} ${circ}`} strokeDashoffset={-neuOffset} strokeLinecap="round" />}
                        {negativePct > 0 && <circle cx="50" cy="50" r={radius} fill="transparent" stroke="#ef4444" strokeWidth="10" strokeDasharray={`${negStroke} ${circ}`} strokeDashoffset={-negOffset} strokeLinecap="round" />}
                      </g>
                    </svg>
                    <div className="donut-chart-center">
                      <span className="donut-pct">{Math.round(positivePct)}%</span>
                      <span className="donut-lbl">Positive</span>
                    </div>
                  </div>
                  <div className="chart-legend">
                    <div className="legend-item"><span className="legend-indicator positive" /><span className="legend-name">Positive</span><span className="legend-count">{feedItems.filter(i => i.sentiment === "Positive").length} ({Math.round(positivePct)}%)</span></div>
                    <div className="legend-item"><span className="legend-indicator neutral" /><span className="legend-name">Neutral</span><span className="legend-count">{feedItems.filter(i => i.sentiment === "Neutral").length} ({Math.round(neutralPct)}%)</span></div>
                    <div className="legend-item"><span className="legend-indicator negative" /><span className="legend-name">Negative</span><span className="legend-count">{feedItems.filter(i => i.sentiment === "Negative").length} ({Math.round(negativePct)}%)</span></div>
                  </div>
                </div>
              </section>

              {/* Brand group + model counts */}
              <div className="counts-cards-subgrid">
                <section className="metrics-card platform-card">
                  <h3 className="primary-text">{cfg.groupLabel} Breakdown</h3>
                  <div className="platform-bars-list">
                    {cfg.groups.map((g, i) => (
                      <PlatformBar key={g} label={g} count={brandGroupCounts[g] || 0} total={totalBrandItems}
                        color={isJLR ? ["#4a7c59", "#c9a84c", "#2d6a4f", "#a78b3e"][i] : ["#0061d5", "#e8b84b", "#0047ab", "#c49a0a"][i]} />
                    ))}
                  </div>
                </section>

                <section className="metrics-card cities-card">
                  <h3 className="secondary-text">Top Reviewed Models</h3>
                  <div className="cities-list">
                    {(() => {
                      const src = allItems.length ? allItems : STATIC_FEEDBACK_ITEMS;
                      const brandFiltered = src.filter(i => i.brand === activeBrand);
                      const modelCounts = {};
                      brandFiltered.forEach(i => { modelCounts[i.event] = (modelCounts[i.event] || 0) + 1; });
                      return Object.entries(modelCounts).sort((a, b) => b[1] - a[1]).slice(0, 6).map(([model, count]) => (
                        <CityItem key={model} label={model} count={count} />
                      ));
                    })()}
                  </div>
                </section>
              </div>
            </div>

            {/* Trend Intelligence + Retrospective */}
            <div className="dashboard-insights-grid">
              <section className="metrics-card insights-card">
                <div className="card-header-row">
                  <h3>
                    <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ color: "var(--color-primary)", marginRight: "8px" }}>
                      <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>
                    </svg>
                    Trend Intelligence
                  </h3>
                  <span className="sync-badge">Live Indexed</span>
                </div>
                <div className="insights-list">
                  {cfg.trends.map((t, i) => (
                    <InsightItem key={i} emoji={t.emoji} bgColor={t.bgColor} title={t.title} description={t.description} />
                  ))}
                </div>
              </section>

              <section className="metrics-card insights-card">
                <div className="card-header-row">
                  <h3>
                    <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ color: "var(--color-secondary)", marginRight: "8px" }}>
                      <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/>
                    </svg>
                    Retrospective Insights
                  </h3>
                  <span className="sync-badge sec">Consolidated</span>
                </div>
                <div className="insights-list">
                  {cfg.retrospective.map((r, i) => (
                    <InsightItem key={i} emoji={r.emoji} bgColor={r.bgColor} title={r.title} description={r.description} />
                  ))}
                </div>
              </section>
            </div>

            {/* Priority + Actionable */}
            <div className="dashboard-insights-grid" style={{ marginTop: "24px" }}>
              <section className="metrics-card insights-card" style={{ flex: 1.2 }}>
                <h3>
                  <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ color: "var(--color-negative)", marginRight: "8px" }}>
                    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
                  </svg>
                  Priority Indicators
                </h3>
                <p style={{ margin: 0, fontSize: "0.75rem", color: "var(--text-muted)", fontStyle: "italic" }}>
                  *Priority scores are AI-generated from sentiment analysis severity.
                </p>
                <div style={{ display: "flex", flexDirection: "column", gap: "12px", marginTop: "12px", maxHeight: "350px", overflowY: "auto" }}>
                  {(allItems.length ? allItems : STATIC_FEEDBACK_ITEMS)
                    .filter(i => i.brand === activeBrand && (i.priority_score || 1) >= 4)
                    .slice(0, 4)
                    .map((item) => (
                      <div key={item.id} style={{ padding: "10px 14px", borderRadius: "8px", backgroundColor: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.18)", borderLeft: "4px solid var(--color-negative)" }}>
                        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px", fontSize: "0.8rem" }}>
                          <strong style={{ color: "var(--text-primary)" }}>{item.event} · {item.platform}</strong>
                          <span style={{ color: "var(--color-negative)", fontWeight: "bold" }}>{"★".repeat(item.priority_score)}</span>
                        </div>
                        <p style={{ margin: 0, fontSize: "0.82rem", color: "var(--text-secondary)" }}>{item.text.slice(0, 180)}...</p>
                      </div>
                    ))}
                  {(allItems.length ? allItems : STATIC_FEEDBACK_ITEMS).filter(i => i.brand === activeBrand && (i.priority_score || 1) >= 4).length === 0 && (
                    <p style={{ color: "var(--text-muted)", fontSize: "0.85rem", fontStyle: "italic" }}>No critical priority items found in current data.</p>
                  )}
                </div>
              </section>

              <section className="metrics-card insights-card" style={{ flex: 1 }}>
                <h3>
                  <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ color: "var(--color-positive)", marginRight: "8px" }}>
                    <circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/>
                  </svg>
                  Actionable Insights
                </h3>
                <div style={{ display: "flex", flexDirection: "column", gap: "12px", marginTop: "12px", maxHeight: "350px", overflowY: "auto" }}>
                  {(allItems.length ? allItems : STATIC_FEEDBACK_ITEMS)
                    .filter(i => i.brand === activeBrand && i.action_insight && i.action_insight !== "No recommendation." && (i.priority_score || 1) >= 3)
                    .slice(0, 4)
                    .map((item) => (
                      <div key={item.id} style={{ padding: "10px 14px", borderRadius: "8px", backgroundColor: "rgba(16,185,129,0.08)", border: "1px solid rgba(16,185,129,0.18)", borderLeft: "4px solid var(--color-positive)" }}>
                        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px", fontSize: "0.8rem" }}>
                          <span style={{ fontWeight: "600", color: "var(--text-primary)" }}>{item.event}</span>
                          <span style={{ color: "var(--text-muted)" }}>#{item.category_tag}</span>
                        </div>
                        <p style={{ margin: 0, fontSize: "0.82rem", fontStyle: "italic", color: "var(--text-secondary)" }}>"{item.action_insight}"</p>
                      </div>
                    ))}
                </div>
              </section>
            </div>
          </div>
        )}

        {/* ── INSIGHTS TAB ── */}
        {activeTab === "insights" && (
          <div className="tab-content insights-tab fade-in">
            <InsightsTab
              analytics={activeBrand === "jlr" ? (jlrAnalytics || analytics) : (tataAnalytics || analytics)}
              stats={stats}
              brand={activeBrand}
              brandLabel={cfg.label}
              onTrendClick={(term) => { setSearchQuery(term); setActiveTab("explorer"); }}
            />
          </div>
        )}

        {/* ── AI CHAT TAB ── */}
        {activeTab === "chat" && (
          <div className="tab-content chat-tab fade-in">
            {!ENV_GEMINI_KEY && (
              <div className="chat-key-prompt">
                <label htmlFor="gemini-key">Gemini API Key</label>
                <input
                  id="gemini-key" type="password" value={geminiApiKey}
                  onChange={(e) => { setGeminiApiKey(e.target.value); localStorage.setItem("jlr-tata-review-gemini-key", e.target.value); }}
                  placeholder="Paste your Gemini API key here"
                />
                <span className="key-hint">Stored only in this browser.</span>
              </div>
            )}

            <div className="chat-messages-container">
              {chatMessages.map((msg, idx) => (
                <div key={idx} className={`chat-bubble-row ${msg.sender === "USER" ? "user-row" : "bot-row"}`}>
                  <div className="chat-bubble">
                    <span className="bubble-sender">{msg.sender === "USER" ? "YOU" : cfg.botName}</span>
                    <p className="bubble-text">{msg.text}</p>
                  </div>
                </div>
              ))}
              {isChatLoading && (
                <div className="chat-bubble-row bot-row">
                  <div className="chat-bubble loading-bubble">
                    <div className="typing-loader"><span/><span/><span/></div>
                    <span className="loading-text">Analysing {cfg.label} review data...</span>
                  </div>
                </div>
              )}
              {chatError && <div className="chat-error-card"><p>{chatError}</p></div>}
              <div ref={chatEndRef} />
            </div>

            <div className="quick-suggestions-section">
              <span className="suggestions-title">
                {activeFollowUps.length > 0 ? "💬 SUGGESTED FOLLOW-UPS" : "⚡ QUICK ANALYTICS"}
              </span>
              <div className="suggestions-chips-container">
                {activeFollowUps.length > 0 ? (
                  activeFollowUps.map((q, idx) => (
                    <button key={idx} className="suggestion-chip follow-up-chip" onClick={() => handleSendChat(q)}>{q}</button>
                  ))
                ) : (
                  cfg.suggestedQuestions.map((q, idx) => (
                    <button key={idx} className="suggestion-chip" onClick={() => handleSendChat(q)}>{q}</button>
                  ))
                )}
              </div>
            </div>

            <div className="chat-input-bar">
              <input type="text" placeholder={`Ask about ${cfg.label} reviews...`}
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSendChat(chatInput)}
              />
              <button className="chat-send-btn" onClick={() => handleSendChat(chatInput)} disabled={!chatInput.trim() || isChatLoading}>
                <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>
                </svg>
              </button>
            </div>
          </div>
        )}

        {/* ── FEED EXPLORER TAB ── */}
        {activeTab === "explorer" && (
          <div className="tab-content explorer-tab fade-in">
            <div className="explorer-search-bar">
              <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="search-icon">
                <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
              </svg>
              <input type="text" placeholder={`Search ${cfg.label} reviews by model, keyword, author...`}
                value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} />
              {searchQuery && <button className="clear-search-btn" onClick={() => setSearchQuery("")}>✕</button>}
            </div>

            <section className="explorer-filters-panel">
              <div className="filter-group">
                <span className="filter-label">Platform:</span>
                <div className="filter-options">
                  <button className={`filter-btn ${selectedPlatform === null ? "active" : ""}`} onClick={() => setSelectedPlatform(null)}>All</button>
                  {cfg.platforms.map(p => (
                    <button key={p} className={`filter-btn ${selectedPlatform === p ? "active" : ""}`} onClick={() => setSelectedPlatform(p)}>{p}</button>
                  ))}
                </div>
              </div>

              <div className="filter-group">
                <span className="filter-label">Sentiment:</span>
                <div className="filter-options">
                  {[null, "Positive", "Neutral", "Negative"].map((s, i) => (
                    <button key={i} className={`filter-btn ${["", "pos", "neu", "neg"][i]} ${selectedSentiment === s ? "active" : ""}`} onClick={() => setSelectedSentiment(s)}>{s || "All"}</button>
                  ))}
                </div>
              </div>

              <div className="filter-group">
                <span className="filter-label">{cfg.groupLabel}:</span>
                <div className="filter-options flex-wrap">
                  <button className={`filter-btn sec ${selectedBrandGroup === null ? "active" : ""}`} onClick={() => setSelectedBrandGroup(null)}>All</button>
                  {cfg.groups.map(g => (
                    <button key={g} className={`filter-btn sec ${selectedBrandGroup === g ? "active" : ""}`} onClick={() => setSelectedBrandGroup(g)}>{g}</button>
                  ))}
                </div>
              </div>

              <div className="filter-group">
                <span className="filter-label">Review Theme:</span>
                <div className="filter-options flex-wrap">
                  <button className={`filter-btn sec ${selectedCategory === null ? "active" : ""}`} onClick={() => setSelectedCategory(null)}>All</button>
                  {["Performance", "EV Range", "Comfort", "Infotainment", "Build Quality", "After-Sales", "Pricing", "Safety", "Off-road", "Design", "General"].map(cat => (
                    <button key={cat} className={`filter-btn sec ${selectedCategory === cat ? "active" : ""}`} onClick={() => setSelectedCategory(cat)}>{cat}</button>
                  ))}
                </div>
              </div>
            </section>

            <div className="explorer-results-header">
              <span className="results-count">{feedItems.length} reviews matched · {cfg.label}</span>
              {(selectedPlatform || selectedSentiment || selectedBrandGroup || selectedCategory || searchQuery) && (
                <button className="clear-filters-link" onClick={handleClearFilters}>Clear filters</button>
              )}
            </div>

            <div className="explorer-cards-list">
              {feedItems.length === 0 ? (
                <div className="no-results-state">
                  <svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" style={{ color: "var(--color-primary)", opacity: 0.5 }}>
                    <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
                  </svg>
                  <h4>No {cfg.label} reviews match your criteria.</h4>
                  <p>Try clearing filters or adjusting your search.</p>
                  <button className="btn-primary" onClick={handleClearFilters}>Reset Search</button>
                </div>
              ) : (
                feedItems.map((item) => (
                  <div key={item.id} className="feedback-feed-card">
                    <div className="card-top-row">
                      <div className="card-author-info">
                        <div className={`platform-badge ${item.platform.toLowerCase().replace(/\s/g, "")}`}>
                          {item.platform.charAt(0)}
                        </div>
                        <span className="author-name">{item.author}</span>
                        <span style={{ marginLeft: "8px", padding: "2px 8px", fontSize: "0.7rem", fontWeight: "700", borderRadius: "4px",
                          backgroundColor: isJLR ? "rgba(74,124,89,0.15)" : "rgba(0,97,213,0.15)",
                          color: isJLR ? "#4a7c59" : "#0061d5",
                          border: `1px solid ${isJLR ? "rgba(74,124,89,0.3)" : "rgba(0,97,213,0.3)"}` }}>
                          {item.city}
                        </span>
                      </div>
                      <span className="card-date">{item.date}</span>
                    </div>

                    <div className="card-event-row">
                      <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="event-icon">
                        <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>
                      </svg>
                      <span className="event-name">{item.event}</span>
                      {item.isUpcoming && <span className="planned-badge">UPCOMING</span>}
                    </div>

                    <p className="card-text">{item.text}</p>

                    {item.action_insight && item.action_insight !== "No recommendation." && (
                      <div style={{ marginTop: "10px", marginBottom: "10px", padding: "8px 12px", fontSize: "0.8rem", borderRadius: "6px", backgroundColor: "rgba(16,185,129,0.08)", borderLeft: "3px solid #10b981", color: "var(--text-secondary)", fontStyle: "italic" }}>
                        💡 {item.action_insight}
                      </div>
                    )}

                    <div className="card-bottom-row" style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                      <div className="city-tag" style={{ display: "flex", alignItems: "center" }}>
                        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="location-icon">
                          <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/>
                        </svg>
                        {item.platform}
                      </div>

                      {item.category_tag && item.category_tag !== "General" && (
                        <span style={{ padding: "2px 8px", fontSize: "0.7rem", fontWeight: "600", borderRadius: "12px",
                          backgroundColor: isJLR ? "rgba(74,124,89,0.12)" : "rgba(0,97,213,0.12)",
                          color: isJLR ? "#4a7c59" : "#0061d5" }}>
                          #{item.category_tag}
                        </span>
                      )}

                      {item.priority_score > 1 && (
                        <span title="AI-Generated Priority" style={{ padding: "2px 8px", fontSize: "0.7rem", fontWeight: "bold", borderRadius: "12px",
                          backgroundColor: item.priority_score >= 4 ? "rgba(239,68,68,0.12)" : "rgba(245,158,11,0.12)",
                          color: item.priority_score >= 4 ? "#dc2626" : "#d97706", cursor: "help" }}>
                          {"★".repeat(item.priority_score)}
                        </span>
                      )}

                      <span className={`sentiment-badge ${item.sentiment.toLowerCase()}`} style={{ marginLeft: "auto" }}>
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
}

// ─── Sub-components ───────────────────────────────────────────────────────────
function PlatformBar({ label, count, total, color }) {
  const percentage = total > 0 ? (count / total) * 100 : 0;
  return (
    <div className="platform-bar-row">
      <div className="bar-labels">
        <span className="bar-title">{label}</span>
        <span className="bar-count">{count} reviews</span>
      </div>
      <div className="bar-track" style={{ backgroundColor: `${color}26` }}>
        <div className="bar-fill" style={{ width: `${percentage}%`, backgroundColor: color }} />
      </div>
    </div>
  );
}

function InsightsTab({ analytics, stats, brand, brandLabel, onTrendClick }) {
  if (!analytics) {
    return (
      <div className="insights-loading">
        <svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" style={{ color: "var(--color-primary)", opacity: 0.5 }}>
          <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
        <p>Analytics available after first scraper run. Run <code>python backend/scraper.py</code> to populate data.</p>
      </div>
    );
  }

  const issues = analytics.keyIssues || [];
  const praises = analytics.topPraises || [];
  const trending = analytics.trendingTerms || [];
  const topEvents = analytics.topEvents || [];
  const citySentiment = analytics.citySentiment || {};
  const positivePosts = analytics.topPositivePosts || [];
  const negativePosts = analytics.topNegativePosts || [];
  const maxTrend = Math.max(...trending.map(t => t.count), 1);
  const isJLR = brand === "jlr";

  return (
    <div className="insights-content">
      <section className="dashboard-banner">
        <div className="banner-top">
          <span className="banner-badge">{brandLabel.toUpperCase()} ANALYTICS</span>
          <span className="banner-emoji">📊</span>
          <button className="print-report-btn" onClick={() => window.print()} title="Print report">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="6 9 6 2 18 2 18 9"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="8"/>
            </svg>
            Print Report
          </button>
        </div>
        <h2>What {brandLabel} customers are saying</h2>
        <p>{analytics.executiveSummary}</p>
      </section>

      <section className="metrics-card consolidated-sentiment-card">
        <div className="consolidated-header">
          <div>
            <h3>Consolidated Sentiment Analysis</h3>
            <p className="consolidated-subtitle">Across all {stats?.totalFeedbackCount || 0} {brandLabel} reviews</p>
          </div>
          <div className="health-index-badge">
            <span className="health-lbl">Sentiment Health</span>
            <span className="health-val">{Math.round((stats?.sentimentPercentages?.Positive || 0) + 0.5 * (stats?.sentimentPercentages?.Neutral || 0))}/100</span>
          </div>
        </div>
        <div className="sentiment-stacked-bar">
          {(stats?.sentimentPercentages?.Positive || 0) > 0 && <div className="stacked-bar-segment positive-segment" style={{ width: `${stats.sentimentPercentages.Positive}%` }} title={`Positive: ${stats.sentimentPercentages.Positive}%`}><span>{Math.round(stats.sentimentPercentages.Positive)}%</span></div>}
          {(stats?.sentimentPercentages?.Neutral || 0) > 0 && <div className="stacked-bar-segment neutral-segment" style={{ width: `${stats.sentimentPercentages.Neutral}%` }} title={`Neutral: ${stats.sentimentPercentages.Neutral}%`}><span>{Math.round(stats.sentimentPercentages.Neutral)}%</span></div>}
          {(stats?.sentimentPercentages?.Negative || 0) > 0 && <div className="stacked-bar-segment negative-segment" style={{ width: `${stats.sentimentPercentages.Negative}%` }} title={`Negative: ${stats.sentimentPercentages.Negative}%`}><span>{Math.round(stats.sentimentPercentages.Negative)}%</span></div>}
        </div>
        <div className="sentiment-stat-cards-grid">
          {[
            { cls: "pos-card", dot: "pos-dot", label: "Positive", pct: stats?.sentimentPercentages?.Positive || 0, desc: "Owners praising performance, design, comfort, and EV experience." },
            { cls: "neu-card", dot: "neu-dot", label: "Neutral", pct: stats?.sentimentPercentages?.Neutral || 0, desc: "Balanced observations, comparisons, feature queries, and test drives." },
            { cls: "neg-card", dot: "neg-dot", label: "Negative", pct: stats?.sentimentPercentages?.Negative || 0, desc: "Complaints about reliability, after-sales, pricing, or EV range shortfalls." },
          ].map(({ cls, dot, label, pct, desc }) => (
            <div key={label} className={`sentiment-stat-card ${cls}`}>
              <div className="stat-card-header"><span className={`dot ${dot}`} /><span className="stat-card-title">{label}</span></div>
              <div className="stat-card-value">{Math.round((pct / 100) * (stats?.totalFeedbackCount || 0))} <span className="stat-card-pct">({Math.round(pct)}%)</span></div>
              <p className="stat-card-desc">{desc}</p>
            </div>
          ))}
        </div>
      </section>

      <div className="insights-grid-2">
        <section className="metrics-card">
          <h3 className="secondary-text">Key Issues</h3>
          <div className="insights-list">
            {issues.length === 0 && <p className="empty-insight">No major issues detected.</p>}
            {issues.map((issue, idx) => (
              <div key={idx} className="insight-row-item compact">
                <div className="insight-emoji-box" style={{ backgroundColor: "var(--color-negative-container)", color: "var(--color-negative)" }}>⚠</div>
                <div className="insight-content"><h4>{issue.theme}</h4><p>{issue.example || `${issue.count} mentions`}</p></div>
                <span className="insight-count">{issue.count}</span>
              </div>
            ))}
          </div>
        </section>
        <section className="metrics-card">
          <h3 className="primary-text">Top Praises</h3>
          <div className="insights-list">
            {praises.length === 0 && <p className="empty-insight">No major praise themes detected.</p>}
            {praises.map((praise, idx) => (
              <div key={idx} className="insight-row-item compact">
                <div className="insight-emoji-box" style={{ backgroundColor: "var(--color-positive-container)", color: "var(--color-positive)" }}>✨</div>
                <div className="insight-content"><h4>{praise.theme}</h4><p>{praise.example || `${praise.count} mentions`}</p></div>
                <span className="insight-count">{praise.count}</span>
              </div>
            ))}
          </div>
        </section>
      </div>

      <section className="metrics-card trending-card">
        <h3>Trending Terms</h3>
        <div className="trending-cloud">
          {trending.map((t, idx) => (
            <div key={idx} className="trend-pill clickable" onClick={() => onTrendClick?.(t.term)}
              style={{ fontSize: `${0.85 + (t.count / maxTrend) * 0.7}rem`, opacity: 0.7 + (t.count / maxTrend) * 0.3 }}
              title={`+${t.positive} Positive  ~${t.neutral} Neutral  -${t.negative} Negative`}>
              <span className="trend-term">{t.term}</span>
              <span className="trend-count">{t.count}</span>
            </div>
          ))}
        </div>
      </section>

      <div className="insights-grid-2">
        <section className="metrics-card">
          <h3>Most Reviewed Models</h3>
          <div className="event-rank-list">
            {topEvents.map((evt, idx) => {
              const total = evt.count || 1;
              return (
                <div key={idx} className="event-rank-row">
                  <div className="event-rank-header">
                    <span className="event-rank-name">{evt.event}</span>
                    <span className="event-rank-count">{evt.count} reviews</span>
                  </div>
                  <div className="event-rank-bar">
                    <div className="rank-bar-segment" style={{ width: `${(evt.positive / total) * 100}%`, backgroundColor: "var(--color-positive)" }} />
                    <div className="rank-bar-segment" style={{ width: `${(evt.neutral / total) * 100}%`, backgroundColor: "var(--color-neutral)" }} />
                    <div className="rank-bar-segment" style={{ width: `${(evt.negative / total) * 100}%`, backgroundColor: "var(--color-negative)" }} />
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        <section className="metrics-card">
          <h3>{isJLR ? "Brand Family Sentiment" : "Segment Sentiment"}</h3>
          <div className="city-sentiment-list">
            {Object.entries(citySentiment).sort((a, b) => b[1].total - a[1].total).map(([group, data]) => {
              const total = data.total || 1;
              return (
                <div key={group} className="city-sentiment-row">
                  <div className="city-sentiment-header">
                    <span className="city-sentiment-name">{group}</span>
                    <span className="city-sentiment-total">{data.total}</span>
                  </div>
                  <div className="city-sentiment-bar">
                    <div className="rank-bar-segment" style={{ width: `${(data.Positive / total) * 100}%`, backgroundColor: "var(--color-positive)" }} />
                    <div className="rank-bar-segment" style={{ width: `${(data.Neutral / total) * 100}%`, backgroundColor: "var(--color-neutral)" }} />
                    <div className="rank-bar-segment" style={{ width: `${(data.Negative / total) * 100}%`, backgroundColor: "var(--color-negative)" }} />
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      </div>

      <div className="insights-grid-2">
        <section className="metrics-card quote-card">
          <h3 className="positive-text">Top Positive Reviews</h3>
          {positivePosts.map((post, idx) => (
            <blockquote key={idx} className="quote-item">
              <p>"{post.text}"</p>
              <footer><span className="quote-author">{post.author}</span><span className="quote-meta">{post.event} · {post.city}</span></footer>
            </blockquote>
          ))}
        </section>
        <section className="metrics-card quote-card">
          <h3 className="negative-text">Top Negative Reviews</h3>
          {negativePosts.map((post, idx) => (
            <blockquote key={idx} className="quote-item">
              <p>"{post.text}"</p>
              <footer><span className="quote-author">{post.author}</span><span className="quote-meta">{post.event} · {post.city}</span></footer>
            </blockquote>
          ))}
        </section>
      </div>
    </div>
  );
}

function CityItem({ label, count }) {
  return (
    <div className="city-list-row">
      <div className="city-label-group">
        <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="city-loc-icon">
          <circle cx="12" cy="5" r="3"/><path d="M12 8v8M9 12h6"/>
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
      <div className="insight-emoji-box" style={{ backgroundColor: bgColor }}>{emoji}</div>
      <div className="insight-content"><h4>{title}</h4><p>{description}</p></div>
    </div>
  );
}

export default App;
