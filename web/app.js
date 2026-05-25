const $ = (id) => document.getElementById(id);

const ui = {
  createForm: $("create-form"),
  createName: $("create-name"),
  createStake: $("create-stake"),
  joinForm: $("join-form"),
  joinName: $("join-name"),
  joinCode: $("join-code"),
  roomCode: $("room-code"),
  playerSummary: $("player-summary"),
  reels: $("reels"),
  spinForm: $("spin-form"),
  spinButton: $("spin-button"),
  dailyButton: $("daily-button"),
  leaveButton: $("leave-button"),
  finishButton: $("finish-button"),
  lines: $("lines"),
  bet: $("bet"),
  result: $("result-strip"),
  leaderboard: $("leaderboard"),
  rankGifts: $("rank-gifts"),
  stats: $("stats"),
  events: $("events"),
};

const session = {
  roomCode: localStorage.getItem("slotRoomCode"),
  playerId: localStorage.getItem("slotPlayerId"),
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

function renderReels(columns) {
  ui.reels.innerHTML = "";

  columns.forEach((column, columnIndex) => {
    const columnEl = document.createElement("div");
    columnEl.className = "reel-column";

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
  ui.dailyButton.disabled = !you || !you.dailyAvailable;
  ui.leaveButton.disabled = !you || room.status === "completed" || you.forfeited;
  ui.finishButton.disabled = !you || room.status === "completed" || !room.playerCount;

  if (state.config) {
    ui.lines.max = state.config.maxPaylines;
    ui.bet.min = state.config.minBet;
    ui.bet.max = state.config.maxBet;
    ui.createStake.min = state.config.minStake;
    ui.createStake.max = state.config.maxStake;
    if (Number(ui.lines.value) > state.config.maxPaylines) {
      ui.lines.value = state.config.maxPaylines;
    }
    if (Number(ui.bet.value) > state.config.maxBet) {
      ui.bet.value = state.config.maxBet;
    }
  }

  if (you) {
    ui.playerSummary.textContent = `${you.name} | ${you.balance} coins | ${you.league.name} league | pot ${room.pot || 0} | stake ${room.stake || 0}`;
    renderStats(you);
  }

  renderLeaderboard(state.players || []);
  renderRankGifts(state.rankGifts || []);
  renderEvents(state.events || []);
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

function saveSession(roomCode, playerId) {
  session.roomCode = roomCode;
  session.playerId = playerId;
  localStorage.setItem("slotRoomCode", roomCode);
  localStorage.setItem("slotPlayerId", playerId);
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
    const winner = data.state.players.find((player) => player.id === data.state.room.winnerId);
    ui.result.textContent = winner
      ? `${winner.name} won the pot.`
      : "Room ended.";
  } catch (error) {
    ui.result.textContent = error.message;
  }
});

ui.spinForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!session.roomCode || !session.playerId) {
    return;
  }

  ui.spinButton.disabled = true;
  ui.result.textContent = "Spinning";
  ui.reels.classList.add("is-spinning");

  try {
    const data = await api(`/api/rooms/${session.roomCode}/spin`, {
      method: "POST",
      body: JSON.stringify({
        playerId: session.playerId,
        lines: Number(ui.lines.value),
        bet: Number(ui.bet.value),
      }),
    });
    renderState(data.state);
    renderSpin(data.spin);
  } catch (error) {
    ui.result.textContent = error.message;
  } finally {
    ui.reels.classList.remove("is-spinning");
    ui.spinButton.disabled = false;
  }
});

renderReels(initialColumns);
if (location.port === "5500") {
  ui.result.textContent = apiServerMessage();
}
startPolling();
