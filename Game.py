import tkinter as tk
from tkinter import messagebox


class GameObject(object):
    def __init__(self, canvas, item):
        self.canvas = canvas
        self.item = item

    def get_position(self):
        return self.canvas.coords(self.item)

    def move(self, x, y):
        self.canvas.move(self.item, x, y)

    def delete(self):
        self.canvas.delete(self.item)


class Ball(GameObject):
    def __init__(self, canvas, x, y, speed=5):
        self.radius = 10
        self.direction = [1, -1]
        # increase the below value to increase the speed of ball
        self.speed = speed
        item = canvas.create_oval(x-self.radius, y-self.radius,
                                  x+self.radius, y+self.radius,
                                  fill='white')
        super(Ball, self).__init__(canvas, item)

    def update(self):
        coords = self.get_position()
        width = self.canvas.winfo_width()
        if coords[0] <= 0 or coords[2] >= width:
            self.direction[0] *= -1
        if coords[1] <= 0:
            self.direction[1] *= -1
        x = self.direction[0] * self.speed
        y = self.direction[1] * self.speed
        self.move(x, y)

    def collide(self, game_objects):
        coords = self.get_position()
        x = (coords[0] + coords[2]) * 0.5
        if len(game_objects) > 1:
            self.direction[1] *= -1
        elif len(game_objects) == 1:
            game_object = game_objects[0]
            coords = game_object.get_position()
            if x > coords[2]:
                self.direction[0] = 1
            elif x < coords[0]:
                self.direction[0] = -1
            else:
                self.direction[1] *= -1

        for game_object in game_objects:
            if isinstance(game_object, Brick):
                game_object.hit()


class Paddle(GameObject):
    def __init__(self, canvas, x, y):
        self.width = 80
        self.height = 10
        self.ball = None
        item = canvas.create_rectangle(x - self.width / 2,
                                       y - self.height / 2,
                                       x + self.width / 2,
                                       y + self.height / 2,
                                       fill='#FFB643')
        super(Paddle, self).__init__(canvas, item)

    def set_ball(self, ball):
        self.ball = ball

    def move(self, offset):
        coords = self.get_position()
        width = self.canvas.winfo_width()
        if coords[0] + offset >= 0 and coords[2] + offset <= width:
            super(Paddle, self).move(offset, 0)
            if self.ball is not None:
                self.ball.move(offset, 0)


class Brick(GameObject):
    COLORS = {1: '#4535AA', 2: '#ED639E', 3: '#8FE1A2', 4: '#F6C85F'}

    def __init__(self, canvas, x, y, hits):
        self.width = 75
        self.height = 20
        self.hits = hits
        color = Brick.COLORS.get(hits, list(Brick.COLORS.values())[-1])
        item = canvas.create_rectangle(x - self.width / 2,
                                       y - self.height / 2,
                                       x + self.width / 2,
                                       y + self.height / 2,
                                       fill=color, tags='brick')
        super(Brick, self).__init__(canvas, item)

    def hit(self):
        self.hits -= 1
        if self.hits == 0:
            self.delete()
        else:
            self.canvas.itemconfig(self.item,
                                   fill=Brick.COLORS.get(self.hits, '#FFFFFF'))


