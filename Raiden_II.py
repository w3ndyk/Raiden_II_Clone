import pygame
import os
import sys
import time

# constants
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
L_GRAY = (240, 240, 240)

wn_w = 16*32
wn_h = 700

ship_w = wn_w/15
ship_h = wn_h/15

timer = 0


class Game:
    def __init__(self, caption, screen_w, screen_h):
        self.caption = pygame.display.set_caption(str(caption))
        self.screen = pygame.display.set_mode((screen_w, screen_h), pygame.SRCALPHA)
        self.clock = pygame.time.Clock()
        self.intro = self.play = self.outro = True
        self.lose = False

        # text
        self.title = Text(75, "Raiden 2 Clone", WHITE, 256, 540)
        self.click = Text(50, "-- Click here to start --", WHITE, 256, 605)
        self.again = Text(50, "-- Click here to play again --", WHITE, 256, 275)
        self.win = Text(70, "Thanks for playing!", WHITE, 256, 325)

        # sounds
        self.opening = pygame.mixer.Sound("sounds/op_music.ogg")
        self.start_button = pygame.mixer.Sound("sounds/start.ogg")
        self.start_button.set_volume(0.8)
        self.play_music = pygame.mixer.Sound("sounds/play_music.ogg")
        self.play_music.set_volume(0.8)
        self.game_over = pygame.mixer.Sound("sounds/game_over.ogg")
        self.ending = pygame.mixer.Sound("sounds/ending.ogg")

        # images
        self.intro_bg = pygame.image.load("images/op_bg.jpg").convert()
        self.intro_bg = pygame.transform.scale(self.intro_bg, (wn_w, wn_h))
        self.intro_bg_rect = self.intro_bg.get_rect()
        self.lose_bg = pygame.image.load("images/game_over.png").convert()
        self.lose_bg = pygame.transform.scale(self.lose_bg, (wn_w, wn_h))
        self.lose_bg_rect = self.lose_bg.get_rect()

    def blink(self, image, rect):
        # blinking text
        if (pygame.time.get_ticks() % 1500) < 500:
            self.screen.blit(image, rect)

    def update(self, ship, camera_e):
        # game over
        if ship.energy <= 0:
            ship.death_sound.play(0)
            time.sleep(0.5)
            self.play_music.stop()
            ship.kill()
            self.play = False
            self.lose = True
            self.game_over.play(0, 0, 2500)
        # win
        if camera_e.rect.y <= 0:
            self.play = False
            self.play_music.stop()
            self.ending.play(0, 0, 1500)
            self.again = Text(50, "-- Click here to play again --", WHITE, 256, 400)


class Text:
    def __init__(self, size, text, color, x, y):
        self.font = pygame.font.Font(None, int(size))
        self.image = self.font.render(str(text), 1, color)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)


class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.Surface((32, 32)).convert()
        self.image.fill(BLACK)
        self.rect = pygame.Rect(x, y, 32, 32)


class Ship(pygame.sprite.Sprite):
    def __init__(self, container):
        pygame.sprite.Sprite.__init__(self)
        self.container = container
        self.x_speed = 5
        self.y_speed = 4
        self.image = pygame.image.load("images/ship.png").convert_alpha()
        self.image = pygame.transform.scale(self.image, (ship_w * 2, ship_h * 2))
        self.rect = self.image.get_rect()
        self.rect.centerx = self.container.centerx
        self.rect.bottom = self.container.bottom - self.rect.height
        self.energy = 10

        # sounds
        self.bullet_sound = pygame.mixer.Sound("sounds/ship_bullet.ogg")
        self.bullet_sound.set_volume(0.08)
        self.death_sound = pygame.mixer.Sound("sounds/ship_death.ogg")
        self.death_sound.set_volume(0.5)

    def update(self, camera_entity_moving, bound, s_b_group, e_b_group, game):
        # uncontrollable for ~3 secs
        if timer > 150:
            # movement
            key = pygame.key.get_pressed()
            if key[pygame.K_w]:
                self.rect.y -= self.y_speed
            if key[pygame.K_s]:
                self.rect.y += self.y_speed
            if key[pygame.K_a]:
                self.rect.x -= self.x_speed
            if key[pygame.K_d]:
                self.rect.x += self.y_speed
            # bullets
            if timer % 8 == 0:
                if key[pygame.K_SPACE]:
                    l_bullet = Bullet(self, 'ship', 'center')
                    l_bullet.rect.centerx -= l_bullet.rect.width
                    r_bullet = Bullet(self, 'ship', 'center')
                    r_bullet.rect.centerx += r_bullet.rect.width
                    self.bullet_sound.play(0)
                    s_b_group.add(l_bullet, r_bullet)

        # follows camera_entity speed
        if camera_entity_moving:
            self.rect.y -= 1

        # out of screen boundaries
        if self.rect.y < -bound:
            self.rect.y = -bound
        if self.rect.y > wn_h - bound - self.rect.height:
            self.rect.y = wn_h - bound - self.rect.height

        self.rect.clamp_ip(self.container)

        # absorb bullet
        collisions = pygame.sprite.spritecollide(self, e_b_group, True)
        for key in collisions:
            self.energy -= key.energy


