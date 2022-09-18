from telnetlib import GA
import time
import math
import pygame
import random


# initialize pygame
pygame.init()
background_img = pygame.image.load("res/images/background.jpg")


class Player:
    def __init__(self, img_path, width, height, x, y, dx, dy):
        self.img_path = img_path
        self.img = pygame.image.load(self.img_path)
        self.width = width
        self.height = height
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy

    def draw(self):
        self.display.blit(self.img, (self.x, self.y))


class Enemy:
    def __init__(self, img_path, width, height, x, y, dx, dy):
        self.img_path = img_path
        self.img = pygame.image.load(self.img_path)
        self.width = width
        self.height = height
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy

    def draw(self):
        self.display.blit(self.img, (self.x, self.y))


class Bullet:
    def __init__(self, img_path, width, height, x, y, dx, dy):
        self.img_path = img_path
        self.img = pygame.image.load(self.img_path)
        self.width = width
        self.height = height
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.fired = False

    def draw(self):
        if self.fired:
            self.display.blit(self.img, (self.x, self.y))


class Laser:
    def __init__(self, img_path, width, height, x, y, dx, dy, shoot_probability, relaxation_time):
        self.img_path = img_path
        self.img = pygame.image.load(self.img_path)
        self.width = width
        self.height = height
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.beamed = False
        self.shoot_probability = shoot_probability
        self.shoot_timer = 0
        self.relaxation_time = relaxation_time

    def draw(self):
        if self.beamed:
            self.display.blit(self.img, (self.x, self.y))


