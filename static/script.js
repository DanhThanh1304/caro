const BOARD_SIZE = 15;
const CELL_SIZE = 38;

// === CẤU HÌNH GIAO DIỆN (THEMES) ===
const THEMES = {
  wood: {
    board: "#eecfa1",
    line: "#5e4026",
    p1: { color: "#000", stroke: null }, // Đen
    p2: { color: "#fff", stroke: "#ddd" }, // Trắng
  },
  paper: {
    board: "#f8f9fa", // Màu giấy trắng
    line: "#2c3e50", // Đường kẻ đen nhạt
    p1: { color: "#2c3e50", stroke: null },
    p2: { color: "#ffffff", stroke: "#2c3e50" }, // Trắng viền đen
  },
  dark: {
    board: "#2d3436", // Màu xám đen
    line: "#636e72", // Đường kẻ xám sáng
    p1: { color: "#00cec9", stroke: null }, // Xanh Neon
    p2: { color: "#ff7675", stroke: null }, // Đỏ nhạt
  },
};

let currentTheme = "wood"; // Mặc định
let board = Array(BOARD_SIZE)
  .fill()
  .map(() => Array(BOARD_SIZE).fill(0));
let currentPlayer = 1;
let gameMode = "easy";
let gameOver = false;
let moveCount = 0;

let turnStartTime;
let timerInterval;
let timeP1 = 4 * 60 * 1000;
let timeP2 = 4 * 60 * 1000;

const canvas = document.getElementById("board");
const ctx = canvas.getContext("2d");

// UI Elements
const timerP1El = document.getElementById("timerP1");
const timerP2El = document.getElementById("timerP2");
const cardP1 = document.getElementById("p1-card");
const cardP2 = document.getElementById("p2-card");
const turnInfoEl = document.getElementById("turnInfo");
const moveCountEl = document.getElementById("moveCount");
const modeSelect = document.getElementById("gameMode");
const themeSelect = document.getElementById("themeSelect"); // Mới thêm
const player2Title = document.getElementById("player2Title");

init();

function init() {
  drawBoard();
  updateUIState();
  startTurnTimer();

  // Sự kiện chọn độ khó
  modeSelect.addEventListener("change", () => {
    gameMode = modeSelect.value;
    player2Title.textContent = gameMode === "pvp" ? "Người 2 (O)" : "AI (O)";
    resetGame();
  });

  // Sự kiện chọn Giao diện (Mới)
  themeSelect.addEventListener("change", () => {
    currentTheme = themeSelect.value;
    drawBoard(); // Vẽ lại ngay lập tức
  });
}

function drawBoard() {
  const theme = THEMES[currentTheme];

  // 1. Vẽ nền
  ctx.fillStyle = theme.board;
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  // 2. Vẽ lưới
  ctx.beginPath();
  ctx.strokeStyle = theme.line;
  ctx.lineWidth = 1;

  for (let i = 0; i < BOARD_SIZE; i++) {
    // Dọc
    ctx.moveTo(i * CELL_SIZE + CELL_SIZE / 2, CELL_SIZE / 2);
    ctx.lineTo(i * CELL_SIZE + CELL_SIZE / 2, canvas.height - CELL_SIZE / 2);
    // Ngang
    ctx.moveTo(CELL_SIZE / 2, i * CELL_SIZE + CELL_SIZE / 2);
    ctx.lineTo(canvas.width - CELL_SIZE / 2, i * CELL_SIZE + CELL_SIZE / 2);
  }
  ctx.stroke();

  // 3. Vẽ 5 điểm sao (Star points)
  const stars = [3, 7, 11];
  ctx.fillStyle = theme.line;
  for (let r of stars) {
    for (let c of stars) {
      ctx.beginPath();
      ctx.arc(
        c * CELL_SIZE + CELL_SIZE / 2,
        r * CELL_SIZE + CELL_SIZE / 2,
        3,
        0,
        Math.PI * 2
      );
      ctx.fill();
    }
  }

  // 4. Vẽ lại các quân cờ đã đánh
  for (let r = 0; r < BOARD_SIZE; r++) {
    for (let c = 0; c < BOARD_SIZE; c++) {
      if (board[r][c] !== 0) {
        drawPiece(r, c, board[r][c]);
      }
    }
  }
}

