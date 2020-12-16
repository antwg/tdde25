from typing import Union, Sequence, Callable

from library import *

from scai_backbone import siege_tanks_TYPEIDS

from workplace import *


# ZW
class Troop:
    """A collection of military units."""
    __target: Point2D  # Common target for all units in troop

    # ___Job_list___
    marines: List[Unit]  # All marines in this troop
    tanks: List[Unit]  # All siege tanks in this troop
    bunkers: Dict[Unit, List[Unit]]  # All bunkers in this troop and the marines within
    others: List[Unit]  # All other units in this troop
    # --------------

    # Class constants
    marines_capacity: int = 8  # How many marines a defending troop is asking for
    tanks_capacity: int = 2  # How many tanks a defending troop is asking for
    marines_capacity_atk: int = 12  # How many marines an attacking troop is asking for
    tanks_capacity_atk: int = 4  # How many tanks a attacking troop is asking for

    target_radius: int = 7  # How close a unit must be to a target to be there

    leash_radius: int = 4  # How close a unit must be to leader when leash is active
    leash_stretch: int = 5  # How far away a unit can be from leader at most when leash is active

    under_attack_wait: int = 200  # How many on_steps the troop wait before
    # declaring not under_attack (if not attacked)

    # Unitlist for those in special states
    not_reached_target: List[Unit]  # All units that have not reached target
    already_idle: List[Unit]  # All units that have been noticed as idle

    tanks_siege: List[Unit]  # All siege tanks in siegemode in this troop
    repair_these: Dict[Unit, List[Unit]]  # All damaged repairable units and who are repairing it

    foes_to_close: List[Unit]  # All foes that are within proximity

    # Statehandlers
    __order: Callable  # A function that moves unit as demanded
    under_attack: int  # If troop is under attack or not and how many on_steps it will remain
    is_attackers: bool  # If troop is attacking or not
    prohibit_refill: bool  # - If troop will request more troops or not

    # Follow leader
    __leash: Union[Callable, None]  # A function that moves unit towards leader position
    leader: Union[Unit, None]  # When marching as one, follow this unit

    # (Attacking) Troop targets
    enemy_bases: List[BaseLocation] = []  # All potential enemy bases for attackers to attack
    enemy_structures: Dict[Point2D, bool] = {}  # All known enemy structures
    # that needs to be destroyed to win and if they're visible or not

    # ---------- EVENTS ----------
    # These are functions triggered by different events. Most are
    # triggered from MyAgent.

    def __init__(self, position: Point2D, is_attackers: bool = False):
        """Called when a new troop is being created. Note that no units are
        required for making a troop, rather it is why they need to be created.
        """
        self.__order = self.__march_order
        self.marines = []
        self.tanks = []
        self.tanks_siege = []
        self.bunkers = {}
        self.others = []
        self.not_reached_target = []
        self.already_idle = []
        self.under_attack = 0
        self.is_attackers = is_attackers
        self.prohibit_refill = False
        self.enemy_bases = []
        self.__leash = None
        self.leader = None
        self.foes_to_close = []
        self.repair_these = {}

        if is_attackers:
            self.marines_capacity = self.marines_capacity_atk
            self.tanks_capacity = self.tanks_capacity_atk

        self.set_target(position)

    def on_step(self, bot: IDABot):
        """Called each on_step() of IDABot."""
        # Remove all non idle units from the idle list
        self.already_idle = list(filter(
            lambda unit: unit.is_idle, self.already_idle))

        if self.under_attack:
            self.under_attack -= 1

            # If no foe is close by or troop not damaged for a while, then calm down
            if not self.foes_to_close or self.under_attack == 0:
                self.under_attack = 0
                self.foes_to_close = []
                self.already_idle = []
                self.not_reached_target = self.get_units()

            # If not moving (shouldn't attack) attack attackers.
            elif self.__order != self.__move_order:
                if not self.foes_to_close:
                    pass
                else:
                    for unit in self.get_units():
                        if not(unit.has_target and unit.target in self.foes_to_close):
                            targeted_foe = self.get_suitable_to_close_foe_for(unit)
                            if targeted_foe:
                                unit.attack_unit(targeted_foe)
        elif self.__leash:
            left_behind = False
            for unit in self.get_units():
                if unit != self.leader and not self.nearby_target(unit):
                    if self.nearby_leader(unit):
                        if unit.has_target and unit.target == self.leader:
                            self.__order(unit)
                    else:
                        if not unit.has_target or unit.target != self.leader:
                            self.__leash(unit)
                        if self.losing_leader(unit):
                            left_behind = True

            if not self.leader.is_idle and left_behind:
                self.leader.stop()
            elif self.leader.is_idle and not left_behind:
                self.__order(self.leader)

        if not self.is_attackers and not self.under_attack:
            if not self.bunkers.keys():
                self.build_bunker(bot, self.target_pos)

    def on_idle(self, unit: Unit, bot: IDABot):
        """Called each time a member is idle."""
        # if unit.unit_type.unit_typeid in repairer_TYPEIDS and self.repair_these:
        #     self.have_unit_repair(unit)
        if unit not in self.already_idle:
            self.already_idle.append(unit)
            self.on_just_idle(unit, bot)

    def on_just_idle(self, unit: Unit, bot: IDABot): 
        """Called each time a member just became idle."""
        if self.under_attack and self.__order != self.__move_order:
            targeted_foe = self.get_suitable_to_close_foe_for(unit)
            if targeted_foe:
                unit.attack_unit(targeted_foe)
            else:
                print(unit, " just panicked!")

        elif self.nearby_target(unit):
            if unit in self.not_reached_target:
                self.not_reached_target.remove(unit)
                self.on_member_reach_target(unit, bot)
        elif not self.nearby_target(unit):
            if unit in self.tanks_siege:
                unit.ability(ABILITY_ID.MORPH_UNSIEGE)
                self.tanks_siege.remove(unit)
            elif not self.__leash or not self.leader == unit:
                self.unit_execute_order(unit)

    def on_member_reach_target(self, unit: Unit, bot: IDABot):
        """A member reaches target for first time."""
        if self.have_all_reached_target and self.prohibit_refill and self.is_attackers:
            if self.target_pos in self.enemy_structures:
                del self.enemy_structures[self.target_pos]

            self.try_to_win(bot)

        elif unit in self.tanks and unit not in self.tanks_siege \
                and not (unit.has_target and unit.target == PLAYER_ENEMY):
            unit.ability(ABILITY_ID.MORPH_SIEGEMODE)
            self.tanks_siege.append(unit)
        elif unit in self.marines:
            for bunker, occupants in self.bunkers.items():
                if len(occupants) < 4:
                    unit.right_click(bunker)
                    self.bunkers[bunker].append(unit)

    def on_damaged_member(self, unit: Unit, bot: IDABot):
        """A member takes damage (might be dead)."""
        self.need_repair(unit)

        for foe in bot.get_all_units():
            if foe.player != PLAYER_ENEMY:
                continue

            if foe not in self.foes_to_close \
                    and max(foe.unit_type.attack_range + foe.radius + unit.radius,
                            10)**2 > foe.position.squared_dist(unit.position):
                self.foes_to_close.append(foe)

        if not self.under_attack:
            if not self.foes_to_close:
                bot.try_to_scan(unit.position)

        self.under_attack = self.under_attack_wait

    # --------- ORDERS ---------
    # Handles how units advance to target and how the execution of it.

    def __march_order(self, unit: Unit) -> None:
        """Have a member attack given position."""
        unit.attack_move(self.__target)

    def __move_order(self, unit: Unit) -> None:
        """Moves a unit to given position."""
        unit.move(self.__target)

    def __attack_order(self, unit: Unit) -> None:
        """Have a unit attack target."""
        unit.attack_unit(self.__target)

    def __follow_leader(self, unit: Unit) -> None:
        """Have unit follow leader."""
        unit.right_click(self.leader)

    def march_units(self, position: Point2D) -> None:
        """Have troop and all its units attack given position."""
        self.__leash = None
        self.__order = self.__march_order
        self.set_target(position)
        self.all_execute_orders()

    def march_together_units(self, position: Point2D) -> None:
        """Have troop and all its units attack given position but stay close to leader."""
        self.__leash = self.__follow_leader
        self.__order = self.__march_order
        self.set_target(position)
        self.all_execute_orders()

    def move_units(self, position: Point2D) -> None:
        """Moves troop and all its units to given position."""
        self.__leash = None
        self.__order = self.__move_order
        self.set_target(position)
        self.all_execute_orders()

    def attack_units(self, target: Unit) -> None:
        """Have all units attack given unit."""
        self.__leash = self.__follow_leader
        self.__order = self.__attack_order
        self.set_target(target)
        self.all_execute_orders()

    def defend_workplace(self, work: Workplace, bot: IDABot) -> None:
        """Have units defend given workplace from enemies."""
        # TODO: Not yet fully implemented, fix or remove
        for unit in bot.get_all_units():
            if unit.player == PLAYER_ENEMY \
                    and work.within_proximity(unit.position):
                self.foes_to_close.append(unit)

    def all_execute_orders(self) -> None:
        """Have all members execute order."""
        for trooper in self.get_units():
            self.__order(trooper)

    def unit_execute_order(self, trooper: Unit):
        """Have a member execute order."""
        self.__order(trooper)

    # ---------- BASIC HANDLERS ----------
    # Handles basic functions as adding and removing units

    def add(self, units: Union[Unit, Sequence[Unit]]) -> None:
        """Adds unit(s) to troop."""
        if isinstance(units, Unit):
            units = [units]

        for unit in units:
            if unit.unit_type.is_building and self.is_attackers:
                continue

            if unit.unit_type.unit_typeid == UNIT_TYPEID.TERRAN_MARINE:
                self.marines.append(unit)
            elif unit.unit_type.unit_typeid in siege_tanks_TYPEIDS:
                self.tanks.append(unit)
                if unit.unit_type.unit_typeid == UNIT_TYPEID.TERRAN_SIEGETANKSIEGED:
                    self.tanks_siege.append(unit)
            elif unit.unit_type.unit_typeid == UNIT_TYPEID.TERRAN_BUNKER:
                if self.nearby_target(unit):
                    self.bunkers[unit] = []
                    self.have_soldiers_enter(unit)
                else:
                    continue
            else:
                self.others.append(unit)

            self.not_reached_target.append(unit)

            if self.satisfied and self.is_attackers:
                self.prohibit_refill = True

            if not unit.unit_type.is_building:
                self.try_assigning_leader(unit)

    def remove(self, unit: Unit) -> None:
        """Handles units that are to be removed from troop."""
        if unit in self.already_idle:
            self.already_idle.remove(unit)
        if unit in self.not_reached_target:
            self.not_reached_target.remove(unit)
        for bunker, occupants in self.bunkers.items():
            if unit in occupants:
                bunker.ability(ABILITY_ID.UNLOADALL)
                self.bunkers[bunker] = []

        if unit in self.marines:
            self.marines.remove(unit)
        elif unit in self.tanks:
            self.tanks.remove(unit)
            if unit in self.tanks_siege:
                unit.ability(ABILITY_ID.MORPH_UNSIEGE)
                self.tanks_siege.remove(unit)
        elif unit in self.bunkers:
            if unit.is_alive and self.bunkers[unit]:
                unit.ability(ABILITY_ID.UNLOADALL)
            del self.bunkers[unit]
        elif unit in self.others:
            self.others.remove(unit)

        if unit == self.leader:
            self.leader = None
            for unit in self.get_units():
                self.try_assigning_leader(unit)

    def get_units(self) -> List[Unit]:
        """Get all units in troop."""
        return (self.marines
                + self.tanks
                + self.others
                + list(self.bunkers.keys()))

    def has_unit(self, unit: Unit) -> bool:
        """Check if troop has unit."""
        if unit in self.get_units():
            return True
        else:
            return False

    def set_target(self, target: Union[Point2D, Unit]):
        """Sets target of troop."""
        self.__target = target
        self.not_reached_target = self.get_units()
        self.already_idle = []

        for bunker in self.bunkers:
            if not self.nearby_target(bunker):
                self.remove(bunker)

    def flush_troop(self) -> List[Unit]:
        """Remove and return all units in troop."""
        units = self.get_units().copy()
        free = []
        while units:
            unit = units.pop()
            if not unit.unit_type.is_building:
                self.remove(unit)
                free.append(unit)
        return free

    # ---------- MISC ----------
    # Other needed functions.

    def build_bunker(self, bot: IDABot, location) -> None:  # AW
        """Builds a bunker when necessary."""
        bunker = UnitType(UNIT_TYPEID.TERRAN_BUNKER, bot)
        workplace = closest_workplace(location)

        if can_afford(bot, bunker) \
                and not currently_building(bot, UNIT_TYPEID.TERRAN_BUNKER) \
                and bot.have_one(UNIT_TYPEID.TERRAN_BARRACKS) \
                and not workplace.is_building_unittype(bunker) \
                and not self.bunkers:
            position = bot.building_placer.get_build_location_near(
                location.to_i(), bunker)
            workplace.have_worker_construct(bunker, position)

    # ZW
    def nearby_target(self, at: Union[Unit, Point2D]) -> bool:
        """Check if a unit is nearby target."""
        if isinstance(at, Unit):
            return at.position.dist(self.target_pos) <= self.target_radius
        elif isinstance(at, Point2D):
            return at.dist(self.target_pos) <= self.target_radius
        else:
            raise Exception("Can't do that!")

    # ZW
    def nearby_leader(self, at: Union[Unit, Point2D]) -> bool:
        """Check if a unit is nearby leader."""
        if isinstance(at, Unit):
            return at.position.squared_dist(self.leader.position) \
                   <= self.leash_radius**2
        elif isinstance(at, Point2D):
            return at.squared_dist(self.leader.position) \
                   <= self.leash_radius**2
        else:
            raise Exception("Can't do that!")

    # ZW
    def losing_leader(self, at: Union[Unit, Point2D]) -> bool:
        """Check if a unit is not nearby (with margin) leader."""
        if isinstance(at, Unit):
            return at.position.squared_dist(self.leader.position) \
                   > (self.leash_radius + self.leash_stretch) ** 2
        elif isinstance(at, Point2D):
            return at.squared_dist(self.leader.position) \
                   > (self.leash_radius + self.leash_stretch) ** 2
        else:
            raise Exception("Can't do that!")

    def try_assigning_leader(self, unit: Unit) -> None:
        """Try to set new leader to given unit for troop."""
        if not unit.unit_type.is_building:
            if not self.leader:
                self.leader = unit
            elif self.leader.is_flying == unit.is_flying:
                if unit.radius > self.leader.radius:
                    self.leader = unit
            elif not unit.is_flying:
                self.leader = unit

    # AW
    def have_soldiers_enter(self, bunker: Unit) -> None:
        """Have marines enter bunker."""
        for marine in self.marines[:4]:
            marine.right_click(bunker)
            self.bunkers[bunker].append(marine)

    def get_suitable_to_close_foe_for(self, unit: Unit) -> Union[Unit, None]:
        """Returns a suitable target for units if they're defending themself
        from attackers."""
        best_aggressor = get_closest(
            [(foe.position, foe) for foe in self.foes_to_close
             if not foe.unit_type.is_building],
            unit.position)
        if best_aggressor:
            return best_aggressor
        else:
            return get_closest(
                [(foe.position, foe) for foe in self.foes_to_close
                 if foe.unit_type.is_building],
                unit.position)

    def need_repair(self, unit: Unit) -> None:
        """Have a unit request repairs and remember this."""
        if unit not in self.repair_these:
            self.repair_these[unit] = []

    def have_unit_repair(self, unit: Unit) -> None:
        """Try to have the unit repair a target that needs repairs."""
        fixed = []
        for repair_this, repairers in self.repair_these.items():
            if repair_this.max_hit_points - repair_this.hit_points:
                fixed.append(self.repair_these[repair_this])
            elif len(repairers) < 3:
                unit.repair(repair_this)
                break

        for unit in fixed:
            del self.repair_these[unit]

    # ZW
    def try_to_win(self, bot: IDABot):
        """Attackers will try to kill all enemy units."""
        if self.enemy_structures:
            # Attack closest structure
            self.march_together_units(get_closest(
                [(pos, pos) for pos in self.enemy_structures],
                self.leader.position if self.leader else self.target_pos))
        elif bot.remember_enemies:
            found = None
            for unit in bot.remember_enemies:
                if unit.position == self.target_pos:
                    found = unit
                    break
            if found:
                bot.remember_enemies.remove(unit)

            self.march_together_units(get_closest(
                [(unit.position, unit.position) for unit in bot.remember_enemies],
                self.leader.position if self.leader else self.target_pos))

    # ---------- PROPERTIES ----------
    # Values that are trivial calculations but important for the object

    @property
    def satisfied(self):
        """Return True if the troop wants more units."""
        return (self.prohibit_refill or
                self.wants_marines <= 0 and self.wants_tanks <= 0)

    @property
    def is_terminated(self):
        """Return True if the troop is empty and can't refill."""
        return self.prohibit_refill and not self.get_units()

    @property
    def have_all_reached_target(self):
        """Returns true if all members are close to target."""
        return not self.not_reached_target and  \
               all([unit.position.squared_dist(self.target_pos)
                    <= self.target_radius**2
                    for unit in self.get_units()])

    @property
    def wants_marines(self) -> int:
        """Return required amount of marines to satisfy capacity."""
        return max(self.marines_capacity - len(self.marines), 0) \
            if not self.under_attack and not self.prohibit_refill else 0

    @property
    def wants_tanks(self) -> int:
        """Return required amount of tanks to satisfy capacity."""
        return max(self.tanks_capacity - len(self.tanks), 0) \
            if not self.under_attack and not self.prohibit_refill else 0

    @property
    def has_enough(self) -> bool:
        """Check if the capacity is satisfied for all unit types."""
        return 0 >= self.wants_marines and 0 >= self.wants_tanks

    @property
    def target_pos(self) -> Point2D:
        """Returns the target position."""
        return self.__target if isinstance(self.__target, Point2D) \
            else self.__target.position

    # ---------- CLASS METHODS ----------
    # Methods relevant to the class rather then any instance of it.
    # Focused on handling enemy targets for troops.

    @classmethod
    def found_enemy_structure(cls, unit: Unit, bot: IDABot):
        """Adds target structure to Troop targets."""
        if unit.is_cloaked:
            cls.enemy_structures[unit.position] = True
            for base in bot.base_location_manager.base_locations:
                if base.contains_position(unit.position) \
                        and base not in cls.enemy_bases:
                    cls.enemy_bases.append(base)

            for troop in attackers:
                if troop.target_pos in cls.enemy_structures:
                    troop.try_to_win(bot)

    @classmethod
    def check_validity_enemy_structures(cls, bot: IDABot):
        """Confirm that enemy_structures are still valid targets."""
        remove_these = []
        for target, visible in cls.enemy_structures.items():
            if visible:
                if not bot.map_tools.is_visible(round(target.x), round(target.y)):
                    cls.enemy_structures[target] = False
            else:
                if bot.map_tools.is_visible(round(target.x), round(target.y)):
                    cls.enemy_structures[target] = True

                    found = None
                    for unit in bot.get_all_units():
                        if unit.player == PLAYER_ENEMY:
                            if unit.position.x == target.x \
                                    and unit.position.y == target.y:
                                if unit.is_alive:
                                    found = unit
                                    break

                    if not found:
                        remove_these.append(target)

        for target in remove_these:
            cls.lost_enemy_structure(target, bot)

    @classmethod
    def lost_enemy_structure(cls, at: Union[Unit, Point2D], bot: IDABot):
        """Removes target structure from Troop targets."""
        if isinstance(at, Unit):
            at = at.position

        del cls.enemy_structures[at]

        for base in cls.enemy_bases.copy():
            if base.contains_position(at) and \
                    not base.is_occupied_by_player(PLAYER_ENEMY):
                cls.enemy_bases.remove(base)

    @property
    def get_leash(self):
        return self.__leash

    @property
    def get_order(self):
        return self.__order

    @property
    def get_target(self):
        return self.__target