class Game:
    def __init__(self, w=800, h=600):
        self.h = h
        self.w = w
        self.display = pygame.display.set_mode((w, h))
        pygame.display.set_caption("Space Invaders")
        self.display_icon = pygame.image.load("res/images/alien.png")
        pygame.display.set_icon(self.display_icon)
        self.reset()

    def reset(self):
        self.running = True
        self.pause_state = 0
        self.score = 0
        self.highest_score = 0
        self.life = 3
        self.kills = 0
        self.difficulty = 1
        self.level = 1
        self.max_kills_to_difficulty_up = 5
        self.max_difficulty_to_level_up = 5
        self.initial_player_velocity = 3.0
        self.initial_enemy_velocity = 1.0
        self.weapon_shot_velocity = 5.0
        self.single_frame_rendering_time = 0
        self.total_time = 0
        self.frame_count = 0
        self.fps = 0

        # game objects
        self.player = type('Player', (), {})()
        self.bullet = type('Bullet', (), {})()
        self.enemies = []
        self.lasers = []

        # player
        player_img_path = "res/images/spaceship.png"  # 64 x 64 px image
        player_width = 64
        player_height = 64
        player_x = (self.w / 2) - (player_width / 2)
        player_y = (self.h / 10) * 9 - (player_height / 2)
        player_dx = self.initial_player_velocity
        player_dy = 0

        self.player = Player(player_img_path, player_width, player_height,
                             player_x, player_y, player_dx, player_dy)

        # bullet
        bullet_img_path = "res/images/bullet.png"  # 32 x 32 px image
        bullet_width = 32
        bullet_height = 32
        bullet_x = player_x + player_width / 2 - bullet_width / 2
        bullet_y = player_y + bullet_height / 2
        bullet_dx = 0
        bullet_dy = self.weapon_shot_velocity

        self.bullet = Bullet(bullet_img_path, bullet_width, bullet_height,
                             bullet_x, bullet_y, bullet_dx, bullet_dy)

        # enemy (number of enemy = level number)
        enemy_img_path = "res/images/enemy.png"  # 64 x 64 px image
        enemy_width = 64
        enemy_height = 64
        enemy_dx = self.initial_enemy_velocity
        enemy_dy = (self.h / 10) / 2

        # laser beam (equals number of enemies and retains corresponding enemy position)
        laser_img_path = "res/images/beam.png"  # 24 x 24 px image
        laser_width = 24
        laser_height = 24
        laser_dx = 0
        laser_dy = self.weapon_shot_velocity
        shoot_probability = 0.3
        relaxation_time = 100

        self.enemies.clear()
        self.lasers.clear()

        for lev in range(self.level):
            enemy_x = random.randint(0, (self.w - enemy_width))
            enemy_y = random.randint(
                ((self.h / 10) * 1 - (enemy_height / 2)), ((self.h / 10) * 4 - (enemy_height / 2)))
            laser_x = enemy_x + enemy_width / 2 - laser_width / 2
            laser_y = enemy_y + laser_height / 2

            enemy_obj = Enemy(enemy_img_path, enemy_width,
                              enemy_height, enemy_x, enemy_y, enemy_dx, enemy_dy)
            self.enemies.append(enemy_obj)

            laser_obj = Laser(laser_img_path, laser_width, laser_height, laser_x, laser_y, laser_dx, laser_dy,
                              shoot_probability, relaxation_time)
            self.lasers.append(laser_obj)

    def scoreboard(self):
        x_offset = 10
        y_offset = 10
        # set font type and size
        font = pygame.font.SysFont("calibre", 16)

        # render font and text sprites
        score_sprint = font.render(
            "SCORE : " + str(self.score), True, (255, 255, 255))
        highest_score_sprint = font.render(
            "HI-SCORE : " + str(self.highest_score), True, (255, 255, 255))
        level_sprint = font.render(
            "LEVEL : " + str(self.level), True, (255, 255, 255))
        difficulty_sprint = font.render(
            "DIFFICULTY : " + str(self.difficulty), True, (255, 255, 255))
        life_sprint = font.render(
            "LIFE LEFT : " + str(self.life) + " | " + ("@ " * self.life), True, (255, 255, 255))

        # performance info
        fps_sprint = font.render(
            "FPS : " + str(self.fps), True, (255, 255, 255))
        frame_time_in_ms = round(self.single_frame_rendering_time * 1000, 2)
        frame_time_sprint = font.render(
            "FT : " + str(frame_time_in_ms) + " ms", True, (255, 255, 255))

        # place the font sprites on the screen
        self.display.blit(score_sprint, (x_offset, y_offset))
        self.display.blit(highest_score_sprint, (x_offset, y_offset + 20))
        self.display.blit(level_sprint, (x_offset, y_offset + 40))
        self.display.blit(difficulty_sprint, (x_offset, y_offset + 60))
        self.display.blit(life_sprint, (x_offset, y_offset + 80))
        self.display.blit(fps_sprint, (self.w - 80, y_offset))
        self.display.blit(frame_time_sprint, (self.w - 80, y_offset + 20))

    def collision_check(self, object1, object2):
        x1_cm = object1.x + object1.width / 2
        y1_cm = object1.y + object1.width / 2
        x2_cm = object2.x + object2.width / 2
        y2_cm = object2.y + object2.width / 2
        distance = math.sqrt(math.pow((x2_cm - x1_cm), 2) +
                             math.pow((y2_cm - y1_cm), 2))
        return distance < ((object1.width + object2.width) / 2)

    def level_up(self):
        self.level += 1
        self.life += 1       # grant a life
        self.difficulty = 1
        if self.level % 3 == 0:
            self.player.dx += 1
            self.bullet.dy += 1
            max_difficulty_to_level_up += 1
            for each_laser in self.lasers:
                each_laser.shoot_probability += 0.1
                if each_laser.shoot_probability > 1.0:
                    each_laser.shoot_probability = 1.0
        if max_difficulty_to_level_up > 7:
            max_difficulty_to_level_up = 7

        font = pygame.font.SysFont("freesansbold", 64)
        gameover_sprint = font.render("LEVEL UP", True, (255, 255, 255))
        self.display.blit(gameover_sprint, (self.w / 2 - 120, self.h / 2 - 32))
        pygame.display.update()
        self.reset()
        time.sleep(1.0)

    def respawn(self, enemy_obj):
        enemy_obj.x = random.randint(0, (self.w - enemy_obj.width))
        enemy_obj.y = random.randint(((self.h / 10) * 1 - (enemy_obj.height / 2)),
                                     ((self.h / 10) * 4 - (enemy_obj.height / 2)))

    def kill_enemy(self, player_obj, bullet_obj, enemy_obj):
        bullet_obj.x = player_obj.x + player_obj.width / 2 - bullet_obj.width / 2
        bullet_obj.y = player_obj.y + bullet_obj.height / 2
        self.score = self.score + 10 * self.difficulty * self.level
        self.kills += 1
        if self.kills % self.max_kills_to_difficulty_up == 0:
            self.difficulty += 1
            if (self.difficulty == self.max_difficulty_to_level_up) and (self.life != 0):
                self.level_up()
        self.respawn(enemy_obj)

    def rebirth(self, player_obj):
        player_obj.x = (self.w / 2) - (player_obj.width / 2)
        player_obj.y = (self.h / 10) * 9 - (player_obj.height / 2)

    def gameover_screen(self):
        self.scoreboard()
        font = pygame.font.SysFont("freesansbold", 64)
        gameover_sprint = font.render("GAME OVER", True, (255, 255, 255))
        self.display.blit(gameover_sprint, (self.w / 2 - 140, self.h / 2 - 32))
        pygame.display.update()

        time.sleep(13.0)

    def gameover(self):
        if self.score > highest_score:
            highest_score = self.score

        running = False
        self.gameover_screen()

    def kill_player(self, player_obj, enemy_obj, laser_obj):
        laser_obj.beamed = False
        laser_obj.x = enemy_obj.x + enemy_obj.width / 2 - laser_obj.width / 2
        laser_obj.y = enemy_obj.y + laser_obj.height / 2
        self.life -= 1
        print("Life Left:", self.life)
        if self.life > 0:
            self.rebirth(player_obj)
        else:
            self.gameover()

    def destroy_weapons(self, player_obj, bullet_obj, enemy_obj, laser_obj):
        bullet_obj.fired = False
        laser_obj.beamed = False
        bullet_obj.x = player_obj.x + player_obj.width / 2 - bullet_obj.width / 2
        bullet_obj.y = player_obj.y + bullet_obj.height / 2
        laser_obj.x = enemy_obj.x + enemy_obj.width / 2 - laser_obj.width / 2
        laser_obj.y = enemy_obj.y + laser_obj.height / 2

    def pause_game(self):
        self.scoreboard()
        font = pygame.font.SysFont("freesansbold", 64)
        gameover_sprint = font.render("PAUSED", True, (255, 255, 255))
        self.display.blit(gameover_sprint, (self.w / 2 - 80, self.h / 2 - 32))
        pygame.display.update()

    def play_step(self):
        self.display.fill((0, 0, 0))
        self.display.blit(background_img, (0, 0))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()

            # Keypress Down Event
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    LEFT_ARROW_KEY_PRESSED = 1
                if event.key == pygame.K_RIGHT:
                    RIGHT_ARROW_KEY_PRESSED = 1
                if event.key == pygame.K_UP:
                    UP_ARROW_KEY_PRESSED = 1
                if event.key == pygame.K_SPACE:
                    SPACE_BAR_PRESSED = 1
                if event.key == pygame.K_RETURN:
                    ENTER_KEY_PRESSED = 1
                    pause_state += 1
                if event.key == pygame.K_ESCAPE:
                    ESC_KEY_PRESSED = 1
                    pause_state += 1

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_RIGHT:
                    RIGHT_ARROW_KEY_PRESSED = 0
                if event.key == pygame.K_LEFT:
                    LEFT_ARROW_KEY_PRESSED = 0
                if event.key == pygame.K_UP:
                    UP_ARROW_KEY_PRESSED = 0
                if event.key == pygame.K_SPACE:
                    SPACE_BAR_PRESSED = 0
                if event.key == pygame.K_RETURN:
                    ENTER_KEY_PRESSED = 0
                if event.key == pygame.K_ESCAPE:
                    ESC_KEY_PRESSED = 0

        if self.pause_state == 2:
            pause_state = 0
            runned_once = False

        if self.pause_state == 1:
            if not runned_once:
                runned_once = True
                self.pause_game()
            return
        # manipulate game objects based on events and player actions
        # player spaceship movement
        if RIGHT_ARROW_KEY_PRESSED:
            self.player.x += self.player.dx
        if LEFT_ARROW_KEY_PRESSED:
            self.player.x -= self.player.dx
        # bullet firing
        if (SPACE_BAR_PRESSED or UP_ARROW_KEY_PRESSED) and not self.bullet.fired:
            self.bullet.fired = True
            self.bullet.x = self.player.x + self.player.width / 2 - self.bullet.width / 2
            self.bullet.y = self.player.y + self.bullet.height / 2
        # bullet movement
        if self.bullet.fired:
            self.bullet.y -= self.bullet.dy

        # iter through every enemies and self.lasers
        for i in range(len(self.enemies)):
            # laser beaming
            if not self.lasers[i].beamed:
                self.lasers[i].shoot_timer += 1
                if self.lasers[i].shoot_timer == self.lasers[i].relaxation_time:
                    self.lasers[i].shoot_timer = 0
                    random_chance = random.randint(0, 100)
                    if random_chance <= (self.lasers[i].shoot_probability * 100):
                        self.lasers[i].beamed = True
                        self.lasers[i].x = self.enemies[i].x + \
                            self.enemies[i].width / 2 - \
                            self.lasers[i].width / 2
                        self.lasers[i].y = self.enemies[i].y + \
                            self.lasers[i].height / 2
            # enemy movement
            self.enemies[i].x += self.enemies[i].dx * \
                float(2 ** (difficulty - 1))
            # laser movement
            if self.lasers[i].beamed:
                self.lasers[i].y += self.lasers[i].dy

        # collision check
        for i in range(len(self.enemies)):
            bullet_enemy_collision = self.collision_check(
                self.bullet, self.enemies[i])
            if bullet_enemy_collision:
                self.kill_enemy(self.player, self.bullet, self.enemies[i])

        for i in range(len(self.lasers)):
            laser_player_collision = self.collision_check(
                self.lasers[i], self.player)
            if laser_player_collision:
                self.kill_player(self.player, self.enemies[i], self.lasers[i])

        for i in range(len(self.enemies)):
            enemy_player_collision = self.collision_check(
                self.enemies[i], self.player)
            if enemy_player_collision:
                self.kill_enemy(self.player, self.bullet, self.enemies[i])
                self.kill_player(self.player, self.enemies[i], self.lasers[i])

        for i in range(len(self.lasers)):
            bullet_laser_collision = self.collision_check(
                self.bullet, self.lasers[i])
            if bullet_laser_collision:
                self.destroy_weapons(
                    self.player, self.bullet, self.enemies[i], self.lasers[i])

        # boundary check: 0 <= x <= self.w, 0 <= y <= self.h
        # self.player spaceship
        if self.player.x < 0:
            self.player.x = 0
        if self.player.x > self.w - self.player.width:
            self.player.x = self.w - self.player.width
        # enemy
        for enemy in self.enemies:
            if enemy.x <= 0:
                enemy.dx = abs(enemy.dx) * 1
                enemy.y += enemy.dy
            if enemy.x >= self.w - enemy.width:
                enemy.dx = abs(enemy.dx) * -1
                enemy.y += enemy.dy
        # bullet
        if self.bullet.y < 0:
            self.bullet.fired = False
            self.bullet.x = self.player.x + self.player.width / 2 - self.bullet.width / 2
            self.bullet.y = self.player.y + self.bullet.height / 2
        # laser
        for i in range(len(self.lasers)):
            if self.lasers[i].y > self.h:
                self.lasers[i].beamed = False
                self.lasers[i].x = self.enemies[i].x + \
                    self.enemies[i].width / 2 - self.lasers[i].width / 2
                self.lasers[i].y = self.enemies[i].y + \
                    self.lasers[i].height / 2

        # create frame by placing objects on the surface
        self.scoreboard()
        for laser in self.lasers:
            laser.draw()
        for enemy in self.enemies:
            enemy.draw()
        self.bullet.draw()
        self.player.draw()

        pygame.display.update()
        frame_count += 1

        total_time = total_time + self.single_frame_rendering_time
        if total_time >= 1.0:
            self.fps = frame_count
            frame_count = 0
            total_time = 0


game = Game()
while True:
    game.play_step()
