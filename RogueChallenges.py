#--------------------------
#You can change the parameters of Roguelike Mode here.
#--------------------------
#The number of spells you start with (default is 14). Set this to -1 to start with all spells
STARTING_SPELLS = 14
#The number of starting spells that are level 1 (default is 2)
LEVEL_ONES = 2
#The number of spells gained on each level (default is 2)
SPELLS_PER_LEVEL = 2
#The number of skills you start with (default 7). Set this to -1 to start with all skills
STARTING_SKILLS = 7
#The number of skills gained on each level (default is 1)
SKILLS_PER_LEVEL = 1
#The cost discount for all skills (default is 0)
SKILL_DISCOUNT = 0

from LevelGen import *
from CommonContent import *
from Consumables import *
from Mutators import *
from RiftWizard import *
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
                    
    for func_name, func in [(key, value) for key, value in locals().items() if callable(value)]:
        if hasattr(cls, func_name):
            setattr(cls, func_name, func)

if not BUG_FIXED:
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
        self.description = "Start with %d spells and %d skills\nGain %d new spells and %d new skills after each completed level" % (self.numspells, self.numskills, self.num_newspells, self.num_newskills)
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
        self.triggered = False #now ready to grant new spells when the level is cleared
        
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
    
    def __init__(self):
        Mutator.__init__(self)
        self.description = "Each level has additional monster generators"

    def on_levelgen_pre(self, levelgen):
        #dont add gates to Mordred's place
        if levelgen.difficulty == 1 or levelgen.difficulty == Level.LAST_LEVEL:
            return
        
        moreGateNum = 1 if levelgen.difficulty < 8 else 2 if levelgen.difficulty < 15 else 3
        levelgen.num_generators += moreGateNum
             
class MonsterHordes(Mutator):

    def __init__(self, min_monsters, max_monsters, min_horde, max_horde):
        Mutator.__init__(self)
        self.min_monsters = min_monsters
        self.max_monsters = max_monsters
        self.min_horde = min_horde
        self.max_horde = max_horde
        self.description = "All levels have more monsters. Areas with relatively easier monsters have many more of them"
        
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

    def __init__(self, min_monsters, max_monsters):
        Mutator.__init__(self)
        self.min_monsters = min_monsters
        self.max_monsters = max_monsters
        self.description = "Each level beyond level 12 has %d-%d extra elite monsters; later levels have elite gates" % (self.min_monsters, self.max_monsters)

    def on_levelgen_pre(self, levelgen):
        # don't add more elites to Mordred's pad
        if (levelgen.difficulty <= 12 or levelgen.difficulty == Level.LAST_LEVEL) and not TEST_ELITE_GATES:
            return
            
        levelgen.num_eliteGates = 0 if levelgen.difficulty < 15 else 1 if levelgen.difficulty < 18 else 2 if levelgen.difficulty < 22 else 3
        levelgen.num_generators -= levelgen.num_eliteGates
    
        _, level = get_spawn_min_max(levelgen.difficulty)
        level += 1

        num_elites = levelgen.random.randint(self.min_monsters, self.max_monsters)

        options = [(s, l) for s, l in Monsters.spawn_options if l == level]
        spawner = levelgen.random.choice(options)[0]
        
        levelgen.chosen_elite = spawner #for the purposes of elite gate mutator
        units = [spawner() for i in range(num_elites)] 
        levelgen.bosses = units + levelgen.bosses     
        
    def on_levelgen(self, levelgen):
        _, cost = get_spawn_min_max(levelgen.difficulty)
        cost += 1
        
        if not hasattr(levelgen, "num_eliteGates"):
            return
        
        for i in range(levelgen.num_eliteGates):
            spawn_point = levelgen.wall_spawn_points.pop()
            levelgen.level.make_floor(spawn_point.x, spawn_point.y)

            obj = MonsterSpawner(levelgen.chosen_elite)
            obj.max_hp = 18 + cost * 12
            obj.description = "EliteGate" # so shielded gates mutator can recognize this is elite
            
            levelgen.level.add_obj(obj, spawn_point.x, spawn_point.y)

class SpawnUniques(Mutator): # not actually used now

    def __init__(self):
        Mutator.__init__(self)
        self.description = "More unique monsters in levels beyond the seventh"

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
        self.description = "Less consumable items and mana potions in each level"

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

    def __init__(self, mult=0.7):
        Mutator.__init__(self)
        self.mult = mult
        self.description = "All enemy monsters have cooldowns reduced by %d%%, rounded up; enemy wizards appear after level 6" % round((1-self.mult)*100)
        self.global_triggers[Level.EventOnUnitPreAdded] = self.on_enemy_added

    def on_enemy_added(self, evt):
        if not evt.unit.ever_spawned:
            self.modify_unit(evt.unit)
            
    def on_levelgen_pre(self, levelgen):            
        if TEST_WIZARD_COOLDOWNS:
            wizard = FrostfireWizard()
            wizard.is_boss = True
            levelgen.bosses.append(wizard)
            
        if levelgen.difficulty > 6:
            wizard = self.random.choice(RareMonsters.all_wizards)[0]()
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
                spell.cool_down = math.ceil(spell.cool_down * self.mult - 0.01)