function drawPiece(row, col, player) {
  const theme = THEMES[currentTheme];
  const x = col * CELL_SIZE + CELL_SIZE / 2;
  const y = row * CELL_SIZE + CELL_SIZE / 2;
  const radius = 15;

  ctx.beginPath();

  // Logic màu sắc theo theme
  let color, stroke;
  if (player === 1) {
    color = theme.p1.color;
    stroke = theme.p1.stroke;
  } else {
    color = theme.p2.color;
    stroke = theme.p2.stroke;
  }

  // Nếu là theme Gỗ, dùng Gradient 3D cho đẹp
  if (currentTheme === "wood") {
    const grad = ctx.createRadialGradient(x - 5, y - 5, 2, x, y, radius);
    if (player === 1) {
      grad.addColorStop(0, "#555");
      grad.addColorStop(1, "#000");
    } else {
      grad.addColorStop(0, "#fff");
      grad.addColorStop(1, "#ddd");
    }
    ctx.fillStyle = grad;
    ctx.shadowColor = "rgba(0,0,0,0.4)";
    ctx.shadowBlur = 4;
    ctx.shadowOffsetX = 2;
    ctx.shadowOffsetY = 2;
  }
  // Các theme khác vẽ phẳng (Flat) cho hiện đại
  else {
    ctx.fillStyle = color;
    ctx.shadowColor = "transparent";
  }

  ctx.arc(x, y, radius, 0, Math.PI * 2);
  ctx.fill();

  // Vẽ viền (nếu có) - Cần thiết cho quân trắng trên nền trắng
  if (stroke) {
    ctx.lineWidth = 2;
    ctx.strokeStyle = stroke;
    ctx.stroke();
  }

  // Reset bóng đổ
  ctx.shadowColor = "transparent";
  ctx.shadowBlur = 0;
  ctx.shadowOffsetX = 0;
  ctx.shadowOffsetY = 0;
}

canvas.addEventListener("click", async (e) => {
  if (gameOver) return;
  if (gameMode !== "pvp" && currentPlayer === 2) return;

  const rect = canvas.getBoundingClientRect();
  const scaleX = canvas.width / rect.width;
  const scaleY = canvas.height / rect.height;

  const col = Math.floor(((e.clientX - rect.left) * scaleX) / CELL_SIZE);
  const row = Math.floor(((e.clientY - rect.top) * scaleY) / CELL_SIZE);

  if (board[row][col] !== 0) return;

  makeMove(row, col, currentPlayer);

  if (!gameOver) {
    currentPlayer = 3 - currentPlayer;
    updateUIState();
    startTurnTimer();

    if (gameMode !== "pvp" && currentPlayer === 2) {
      setTimeout(aiMove, 500);
    }
  }
});

function makeMove(row, col, player) {
  board[row][col] = player;
  moveCount++;
  moveCountEl.textContent = moveCount;

  // Vẽ lại bàn cờ để cập nhật nước đi mới
  drawBoard();

  // Vẽ viền đỏ đánh dấu nước vừa đi
  highlightLastMove(row, col);

  if (checkWin(player)) {
    let title = "";
    let msg = "";

    if (gameMode === "pvp") {
      title = player === 1 ? "CHIẾN THẮNG! 🏆" : "CHIẾN THẮNG! 🏆";
      msg =
        player === 1
          ? "Người chơi 1 (X) đã xuất sắc giành chiến thắng!"
          : "Người chơi 2 (O) đã xuất sắc giành chiến thắng!";
    } else {
      // Chế độ đấu AI
      if (player === 1) {
        title = "CHÚC MỪNG! 🎉";
        msg = "Bạn đã đánh bại AI! Trí tuệ siêu phàm!";
      } else {
        title = "THẤT BẠI... 💀";
        msg = "AI đã chiến thắng. Hãy thử lại nhé!";
      }
    }

    // Thay thế alert bằng showResult
    setTimeout(() => showResult(title, msg), 200);

    gameOver = true;
    clearInterval(timerInterval);
    turnInfoEl.textContent = "Trò chơi kết thúc!";
  }
}

function highlightLastMove(row, col) {
  const x = col * CELL_SIZE + CELL_SIZE / 2;
  const y = row * CELL_SIZE + CELL_SIZE / 2;

  ctx.beginPath();
  ctx.strokeStyle = "#e74c3c"; // Màu đỏ nổi bật
  ctx.lineWidth = 2;

  // Vẽ dấu + nhỏ ở giữa quân cờ để đánh dấu
  const size = 4;
  ctx.moveTo(x - size, y);
  ctx.lineTo(x + size, y);
  ctx.moveTo(x, y - size);
  ctx.lineTo(x, y + size);
  ctx.stroke();
}