# ========== END OF TROOP ==========


# All troops!
defenders: List[Troop] = []
attackers: List[Troop] = []


# ZW
def create_troop_defending(point: Point2D):
    """Create a new troop with given target that are suppose to defend."""
    defenders.append(Troop(point))


# ZW
def create_troop_attacking(point: Point2D):
    """Creates a new troop with given target that are suppose to attack."""
    attackers.append(Troop(point, True))


# ZW
def remove_terminated_troops() -> None:
    """Remove empty troops from relevant lists."""
    i = 0
    while i < len(attackers):
        if attackers[i].is_terminated:
            attackers.pop(i)
        else:
            i += 1
    i = 0
    while i < len(defenders):
        if defenders[i].is_terminated:
            defenders.pop(i)
        else:
            i += 1


# ZW
def all_troops():
    """Returns all troops."""
    return attackers + defenders


# ZW
def marine_seeks_troop(position: Point2D) -> Union[Troop, None]:
    """Find closest troop requiring a marine most."""
    closest = [None, None, None]
    distance = [0, 0, 0]

    for troop in all_troops():
        if troop.prohibit_refill:
            continue

        if troop.wants_marines > 0 and not troop.is_attackers:
            if not closest[0] or troop.target_pos.dist(position) / troop.wants_marines < distance[0]:
                closest[0] = troop
                distance[0] = troop.target_pos.dist(position)
        elif troop.wants_marines > 0:
            if not closest[1] or troop.target_pos.dist(position) / troop.wants_marines < distance[1]:
                closest[1] = troop
                distance[1] = troop.target_pos.dist(position)
        else:
            if not closest[2] or troop.target_pos.dist(position) < distance[2]:
                closest[2] = troop
                distance[2] = troop.target_pos.dist(position)

    return closest[0] if closest[0] else closest[1] if closest[1] else closest[2]


