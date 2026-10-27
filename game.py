import random
import time
import threading
from dataclasses import dataclass, field

# ============================================================
# КОНСТАНТЫ
# ============================================================

TICK_SECONDS = 30
TOTAL_TICKS = 200
CORE_SPAWN_MIN = 10
CORE_SPAWN_MAX = 15
PAUSE_SECONDS = 1.0

VASSAL_TRIBUTE = 20
ALLY_TRIBUTE = 10
SECT_WAR_SLOWDOWN = 0.5
OCCULT_COOLDOWN = 12
OCCULT_ROLLBACK = 9.5
SPY_COST = 50
OCCULT_COST = 150
VASSAL_IMMUNITY_TICKS = 10
DIGGER_MASSACRE_ARMY = 50
SECT_PEACE_DEADLINE = 6
ALLY_CORE_PRICE_MIN = 10000
ALLY_CORE_PRICE_MAX = 20000

CHERNOBOG_ACCEL_MULTIPLIER = 2.0   # во сколько раз ускоряется призыв

CHERNOBOG_PHASES = [
    ("Спокойствие", 999),
    ("Фаза I: Небо багровеет", 40),
    ("Фаза II: Алый луч", 40),
    ("Фаза III: Три красных глаза", 40),
    ("Ожидание: 6 тиков", 6),
    ("Призыв", 0),
]

# Индексы совпадают с CHERNOBOG_PHASES: 1..4 (Призыв баннера не имеет)
CHERNO_BANNERS = {
    1: ("Ф А З А   I", "Н Е Б О   Б А Г Р О В Е Е Т",
        "«Тени шевелятся на востоке...»"),
    2: ("Ф А З А   II", "А Л Ы Й   Л У Ч",
        "«Земля дрожит под ногами.»"),
    3: ("Ф А З А   III", "Т Р И   К Р А С Н Ы Х   Г Л А З А",
        "«Он смотрит. Он видит. Он ждёт.»"),
    4: ("Ф И Н А Л", "О Ж И Д А Н И Е",
        "«Три тика. Три удара сердца.»"),
}

TARGET_STOLICA = "stolica"
TARGET_GARRISON = "garrison"
TARGET_VAULT = "vault"
TARGET_PEACE = "peace"

REL_FRIEND = 70
REL_WARM = 50
REL_COLD = -30
REL_ENEMY = -70
REL_ALLY = 100
REL_ALLY_BREAK = 80

RUMOR_INTERVAL_MIN = 3
RUMOR_INTERVAL_MAX = 5


# ============================================================
# ТЕКСТЫ: РЕАКЦИИ НАРОДА И СЛУХИ
# ============================================================

REACTIONS = {
    "taxes": [
        "💰 Народ ворчит: «Правитель — сволочь! Где медицина и образование?»",
        "💰 Крестьяне шепчутся: «Опять дерут...»",
        "💰 Купцы недовольны: «Налоги душат торговлю!»",
        "💰 Старики качают головой: «При прошлом князе легче жилось.»",
    ],
    "war_declared": [
        "⚔️ Уныние в народе. Люди не хотят умирать за чужие земли.",
        "⚔️ Матери плачут: «Опять война...»",
        "⚔️ Парни прячутся по дворам, лишь бы не в ополчение.",
        "⚔️ Старики вздыхают: «Кровью зальют землю...»",
    ],
    "trade": [
        "🤝 Радость на рынках! Купцы ликуют.",
        "🤝 Люди довольны: «Наконец-то товары пошли!»",
        "🤝 Торговые лавки полны, народ гомонит и торгуется.",
        "🤝 Звон монет тешит горожан — жить стало легче.",
    ],
    "victory": [
        "🏆 Слава князю! Победа!",
        "🏆 «Герой! Герой!» — скандирует толпа.",
        "🏆 В честь победы народ гуляет и пьёт всю ночь.",
        "🏆 Гонцы разносят весть: наш князь непобедим!",
    ],
    "defeat": [
        "💀 Позор! Мы потеряли всё!",
        "💀 Князь не справился. Народ ропщет.",
        "💀 Траур в деревнях — не вернулись сыновья.",
        "💀 Уныние и злоба: «Куда ты нас завёл?»",
    ],
    "alliance": [
        "🤝 Народ надеется: с другом-соседом спокойнее.",
        "🤝 Горожане толкуют: «Слыхал? Князь союз заключил.»",
        "🤝 Купцы рады — с союзником торговать сподручнее.",
    ],
    "famine": [
        "🌾 Голод. В деревнях едят лебеду и кору.",
        "🌾 Бабы голосят: «Хлеба нет, дети пухнут!»",
        "🌾 На базаре давка за последнюю горсть муки.",
    ],
    "epidemic": [
        "🦠 Мор пошёл. На улицах пахнет дымом и горелым тряпьём.",
        "🦠 Люди бегут из городов, разнося хворь по дорогам.",
        "🦠 Знахари бессильны; кто в силах — молится.",
    ],
    "tower_activated": [
        "🕰️ Башня гудит — у народа волосы дыбом и трепет в сердце.",
        "🕰️ «Князь стал богом!» — шепчут на площадях.",
        "🕰️ Ночью над землями стоит красное зарево и звон.",
    ],
    "cherno_accel": [
        "🌑 Тени сгустились. Люди чувствуют: что-то не так.",
        "🌑 Собаки воют, дети видят дурные сны.",
        "🌑 В церквях свечи гаснут сами собой.",
    ],
}

RUMORS = {
    "taxes": ["Князь дерёт три шкуры!", "Князь бухает с сатаной!",
              "Опять поборы — хоть по миру иди."],
    "sect_war": ["Князь знается с тёмными!", "Он с бессмертным чай пил!"],
    "alliance": ["Князь продался!", "Теперь мы под чужими ходим..."],
    "war": ["Кровопийца! Опять война!", "Может, хватит?"],
    "tower_activated": ["Князь стал богом!", "Он теперь и время повернёт!"],
    "chaos": ["Конец близок!", "Чернобог идёт!"],
    "neutral": ["Погода-то какая...", "Князь-то наш ничего вроде."],
}


def pause(seconds: float = PAUSE_SECONDS):
    time.sleep(seconds)


# ============================================================
# СОСТОЯНИЕ
# ============================================================

@dataclass
class Ruler:
    name: str
    birth_tick: int
    lifespan_ticks: int
    is_immortal: bool = False
    knows_core: bool = True
    is_fool: bool = False
    is_aggressive: bool = False

    def is_dead(self, current_tick: int) -> bool:
        if self.is_immortal:
            return False
        return (current_tick - self.birth_tick) >= self.lifespan_ticks


@dataclass
class Neighbor:
    id: str
    name: str
    ruler: Ruler
    gold: int
    army: int
    army_quality: int
    has_core: bool = False
    core_revealed: bool = False
    has_tower: bool = False
    is_sect: bool = False
    is_diggers: bool = False
    is_destroyed: bool = False
    is_vassal: bool = False
    is_ally: bool = False
    ally_core_price: int = 0
    at_war_with_player: bool = False
    war_started_tick: int = 0
    ally_helped_in_war: bool = False
    relation_to_player: int = 0
    vassal_immunity_until: int = 0
    territory: int = 0
    food: int = 0
    intel_gold: int = -1
    intel_food: int = -1
    intel_expires_tick: int = 0

    def short_status(self) -> str:
        if self.is_destroyed:
            return "☠ уничтожено"
        tags = []
        if self.is_ally:
            tags.append("🤝СОЮЗ")
        if self.is_vassal:
            tags.append("🔗вассал")
        if self.at_war_with_player:
            tags.append("⚔ВОЙНА")
        if self.has_tower:
            tags.append("✨⌛")
        if self.has_core and self.core_revealed:
            tags.append("🔮ЯДРО")
        if self.is_sect:
            tags.append("🌑")
        parts = [f"⚔{self.army}"]
        if self.territory:
            parts.append(f"🏞️{self.territory}")
        if self.intel_gold >= 0:
            parts.append(f"[разведка: 💰{self.intel_gold}, 🌾{self.intel_food}]")
        if tags:
            parts.append(" ".join(tags))
        return " ".join(parts)


