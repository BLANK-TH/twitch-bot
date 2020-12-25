# Commands
**Prefix:** `b!`

&lt;example> Required

[example] optional

If the command contains quotation marks, then make sure those quotation marks are there or the command may break.

## Table of Contents
- [Fun Commands](#fun-commands)
- [Utility Commands](#utility-commands)
- [Mod Commands](#mod-commands)

## Fun Commands
### Good Bot
**Command**: `goodbot`
Call BLANK a good bot and shows how many times this command has been used.
### Good Human
**Command**: `goodhuman`
Same as [good bot](#good-bot) except with good human instead.
### Christmas
**Command**: `christmas`
Time until Christmas (in UTC).
### Sabotage
**Command**: `sabotage [add/remove] [value]`
Posts a random message sabotaging BLANK. Mods can also use this command to add/remove phrases to the sabotage list.

## Utility Commands
### Help
**Command**: `help` **OR** `commands`
Get a link to this page
### Personal Information Warning
**Command:** `piwarning` **OR** `pi`
Warn BLANK about the current post possible violating PI rules (more noticeable than a chat message).
### Get Gamma
**Command**: `getgamma` **OR** `gamma`
Get BLANK's current gamma (number of transcriptions done in total), this command was tested to be instantly updated when the gamma is updated
### Progress
**Command**: `progress`
Get the number of transcriptions BLANK has done since the start of the stream.
### Transcribers
**Command**: `transcribers [add/remove] [value]`
Posts a list of streaming transcribers. Mods can also use this command to add/remove transcribers from the list.
### Calculator
**Command**: `calculate <expression>` **OR** `c <expression>`
Calculates a given expression

## Mod Commands
### Starting Gamma
**Command**: `startinggamma [new gamma]` **OR** `sg [new gamma]`
Get the starting gamma of the stream or set it.
### Restart
**Command**: `restart [cache data]`
Restart the bot, add a boolean value after the command to specify whether or not to cache data (like starting gamma).
### Add Mod
**Command**: `addmod <mod>`
Add a ToR mod to the detection list.
### Add Mod
**Command**: `removemod <mod>`
Remove a ToR mod from the detection list.
