import pygame
from .GameScene import GameScene
from .Player import Player
from .Mob import Mob
from .Coin import Coin
from .Map import Map
from .Camera import Camera
from .ParallaxBg import ParallaxLayer
from . import settings
import os
from .UI import Font


class Levels(GameScene):
    def __init__(self, switch_scene):
        self._switch_scene = switch_scene
        GameScene.__init__(self)

        self.levels = [
            'level0.tmx',
            'level1.tmx',
            'level5.tmx',
        ]
        self.current_level = 0

        self.level_complete = False
        self._fadeout_timer = 0
        self._fadeout_time = 2

        # sprite groups
        self.all_sprites = pygame.sprite.LayeredUpdates()
        self.mobs = pygame.sprite.Group()
        self.coins = pygame.sprite.Group()

        self.player = Player((0, 0), groups=(self.all_sprites,))
        self.camera = Camera()



        parallax_folder = os.path.join(settings.img_folder, "Parallax Forest Background (Seamless)",
                                       "edited")
        self.textures = {
            'parallax_1': pygame.image.load(os.path.join(parallax_folder, "06_Forest.png")).convert_alpha(),
            'parallax_2': pygame.image.load(os.path.join(parallax_folder, "07_Forest.png")).convert_alpha(),
            'parallax_3': pygame.image.load(os.path.join(parallax_folder, "08_Forest.png")).convert_alpha(),
            'coin': pygame.transform.scale(
                        pygame.image.load(os.path.join(settings.img_folder, "coins_animation.png")).convert_alpha().subsurface(pygame.Rect(0, 0, 16, 16)),
                        (32, 32)
                    ),
            "heart": pygame.transform.scale(pygame.image.load(os.path.join(settings.img_folder, "HUD", "heart.png")).convert_alpha(), (30, 27)),

        }
        # bg music
        # pygame.mixer.music.load(os.path.join(settings.music_folder, 'Road to Dazir.ogg'))
        # pygame.mixer.music.set_volume(0.5)
        # self._playing_bgm = False

        self.load_new_level(self.current_level)



    def load_new_level(self, level_num):
        self.all_sprites.empty()
        self.coins.empty()
        self.mobs.empty()
        self.all_sprites.add(self.player)

        self.level_complete = False
        self._fadeout_timer = 0

        self.map = Map(os.path.join(settings.levels_folder, self.levels[level_num]))
        self.map_img = self.map.make_map()
        self.player.set_pos(self.map.spawn_point)
        self.camera.set_boundaries(self.map_img.get_rect())
        self.camera.set_pos(self.map.spawn_point)

        # mob spawns
        for mob_spawn in self.map.mob_spawns:
            Mob(mob_spawn, groups=(self.all_sprites, self.mobs))

        # coins
        for coin_loc in self.map.coins:
            Coin(coin_loc[0], coin_loc[1], groups=(self.all_sprites, self.coins))

        # make parallax layers
        self.parallax_bg = [
            ParallaxLayer(self.textures['parallax_3'], 0.3, self.camera, self.map.width, self.map.height),
            ParallaxLayer(self.textures['parallax_2'], 0.4, self.camera, self.map.width, self.map.height),
            ParallaxLayer(self.textures['parallax_1'], 0.6, self.camera, self.map.width, self.map.height),
        ]
        self.parallax_fg = [
        ]

        # start bg music
        # pygame.mixer.music.play(-1)

    def render_backgrounds(self, surface):
        # surface.fill((222, 253, 253))
        for i in range(len(self.parallax_bg)):
            self.parallax_bg[i].render(surface, self.camera)

    def render_foregrounds(self, surface):
        for i in range(len(self.parallax_fg)):
            self.parallax_fg[i].render(surface, self.camera)

    def render_hud(self, surface):
        x = 30
        y = surface.get_rect().height - 40

        # health
        surface.blit(self.textures["heart"], (x, y))
        Font.put_text(surface, str(self.player.health), (x+35, y), (251, 251, 251))

        # coins
        surface.blit(self.textures["coin"], (x+100, y))
        Font.put_text(surface, str(self.player.coins), (x+140, y), (251, 251, 251))

    def render(self, surface):
        # if not self._playing_bgm:
        #     pygame.mixer.music.load(os.path.join(settings.music_folder, 'Road to Dazir.ogg'))
        #     pygame.mixer.music.set_volume(0.5)
        #     pygame.mixer.music.play(-1)
        #     self._playing_bgm = True

        if self.level_complete:
            surface.fill((220, 220, 220), special_flags=pygame.BLEND_MULT)
        else:
            self.render_backgrounds(surface)
            surface.blit(self.map_img, (0, 0), area=self.camera.camera_rect)
            for sprite in self.all_sprites:
                sprite.render(surface, self.camera)

            self.render_hud(surface)

            if settings.DEBUG_DRAW:
                for obs in self.map.collidables:
                    obs.render(surface, self.camera)
            # self.render_foregrounds(surface)


    def update(self, delta_time):
        self.camera.move_to(self.player.rect.center, delta_time)

        if not self.level_complete:
            # check if reached goal
            if self.map.goal.contains(self.player.rect):
                print("Level", self.current_level, "Complete!")
                self.level_complete = True
                self._fadeout_timer = self._fadeout_time

            # normal game loop updates
            self.player.update(delta_time, self.map, self.mobs, self.coins)
            for mob in self.mobs:
                mob.update(delta_time, self.map)
            for coin in self.coins:
                coin.update(delta_time)

            if self.player.health == 0:
                self.player.health = self.player._max_health
                self.load_new_level(self.current_level)

        # goal reached, fadeout animation
        elif self._fadeout_timer > 0:
            self._fadeout_timer -= delta_time

        # fadeout animation complete, load new level
        else:
            self.current_level = (self.current_level+1) % len(self.levels)
            self.load_new_level(self.current_level)

    def handle_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_n:
                if self.camera.boundaries is None:
                    self.camera.set_boundaries(self.map_img.get_rect())
                else:
                    self.camera.set_boundaries(None)
            elif event.key == pygame.K_p:
                self._switch_scene("pause_menu")

