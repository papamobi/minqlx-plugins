# This is an extension plugin  for minqlx.
# Copyright (C) 2016 mattiZed (github) aka mattiZed (ql)
# ** This plugin is thanks to mattiZed. Just modified EXTENSIVELY by BarelyMiSSeD
# to expand on the pummel counting and add grenade, air rockets,
# and air plasma, air pummel, and air rail. It also adds end of match reports for the match,
# and total counts for each of the kill types when called.

# You can redistribute it and/or modify it under the terms of the
# GNU General Public License as published by the Free Software Foundation,
# either version 3 of the License, or (at your option) any later version.

# You should have received a copy of the GNU General Public License
# along with this plugin. If not, see <http://www.gnu.org/licenses/>.

# This is a fun plugin written for Mino's Quake Live Server Mod minqlx.
# It displays "Killer x:y Victim" message when Victim gets killed with gauntlet
# and stores the information within REDIS DB

# Players can display their kill stats with:
#  "pummels" via !pummel or !gauntlet
#  "air gauntlets" via !airgauntlet
#  "grenades" via !grenades or !grenade
#  "air rockets" via !rockets or !rocket
#  "air plasma" via !plasma
#  "air rail" via !airrail
# the Total displayed is all of that type kill and it displays kills for
# the victims that are on the server on the same time.

# ******  How to set which kill types are recorded ******
# Add the values for each type of kill listed below and set that value
#  to the qlx_killsMonitorKillTypes in the same location as the rest of
#  your minqlx cvar's.
#
#  ****Kill Monitor Values****
#         Pummel:  1    (records any pummel/gauntlet kill)
#     Air Pummel:  2    (records any pummel/gauntlet kill where killer and victim are airborne)
# Direct Grenade:  4    (records any kills with direct grenade hits)
#    Air Rockets:  8    (records any Air Rocket kills)
#     Air Plasma:  16   (records any Air Plasma kills)
#      Air Rails:  32   (records any Air Rails kills where both the killer and victim are airborne)
#
# The Default value is 'set qlx_killsMonitorKillTypes "63"' which enables
#  all the kill monitor types.

import minqlx

# DB related
PLAYER_KEY = "minqlx:players:{}"

# Add Game types here if this script is not working with your game type. Follow the format.
# Find your gametype in game with the !kgt or !killsgametype command.
SUPPORTED_GAMETYPES = ("ca", "ctf", "dom", "ft", "tdm", "ffa", "ictf", "ad")