async function aiMove() {
  if (gameOver || currentPlayer !== 2) return;

  turnInfoEl.textContent = "AI đang tính...";

  try {
    const res = await fetch("/ai_move", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ board, mode: gameMode }),
    });

    const data = await res.json();

    if (!data.move) return;

    const [r, c] = data.move;
    makeMove(r, c, 2);

    if (!gameOver) {
      currentPlayer = 1;
      updateUIState();
      startTurnTimer();
    }
  } catch (err) {
    console.error("Lỗi AI:", err);
  }
}

function checkWin(player) {
  const dirs = [
    [1, 0],
    [0, 1],
    [1, 1],
    [1, -1],
  ];
  for (let r = 0; r < BOARD_SIZE; r++) {
    for (let c = 0; c < BOARD_SIZE; c++) {
      if (board[r][c] !== player) continue;
      for (const [dx, dy] of dirs) {
        let cnt = 0;
        for (let k = 0; k < 5; k++) {
          const x = r + dx * k,
            y = c + dy * k;
          if (board[x]?.[y] === player) cnt++;
        }
        if (cnt === 5) return true;
      }
    }
  }
  return false;
}

/* ---------------- TIMER & UI ---------------- */

function startTurnTimer() {
  clearInterval(timerInterval);
  turnStartTime = Date.now();

  timerInterval = setInterval(() => {
    const now = Date.now();
    const elapsed = now - turnStartTime;

    if (currentPlayer === 1) timeP1 -= elapsed;
    else timeP2 -= elapsed;

    turnStartTime = now;
    updateTimers();

    // Xử lý khi Người chơi 1 hết giờ
    if (timeP1 <= 0 && currentPlayer === 1) {
      let msg =
        gameMode === "pvp"
          ? "Người chơi 1 hết giờ! Người chơi 2 thắng."
          : "Bạn đã hết thời gian suy nghĩ!";
      showResult("HẾT GIỜ ⏳", msg); // Dùng Modal

      gameOver = true;
      clearInterval(timerInterval);
    }

    // Xử lý khi Người chơi 2 (hoặc AI) hết giờ
    if (timeP2 <= 0 && currentPlayer === 2) {
      let msg =
        gameMode === "pvp"
          ? "Người chơi 2 hết giờ! Người chơi 1 thắng."
          : "AI đã hết thời gian!";
      showResult("ĐỐI THỦ HẾT GIỜ ⏳", msg); // Dùng Modal

      gameOver = true;
      clearInterval(timerInterval);
    }
  }, 200);
}

function formatTime(ms) {
  if (ms < 0) ms = 0;
  const m = Math.floor(ms / 60000)
    .toString()
    .padStart(2, "0");
  const s = Math.floor((ms % 60000) / 1000)
    .toString()
    .padStart(2, "0");
  return `${m}:${s}`;
}

function updateTimers() {
  timerP1El.textContent = formatTime(timeP1);
  timerP2El.textContent = formatTime(timeP2);
  timerP1El.classList.toggle("red", timeP1 < 30000);
  timerP2El.classList.toggle("red", timeP2 < 30000);
}

function updateUIState() {
  if (currentPlayer === 1) {
    turnInfoEl.textContent = "Lượt của bạn!";
    turnInfoEl.style.color = "#00ff9c";
    cardP1.classList.add("active");
    cardP2.classList.remove("active");
  } else {
    turnInfoEl.textContent =
      gameMode === "pvp" ? "Lượt người 2" : "AI đang tính...";
    turnInfoEl.style.color = "#fff";
    cardP1.classList.remove("active");
    cardP2.classList.add("active");
  }
}

function resetGame() {
  board = Array(BOARD_SIZE)
    .fill()
    .map(() => Array(BOARD_SIZE).fill(0));
  currentPlayer = 1;
  gameOver = false;
  moveCount = 0;
  timeP1 = 4 * 60 * 1000;
  timeP2 = 4 * 60 * 1000;

  moveCountEl.textContent = "0";
  timerP1El.textContent = "04:00";
  timerP2El.textContent = "04:00";
  timerP1El.classList.remove("red");
  timerP2El.classList.remove("red");

  drawBoard();
  updateUIState();
  startTurnTimer();
}

// === CÁC HÀM XỬ LÝ MODAL (Thêm vào cuối file) ===
const modal = document.getElementById("resultModal");
const modalTitle = document.getElementById("modalTitle");
const modalMsg = document.getElementById("modalMessage");

function showResult(title, message) {
  modalTitle.textContent = title;
  modalMsg.textContent = message;

  modal.classList.add("show"); // Hiện modal

  // Phát âm thanh chiến thắng nếu muốn (tùy chọn)
}

function closeModalAndReset() {
  modal.classList.remove("show"); // Ẩn modal
  resetGame(); // Gọi hàm reset game có sẵn
}