class WorseHealPotSpell(HealPotSpell):
    def cast_instant(self, x, y):
        poison = self.caster.get_buff(Poison)
        if poison:
            self.caster.remove_buff(poison)
        else:
            self.caster.deal_damage(self.caster.cur_hp-self.caster.max_hp, Tags.Heal, self)
            
class PlayerHealingReduction(Mutator):

    def __init__(self, healReducPercent=30):
        Mutator.__init__(self)
        self.healReducPercent = healReducPercent
        self.description = "Healing potions restore %d%% of your missing HP, and you restore %d%% less HP with all other healing effects"  % (100-healReducPercent, healReducPercent)
        
    def worse_heal_potion(self):
        item = heal_potion()
        newDescription = "Drinking this potion restores 100%% of the drinker's missing HP.\n(Restores %d%% of missing HP after the healing reduction.)\n" %(100-self.healReducPercent)
        if ANTI_POISON:
            newDescription += "If the user is [poisoned], remove [poison] but does not heal."
        else:
            newDescription += "Cannot be used while poisoned."
        item.description = newDescription
        item.set_spell(WorseHealPotSpell())
        return item

    def on_game_begin(self, game):
        game.p1.apply_buff(HealReductionCurse(self.healReducPercent))
        newPotion = self.worse_heal_potion()
        newPotion.spell.caster = game.p1
        newPotion.spell.owner = game.p1
        game.p1.items[0] = newPotion
        
        if TEST_HEAL_REDUCTION:
            game.p1.cur_hp = 5
            game.p1.add_spell(SoulTax())
            
    def on_levelgen_pre(self, levelgen):            
        if TEST_HEAL_REDUCTION:
            if levelgen.difficulty == 1:
                levelgen.bosses.append(Ogre())
            else:
                levelgen.items.append(heal_potion())
        
        for i in range(len(levelgen.items)):
            if levelgen.items[i].name == "Healing Potion":
                levelgen.items[i] = self.worse_heal_potion()
        
class HealReductionCurse(Level.Buff):

    def __init__(self, healReducPercent):
        Level.Buff.__init__(self)
        self.buff_type = Level.BUFF_TYPE_PASSIVE
        self.resists[Tags.Heal] = healReducPercent
            
class EnemyShieldIncrease(Mutator):
    
    def __init__(self, chance=0.3):
        Mutator.__init__(self)
        self.chance = chance
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
            self.modify_unit(u, levelgen.random)

    def modify_unit(self, unit, prng=None):
        if unit.is_lair or unit.team == TEAM_PLAYER or unit.name == "Mordred":
            return
            
        if not prng:
            prng = random
        
        num_trials = unit.shields
        for _ in range(0, num_trials):
            if prng.random() < self.chance:
                unit.shields += 1
                
class LessSpellPoints(Mutator):
    def __init__(self):
        Mutator.__init__(self)
        self.description = "1 less SP in every third level"
        
    def on_levelgen_pre(self, levelgen):
        if levelgen.difficulty % 3 == 0:
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
        (2, 4), # 7 - (guaranteed wizard)
        (2, 4), # 8 - (+1 gate)
        (2, 4), # 9 - more elites
        (3, 4), # 10 - generators increase
        (3, 5), # 11 - guaranteed unique, harder uniques
        (3, 5), # 12 
        (3, 5), # 13 - (more elite)
        (4, 5), # 14
        (4, 5), # 15 - (+1 gate)(change one gate to the elite type introduced in #13)
        (4, 6), # 16
        (5, 6), # 17
        (5, 6), # 18 - (another gate changed to elite)
        (5, 6), # 19 - guaranteed 2 unique
        (5, 7), # 20 - generators increase, harder uniques
        (5, 7), # 21   
        (5, 7), # 22 - (another gate changed to elite)
        (6, 8), # 23 - guaranteed 3 unique
        (7, 8), # 24
"""
   
addCumulativeTrial(MoreGates())
addCumulativeTrial(MonsterHordes(10,20,10,6))
addCumulativeTrial(EnemyDamageMult(1.15)) 
addCumulativeTrial(EliteSpawnsAndGates(5,7))
addCumulativeTrial(LessConsumables())
if not MORDRED_OVERHAULED:
    addCumulativeTrial(StrongerMordred()) 
addCumulativeTrial(MonsterHPMultFraction(1.3))    
addCumulativeTrial(FasterShieldGates())
addCumulativeTrial(PlayerHealingReduction(35)) 
addCumulativeTrial(EnemyShieldIncrease(0.3))
addCumulativeTrial(WizardAndCooldowns(0.7))
addCumulativeTrial(EnemyDamageMult(1.3))
addCumulativeTrial(LessSpellPoints())

all_trials.extend(TrialList)