@dataclass
class PendingLetter:
    kind: str
    text: str
    neighbor_id: str | None = None
    amount: int = 0
    deadline_tick: int = 0


@dataclass
class Player:
    gold: int = 300
    army: int = 10
    army_quality: int = 5
    occult_army: int = 0
    occult_last_used_tick: int = -999
    spies: int = 0
    mail: list = field(default_factory=list)
    log: list = field(default_factory=list)
    has_core: bool = False
    has_tower: bool = True
    tower_activated: bool = False
    current_war_target: str | None = None
    pending_wars: list = field(default_factory=list)
    last_war_order: str = TARGET_GARRISON
    last_rumor: str = ""
    tax_collect_count: int = 0
    rumor_countdown: int = 0
    last_alliance_tick: int = -999
    science_level: int = 0
    science_cost: int = 500
    food: int = 100
    food_production: int = 0
    food_consumption: int = 0
    food_sowing: bool = False
    food_sowing_end_tick: int = 0
    population: int = 1000
    population_growth: float = 1.0
    mood: int = 50
    mood_calm_ticks: int = 0
    reputation: int = 50
    territory: int = 15


@dataclass
class GameState:
    tick: int = 0
    player: Player = field(default_factory=Player)
    neighbors: dict = field(default_factory=dict)
    core_owner_id: str | None = None
    core_spawned: bool = False
    core_spawn_tick: int = 0
    cherno_phase_idx: int = 0
    cherno_phase_tick: float = 0.0
    cherno_accelerated: bool = False   # ускорение Чернобога (навсегда)
    game_over: bool = False
    victory: bool = False
    victory_reason: str = ""
    last_tick_time: float = 0.0
    pending_letters: list = field(default_factory=list)


# ============================================================
# СОЗДАНИЕ МИРА
# ============================================================

def create_world() -> GameState:
    gs = GameState()

    gs.neighbors["huns"] = Neighbor(
        id="huns",
        name="Воинственные гунны",
        ruler=Ruler("Багдыр", 0, random.randint(40, 120), is_aggressive=True),
        gold=200, army=15, army_quality=7,
        territory=10, food=45,
    )
    gs.neighbors["varfolomey"] = Neighbor(
        id="varfolomey",
        name="Варфоломеева Империя",
        ruler=Ruler("Император Варфоломей XIV", 0, random.randint(40, 120)),
        gold=500, army=25, army_quality=8,
        territory=39, food=120,
    )
    gs.neighbors["sect"] = Neighbor(
        id="sect",
        name="Послы тёмного мира",
        ruler=Ruler("Бессмертный", 0, 999999, is_immortal=True),
        gold=100, army=10, army_quality=5,
        is_sect=True,
        territory=10, food=60,
    )
    gs.neighbors["ryazan"] = Neighbor(
        id="ryazan",
        name="Гибнущая Рязанская империя",
        ruler=Ruler("Князь Рязанский", 0, random.randint(40, 120)),
        gold=80, army=6, army_quality=3,
        territory=5, food=30,
    )
    gs.neighbors["diggers"] = Neighbor(
        id="diggers",
        name="Подземное царство Диггеров",
        ruler=Ruler("Король Кротов", 0, random.randint(40, 120)),
        gold=150, army=8, army_quality=2,
        is_diggers=True,
        territory=1, food=20,
    )

    gs.player.log.append("🏰 Ты — князь Великого Таймленда. Башня Времени стоит в твоих землях, но дремлет.")
    gs.player.log.append("🔮 Где-то далеко появится Ядро активации. Найди его.")
    gs.player.log.append("🌑 Секта тёмного мира готовит призыв Чернобога. Не дай ему прийти раньше времени.")
    return gs


# ============================================================
# АТМОСФЕРА: БАННЕР, РЕАКЦИИ, СЛУХИ
# ============================================================

def show_cherno_banner(gs: GameState, phase_idx: int):
    """Крупный красный баннер при смене фазы Чернобога. Держится 3 секунды."""
    data = CHERNO_BANNERS.get(phase_idx)
    if not data:
        return
    label, name, quote = data

    reset = "\033[0m"
    color = "\033[1m\033[91m"
    if gs.cherno_accelerated:
        color += "\033[5m"

    width = 48
    title = f"🌑 {label} : {name} 🌑"
    lines = [
        "╔" + "═" * width + "╗",
        "║" + " " * width + "║",
        "║" + title.center(width) + "║",
        "║" + " " * width + "║",
        "║" + quote.center(width) + "║",
        "║" + " " * width + "║",
    ]
    if gs.cherno_accelerated:
        lines.append("║" + "⚠️ УСКОРЕНО ⚠️".center(width) + "║")
        lines.append("║" + " " * width + "║")
    lines.append("╚" + "═" * width + "╝")

    print()
    for line in lines:
        print(f"{color}{line}{reset}")
    print(reset, end="")
    pause(3)


def react(gs: GameState, kind: str):
    """Флейвор-реакция народа: случайный текст в лог (без прямого вывода)."""
    variants = REACTIONS.get(kind)
    if not variants:
        return
    gs.player.log.append(random.choice(variants))


def tick_rumors(gs: GameState):
    """Раз в 3–5 тиков — контекстный слух: в лог и в шапку (last_rumor)."""
    p = gs.player
    if p.rumor_countdown > 0:
        p.rumor_countdown -= 1
        return
    p.rumor_countdown = random.randint(RUMOR_INTERVAL_MIN, RUMOR_INTERVAL_MAX)

    if any(n.is_sect and n.at_war_with_player for n in gs.neighbors.values()):
        context = "sect_war"
    elif p.last_alliance_tick >= 0 and gs.tick - p.last_alliance_tick <= 5:
        context = "alliance"
    elif p.current_war_target or p.pending_wars:
        context = "war"
    elif p.tower_activated:
        context = "tower_activated"
    elif gs.cherno_phase_idx >= 3:
        context = "chaos"
    elif p.tax_collect_count >= 3:
        context = "taxes"
    else:
        context = "neutral"

    rumor = random.choice(RUMORS[context])
    p.last_rumor = rumor
    gs.player.log.append(f"🗣️ Слух: «{rumor}»")
    if context == "taxes":
        p.tax_collect_count = 0


# ============================================================
# ВОЙНА: ОЧЕРЕДЬ
# ============================================================

def start_war_against_player(gs: GameState, n: Neighbor, reason: str):
    n.at_war_with_player = True
    n.war_started_tick = gs.tick

    if gs.player.current_war_target is None:
        gs.player.current_war_target = n.id
        gs.player.log.append(f"⚔️ {reason} Война с {n.name}!")
        queue_urgent(gs, "war_declared", f"⚔️ СРОЧНО: {reason} Война с {n.name}!", n.id)
    else:
        if n.id not in gs.player.pending_wars:
            gs.player.pending_wars.append(n.id)
        cur = gs.neighbors.get(gs.player.current_war_target)
        cur_name = cur.name if cur else "?"
        gs.player.log.append(f"⚔️ {reason} {n.name} встал в очередь (сейчас воюешь с {cur_name}).")
        gs.player.mail.append(f"📜 {n.name} объявил войну. Ждёт в очереди за {cur_name}.")

    call_allies_to_war(gs, n.id)


def advance_war_queue(gs: GameState):
    p = gs.player
    p.current_war_target = None
    while p.pending_wars:
        next_id = p.pending_wars.pop(0)
        n = gs.neighbors.get(next_id)
        if n and not n.is_destroyed and n.at_war_with_player:
            p.current_war_target = next_id
            gs.player.log.append(f"⚔️ Теперь твой противник: {n.name}.")
            queue_urgent(gs, "war_declared", f"⚔️ СРОЧНО: {n.name} — теперь твой противник!", n.id)
            return


