const $ = (id) => document.getElementById(id);

const ui = {
  createForm: $("create-form"),
  createName: $("create-name"),
  createStake: $("create-stake"),
  joinForm: $("join-form"),
  joinName: $("join-name"),
  joinCode: $("join-code"),
  resumeForm: $("resume-form"),
  resumeCode: $("resume-code"),
  roomCode: $("room-code"),
  currentBalanceValue: $("current-balance-value"),
  saveCodeValue: $("save-code-value"),
  friendCodeValue: $("friend-code-value"),
  playerSummary: $("player-summary"),
  reels: $("reels"),
  cabinet: $("slot-cabinet"),
  leverButton: $("lever-button"),
  spinForm: $("spin-form"),
  spinButton: $("spin-button"),
  musicToggle: $("music-toggle"),
  soundToggle: $("sound-toggle"),
  dailyButton: $("daily-button"),
  pauseButton: $("pause-button"),
  leaveButton: $("leave-button"),
  finishButton: $("finish-button"),
  lines: $("lines"),
  bet: $("bet"),
  result: $("result-strip"),
  leaderboard: $("leaderboard"),
  rankGifts: $("rank-gifts"),
  stats: $("stats"),
  events: $("events"),
  friends: $("friends"),
  friendForm: $("friend-form"),
  friendCodeInput: $("friend-code-input"),
  chatLog: $("chat-log"),
  chatForm: $("chat-form"),
  chatInput: $("chat-input"),
  confettiLayer: $("confetti-layer"),
};

const session = {
  roomCode: localStorage.getItem("slotRoomCode"),
  playerId: localStorage.getItem("slotPlayerId"),
  saveCode: localStorage.getItem("slotSaveCode"),
  pollTimer: null,
};

const initialColumns = [
  [
    { symbol: "SEVEN", label: "7", color: "bright_red" },
    { symbol: "DIAMOND", label: "DMD", color: "bright_cyan" },
    { symbol: "CHERRY", label: "CHRY", color: "red" },
  ],
  [
    { symbol: "BELL", label: "BELL", color: "yellow" },
    { symbol: "WILD", label: "WILD", color: "magenta" },
    { symbol: "SCATTER", label: "SCAT", color: "bright_blue" },
  ],
  [
    { symbol: "BAR", label: "BAR", color: "white" },
    { symbol: "LEMON", label: "LEMN", color: "green" },
    { symbol: "SEVEN", label: "7", color: "bright_red" },
  ],
];

const symbolSamples = [
  { symbol: "SEVEN", label: "7", color: "bright_red" },
  { symbol: "DIAMOND", label: "DMD", color: "bright_cyan" },
  { symbol: "CHERRY", label: "CHRY", color: "red" },
  { symbol: "BELL", label: "BELL", color: "yellow" },
  { symbol: "BAR", label: "BAR", color: "white" },
  { symbol: "LEMON", label: "LEMN", color: "green" },
  { symbol: "WILD", label: "WILD", color: "magenta" },
  { symbol: "SCATTER", label: "SCAT", color: "bright_blue" },
];

let audioContext;
let musicTimer;
let musicEnabled = false;
let soundEnabled = true;
const coinFormat = new Intl.NumberFormat("en-US");

function formatCoins(value) {
  return `${coinFormat.format(Number(value) || 0)} coins`;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const contentType = response.headers.get("content-type") || "";
  const body = await response.text();
  let data = {};

  if (contentType.includes("application/json") && body) {
    data = JSON.parse(body);
  } else if (path.startsWith("/api/")) {
    throw new Error(apiServerMessage());
  }

  if (!response.ok) {
    throw new Error(data.error || "Request failed");
  }

  return data;
}

function apiServerMessage() {
  if (location.port === "5500") {
    return "Live Server cannot run the multiplayer API. Start Python with `python web_app.py`, then open http://127.0.0.1:8000.";
  }

  return "The multiplayer API did not return JSON. Make sure `python web_app.py` is running and open the page from that server.";
}

