# pylint: disable=no-member

import sys
import random
import pygame as py
import asyncio #ブラウザ上で遊べるように追加

# 設定
RED = (255, 0, 0)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)


def dq_f(number):
    # 数値を全角文字に変換する関数（ドラクエフォント）
    trans = str.maketrans({
        chr(0x0021 + i): chr(0xFF01 + i) for i in range(94)
    })
    return str(int(number)).translate(trans)

# 音源と再生の管理クラス
class Sound:
    def __init__(self):
        py.mixer.init()
        self.sounds = {
            "BGM": "sound/battle_bgm.ogg",
            "WIN": "sound/yhee.ogg",
            "LOSE": "sound/lose.ogg",
            "SEL": "sound/botton.ogg",
            "ATK": "sound/attack.ogg",
            "MAG": "sound/jyumon.ogg"
        }

# 音を鳴らす関数
    def play(self, key, loop=-1, is_bgm=True):
        if is_bgm:
                py.mixer.music.load(self.sounds[key])
                py.mixer.music.play(loop)
        else:
                py.mixer.Sound(self.sounds[key]).play()

# ステータスと行動の管理クラス
class Character:

#キャラクターのステータス関数
    def __init__(self, name, hp_max, image_path, pos, size, dmg_range):
        self.name = name
        self.hp = hp_max
        self.max_hp = hp_max
        self.display_hp = hp_max
        self.pos = list(pos)
        self.anime = 0
        self.dmg_min, self.dmg_max = dmg_range
        self.charge = 1
        self.barrier = False
        self.last_bar = False
        self.last_charge = False  # 前にチャージしたかの目印
        self.img = py.transform.scale(
            py.image.load(image_path).convert_alpha(), size
        )

#わざの関数
    def act(self, target, actuin):
        # 0:たたかう, 1:ため, 2:ばりあ を実行してメッセージを返す
        if actuin == 0:
            dmg = random.randint(self.dmg_min, self.dmg_max) * self.charge
            if target.barrier:
                dmg = 0
            target.hp = max(0, target.hp - dmg)
            # 行動後はフラグをすべてリセット
            self.anime, self.charge, self.last_bar, self.last_charge = 15, 1, False, False
            return f"{self.name}のこうげき！{target.name}に {dq_f(dmg)}ダメージ！"
        # チャージに記録と攻撃力アップ
        if actuin == 1:
            self.charge *= 1.2
            self.last_bar = False
            self.last_charge = True  
            return f"{self.name}は カ をためた！"

        # ばりあ
        self.barrier, self.last_bar = True, True
        self.last_charge = False  
        return f"{self.name}は まもりをかためた！"