# ZW
def tank_seeks_troop(position: Point2D) -> Union[Troop, None]:
    """Find closest troop requiring a tank most."""
    closest = [None, None, None]
    distance = [0, 0, 0]

    for troop in all_troops():
        if troop.prohibit_refill:
            continue

        if troop.wants_tanks > 0 and not troop.is_attackers:
            if not closest[0] or troop.target_pos.dist(position) / troop.wants_tanks < distance[0]:
                closest[0] = troop
                distance[0] = troop.target_pos.dist(position)
        elif troop.wants_tanks > 0:
            if not closest[1] or troop.target_pos.dist(position) / troop.wants_tanks < distance[1]:
                closest[1] = troop
                distance[1] = troop.target_pos.dist(position)
        else:
            if not closest[2] or troop.target_pos.dist(position) < distance[2]:
                closest[2] = troop
                distance[2] = troop.target_pos.dist(position)

    return closest[0] if closest[0] else closest[1] if closest[1] else closest[2]


# ZW
def bunker_seeks_troop(position: Point2D) -> Union[Troop, None]:
    """Return suitable troop for bunker."""
    for troop in all_troops():
        if not troop.is_attackers and troop.nearby_target(position):
            return troop
    return None


# ZW
def find_unit_troop(unit: Unit) -> Union[Troop, None]:
    """Return the troop this unit is in. If not any then null."""
    for troop in all_troops():
        if troop.has_unit(unit):
            return troop
    return None


def closest_troop(pos: Point2D) -> Union[Troop, None]:
    """Finds the closest troop to a position"""
    closest = None
    distance = 0
    for troop in all_troops():
        if not closest or distance > troop.target_pos.dist(pos):
            closest = troop
            distance = troop.target_pos.dist(pos)

    return closest
