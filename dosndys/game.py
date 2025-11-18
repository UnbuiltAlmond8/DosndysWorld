import shutil
import random
import time
import os
import json
import math

try:
    import keyboard
except ImportError:
    raise ModuleNotFoundError("keyboard module not installed, please run 'pip install keyboard'")

from collections import Counter
from typing import Any

with open("./global.json", "r") as f:
    try:
        settings: dict[str, dict] = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        raise ValueError("global.json either does not exist or does not conform to valid JSON")

try:
    coins_conf: dict[str, int] = settings["coins"]
    skillcheck_conf: dict[str, int] = settings["skillcheck"]
    onmapload_conf: dict[str, bool] = settings["onmapload"]
    moveset: dict[str, str] = settings["moveset"]
except KeyError:
    raise ValueError("global.json does not conform to settings schema")

def clear() -> None:
    os.system('cls') if os.name == "nt" else os.system('clear')
    print()

def checkType(types: list, *items: Any) -> bool:
    return types == [type(i) for i in items]

# --- BEGIN CONSTANTS ---
try:
    coins_until_end: int = coins_conf["coins_until_end"]
    MINIMUM_LEVEL_FOR_COIN_REQ_INCREASE: int = coins_conf["MINIMUM_LEVEL_FOR_COIN_REQ_INCREASE"]
    INCREASE_ONLY_WHEN_LEVEL_MODULO_IS_ZERO: int = coins_conf["INCREASE_ONLY_WHEN_LEVEL_MODULO_IS_ZERO"]
    AMOUNT_TO_INCREASE_BY: int = coins_conf["AMOUNT_TO_INCREASE_BY"]

    SKILL_CHECK_MARKER_SIZE: int = skillcheck_conf["SKILL_CHECK_MARKER_SIZE"]
    SKILL_CHECK_SIZE: int = skillcheck_conf["SKILL_CHECK_SIZE"]
    SKILL_CHECK_CENTER_RANGE: int = skillcheck_conf["SKILL_CHECK_CENTER_RANGE"]
    SKILL_CHECK_SPEED: int = skillcheck_conf["SKILL_CHECK_SPEED"]
    
    MOVESET: list[str] = [moveset["UP"], moveset["LEFT"], moveset["DOWN"], moveset["RIGHT"], moveset["SKILLCHECK"]]

    USE_RANDOM_SPAWN_POINT: bool = onmapload_conf["USE_RANDOM_SPAWN_POINT"]
except KeyError:
    raise ValueError("global.json does not conform to settings schema")

# Type checking
assert checkType([int, int, int], coins_until_end, MINIMUM_LEVEL_FOR_COIN_REQ_INCREASE, AMOUNT_TO_INCREASE_BY), \
    "global.json does not conform to settings schema"
assert checkType([int, int, int, int], SKILL_CHECK_MARKER_SIZE, SKILL_CHECK_SIZE, SKILL_CHECK_CENTER_RANGE, SKILL_CHECK_SPEED), \
    "global.json does not conform to settings schema"
assert set(type(i) for i in MOVESET) == set([str]), "global.json does not conform to settings schema"
assert checkType([bool], USE_RANDOM_SPAWN_POINT), "global.json does not conform to settings schema"

# --- BEGIN ACTUAL GAME ---
def setCommonLineLength(map: str) -> None:
    global common_line_length_from_map

    map_lines: list[str] = map.splitlines()
    map_line_lengths: list = [len(l) for l in map_lines]
    common_length: list = list(set(map_line_lengths))

    assert (sorted(set(map)) == ['\n', ' ', '#', 'E', 'O', 'U'] and \
           Counter(map).get("O") == 1 and \
           Counter(map).get("U") == 1 and \
           Counter(map).get("E") == 3), "Invalid map"
    assert "EEE" in map, "Invalid map"
    assert len(common_length) == 2 and common_length[0] == 0, "Invalid map"
    assert len(MOVESET) == 5, "Amount of keys in moveset must be exactly 5"

    common_line_length_from_map = common_length[1]

def skillcheck() -> int:
    global to_print, _map
    marker_position: int = random.randint(0, SKILL_CHECK_SIZE)
    current_position: int = 0
    print()
    print(to_print[:-3]
        .replace("#", "\x1b[38;2;0;0;255m■\x1b[0m")
        .replace("P", "\x1b[38;2;0;255;0m■\x1b[0m")
        .replace("O", "\x1b[38;2;255;255;0m■\x1b[0m")
        .replace("U", " "), flush=True)
    print(' ' * marker_position + ('\x1b[38;2;255;255;0m▄\x1b[0m' * SKILL_CHECK_MARKER_SIZE))
    for _ in range(SKILL_CHECK_SIZE + SKILL_CHECK_MARKER_SIZE):
        print("\x1b[38;2;255;255;255m▀\x1b[0m", end='', flush=True)
        current_position += 1
        progress: int = -(marker_position - current_position)
        if progress <= SKILL_CHECK_MARKER_SIZE and progress > 0:
            marker_midpoint: float = SKILL_CHECK_MARKER_SIZE / 2
            in_range_of_midpoint = (
                progress > marker_midpoint - SKILL_CHECK_CENTER_RANGE and \
                progress < marker_midpoint + SKILL_CHECK_CENTER_RANGE + 1
            )
            if keyboard.is_pressed(MOVESET[4]):
                clear()
                return 1 + in_range_of_midpoint
        elif keyboard.is_pressed(MOVESET[4]):
            if coins == 0:
                clear()
                print("Game over! You ran out of coins.")
                exit()
            else:
                print()
                print()
            return -1
        time.sleep(1 / SKILL_CHECK_SPEED)
    if coins == 0:
        clear()
        print("Game over! You ran out of coins.")
        exit()
    clear()
    return -1

