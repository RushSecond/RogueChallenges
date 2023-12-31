#--------------------------
#You can change the parameters of Roguelike Mode here.
#--------------------------
#The number of spells you start with (default is 14). Set this to -1 to start with all spells
STARTING_SPELLS = 14
#The number of starting spells that are level 1 (default is 2)
LEVEL_ONES = 2
#The number of spells gained on each realm (default is 2)
SPELLS_PER_LEVEL = 2
#The number of skills you start with (default 7). Set this to -1 to start with all skills
STARTING_SKILLS = 7
#The number of skills gained on each realm (default is 1)
SKILLS_PER_LEVEL = 1
#The cost discount for all skills (default is 0)
SKILL_DISCOUNT = 0

from LevelGen import *
from CommonContent import *
from Consumables import *
from Mutators import *
from RiftWizard import *
from Variants import *
import Level, Spells, Monsters, math
import sys, random, copy

try:
    import mods.MordredOverhaul.MordredOverhaul
    MORDRED_OVERHAULED = True
except ImportError:
    MORDRED_OVERHAULED = False
    
try:
    import mods.Bugfixes.Bugfixes
    BUG_FIXED = True
except ImportError:
    BUG_FIXED = False
    
try:
    import mods.PoisonCounterplays.PoisonCounterplays
    ANTI_POISON = True
except ImportError:
    ANTI_POISON = False

TEST_CHEATY = False
TEST_ELITE_GATES = False
TEST_SHIELD_GATES = False
TEST_MORDRED = False
TEST_SLIMES = False
TEST_WIZARD_COOLDOWNS = False
TEST_HEAL_REDUCTION = False
TEST_SH_INCREASE = False
TEST_HORDES = False