def call_allies_to_war(gs: GameState, enemy_id: str):
    for ally in gs.neighbors.values():
        if not ally.is_ally or ally.is_destroyed:
            continue
        if ally.ally_helped_in_war:
            continue
        helpers = random.randint(1, 2)
        gs.player.army += helpers
        ally.ally_helped_in_war = True
        gs.player.log.append(f"🤝 Союзник {ally.name} прислал {helpers} воинов!")
        gs.player.mail.append(f"📜 {ally.name} прислал {helpers} воинов на войну.")


def reset_ally_help_flags(gs: GameState):
    for n in gs.neighbors.values():
        n.ally_helped_in_war = False


# ============================================================
# ЛОГИКА ТИКА
# ============================================================

def queue_urgent(gs: GameState, kind: str, text: str, neighbor_id=None, amount=0):
    gs.pending_letters.append(PendingLetter(
        kind=kind, text=text, neighbor_id=neighbor_id, amount=amount,
        deadline_tick=gs.tick + 1,
    ))


def tick_core_spawn(gs: GameState):
    if gs.core_spawned:
        return
    if gs.tick >= gs.core_spawn_tick:
        candidates = [n for n in gs.neighbors.values() if not n.is_destroyed and not n.is_sect]
        owner = random.choice(candidates)
        owner.has_core = True
        owner.core_revealed = False
        gs.core_owner_id = owner.id
        gs.core_spawned = True
        gs.player.log.append("🔮 Ядро активации появилось у кого-то из соседей.")
        queue_urgent(
            gs,
            "core_spotted",
            "🔮 СРОЧНО: по слухам, у кого-то из соседей появилось Ядро активации Башни. Пошли шпионов на разведку!"
        )


def is_too_peaceful(gs: GameState) -> bool:
    """Проверяет, не стал ли игрок слишком могущественным.
    Все 4 условия:
      1. Ядро у игрока
      2. Башня у игрока
      3. Нет активных войн
      4. Все соседи — вассалы/союзники/уничтожены
    """
    p = gs.player
    if not p.has_core:
        return False
    if not p.has_tower:
        return False
    if p.current_war_target is not None or p.pending_wars:
        return False
    for n in gs.neighbors.values():
        if n.is_sect:
            continue  # секта не в счёт
        if n.is_destroyed:
            continue
        if n.is_vassal or n.is_ally:
            continue
        # Есть независимый сосед — не мирно
        return False
    return True


def tick_cherno(gs: GameState):
    if gs.core_spawned and gs.cherno_phase_idx == 0:
        gs.cherno_phase_idx = 1
        gs.cherno_phase_tick = 0
        gs.player.log.append(f"🌑 {CHERNOBOG_PHASES[1][0]} — небо на востоке наливается багровым.")
        show_cherno_banner(gs, 1)

    if gs.cherno_phase_idx == 0:
        return

    # --- Проверка на ускорение (один раз, навсегда) ---
    if not gs.cherno_accelerated and is_too_peaceful(gs):
        gs.cherno_accelerated = True
        gs.player.log.append("🌑 Секта узрела твою мощь и ускорила ритуал! Призыв ×2.")
        react(gs, "cherno_accel")
        queue_urgent(
            gs, "core_spotted",
            "🌑 СРОЧНО: Чернобог чувствует твоё могущество! Призыв ускоряется вдвое. Тени гнева придут раньше!"
        )

    # --- Базовый инкремент ---
    increment = 1.0
    sect = gs.neighbors.get("sect")
    if sect and sect.at_war_with_player:
        increment -= SECT_WAR_SLOWDOWN

    # --- Ускорение (если активировано) ---
    if gs.cherno_accelerated:
        increment *= CHERNOBOG_ACCEL_MULTIPLIER

    increment = max(0.0, increment)

    name, duration = CHERNOBOG_PHASES[gs.cherno_phase_idx]
    gs.cherno_phase_tick += increment
    gs.cherno_phase_tick = max(0.0, gs.cherno_phase_tick)

    if gs.cherno_phase_tick >= duration:
        gs.cherno_phase_idx += 1
        gs.cherno_phase_tick = 0
        if gs.cherno_phase_idx < len(CHERNOBOG_PHASES):
            show_cherno_banner(gs, gs.cherno_phase_idx)
            next_name = CHERNOBOG_PHASES[gs.cherno_phase_idx][0]
            gs.player.log.append(f"🌑 {next_name}")
        else:
            trigger_apocalypse(gs)


def trigger_apocalypse(gs: GameState):
    if gs.player.tower_activated:
        gs.game_over = True
        gs.victory = True
        gs.victory_reason = "🕰️ Бог Времени явился и разорвал Чернобога! Ты победил."
    else:
        gs.game_over = True
        gs.victory = False
        gs.victory_reason = "💀 Чернобог пришёл. Тени гнева стёрли всех. Ты проиграл."


