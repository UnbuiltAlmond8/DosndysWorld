# Documentation

Dosndy's World was inspired by Dandy's World and the terminal-only nature of DOS games. If some code is unclear, it's because the author's goal was merely to get the game working.

Directories are shown relative to the root of this repository.

## Maps

Map files are located in `./dosndys/maps` with the name `mapN.txt` where `N` is an integer. 
- IMPORTANT: Map files are 1-indexed! Do not attempt to create a `map0.txt` file, as it will never be used.
At the start or upon load, a random map file is chosen.
If an INVALID map is encountered, the game will crash.

A valid map must:
- (file name only) match the regex pattern `map\d+\.txt` in the file name
- consist only of the characters #, O, E, U, spaces, and newlines
- comtain at least one of the aforementioned characters, except:
  - O, which must appear exactly once
  - U, which must appear exactly once, and is the initial position of the player
  - E, which must appear exactly three times, consecutively
- have all its lines be of equal length
  
and should:
- have an EEE elevator sequence placed within the horizontal walls at the very top or bottom
- not have holes in the walls that allow going outside of the map

Example:

```
############EEE###########
#          O             #
#                        #
#     ##############U    #
#                        #
#                        #
##########################
```

## global.json

The global.json file must respect the below schema:

```json5
{
    "coins": {
        // Base number of coins until the elevator is activated.
        // Default: 15.
        "COINS_UNTIL_END": number,

        // The starting level when the coin amount required is increased.
        // Default: 3.
        "MINIMUM_LEVEL_FOR_COIN_REQ_INCREASE": number,

        // Apply the increase only when level % value == 0.
        // Default: 5.
        "INCREASE_ONLY_WHEN_LEVEL_MODULO_IS_ZERO": number,

        // When an increase occurs, how much do we increase the coin
        // requirement by?
        // Default: 5.
        "AMOUNT_TO_INCREASE_BY": number
    },
    "skillcheck": {
        "SKILL_CHECK_MARKER_SIZE": number, // Default: 10
        "SKILL_CHECK_SIZE": number, // Default: 30
        "SKILL_CHECK_CENTER_RANGE": number, // Default: 1
        "SKILL_CHECK_SPEED": number // Default: 20
    },
    "moveset": {
        // Changes to this moveset are reflected in the start
        // screen.
        "up": string, // Default: "w"
        "left": string, // Default: "a"
        "down": string, // Default: "s"
        "right": string, // Default: "d"
        "skillcheck": string // Default: "space"
    },
    "onmapload": {
        // If true, moves the U to a random walkable point before
        // loading the map.
        // Default: true.
        "USE_RANDOM_SPAWN_POINT": boolean
    }
}
```

Note that the values in `moveset` have to be of valid keyboard key names that the Python `keyboard` module can use.
For the values in `skillcheck`, they are measured in characters with the exception of `speed` which is measured as the denominator of a fraction of a second.

The `global.json` file must exist in `./dosndys` and conform to valid JSON schema, otherwise you will get the error `global.json either does not exist or does not conform to valid JSON`. If this passes, but it does not conform to the schema described above, you will get the error `global.json does not conform to settings schema`.

## Notes about the game

Some parts of the script are directory dependent, so you have to run `python game.py` from `./dosndys`.

For the best experience, ANSI color support is highly recommended. If your terminal does not support this feature, either 1) remove the ANSI-based `to_print` replacements in the unminified code and change the skill check characters to simple ASCII or 2) use a different terminal with such support enabled.

It is highly recommended to use PowerShell with PSReadLine to prevent your keystrokes from being displayed after exiting. This is important because the script intentionally does not pass `suppress=True` as that may cause the keyboard to not work in other applications.

## Debug mode (advanced)

To activate debug mode, type in `debug` at the start and press Enter. With debug mode, you can choose a map to test, your position coordinates and the terminal size will show up, and you will not be accused of cheating when you go outside of the map if even possible.

## Minified version

A minified version is available for the same experience with reduced file size, available in the `./dosndys-min.7z` file. The author used python-minifier and Notepad++ JSON compression tools alongside 7zip to make this minification possible.