def insert_coin() -> None:
    global _map, coins, failed_skill_check, has_just_did_skill_check
    gain: int = skillcheck()
    coins += gain
    _map = _map.replace("O", " ")
    space_indexes: list = [i for i, c in enumerate(_map) if c == ' ']
    if space_indexes:
        random_index: int = random.choice(space_indexes)
        _map = _map[:random_index] + 'O' + _map[random_index + 1:]
    if gain == -1:
        failed_skill_check = True
    has_just_did_skill_check = True

def insert_spawn_point() -> None:
    global _map
    _map = _map.replace("U", " ")
    space_indexes: list = [i for i, c in enumerate(_map) if c == ' ']
    if space_indexes:
        random_index: int = random.choice(space_indexes)
        _map = _map[:random_index] + 'U' + _map[random_index + 1:]

def move_player(state, player_char) -> str:
    global coins, _map, common_padding, has_gone_left, has_gone_down, has_gone_up, \
           has_gone_right, move_offset_h, move_offset_v, to_print, has_just_did_skill_check, \
           attempted_to_go_outside, request_map_update, attempted_to_walk_into_wall
    chars: list = list(state[common_padding:])
    position: int = chars.index('U') \
        + move_offset_h \
        - move_offset_v * (common_padding + common_line_length_from_map + 1)
    if position < 0 or position > len(chars):
        move_offset_h = 0
        move_offset_v = 0
        has_gone_left = False
        has_gone_up = False
        has_gone_down = False
        has_gone_right = False
        attempted_to_go_outside = True
        return move_player(state, player_char)
    elif chars[position] == "#":
        if has_gone_left:
            move_offset_h += 1
        elif has_gone_down:
            move_offset_v += 1
        elif has_gone_up:
            move_offset_v -= 1
        elif has_gone_right:
            move_offset_h -= 1
        attempted_to_walk_into_wall = True
        return move_player(state, player_char)
    elif chars[position] == "O":
        insert_coin()
    elif chars[position] == "E":
        if coins >= coins_until_end:
            move_offset_v = 0
            move_offset_h = 0
            request_map_update = 1
        else:
            if has_gone_left:
                move_offset_h += 1
            elif has_gone_down:
                move_offset_v += 1
            elif has_gone_up:
                move_offset_v -= 1
            elif has_gone_right:
                move_offset_h -= 1
            attempted_to_walk_into_wall = True
            return move_player(state, player_char)
    chars[position] = player_char
    return state[:common_padding] + ''.join(chars)

def loop() -> int:
    global common_padding, has_gone_left, has_gone_down, has_gone_up, has_gone_right, \
           move_offset_h, move_offset_v, to_print, attempted_to_go_outside, failed_skill_check, \
           has_just_did_skill_check, debug, _map, request_map_update, coins, level, \
           attempted_to_walk_into_wall

    request_map_update = 0
        
    setCommonLineLength(_map)

    terminal = shutil.get_terminal_size()

    lines: list = _map.splitlines()

    padding = lambda line: round(terminal.columns / 2) - round(len(line) / 2)
    map_offset_v: int = math.floor(terminal.lines / 2) - math.floor(len(lines) / 2)

    to_print = '\n' * (map_offset_v)
    for line in lines:
        common_padding = padding(line)
        to_print += (' ' * common_padding) + line + '\n'
    to_print += '\n' * (map_offset_v)

    to_print = move_player(to_print, "P")

    # Optimization: Do not print at all upon attempting to walk into wall
    if not attempted_to_walk_into_wall:
        if not has_just_did_skill_check:
            print()
        print(to_print[:-2]
            .replace("#", "\x1b[38;2;0;0;255m■\x1b[0m")
            .replace("P", "\x1b[38;2;0;255;0m■\x1b[0m")
            .replace("O", "\x1b[38;2;255;255;0m■\x1b[0m")
            .replace("U", " "), end='', flush=True)

        stats: str = f"Coins: \x1b[38;2;255;255;0m{coins}\x1b[0m"
        stats += f"/{coins_until_end} | Level: {level}"

        if attempted_to_go_outside and not debug:
            stats +=  " | \x1b[38;2;255;0;0mCheating detected, you have been placed back in the map!\x1b[0m"
        elif debug:
            stats += f" | X Position: {move_offset_h} | Y Position: {move_offset_v} | Terminal: {terminal}"

        if failed_skill_check:
            stats += f" | \x1b[38;2;255;0;0mThe machine took away your coin because you messed it up!\x1b[0m"

        print(stats)

    attempted_to_walk_into_wall = False
    has_just_did_skill_check = False
    failed_skill_check = False
    attempted_to_go_outside = False

    while 1:
        event: keyboard._keyboard_event.KeyboardEvent = keyboard.read_event()
        if event.event_type == keyboard.KEY_DOWN:
            k = keyboard.is_pressed
            if True in [
                k(MOVESET[0]),
                k(MOVESET[1]),
                k(MOVESET[2]),
                k(MOVESET[3])
            ]:
                break
            
    if keyboard.is_pressed(MOVESET[1]):
        has_gone_left = True
        has_gone_up = False
        has_gone_down = False
        has_gone_right = False
        move_offset_h -= 1 # pyright: ignore[reportOperatorIssue]
    elif keyboard.is_pressed(MOVESET[3]):
        has_gone_left = False
        has_gone_up = False
        has_gone_down = False
        has_gone_right = True
        move_offset_h += 1 # pyright: ignore[reportOperatorIssue]
    elif keyboard.is_pressed(MOVESET[0]):
        has_gone_left = False
        has_gone_up = True
        has_gone_down = False
        has_gone_right = False
        move_offset_v += 1 # pyright: ignore[reportOperatorIssue]
    elif keyboard.is_pressed(MOVESET[2]):
        has_gone_left = False
        has_gone_up = False
        has_gone_down = True
        has_gone_right = False
        move_offset_v -= 1 # pyright: ignore[reportOperatorIssue]
    return request_map_update

