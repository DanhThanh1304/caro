from flask import Flask, render_template, request, jsonify
import random
from copy import deepcopy
app = Flask(__name__)

BOARD_SIZE = 15

def check_win(board, player):
    n = len(board)
    dirs = [(1,0),(0,1),(1,1),(1,-1)]
    for i in range(n):
        for j in range(n):
            if board[i][j] != player:
                continue
            for dx,dy in dirs:
                cnt = 0
                x,y = i,j
                while 0<=x<n and 0<=y<n and board[x][y]==player:
                    cnt += 1
                    x += dx; y += dy
                if cnt>=5:
                    return True
    return False

def ai_easy(board):
    # random move
    n = len(board)
    empties = [(i,j) for i in range(n) for j in range(n) if board[i][j]==0]
    return random.choice(empties) if empties else None

def score_line(line, player):
    # simple heuristic scoring
    opp = 1 if player==2 else 2
    s = 0
    cnt_player = line.count(player)
    cnt_empty = line.count(0)
    if cnt_player==0:
        return 0
    s += cnt_player**2
    if cnt_empty==len(line)-cnt_player:
        s += cnt_player*2
    return s

def heuristic_move(board, player):
    n = len(board)
    best = None; best_score = -1
    for i in range(n):
        for j in range(n):
            if board[i][j]!=0: continue
            sc = 0
            # check rows, cols, diags around
            for dx,dy in [(1,0),(0,1),(1,1),(1,-1)]:
                line = []
                for k in range(-4,5):
                    x = i + k*dx; y = j + k*dy
                    if 0<=x<n and 0<=y<n:
                        line.append(board[x][y])
                sc += score_line(line, player)
                sc += score_line(line, 1 if player==2 else 2) * 0.9
            if sc>best_score:
                best_score = sc; best = (i,j)
    return best

def minimax(board, depth, player, maximizing, alpha, beta):
    # player: ai player number (2), maximizing when it's ai's turn
    opponent = 1 if player==2 else 2
    if check_win(board, 2): return (None, 10000)
    if check_win(board, 1): return (None, -10000)
    if depth==0:
        # evaluate simple heuristic
        sc = 0
        for i in range(len(board)):
            for j in range(len(board)):
                if board[i][j]==2:
                    sc += 1
                elif board[i][j]==1:
                    sc -= 1
        return (None, sc)
    moves = []
    n = len(board)
    for i in range(n):
        for j in range(n):
            if board[i][j]==0:
                moves.append((i,j))
    if not moves:
        return (None, 0)
    best_move = None
    if maximizing:
        max_eval = -10**9
        for mv in moves:
            x,y = mv
            board[x][y] = 2
            _, eval_score = minimax(board, depth-1, player, False, alpha, beta)
            board[x][y] = 0
            if eval_score>max_eval:
                max_eval = eval_score; best_move = mv
            alpha = max(alpha, eval_score)
            if beta<=alpha:
                break
        return (best_move, max_eval)
    else:
        min_eval = 10**9
        for mv in moves:
            x,y = mv
            board[x][y] = 1
            _, eval_score = minimax(board, depth-1, player, True, alpha, beta)
            board[x][y] = 0
            if eval_score<min_eval:
                min_eval = eval_score; best_move = mv
            beta = min(beta, eval_score)
            if beta<=alpha:
                break
        return (best_move, min_eval)

@app.route("/")
def index():
    return render_template("index.html", board_size=BOARD_SIZE)

@app.route("/ai_move", methods=["POST"])
def ai_move():
    data = request.get_json()
    board = data.get("board")
    mode = data.get("mode","easy")
    # board comes as list of lists with 0 empty, 1 player, 2 ai
    if mode=="easy":
        mv = ai_easy(board)
    elif mode=="medium":
        mv = heuristic_move(board, 2)
    else:
        # hard: try minimax with limited depth, fallback to heuristic
        bcopy = deepcopy(board)
        mv, sc = minimax(bcopy, 3, 2, True, -10**9, 10**9)
        if mv is None:
            mv = heuristic_move(board, 2)
    if mv is None:
        return jsonify({"move": None})
    return jsonify({"move": mv})

if __name__=="__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)