function symbolPaint(symbol) {
  const paints = {
    SEVEN: ["#731f35", "#f8dfe3"],
    DIAMOND: ["#227c7d", "#d8f1ee"],
    BELL: ["#d6a33d", "#fff1c6"],
    CHERRY: ["#c73550", "#f8dfe3"],
    BAR: ["#2a0610", "#f7f0e5"],
    LEMON: ["#6f8e76", "#edf6ec"],
    WILD: ["#581426", "#efd8e0"],
    SCATTER: ["#2f6f73", "#dcefed"],
  };
  return paints[symbol] || ["#5e554c", "#ffffff"];
}

function symbolSvg(cell) {
  const symbol = cell.symbol || "BAR";
  const label = escapeHtml(cell.label || symbol);
  const [main, soft] = symbolPaint(symbol);

  if (symbol === "DIAMOND") {
    return `<svg viewBox="0 0 100 100" role="img" aria-label="${label}">
      <rect width="100" height="100" rx="18" fill="${soft}"/>
      <polygon points="50,10 84,50 50,90 16,50" fill="${main}"/>
      <text x="50" y="57" text-anchor="middle" font-size="22" font-weight="800" fill="#fff">${label}</text>
    </svg>`;
  }

  if (symbol === "CHERRY") {
    return `<svg viewBox="0 0 100 100" role="img" aria-label="${label}">
      <rect width="100" height="100" rx="18" fill="${soft}"/>
      <path d="M48 36 C50 24 60 18 72 18" stroke="#386b35" stroke-width="7" fill="none"/>
      <circle cx="38" cy="60" r="22" fill="${main}"/>
      <circle cx="62" cy="66" r="20" fill="#9f2536"/>
      <text x="50" y="91" text-anchor="middle" font-size="16" font-weight="800" fill="#2f2925">${label}</text>
    </svg>`;
  }

  if (symbol === "BELL") {
    return `<svg viewBox="0 0 100 100" role="img" aria-label="${label}">
      <rect width="100" height="100" rx="18" fill="${soft}"/>
      <path d="M28 68 H72 L66 38 C63 25 37 25 34 38 Z" fill="${main}"/>
      <circle cx="50" cy="75" r="8" fill="#9c711d"/>
      <text x="50" y="92" text-anchor="middle" font-size="16" font-weight="800" fill="#2f2925">${label}</text>
    </svg>`;
  }

  if (symbol === "SCATTER") {
    return `<svg viewBox="0 0 100 100" role="img" aria-label="${label}">
      <rect width="100" height="100" rx="18" fill="${soft}"/>
      <polygon points="50,9 61,38 92,38 67,57 76,88 50,70 24,88 33,57 8,38 39,38" fill="${main}"/>
      <text x="50" y="57" text-anchor="middle" font-size="17" font-weight="900" fill="#fff">${label}</text>
    </svg>`;
  }

  if (symbol === "WILD") {
    return `<svg viewBox="0 0 100 100" role="img" aria-label="${label}">
      <rect width="100" height="100" rx="18" fill="${soft}"/>
      <path d="M58 8 L24 55 H48 L40 92 L76 44 H52 Z" fill="${main}"/>
      <text x="50" y="58" text-anchor="middle" font-size="17" font-weight="900" fill="#fff">${label}</text>
    </svg>`;
  }

  return `<svg viewBox="0 0 100 100" role="img" aria-label="${label}">
    <rect width="100" height="100" rx="18" fill="${soft}"/>
    <circle cx="50" cy="50" r="33" fill="${main}"/>
    <text x="50" y="58" text-anchor="middle" font-size="${label.length > 3 ? 20 : 34}" font-weight="900" fill="#fff">${label}</text>
  </svg>`;
}

function renderReels(columns, columnStates = []) {
  ui.reels.innerHTML = "";

  columns.forEach((column, columnIndex) => {
    const columnEl = document.createElement("div");
    columnEl.className = `reel-column ${columnStates[columnIndex] || ""}`.trim();

    column.forEach((cell, rowIndex) => {
      const cellEl = document.createElement("div");
      cellEl.className = "reel-cell";
      cellEl.style.setProperty("--cell-index", columnIndex * 3 + rowIndex);
      cellEl.innerHTML = symbolSvg(cell);
      columnEl.append(cellEl);
    });

    ui.reels.append(columnEl);
  });
}