# Yes I made this ASCII art entirely by myself
print("""
DDDDD    OOOOO    SSSSS  NN    N  DDDDD   YY   YY  ''   SSSSS
D   DD  OO   OO  S       N N   N  D   DD   YY YY   ''  S     
D    D  O     O   SSSS   N  N  N  D    D    YYY         SSSS 
D   DD  OO   OO       S  N   N N  D   DD     Y              S
DDDDD    OOOOO   SSSSS   N    NN  DDDDD      Y         SSSSS
W     W     W   OOOOO   RRRRR   L       DDDDD
W    W W    W  OO   OO  R    R  L       D   DD
W   W   W   W  O     O  RRRRR   L       D    D
 W W     W W   OO   OO  R   R   L       D   DD
  W       W     OOOOO   R    R  LLLLLL  DDDDD
""")

print("""
Made by UnbuiltAlmond8
For advanced users, see ./DOCS.md for information on customizing
the game.
""")

print("This is a simple game where you try to collect random coins\n"
      "to get higher scores. To get coins, you need to perform a\n"
      "skill check by pressing Space when the bar is within the\n"
      "marker. If unsuccessful, a coin is deducted.\n\n"
      "Once you get enough coins, you can enter the elevator to go to\n"
      "the next level.\n\n"
      "The game ends when your coins become in debt.\n\n"
     f"Move using the {', '.join(MOVESET[:-2]).upper()} and {MOVESET[-2].upper()} keys.\n\n"
      "For best results, you may need to reduce your terminal\n"
      "zoom size and use a TTY that has ANSI color support."
)

conf: str = input("Ready? (Ctrl+C or Ctrl+D to quit) ").lower()
assert not conf.startswith("n"), "Game exited."
debug: bool = conf == "debug"

clear()

def changeMap(chosen_index: int | None = None) -> None:
    global _map, coins
    maps: list[str] = os.listdir('./maps')
    if chosen_index is None:
        chosen_index = random.randint(1, len(maps)) # maps are 1-indexed
    with open(f"./maps/map{chosen_index}.txt", "r") as f:
        data: str = f.read()
        _map = "\n" + data + "\n"
        if USE_RANDOM_SPAWN_POINT:
            insert_spawn_point()
        coins = 0

changeMap()

coins: int = 0

has_gone_left: bool = False
has_gone_up: bool = False
has_gone_down: bool = False
has_gone_right: bool = False

move_offset_h = 0
move_offset_v = 0

attempted_to_go_outside: bool = False
attempted_to_walk_into_wall: bool = False
failed_skill_check: bool = False
has_just_did_skill_check: bool = False

request_map_update: int = 0
level: int = 0

if debug:
    print("Debug mode enabled, please choose a map.\n")
    maps = os.listdir("./maps")
    for k, v in enumerate(maps):
        print(f"{k+1}) {v}")
    print()
    option = input("Choose an option: ")
    try:
        assert 1 <= int(option) <= len(maps), "Invalid choice"
    except ValueError:
        raise ValueError("Invalid choice")
    changeMap(chosen_index=int(option))

while 1:
    response: int = loop()
    if response == 1:
        level += 1
        if level >= MINIMUM_LEVEL_FOR_COIN_REQ_INCREASE and level % INCREASE_ONLY_WHEN_LEVEL_MODULO_IS_ZERO == 0:
            coins_until_end += AMOUNT_TO_INCREASE_BY
        changeMap()