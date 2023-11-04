To install this mod, click on the green Code button on this page, then "Download ZIP". Rename the "RogueChallenges-main" folder to "RogueChallenges" and then put it into your mods folder in your RiftWizard folder.

This mod requires AAA_Loader by Bord Listian: https://github.com/DaedalusGame/AAA_Loader
Visit the above link and install it the same way you install this mod, except that you rename the "AAA_Loader-master" folder to "AAA_Loader" before putting it into the mods folder.

Here's some other mods by JohnSolaris that are not required but are highly recommended:

Bugfixes: https://github.com/jh1993/Bugfixes
No More Scams: https://github.com/jh1993/NoMoreScams
Underused Options: https://github.com/jh1993/UnderusedOptions

Feel free to open RogueChallenges.py and edit the parameters near the top if you want to change how Roguelike Mode works, or disable it.

---------------------------------------------------------------------------------------------------

This mod adds many additonal archmage trials. All of them limit your spells and skills similarly to the RogueLikeMode mod. Each successive challenge have all the modifiers of all the previous challenges, similarly to Ascensions in Slay the Spire, Covenent in Monster Train, Eclipse in Risk of Rain 2, etc. All of them are succinctly summarized on the Archmage Trials screen ingame, but if you want to know all the little details then here they are.

----- Roguelike Mode:
--- Start with 14 spells and 7 skills. Gain 2 new spells and 1 new skill after each completed realm.

- You always start with two spells that cost 1 SP.
- Unlike previous versions, you get the new spells and skill immediately when you defeat all the enemies, so you can see what new things you got before entering a new realm.
- There is no discount on skills, by default.
- Again, you can open RogueChallenges.py and edit the parameters near the top if you want to change how many spells and skills you start with, or how many you gain after each realm, or even bring back the skill discount. You can even disable the spell and skill restrictions entirely if you want to try the following trials without them.

----- Rogue Challenge 1:
--- Each realm has additional monster generators.

- Realm 2 onward has one additional gate.
- Realm 8 onward has another additional gate.
- Realm 15 onward has yet another gate.

----- Rogue Challenge 2:
--- All realms have more monsters. Realms with relatively easier monsters have many more of them.

- Usually all realms have 5-20 "normal" monsters.
- If these monsters are at the maximum possible level relative to the player's progress, the amount is increased to 10-20.
- If these monsters are instead at the minimum possible level, the amount is increased to 20-26.
- The final amount scales proporionally if the monsters have level in between the maximum or minimum.

----- Rogue Challenge 3:
--- All enemy monsters have 15% more damage.

- This only affects the damage from spells. Passive effects like Efreet damage aura remain the same.
- The damage is always rounded to the nearest whole number. A spell with 3 damage will still remain at 3, but a spell with 4 damage will be increased to 5.

----- Rogue Challenge 4:
--- Realms 9 and beyond have extra elite monsters and elite gates

- Elite monsters are variant monsters or monsters that are one level higher than the maximum "normal" monster level that can appear in a rift.
- Realm 9 onward has 0-2 extra elite monsters, and every 2 realms there is an additional elite monster, until it maxes at 5-7
- Elite gates have higher HP than normal gates and spawn these more difficult additional monsters.
- Starting at realm 9, for the rest of the game all realms have one normal gate replaced by an elite gate.
- This replacement is increased to two gates at realm 15, and increased to three gates at realm 22.
- I recommend avoiding rifts with three Bone Shambler Megalith gates spread out over the map.

----- Rogue Challenge 5:
--- Less consumable items and mana potions in each realm.

- Normally after realm 4, each realm has a 1/6 chance of containing two mana potions and a 2/6 chance of one mana potion. This is changed to a 1/10 chance of two mana potions and a 4/10 chance of one mana potion. The chance of getting no mana potions is unchanged.
- Normally after realm 2, each realm has a 1/8 chance of three consumables, a 1/8 chance of two consumables, and a 2/8 chance of one consumable. This is changed to a 1/8 chance of two consumables and a 3/8 chance of one consumable. The chance of getting no consumables is unchanged.

----- Rogue Challenge 6:
--- Mordred creates more difficult realms, and gains a shield every 2 turns, up to max of 7.

- Normally Mordred's Planar Interposition creates level 19 realms. This is increased to level 20 realms at the start. In addition, every Reincarnation life he loses increased the level of Planar Interposition realms by 1. After losing all his extra lives he will create level 24 realms.
- Try saving some consumable items for Mordred's last few lives, since getting suddenly surrounded by very high level monsters can get dicey.
- If you have JohnSolaris' Mordred Overhauled mod, this challenge is skipped since it is incompatible with that mod. Rogue Challenge 7 below would be displayed as Rogue Challenge 6 instead, etc.

----- Rogue Challenge 7:
--- All enemy monsters have 30% more HP.

- HP is rounded to the nearest whole number.
- This does not affect gates.
- This causes Bone Splinters that would normally have 8 hp, to show up as 10 hp Bone Shamblers instead, which changes their sprite. It doesn't have any adverse gameplay effects though.

----- Rogue Challenge 8:
--- Gates spawn units 1 turn faster and have 1 SH, elite gates have 2 SH

- Normally gates create a monster every 7-10 turns. With this change they now create monsters every 6-9 turns.
- Elite gates are the gates created by Rogue Challenge 4 that create stronger monsters.
- Be very careful about realms with multiple war banners as the monster count can really get out of hand quickly.

----- Rogue Challenge 9:
--- Healing potions restore 60% of your missing HP or 40% of your max HP, whichever is greater.

- You still get the most value from your healing potions by waiting until you have very low HP remaining.
- If you want to return to full HP for safety, you can just use two healing potions.

----- Rogue Challenge 10:
--- Each point of SH on monsters has a 30% chance of granting +1 SH.

- Each SH point decides whether to grant another SH completely independently of the other SH and other monsters.
- Enemies with SH could end up with no additional SH. Or they could end up with double SH, if they are very lucky.
- As an example, a glass golem normally has 2 SH. With this challenge, each different glass golem has a 49% chance of 2 SH, a 42% chance of 3 SH, and a 9% chance of 4 SH.
- This can increase SH above 20. I'm really sorry about the glass butterflies.

----- Rogue Challenge 11:
--- All enemy monsters have cooldowns reduced by 30%, rounded up; enemy wizards appear after realm 6.

- The smallest cooldown that is affected is 4, which is changed to 3 by this challenge.
- The wizards that can appear are the same ones that appear in Wizard Warlords trial.

----- Rogue Challenge 12:
--- All enemy monsters have 30% more damage.

- This replaces the effect of Rogue Challenge 3.
- Again the damage only affects spells, and rounds to the nearest whole number.

----- Rogue Challenge 13:
--- 1 less SP in every third realm.

- Affects realms 3, 6, 9, 12, etc.
- I put this challenge last since its has the greatest difficulty/interesting ratio.

---------------------------------------------------------------------------------------------------

Thank you very much to all of the following people. Without their contributions to the community this mod would not have existed:

dylanwhite, for making Rift Wizard (:having_a_ball:)
Mike, for the original roguelike mode mod
Anti-Tank Guided Missile, for creating and maintaining the BetterRogue mod
Bord Listian, for AAA Loader, so even a dummy like me can get mods to work
JohnSolaris, for his many excellent mods that both improve the gameplay of Rift Wizard have many excellent code samples that I learned from
jorbs (https://www.twitch.tv/jorbs), for very briefly playing Rift Wizard on his stream and thus reigniting my interest for this game in 2023