def tick_neighbors(gs: GameState):
    for n in gs.neighbors.values():
        if n.is_destroyed:
            continue
        if gs.tick > n.intel_expires_tick and n.intel_expires_tick != 0:
            n.intel_gold = -1
            n.intel_food = -1
            n.intel_expires_tick = 0

        # Смерть правителя
        if n.ruler.is_dead(gs.tick):
            old_name = n.ruler.name
            is_fool = random.random() > 0.7
            is_aggressive = random.random() < 0.4
            n.ruler = Ruler(
                name=f"Наследник {old_name}",
                birth_tick=gs.tick,
                lifespan_ticks=random.randint(40, 120),
                is_immortal=n.is_sect,
                knows_core=random.random() > 0.3,
                is_fool=is_fool,
                is_aggressive=is_aggressive,
            )
            gs.player.log.append(f"📬 Умер {old_name} ({n.name}). Новый правитель: {n.ruler.name}")
            gs.player.mail.append(f"📜 Умер {old_name}. Трон {n.name} занял {n.ruler.name}.")
            if n.has_core and not n.ruler.knows_core:
                gs.player.mail.append(f"📜 Слух: {n.ruler.name}, кажется, не в курсе, что у него хранится нечто важное...")

        # ЗАМОРОЗКА: враг в очереди
        if n.at_war_with_player and n.id != gs.player.current_war_target:
            continue

        # Союзник
        if n.is_ally:
            if n.relation_to_player < REL_ALLY_BREAK:
                n.is_ally = False
                gs.player.reputation = max(0, gs.player.reputation - 30)
                gs.player.mood = max(0, gs.player.mood - 2)
                gs.player.log.append(f"💔 Союз с {n.name} расторгнут (отношения упали).")
                gs.player.mail.append(f"📜 Союз с {n.name} распался.")
            else:
                tribute = ALLY_TRIBUTE
                n.gold = max(0, n.gold - tribute)
                gs.player.gold += tribute
            continue

        # Вассал
        if n.is_vassal:
            tribute = VASSAL_TRIBUTE
            n.gold = max(0, n.gold - tribute)
            gs.player.gold += tribute
            if (gs.player.army < n.army
                    and gs.tick >= n.vassal_immunity_until
                    and random.random() < 0.1):
                n.is_vassal = False
                gs.player.log.append(f"💥 ВАССАЛ ВОССТАЛ: {n.name} сбросил присягу!")
                start_war_against_player(gs, n, f"{n.name} восстал против тебя!")
            continue

        # Секта
        if n.is_sect:
            if n.at_war_with_player:
                gs.player.reputation = min(100, gs.player.reputation + 5)
                ticks_at_war = gs.tick - n.war_started_tick
                if ticks_at_war >= SECT_PEACE_DEADLINE:
                    lost = gs.player.army
                    gs.player.army = 0
                    n.at_war_with_player = False
                    gs.player.log.append(
                        f"💀 Секта покарала тебя! Вся армия ({lost}) уничтожена. Война окончена."
                    )
                    if gs.player.current_war_target == n.id:
                        advance_war_queue(gs)
                elif ticks_at_war >= 1:
                    gs.player.log.append(
                        f"🌑 Секта готовит возмездие... ({ticks_at_war}/{SECT_PEACE_DEADLINE} тиков до кары). Предложи мир!"
                    )
            continue

        # Диггеры
        if n.is_diggers:
            if n.at_war_with_player:
                continue
            if gs.player.gold > 0 and random.random() < 0.3:
                stolen = min(gs.player.gold, random.randint(5, 25))
                gs.player.gold -= stolen
                gs.player.log.append(f"⛏️ Диггеры украли {stolen} золота!")
            if gs.player.army > 0 and random.random() < 0.15:
                stolen = min(gs.player.army, random.randint(1, 3))
                gs.player.army -= stolen
                gs.player.log.append(f"⛏️ Диггеры украли {stolen} войск!")
            continue

        # Гунны
        if n.id == "huns":
            if random.random() < 0.4:
                n.army += random.randint(1, 3)
            if not n.at_war_with_player and gs.player.has_tower:
                chance = 0.05
                if n.relation_to_player < REL_COLD:
                    chance += 0.05
                if n.relation_to_player < REL_ENEMY:
                    chance += 0.10
                if n.relation_to_player > REL_FRIEND:
                    chance = 0.0
                if random.random() < chance:
                    start_war_against_player(gs, n, "Гунны напали без причины!")

        elif n.id == "varfolomey":
            n.gold += random.randint(10, 30)
            if (not n.at_war_with_player
                    and gs.player.has_tower
                    and gs.player.army > n.army * 2
                    and random.random() < 0.02
                    and n.relation_to_player < REL_FRIEND):
                start_war_against_player(gs, n, "Варфоломеева Империя испугалась твоей мощи.")
            if (n.relation_to_player >= REL_FRIEND
                    and not n.at_war_with_player
                    and random.random() < 0.05):
                potential = [x for x in gs.neighbors.values()
                             if not x.at_war_with_player
                             and x.id not in ("varfolomey", "sect")
                             and not x.is_destroyed
                             and x.relation_to_player < REL_COLD]
                if potential:
                    target = random.choice(potential)
                    gs.player.mail.append(f"📜 Друг из Варфоломеевой Империи шепчет: {target.name} что-то замышляет.")

        elif n.id == "ryazan":
            if random.random() < 0.3 and n.army > 1:
                n.army -= 1
            if (not n.at_war_with_player
                    and gs.player.current_war_target
                    and n.relation_to_player < REL_COLD
                    and random.random() < 0.08):
                start_war_against_player(gs, n, "Рязань ударила в спину!")

        # Союз
        if (not n.is_ally
                and not n.at_war_with_player
                and not n.is_vassal
                and not n.is_sect
                and n.relation_to_player >= REL_ALLY):
            form_alliance(gs, n)


def form_alliance(gs: GameState, n: Neighbor):
    n.is_ally = True
    n.ally_core_price = random.randint(ALLY_CORE_PRICE_MIN, ALLY_CORE_PRICE_MAX)
    gs.player.last_alliance_tick = gs.tick
    react(gs, "alliance")
    gs.player.log.append(
        f"🤝 {n.name} стал твоим союзником! Цена выкупа Ядра (если появится): {n.ally_core_price} золота."
    )
    gs.player.mail.append(
        f"📜 {n.name} предлагает вечный союз. Цена выкупа Ядра: {n.ally_core_price} золота."
    )


def science_bonus_percent(p: Player) -> float:
    """Бонус науки: +5% ко всему на ур. 1 (задел на ур. 2-3)."""
    if p.science_level >= 1:
        return 0.05
    return 0.0


def tick_player(gs: GameState):
    p = gs.player
    bonus = science_bonus_percent(p)
    base_income = random.randint(10, 25)
    pop_tax = int(p.population * 0.03)
    total = base_income + pop_tax
    if p.mood > 70:
        total = int(total * 1.2)
    elif p.mood < 30:
        total = int(total * 0.7)
    total = int(total * (1 + bonus))
    p.gold += total


def tick_economy(gs: GameState):
    p = gs.player
    bonus = science_bonus_percent(p)
    p.food_production = int(p.territory * 2 * (1 + bonus))
    p.food_consumption = int(p.population * 0.02)

    if p.food_sowing and gs.tick == p.food_sowing_end_tick:
        gs.player.log.append("🌾 Урожай созрел — собери его в [е] Еда.")

    p.food += p.food_production - p.food_consumption

    # --- настроение: только штрафы за события ---
    calm = True
    if p.current_war_target:
        p.mood -= 1
        calm = False
    if p.reputation < 30:
        p.mood -= 2
        calm = False

    if p.food < 0:
        p.population = max(0, int(p.population * 0.98))
        p.food = 0
        p.mood -= 5
        calm = False
        gs.player.log.append("🌾 Голод: жители мрут (-2%/тик), настроение -5.")

    # --- рост жителей: только пока еды в профицит ---
    growth = 0.0
    if p.food > 0 and p.mood > 50 and p.food_production > p.food_consumption:
        growth = 0.015 if p.mood > 70 else 0.01
        p.population = max(0, int(p.population * (1 + growth)))
        p.population_growth = round(growth * 100, 1)
        p.reputation += 3

    if p.science_level > 0:
        p.reputation += 5

    # --- пассивный рост настроения: +3 за 10 спокойных тиков ---
    if calm:
        p.mood_calm_ticks += 1
        if p.mood_calm_ticks >= 10:
            p.mood += 3
            p.mood_calm_ticks = 0
    else:
        p.mood_calm_ticks = 0

    # --- во время войны настроение падает, но не ниже 5 ---
    if p.current_war_target:
        p.mood = max(5, p.mood)

    if p.mood < 10 and not p.current_war_target and random.random() < 0.10:
        lost = int(p.population * 0.05)
        p.population -= lost
        p.gold = int(p.gold * 0.9)
        gs.player.log.append(f"🔥 БУНТ! Народ взбунтовался: жители -{lost}, золото -10%.")
        react(gs, "defeat")

    p.mood = max(0, min(100, p.mood))
    p.reputation = max(0, min(100, p.reputation))


def do_tick(gs: GameState):
    gs.tick += 1
    tick_player(gs)
    tick_core_spawn(gs)
    tick_neighbors(gs)
    tick_cherno(gs)
    tick_rumors(gs)
    tick_economy(gs)

    if gs.tick >= TOTAL_TICKS and not gs.game_over:
        gs.game_over = True
        gs.victory = False
        gs.victory_reason = "⏳ 200 ходов истекли. Ты не успел."


# ============================================================
# ВОЙНА
# ============================================================