class Camera(object):
    def __init__(self, total_w, total_h):
        self.state = pygame.Rect(0, 0, total_w, total_h)

    def apply(self, target):
        return target.rect.move(self.state.topleft)

    def update(self, ship_rect, camera_entity_rect):
        x = self.x_camera(ship_rect)
        y = self.y_camera(camera_entity_rect)

        self.state = pygame.Rect(x, y, self.state.width, self.state.height)

    def x_camera(self, ship_rect):
        x = -ship_rect.centerx + wn_w / 2

        # stop scrolling at LEFT EDGE
        if x > 0:
            x = 0
        # stop scrolling at RIGHT EDGE
        elif x < -(self.state.width - wn_w):
            x = -(self.state.width - wn_w)

        return x

    def y_camera(self, camera_entity_rect):
        y = -camera_entity_rect.y + wn_h / 2

        # stop scrolling at TOP
        if y > 0:
            y = 0
        # stop scrolling at BOTTOM
        elif y < -(self.state.height - wn_h):
            y = -(self.state.height - wn_h)

        return y


class CameraEntity(pygame.sprite.Sprite):
    def __init__(self, container):
        pygame.sprite.Sprite.__init__(self)
        self.container = container
        self.image = pygame.Surface((8, 8)).convert()
        self.image.fill(L_GRAY)
        self.rect = self.image.get_rect()
        self.rect.centerx = self.container.centerx
        self.rect.y = self.container.bottom
        self.moving = False

    # PyMethod may be static
    def update(self):
        self.rect.y -= 1

        if self.rect.y < self.container.bottom - wn_h/2:
            self.moving = True

        if self.rect.y < wn_h/2:
            self.moving = False


class Bullet(pygame.sprite.Sprite):
    def __init__(self, ship, type, direction):
        pygame.sprite.Sprite.__init__(self)
        self.type = type
        self.direction = direction

        if self.type == 'ship':
            self.image = pygame.image.load("images/ship_bullet.png").convert_alpha()
        if self.type == 'huey':
            self.image = pygame.image.load("images/huey_bullet.png").convert_alpha()

        self.image = pygame.transform.scale(self.image, (10, 10))

        if self.direction == 'left':
            self.image = pygame.transform.rotate(self.image, -45)
        if self.direction == 'right':
            self.image = pygame.transform.rotate(self.image, 45)

        self.rect = self.image.get_rect()
        self.set_pos(ship)
        self.speed = 15
        self.energy = 1

    def set_pos(self, ship):
        self.rect.midbottom = ship.rect.midbottom

    def update(self, x_bound, y_bound, ship):
        # type
        if self.type == 'ship':
            self.rect.y -= self.speed
        
        if self.type == 'huey':
            self.rect.y += self.speed
            # direction
            if self.direction == 'right':
                self.rect.x += 10
            if self.direction == 'left':
                self.rect.x -= 10

        # out of screen
        if self.rect.y < (y_bound - self.rect.height) or self.rect.y > wn_h - y_bound:
            self.kill()
        if self.rect.x < (x_bound - self.rect.width) or self.rect.x > wn_w - x_bound:
            self.kill()