class Game(tk.Frame):
    def __init__(self, master):
        super(Game, self).__init__(master)
        self.lives = 3
        self.score = 0
        self.level = 1
        self.paused = False

        self.width = 610
        self.height = 400
        self.canvas = tk.Canvas(self, bg='#D6D1F5',
                                width=self.width,
                                height=self.height,)
        self.canvas.pack()
        self.pack()

        self.items = {}
        self.ball = None
        self.paddle = Paddle(self.canvas, self.width/2, 326)
        self.items[self.paddle.item] = self.paddle

        # build initial level
        self.build_level(self.level)

        # HUD placeholders
        self.hud = None
        self.score_hud = None
        self.level_hud = None
        self.update_hud()

        self.setup_game()
        self.canvas.focus_set()
        self.canvas.bind('<Left>', lambda _: self.paddle.move(-10))
        self.canvas.bind('<Right>', lambda _: self.paddle.move(10))
        self.canvas.bind('<space>', lambda _: self.toggle_pause())

    # ----------------- level & bricks -----------------
    def build_level(self, level):
        # cleanup existing bricks
        for item in self.canvas.find_withtag('brick'):
            try:
                self.canvas.delete(item)
            except Exception:
                pass
        # basic layout: number of rows increases with level
        rows = min(3 + level, 8)
        # hits scale with level (max 4)
        max_hits = min(1 + level // 2, 4)
        y_start = 50
        spacing_y = 22
        for row in range(rows):
            hits = max(1, max_hits - (row // 2))
            for x in range(5, self.width - 5, 75):
                brick = Brick(self.canvas, x + 37.5, y_start + row * spacing_y, hits)
                self.items[brick.item] = brick

    def next_level(self):
        self.level += 1
        self.build_level(self.level)
        # make ball slightly faster each level
        if self.ball:
            self.ball.speed = min(self.ball.speed + 1, 12)
        self.update_hud()
        self.setup_game()

    # ----------------- HUD -----------------
    def update_hud(self):
        self.update_lives_text()
        self.update_score_text()
        self.update_level_text()

    def update_lives_text(self):
        text = 'Lives: %s' % self.lives
        if self.hud is None:
            self.hud = self.draw_text(50, 20, text, 15)
        else:
            self.canvas.itemconfig(self.hud, text=text)

    def update_score_text(self):
        text = f'Score: {self.score}'
        if self.score_hud is None:
            self.score_hud = self.draw_text(300, 20, text, 12)
        else:
            self.canvas.itemconfig(self.score_hud, text=text)

    def update_level_text(self):
        text = f'Level: {self.level}'
        if self.level_hud is None:
            self.level_hud = self.draw_text(520, 20, text, 12)
        else:
            self.canvas.itemconfig(self.level_hud, text=text)

    # ----------------- game setup & loop -----------------
    def setup_game(self):
        # reset paddle position
        self.canvas.coords(self.paddle.item,
                           (self.width/2) - self.paddle.width/2,
                           326 - self.paddle.height/2,
                           (self.width/2) + self.paddle.width/2,
                           326 + self.paddle.height/2)
        self.add_ball()
        self.update_hud()
        # show start text
        self.text = self.draw_text(300, 200, 'Press Space to start or resume')

    def add_ball(self):
        if self.ball is not None:
            try:
                self.ball.delete()
            except Exception:
                pass
        paddle_coords = self.paddle.get_position()
        x = (paddle_coords[0] + paddle_coords[2]) * 0.5
        # speed depends on level
        speed = 5 + (self.level - 1) // 2
        self.ball = Ball(self.canvas, x, 310, speed=speed)
        self.paddle.set_ball(self.ball)

    def draw_text(self, x, y, text, size='40'):
        font = ('Forte', size)
        return self.canvas.create_text(x, y, text=text,
                                       font=font)

    def start_game(self):
        # remove start text and start loop
        try:
            self.canvas.delete(self.text)
        except Exception:
            pass
        self.paused = False
        self.game_loop()

    def toggle_pause(self):
        # space toggles pause/resume
        if hasattr(self, 'text') and self.text is not None:
            # if we're at the start screen, start instead of toggling
            self.start_game()
            return
        self.paused = not self.paused
        if not self.paused:
            # resume
            self.game_loop()
        else:
            # show paused text
            self.text = self.draw_text(300, 200, 'Paused')

    def game_loop(self):
        if self.paused:
            return
        # check collisions and game state
        self.check_collisions()
        num_bricks = len(self.canvas.find_withtag('brick'))
        if num_bricks == 0:
            # level complete
            self.ball.speed = None
            self.show_level_complete_popup()
            return
        elif self.ball.get_position()[3] >= self.height:
            # ball fell
            self.ball.speed = None
            self.lives -= 1
            self.update_lives_text()
            if self.lives < 0:
                # game over
                messagebox.showinfo('GAME OVER', f'Your Score: {self.score}')
                self.draw_text(300, 200, 'You Lose! Game Over!')
                return
            else:
                # reset ball & continue
                self.after(1000, self.setup_game)
                return
        else:
            self.ball.update()
            self.after(50, self.game_loop)

    # ----------------- collisions & scoring -----------------
    def check_collisions(self):
        # count bricks before
        bricks_before = len(self.canvas.find_withtag('brick'))

        ball_coords = self.ball.get_position()
        items = self.canvas.find_overlapping(*ball_coords)
        objects = [self.items[x] for x in items if x in self.items]

        # process collision
        self.ball.collide(objects)

        # cleanup any deleted canvas items from self.items
        active_ids = set(self.canvas.find_all())
        self.items = {k: v for k, v in self.items.items() if k in active_ids}

        # count bricks after
        bricks_after = len(self.canvas.find_withtag('brick'))
        destroyed = bricks_before - bricks_after
        if destroyed > 0:
            self.score += destroyed * 10
            self.update_score_text()

    # ----------------- popups -----------------
    def show_level_complete_popup(self):
        # pause game while popup is active
        self.paused = True

        popup = tk.Toplevel(self)
        popup.title('Level Complete')
        popup.geometry('300x150')
        popup.transient(self.master)
        popup.grab_set()

        label = tk.Label(popup, text=f'Level {self.level} Complete!')
        label.pack(pady=5)

        score_label = tk.Label(popup, text=f'Score: {self.score}')
        score_label.pack(pady=5)

        btn_frame = tk.Frame(popup)
        btn_frame.pack(pady=10)

        def on_next():
            popup.grab_release()
            popup.destroy()
            self.paused = False
            self.next_level()

        def on_pause_toggle():
            # toggle pause/resume inside the popup
            if self.paused:
                # currently paused -> resume and close popup
                self.paused = False
                popup.grab_release()
                popup.destroy()
                # resume loop
                self.game_loop()
            else:
                # pause game
                self.paused = True
                # change button text to 'Resume' not necessary here since we close popup

        next_btn = tk.Button(btn_frame, text='Lanjut', width=10, command=on_next)
        next_btn.grid(row=0, column=0, padx=5)

        pause_btn = tk.Button(btn_frame, text='Pause', width=10, command=on_pause_toggle)
        pause_btn.grid(row=0, column=1, padx=5)

    # ----------------- end -----------------


if __name__ == '__main__':
    root = tk.Tk()
    root.title('Break those Bricks!')
    game = Game(root)
    game.mainloop()