# アニメーションとHPバーの更新
    def update(self):
        if self.anime > 0:
            self.anime -= 1
        diff = self.hp - self.display_hp
        if diff != 0:
            speed = max(abs(diff) // 10, 1)
            self.display_hp += (1 if diff > 0 else -1) * speed
# キャラクターとHPバーを描画
    def draw(self, screen, font, is_player):
        x_pos, y_pos = (480, 295) if is_player else (30, 40)
        offset = (40 if is_player else -40) if self.anime > 0 else 0
        screen.blit(self.img, (self.pos[0] + offset, self.pos[1]))

        ratio = self.display_hp / self.max_hp
        screen.blit(font.render(self.name, True, BLACK), (x_pos, y_pos))
        py.draw.rect(screen, (100, 100, 100), (x_pos, y_pos + 45, 200, 15))
        color = GREEN if ratio > 0.5 else YELLOW if ratio > 0.2 else RED
        py.draw.rect(screen, color, (x_pos, y_pos + 45, int(200 * ratio), 15))
        screen.blit(
            font.render(f"ＨＰ：{dq_f(self.display_hp)}", True, BLACK),
            (x_pos, y_pos + 65)
        )

# ゲーム全体の進行を管理するクラス
class  Advance:
    def __init__(self):
        py.init()
        self.screen = py.display.set_mode((800, 600))
        self.font = py.font.Font("asset/DragonQuestFC.ttf", 30)
        self.bg_img = py.transform.scale(
            py.image.load("asset/bf.png"),
            (800, 600)
        )
        self.snd = Sound()
        self.player = Character(
            "おちょめぐんそう", 800, "asset/player1.png",
            (90, 252), (180, 180), (80, 120)
        )
        self.enemy = Character(
            "ゴルゴバット", 500,
            "asset/character_monster_gargoyle_purple.png",
            (515, 115), (180, 180), (150,300) # 攻撃力の変更一番右
        )
        self.state = "INPUT"
        self.msg = f"{self.enemy.name}があらわれた！"
        self.selected_idx = 0
        self.queue = []
        self.snd.play("BGM")
# ボタンの入力処理
    def handle_key(self, key):
        if self.state == "END" and key == py.K_RETURN:
            py.quit()
            sys.exit()
        if self.state == "INPUT" and key == py.K_RETURN:
            # 連続使用のチェック
            if self.selected_idx == 2 and self.player.last_bar:
                self.msg = "ばりあ は れんぞくで使えない！"
                return
            if self.selected_idx == 1 and self.player.last_charge:
                self.msg = "ためわざ は れんぞくで使えない！"
                return
            # 敵の選択肢の決定
            opts = [0, 1, 2]
            if self.enemy.last_bar:
                opts.remove(2)
            if self.enemy.last_charge:
                opts.remove(1)
            e_idx = random.choice(opts)
            # 行動順決定
            if e_idx == 2 and self.selected_idx != 2:
                self.queue = [
                    (self.enemy, self.player, e_idx),
                    (self.player, self.enemy, self.selected_idx)
                ]
            else:
                self.queue = [
                    (self.player, self.enemy, self.selected_idx),
                    (self.enemy, self.player, e_idx)
                ]
            self.state = "MSG"
            self.next_move()

        elif self.state == "MSG" and key == py.K_RETURN:
            if self.queue:
                self.next_move()
            else:
                self.player.barrier = self.enemy.barrier = False
                self.msg, self.state = "どうする？", "INPUT"

# 次の行動
    def next_move(self):
        actor, target, idx = self.queue.pop(0)
        if actor.hp > 0:
            self.msg = actor.act(target, idx)
            self.snd.play("ATK" if idx == 0 else "MAG", is_bgm=False)
            if self.enemy.hp <= 0:
                self.msg, self.state = f"{self.enemy.name}をたおした！", "END"
                self.snd.play("WIN", 0)
            elif self.player.hp <= 0:
                self.msg, self.state = "はいぼく", "END"
                self.snd.play("LOSE", 0)

  # 画面表示
    def draw(self):
        self.screen.blit(self.bg_img, (0, 0))
        self.enemy.draw(self.screen, self.font, False)
        self.player.draw(self.screen, self.font, True)

        for i, line in enumerate(self.msg.split('\n')):
            text_surface = self.font.render(line, True, BLACK)
            self.screen.blit(text_surface, (60, 460 + i * 40))

        if self.state == "INPUT":
            cmds = ["たたかう", "ためわざ", "ばりあ"]
            for i, cmd in enumerate(cmds):
                color = RED if self.selected_idx == i else BLACK
                self.screen.blit(self.font.render(cmd, True, color),
                                 (530, 460 + i * 35))
        py.display.update()

#メインのループ処理
    async def run(self):
        clock = py.time.Clock()
        while True:
            for event in py.event.get():
                if event.type == py.QUIT:
                    py.quit()
                    sys.exit()
                if event.type == py.KEYDOWN:
                    if self.state == "INPUT" and event.key in (py.K_UP,
                                                              py.K_DOWN):
                        move = 1 if event.key == py.K_DOWN else -1
                        self.selected_idx = (self.selected_idx + move) % 3
                        self.snd.play("SEL", is_bgm=False)
                    else:
                        self.handle_key(event.key)
            self.player.update()
            self.enemy.update()
            self.draw()
            clock.tick(60)

            await asyncio.sleep(0)

# pygbagが認識できるように、外側に main() 関数を作る
async def main():
    game = Advance()
    await game.run()

if __name__ == "__main__":
    asyncio.run(main())