function renderState(state) {
  const you = state.you;
  const room = state.room || {};
  ui.roomCode.textContent = state.roomCode || "------";
  ui.spinButton.disabled = !you || room.status === "completed" || you.forfeited;
  ui.leverButton.disabled = ui.spinButton.disabled;
  ui.dailyButton.disabled = !you || !you.dailyAvailable;
  ui.pauseButton.disabled = !you;
  ui.leaveButton.disabled = !you || room.status === "completed" || you.forfeited;
  ui.finishButton.disabled = !you || room.status === "completed" || !room.playerCount;

  if (state.config) {
    applyConfig(state.config);
  }

  if (you) {
    if (you.saveCode) {
      session.saveCode = you.saveCode;
      localStorage.setItem("slotSaveCode", you.saveCode);
      ui.saveCodeValue.textContent = you.saveCode;
    }
    if (you.friendCode) {
      ui.friendCodeValue.textContent = you.friendCode;
    }
    ui.currentBalanceValue.textContent = formatCoins(you.balance);
    ui.playerSummary.textContent = `${you.name} | ${formatCoins(you.balance)} | ${you.league.name} league | pot ${coinFormat.format(room.pot || 0)} | stake ${coinFormat.format(room.stake || 0)}`;
    renderStats(you);
    renderFriends(you.friends || []);
  }

  renderLeaderboard(state.players || []);
  renderRankGifts(state.rankGifts || []);
  renderEvents(state.events || []);
  renderChat(state.chat || []);
}

function applyConfig(config) {
  ui.lines.max = config.maxPaylines;
  ui.bet.min = config.minBet;
  ui.bet.max = config.maxBet;
  ui.createStake.min = config.minStake;
  ui.createStake.max = config.maxStake;

  const stake = Number(ui.createStake.value);
  if (!stake || stake < config.minStake || stake > config.maxStake) {
    ui.createStake.value = config.defaultStake;
  }
  if (Number(ui.lines.value) > config.maxPaylines) {
    ui.lines.value = config.maxPaylines;
  }
  if (Number(ui.bet.value) > config.maxBet) {
    ui.bet.value = config.maxBet;
  }
  if (!session.playerId) {
    ui.currentBalanceValue.textContent = `${coinFormat.format(config.startingCoins)} starting coins`;
    ui.playerSummary.textContent = `No active profile | ${formatCoins(config.startingCoins)} starting balance`;
  }
}

async function loadAppConfig() {
  try {
    const data = await api("/api/config");
    applyConfig(data.config);
  } catch (error) {
    if (!session.playerId) {
      ui.playerSummary.textContent = "No active profile | 50,000 starting balance";
    }
  }
}

function renderLeaderboard(players) {
  ui.leaderboard.innerHTML = "";

  players.forEach((player, index) => {
    const row = document.createElement("div");
    row.className = `leader-row rank-${player.rank || index + 1}`;

    const identity = document.createElement("div");
    identity.className = "leader-identity";

    const name = document.createElement("strong");
    name.textContent = `${player.rank || index + 1}. ${player.name}`;

    const gift = document.createElement("small");
    gift.className = "leader-gift";
    gift.textContent = player.gift ? player.gift.name : "No gift rank";

    identity.append(name, gift);

    const value = document.createElement("span");
    value.className = "leader-score";
    value.innerHTML = `${player.roomScore}<br><small>${player.balance} coins</small>`;

    row.append(identity, value);
    ui.leaderboard.append(row);
  });
}

function renderRankGifts(gifts) {
  ui.rankGifts.innerHTML = "";

  gifts.forEach((gift) => {
    const card = document.createElement("div");
    card.className = `gift-card gift-${gift.accent}`;

    const rank = document.createElement("strong");
    rank.textContent = `#${gift.rank}`;

    const copy = document.createElement("span");
    copy.textContent = gift.name;

    const description = document.createElement("small");
    description.textContent = gift.description;

    card.append(rank, copy, description);
    ui.rankGifts.append(card);
  });
}

function renderFriends(friends) {
  ui.friends.innerHTML = "";

  if (!friends.length) {
    const empty = document.createElement("div");
    empty.className = "empty-state";
    empty.textContent = "No friends yet";
    ui.friends.append(empty);
    return;
  }

  friends.forEach((friend) => {
    const card = document.createElement("div");
    card.className = "friend-card";

    const identity = document.createElement("strong");
    identity.textContent = friend.name;

    const details = document.createElement("span");
    details.textContent = `${friend.league.name} league | ${friend.friendCode}`;

    card.append(identity, details);
    ui.friends.append(card);
  });
}

