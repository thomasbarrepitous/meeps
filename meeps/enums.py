from enum import Enum


class ItemTier(str, Enum):
    """Item tier classifications in League of Legends."""

    STARTER = "Starter"
    BASIC = "Basic"
    EPIC = "Epic"
    LEGENDARY = "Legendary"
    MYTHIC = "Mythic"


class ChampionResource(str, Enum):
    """Resource types used by League of Legends champions."""

    MANA = "Mana"
    ENERGY = "Energy"
    FURY = "Fury"
    FLOW = "Flow"
    RAGE = "Rage"
    HEAT = "Heat"
    FEROCITY = "Ferocity"
    SHIELD = "Shield"
    COURAGE = "Courage"
    GRIT = "Grit"
    BLOODTHIRST = "Bloodthirst"
    NONE = "None"


class ChampionAttribute(str, Enum):
    """Champion class/attribute classifications."""

    FIGHTER = "Fighter"
    TANK = "Tank"
    MAGE = "Mage"
    ASSASSIN = "Assassin"
    MARKSMAN = "Marksman"
    SUPPORT = "Support"


class Role(str, Enum):
    """In-game roles/positions in League of Legends."""

    TOP = "Top"
    JUNGLE = "Jungle"
    MID = "Mid"
    BOT = "Bot"
    SUPPORT = "Support"
