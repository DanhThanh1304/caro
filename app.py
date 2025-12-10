from flask import Flask, render_template, request, jsonify
from copy import deepcopy
import random
import math

app = Flask(__name__)

BOARD_SIZE = 12

# =======================
# KIỂM TRA THẮNG
# =======================
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

# =======================
# HEURISTIC & MINIMAX
# =======================
def score_line(line, player):
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

def is_in(board, y, x):
    n = len(board)
    return 0 <= y < n and 0 <= x < n

def march(board, y, x, dy, dx, length):
    yf = y + length * dy
    xf = x + length * dx
    while not is_in(board, yf, xf):
        yf -= dy
        xf -= dx
    return yf, xf

def score_of_list(lis, player):
    if player not in lis and 0 not in lis:
        return -1
    opp = 1 if player == 2 else 2
    if opp in lis:
        return -1
    blank = lis.count(0)
    filled = lis.count(player)
    if blank == 5:
        return 0
    return filled

def row_to_list(board, y, x, dy, dx, yf, xf):
    row = []
    while y != yf + dy or x != xf + dx:
        if is_in(board, y, x):
            row.append(board[y][x])
        y += dy
        x += dx
    return row

def score_of_row(board, cordi, dy, dx, cordf, player):
    colscores = []
    y, x = cordi
    yf, xf = cordf
    row = row_to_list(board, y, x, dy, dx, yf, xf)
    if len(row) < 5:
        return []
    for start in range(len(row) - 4):
        score = score_of_list(row[start:start + 5], player)
        colscores.append(score)
    return colscores

def score_ready(scorecol):
    sumcol = {0: {}, 1: {}, 2: {}, 3: {}, 4: {}, 5: {}, -1: {}}
    for key in scorecol:
        for score in scorecol[key]:
            if key in sumcol[score]:
                sumcol[score][key] += 1
            else:
                sumcol[score][key] = 1
    return sumcol

def sum_sumcol_values(sumcol):
    for key in sumcol:
        if key == 5:
            sumcol[5] = int(1 in sumcol[5].values())
        else:
            sumcol[key] = sum(sumcol[key].values())

def score_of_col(board, player):
    f = len(board)
    scores = {(0, 1): [], (-1, 1): [], (1, 0): [], (1, 1): []}
    for start in range(f):
        scores[(0, 1)].extend(score_of_row(board, (start, 0), 0, 1, (start, f - 1), player))
        scores[(1, 0)].extend(score_of_row(board, (0, start), 1, 0, (f - 1, start), player))
        scores[(1, 1)].extend(score_of_row(board, (start, 0), 1, 1, (f - 1, f - 1 - start), player))
        scores[(-1, 1)].extend(score_of_row(board, (start, 0), -1, 1, (0, start), player))
        if start + 1 < f:
            scores[(1, 1)].extend(score_of_row(board, (0, start + 1), 1, 1, (f - 2 - start, f - 1), player))
            scores[(-1, 1)].extend(score_of_row(board, (f - 1, start + 1), -1, 1, (start + 1, f - 1), player))
    return score_ready(scores)

def get_static_heuristic_score(board):
    ai_scores = score_of_col(board, 2)
    sum_sumcol_values(ai_scores)
    human_scores = score_of_col(board, 1)
    sum_sumcol_values(human_scores)

    if ai_scores[5] > 0:
        return 100000
    if human_scores[5] > 0:
        return -100000

    ai_total = (ai_scores[1] * 1) + (ai_scores[2] * 4) + (ai_scores[3] * 8) + (ai_scores[4] * 100)
    human_total = (human_scores[1] * 1) + (human_scores[2] * 4) + (human_scores[3] * 8) + (human_scores[4] * 100)

    return ai_total - (human_total * 1.1)

def find_critical_moves(board, player):
    """
    Tìm các nước đi quan trọng:
    - Nước thắng ngay (4 quân liên tiếp)
    - Nước chặn đối phương (đối phương có 3+ quân liên tiếp)
    """
    n = len(board)
    critical = []
    opponent = 1 if player == 2 else 2
    
    # Kiểm tra tất cả ô trống
    for i in range(n):
        for j in range(n):
            if board[i][j] != 0:
                continue
            
            # Thử đặt quân của mình
            board[i][j] = player
            if check_win(board, player):
                board[i][j] = 0
                return [(i, j)]  # Thắng ngay, return luôn
            board[i][j] = 0
            
            # Thử đặt quân đối phương xem có nguy hiểm không
            board[i][j] = opponent
            if check_win(board, opponent):
                board[i][j] = 0
                critical.append((i, j))  # Phải chặn
                continue
            board[i][j] = 0
            
            # Kiểm tra đối phương có 3 quân liên tiếp không (nguy hiểm!)
            board[i][j] = opponent
            is_dangerous = False
            for dx, dy in [(1,0), (0,1), (1,1), (1,-1)]:
                count = 1  # Đếm quân ở vị trí hiện tại
                
                # Đếm về phía trước
                for k in range(1, 5):
                    x, y = i + dx*k, j + dy*k
                    if 0 <= x < n and 0 <= y < n and board[x][y] == opponent:
                        count += 1
                    else:
                        break
                
                # Đếm về phía sau
                for k in range(1, 5):
                    x, y = i - dx*k, j - dy*k
                    if 0 <= x < n and 0 <= y < n and board[x][y] == opponent:
                        count += 1
                    else:
                        break
                
                if count >= 3:  # 3 quân liên tiếp trở lên
                    is_dangerous = True
                    break
            
            board[i][j] = 0
            
            if is_dangerous:
                critical.append((i, j))
    
    return critical