function renderStats(player) {
  const stats = [
    ["League", `${player.league.name} (${player.leaguePoints})`],
    ["Room score", player.roomScore],
    ["Coins", player.balance],
    ["Spins", player.stats.spins],
    ["Win rate", `${Math.round(player.stats.winRate * 100)}%`],
    ["Biggest win", `$${player.stats.biggest_win}`],
    ["Net", `$${player.stats.net}`],
    ["Jackpots", player.stats.jackpots],
    ["Free spins", player.freeSpins],
    ["Achievements", player.achievements.length],
    ["Room wins", player.wins],
    ["Forfeits", player.forfeits],
  ];

  ui.stats.innerHTML = "";
  stats.forEach(([label, value]) => {
    const dt = document.createElement("dt");
    const dd = document.createElement("dd");
    dt.textContent = label;
    dd.textContent = value;
    ui.stats.append(dt, dd);
  });
}

function renderEvents(events) {
  ui.events.innerHTML = "";
  events.forEach((event) => {
    const item = document.createElement("li");
    item.textContent = event;
    ui.events.append(item);
  });
}

function renderChat(messages) {
  ui.chatLog.innerHTML = "";
  messages.forEach((message) => {
    const item = document.createElement("div");
    item.className = `chat-message ${message.kind === "emoji" ? "is-emoji" : ""}`;

    if (message.kind !== "emoji") {
      const name = document.createElement("strong");
      name.textContent = message.playerName;
      item.append(name);
    }

    const body = document.createElement("span");
    body.textContent = message.message;
    item.append(body);
    ui.chatLog.append(item);
  });
  ui.chatLog.scrollTop = ui.chatLog.scrollHeight;
}

function renderSpin(spin) {
  renderReels(spin.columns);

  const lines = [];
  lines.push(spin.totalWinnings ? `Won $${spin.totalWinnings}` : "No win");

  if (spin.freeSpinUsed) {
    lines.push("Free spin used");
  }
  if (spin.freeSpinsAwarded) {
    lines.push(`Free spins +${spin.freeSpinsAwarded}`);
  }
  if (spin.bonusMultiplier > 1) {
    lines.push(`${spin.bonusMultiplier}x bonus`);
  }
  if (spin.jackpotHit) {
    lines.push("Jackpot");
  }
  if (spin.awards?.length) {
    spin.awards.forEach((award) => {
      lines.push(`${award.name}: +${award.coins} coins`);
    });
  }

  spin.lineWins.forEach((line) => {
    lines.push(`${line.name}: ${line.symbols.join(" ")} pays $${line.amount}`);
  });

  spin.messages.forEach((message) => lines.push(message));
  ui.result.innerHTML = lines.map(escapeHtml).join("<br>");
  ui.result.classList.remove("result-pop");
  void ui.result.offsetWidth;
  ui.result.classList.add("result-pop");
}

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function randomCell() {
  return symbolSamples[Math.floor(Math.random() * symbolSamples.length)];
}

function randomColumns() {
  return Array.from({ length: 3 }, () =>
    Array.from({ length: 3 }, () => randomCell())
  );
}

async function animateSpinToResult(finalColumns) {
  const displayed = randomColumns();
  const locked = [false, false, false];
  const states = ["is-spinning", "is-spinning", "is-spinning"];

  playSpinSound();
  ui.cabinet.classList.add("is-pulling");
  ui.reels.classList.add("is-spinning");

  const interval = setInterval(() => {
    for (let column = 0; column < displayed.length; column += 1) {
      if (!locked[column]) {
        displayed[column] = Array.from({ length: 3 }, () => randomCell());
      }
    }
    renderReels(displayed, states);
  }, 86);

  await delay(620);
  ui.cabinet.classList.remove("is-pulling");

  for (let column = 0; column < finalColumns.length; column += 1) {
    states[column] = "is-stopping";
    await delay(520 + column * 180);
    locked[column] = true;
    displayed[column] = finalColumns[column];
    states[column] = "";
    playReelStopSound(column);
    renderReels(displayed, states);
  }

  clearInterval(interval);
  ui.reels.classList.remove("is-spinning");
  renderReels(finalColumns);
}

