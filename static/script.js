const BOARD_SIZE = 15;
const CELL_SIZE = 38;

let board = Array(BOARD_SIZE).fill().map(() => Array(BOARD_SIZE).fill(0));
let currentPlayer = 1;
let gameMode = 'easy';
let gameOver = false;
let moveCount = 0;

let turnStartTime;
let timerInterval;

let timeP1 = 4 * 60 * 1000;
let timeP2 = 4 * 60 * 1000;

const canvas = document.getElementById("board");
const ctx = canvas.getContext("2d");

const timerP1 = document.getElementById("timerP1");
const timerP2 = document.getElementById("timerP2");
const turnInfoEl = document.getElementById("turnInfo");
const moveCountEl = document.getElementById("moveCount");
const modeSelect = document.getElementById("gameMode");

init();

function init() {
    drawBoard();
    updateTurnInfo();
    startTurnTimer();
    modeSelect.addEventListener("change", () => {
        gameMode = modeSelect.value;
        document.getElementById("player2Title").textContent =
            gameMode === "pvp" ? "Người chơi 2 (O)" : "AI (O)";
    });
}

function drawBoard() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = "#f4a261";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.strokeStyle = "#2a2a2a";

    for (let i = 0; i < BOARD_SIZE; i++) {
        ctx.beginPath();
        ctx.moveTo(i * CELL_SIZE + CELL_SIZE / 2, CELL_SIZE / 2);
        ctx.lineTo(i * CELL_SIZE + CELL_SIZE / 2, canvas.height - CELL_SIZE / 2);
        ctx.moveTo(CELL_SIZE / 2, i * CELL_SIZE + CELL_SIZE / 2);
        ctx.lineTo(canvas.width - CELL_SIZE / 2, i * CELL_SIZE + CELL_SIZE / 2);
        ctx.stroke();
    }

    for (let r = 0; r < BOARD_SIZE; r++) {
        for (let c = 0; c < BOARD_SIZE; c++) {
            if (board[r][c] === 1) drawPiece(r, c, "#2a2a2a");
            if (board[r][c] === 2) drawPiece(r, c, "#fff", "#2a2a2a");
        }
    }
}

function drawPiece(row, col, fill, stroke = null) {
    const x = col * CELL_SIZE + CELL_SIZE / 2;
    const y = row * CELL_SIZE + CELL_SIZE / 2;

    ctx.beginPath();
    ctx.arc(x, y, 15, 0, Math.PI * 2);
    ctx.fillStyle = fill;
    ctx.fill();

    if (stroke) {
        ctx.strokeStyle = stroke;
        ctx.lineWidth = 3;
        ctx.stroke();
    }
}

canvas.addEventListener("click", async (e) => {
    if (gameOver) return;
    if (gameMode !== "pvp" && currentPlayer === 2) return;

    const rect = canvas.getBoundingClientRect();
    const col = Math.floor((e.clientX - rect.left) / CELL_SIZE);
    const row = Math.floor((e.clientY - rect.top) / CELL_SIZE);

    if (board[row][col] !== 0) return;

    makeMove(row, col, currentPlayer);

    if (!gameOver) {
        currentPlayer = 3 - currentPlayer;
        updateTurnInfo();
        startTurnTimer();

        if (gameMode !== "pvp" && currentPlayer === 2) {
            setTimeout(aiMove, 600);
        }
    }
});

function makeMove(row, col, player) {
    board[row][col] = player;
    moveCount++;
    moveCountEl.textContent = moveCount;

    drawBoard();

    if (checkWin(player)) {
        setTimeout(() => alert(player === 1 ? "Bạn thắng!" : "Đối thủ thắng!"), 120);
        gameOver = true;
        clearInterval(timerInterval);
    }
}

async function aiMove() {
    if (gameOver || currentPlayer !== 2) return;

    const res = await fetch("/ai_move", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ board, mode: gameMode })
    });

    const data = await res.json();

    if (!data.move) return;

    const [r, c] = data.move;
    makeMove(r, c, 2);

    currentPlayer = 1;
    updateTurnInfo();
    startTurnTimer();
}

function checkWin(player) {
    const dirs = [[1, 0], [0, 1], [1, 1], [1, -1]];

    for (let r = 0; r < BOARD_SIZE; r++) {
        for (let c = 0; c < BOARD_SIZE; c++) {
            if (board[r][c] !== player) continue;
            for (const [dx, dy] of dirs) {
                let cnt = 0;
                for (let k = 0; k < 5; k++) {
                    const x = r + dx * k, y = c + dy * k;
                    if (board[x]?.[y] === player) cnt++;
                }
                if (cnt === 5) return true;
            }
        }
    }
    return false;
}

/* ---------------- TIMER ---------------- */

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

        if (timeP1 <= 0 && currentPlayer === 1) {
            alert("Bạn hết giờ! AI đi thay.");
            currentPlayer = 2;
            startTurnTimer();
            aiMove();
        }
        if (timeP2 <= 0 && currentPlayer === 2) {
            alert("AI hết giờ! Bạn thắng!");
            gameOver = true;
            clearInterval(timerInterval);
        }

    }, 200);
}

function formatTime(ms) {
    const m = Math.floor(ms / 60000).toString().padStart(2, "0");
    const s = Math.floor((ms % 60000) / 1000).toString().padStart(2, "0");
    return `${m}:${s}`;
}

function updateTimers() {
    timerP1.textContent = formatTime(timeP1);
    timerP2.textContent = formatTime(timeP2);

    timerP1.classList.toggle("red", timeP1 < 30000);
    timerP2.classList.toggle("red", timeP2 < 30000);
}

function updateTurnInfo() {
    turnInfoEl.textContent =
        currentPlayer === 1 ? "Lượt của bạn (X)" :
            gameMode === "pvp" ? "Lượt của người chơi 2 (O)" :
                "AI đang suy nghĩ...";
}

function resetGame() {
    board = Array(BOARD_SIZE).fill().map(() => Array(BOARD_SIZE).fill(0));
    currentPlayer = 1;
    gameOver = false;
    moveCount = 0;

    timeP1 = 4 * 60 * 1000;
    timeP2 = 4 * 60 * 1000;

    moveCountEl.textContent = "0";
    timerP1.textContent = "04:00";
    timerP2.textContent = "04:00";

    drawBoard();
    updateTurnInfo();
    startTurnTimer();
}