def resolve_war_tick(gs: GameState, target_id: str, order: str):
    p = gs.player
    n = gs.neighbors.get(target_id)
    if not n or n.is_destroyed or not n.at_war_with_player:
        if p.current_war_target == target_id:
            advance_war_queue(gs)
        return

    if order == TARGET_PEACE:
        try_make_peace(gs, n)
        return

    if n.is_sect:
        p.army = max(0, p.army - random.randint(0, 1))
        gs.player.log.append("⚔️ Рейд на секту. Прогресс призыва замедлен.")
        return

    player_power = p.army * p.army_quality
    enemy_power = n.army * n.army_quality
    player_roll = player_power * random.uniform(0.8, 1.2)
    enemy_roll = enemy_power * random.uniform(0.8, 1.2)

    if player_roll > enemy_roll:
        enemy_losses = max(1, int(n.army * random.uniform(0.2, 0.4)))
        player_losses = max(0, int(p.army * random.uniform(0.05, 0.15)))
        n.army = max(0, n.army - enemy_losses)
        p.army = max(0, p.army - player_losses)
        gs.player.log.append(f"⚔️ Стычка с {n.name}: победа! Враг -{enemy_losses}, ты -{player_losses}.")

        if order == TARGET_STOLICA:
            loot = min(n.gold, random.randint(20, 60))
            n.gold -= loot
            p.gold += loot
            gs.player.log.append(f"🏛️ Разграблена столица: +{loot} золота.")
        elif order == TARGET_VAULT:
            loot = min(n.gold, random.randint(30, 80))
            n.gold -= loot
            p.gold += loot
            gs.player.log.append(f"💰 Склады разграблены: +{loot} золота.")
    else:
        player_losses = max(1, int(p.army * random.uniform(0.2, 0.4)))
        enemy_losses = max(0, int(n.army * random.uniform(0.05, 0.15)))
        p.army = max(0, p.army - player_losses)
        n.army = max(0, n.army - enemy_losses)
        gs.player.log.append(f"⚔️ Стычка с {n.name}: поражение. Ты -{player_losses}, враг -{enemy_losses}.")

    if n.army <= 0 and p.army <= 0:
        gs.player.log.append(f"♟️ Обе армии истощены. Лидеры {n.name} и твой играют в шахматы...")
        if random.random() < 0.5:
            gs.player.log.append("🏆 Ты выиграл в шахматы!")
            win_war(gs, n)
        else:
            gs.player.log.append("💀 Ты проиграл в шахматы.")
            lose_war(gs, n)
    elif n.army <= 0:
        win_war(gs, n)
    elif p.army <= 0:
        lose_war(gs, n)


def win_war(gs: GameState, n: Neighbor):
    p = gs.player
    react(gs, "victory")
    p.mood = max(0, min(100, p.mood + 10))
    p.reputation = max(0, min(100, p.reputation + 10))

    if n.is_diggers:
        n.is_destroyed = True
        n.at_war_with_player = False
        gs.player.log.append("🏆 Диггеры истреблены навсегда!")
        if p.current_war_target == n.id:
            advance_war_queue(gs)
        reset_ally_help_flags(gs)
        return

    if n.is_sect:
        repel_sect(gs, n)
        return

    n.is_vassal = True
    n.at_war_with_player = False
    n.army = min(n.army, 5)
    n.vassal_immunity_until = gs.tick + VASSAL_IMMUNITY_TICKS
    if n.has_core:
        n.has_core = False
        n.core_revealed = False
        p.has_core = True
        gs.core_owner_id = "player"
        gs.player.log.append(f"🔮 Ты забрал Ядро активации у {n.name}!")
    if n.has_tower:
        n.has_tower = False
        p.has_tower = True
        gs.player.log.append("🏰 Ты вернул Башню Времени!")
    loot = n.gold // 2
    n.gold -= loot
    p.gold += loot
    gs.player.log.append(f"🏆 ПОБЕДА над {n.name}! +{loot} золота. Он стал вассалом.")
    if p.current_war_target == n.id:
        advance_war_queue(gs)
    reset_ally_help_flags(gs)


