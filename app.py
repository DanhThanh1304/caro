from flask import Flask, render_template, request, jsonify
import random
from copy import deepcopy
import math

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

#=================CHE DO TRUNG BINH=================

def is_in(board, y, x):
    n = len(board)
    return 0 <= y < n and 0 <= x < n

def march(board, y, x, dy, dx, length):
    
    # Tìm vị trí xa nhất trong dy,dx trong khoảng length
    
    yf = y + length * dy
    xf = x + length * dx
    # Chừng nào yf,xf không có trong board
    while not is_in(board, yf, xf):
        yf -= dy
        xf -= dx
    return yf, xf

def score_of_list(lis, player):
    
    # Đánh giá một đoạn 5 ô. player = 1 (người) hoặc 2 (AI)
    
    if player not in lis and 0 not in lis:
        # Bị chặn hoàn toàn bởi đối thủ
        return -1
        
    opp = 1 if player == 2 else 2
    
    # Nếu có quân cờ của đối thủ trong 5 ô này, đường này bị chặn
    if opp in lis:
        return -1
        
    blank = lis.count(0)
    filled = lis.count(player)
    
    if blank == 5: # 5 ô trống
        return 0
    
    # Trả về số quân cờ của player (1, 2, 3, 4, 5)
    return filled

def row_to_list(board, y, x, dy, dx, yf, xf):
    # trả về list của y,x từ yf,xf
    row = []
    while y != yf + dy or x != xf + dx:
        if is_in(board, y, x):
            row.append(board[y][x])
        y += dy
        x += dx
    return row

def score_of_row(board, cordi, dy, dx, cordf, player):
    
    # trả về một list với mỗi phần tử đại diện cho số điểm của 5 khối
    
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
    
    # Khởi tạo hệ thống điểm
    
    # -1: Bị chặn, 0: Trống, 1-5: Số quân
    sumcol = {0: {}, 1: {}, 2: {}, 3: {}, 4: {}, 5: {}, -1: {}}
    for key in scorecol:
        for score in scorecol[key]:
            if key in sumcol[score]:
                sumcol[score][key] += 1
            else:
                sumcol[score][key] = 1
    return sumcol

def sum_sumcol_values(sumcol):
    
    # hợp nhất điểm của mỗi hướng
    
    for key in sumcol:
        if key == 5:
            # Nếu có 1 đường 5, giá trị là 1 (thắng)
            sumcol[5] = int(1 in sumcol[5].values())
        else:
            # Cộng tổng số đường 1, 2, 3, 4...
            sumcol[key] = sum(sumcol[key].values())

def score_of_col(board, player):
    
    # Tính toán điểm số toàn bàn cờ cho 'player'
    
    f = len(board)
    # scores của 4 hướng đi
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
    
    # Hàm đánh giá tĩnh (static evaluation) cho Minimax. Tính toán điểm tổng cho AI (2) và Người chơi (1).
    
    
    # 1. Tính điểm cho AI (player 2)
    ai_scores = score_of_col(board, 2)
    sum_sumcol_values(ai_scores)
    
    # 2. Tính điểm cho Người (player 1)
    human_scores = score_of_col(board, 1)
    sum_sumcol_values(human_scores)

    # Nếu AI thắng
    if ai_scores[5] > 0:
        return 100000
    # Nếu Người thắng
    if human_scores[5] > 0:
        return -100000

    # Tính điểm dựa trên số lượng các đường
    # Ưu tiên cao cho đường 4, rồi 3, 2, 1
    ai_total = (ai_scores[1] * 1) + \
                 (ai_scores[2] * 4) + \
                 (ai_scores[3] * 8) + \
                 (ai_scores[4] * 100) # Đường 4 rất mạnh

    human_total = (human_scores[1] * 1) + \
                    (human_scores[2] * 4) + \
                    (human_scores[3] * 8) + \
                    (human_scores[4] * 100)

    # Trả về chênh lệch điểm, ưu tiên chặn đối thủ (human_total * 1.1)
    return ai_total - (human_total * 1.1)

#======================================================================

def minimax(board, depth, player, maximizing, alpha, beta):
    # player: AI player number (luôn là 2)
    opponent = 1 # Người chơi (luôn là 1)
    
    # Kiểm tra thắng/thua (trường hợp cơ sở)
    if check_win(board, 2): return (None, 100000)
    if check_win(board, 1): return (None, -100000)
    
    # Hết độ sâu (nút lá)
    if depth == 0:
        # **THAY ĐỔI QUAN TRỌNG:**
        # Sử dụng hàm heuristic mới thay vì đếm quân cờ đơn giản
        return (None, get_static_heuristic_score(board))

    # Lấy các nước đi có thể
    moves = []
    n = len(board)
    for i in range(n):
        for j in range(n):
            if board[i][j] == 0:
                # Thử ưu tiên các nước đi gần quân cờ đã có
                # (Tối ưu hóa đơn giản, có thể bỏ qua)
                is_near = False
                for dx in range(-1, 2):
                    for dy in range(-1, 2):
                        if dx == 0 and dy == 0: continue
                        if is_in(board, i+dx, j+dy) and board[i+dx][j+dy] != 0:
                            is_near = True; break
                    if is_near: break
                if is_near:
                    moves.append((i,j))
                    
    # Nếu không có nước đi nào (hòa)
    if not moves:
        # Nếu không tìm thấy nước đi "gần", thử tất cả các ô trống
        if not moves:
             for i in range(n):
                for j in range(n):
                    if board[i][j] == 0:
                        moves.append((i,j))
        if not moves:
            return (None, 0)
    
    # Sắp xếp ngẫu nhiên để đa dạng hóa
    random.shuffle(moves)

    best_move = None
    if maximizing: # Lượt của AI
        max_eval = -math.inf
        for mv in moves:
            x, y = mv
            board[x][y] = 2 # AI đi
            _, eval_score = minimax(board, depth - 1, player, False, alpha, beta)
            board[x][y] = 0 # Hoàn tác
            
            if eval_score > max_eval:
                max_eval = eval_score
                best_move = mv
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break # Cắt tỉa Alpha
        return (best_move, max_eval)
    
    else: # Lượt của Người chơi
        min_eval = math.inf
        for mv in moves:
            x, y = mv
            board[x][y] = 1 # Người đi
            _, eval_score = minimax(board, depth - 1, player, True, alpha, beta)
            board[x][y] = 0 # Hoàn tác
            
            if eval_score < min_eval:
                min_eval = eval_score
                best_move = mv
            beta = min(beta, eval_score)
            if beta <= alpha:
                break # Cắt tỉa Beta
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
        bcopy = deepcopy(board)
        mv, sc = minimax(bcopy, 3, 2, True, -math.inf, math.inf)
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
    app.run(debug=True)
