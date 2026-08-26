import random
import tkinter as tk


WIDTH = 800
HEIGHT = 480
GROUND_Y = 385

BACKGROUND = "#f7f4ea"
INK = "#232924"
GROUND = "#687466"
CACTUS = "#316f4e"
ACCENT = "#e16f48"


class DinoGame:
    def __init__(self, window):
        self.window = window
        self.window.title("Offline Dino Run")
        self.canvas = tk.Canvas(
            window,
            width=WIDTH,
            height=HEIGHT,
            bg=BACKGROUND,
            highlightthickness=0,
        )
        self.canvas.pack()
        self.window.bind("<space>", self.jump)
        self.window.bind("<Up>", self.jump)
        self.window.bind("<KeyPress-r>", self.restart)
        self.window.bind("<Escape>", lambda event: self.window.destroy())
        self.reset()
        self.update()

    def reset(self):
        self.dino_x = 100
        self.dino_y = GROUND_Y - 58
        self.dino_velocity = 0
        self.obstacles = []
        self.obstacle_timer = 50
        self.score = 0
        self.game_over = False
        self.ground_offset = 0

    def jump(self, event=None):
        if self.game_over:
            self.reset()
        elif self.dino_y >= GROUND_Y - 58:
            self.dino_velocity = -16

    def restart(self, event=None):
        if self.game_over:
            self.reset()

    def update(self):
        if not self.game_over:
            self.dino_velocity += 0.8
            self.dino_y += self.dino_velocity
            if self.dino_y > GROUND_Y - 58:
                self.dino_y = GROUND_Y - 58
                self.dino_velocity = 0

            self.obstacle_timer -= 1
            if self.obstacle_timer <= 0:
                height = random.choice((35, 45, 60))
                width = random.choice((18, 24, 30))
                self.obstacles.append([WIDTH + 20, height, width])
                self.obstacle_timer = random.randint(55, 100)

            for obstacle in self.obstacles:
                obstacle[0] -= 7
            self.obstacles = [
                obstacle for obstacle in self.obstacles if obstacle[0] + obstacle[2] > 0
            ]

            self.score += 1
            self.ground_offset = (self.ground_offset + 7) % 40
            self.check_collision()

        self.draw()
        self.window.after(16, self.update)

    def check_collision(self):
        dino_left = self.dino_x + 8
        dino_right = self.dino_x + 34
        dino_top = self.dino_y + 8
        dino_bottom = self.dino_y + 58

        for obstacle_x, obstacle_height, obstacle_width in self.obstacles:
            obstacle_left = obstacle_x
            obstacle_right = obstacle_x + obstacle_width
            obstacle_top = GROUND_Y - obstacle_height
            if (
                dino_right > obstacle_left
                and dino_left < obstacle_right
                and dino_bottom > obstacle_top
                and dino_top < GROUND_Y
            ):
                self.game_over = True

    def draw(self):
        self.canvas.delete("all")
        self.canvas.create_line(0, GROUND_Y, WIDTH, GROUND_Y, fill=GROUND, width=3)

        for x in range(-40, WIDTH + 40, 40):
            line_x = x - self.ground_offset
            self.canvas.create_line(
                line_x,
                GROUND_Y + 14,
                line_x + 16,
                GROUND_Y + 14,
                fill=GROUND,
                width=2,
            )

        self.draw_dinosaur()
        for obstacle_x, obstacle_height, obstacle_width in self.obstacles:
            self.draw_cactus(obstacle_x, obstacle_height, obstacle_width)

        self.canvas.create_text(
            WIDTH - 75,
            28,
            text=f"SCORE {self.score // 6:04d}",
            fill=INK,
            font=("TkFixedFont", 16),
        )

        if self.game_over:
            self.canvas.create_text(
                WIDTH // 2,
                HEIGHT // 2 - 24,
                text="GAME OVER",
                fill=ACCENT,
                font=("TkFixedFont", 36, "bold"),
            )
            self.canvas.create_text(
                WIDTH // 2,
                HEIGHT // 2 + 28,
                text="SPACE to jump    R to restart",
                fill=INK,
                font=("TkFixedFont", 16),
            )

    def draw_dinosaur(self):
        x = self.dino_x
        y = self.dino_y
        self.canvas.create_rectangle(x, y, x + 42, y + 58, fill=INK, outline=INK)
        self.canvas.create_rectangle(x + 34, y - 22, x + 50, y + 6, fill=INK, outline=INK)
        self.canvas.create_rectangle(x + 35, y - 15, x + 39, y - 11, fill=BACKGROUND, outline=BACKGROUND)
        self.canvas.create_rectangle(x + 6, y + 56, x + 13, y + 74, fill=INK, outline=INK)
        self.canvas.create_rectangle(x + 29, y + 56, x + 36, y + 74, fill=INK, outline=INK)

    def draw_cactus(self, x, height, width):
        top = GROUND_Y - height
        self.canvas.create_rectangle(x, top, x + width, GROUND_Y, fill=CACTUS, outline=CACTUS)
        self.canvas.create_rectangle(x - 10, top + 18, x, top + 26, fill=CACTUS, outline=CACTUS)
        self.canvas.create_rectangle(x - 10, top + 10, x - 2, top + 26, fill=CACTUS, outline=CACTUS)
        self.canvas.create_rectangle(x + width, top + 32, x + width + 10, top + 40, fill=CACTUS, outline=CACTUS)


window = tk.Tk()
DinoGame(window)
window.mainloop()