class Huey(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.x_speed = 2
        self.y_speed = 4
        self.image = pygame.image.load("images/huey.gif").convert_alpha()
        self.image = pygame.transform.scale(self.image, (ship_w * 2, ship_h * 2))
        self.rect = self.image.get_rect()
        self.rect.centerx = wn_w/2
        self.rect.bottom = -self.rect.height
        self.energy = 50

        # sounds
        self.bullet_sound = pygame.mixer.Sound("sounds/enemy_bullet.ogg")
        self.bullet_sound.set_volume(0.25)
        self.death_sound = pygame.mixer.Sound("sounds/enemy_death.ogg")
        self.death_sound.set_volume(0.7)

    def update(self, camera_entity_moving, bound, e_b_group, s_b_group):
        # movement
        if 250 < timer < 565:
            self.rect.y += self.y_speed
        if timer > 550:
            self.rect.y -= 1
            if timer % 85 == 0:
                # bullets
                self.bullet_sound.play(0)
                c_bullet = Bullet(self, 'huey', 'center')
                r_bullet = Bullet(self, 'huey', 'right')
                l_bullet = Bullet(self, 'huey', 'left')
                e_b_group.add(c_bullet, r_bullet, l_bullet)
            if 650 < timer < 800:
                self.rect.x += self.x_speed
            if 850 < timer < 1050:
                self.rect.x -= self.x_speed
            if 1100 < timer < 1250:
                self.rect.x += self.x_speed
            if 1250 < timer < 1300:
                self.rect.x -= self.x_speed
            if timer > 1350:
                self.rect.x += self.x_speed
                self.rect.y += self.y_speed/2
                # removed if out of screen
                if self.rect.x > wn_w - bound + self.rect.width:
                    self.kill()

        # absorb bullets
        collisions = pygame.sprite.spritecollide(self, s_b_group, True)
        for key in collisions:
            self.energy -= key.energy

        # death
        if self.energy <= 0:
            self.kill()
            self.death_sound.play(0)


def main():
    global wn_w, wn_h, timer, WHITE, BLACK, L_GRAY

    while True:
        # variables
        fps = 60
        timer = 0

        # objects
        game = Game('Raiden 2 Clone', wn_w, wn_h)

        # groups
        platform_group = pygame.sprite.Group()
        ship_bullet_group = pygame.sprite.Group()
        enemy_bullet_group = pygame.sprite.Group()

        # load level
        level = [
            "PPPPPPPPPPPPPPPPPPPPPP",
            "P                    P",
            "P                    P",
            "P                    P",
            "P                    P",
            "P                    P",
            "PPPP                 P",
            "P                    P",
            "P                    P",
            "P                PPPPP",
            "P                    P",
            "P                    P"
            "P                    P",
            "P                    P",
            "P                    P",
            "P                    P",
            "P              PPPPPPP",
            "P                    P",
            "PPPPPP               P",
            "P                    P",
            "P                    P",
            "P                    P",
            "P             PPPPPPPP",
            "P                    P",
            "P                    P",
            "PPPP                 P",
            "P                    P",
            "P                    P",
            "P                    P",
            "P                    P",
            "P                    P",
            "P                PPPPP",
            "P                    P",
            "PPPPPPPP             P",
            "P                    P",
            "P                    P",
            "P                    P",
            "P                PPPPP",
            "P                    P",
            "P                    P",
            "PPPP                 P",
            "P                    P",
            "P                    P",
            "P              PPPPPPP",
            "P                    P",
            "P                    P",
            "P                    P",
            "P                    P",
            "PPPPPP               P",
            "P                    P",
            "P                    P",
            "P             PPPPPPPP",
            "P                    P",
            "P                    P",
            "PPPP                 P",
            "P                    P",
            "P                    P",
            "P                PPPPP",
            "P                    P",
            "P                    P",
            "PPPPPPPPPPPPPPPPPPPPPP", ]

        # build level
        x = y = 0
        for row in level:
            for col in row:
                if col == 'P':
                    p = Platform(x, y)
                    platform_group.add(p)
                x += 32
            y += 32
            x = 0

        # camera
        total_w = len(level[0])*32
        total_h = len(level)*32
        camera = Camera(total_w, total_h)

        total_rect = pygame.rect.Rect(0, 0, total_w, total_h)

        # objects
        ship = Ship(total_rect)
        ship_group = pygame.sprite.Group()
        ship_group.add(ship)

        camera_entity = CameraEntity(total_rect)
        camera_entity_group = pygame.sprite.Group()
        camera_entity_group.add(camera_entity)

        huey = Huey()
        huey_group = pygame.sprite.Group()
        huey_group.add(huey)

        # music
        game.opening.play(-1, 0, 2500)

        # fade in opening background
        for x in range(0, 200):
            game.intro_bg.set_alpha(x)
            game.screen.blit(game.intro_bg, game.intro_bg_rect)
            pygame.display.update()
            x += 1

        # intro
        while game.intro:
            # checks if window exit button is pressed or if screen is clicked
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                # 5.5 second wait and next screen
                elif pygame.time.get_ticks() > 5500 and (event.type == pygame.MOUSEBUTTONDOWN or
                                                                 pygame.key.get_pressed()[pygame.K_RETURN] != 0):
                    game.screen.blit(game.click.image, game.click.rect)
                    pygame.display.flip()
                    game.intro = False
                    game.start_button.play(0, 0, 1500)
                    game.opening.fadeout(750)
                    time.sleep(1.5)
                    game.play_music.play(-1, 0, 2500)

            # blit images
            game.screen.blit(game.intro_bg, game.intro_bg_rect)
            game.screen.blit(game.title.image, game.title.rect)
            # blinking text
            game.blink(game.click.image, game.click.rect)

            # limits frames per iteration of while loop
            game.clock.tick(fps)
            # writes to main surface
            pygame.display.flip()

        # gameplay
        while game.play:
            # exit screen
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()

            # update
            game.screen.fill(L_GRAY)
            camera.update(ship.rect, camera_entity.rect)
            ship_group.update(camera_entity.moving, camera.state.y, ship_bullet_group, enemy_bullet_group, game)
            camera_entity_group.update()
            huey_group.update(camera_entity.moving, camera.state.x, enemy_bullet_group, ship_bullet_group)
            ship_bullet_group.update(camera.state.x, camera.state.y, ship)
            enemy_bullet_group.update(camera.state.x, camera.state.y, ship)
            game.update(ship, camera_entity)

            # draw everything
            for c in camera_entity_group:
                game.screen.blit(c.image, camera.apply(c))

            for p in platform_group:
                game.screen.blit(p.image, camera.apply(p))

            for b in ship_bullet_group:
                game.screen.blit(b.image, camera.apply(b))
            for x in enemy_bullet_group:
                game.screen.blit(x.image, camera.apply(x))

            for h in huey_group:
                game.screen.blit(h.image, camera.apply(h))
            for s in ship_group:
                game.screen.blit(s.image, camera.apply(s))

            # limits frames per iteration of while loop
            timer += 1
            game.clock.tick(fps)
            # writes to main surface
            pygame.display.flip()

        # game over
        while game.lose:
            # checks if window exit button is pressed or if screen is clicked
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN or pygame.key.get_pressed()[pygame.K_RETURN] != 0:
                    game.screen.blit(game.again.image, game.again.rect)
                    pygame.display.flip()
                    time.sleep(1)
                    game.outro = game.lose = False
                    game.game_over.stop()

            # blit images
            game.screen.blit(game.lose_bg, game.lose_bg_rect)
            # blinking text
            game.blink(game.again.image, game.again.rect)

            # limits frames per iteration of while loop
            game.clock.tick(fps)
            # writes to main surface
            pygame.display.flip()

        # outro
        while game.outro:
            # checks if window exit button is pressed or if screen is clicked
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN or pygame.key.get_pressed()[pygame.K_RETURN] != 0:
                    game.screen.blit(game.again.image, game.again.rect)
                    pygame.display.flip()
                    game.outro = False
                    time.sleep(1)
                    game.ending.stop()

            # blit images
            game.screen.fill(BLACK)
            game.screen.blit(game.win.image, game.win.rect)
            # blinking
            game.blink(game.again.image, game.again.rect)

            # limits frames per iteration of while loop
            game.clock.tick(fps)
            # writes to main surface
            pygame.display.flip()


if __name__ == "__main__":
    # force static position of screen
    os.environ['SDL_VIDEO_CENTERED'] = '1'

    # runs imported module
    pygame.init()

    # to get rid of sound lag
    pygame.mixer.pre_init(44100, -16, 2, 2048)

    main()