class kills(minqlx.Plugin):
    def __init__(self):
        self.set_cvar_once("qlx_killsMonitorKillTypes", "63")

        self.add_hook("kill", self.handle_kill)
        self.add_hook("game_end", self.handle_end_game)
        self.add_hook("map", self.handle_map)

        self.add_command(("pummel", "gauntlet"), self.cmd_pummel)
        self.add_command(("airpummel", "airgauntlet"), self.cmd_airpummel)
        self.add_command(("grenades", "grenade"), self.cmd_grenades)
        self.add_command(("rockets", "rocket"), self.cmd_rocket)
        self.add_command("plasma", self.cmd_plasma)
        self.add_command(("airrail", "airrails"), self.cmd_airrail)
        self.add_command("kills_version", self.kills_version)
        self.add_command(("gametypes", "games"), self.supported_games)
        self.add_command("kills", self.kills_recorded)
        self.add_command(("kgt", "killsgametype"), self.cmd_kills_gametype, 3)
        self.add_command(("rkm", "reloadkillsmonitor"), self.cmd_kills_monitor, 3)

        self.kills_pummel = {}
        self.kills_airpummel = {}
        self.kills_grenades = {}
        self.kills_rockets = {}
        self.kills_plasma = {}
        self.kills_airrail = {}

        self.kills_killMonitor = [0,0,0,0,0,0]
        self.cmd_kills_monitor()

        self.kills_gametype = self.game.type_short

    def handle_kill(self, victim, killer, data):
        if self.kills_gametype in SUPPORTED_GAMETYPES:
            mod = data["MOD"]
            msg = None
            if mod == "GAUNTLET" and (self.kills_killMonitor[0] or self.kills_killMonitor[1]):
                killed = data["VICTIM"]
                kill = data["KILLER"]
                if killed["AIRBORNE"] and kill["AIRBORNE"] and self.kills_killMonitor[1]:
                    self.sound_play("sound/vo_evil/rampage2")

                    if self.game.state == "in_progress":
                        killer_steam_id = killer.steam_id
                        victim_steam_id = victim.steam_id
                        self.db.sadd(PLAYER_KEY.format(killer_steam_id) + ":airpummel", str(victim_steam_id))
                        self.db.incr(PLAYER_KEY.format(killer_steam_id) + ":airpummel:" + str(victim_steam_id))

                        killer_score = self.db[PLAYER_KEY.format(killer_steam_id) + ":airpummel:" + str(victim_steam_id)]
                        victim_score = 0
                        if PLAYER_KEY.format(victim_steam_id) + ":airpummel:" + str(killer_steam_id) in self.db:
                            victim_score = self.db[PLAYER_KEY.format(victim_steam_id) + ":airpummel:" + str(killer_steam_id)]

                        msg = "^1AIR GAUNTLET!^7 {} ^1{}^7:^1{}^7 {}".format(killer.name, killer_score, victim_score, victim.name)
                        self.add_killer(str(killer.name), "AIRGAUNTLET")
                    else:
                        msg = "^1AIR GAUNTLET!^7 {}^7 :^7 {} ^7(^3warmup^7)".format(killer.name, victim.name)

                elif self.kills_killMonitor[0]:
                    self.sound_play("sound/vo_evil/humiliation1")

                    if self.game.state == "in_progress":
                        killer_steam_id = killer.steam_id
                        victim_steam_id = victim.steam_id
                        self.db.sadd(PLAYER_KEY.format(killer_steam_id) + ":pummeled", str(victim_steam_id))
                        self.db.incr(PLAYER_KEY.format(killer_steam_id) + ":pummeled:" + str(victim_steam_id))

                        killer_score = self.db[PLAYER_KEY.format(killer_steam_id) + ":pummeled:" + str(victim_steam_id)]
                        victim_score = 0
                        if PLAYER_KEY.format(victim_steam_id) + ":pummeled:" + str(killer_steam_id) in self.db:
                            victim_score = self.db[PLAYER_KEY.format(victim_steam_id) + ":pummeled:" + str(killer_steam_id)]

                        msg = "^1PUMMEL!^7 {} ^1{}^7:^1{}^7 {}".format(killer.name, killer_score, victim_score, victim.name)
                        self.add_killer(str(killer.name), "GAUNTLET")
                    else:
                        msg = "^1PUMMEL!^7 {}^7 :^7 {} ^7(^3warmup^7)".format(killer.name, victim.name)

            elif mod == "GRENADE" and self.kills_killMonitor[2]:
                self.sound_play("sound/vo_female/holy_shit")

                if self.game.state == "in_progress":
                    killer_steam_id = killer.steam_id
                    victim_steam_id = victim.steam_id
                    self.db.sadd(PLAYER_KEY.format(killer_steam_id) + ":grenaded", str(victim_steam_id))
                    self.db.incr(PLAYER_KEY.format(killer_steam_id) + ":grenaded:" + str(victim_steam_id))

                    killer_score = self.db[PLAYER_KEY.format(killer_steam_id) + ":grenaded:" + str(victim_steam_id)]
                    victim_score = 0
                    if PLAYER_KEY.format(victim_steam_id) + ":grenaded:" + str(killer_steam_id) in self.db:
                        victim_score = self.db[PLAYER_KEY.format(victim_steam_id) + ":grenaded:" + str(killer_steam_id)]

                    msg = "^1GRENADE KILL!^7 {} ^1{}^7:^1{}^7 {}".format(killer.name, killer_score, victim_score, victim.name)
                    self.add_killer(str(killer.name), "GRENADE")
                else:
                    msg = "^1GRENADE KILL!^7 {}^7 :^7 {} ^7(^3warmup^7)".format(killer.name, victim.name)

            elif mod == "ROCKET" and self.kills_killMonitor[3]:
                killed = data["VICTIM"]
                if killed["AIRBORNE"]:
                    self.sound_play("sound/vo_evil/midair1")

                    if self.game.state == "in_progress":
                        killer_steam_id = killer.steam_id
                        victim_steam_id = victim.steam_id
                        self.db.sadd(PLAYER_KEY.format(killer_steam_id) + ":rocket", str(victim_steam_id))
                        self.db.incr(PLAYER_KEY.format(killer_steam_id) + ":rocket:" + str(victim_steam_id))

                        killer_score = self.db[PLAYER_KEY.format(killer_steam_id) + ":rocket:" + str(victim_steam_id)]
                        victim_score = 0
                        if PLAYER_KEY.format(victim_steam_id) + ":rocket:" + str(killer_steam_id) in self.db:
                            victim_score = self.db[PLAYER_KEY.format(victim_steam_id) + ":rocket:" + str(killer_steam_id)]

                        msg = "^1AIR ROCKET KILL!^7 {} ^1{}^7:^1{}^7 {}".format(killer.name, killer_score, victim_score, victim.name)
                        self.add_killer(str(killer.name), "ROCKET")
                    else:
                        msg = "^1AIR ROCKET KILL!^7 {}^7 :^7 {} ^7(^3warmup^7)".format(killer.name, victim.name)

            elif mod == "PLASMA" and self.kills_killMonitor[4]:
                killed = data["VICTIM"]
                if killed["AIRBORNE"]:
                    self.sound_play("sound/vo_evil/damage")

                    if self.game.state == "in_progress":
                        killer_steam_id = killer.steam_id
                        victim_steam_id = victim.steam_id
                        self.db.sadd(PLAYER_KEY.format(killer_steam_id) + ":plasma", str(victim_steam_id))
                        self.db.incr(PLAYER_KEY.format(killer_steam_id) + ":plasma:" + str(victim_steam_id))

                        killer_score = self.db[PLAYER_KEY.format(killer_steam_id) + ":plasma:" + str(victim_steam_id)]
                        victim_score = 0
                        if PLAYER_KEY.format(victim_steam_id) + ":plasma:" + str(killer_steam_id) in self.db:
                            victim_score = self.db[PLAYER_KEY.format(victim_steam_id) + ":plasma:" + str(killer_steam_id)]

                        msg = "^1AIR PLASMA KILL!^7 {} ^1{}^7:^1{}^7 {}".format(killer.name, killer_score, victim_score, victim.name)
                        self.add_killer(str(killer.name), "PLASMA")
                    else:
                        msg = "^1AIR PLASMA KILL!^7 {}^7 :^7 {} ^7(^3warmup^7)".format(killer.name, victim.name)

            elif (mod == "RAILGUN" or mod == "RAILGUN_HEADSHOT") and self.kills_killMonitor[5]:
                killed = data["VICTIM"]
                kill = data["KILLER"]
                if killed["AIRBORNE"] and kill["AIRBORNE"]:
                    self.sound_play("sound/vo_female/midair3")

                    if self.game.state == "in_progress":
                        killer_steam_id = killer.steam_id
                        victim_steam_id = victim.steam_id
                        self.db.sadd(PLAYER_KEY.format(killer_steam_id) + ":airrail", str(victim_steam_id))
                        self.db.incr(PLAYER_KEY.format(killer_steam_id) + ":airrail:" + str(victim_steam_id))

                        killer_score = self.db[PLAYER_KEY.format(killer_steam_id) + ":airrail:" + str(victim_steam_id)]
                        victim_score = 0
                        if PLAYER_KEY.format(victim_steam_id) + ":airrail:" + str(killer_steam_id) in self.db:
                            victim_score = self.db[PLAYER_KEY.format(victim_steam_id) + ":airrail:" + str(killer_steam_id)]

                        msg = "^1AIR RAIL KILL!^7 {} ^1{}^7:^1{}^7 {}".format(killer.name, killer_score, victim_score, victim.name)
                        self.add_killer(str(killer.name), "AIRRAIL")
                    else:
                        msg = "^1AIR RAIL KILL!^7 {}^7 :^7 {} ^7(^3warmup^7)".format(killer.name, victim.name)

            if msg:
                self.msg(msg)

    def handle_map(self, mapname, factory):
        self.kills_gametype = self.game.type_short

    def handle_end_game(self, data):
        self.kills_gametype = self.game.type_short
        if self.kills_gametype in SUPPORTED_GAMETYPES:
            count = 0

            msg = "^3Pummel ^1Killers^7: "
            for k, v in self.kills_pummel.items():
                msg += "{}^7:^1{}^7 ".format(k, v)
                count += 1
            if count > 0:
                self.msg(msg)
                count = 0

            msg = "^3Air Gauntlet ^1Killers^7: "
            for k, v in self.kills_airpummel.items():
                msg += "{}^7:^1{}^7 ".format(k, v)
                count += 1
            if count > 0:
                self.msg(msg)
                count = 0

            msg = "^3Grenade ^1Killers^7: "
            for k, v in self.kills_grenades.items():
                msg += "{}^7:^1{}^7 ".format(k, v)
                count += 1
            if count > 0:
                self.msg(msg)
                count = 0

            msg = "^3Air Rocket ^1Killers^7: "
            for k, v in self.kills_rockets.items():
                msg += "{}^7:^1{}^7 ".format(k, v)
                count += 1
            if count > 0:
                self.msg(msg)
                count = 0

            msg = "^3Air Plasma ^1Killers^7: "
            for k, v in self.kills_plasma.items():
                msg += "{}^7:^1{}^7 ".format(k, v)
                count += 1
            if count > 0:
                self.msg(msg)
                count = 0

            msg = "^3Air Rail ^1Killers^7: "
            for k, v in self.kills_airrail.items():
                msg += "{}^7:^1{}^7 ".format(k, v)
                count += 1
            if count > 0:
                self.msg(msg)

            self.kills_pummel = {}
            self.kills_airpummel = {}
            self.kills_grenades = {}
            self.kills_rockets = {}
            self.kills_plasma = {}
            self.kills_airrail = {}

    def cmd_kills_gametype(self, player, msg, channel):
        player.tell("^2The current gametype is \'{}\'".format(self.kills_gametype))
        return minqlx.RET_STOP_ALL

    def cmd_pummel(self, player, msg, channel):
        if not self.kills_killMonitor[0]:
                self.msg("^4Pummel Kill ^7stats are not enabled on this server.")
        else:
            if len(msg) > 1:
                player = self.player_id(msg[1], player)

            p_steam_id = player.steam_id
            total = 0
            pummels = self.db.smembers(PLAYER_KEY.format(p_steam_id) + ":pummeled")
            players = self.teams()["spectator"] + self.teams()["red"] + self.teams()["blue"] + self.teams()["free"]

            msg = ""
            for p in pummels:
                total += int(self.db[PLAYER_KEY.format(p_steam_id) + ":pummeled:" + str(p)])
                for pl in players:
                    if p == str(pl.steam_id):
                        count = self.db[PLAYER_KEY.format(p_steam_id) + ":pummeled:" + p]
                        msg +=  pl.name + ": ^1" + count + "^7 "
            if total:
                self.msg("^4Pummel^7 Stats for {}: Total ^4Pummels^7: ^1{}".format(player, total))
                self.msg(msg)
            else:
                self.msg("{} ^7has not ^4pummeled^7 anybody on this server.".format(player))

    def cmd_airpummel(self, player, msg, channel):
        if not self.kills_killMonitor[1]:
                self.msg("^4Air Pummel Kill ^7stats are not enabled on this server.")
        else:
            if len(msg) > 1:
                player = self.player_id(msg[1], player)

            p_steam_id = player.steam_id
            total = 0
            pummels = self.db.smembers(PLAYER_KEY.format(p_steam_id) + ":airpummel")
            players = self.teams()["spectator"] + self.teams()["red"] + self.teams()["blue"] + self.teams()["free"]

            msg = ""
            for p in pummels:
                total += int(self.db[PLAYER_KEY.format(p_steam_id) + ":airpummel:" + str(p)])
                for pl in players:
                    if p == str(pl.steam_id):
                        count = self.db[PLAYER_KEY.format(p_steam_id) + ":airpummel:" + p]
                        msg +=  pl.name + ": ^1" + count + "^7 "
            if total:
                self.msg("^4Air Gauntlet^7 Stats for {}: Total ^4Air Gauntlets^7: ^1{}".format(player, total))
                self.msg(msg)
            else:
                self.msg("{} ^7has not ^4air gauntleted^7 anybody on this server.".format(player))

    def cmd_grenades(self, player, msg, channel):
        if not self.kills_killMonitor[2]:
                self.msg("^4Grenade Kill ^7stats are not enabled on this server.")
        else:
            if len(msg) > 1:
                player = self.player_id(msg[1], player)

            p_steam_id = player.steam_id
            total = 0
            grenades = self.db.smembers(PLAYER_KEY.format(p_steam_id) + ":grenaded")
            players = self.teams()["spectator"] + self.teams()["red"] + self.teams()["blue"] + self.teams()["free"]

            msg = ""
            for p in grenades:
                total += int(self.db[PLAYER_KEY.format(p_steam_id) + ":grenaded:" + str(p)])
                for pl in players:
                    if p == str(pl.steam_id):
                        count = self.db[PLAYER_KEY.format(p_steam_id) + ":grenaded:" + p]
                        msg += pl.name + ": ^1" + count + "^7 "
            if total:
                self.msg("^4Grenade^7 Stats for {}: Total ^4Grenade^7 Kills: ^1{}".format(player, total))
                self.msg(msg)
            else:
                self.msg("{} ^7has not ^4grenade^7 killed anybody on this server.".format(player))

    def cmd_rocket(self, player, msg, channel):
        if not self.kills_killMonitor[3]:
                self.msg("^4Air Rocket Kill ^7stats are not enabled on this server.")
        else:
            if len(msg) > 1:
                player = self.player_id(msg[1], player)

            p_steam_id = player.steam_id
            total = 0
            rocket = self.db.smembers(PLAYER_KEY.format(p_steam_id) + ":rocket")
            players = self.teams()["spectator"] + self.teams()["red"] + self.teams()["blue"] + self.teams()["free"]

            msg = ""
            for p in rocket:
                total += int(self.db[PLAYER_KEY.format(p_steam_id) + ":rocket:" + str(p)])
                for pl in players:
                    if p == str(pl.steam_id):
                        count = self.db[PLAYER_KEY.format(p_steam_id) + ":rocket:" + p]
                        msg += pl.name + ": ^1" + count + "^7 "
            if total:
                self.msg("^4Air Rocket^7 Stats for {}: Total ^4Air Rocket^7 Kills: ^1{}".format(player, total))
                self.msg(msg)
            else:
                self.msg("{} has not ^4air rocket^7 killed anybody on this server.".format(player))

    def cmd_plasma(self, player, msg, channel):
        if not self.kills_killMonitor[4]:
                self.msg("^4Air Plasma Kill ^7stats are not enabled on this server.")
        else:
            if len(msg) > 1:
                player = self.player_id(msg[1], player)

            p_steam_id = player.steam_id
            total = 0
            rocket = self.db.smembers(PLAYER_KEY.format(p_steam_id) + ":plasma")
            players = self.teams()["spectator"] + self.teams()["red"] + self.teams()["blue"] + self.teams()["free"]

            msg = ""
            for p in rocket:
                total += int(self.db[PLAYER_KEY.format(p_steam_id) + ":plasma:" + str(p)])
                for pl in players:
                    if p == str(pl.steam_id):
                        count = self.db[PLAYER_KEY.format(p_steam_id) + ":plasma:" + p]
                        msg += pl.name + ": ^1" + count + "^7 "
            if total:
                self.msg("^4Air Plasma^7 Stats for {}: Total ^4Air Plasma^7 Kills: ^1{}".format(player, total))
                self.msg(msg)
            else:
                self.msg("{} has not ^4air plasma^7 killed anybody on this server.".format(player))

    def cmd_airrail(self, player, msg, channel):
        if not self.kills_killMonitor[5]:
                self.msg("^4Air Rail Kill ^7stats are not enabled on this server.")
        else:
            if len(msg) > 1:
                player = self.player_id(msg[1], player)

            p_steam_id = player.steam_id
            total = 0
            pummels = self.db.smembers(PLAYER_KEY.format(p_steam_id) + ":airrail")
            players = self.teams()["spectator"] + self.teams()["red"] + self.teams()["blue"] + self.teams()["free"]

            msg = ""
            for p in pummels:
                total += int(self.db[PLAYER_KEY.format(p_steam_id) + ":airrail:" + str(p)])
                for pl in players:
                    if p == str(pl.steam_id):
                        count = self.db[PLAYER_KEY.format(p_steam_id) + ":airrail:" + p]
                        msg +=  pl.name + ": ^1" + count + "^7 "
            if total:
                self.msg("^4Air Rail^7 Stats for {}: Total ^4Air Rails^7: ^1{}".format(player, total))
                self.msg(msg)
            else:
                self.msg("{} ^7has not ^4air railed^7 anybody on this server.".format(player))

    def add_killer(self, killer, method):
        if method == "GAUNTLET":
            try:
                self.kills_pummel[killer] += 1
            except:
                self.kills_pummel[killer] = 1
        if method == "AIRGAUNTLET":
            try:
                self.kills_airpummel[killer] += 1
            except:
                self.kills_airpummel[killer] = 1
        if method == "GRENADE":
            try:
                self.kills_grenades[killer] += 1
            except:
                self.kills_grenades[killer] = 1
        if method == "ROCKET":
            try:
                self.kills_rockets[killer] += 1
            except:
                self.kills_rockets[killer] = 1
        if method == "PLASMA":
            try:
                self.kills_plasma[killer] += 1
            except:
                self.kills_plasma[killer] = 1
        if method == "AIRRAIL":
            try:
                self.kills_airrail[killer] += 1
            except:
                self.kills_airrail[killer] = 1

    def sound_play(self, path):
        for p in self.players():
            if self.db.get_flag(p, "essentials:sounds_enabled", default=True):
                super().play_sound(path, p)

    def supported_games(self, player, msg, channel):
        self.msg("^4Special kills ^7are recorded on this server when playing gateypes:")
        self.msg("^3{}".format(str(SUPPORTED_GAMETYPES)))

    def kills_recorded(self, player, msg, channel):
        self.msg("^4Special kills ^7are recorded when these kills are made:")
        self.msg("^3Pummel^7, ^3Air Gauntlet^7, ^3Direct Grenade^7, ^3Mid-Air Rocket^7,\n ^3Mid-Air Plasma, and ^3Air Rails")
        self.msg("^6Commands^7: ^4!pummel^7, ^4!airgauntlet^7, ^4!grenades^7, ^4!rockets^7,\n ^4!plasma, ^4!airrails")

    def player_id(self, id, player):
        try:
            id = int(id)
            if 0 <= id <= 63:
                try:
                    target_player = self.player(id)
                except minqlx.NonexistentPlayerError:
                    player.tell("^3Invalid client ID. Use a client ID.")
                    return minqlx.RET_STOP_EVENT
                if not target_player:
                    player.tell("^3Invalid client ID. Use a client ID.")
                    return minqlx.RET_STOP_EVENT
            elif id < 0:
                player.tell("^3usage^7=^7<^2player id^7>")
                return minqlx.RET_STOP_EVENT
            elif len(str(id)) != 17:
                player.tell("^3STEAM ID's are not supported.")
                return minqlx.RET_STOP_EVENT
        except ValueError:
            player.tell("^3Invalid ID. Use a client ID.")
            return minqlx.RET_STOP_EVENT

        return target_player

    def cmd_kills_monitor(self, player=None, msg=None, channel=None):
        games = self.get_cvar("qlx_killsMonitorKillTypes", int)
        binary = bin(games)[2:]
        length = len(str(binary))
        count = 0

        while length > 0:
            self.kills_killMonitor[count] = int(binary[length - 1])
            count += 1
            length -= 1

        if player:
            player.tell("Monitor: {}".format(str(self.kills_killMonitor)))
            return minqlx.RET_STOP_ALL

    def kills_version(self, player, msg, channel):
        self.msg("^7This server is running ^4Kills^7 Version^1 1.09")