function triggerConfetti() {
  const colors = ["#731f35", "#c73550", "#d6a33d", "#227c7d", "#fff1c6"];
  ui.confettiLayer.innerHTML = "";

  for (let index = 0; index < 90; index += 1) {
    const piece = document.createElement("span");
    piece.className = "confetti-piece";
    piece.style.left = `${Math.random() * 100}%`;
    piece.style.background = colors[index % colors.length];
    piece.style.setProperty("--drift", `${Math.random() * 220 - 110}px`);
    piece.style.setProperty("--fall-duration", `${1200 + Math.random() * 1200}ms`);
    piece.style.setProperty("--spin", `${Math.random() * 360}deg`);
    ui.confettiLayer.append(piece);
  }

  ui.cabinet.classList.remove("jackpot-flash");
  void ui.cabinet.offsetWidth;
  ui.cabinet.classList.add("jackpot-flash");
  setTimeout(() => {
    ui.confettiLayer.innerHTML = "";
    ui.cabinet.classList.remove("jackpot-flash");
  }, 2600);
}

function ensureAudio() {
  if (!audioContext) {
    const AudioEngine = window.AudioContext || window.webkitAudioContext;
    if (!AudioEngine) {
      return null;
    }
    audioContext = new AudioEngine();
  }
  if (audioContext.state === "suspended") {
    audioContext.resume();
  }
  return audioContext;
}

function playTone(
  frequency,
  duration = 0.12,
  type = "sine",
  gain = 0.05,
  startOffset = 0,
  allowMuted = false
) {
  if (!soundEnabled && !allowMuted) {
    return;
  }

  const context = ensureAudio();
  if (!context) {
    return;
  }
  const oscillator = context.createOscillator();
  const volume = context.createGain();
  const start = context.currentTime + startOffset;
  oscillator.type = type;
  oscillator.frequency.setValueAtTime(frequency, start);
  volume.gain.setValueAtTime(0.0001, start);
  volume.gain.exponentialRampToValueAtTime(gain, start + 0.02);
  volume.gain.exponentialRampToValueAtTime(0.0001, start + duration);
  oscillator.connect(volume).connect(context.destination);
  oscillator.start(start);
  oscillator.stop(start + duration + 0.02);
}

function playSpinSound() {
  if (!soundEnabled) {
    return;
  }
  for (let index = 0; index < 12; index += 1) {
    playTone(160 + index * 18, 0.07, "sawtooth", 0.028, index * 0.055);
  }
}

function playReelStopSound(column) {
  if (!soundEnabled) {
    return;
  }
  playTone(220 + column * 80, 0.1, "square", 0.045);
}

function playJackpotSound() {
  if (!soundEnabled) {
    return;
  }
  [523, 659, 784, 1046].forEach((note, index) => {
    playTone(note, 0.16, "triangle", 0.07, index * 0.12);
  });
}

function startMusic() {
  const context = ensureAudio();
  if (!context) {
    musicEnabled = false;
    ui.musicToggle.textContent = "Music Off";
    return;
  }
  stopMusic();
  const notes = [196, 247, 294, 247, 220, 262, 330, 262];
  let index = 0;
  musicTimer = setInterval(() => {
    if (!musicEnabled) {
      return;
    }
    playTone(notes[index % notes.length], 0.22, "triangle", 0.018, 0, true);
    index += 1;
  }, 520);
}

function stopMusic() {
  clearInterval(musicTimer);
}

function saveSession(roomCode, playerId) {
  session.roomCode = roomCode;
  session.playerId = playerId;
  localStorage.setItem("slotRoomCode", roomCode);
  localStorage.setItem("slotPlayerId", playerId);
}

function saveProfileSession(playerId, saveCode) {
  session.playerId = playerId;
  localStorage.setItem("slotPlayerId", playerId);
  if (saveCode) {
    session.saveCode = saveCode;
    localStorage.setItem("slotSaveCode", saveCode);
    ui.saveCodeValue.textContent = saveCode;
  }
}