def lose_war(gs: GameState, n: Neighbor):
    p = gs.player
    react(gs, "defeat")
    p.mood = max(0, min(100, p.mood - 15))
    p.reputation = max(0, min(100, p.reputation - 15))
    gs.player.log.append(f"💀 ПОРАЖЕНИЕ от {n.name}.")
    n.at_war_with_player = False

    if p.has_tower:
        p.has_tower = False
        n.has_tower = True
        loss = -(-p.gold * 3 // 4)
        p.gold -= loss
        n.gold += loss
        gs.player.log.append(f"🏰 Башня Времени захвачена {n.name}! Ты потерял {loss} золота.")
        queue_urgent(
            gs, "tower_stolen",
            f"🏰 СРОЧНО: {n.name} захватил Башню Времени и {loss} золота! Пошли шпиона вернуть её.",
            n.id,
        )
    else:
        gs.player.log.append("Ты никому не интересен без Башни. Ничего не потеряно.")
    if p.current_war_target == n.id:
        advance_war_queue(gs)
    reset_ally_help_flags(gs)


def repel_sect(gs: GameState, n: Neighbor):
    p = gs.player
    n.at_war_with_player = False
    n.army = max(10, n.army + 5)
    gs.player.log.append("🌑 Секта отброшена, но не уничтожена. Она восстановится.")
    if p.current_war_target == n.id:
        advance_war_queue(gs)


def try_make_peace(gs: GameState, n: Neighbor):
    if n.is_sect:
        n.at_war_with_player = False
        gs.player.log.append("🕊️ Секта приняла мир. Она возвращается к своим ритуалам.")
        if gs.player.current_war_target == n.id:
            advance_war_queue(gs)
        return

    base = 50
    base -= n.relation_to_player // 2
    if gs.player.army > n.army:
        base += 20
    elif gs.player.army < n.army:
        base -= 20
    base = max(5, min(95, base))
    if random.randint(1, 100) <= base:
        n.at_war_with_player = False
        n.relation_to_player += 10
        gs.player.log.append(f"🕊️ Мир с {n.name} заключён!")
        if gs.player.current_war_target == n.id:
            advance_war_queue(gs)
    else:
        gs.player.log.append(f"❌ {n.name} отверг мирное предложение.")


def prompt_war_order(gs: GameState):
    target_id = gs.player.current_war_target
    if not target_id:
        return
    n = gs.neighbors.get(target_id)
    if not n or n.is_destroyed:
        advance_war_queue(gs)
        return

    print("\n" + "=" * 60)
    print(f"⚔️ ВОЙНА с {n.name}")
    print(f"Твоя армия: {gs.player.army} (кач. {gs.player.army_quality}) | "
          f"Враг: {n.army} (кач. {n.army_quality})")

    if gs.player.pending_wars:
        names = [gs.neighbors[x].name for x in gs.player.pending_wars if x in gs.neighbors]
        print(f"📋 В очереди: {', '.join(names)}")

    if n.is_sect:
        ticks_at_war = gs.tick - n.war_started_tick
        left = SECT_PEACE_DEADLINE - ticks_at_war
        print(f"🌑 До кары секты: {max(0, left)} тиков. Предложи мир — или потеряешь армию!")
        print("  1. Провести рейд")
        print("  2. 🕊️ Предложить мир")
        ans = input("> ").strip()
        if ans == "2":
            resolve_war_tick(gs, target_id, TARGET_PEACE)
        else:
            resolve_war_tick(gs, target_id, TARGET_GARRISON)
        pause()
        return

    print("Куда бьём? (Enter — повторить прошлый приказ)")
    print("  1. 🏛️ Столица (золото, сильный гарнизон)")
    print("  2. ⚔️ Гарнизон (ослабить армию)")
    print("  3. 💰 Склады (много золота)")
    print("  4. 🕊️ Предложить мир")
    print("=" * 60)

    ans = input("> ").strip()
    mapping = {
        "1": TARGET_STOLICA,
        "2": TARGET_GARRISON,
        "3": TARGET_VAULT,
        "4": TARGET_PEACE,
        "": gs.player.last_war_order,
    }
    order = mapping.get(ans, gs.player.last_war_order)
    gs.player.last_war_order = order
    resolve_war_tick(gs, target_id, order)
    pause()


# ============================================================
# ДЕЙСТВИЯ ИГРОКА
# ============================================================

def action_taxes(gs: GameState):
    p = gs.player
    bonus = science_bonus_percent(p)
    income = random.randint(20, 50)
    income = int(income * (1+bonus))
    p.gold += income
    p.tax_collect_count += 1
    p.mood = max(0, p.mood - 2)
    p.mood_calm_ticks = 0
    react(gs, "taxes")
    print(f"💰 Собраны налоги: +{income} золота.")
    pause()


def action_army(gs: GameState):
    cost = 30
    if gs.player.gold < cost:
        print(f"❌ Не хватает золота (нужно {cost}).")
        pause()
        return
    gs.player.gold -= cost
    gs.player.army += 1
    print(f"⚔️ Нанят 1 воин. Армия: {gs.player.army}. Золото: {gs.player.gold}.")
    pause()


def action_interact(gs: GameState):
    print("\nС кем взаимодействовать?")
    ids = [nid for nid, n in gs.neighbors.items() if not n.is_destroyed]
    if not ids:
        print("  (никого не осталось)")
        pause()
        return
    for i, nid in enumerate(ids, 1):
        n = gs.neighbors[nid]
        queued = " 📋в очереди" if nid in gs.player.pending_wars else ""
        print(f"  {i}. {n.name} — {n.short_status()}{queued}")
    print("  0. Назад")
    try:
        choice = int(input("> ").strip())
    except ValueError:
        print("❌ Некорректный ввод.")
        pause()
        return
    if choice == 0 or choice > len(ids):
        return
    n = gs.neighbors[ids[choice - 1]]

    print(f"\nВзаимодействие с {n.name}:")
    print("  1. Поговорить")
    if not n.is_diggers:
        print("  2. Торговать")
    if n.at_war_with_player:
        print("  3. 🕊️ Предложить мир")
    else:
        print("  3. Объявить войну")
    if not n.is_diggers:
        print("  4. Подкупить посла")
    can_buy_core = n.has_core and not n.ruler.knows_core
    can_persuade = n.has_core and not n.ruler.knows_core and n.relation_to_player >= REL_WARM
    can_buy_from_ally = n.is_ally and n.has_core and n.ally_core_price > 0
    if can_buy_core:
        print("  5. Выкупить странность (Ядро)")
    if can_persuade:
        print("  6. Уговорить отдать странность")
    if can_buy_from_ally:
        print(f"  7. Выкупить Ядро у союзника ({n.ally_core_price} золота)")
    print("  0. Назад")

    try:
        sub = int(input("> ").strip())
    except ValueError:
        print("❌ Некорректный ввод.")
        pause()
        return

    if sub == 1:
        print(f"🗣️ Ты говоришь с {n.name}. Отношения улучшены.")
        n.relation_to_player += 2 + int(2 * science_bonus_percent(gs.player))
        pause()
    elif sub == 2 and not n.is_diggers:
        if gs.player.gold >= 50:
            gs.player.gold -= 50
            n.gold += 50
            n.relation_to_player += 5
            react(gs, "trade")
            print("🤝 Ты заплатил 50 золота. Отношения улучшены.")
        else:
            print("❌ Не хватает золота.")
        pause()
    elif sub == 3:
        if n.at_war_with_player:
            try_make_peace(gs, n)
            pause()
            return
        if n.is_vassal:
            print("❌ Это твой вассал.")
            pause()
            return
        if n.is_ally:
            print("❌ Это твой союзник.")
            pause()
            return
        if n.is_diggers and gs.player.army >= DIGGER_MASSACRE_ARMY:
            print(f"⚔️ Твоя армия ({gs.player.army}) подавляющая. Диггеры складывают головы без боя!")
            n.is_destroyed = True
            gs.player.log.append("🏆 Диггеры истреблены без боя — они сложили головы перед мощью.")
            pause()
            return
        print(f"⚔️ Ты объявил войну {n.name}.")
        n.relation_to_player -= 30
        if gs.player.army > n.army * 2:
            gs.player.reputation = max(0, gs.player.reputation - 15)
            gs.player.log.append("📉 Нападение на слабого: репутация -15.")
        react(gs, "war_declared")
        start_war_against_player(gs, n, f"Ты объявил войну {n.name}.")
        pause()
    elif sub == 4 and not n.is_diggers:
        if gs.player.gold >= 30:
            gs.player.gold -= 30
            print(f"🕵️ Ты подкупил посла {n.name}. Отношения улучшены.")
            n.relation_to_player += 10 + int(10 * science_bonus_percent(gs.player))
        else:
            print("❌ Не хватает золота.")
        pause()
    elif sub == 5 and can_buy_core:
        try_buy_core(gs, n)
    elif sub == 6 and can_persuade:
        try_persuade_core(gs, n)
    elif sub == 7 and can_buy_from_ally:
        try_buy_core_from_ally(gs, n)
    else:
        pass


def try_buy_core(gs: GameState, n: Neighbor):
    base_price = 200 + max(0, -n.relation_to_player)
    base_price = min(600, base_price)
    print(f"\n💰 Выкуп «странности» у {n.name}")
    print(f"Цена: ~{base_price} золота (отношения: {n.relation_to_player})")
    if gs.player.gold < base_price:
        print(f"❌ Не хватает золота (у тебя {gs.player.gold}).")
        pause()
        return
    chance = max(5, min(95, 50 + n.relation_to_player // 2))
    print(f"Шанс согласия: ~{chance}%")
    ans = input("Попытаться? (д/н): ").strip().lower()
    if ans not in ("д", "да", "y", "yes"):
        return
    if random.randint(1, 100) <= chance:
        gs.player.gold -= base_price
        n.gold += base_price
        n.has_core = False
        n.core_revealed = False
        gs.player.has_core = True
        gs.core_owner_id = "player"
        print(f"🔮 Успех! Ты выкупил Ядро за {base_price} золота.")
        gs.player.log.append(f"🔮 Выкуплено Ядро у {n.name} за {base_price}.")
    else:
        print(f"❌ {n.name} отказался продавать «странность».")
    pause()


def try_persuade_core(gs: GameState, n: Neighbor):
    print(f"\n🤝 Уговор {n.name}")
    print(f"У него есть «странность», о которой он не знает. Отношения: {n.relation_to_player}")
    chance = max(5, min(90, n.relation_to_player - 40))
    print(f"Шанс убедить: ~{chance}%")
    ans = input("Попытаться? (д/н): ").strip().lower()
    if ans not in ("д", "да", "y", "yes"):
        return
    if random.randint(1, 100) <= chance:
        n.has_core = False
        n.core_revealed = False
        gs.player.has_core = True
        gs.core_owner_id = "player"
        n.relation_to_player -= 20
        print(f"🔮 Успех! {n.name} отдал «странность» даром. Отношения -20.")
        gs.player.log.append(f"🔮 Уговор сработал: {n.name} отдал Ядро.")
    else:
        n.relation_to_player -= 10
        print(f"❌ {n.name} не поддался уговорам. Отношения -10.")
    pause()


def try_buy_core_from_ally(gs: GameState, n: Neighbor):
    price = n.ally_core_price
    print(f"\n💰 Выкуп Ядра у союзника {n.name}")
    print(f"Цена (фиксирована при союзе): {price} золота")
    if gs.player.gold < price:
        print(f"❌ Не хватает золота (у тебя {gs.player.gold}).")
        pause()
        return
    ans = input("Выкупить? (д/н): ").strip().lower()
    if ans not in ("д", "да", "y", "yes"):
        return
    gs.player.gold -= price
    n.gold += price
    n.has_core = False
    n.core_revealed = False
    gs.player.has_core = True
    gs.core_owner_id = "player"
    print(f"🔮 Ты выкупил Ядро у союзника за {price} золота!")
    gs.player.log.append(f"🔮 Ядро выкуплено у союзника {n.name} за {price}.")


def action_mail(gs: GameState):
    print("\n📬 ПИСЬМА:")
    if not gs.player.mail:
        print("  (пусто)")
    else:
        for m in gs.player.mail:
            print(f"  • {m}")
    gs.player.mail.clear()
    pause()


def action_log(gs: GameState):
    print("\n📜 ЛОГ СОБЫТИЙ (последние 15):")
    for entry in gs.player.log[-15:]:
        print(f"  • {entry}")
    pause()


def action_activate_tower(gs: GameState):
    if not gs.player.has_core:
        print("❌ У тебя нет Ядра.")
        pause()
        return
    if not gs.player.has_tower:
        print("❌ Башни нет на твоей территории. Сначала верни её.")
        pause()
        return
    gs.player.tower_activated = True
    react(gs, "tower_activated")
    print("🔮 Башня Времени активирована! Теперь ты можешь бросить вызов Чернобогу.")
    pause()


def action_science(gs: GameState):
    p = gs.player
    print("\n🎓 НАУКА")
    print(f"Уровень: {p.science_level}")
    if p.science_level == 0:
        print("Эффект: нет")
        print(f"Следующий уровень: {p.science_cost} золота")
        print("Даёт: +5% ко всему")
        if p.gold < p.science_cost:
            print("❌ Не хватает золота.")
            pause()
            return
        try:
            ans = input("Исследовать? (д/н): ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return
        if ans not in ("д", "да", "y", "yes"):
            return
        p.gold -= p.science_cost
        p.science_level = 1
        p.science_cost = 750
        print("🎓 Уровень науки повышен до 1! (+5% ко всему)")
    else:
        print("Эффект: +5% ко всему")
        print("Дальнейшие уровни (2-3) запланированы в Волне 3.")
    pause()


def action_food(gs: GameState):
    p = gs.player
    bonus = science_bonus_percent(p)
    prod = int(p.territory * 2 * (1 + bonus))
    cons = int(p.population * 0.02)
    print("\n🌾 ЕДА")
    print(f"Запас: {p.food}")
    print(f"Производство: +{prod}/тик")
    print(f"Потребление: -{cons}/тик")
    print(f"Итог: {prod - cons}/тик")
    print("  1. Посеять (100 золота → +200 еды через 3 тика)")
    print("  2. Собрать урожай (если созрел)")
    print("  3. Продать 100 еды (→ +50 золота)")
    print("  4. Купить 100 еды (→ -60 золота)")
    print("  0. Назад")
    try:
        c = input("> ").strip()
    except (EOFError, KeyboardInterrupt):
        return
    if c == "1":
        if p.food_sowing:
            print("❌ Уже что-то посеяно.")
        elif p.gold < 100:
            print("❌ Не хватает золота.")
        else:
            p.gold -= 100
            p.food_sowing = True
            p.food_sowing_end_tick = gs.tick + 3
            print("🌱 Посеяно. Урожай через 3 тика.")
    elif c == "2":
        if not p.food_sowing:
            print("❌ Нечего собирать.")
        elif gs.tick < p.food_sowing_end_tick:
            print(f"⏳ Урожай созреет через {p.food_sowing_end_tick - gs.tick} тика.")
        else:
            p.food += 200
            p.food_sowing = False
            print("🌾 Собрано +200 еды.")
    elif c == "3":
        if p.food < 100:
            print("❌ Недостаточно еды.")
        else:
            p.food -= 100
            p.gold += 50
            print("💰 Продано 100 еды за 50 золота.")
    elif c == "4":
        if p.gold < 60:
            print("❌ Не хватает золота.")
        else:
            p.gold -= 60
            p.food += 100
            print("🌾 Куплено 100 еды за 60 золота.")
    elif c == "0":
        return
    pause()


def action_spies(gs: GameState):
    print(f"\n🕵️ ШПИОНЫ (у тебя: {gs.player.spies})")
    print("  1. Нанять шпиона (50 золота)")
    print("  2. Разведать про Ядро")
    print("  3. Выкрасть Башню")
    print("  4. Подслушать планы")
    print("  0. Назад")
    try:
        choice = int(input("> ").strip())
    except ValueError:
        pause()
        return

    if choice == 0:
        return
    elif choice == 1:
        if gs.player.gold >= SPY_COST:
            gs.player.gold -= SPY_COST
            gs.player.spies += 1
            print(f"🕵️ Нанят шпион. Всего: {gs.player.spies}.")
        else:
            print("❌ Не хватает золота.")
        pause()
        return
    elif choice in (2, 3, 4):
        if gs.player.spies <= 0:
            print("❌ У тебя нет шпионов.")
            pause()
            return

        if choice == 3:
            targets = [n for n in gs.neighbors.values()
                       if not n.is_destroyed and n.has_tower]
            if not targets:
                print("🕵️ Ни у кого нет Башни. Красть нечего.")
                pause()
                return
        else:
            targets = [n for n in gs.neighbors.values()
                       if not n.is_destroyed and not n.is_sect]

        print("\nВ какую страну отправить?")
        for i, n in enumerate(targets, 1):
            print(f"  {i}. {n.name}")
        print("  0. Назад")
        try:
            t = int(input("> ").strip())
        except ValueError:
            pause()
            return
        if t == 0 or t > len(targets):
            return
        target = targets[t - 1]

        if choice == 2:
            gs.player.spies -= 1
            spy_recon(gs, target)
        elif choice == 3:
            if gs.player.spies < 2:
                print("❌ Для кражи Башни нужно 2 шпиона.")
                pause()
                return
            gs.player.spies -= 2
            spy_steal_tower(gs, target)
        elif choice == 4:
            gs.player.spies -= 1
            spy_listen(gs, target)
        pause()


def spy_recon(gs: GameState, n: Neighbor):
    if n.has_core:
        n.core_revealed = True
        if n.ruler.knows_core:
            print(f"🔮 Шпион донёс: у {n.name} ТОЧНО есть Ядро. Правитель знает.")
            gs.player.log.append(f"🕵️ Разведка: {n.name} — Ядро (знает).")
        else:
            print(f"🔮 Шпион донёс: у {n.name} есть Ядро, но правитель НЕ знает.")
            gs.player.log.append(f"🕵️ Разведка: {n.name} — Ядро (НЕ знает).")
    else:
        n.core_revealed = False
        print(f"🕵️ Шпион донёс: у {n.name} Ядра нет.")
        gs.player.log.append(f"🕵️ Разведка: {n.name} — нет Ядра.")
    n.intel_gold = n.gold
    n.intel_food = n.food
    n.intel_expires_tick = gs.tick + 1
    gs.player.log.append(f"🕵️ Разведка: {n.name} — золото {n.intel_gold}, еда {n.intel_food}")


def spy_steal_tower(gs: GameState, n: Neighbor):
    if not n.has_tower:
        print(f"🕵️ У {n.name} нет Башни.")
        return
    roll = random.random()
    if roll < 0.15 * (1 + science_bonus_percent(gs.player)):
        n.has_tower = False
        gs.player.has_tower = True
        print("🎉 Шпионы вернули Башню Времени!")
        gs.player.log.append(f"🕵️ Башня возвращена от {n.name}!")
    elif roll < 0.55:
        print("❌ Провал кражи Башни, шпионы уцелели.")
    else:
        print(f"💥 Шпионы раскрыты! {n.name} в ярости.")
        gs.player.log.append(f"🕵️ Шпионы раскрыты у {n.name}!")
        n.relation_to_player -= 40
        if not n.at_war_with_player and random.random() < 0.5:
            start_war_against_player(gs, n, f"{n.name} объявил войну за шпионаж!")


def spy_listen(gs: GameState, n: Neighbor):
    if n.at_war_with_player:
        print(f"🕵️ {n.name} воюет с тобой.")
        return
    if n.relation_to_player < REL_COLD:
        print(f"🕵️ {n.name} замышляет против тебя.")
        gs.player.log.append(f"🕵️ {n.name} замышляет атаку.")
    else:
        print(f"🕵️ {n.name} пока не замышляет ничего против тебя.")


def action_occult(gs: GameState):
    cd_left = OCCULT_COOLDOWN - (gs.tick - gs.player.occult_last_used_tick)
    print(f"\n👁️ ОККУЛЬТИЗМ")
    print(f"Отрядов: {gs.player.occult_army}")
    if cd_left > 0:
        print(f"Кулдаун: ещё {cd_left} тиков")
    else:
        print("Готово к применению.")
    print("  1. Нанять отряд (150 золота)")
    print("  2. Применить оккультную атаку (-9.5 прогресса)")
    print("  0. Назад")
    try:
        choice = int(input("> ").strip())
    except ValueError:
        pause()
        return

    if choice == 1:
        if gs.player.gold >= OCCULT_COST:
            gs.player.gold -= OCCULT_COST
            gs.player.occult_army += 1
            print(f"👁️ Нанят отряд оккультистов. Всего: {gs.player.occult_army}.")
        else:
            print("❌ Не хватает золота.")
        pause()
    elif choice == 2:
        if gs.player.occult_army <= 0:
            print("❌ Нет отрядов.")
            pause()
            return
        if cd_left > 0:
            print(f"❌ Ещё не готово ({cd_left} тиков).")
            pause()
            return
        if gs.cherno_phase_idx == 0:
            print("❌ Чернобог ещё не начал просыпаться.")
            pause()
            return
        gs.cherno_phase_tick = max(0.0, gs.cherno_phase_tick - OCCULT_ROLLBACK * (1 + science_bonus_percent(gs.player)))
        gs.player.occult_last_used_tick = gs.tick
        rb = OCCULT_ROLLBACK * (1 + science_bonus_percent(gs.player))
        print(f"👁️ Оккультная атака! Прогресс отброшен на {rb:.1f}.")
        gs.player.log.append(f"👁️ Оккультная атака: -{rb:.1f} прогресса.")
        pause()
    else:
        pass


def handle_urgent_letters(gs: GameState):
    if not gs.pending_letters:
        return
    letter = gs.pending_letters.pop(0)

    print("\n" + "!" * 60)
    print(letter.text)
    print("!" * 60)
    print("  [Enter — продолжить]")
    try:
        input()
    except (EOFError, KeyboardInterrupt):
        pass


# ============================================================
# UI
# ============================================================

def render(gs: GameState):
    print("\033[2J\033[H", end="")

    elapsed = time.time() - gs.last_tick_time
    seconds_left = max(0, int(TICK_SECONDS - elapsed))

    print("=" * 60)
    print(f" ТАЙМЛЕНД | Ход {gs.tick}/{TOTAL_TICKS} | ⏱ след. тик через ~{seconds_left} сек")
    print("-" * 60)
    p = gs.player
    print(f"💰 Золото: {p.gold} | ⚔️ Армия: {p.army} (кач. {p.army_quality}) | 🎓 Наука: ур. {p.science_level}")
    print(f"🌾 Еда: {p.food} | 👥 Жители: {p.population} | 🏞️ Земля: {p.territory}")
    print(f"🕵️ Шпионы: {p.spies} | 👁️ Оккульт: {p.occult_army} | 📉 Репутация: {p.reputation}")
    tower_state = "активна" if p.tower_activated else ("дремлет" if p.has_tower else "🏴утеряна")
    core_state = "у тебя" if p.has_core else "неизвестно"
    print(f"😊 Настроение: {p.mood}% | 🏰 Башня: {tower_state} | 🔮 Ядро: {core_state}")

    if p.current_war_target:
        n = gs.neighbors.get(p.current_war_target)
        if n:
            print(f"⚔️ ВОЙНА с {n.name}")
    if p.pending_wars:
        names = [gs.neighbors[x].name for x in p.pending_wars if x in gs.neighbors]
        print(f"📋 В очереди войн: {', '.join(names)}")

    if gs.core_spawned:
        name, dur = CHERNOBOG_PHASES[gs.cherno_phase_idx]
        if gs.cherno_accelerated:
            print(f"🌑 Чернобог: {name} ({gs.cherno_phase_tick:.1f}/{dur}) — УСКОРЕН ×2 ⚠️")
        else:
            print(f"🌑 Чернобог: {name} ({gs.cherno_phase_tick:.1f}/{dur})")

    if p.last_rumor:
        print(f"\033[3m🗣️ Слух: «{p.last_rumor}»\033[0m")

    print("-" * 60)
    print("Соседи:")
    for n in gs.neighbors.values():
        rel = f"[{n.relation_to_player:+d}]" if not n.is_destroyed else ""
        print(f"  • {n.name:26s} {n.short_status()} {rel}")

    print("-" * 60)
    print("📜 Последние события:")
    for entry in p.log[-6:]:
        print(f"  • {entry}")

    print("-" * 60)
    print("[1] Налоги  [2] Армия      [3] Взаимодействие  [4] Почта")
    print("[5] Лог     [6] Башня       [7] Шпионы          [8] Оккультизм")
    print("[9] Наука   [е] Еда        [с] Статус           [0] Выход")
    print("=" * 60)


# ============================================================
# ФОНОВЫЙ ТИК + ГЛАВНЫЙ ЦИКЛ
# ============================================================

class Game:
    def __init__(self):
        self.gs = create_world()
        self.gs.core_spawn_tick = random.randint(CORE_SPAWN_MIN, CORE_SPAWN_MAX)
        self.gs.last_tick_time = time.time()
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.war_prompt_pending = False
        self.urgent_pending = False

    def tick_loop(self):
        while not self.stop_event.is_set():
            time.sleep(1)
            with self.lock:
                if self.gs.game_over:
                    self.stop_event.set()
                    return
                if time.time() - self.gs.last_tick_time >= TICK_SECONDS:
                    do_tick(self.gs)
                    self.gs.last_tick_time = time.time()
                    if self.gs.player.current_war_target:
                        self.war_prompt_pending = True
                    if self.gs.pending_letters:
                        self.urgent_pending = True
                    if not self.gs.game_over:
                        render(self.gs)

    def run(self):
        tick_thread = threading.Thread(target=self.tick_loop, daemon=True)
        tick_thread.start()

        with self.lock:
            render(self.gs)

        while not self.stop_event.is_set():
            if self.urgent_pending:
                self.urgent_pending = False
                while True:
                    with self.lock:
                        if not self.gs.pending_letters:
                            break
                        render(self.gs)
                        handle_urgent_letters(self.gs)
                    with self.lock:
                        render(self.gs)
                continue

            if self.war_prompt_pending:
                self.war_prompt_pending = False
                with self.lock:
                    if self.gs.player.current_war_target:
                        render(self.gs)
                        prompt_war_order(self.gs)
                        render(self.gs)
                continue

            try:
                ans = input("> ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print("\nВыход.")
                self.stop_event.set()
                break

            with self.lock:
                gs = self.gs

                if ans in ("0", "выход", "exit", "quit"):
                    self.stop_event.set()
                    break

                if ans in ("с", "статус", "status"):
                    pass
                elif ans == "1":
                    action_taxes(gs)
                elif ans == "2":
                    action_army(gs)
                elif ans == "3":
                    action_interact(gs)
                elif ans == "4":
                    action_mail(gs)
                elif ans == "5":
                    action_log(gs)
                elif ans == "6":
                    action_activate_tower(gs)
                elif ans == "7":
                    action_spies(gs)
                elif ans == "8":
                    action_occult(gs)
                elif ans == "9":
                    action_science(gs)
                elif ans == "е" or ans == "e":
                    action_food(gs)
                elif ans == "":
                    continue
                else:
                    print("❓ Неизвестная команда.")
                    pause()

                if not gs.game_over:
                    render(gs)
                else:
                    self.stop_event.set()
                    break

        with self.lock:
            gs = self.gs
            print("\n" + "=" * 60)
            if gs.game_over:
                if gs.victory:
                    print(f"🏆 ПОБЕДА! {gs.victory_reason}")
                else:
                    print(f"💀 ПОРАЖЕНИЕ. {gs.victory_reason}")
            else:
                print("Игра завершена.")
            print("=" * 60)


if __name__ == "__main__":
    Game().run()