def minimax(board, depth, player, maximizing, alpha, beta):
    opponent = 1
    if check_win(board, 2): return (None, 100000)
    if check_win(board, 1): return (None, -100000)
    if depth == 0:
        return (None, get_static_heuristic_score(board))

    moves = []
    n = len(board)
    
    # *** THÊM BƯỚC NÀY: Kiểm tra nước đi quan trọng trước ***
    critical_moves = find_critical_moves(board, 2)
    if critical_moves:
        moves = critical_moves  # Ưu tiên các nước đi quan trọng
    else:
        # Bước 1: Thu thập các nước đi gần quân cờ (trong vòng 2 ô)
        for i in range(n):
            for j in range(n):
                if board[i][j] == 0:
                    is_near = False
                    for dx in range(-2, 3):
                        for dy in range(-2, 3):
                            if dx == 0 and dy == 0: continue
                            if is_in(board, i+dx, j+dy) and board[i+dx][j+dy] != 0:
                                is_near = True
                                break
                        if is_near: break
                    if is_near:
                        moves.append((i,j))
        
        # Bước 2: Nếu không tìm thấy nước đi gần, lấy tất cả ô trống
        if not moves:
            for i in range(n):
                for j in range(n):
                    if board[i][j] == 0:
                        moves.append((i,j))
    
    # KIỂM TRA THÊM: Nếu vẫn không có nước đi (bàn cờ đầy)
    if not moves:
        return (None, 0)
    
    # Bước 3: Giới hạn số lượng nước đi (tối đa 20 nước) - BỎ QUA nếu là critical moves
    if len(moves) > 20 and not critical_moves:
        scored_moves = []
        for mv in moves:
            i, j = mv
            score = 0
            
            for dx, dy in [(1,0), (0,1), (1,1), (1,-1)]:
                for k in range(-4, 5):
                    x, y = i + k*dx, j + k*dy
                    if 0 <= x < n and 0 <= y < n:
                        if board[x][y] == 2:
                            score += 2
                        elif board[x][y] == 1:
                            score += 1
            
            scored_moves.append((score, mv))
        
        scored_moves.sort(reverse=True)
        moves = [mv for _, mv in scored_moves[:20]]

    # Bước 4: Xáo trộn (trừ khi là critical moves)
    if not critical_moves:
        random.shuffle(moves)
    
    best_move = None
    
    # Bước 5: Minimax với alpha-beta pruning
    if maximizing:
        max_eval = -math.inf
        for mv in moves:
            x, y = mv
            board[x][y] = 2
            _, eval_score = minimax(board, depth - 1, player, False, alpha, beta)
            board[x][y] = 0
            
            if eval_score > max_eval:
                max_eval = eval_score
                best_move = mv
            
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        
        return (best_move, max_eval)
    else:
        min_eval = math.inf
        for mv in moves:
            x, y = mv
            board[x][y] = 1
            _, eval_score = minimax(board, depth - 1, player, True, alpha, beta)
            board[x][y] = 0
            
            if eval_score < min_eval:
                min_eval = eval_score
                best_move = mv
            
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        
        return (best_move, min_eval)

# =======================
# ROUTES
# =======================
@app.route("/")
def home():
    # Trang chủ để chọn chế độ
    return render_template("home.html")
@app.route("/game")
def game():
    # Trang bàn cờ
    return render_template("game.html", board_size=12) # Đổi tên file index.html thành game.html

@app.route("/ai_move", methods=["POST"])
def ai_move():
    # ... (Giữ nguyên logic xử lý AI cũ) ...
    data = request.get_json()
    board = data.get("board")
    mode = data.get("mode","easy")

    if mode=="easy":
        # EASY = minimax depth 1
        bcopy = deepcopy(board)
        mv, sc = minimax(bcopy, 1, 2, True, -math.inf, math.inf)
    elif mode=="medium":
        # MEDIUM = minimax depth 2
        bcopy = deepcopy(board)
        mv, sc = minimax(bcopy, 2, 2, True, -math.inf, math.inf)
    else:
        # HARD = minimax depth 3 + heuristic fallback
        bcopy = deepcopy(board)
        mv, sc = minimax(bcopy, 3, 2, True, -math.inf, math.inf)
        if mv is None:
            mv = heuristic_move(board, 2)

    if mv is None:
        return jsonify({"move": None})
    return jsonify({"move": mv})

if __name__=="__main__":
    app.run(debug=True)


