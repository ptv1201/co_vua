import pygame
import chess
import sys
import math

# --- Cấu hình ---
WIDTH, HEIGHT = 640, 640
SQUARE_SIZE = WIDTH // 8
WHITE = (240, 217, 181)
BROWN = (77, 40, 0)
HIGHLIGHT_COLOR = (0, 255, 0, 100)  # Xanh lá 
HIGHLIGHT_COLOR_KING = (255, 0, 0, 150)  # Đỏ 

# --- Khởi tạo ---

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
highlight_surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
pygame.display.set_caption("Chess")
board = chess.Board()

pygame.mixer.init()
move_sound = pygame.mixer.Sound("sound/sfx_wing.wav")
capture_sound = pygame.mixer.Sound("sound/sfx_hit.wav")
check_sound = pygame.mixer.Sound("sound/sfx_point.wav")

# --- Tải hình ảnh quân cờ ---

pieces_img = {}
for piece in ['r', 'n', 'b', 'q', 'k', 'p']:  # đen: b
    img = pygame.image.load(f'asset/{piece}b.png')
    pieces_img[piece + 'b'] = pygame.transform.scale(img, (SQUARE_SIZE*0.7, SQUARE_SIZE))
for piece in ['r', 'n', 'b', 'q', 'k', 'p']:  # trắng: w
    img = pygame.image.load(f'asset/{piece}w.png')
    pieces_img[piece + 'w'] = pygame.transform.scale(img, (SQUARE_SIZE*0.7, SQUARE_SIZE))

# --- Đánh giá điểm quân cờ ---
piece_value = {
    chess.PAWN: 1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK: 5,
    chess.QUEEN: 9,
    chess.KING: 1000
}

# def evaluate_board(board):
#     score = 0
#     for square in chess.SQUARES:
#         piece = board.piece_at(square)
#         if piece:
#             value = piece_value[piece.piece_type]
#             score += value if piece.color == chess.WHITE else -value
#     return score

def evaluate_board(board):
    score = 0

    # Ưu tiên kiểm soát trung tâm
    center_squares = [chess.D4, chess.D5, chess.E4, chess.E5]

    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            value = piece_value[piece.piece_type]

            # Ưu tiên tấn công: cộng thêm điểm nếu quân trắng đang tấn công
            attack_bonus = 0
            if piece.color == chess.WHITE:
                attackers = board.attackers(chess.WHITE, square)
                if attackers:
                    attack_bonus += 0.2 * len(attackers)

            # Ưu tiên kiểm soát trung tâm
            center_bonus = 0
            if square in center_squares:
                center_bonus = 0.3

            # Cộng/trừ điểm theo màu
            if piece.color == chess.WHITE:
                score += value + attack_bonus + center_bonus
            else:
                score -= value + attack_bonus + center_bonus

    # Ưu tiên chiếu vua
    if board.is_check():
        score += 0.5 if board.turn == chess.BLACK else -0.5

    return score


# --- Thuật toán Minimax ---
def minimax(board, depth, alpha, beta, maximizing):
    if depth == 0 or board.is_game_over():
        return evaluate_board(board), None

    best_move = None

    if maximizing:
        max_eval = -math.inf
        for move in board.legal_moves:
            board.push(move)
            eval, _ = minimax(board, depth - 1, alpha, beta, False)
            board.pop()
            if eval > max_eval:
                max_eval = eval
                best_move = move
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval, best_move
    else:
        min_eval = math.inf
        for move in board.legal_moves:
            board.push(move)
            eval, _ = minimax(board, depth - 1, alpha, beta, True)
            board.pop()
            if eval < min_eval:
                min_eval = eval
                best_move = move
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval, best_move

# --- Vẽ bàn cờ và quân cờ ---
def draw_board():
    for rank in range(8):
        for file in range(8):
            color = WHITE if (rank + file) % 2 == 0 else BROWN
            pygame.draw.rect(screen, color, pygame.Rect(file*SQUARE_SIZE, rank*SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

def draw_pieces():
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            col = chess.square_file(square)
            row = 7 - chess.square_rank(square)
            key = piece.symbol().lower() + ('w' if piece.color == chess.WHITE else 'b')
            screen.blit(pieces_img[key], (col*SQUARE_SIZE, row*SQUARE_SIZE))
            
def highlight_moves(square):
    piece = board.piece_at(square)
    if not piece:
        return
    for move in board.legal_moves:
        if move.from_square == square:
            col = chess.square_file(move.to_square)
            row = 7 - chess.square_rank(move.to_square)
            highlight_surface.fill(HIGHLIGHT_COLOR)
            screen.blit(highlight_surface, (col * SQUARE_SIZE, row * SQUARE_SIZE))
            
def highlight_king_in_check():
    if board.is_check():
        king_square = board.king(board.turn)  # Lấy ô vua của bên đang bị chiếu
        col = chess.square_file(king_square)
        row = 7 - chess.square_rank(king_square)
        highlight_surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
        highlight_surface.fill(HIGHLIGHT_COLOR_KING)  # Màu đỏ với alpha
        screen.blit(highlight_surface, (col * SQUARE_SIZE, row * SQUARE_SIZE))


def get_square_from_mouse(pos):
    x, y = pos
    file = x // SQUARE_SIZE
    rank = 7 - (y // SQUARE_SIZE)
    return chess.square(file, rank)

# --- Vòng lặp chính ---
selected = None
running = True
player_turn = True  # người chơi là trắng

while running:
    draw_board()
    highlight_king_in_check()
    if selected is not None:
       highlight_moves(selected)
    draw_pieces()
    pygame.display.flip()

    if board.is_game_over():
        print("Game Over:", board.result())
        pygame.time.wait(3000)
        running = False
        break

    if not player_turn:
        pygame.time.wait(500)
        _, move = minimax(board, depth=3, alpha=-math.inf, beta=math.inf, maximizing=False)
        if move:
          if board.is_capture(move):
             capture_sound.play()
          else:
             move_sound.play()
          board.push(move)
          if board.is_check():
             check_sound.play()
          player_turn = True
        continue

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN and player_turn:
            square = get_square_from_mouse(pygame.mouse.get_pos())
            piece = board.piece_at(square)

            if selected is None:
                if piece and piece.color == chess.WHITE:
                    selected = square
            else:
                move = chess.Move(selected, square)
                if move in board.legal_moves:
                  if board.is_capture(move):
                     capture_sound.play()
                  else:
                     move_sound.play()
                  board.push(move)
                  if board.is_check():
                     check_sound.play()
                  player_turn = False

                selected = None

pygame.quit()
sys.exit()