# shamelessly stolen from bugfixes in case that mod isn't present
# so you can actually read what the new trials do
def modify_class(cls):

    if cls is PyGameView:
    
        def draw_pick_trial(self):

            num_modded_trials = len(all_trials) - 13
            shift_down = min(num_modded_trials, 5)
            shift_up = 0
            if num_modded_trials > 5:
                shift_up = num_modded_trials - 5

            rect_w = max(self.font.size(trial.name)[0] for trial in all_trials)
            cur_x = self.screen.get_width() // 2 - rect_w // 2
            cur_y = self.screen.get_height() // 2 - self.linesize * (4 + shift_up)

            cur_color = (255, 255, 255)
            for trial in all_trials:
                self.draw_string(trial.name, self.screen, cur_x, cur_y, cur_color, mouse_content=trial, content_width=rect_w)
                if SteamAdapter.get_trial_status(trial.name):
                    self.draw_string("*", self.screen, cur_x - 16, cur_y, COLOR_VICTORY)
                cur_y += self.linesize

            cur_y += self.linesize * (10 - shift_down)

            if isinstance(self.examine_target, Trial):
                desc = self.examine_target.get_description()
                for line in desc.split('\n'):
                    cur_x = (self.screen.get_width() // 2) - (self.font.size(line)[0] // 2)
                    self.draw_string(line, self.screen, cur_x, cur_y)
                    cur_y += self.linesize
                    
        def get_anim(self, unit, forced_name=None):

            # Find the asset name
            if forced_name:
                asset = ["char", forced_name]
            else:
                asset = get_unit_asset(unit)

            # Determine lair colors for lairs
            lair_colors = None
            if unit.is_lair:
                example_monster = unit.buffs[0].example_monster
                example_sprite_name = example_monster.get_asset_name()
                example_sprite = self.get_sprite_sheet(get_unit_asset(example_monster))
                lair_colors = example_sprite.get_lair_colors()
                
            # modify colors of elite gates
            if lair_colors is not None and unit.description == "EliteGate":
                new_colors = []
                for i in range(len(lair_colors)):
                    color = lair_colors[i]
                    colorR = min(255, color[0] + 70)
                    colorG = min(255, color[1] + 70)
                    colorB = min(255, color[2] + 70)
                    new_colors.append(tuple([colorR, colorG, colorB]))
                    
                lair_colors = tuple(new_colors)

            sprite = self.get_sprite_sheet(asset, lair_colors=lair_colors)

            return UnitSprite(unit, sprite, view=self)
                    
    for func_name, func in [(key, value) for key, value in locals().items() if callable(value)]:
        if hasattr(cls, func_name):
            setattr(cls, func_name, func)

curr_module = sys.modules[__name__]
curr_module.modify_class(PyGameView)


class RogueLikeMode(Mutator):
    #most of this remains the same as the original roguelike mod, just some optimizations where necessary
    def __init__(self, numspells=5, numstarters=2, num_newspells=2, numskills=1, num_newskills=1, discount= 2):
        Mutator.__init__(self)
        # negative numbers = give the player all the spells
        # also use floor incase some dummy puts in decimal numbers
        self.numspells = 9999 if numspells < 0 else math.floor(numspells) 
        self.numstarters = math.floor(numstarters)
        self.numskills = 9999 if numskills < 0 else math.floor(numskills)
        self.num_newspells = math.floor(num_newspells)
        self.num_newskills = math.floor(num_newskills)
        self.discount = math.floor(discount)
        self.description = "Start with %d spells and %d skills\nGain %d new spells and %d new skills after each completed realm" % (self.numspells, self.numskills, self.num_newspells, self.num_newskills)
        if self.discount > 0:
            self.description += "\nSkills are %d SP cheaper" % self.discount
        self.otherspells = None
        self.availablespells = None
        self.availableskills = None
        self.otherskills = None
        
    def on_generate_spells(self, spells):
        self.availablespells, self.otherspells = spells, list(spells)
        
    def on_generate_skills(self, skills):
        self.availableskills, self.otherskills = skills, list(skills)
        
    def on_game_begin(self, game):
        if TEST_CHEATY:
            game.p1.max_hp = 999
            game.p1.cur_hp = 999
            game.p1.xp = 999
            self.numspells = 9999
            self.numskills = 9999
            
        if self.numspells < len(self.availablespells):
            self.availablespells.clear()
            starters = [s for s in self.otherspells if s.level < 2 and s.name != "Parlor Trick"] #parlor trick can't clear the 1st level
            random.shuffle(starters)
            for s in range(0, self.numstarters):
                if s < len(starters):
                    self.availablespells.insert(0,starters[s])
                    self.otherspells.remove(starters[s])
            random.shuffle(self.otherspells)
            #minor iteration change to make sure players start with the correct number of spells
            for s in range(0, self.numspells-self.numstarters):
                if len(self.otherspells) > 0: # this ensures the game doesn't crash if we run out of spells/skills
                    self.availablespells.insert(0,self.otherspells[0])
                    self.otherspells.remove(self.otherspells[0])
        else:
            self.otherspells.clear()
                    
        if self.numspells < len(self.availableskills):           
            self.availableskills.clear()
            random.shuffle(self.otherskills)
            for s in range(0, self.numskills):
                if len(self.otherskills) > 0:
                    self.otherskills[0].level = max(1, self.otherskills[0].level-self.discount)
                    self.availableskills.insert(0,self.otherskills[0])
                    self.otherskills.remove(self.otherskills[0])
        else:
            self.otherskills.clear()
        #applies the new form of the roguelike buff
        game.p1.apply_buff(RogueLikeModeBuff(self.num_newspells, self.num_newskills, self.discount, self.availablespells, self.otherspells, self.availableskills, self.otherskills))       

class RogueLikeModeBuff(Level.Buff):

    def __init__(self, num_newspells, num_newskills, discount, availablespells, otherspells, availableskills, otherskills):
        Level.Buff.__init__(self)
        #makes the roguelike mode buff passive since fae arcanists can only dispel buffs of bless type
        self.buff_type = Level.BUFF_TYPE_PASSIVE
        self.num_newspells = num_newspells
        self.num_newskills = num_newskills
        self.discount = discount
        self.availablespells = availablespells
        self.otherspells = otherspells
        self.availableskills = availableskills
        self.otherskills = otherskills
        self.triggered = False
        self.name = "Roguelike Mode"
        self.prereq = 0 # needed if bugfixes isn't present, else the game crashes
        self.description = "Gain %d new spells and %d new skills every level. Skills cost 2 SP less." # we never see this anyway
        self.owner_triggers[Level.EventOnUnitAdded] = self.enter_level_reset
        
    def enter_level_reset(self, evt):
        self.triggered = False #now ready to grant new spells when the realm is cleared
        
    def on_pre_advance(self):
        if self.triggered:
            return
        if not all(u.team == TEAM_PLAYER for u in self.owner.level.units):
            return
        #level is cleared, so grant new stuff
        self.triggered = True
        self.update_spells(self.owner)

    def update_spells(self, owner):
        random.shuffle(self.otherspells)
        for _ in range(self.num_newspells):
            if len(self.otherspells) > 0:
                self.availablespells.insert(0,self.otherspells[0])
                self.otherspells.remove(self.otherspells[0])
        random.shuffle(self.otherskills)
        for _ in range(self.num_newskills):
            if len(self.otherskills) > 0:
                self.otherskills[0].level = max(1, self.otherskills[0].level-self.discount)
                self.availableskills.insert(0,self.otherskills[0])
                self.otherskills.remove(self.otherskills[0])
            
class MoreGates(Mutator):
    
    def __init__(self, realm_list=[2,15]):
        Mutator.__init__(self)
        self.realm_list = realm_list
        self.description = "Each realm has additional monster generators"

    def on_levelgen_pre(self, levelgen):
        #dont add gates to Mordred's place
        if levelgen.difficulty == Level.LAST_LEVEL:
            return
        
        for realm_num in self.realm_list:
            if levelgen.difficulty >= realm_num:
                levelgen.num_generators += 1
             
class MonsterHordes(Mutator):

    def __init__(self, min_monsters, max_monsters, min_horde, max_horde):
        Mutator.__init__(self)
        self.min_monsters = min_monsters
        self.max_monsters = max_monsters
        self.min_horde = min_horde
        self.max_horde = max_horde
        self.description = "All realms have more monsters. Realms with relatively easier monsters have many more of them"
        
    def on_levelgen_pre(self, levelgen):
        if levelgen.difficulty == 1:
            return
        
        minLevel, maxLevel = get_spawn_min_max(levelgen.difficulty)
        avgLevel = 0
        for spawner, cost in levelgen.spawn_options:
            avgLevel += (cost / len(levelgen.spawn_options))
        
        levelDiff = maxLevel - minLevel
        lerpVar = 0
        if levelDiff > 0:
            lerpVar = (maxLevel - avgLevel) / levelDiff
        
        finalMin = round(self.min_monsters + self.min_horde * lerpVar + 0.001)
        finalMax = round(self.max_monsters + self.max_horde * lerpVar + 0.001)
        
        levelgen.num_monsters = levelgen.random.randint(finalMin, finalMax)
        
        if TEST_HORDES:
            print("difficulty = %d, avgLevel = %f, lerpVar = %f, finalMin = %d, finalMax = %d" % (levelgen.difficulty, avgLevel, lerpVar, finalMin, finalMax))

class MonsterHPMultFraction(Mutator):

    def __init__(self, mult=2):
        Mutator.__init__(self)
        self.mult = mult
        if TEST_SLIMES:
            self.mult = 2.1
        self.description = "All enemy monsters have %d%% more HP" % round((self.mult-1)*100)
        self.global_triggers[Level.EventOnUnitPreAdded] = self.on_enemy_added

    def on_enemy_added(self, evt):
        if not evt.unit.ever_spawned:
            self.modify_unit(evt.unit)

    def on_levelgen(self, levelgen):
        if TEST_SLIMES and levelgen.difficulty == 1:
            spawn_point = levelgen.empty_spawn_points.pop()
            obj = Monsters.GreenSlime()
            levelgen.level.add_obj(obj, spawn_point.x, spawn_point.y)
            
        for u in levelgen.level.units:
            self.modify_unit(u)

    def modify_unit(self, unit):
        if unit.is_lair:
            return
        if unit.team == TEAM_PLAYER:
            return
        # Do not buff the HP of splitting units
        if isinstance(unit.source, SplittingBuff):
            return
        unit.max_hp = round(unit.max_hp * self.mult + 0.001) #add 0.001 so float arithemetic doesn't screw up
        unit.cur_hp = round(unit.cur_hp * self.mult + 0.001)
        
        # need to reset slime buffs after changing their hp
        for b in unit.buffs:
            if isinstance(b, SlimeBuff):
                unit.remove_buff(b)
                unit.apply_buff(b)

class EliteSpawnsAndGates(Mutator):

    def __init__(self, realm_start = 9, realm_step = 2, max_avg_elites = 6):
        Mutator.__init__(self)
        self.realm_start = realm_start
        if TEST_ELITE_GATES:
            self.realm_start = 1
        self.realm_step = realm_step
        self.max_avg_elites = max_avg_elites
        self.description = "Realms %d and beyond have extra elite monsters and elite gates" % self.realm_start
        
    def extra_elite_num(self, levelgen):
        num_steps = (levelgen.difficulty - self.realm_start) // self.realm_step
        num = min(self.max_avg_elites, num_steps+1)
        
        return levelgen.random.randint(num-1,num+1)
        
    def roll_variant_new(self, spawn, levelgen):
        elite_gate_flag = levelgen.difficulty >= self.realm_start and not hasattr(levelgen, "gate_elite")

        prng = levelgen.random

        # forcevariant cheat- allways spawn a specific variant, even if that monster isnt present.  for debug.
        if 'forcevariant' in sys.argv:
            var_str = sys.argv[sys.argv.index('forcevariant') + 1]
            var_str = var_str.lower()
            var_str = var_str.replace(' ', '')
            var_str = var_str.replace('_', '')

            for spawn_list in variants.values():
                for spawn, lb, ub, w in spawn_list:
                    spawn_str = spawn().name
                    spawn_str = spawn_str.replace(' ', '')
                    spawn_str = spawn_str.lower()
                    if var_str in spawn_str:
                        num = prng.randint(lb, ub)
                        units = [spawn() for i in range(num)]
                        return units

        if spawn in variants:
            options = variants[spawn]
            choice = prng.choices(population=options, weights=[o[3] for o in options])[0]
            variant_spawn, min_num, max_num, weight = choice 
            num = prng.randint(min_num, max_num)
            
            # some really bad stuff can come out of gates with max num of 4
            # but oh well lets see some fireworks
            if (max_num >= 4 and elite_gate_flag):
                levelgen.gate_elite = variant_spawn # for making gates
                num += self.extra_elite_num(levelgen)

            units = [variant_spawn() for i in range(num)]
    #       if max_num == 1:
    #           for u in units:
    #               u.is_boss = True

            return units
        else:
            return None
        
    def get_elites_new(self, levelgen):
        elite_gate_flag = levelgen.difficulty >= self.realm_start and not hasattr(levelgen, "gate_elite")
    
        _, level = get_spawn_min_max(levelgen.difficulty)

        # if there's no gate elite, force a level +1 for it
        if levelgen.difficulty < 5 or elite_gate_flag:
            modifier = 1
        else:
            modifier = self.random.choice([1, 1, 1, 1, 2, 2])

        level = min(level + modifier, 9)

        if modifier == 1:
            num_elites = self.random.choice([5, 6, 7])
        if modifier == 2:
            num_elites = self.random.choice([3, 4, 5])
        if modifier == 3:
            num_elites = self.random.choice([2, 3])

        options = [(s, l) for s, l in spawn_options if l == level]
        spawner = self.random.choice(options)[0]
        
        if elite_gate_flag:
            levelgen.gate_elite = spawner # for making gates
            num_elites += self.extra_elite_num(levelgen)
            
        units = [spawner() for i in range(num_elites)] 
        return units

    def on_levelgen_pre(self, levelgen):
        difficulty = levelgen.difficulty
        # don't add more elites to Mordred's pad
        if difficulty == Level.LAST_LEVEL:
            return
            
        levelgen.num_eliteGates = (0 if difficulty < self.realm_start else
                                    1 if difficulty < 15 else
                                    2 if difficulty < 22 else 
                                    3)
        levelgen.num_generators -= levelgen.num_eliteGates
        
        # ok now lets redo the whole boss list
        levelgen.bosses = []

        num_boss_spawns = (0 if difficulty <= 1 and not TEST_ELITE_GATES else
                           1 if difficulty <= 3 and not TEST_ELITE_GATES else
                           2 if difficulty <= 8 else
                           3)

        # for debugging
        if 'forcevariant' in sys.argv:
            num_boss_spawns = 1

        for i in range(num_boss_spawns):
        
            # first 50% chance to make a variant if we can, otherwise make an elite
            # Should be- 50% first time, 30% subsequent times
        
            chance = .5 if i == 0 else .3
            
            # 0% last time if we still need an elite gate
            if difficulty >= self.realm_start and i == num_boss_spawns-1 and not hasattr(levelgen, "gate_elite"):
                chance = 0
                
            roll_result = None
            
            if levelgen.random.random() < chance or 'forcevariant' in sys.argv:
                spawn_type = levelgen.random.choice(levelgen.spawn_options)
                roll_result = self.roll_variant_new(spawn_type[0], levelgen)
                
            if roll_result is not None:
                levelgen.bosses.extend(roll_result)
            else:
                levelgen.bosses.extend(self.get_elites_new(levelgen))

        num_uniques = 0
        if 6 <= difficulty <= 10:
            num_uniques = levelgen.random.choice([0, 0, 1])
        if 11 <= difficulty <= 19:
            num_uniques = levelgen.random.choice([1, 1, 2])
        if 19 <= difficulty <= 22:
            num_uniques = levelgen.random.choice([2, 3])
        if 23 <= difficulty < LAST_LEVEL:
            num_uniques = 3

        if 'forcerare' in sys.argv:
            num_uniques = 1

        for i in range(num_uniques):
            tags = set()
            
            for o in levelgen.spawn_options:
                for t in o[0]().tags:
                    tags.add(t)

            spawns = roll_rare_spawn(difficulty, tags, prng=levelgen.random)
            levelgen.bosses.extend(spawns)
        
    def on_levelgen(self, levelgen):
        _, cost = get_spawn_min_max(levelgen.difficulty)
        cost += 1
        
        if not hasattr(levelgen, "num_eliteGates"):
            return
        
        for i in range(levelgen.num_eliteGates):
            spawn_point = levelgen.wall_spawn_points.pop()
            levelgen.level.make_floor(spawn_point.x, spawn_point.y)

            obj = MonsterSpawner(levelgen.gate_elite)
            obj.max_hp = 18 + cost * 12
            obj.description = "EliteGate" # so shielded gates mutator can recognize this is elite
            
            levelgen.level.add_obj(obj, spawn_point.x, spawn_point.y)

class SpawnUniques(Mutator): # not actually used now

    def __init__(self):
        Mutator.__init__(self)
        self.description = "More unique monsters in realms beyond the seventh"

    def on_levelgen_pre(self, levelgen):
        #don't add uniques to Mordred's crib
        if levelgen.difficulty <= 7 or levelgen.difficulty == Level.LAST_LEVEL:
            return
            
        tags = set()
        
        for o in levelgen.spawn_options:
            for t in o[0]().tags:
                tags.add(t)
        spawns = roll_rare_spawn(levelgen.difficulty, tags, prng=levelgen.random)
        levelgen.bosses.extend(spawns)
            
class LessConsumables(Mutator):

    def __init__(self):
        Mutator.__init__(self)
        self.description = "Less consumable items and mana potions in each realm"

    def on_levelgen_pre(self, levelgen):
        if levelgen.difficulty < 3 or levelgen.difficulty == Level.LAST_LEVEL:
            return
            
        if levelgen.difficulty >= 5: #levels 1-4 always have exactly 1 mana potion
            levelgen.num_recharges = levelgen.random.choice([0, 0, 0, 0, 0, 1, 1, 1, 1, 2])
            
        num_consumables = levelgen.random.choice([0, 0, 0, 0, 1, 1, 1, 2])
    
        #gotta completely redo all the items to change any of them
        levelgen.items = []
        for _ in range(num_consumables):
            levelgen.items.append(roll_consumable(prng=levelgen.random))

        for _ in range(levelgen.num_heals):
            levelgen.items.append(heal_potion())

        for _ in range(levelgen.num_recharges):
            levelgen.items.append(mana_potion())
            
        levelgen.random.shuffle(levelgen.items)
            
class FasterShieldGates(Mutator):

    def __init__(self):
        Mutator.__init__(self)
        self.description = "Enemy gates spawn monsters 1 turn faster and have 1 SH, elite gates have 2 SH"
        self.global_triggers[Level.EventOnUnitPreAdded] = self.on_enemy_added
        
    def on_game_begin(self, game):
        if TEST_SHIELD_GATES:
            game.p1.add_item(troll_crown())
            
    def on_enemy_added(self, evt):
        self.modify_unit(evt.unit)

    def on_levelgen(self, levelgen):
        for u in levelgen.level.units:
            self.modify_unit(u)

    def modify_unit(self, unit):
        if not unit.is_lair:
            return
        if unit.team == TEAM_PLAYER:
            return
        
        gate = unit.get_buff(Generator2Buff)
        gate.min_turns -=1
        gate.max_turns -= 1
        gate.turns -= 1
        unit.shields = 1
        
        if unit.description == "EliteGate":
            unit.shields = 2

class PlanarReincarnation(ReincarnationBuff):
    def __init__(self, lives=1):
        ReincarnationBuff.__init__(self, lives=lives)
        self.buff_type = BUFF_TYPE_PASSIVE
    def respawn(self):
        self.owner.level.queue_spell(ReincarnationBuff.respawn(self))
        if self.owner.corruptSpell:
            self.owner.corruptSpell.forced_difficulty += 1
        yield
    def get_tooltip(self):
        return "Reincarnates when killed (%d times)" % self.lives

class StrongerMordred(Mutator):

    def __init__(self):
        Mutator.__init__(self)
        self.description = "Mordred creates more difficult realms, and gains a shield every 2 turns, up to max of 7"
        self.corruptionLevel = 20            
    
    def on_levelgen_pre(self, levelgen):
        if TEST_MORDRED and levelgen.difficulty == 1:
            levelgen.bosses.append(Mordred())

    def on_levelgen(self, levelgen):
        for u in levelgen.level.units:
            self.modify_unit(u)

    def modify_unit(self, unit):
        if not unit.name == "Mordred":
            return

        for b in unit.buffs:
            if type(b) == ReincarnationBuff:
                unit.remove_buff(b)
        unit.apply_buff(PlanarReincarnation(4))
        
        if TEST_MORDRED:
            shieldBuff = ShieldRegenBuff(1,5)
            unit.max_hp = 1
            unit.cur_hp = 1
            unit.shields = 1
            self.corruptionLevel = 2 # I tried 1 but it created multiple Mordreds
        else:
            shieldBuff = ShieldRegenBuff(7,2)
            
        shieldBuff.buff_type = BUFF_TYPE_PASSIVE
        unit.apply_buff(shieldBuff)
        
        for s in unit.spells:
            if type(s) == MordredCorruption:
                s.forced_difficulty = self.corruptionLevel
                unit.corruptSpell = s
                
class EnemyDamageMult(Mutator):

    def __init__(self, mult=2):
        Mutator.__init__(self)
        self.mult = mult
        self.description = "All enemy monsters have %d%% more damage" % round((self.mult-1)*100)
        self.global_triggers[Level.EventOnUnitPreAdded] = self.on_enemy_added

    def on_enemy_added(self, evt):
        if not evt.unit.ever_spawned:
            self.modify_unit(evt.unit)

    def on_levelgen(self, levelgen):
        for u in levelgen.level.units:
            self.modify_unit(u)

    def modify_unit(self, unit):
        if unit.is_lair:
            return
        if unit.team == TEAM_PLAYER:
            return
        
        for spell in unit.spells:
            if hasattr(spell, 'damage'):
                spell.damage = round(spell.damage * self.mult + 0.001)
                
class WizardAndCooldowns(Mutator):

    def __init__(self, cool_mult=0.7, realm_wizard_start = 7, wizard_chance_per_realm = .1):
        Mutator.__init__(self)
        self.cool_mult = cool_mult
        self.realm_wizard_start = realm_wizard_start
        self.wizard_chance_per_realm = wizard_chance_per_realm
        self.description = "All enemy monsters have cooldowns reduced by %d%%, rounded up; enemy wizards may appear in realm %d or later" % (round((1-self.cool_mult)*100), self.realm_wizard_start)
        self.global_triggers[Level.EventOnUnitPreAdded] = self.on_enemy_added

    def on_enemy_added(self, evt):
        if not evt.unit.ever_spawned:
            self.modify_unit(evt.unit)
            
    def on_levelgen_pre(self, levelgen):
        if levelgen.difficulty == Level.LAST_LEVEL:
            return
            
        if TEST_WIZARD_COOLDOWNS:
            wizard = FrostfireWizard()
            wizard.is_boss = True
            levelgen.bosses.append(wizard)
        
        chance = self.wizard_chance_per_realm * (1 + levelgen.difficulty - self.realm_wizard_start)
        if levelgen.random.random() < chance:
            wizard = levelgen.random.choice(RareMonsters.all_wizards)[0]()
            wizard.is_boss = True
            levelgen.bosses.append(wizard)

    def on_levelgen(self, levelgen):            
        for u in levelgen.level.units:
            self.modify_unit(u)

    def modify_unit(self, unit):
        if unit.is_lair or unit.team == TEAM_PLAYER or unit.name == "Mordred":
            return
        
        for spell in unit.spells:
            if hasattr(spell, 'cool_down'):
                spell.cool_down = math.ceil(spell.cool_down * self.cool_mult - 0.01)

class WorseHealPotSpell(HealPotSpell):

    def __init__(self, healMissing, healMax):
        HealPotSpell.__init__(self)
        self.healMissing = healMissing
        self.healMax = healMax

    def cast_instant(self, x, y):
        poison = self.caster.get_buff(Poison)
        if poison:
            self.caster.remove_buff(poison)
        else:
            missing_hp_heal = (self.caster.max_hp - self.caster.cur_hp) * self.healMissing
            max_hp_heal = self.caster.max_hp * self.healMax
            heal_amount = max(missing_hp_heal, max_hp_heal)
            self.caster.deal_damage(-heal_amount, Tags.Heal, self)
            
class PlayerHealingReduction(Mutator):

    def __init__(self, healMissing, healMax):
        Mutator.__init__(self)
        self.healMissing = healMissing
        self.healMax = healMax
        self.description = "Healing potions restore %d%% of your missing HP or %d%% of your max HP, whichever is greater" % (round(self.healMissing*100), round(self.healMax*100))
             
    def worse_heal_potion(self):
        item = heal_potion()
        newDescription = "Drinking this potion restores %d%% of your missing HP or %d%% of your max HP, whichever is greater.\n" % (round(self.healMissing*100), round(self.healMax*100))
        if ANTI_POISON:
            newDescription += "If the user is [poisoned], remove [poison] but does not heal."
        else:
            newDescription += "Cannot be used while poisoned."
        item.description = newDescription
        item.set_spell(WorseHealPotSpell(self.healMissing, self.healMax))
        return item

    def on_game_begin(self, game):
        newPotion = self.worse_heal_potion()
        newPotion.spell.caster = game.p1
        newPotion.spell.owner = game.p1
        game.p1.items[0] = newPotion
        
        if TEST_HEAL_REDUCTION:
            game.p1.cur_hp = 1
            game.p1.add_spell(SoulTax())
            
    def on_levelgen_pre(self, levelgen):            
        if TEST_HEAL_REDUCTION:
            levelgen.items.append(heal_potion())
        
        for i in range(len(levelgen.items)):
            if levelgen.items[i].name == "Healing Potion":
                levelgen.items[i] = self.worse_heal_potion()
            
class EnemyShieldIncrease(Mutator):
    
    def __init__(self, chance=0.3, gateChance = 0.02):
        Mutator.__init__(self)
        self.chance = chance
        self.gateChance = gateChance
        self.description = "Each point of SH on monsters has a %d%% chance of granting +1 SH" % round((self.chance)*100)
        self.global_triggers[Level.EventOnUnitPreAdded] = self.on_enemy_added

    def on_enemy_added(self, evt):
        if not evt.unit.ever_spawned:
            self.modify_unit(evt.unit)
            
    def on_levelgen_pre(self, levelgen):            
        if TEST_SH_INCREASE and levelgen.difficulty == 1:
            for i in range(0, 10):
                levelgen.bosses.append(FloatingEye())
                levelgen.bosses.append(GlassButterfly())

    def on_levelgen(self, levelgen):            
        for u in levelgen.level.units:
            self.modify_unit(u, levelgen.random, levelgen.difficulty)

    def modify_unit(self, unit, prng=None, difficulty = 1):
        if unit.team == TEAM_PLAYER or unit.name == "Mordred":
            return
            
        if not prng:
            prng = random
        
        num_trials = unit.shields
        shieldChance = self.chance
        if unit.is_lair:
            shieldChance = min(self.chance, self.gateChance * (difficulty - 1))
        for _ in range(0, num_trials):
            if prng.random() < self.chance:
                unit.shields += 1
                
class LessSpellPoints(Mutator):
    def __init__(self, realm_mod = 4):
        Mutator.__init__(self)
        self.realm_mod = realm_mod
        self.description = "Every %d realms, there's one less Memory Orb to pick up" % self.realm_mod
        
    def on_levelgen_pre(self, levelgen):
        if levelgen.difficulty % self.realm_mod == 0:
            levelgen.num_xp -= 1
    #well that was easy

#-----------------------------

RogueLikeMutator = RogueLikeMode(STARTING_SPELLS, LEVEL_ONES,  SPELLS_PER_LEVEL, STARTING_SKILLS, SKILLS_PER_LEVEL, SKILL_DISCOUNT)
TrialList = [Trial("Roguelike Mode", [RogueLikeMutator])]

def addCumulativeTrial(newMutator):
    newTrial = copy.deepcopy(TrialList[-1])
    ascensionNum = len(TrialList)
    newTrial.name = "Rogue Challenge %d" %ascensionNum
    
    for m in newTrial.mutators:
        if type(m) == type(newMutator):
            newTrial.mutators.remove(m)
    
    # Even with bugfixes only 6 lines of text can show up for each trial
    # I could modify the trial screen even more so all the text can show up
    # but seems easier to just show only the last modifier to be added
    if ascensionNum == 2:
        newTrial.mutators[1].description = "Same modifiers as all the previous Rogue Challenges, plus...\n"   
        
    if ascensionNum > 2:
        newTrial.mutators[2].description = newMutator.description
        newMutator.description = ""
        
    newTrial.mutators.append(newMutator)
    TrialList.append(newTrial)
    
"""
        (1, 1), # 1
        (1, 1), # 2 - more elites (+1 gate)
        (1, 2), # 3 
        (1, 3), # 4 - more elites
        (2, 3), # 5 - generators increase
        (2, 4), # 6 - chance of unique
        (2, 4), # 7 - (10% wizard)
        (2, 4), # 8
        (2, 4), # 9 - more elites (slightly more, and change one gate to an elite type )
        (3, 4), # 10 - generators increase
        (3, 5), # 11 - guaranteed unique, harder uniques
        (3, 5), # 12 
        (3, 5), # 13 - (another gate changed to elite)
        (4, 5), # 14
        (4, 5), # 15 - (+1 gate)
        (4, 6), # 16
        (5, 6), # 17
        (5, 6), # 18 - 
        (5, 6), # 19 - guaranteed 2 unique
        (5, 7), # 20 - generators increase, harder uniques
        (5, 7), # 21   
        (5, 7), # 22 - (another gate changed to elite)
        (6, 8), # 23 - guaranteed 3 unique
        (7, 8), # 24
"""
   
addCumulativeTrial(MoreGates(realm_list=[2,15]))
addCumulativeTrial(MonsterHordes(10,20,10,6))
addCumulativeTrial(EnemyDamageMult(1.15))
addCumulativeTrial(EliteSpawnsAndGates(realm_start = 9, realm_step = 2, max_avg_elites = 6))
addCumulativeTrial(LessConsumables())
if not MORDRED_OVERHAULED:
    addCumulativeTrial(StrongerMordred())
addCumulativeTrial(MonsterHPMultFraction(1.3))
addCumulativeTrial(FasterShieldGates())
addCumulativeTrial(PlayerHealingReduction(healMissing = .6, healMax = .4)) 
addCumulativeTrial(EnemyShieldIncrease(chance=0.3, gateChance = 0.02))
addCumulativeTrial(WizardAndCooldowns(cool_mult=0.7, realm_wizard_start = 7, wizard_chance_per_realm = .1))
addCumulativeTrial(EnemyDamageMult(1.3))
addCumulativeTrial(LessSpellPoints(realm_mod = 4))

#and for the true masochists, here's one with all the nerfs undone
UnfairMutators = [MoreGates(realm_list=[2,8,15]), 
                   WizardAndCooldowns(cool_mult=0.7, realm_wizard_start = 7, wizard_chance_per_realm = 1),
                   LessSpellPoints(realm_mod = 3)]

UnfairTrial = copy.deepcopy(TrialList[-1])
UnfairTrial.name = "Unfair Challenge"
for u in UnfairMutators:
    for m in UnfairTrial.mutators:
        if type(m) == type(u):
            UnfairTrial.mutators.remove(m)
    u.description = ""
    UnfairTrial.mutators.append(u)
    
UnfairTrial.mutators[1].description = "Same modifiers as all the previous Rogue Challenges, plus...\n"  
UnfairTrial.mutators[2].description = "All nerfs I've made to Rogue Challenges are reverted. This is REALLY HARD"
TrialList.append(UnfairTrial)

all_trials.extend(TrialList)