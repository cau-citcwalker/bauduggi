import asyncio
import pygame

# 초기화
pygame.init()

# 화면 설정
WIDTH, HEIGHT = 1280, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("바우덕이 놀이")

# 색상
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# FPS 설정
clock = pygame.time.Clock()

# 한글 폰트 설정
big_font = pygame.font.Font("./assets/font/font.ttf", 90)
font = pygame.font.Font("./assets/font/font.ttf", 70)
small_font = pygame.font.Font("./assets/font/font.ttf", 36)

# 리듬 데이터 불러오기
def load_rhythm_data(filename):
    rhythm_data = []
    with open(filename, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            time_str, col_str = line.split(",")
            rhythm_data.append((int(time_str), int(col_str)))
    return rhythm_data

rhythm_data = load_rhythm_data("./assets/rhythm/rhythm.txt")
rhythm_index = 0

# 이미지 불러오기
character_img_left = pygame.image.load("./assets/image/cha_left.png")
character_img_right = pygame.image.load("./assets/image/cha_right.png")
characters = [character_img_left, character_img_right]

CHAR_WIDTH, CHAR_HEIGHT = character_img_left.get_size()

# 부채 이미지 1개 불러오기
boochae_img = pygame.image.load("./assets/image/boochae.png")
boochae_img = pygame.transform.scale(boochae_img, (100, 70))  # 원하는 크기로 조절

enemy_img = pygame.image.load("./assets/image/plate.png")
enemy_img = pygame.transform.scale(enemy_img, (125, 100))

backgrounds = [
    pygame.image.load(f"./assets/image/background{i}.png") for i in range(6)
]
backgrounds = [pygame.transform.scale(bg, (WIDTH, HEIGHT)) for bg in backgrounds]

start_img = pygame.image.load("./assets/image/start.png")

# 배경 단계 결정 함수 (수정됨)
def get_background_stage(score, prev_stage):
    if score >= 194:
        stage = 5
    elif score > 150:
        stage = 4
    elif score > 110:
        stage = 3
    elif score > 60:
        stage = 2
    elif score > 40:
        stage = 1
    else:
        stage = 0

    if stage != prev_stage:
        return stage, "얼씨구!"
    else:
        return stage, ""

# 음악 준비
pygame.mixer.music.load("./assets/sound/game_bgm.mp3")
pygame.mixer.music.load("./assets/sound/lobby_bgm.mp3")
pygame.mixer.music.play(-1)

# 칼럼 설정
num_columns = 4
MARGIN_X = 100
game_width = WIDTH - MARGIN_X * 2
column_width = game_width // num_columns
columns_x = [MARGIN_X + column_width * i for i in range(num_columns)]

# 플레이어 초기 위치 (바닥에서 캐릭터 높이만큼 띄우기)
player_col = 0
player_pos_y = HEIGHT - CHAR_HEIGHT + 10

# 적 이동 속도 및 리스트
enemy_speed = 4
enemies = []

# 피드백 메시지 관련
feedback = ""
feedback_timer = 0
FEEDBACK_DURATION = 1000

# 점수 및 놓친 개수
score = 0
miss_count = 0
MAX_MISS = 3

# 게임 시작 기준 시간
start_time = 0

# 게임 상태 변수
game_started = False
game_over = False

# 이전 배경 단계 저장 변수 (전역)
prev_stage = -1

# 충돌 체크 함수 - y축 영역 겹침으로 정확도 개선
def detect_collision(player_col, enemy_col, player_y, enemy_y, player_height, enemy_height):
    if player_col != enemy_col:
        return False

    # 캐릭터 충돌 판정 영역
    effective_player_top = player_y + player_height * (1 / 3)
    effective_player_bottom = player_y + player_height * (1 / 3)

    enemy_top = enemy_y
    enemy_bottom = enemy_y + enemy_height

    return not (effective_player_bottom < enemy_top or enemy_bottom < effective_player_top)

# 게임 초기화 및 재시작 함수
def reset_game():
    global game_started, game_over, rhythm_index, enemies, feedback, score, miss_count, player_col, start_time, character_img, prev_stage
    game_started = True
    game_over = False
    rhythm_index = 0
    enemies.clear()
    feedback = ""
    score = 0
    miss_count = 0
    player_col = 1
    character_img = character_img_left
    start_time = pygame.time.get_ticks()
    pygame.mixer.music.load("./assets/sound/game_bgm.mp3")
    pygame.mixer.music.play()
    prev_stage = -1  # 배경단계 초기화

# 메인 루프 / 게임 진행 시간 (밀리초 단위), 1분 36초 = 96,000ms
game_duration = 96000
running = True
tick = 0
async def main():
    current_time = pygame.time.get_ticks()

    # 배경 그리기 및 배경단계 변경 체크
    if game_started or game_over:
        stage, new_feedback = get_background_stage(score, prev_stage)
        screen.blit(backgrounds[stage], (0, 0))

        # 부채 이미지 그리기 (왼쪽 상단)
        for i in range(MAX_MISS - miss_count):
            fan_x = 40 + i * (70 + 40)
            fan_y = 20
            screen.blit(boochae_img, (fan_x, fan_y))

        if new_feedback:
            feedback = new_feedback
            feedback_timer = current_time
            prev_stage = stage
    else:
        #title label
        text_Title = big_font.render("바우덕이 놀이", True, BLACK)
        temp_surface = pygame.Surface(text_Title.get_size())
        temp_surface.fill((192, 192, 192))
        temp_surface.set_alpha(50)
        temp_surface.blit(text_Title, (0, 0))

        #text label2
        text_start = small_font.render("마우스를 클릭해 시작하기", True, BLACK)  # 문구 변경
        start_surface = pygame.Surface(text_start.get_size())
        start_surface.fill((192, 192, 192))
        start_surface.set_alpha(50)
        start_surface.blit(text_start, (0, 0))

        #character animation
        character = characters[0]
        if 15 < tick < 30:
            character = characters[1]
        elif tick == 30:
            tick = 0
        character = pygame.transform.scale(character, (1200, 750))

        #draw objects
        screen.blit(backgrounds[0], (0, 0))
        screen.blit(character, (-400, -25))
        screen.blit(temp_surface, (WIDTH // 2 - text_Title.get_width() // 2, HEIGHT // 2 - 200))
        screen.blit(text_Title, (WIDTH // 2 - text_Title.get_width() // 2, HEIGHT // 2 - 200))
        screen.blit(start_surface, (WIDTH // 2 - text_start.get_width() // 2, HEIGHT // 2 -20))
        screen.blit(text_start, (WIDTH // 2 - text_start.get_width() // 2, HEIGHT // 2 -20))

        tick += 1

        # 이벤트 처리
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if not game_started and not game_over:
                reset_game()
            elif game_started and not game_over:
                mouse_x, _ = event.pos
                if mouse_x < WIDTH // 2 and player_col > 0:
                    player_col -= 1
                    character_img = character_img_left
                elif mouse_x >= WIDTH // 2 and player_col < num_columns - 1:
                    player_col += 1
                    character_img = character_img_right
            elif game_over:
                reset_game()

    # 키가 눌리지 않으면 이미지 유지
    keys = pygame.key.get_pressed()
    if not keys[pygame.K_LEFT] and not keys[pygame.K_RIGHT]:
        pass

    if game_started and not game_over:
        relative_time = current_time - start_time

        # 리듬에 맞춰 적 생성
        while rhythm_index < len(rhythm_data) and relative_time >= rhythm_data[rhythm_index][0]:
            spawn_col = rhythm_data[rhythm_index][1]
            enemies.append([spawn_col, 0])
            rhythm_index += 1

        # 적 이동 및 충돌 판정
        for enemy in enemies[:]:
            enemy[1] += enemy_speed

            if detect_collision(player_col, enemy[0], player_pos_y, enemy[1], CHAR_HEIGHT, 60):
                score += 1
                enemies.remove(enemy)

            elif enemy[1] > HEIGHT:
                feedback = "절씨구~"
                feedback_timer = current_time
                miss_count += 1
                enemies.remove(enemy)

        # 적 그리기 (칼럼 중앙 정렬)
        for enemy in enemies:
            enemy_x = columns_x[enemy[0]] + (column_width // 2) - (60 // 2)
            screen.blit(enemy_img, (enemy_x, enemy[1]))

        # 플레이어 그리기 (칼럼 중앙 정렬)
        player_x = columns_x[player_col] + (column_width // 2) - (CHAR_WIDTH // 2)
        screen.blit(character_img, (player_x, player_pos_y))

        # 게임 종료 조건 체크 & 음악 재생이 끝났는지 체크 추가
        music_pos = pygame.mixer.music.get_pos()  # 음악 재생 위치(ms), 재생중 아니면 -1 리턴

        if miss_count >= MAX_MISS or relative_time >= game_duration or music_pos == -1:
            game_over = True
            game_started = False
            pygame.mixer.music.stop()

    elif not game_started and not game_over:
        # 시작 화면 (이미 위에서 그림)
        pass

    elif game_over:
        # 게임 오버 화면 출력
        over_text = font.render("놀이 끝!", True, BLACK)
        retry_text = small_font.render("마우스를 클릭해 다시 놀기", True, BLACK)  # 문구 변경

        if score > 150:
            retry_text = small_font.render("마우스를 클릭해 다시 놀기", True, WHITE)

        screen.blit(over_text, (WIDTH // 2 - over_text.get_width() // 2, HEIGHT // 2 - 250))
        screen.blit(retry_text, (WIDTH // 2 - retry_text.get_width() // 2, HEIGHT // 2 + 20))

    # 피드백 메시지 출력
    if current_time - feedback_timer < FEEDBACK_DURATION and feedback:
        feedback_text = font.render(feedback, True, WHITE)
        if score < 194:
            feedback_text = font.render(feedback, True, BLACK)
        screen.blit(feedback_text, (WIDTH // 2 - feedback_text.get_width() // 2, HEIGHT // 2 - 150))

    pygame.display.flip()
    clock.tick(60)
    await asyncio.sleep(0)  # 이벤트 루프에 제어권 반환

asyncio.run(main())
pygame.quit()