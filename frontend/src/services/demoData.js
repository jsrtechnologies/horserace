/**
 * Demo Data Generator
 * Generates deterministic Australian horse racing data for demonstration
 * Uses seeded random for consistent predictions across refreshes
 */

// Seeded random number generator for deterministic results
// Using mulberry32 algorithm with race_id as seed
const createSeededRandom = (seed) => {
  return () => {
    let t = seed += 0x6D2B79F5;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
};

// Create global seeded random with a fixed seed for consistency
// This ensures same predictions across all pages and refreshes
const globalSeed = 12345;
let seededRandom = createSeededRandom(globalSeed);

// Helper functions using seeded random
const randomInt = (min, max) => Math.floor(seededRandom() * (max - min + 1)) + min;
const randomFloat = (min, max) => seededRandom() * (max - min) + min;
const randomChoice = (arr) => arr[Math.floor(seededRandom() * arr.length)];
const randomChoices = (arr, count) => {
  const shuffled = [...arr].sort(() => seededRandom() - 0.5);
  return shuffled.slice(0, count);
};

const VENUES = [
  { name: "Flemington", state: "VIC" },
  { name: "Caulfield", state: "VIC" },
  { name: "Moonee Valley", state: "VIC" },
  { name: "Randwick", state: "NSW" },
  { name: "Rosehill", state: "NSW" },
  { name: "Warwick Farm", state: "NSW" },
  { name: "Doomben", state: "QLD" },
  { name: "Eagle Farm", state: "QLD" },
  { name: "Gold Coast", state: "QLD" },
  { name: "Morphettville", state: "SA" },
  { name: "Ascot", state: "WA" },
  { name: "Hobart", state: "TAS" },
];

const HORSES = [
  { name: "Winx", age: 7, sire: "Street Cry", dam: "Vegas Showgirl" },
  { name: "Anamoe", age: 4, sire: "Street Boss", dam: "Anatola" },
  { name: "Profiteer", age: 4, sire: "Capitalist", dam: "Misfit" },
  { name: "Artorius", age: 4, sire: "Flying Artie", dam: "Marmelo" },
  { name: "Zaaki", age: 6, sire: "Leroidesanimaux", dam: "Kazda" },
  { name: "Mr Brightside", age: 5, sire: "Bullbars", dam: "Luna" },
  { name: "Cascadian", age: 6, sire: "Famous Again", dam: "Cascadia" },
  { name: "Mo'unga", age: 5, sire: "Savabeel", dam: "Kalash" },
  { name: "Denormal", age: 4, sire: "More Than Ready", dam: "Denouncement" },
  { name: "Pericles", age: 4, sire: "Capitalist", dam: "Kalter" },
  { name: "Kovalica", age: 4, sire: "Ocean Park", dam: "Acacius" },
  { name: "Mighty Ulysses", age: 5, sire: "Ulysses", dam: "Mighty High" },
  { name: "Pinfluence", age: 5, sire: "Toronado", dam: "Influence" },
  { name: "Lunick", age: 4, sire: "Lunar Rise", dam: "Nickel" },
  { name: "Lightsaber", age: 6, sire: "Highlighter", dam: "Blade of Light" },
  { name: "Vince", age: 5, sire: "Unencumbered", dam: "Vinci" },
  { name: "Grail", age: 4, sire: "Pierro", dam: "Grail Maiden" },
  { name: "Trickstar", age: 5, sire: "Not a Single Doubt", dam: "Trick of Light" },
  { name: "Maltitude", age: 5, sire: "Mongolian Khan", dam: "Mull Over" },
  { name: "Royal Halberd", age: 4, sire: "Pride of Dubai", dam: "Royal Asset" },
];

const JOCKEYS = [
  "James McDonald", "Mark Zahra", "Blake Shinn", "Tommy Berry", "Ben Melham",
  "Craig Williams", "Damien Oliver", "John Allen", "Koby Jennings", "Michael Dee",
  "William Pike", "Nash Rawiller", "Levi Kamei", "Jamie Kah", "Daniel Stackhouse"
];

const TRAINERS = [
  "Chris Waller", "James Cummings", "Peter & Paul Snowden", "Gai Waterhouse",
  "Mick Price", "Grahame Begg", "Peter Moody", "Leon & Troy Corstens",
  "Kelly Schweida", "Matt Laurie", "Annabel Neasham", "John O'Shea",
  "Tony & Calvin McEvoy", "Symon Wilde", "Robert Smerdon"
];

const WEATHER = ["Fine", "Cloudy", "Overcast", "Light Rain", "Heavy Rain", "Windy"];
const TRACK_RATINGS = ["Good 3", "Good 4", "Soft 5", "Soft 6", "Heavy 8", "Heavy 9"];
const RACE_CLASSES = ["BM72", "BM78", "Class 1", "Class 2", "Class 3", "Maiden", "Open", "Group 3"];
const DISTANCES = [1000, 1100, 1200, 1300, 1400, 1500, 1600, 1800, 2000, 2200];

// Generate random form string
const generateFormString = () => {
  const positions = [];
  for (let i = 0; i < 5; i++) {
    positions.push(randomInt(1, 15));
  }
  return positions.join("-");
};

// Generate odds with realistic distribution
const generateOdds = () => {
  const rand = seededRandom();
  if (rand < 0.1) return randomFloat(2, 4);
  if (rand < 0.25) return randomFloat(4, 8);
  if (rand < 0.5) return randomFloat(8, 15);
  if (rand < 0.75) return randomFloat(15, 30);
  return randomFloat(30, 60);
};

export const generateVenues = () => {
  return VENUES.map((v, i) => ({
    id: i + 1,
    ...v,
    track_type: "Turf"
  }));
};

export const generateHorses = () => {
  return HORSES.map((h, i) => ({
    id: i + 1,
    ...h,
    gender: i < 5 ? "Colt" : i < 10 ? "Mare" : "Gelding"
  }));
};

export const generateJockeys = () => {
  return JOCKEYS.map((j, i) => ({
    id: i + 1,
    name: j
  }));
};

export const generateTrainers = () => {
  return TRAINERS.map((t, i) => ({
    id: i + 1,
    name: t
  }));
};

export const generateMeetings = (daysBack = 0) => {
  const meetings = [];
  const today = new Date();
  
  const daysToGenerate = daysBack === 0 ? 1 : Math.min(daysBack, 30);
  
  for (let d = 0; d < daysToGenerate; d++) {
    const date = new Date(today);
    date.setDate(date.getDate() - d);
    
    const numMeetings = randomInt(1,4);
    const selectedVenues = randomChoices(VENUES, numMeetings);
    
    selectedVenues.forEach((venue, idx) => {
      meetings.push({
        id: meetings.length + 1,
        date: date.toISOString(),
        venue_id: VENUES.indexOf(venue) + 1,
        venue: venue,
        weather: randomChoice(WEATHER),
        track_rating: randomChoice(TRACK_RATINGS)
      });
    });
  }
  
  return meetings;
};

export const generateRaces = (meetings) => {
  const races = [];
  
  meetings.forEach((meeting) => {
    const numRaces = randomInt(6, 10);
    
    for (let i = 1; i <= numRaces; i++) {
      const raceDate = new Date(meeting.date);
      raceDate.setHours(12 + i, 30, 0, 0);
      
      const isPast = raceDate < new Date();
      
      races.push({
        id: races.length + 1,
        meeting_id: meeting.id,
        race_number: i,
        race_name: `Race ${i}`,
        distance: randomChoice(DISTANCES),
        race_class: randomChoice(RACE_CLASSES),
        prize_money: randomChoice([20000, 30000, 50000, 75000, 100000, 150000]),
        race_time: raceDate.toISOString(),
        race_type: "Gallops",
        status: isPast ? "completed" : "scheduled",
        meeting: meeting
      });
    }
  });
  
  return races;
};

export const generateParticipants = (races, horses, jockeys, trainers) => {
  const participants = [];
  
  races.forEach((race) => {
    const numRunners = randomInt(8, 15);
    const selectedHorses = randomChoices(horses, numRunners);
    
    selectedHorses.forEach((horse, idx) => {
      const odds = generateOdds();
      
      participants.push({
        id: participants.length + 1,
        race_id: race.id,
        horse_id: horse.id,
        horse: horse,
        jockey: randomChoice(jockeys),
        trainer: randomChoice(trainers),
        barrier: idx + 1,
        carried_weight: randomFloat(50, 62).toFixed(1),
        rating: randomInt(60, 120),
        form_string: generateFormString(),
        days_since_last_run: randomInt(7, 60),
        weight_change: randomFloat(-1.5, 1.5).toFixed(1),
        is_scratched: seededRandom() < 0.03,
        win_probability: 0,
        fixed_win: odds.toFixed(2),
        fixed_place: (odds / 3).toFixed(2)
      });
    });
    
    const totalInverse = participants
      .filter(p => p.race_id === race.id && !p.is_scratched)
      .reduce((sum, p) => sum + (1 / parseFloat(p.fixed_win)), 0);
    
    participants
      .filter(p => p.race_id === race.id && !p.is_scratched)
      .forEach(p => {
        p.win_probability = ((1 / parseFloat(p.fixed_win)) / totalInverse * 100).toFixed(1);
      });
  });
  
  return participants;
};

export const generateRaceResults = (participants, races) => {
  const results = [];
  
  races.filter(r => r.status === "completed").forEach((race) => {
    const raceParticipants = participants
      .filter(p => p.race_id === race.id && !p.is_scratched)
      .sort(() => seededRandom() - 0.5);
    
    raceParticipants.forEach((p, idx) => {
      const position = idx + 1;
      const dividend = position === 1 ? randomFloat(2, 15) : position <= 3 ? randomFloat(1.5, 8) : randomFloat(1.1, 4);
      
      results.push({
        id: results.length + 1,
        race_id: race.id,
        participant_id: p.id,
        finishing_position: position,
        dividend: dividend.toFixed(2),
        place_dividend: position <= 3 ? (dividend / 3).toFixed(2) : null,
        margin: position === 1 ? "0L" : `${randomFloat(0.5, 5).toFixed(1)}L`
      });
    });
  });
  
  return results;
};

// Main function to generate all demo data
export const generateDemoData = (daysBack = 0) => {
  const venues = generateVenues();
  const horses = generateHorses();
  const jockeys = generateJockeys();
  const trainers = generateTrainers();
  const meetings = generateMeetings(daysBack);
  const races = generateRaces(meetings);
  const participants = generateParticipants(races, horses, jockeys, trainers);
  const results = generateRaceResults(participants, races);
  
  return {
    venues,
    horses,
    jockeys,
    trainers,
    meetings,
    races,
    participants,
    results,
    stats: {
      venues: venues.length,
      horses: horses.length,
      jockeys: jockeys.length,
      trainers: trainers.length,
      meetings: meetings.length,
      races: races.length,
      participants: participants.length,
      results: results.length
    }
  };
};

// Cache key for predictions
const PREDICTIONS_CACHE_KEY = 'ausrace_predictions_cache';
const PREDICTIONS_TIMESTAMP_KEY = 'ausrace_predictions_timestamp';

// Get cached predictions or generate new ones
const getCachedPredictions = () => {
  try {
    const cached = localStorage.getItem(PREDICTIONS_CACHE_KEY);
    if (cached) {
      return JSON.parse(cached);
    }
  } catch (e) {
    console.log("No cached predictions found");
  }
  return null;
};

// Save predictions to cache
const savePredictionsToCache = (predictions) => {
  try {
    localStorage.setItem(PREDICTIONS_CACHE_KEY, JSON.stringify(predictions));
    localStorage.setItem(PREDICTIONS_TIMESTAMP_KEY, Date.now().toString());
  } catch (e) {
    console.error("Error saving predictions to cache:", e);
  }
};

// Generate upcoming races with predictions
export const generateUpcomingRaces = () => {
  // Check cache first
  const cached = getCachedPredictions();
  if (cached && cached.races) {
    return cached.races;
  }
  
  const data = generateDemoData(0);
  
  const upcomingRaces = data.races
    .filter(r => r.status === "scheduled")
    .sort((a, b) => new Date(a.race_time) - new Date(b.race_time))
    .slice(0, 10);
  
  const result = upcomingRaces.map(race => {
    const raceParticipants = data.participants.filter(p => p.race_id === race.id);
    
    return {
      ...race,
      participants: raceParticipants.sort((a, b) => parseFloat(b.win_probability) - parseFloat(a.win_probability)),
      venue_name: race.meeting?.venue?.name || "Unknown",
      track_rating: race.meeting?.track_rating || "Good 4",
      weather: race.meeting?.weather || "Fine"
    };
  });
  
  // Cache the result
  savePredictionsToCache({ races: result, timestamp: Date.now() });
  
  return result;
};

// Generate best bets - deterministic and cached
export const generateBestBets = () => {
  // Check cache first
  const cached = getCachedPredictions();
  if (cached && cached.bestBets) {
    return cached.bestBets;
  }
  
  const upcoming = generateUpcomingRaces();
  const bestBets = [];
  
  upcoming.forEach((race, raceIdx) => {
    const top3 = race.participants.slice(0, 3);
    
    top3.forEach((horse, horseIdx) => {
      if (parseFloat(horse.win_probability) > 10) {
        bestBets.push({
          race_id: race.id,
          race_number: race.race_number,
          race_name: race.race_name,
          distance: race.distance,
          race_time: race.race_time,
          venue: race.venue_name,
          horse_name: horse.horse.name,
          jockey_name: horse.jockey.name,
          win_probability: parseFloat(horse.win_probability),
          confidence_score: parseFloat(horse.win_probability),
          fixed_win: horse.fixed_win,
          factors: {
            positive: [
              parseFloat(horse.win_probability) > 25 ? "High win probability" : null,
              horse.form_string?.startsWith("1") ? "Won last start" : null,
              horse.barrier <= 4 ? "Good barrier draw" : null
            ].filter(Boolean),
            negative: [
              parseInt(horse.days_since_last_run) > 45 ? "Lacks recent runs" : null,
              horse.barrier > 10 ? "Wide barrier" : null
            ].filter(Boolean)
          }
        });
      }
    });
  });
  
  const result = bestBets
    .sort((a, b) => b.confidence_score - a.confidence_score)
    .slice(0, 10);
  
  // Cache the result
  const cache = getCachedPredictions() || {};
  cache.bestBets = result;
  savePredictionsToCache(cache);
  
  return result;
};

// Clear prediction cache (force regenerate)
export const clearPredictionCache = () => {
  try {
    localStorage.removeItem(PREDICTIONS_CACHE_KEY);
    localStorage.removeItem(PREDICTIONS_TIMESTAMP_KEY);
  } catch (e) {
    console.error("Error clearing prediction cache:", e);
  }
};

export default generateDemoData;