function startPolling() {
  clearInterval(session.pollTimer);
  if (!session.roomCode || !session.playerId) {
    return;
  }

  refreshState();
  session.pollTimer = setInterval(refreshState, 1500);
}

async function refreshState() {
  if (!session.roomCode || !session.playerId) {
    return;
  }

  try {
    const data = await api(
      `/api/rooms/${session.roomCode}/state?playerId=${encodeURIComponent(session.playerId)}`
    );
    renderState(data.state);
  } catch (error) {
    ui.result.textContent = error.message;
    clearInterval(session.pollTimer);
  }
}

ui.createForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    const data = await api("/api/rooms", {
      method: "POST",
      body: JSON.stringify({
        name: ui.createName.value,
        playerId: session.playerId,
        stake: Number(ui.createStake.value),
      }),
    });
    saveSession(data.roomCode, data.playerId);
    renderState(data.state);
    startPolling();
    ui.result.textContent = "Room created";
  } catch (error) {
    ui.result.textContent = error.message;
  }
});

ui.joinForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    const code = ui.joinCode.value.trim().toUpperCase();
    const data = await api(`/api/rooms/${code}/join`, {
      method: "POST",
      body: JSON.stringify({
        name: ui.joinName.value,
        playerId: session.playerId,
      }),
    });
    saveSession(data.roomCode, data.playerId);
    renderState(data.state);
    startPolling();
    ui.result.textContent = "Joined room";
  } catch (error) {
    ui.result.textContent = error.message;
  }
});

ui.leverButton.addEventListener("click", () => {
  if (!ui.spinButton.disabled) {
    ui.spinForm.requestSubmit();
  }
});

ui.musicToggle.addEventListener("click", () => {
  musicEnabled = !musicEnabled;
  ui.musicToggle.textContent = musicEnabled ? "Music On" : "Music Off";
  if (musicEnabled) {
    startMusic();
  } else {
    stopMusic();
  }
});

ui.soundToggle.addEventListener("click", () => {
  soundEnabled = !soundEnabled;
  ui.soundToggle.textContent = soundEnabled ? "Sound On" : "Sound Off";
});

ui.resumeForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    const data = await api("/api/profile/resume", {
      method: "POST",
      body: JSON.stringify({
        saveCode: ui.resumeCode.value,
        name: ui.createName.value || ui.joinName.value,
      }),
    });
    saveProfileSession(data.playerId, data.profile.saveCode);
    if (data.roomCode) {
      session.roomCode = data.roomCode;
      localStorage.setItem("slotRoomCode", data.roomCode);
    }
    if (data.state) {
      renderState(data.state);
    } else {
      renderStats(data.profile);
      ui.currentBalanceValue.textContent = formatCoins(data.profile.balance);
      ui.friendCodeValue.textContent = data.profile.friendCode || "Add a profile first";
      renderFriends(data.profile.friends || []);
      ui.playerSummary.textContent = `${data.profile.name} | ${formatCoins(data.profile.balance)} | ${data.profile.league.name} league`;
    }
    startPolling();
    ui.result.textContent = data.reward
      ? `${data.reward.name}: +${data.reward.coins} coins and +${data.reward.freeSpins} free spins`
      : "Profile resumed.";
  } catch (error) {
    ui.result.textContent = error.message;
  }
});

ui.dailyButton.addEventListener("click", async () => {
  if (!session.playerId) {
    return;
  }

  try {
    const data = await api("/api/rewards/daily", {
      method: "POST",
      body: JSON.stringify({
        playerId: session.playerId,
        name: ui.createName.value || ui.joinName.value,
      }),
    });
    ui.result.textContent = `Daily reward claimed: +${data.reward.amount} coins`;
    refreshState();
  } catch (error) {
    ui.result.textContent = error.message;
  }
});

ui.pauseButton.addEventListener("click", async () => {
  if (!session.playerId) {
    return;
  }

  try {
    const data = await api("/api/profile/pause", {
      method: "POST",
      body: JSON.stringify({ playerId: session.playerId }),
    });
    saveProfileSession(data.profile.id, data.profile.saveCode);
    renderStats(data.profile);
    ui.currentBalanceValue.textContent = formatCoins(data.profile.balance);
    ui.friendCodeValue.textContent = data.profile.friendCode || "Add a profile first";
    renderFriends(data.profile.friends || []);
    ui.result.textContent = `Paused and saved. Resume with ${data.profile.saveCode}.`;
  } catch (error) {
    ui.result.textContent = error.message;
  }
});

ui.leaveButton.addEventListener("click", async () => {
  if (!session.roomCode || !session.playerId) {
    return;
  }

  try {
    const data = await api(`/api/rooms/${session.roomCode}/leave`, {
      method: "POST",
      body: JSON.stringify({ playerId: session.playerId }),
    });
    renderState(data.state);
    ui.result.textContent = "You left the room and forfeited your stake.";
  } catch (error) {
    ui.result.textContent = error.message;
  }
});

ui.finishButton.addEventListener("click", async () => {
  if (!session.roomCode || !session.playerId) {
    return;
  }

  try {
    const data = await api(`/api/rooms/${session.roomCode}/finish`, {
      method: "POST",
      body: JSON.stringify({ playerId: session.playerId }),
    });
    renderState(data.state);
    const winner = data.state.players.find((player) => player.isWinner);
    ui.result.textContent = winner
      ? `${winner.name} won the pot.`
      : "Room ended.";
  } catch (error) {
    ui.result.textContent = error.message;
  }
});

ui.friendForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!session.playerId) {
    ui.result.textContent = "Create or resume a profile before adding friends.";
    return;
  }

  try {
    const data = await api("/api/friends/add", {
      method: "POST",
      body: JSON.stringify({
        playerId: session.playerId,
        friendCode: ui.friendCodeInput.value,
      }),
    });
    ui.friendCodeInput.value = "";
    ui.friendCodeValue.textContent = data.profile.friendCode;
    renderStats(data.profile);
    renderFriends(data.profile.friends || []);
    ui.result.textContent = "Friend added.";
  } catch (error) {
    ui.result.textContent = error.message;
  }
});

async function sendChat(message, kind = "text") {
  if (!session.roomCode || !session.playerId) {
    ui.result.textContent = "Join a room before chatting.";
    return;
  }

  try {
    const data = await api(`/api/rooms/${session.roomCode}/chat`, {
      method: "POST",
      body: JSON.stringify({
        playerId: session.playerId,
        message,
        kind,
      }),
    });
    renderState(data.state);
  } catch (error) {
    ui.result.textContent = error.message;
  }
}

ui.chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = ui.chatInput.value.trim();
  if (!message) {
    return;
  }
  ui.chatInput.value = "";
  sendChat(message);
});

document.querySelectorAll("[data-emoji]").forEach((button) => {
  button.addEventListener("click", () => {
    sendChat(button.dataset.emoji, "emoji");
  });
});

ui.spinForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!session.roomCode || !session.playerId) {
    return;
  }

  ui.spinButton.disabled = true;
  ui.leverButton.disabled = true;
  ui.result.textContent = "Spinning";
  let stateRendered = false;

  try {
    const data = await api(`/api/rooms/${session.roomCode}/spin`, {
      method: "POST",
      body: JSON.stringify({
        playerId: session.playerId,
        lines: Number(ui.lines.value),
        bet: Number(ui.bet.value),
      }),
    });
    await animateSpinToResult(data.spin.columns);
    renderState(data.state);
    stateRendered = true;
    renderSpin(data.spin);
    if (data.spin.jackpotHit) {
      triggerConfetti();
      playJackpotSound();
    }
  } catch (error) {
    ui.result.textContent = error.message;
  } finally {
    ui.reels.classList.remove("is-spinning");
    ui.cabinet.classList.remove("is-pulling");
    if (!stateRendered) {
      ui.spinButton.disabled = !session.roomCode || !session.playerId;
    }
    ui.leverButton.disabled = ui.spinButton.disabled;
  }
});

renderReels(initialColumns);
renderFriends([]);
ui.leverButton.disabled = ui.spinButton.disabled;
if (session.saveCode) {
  ui.saveCodeValue.textContent = session.saveCode;
  ui.resumeCode.value = session.saveCode;
}
if (location.port === "5500") {
  ui.result.textContent = apiServerMessage();
}
loadAppConfig();
startPolling();
