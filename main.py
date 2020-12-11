import time
import random
from copy import deepcopy
from typing import List

from scai_backbone import *
from debug import *
from extra import *
from armies import *
from workplace import *


class MyAgent(ScaiBackbone):
    """A bot that uses IDABot to play and win Starcraft 2 matches."""

    # ---------- GLOBAL EVENTS ----------
    # These are functions triggered by different special events.

    def on_game_start(self) -> None:
        """Called on start up, passed from IDABot.on_game_start()."""
        ScaiBackbone.on_game_start(self)

        # if self.side() == 'right':
        #     create_troop_defending(Point2D(114, 46))
        # else:
        #     create_troop_defending(Point2D(38, 122))
        create_workplace(self.base_location_manager
                         .get_player_starting_base_location(PLAYER_SELF), self)

    def on_step(self) -> None:
        """Called each cycle, passed from IDABot.on_step()."""
        ScaiBackbone.on_step(self)

        self.trigger_events_for_all_units()
        self.trigger_events_for_my_units()

        print_debug(self)

        self.train_scv()

        for workplace in workplaces:
            if workplace.under_attack and not workplace.was_under_attack:
                defender = closest_troop(workplace.location.position)
                defender.defend_workplace(workplace, self)
            workplace.on_step(self)

        all_satisfied = True
        for troop in all_troops():
            troop.on_step(self)
            if not troop.is_attackers and not troop.satisfied:
                all_satisfied = False

        if all_satisfied and len(workplaces) > 2:
            if self.side() == 'right':
                create_troop_attacking(Point2D(108, 55))
            else:
                create_troop_attacking(Point2D(46, 117))

        remove_terminated_troops()
        Troop.check_validity_enemy_structures(self)

        if self.should_train_tanks:
            self.train_tank()
        if self.should_train_marines:
            self.train_marine()
        if self.should_develop_infantry:
            self.develop_infantry()
        if self.should_develop_vehicle:
            self.develop_vehicle()
        self.scout()

        if not Troop.enemy_structures:
            self.scout()

    # ---------- LOCAL EVENTS ----------
    # These are events handling individual units in special states only

    def on_new_my_unit(self, unit: Unit) -> None:
        """Called each time a new unit is noticed (when a building is finished)."""

        # Places building in right workplace (base location)
        add_to_workplace = False

        if unit.unit_type.is_building:
            for workplace in workplaces:
                if workplace.has_build_target(unit):
                    workplace.on_building_completed(unit)
                    break

        # lowers a supply depot when done building
        if unit.unit_type.unit_typeid == UNIT_TYPEID.TERRAN_SUPPLYDEPOT:
            unit.ability(ABILITY_ID.MORPH_SUPPLYDEPOT_LOWER)

        # add marine to closest troop wanting marines
        elif unit.unit_type.unit_typeid == UNIT_TYPEID.TERRAN_MARINE:
            troop = marine_seeks_troop(unit.position)
            if troop:
                troop.add(unit)

        # add bunker to closest troop
        elif unit.unit_type.unit_typeid == UNIT_TYPEID.TERRAN_BUNKER:
            troop = bunker_seeks_troop(unit.position)
            if troop:
                troop.add(unit)

        # add tank to closest troop wanting tanks
        elif unit.unit_type.unit_typeid in [UNIT_TYPEID.TERRAN_SIEGETANK,
                                            UNIT_TYPEID.TERRAN_SIEGETANKSIEGED]:
            troop = tank_seeks_troop(unit.position)
            if troop:
                troop.add(unit)

        # If should add to a workplace, then do so
        elif unit.unit_type.unit_typeid in \
                (refineries_TYPEIDS
                 + [UNIT_TYPEID.TERRAN_BARRACKS,
                    UNIT_TYPEID.TERRAN_ENGINEERINGBAY,
                    UNIT_TYPEID.TERRAN_FACTORY,
                    UNIT_TYPEID.TERRAN_ARMORY]):
            work = closest_workplace(unit.position)
            if work:
                work.add(unit)

        # adds SCV to closest workplace wanting SCVs
        elif unit.unit_type.unit_typeid == UNIT_TYPEID.TERRAN_SCV:
            workplace = scv_seeks_workplace(unit.position)
            if workplace:
                workplace.add(unit)

        # add commandcenter to workplace at the end
        elif unit.unit_type.unit_typeid == UNIT_TYPEID.TERRAN_COMMANDCENTER:
            work = closest_workplace(unit.position)
            if work:
                work.add(unit)

        # TODO: Good number?
        if len(workplaces) < 3:
            self.expansion()

        elif all(map(lambda troop: troop.satisfied, all_troops())) \
                and all(map(lambda work: work.has_enough_scvs, workplaces)):
            self.kill_em_all()

    def on_idle_my_unit(self, unit: Unit) -> None:
        """Called each time a unit is idle."""
        troop = find_unit_troop(unit)
        if troop:
            troop.on_idle(unit, self)

        work = find_unit_workplace(unit)
        if work:
            work.on_idle_my_unit(unit, self)

        if unit.unit_type.unit_typeid == UNIT_TYPEID.TERRAN_ENGINEERINGBAY:
            self.should_develop_infantry.append(unit)
        elif unit.unit_type.unit_typeid == UNIT_TYPEID.TERRAN_ARMORY:
            self.should_develop_vehicle.append(unit)

        if unit in scouts:
            self.scout()

        #     if unit.position.dist(self.scout_path[self.scout_index]) < 3:
        #         self.scout_index = (self.scout_index + 1) % len(self.scout_path)
        # unit.move(self.scout_path[self.scout_index])

    def on_damaged_my_unit(self, unit: Unit) -> None:
        """Called each time a unit has lost life (even if dead)."""
        troop = find_unit_troop(unit)
        if troop:
            troop.on_damaged_member(unit, self)

        work = find_unit_workplace(unit)
        if work:
            work.on_damaged_member(unit, self)
            if not work.was_under_attack:
                troop = closest_troop(work.location.position)
                troop.defend_workplace(work, self)

    def on_lost_my_unit(self, unit: Unit) -> None:
        """Called each time a unit is killed."""
        # Try removing from troop if in any
        troop = find_unit_troop(unit)
        if troop:
            troop.remove(unit)

        work = find_unit_workplace(unit)
        if work:
            work.remove(unit)

        # remove scout from scouts list
        if unit in scouts:
            remove_scout(unit)
            self.scout()

    # ---------- GLOBAL EVENTS ----------
    # These events are triggered by all units,

    def on_discover_unit(self, unit: Unit):
        """Called when a unit is discovered, includes some on new_my_unit."""
        if unit.unit_type.unit_typeid in minerals_TYPEIDS and unit.minerals_left_in_mineralfield > 0:
            for workplace in workplaces:
                if workplace.location.contains_position(unit.position):
                    workplace.add_mineral_field(unit)

        elif unit.unit_type.unit_typeid in geysers_TYPEIDS and unit.gas_left_in_refinery > 0:
            for workplace in workplaces:
                if workplace.location.contains_position(unit.position):
                    workplace.add_geyser(unit)

        if unit.player == PLAYER_ENEMY and unit.unit_type.is_building:
            Troop.found_enemy_structure(unit, self)

    def on_lost_unit(self, unit: Unit):
        """Called when a unit is lost, even when lost_my_unit."""
        if unit.unit_type.unit_typeid in minerals_TYPEIDS:
            for workplace in workplaces:
                if unit in workplace.mineral_fields:
                    workplace.mineral_fields.remove(unit)

        if unit.player == PLAYER_ENEMY:
            for troop in all_troops():
                if unit in troop.foes_to_close:
                    troop.foes_to_close.remove(unit)

    # ---------- EVENT TRIGGERS ----------
    # Triggers all internal events.

    remember_mine: Dict[Unit, int] = {}  # Units and their remembered life

    def trigger_events_for_my_units(self):
        """Find bot units with special conditions and activate triggers for them."""
        temp_remember_these = self.remember_mine.copy()
        # Checks for new units
        for unit in self.get_my_units():
            if unit not in temp_remember_these:
                # A new unit is discovered
                if unit.is_alive and unit.is_completed:
                    self.remember_mine[unit] = unit.hit_points
                    self.on_new_my_unit(unit)
            else:
                # A remembered unit is found

                # If the unit has taken damage...
                if unit.hit_points < temp_remember_these[unit]:
                    self.on_damaged_my_unit(unit)
                self.remember_mine[unit] = unit.hit_points

                # If unit is alive...
                if unit.is_alive:
                    del temp_remember_these[unit]

                    # If idle call on_idle_unit()
                    if unit.is_idle:
                        self.on_idle_my_unit(unit)

        for remembered_unit in temp_remember_these:
            # A remembered unit is not found
            if not remembered_unit.is_alive:
                self.on_lost_my_unit(remembered_unit)
                del self.remember_mine[remembered_unit]

    remember_these: List[Unit]
    remember_enemies: List[Unit]

    def trigger_events_for_all_units(self):
        """Find all units with special conditions and activate triggers for them."""
        temp_remember_these = self.remember_these.copy()

        just_found = []

        # Checks for new units
        for unit in self.get_all_units():
            if unit.is_cloaked:  # is_cloaked inverted
                if unit not in temp_remember_these:
                    # A new unit is discovered
                    if unit.is_alive:
                        self.remember_these.append(unit)
                        just_found.append(unit)
                        if unit.player == PLAYER_ENEMY:
                            self.remember_enemies.append(unit)
                        self.on_discover_unit(unit)

                else:
                    # A remembered unit is found
                    if unit.is_alive:
                        temp_remember_these.remove(unit)

        for remembered_unit in temp_remember_these:
            # A remembered unit is lost
            if not remembered_unit.is_alive or not remembered_unit.is_cloaked:
                self.on_lost_unit(remembered_unit)

                if remembered_unit in self.remember_enemies:
                    self.remember_enemies.remove(remembered_unit)
                self.remember_these.remove(remembered_unit)

    # ---------- TRAIN ----------
    # Functions that tries to train a unit or upgrade it.

    # ZW
    def train_scv(self):
        """Builds a SCV if possible on a base if needed."""
        scv_type = UnitType(UNIT_TYPEID.TERRAN_SCV, self)
        if can_afford(self, scv_type):
            ccs = get_my_types_units(self, grounded_command_centers_TYPEIDS)
            ccs = list(filter(lambda cc: cc.is_idle, ccs))

            for workplace in workplaces:
                if not ccs:
                    break
                count_needed = workplace.wants_scvs
                while count_needed > 0 and ccs:
                    trainer = get_closest_unit(ccs, workplace.location.position)
                    trainer.train(scv_type)
                    count_needed -= 1
                    ccs.remove(trainer)

    # ZW
    def train_marine(self):
        """Train marines if more are required."""

        # Tries to fill troops by producing marines
        barracks = self.should_train_marines
        marine = UnitType(UNIT_TYPEID.TERRAN_MARINE, self)
        # To stop overflow of produce
        not_promised_marine = len(list(filter(
            lambda b: b.is_constructing(marine), self.get_my_units())))

        for troop in all_troops():
            if troop.wants_marines - not_promised_marine > 0 \
                    and can_afford(self, marine):

                barrack = get_closest_unit(barracks, troop.target_pos)
                if barrack:
                    barrack.train(marine)
                    barracks.remove(barrack)

            not_promised_marine -= troop.wants_marines

        self.should_train_marines = []

    # ZW
    def train_tank(self):
        """Train tanks if more are required."""

        tank = UnitType(UNIT_TYPEID.TERRAN_SIEGETANK, self)

        if can_afford(self, tank):
            factories = self.should_train_tanks

            # To stop overflow of produce
            not_promised_tanks = len(list(filter(
                lambda b: b.is_constructing(tank), self.get_my_units())))

            for troop in all_troops():
                if troop.wants_tanks - not_promised_tanks > 0:

                    factory = get_closest_unit(factories, troop.target_pos)

                    if factory:
                        factory.train(tank)
                        factories.remove(factory)

                not_promised_tanks -= troop.wants_tanks

        self.should_train_tanks = []

    def develop_infantry(self):
        """Use engineering bays to develop infantry units."""

        if self.minerals >= 600 and self.gas >= 600 and self.should_develop_infantry:

            for engineering_bay in self.should_develop_infantry:
                engineering_bay.research(UPGRADE_ID.TERRANINFANTRYWEAPONSLEVEL1)
                engineering_bay.research(UPGRADE_ID.TERRANINFANTRYARMORSLEVEL1)
                engineering_bay.research(UPGRADE_ID.TERRANINFANTRYWEAPONSLEVEL2)
                engineering_bay.research(UPGRADE_ID.TERRANINFANTRYARMORSLEVEL2)
                engineering_bay.research(UPGRADE_ID.TERRANINFANTRYWEAPONSLEVEL3)
                engineering_bay.research(UPGRADE_ID.TERRANINFANTRYARMORSLEVEL3)

        self.should_develop_infantry = []

    def develop_vehicle(self):
        """Use armories to develop vehicles units."""

        if self.minerals >= 600 and self.gas >= 600 and self.should_develop_vehicle:

            for engineering_bay in self.should_develop_vehicle:
                engineering_bay.research(UPGRADE_ID.TERRANVEHICLEANDSHIPARMORSLEVEL1)
                engineering_bay.research(UPGRADE_ID.TERRANVEHICLEANDSHIPARMORSLEVEL2)
                engineering_bay.research(UPGRADE_ID.TERRANVEHICLEANDSHIPARMORSLEVEL3)
                engineering_bay.research(UPGRADE_ID.TERRANVEHICLEWEAPONSLEVEL1)
                engineering_bay.research(UPGRADE_ID.TERRANVEHICLEWEAPONSLEVEL2)
                engineering_bay.research(UPGRADE_ID.TERRANVEHICLEWEAPONSLEVEL3)

        self.should_develop_vehicle = []

    # ---------- ORGANS ----------
    # Major impact functions that are important for the bot.

    # DP
    def scout(self):
        """Finds suitable scout (miner) that checks all base locations."""
        if not all_base_chords:
            # Gets all base chords
            for cords in choke_point_dict:
                if cords not in [(26, 137), (125, 30)]:
                    all_base_chords.append(cords)

        if not scouts:
            # Finds and adds scout to scouts
            scout = workplaces[-1].get_scout()

            if scout:
                closest_base = self.closest_position(scout.position, all_base_chords)
                scout.move(closest_base)

        if scouts and len(all_base_chords) > 0:
            scout = scouts[0]
            closest_base = self.closest_position(scout.position, all_base_chords)
            real_base = get_closest([(base.position, base) for base in \
                                     self.base_location_manager.base_locations], closest_base)
            # Move to closest base chord. If there or idle, go to next site.
            if scout.is_idle and Troop.enemy_structures:
                if real_base.contains_position(closest_base) and real_base.contains_position(scout.position):
                    all_base_chords.remove((closest_base.x, closest_base.y))
                    scout.move(closest_base)
                else:
                    scout.move(closest_base)

            elif not Troop.enemy_structures:
                if self.side() == "right":
                    scout.move(Point2D(26, 137))
                else:
                    scout.move(Point2D(125, 30))

    def expansion(self):  # AW
        command_center = UNIT_TYPEID.TERRAN_COMMANDCENTER
        command_center_type = UnitType(UNIT_TYPEID.TERRAN_COMMANDCENTER, self)
        location = self.base_location_manager.get_next_expansion(PLAYER_SELF). \
            depot_position

        if (self.troops_full() or not all_troops())\
                and can_afford(self, command_center_type) \
                and not currently_building(self, command_center) \
                and closest_workplace(location).get_suitable_builder():

            workplace = closest_workplace(location)
            worker = workplace.get_suitable_worker_and_remove()

            if worker:
                new_workplace = create_workplace \
                    (self.base_location_manager.get_next_expansion(PLAYER_SELF),
                     self)
                new_workplace.add(worker)
                new_workplace.have_worker_construct(command_center_type,
                                                    location)

                point = self.choke_points((location.x, location.y))
                create_troop_defending(point)

    def kill_em_all(self):
        """Flush almost all units to a single troop and attack."""

        army = None
        for attacker in attackers:
            if not attacker.satisfied:
                army = attacker
                break

        if army:
            army.prohibit_refill = True

            self.send_chat("Going for the win!")

            for troop in defenders:
                if troop != army:
                    army.add(troop.flush_troop())

            for workplace in workplaces:
                army.add(workplace.flush_units())

    def try_to_scan(self, point: Point2D) -> None:
        """Look for an orbital command center and have it scan given position."""
        orbitals = get_my_type_units(self, UNIT_TYPEID.TERRAN_ORBITALCOMMAND)
        most_suitable = None
        for orbital in orbitals:
            if orbital.energy >= 50 \
                    and (not most_suitable
                         or orbital.energy < most_suitable.energy):
                most_suitable = orbital
                if orbital.energy == orbital.max_energy:
                    break

        if most_suitable:
            most_suitable.ability(ABILITY_ID.EFFECT_SCAN, point)

    # ---------- NAVIGATION ----------
    # The handling and understanding of positions and distances.

    def side(self):
        """Return what side player spawns on"""
        start_location = self.base_location_manager. \
            get_player_starting_base_location(PLAYER_SELF).position
        start_location_tuple = (start_location.x, start_location.y)

        if start_location_tuple == (127.750000, 28.500000):
            return 'right'
        else:
            return 'left'

    def closest_position(self, pos: Point2D, chord_list):
        """Checks the closest base_location to a position"""
        closest = None
        distance = 0
        for base_chords in chord_list:
            base = Point2D(base_chords[0], base_chords[1])
            # Point2D.dist(...) is a function in scai_backbone
            if not closest or distance > base.dist(pos):
                closest = base
                distance = base.dist(pos)

        return closest

    def get_coords(self):
        """Prints position of all workers"""
        for unit in self.get_my_units():
            text = str(unit.position)
            self.map_tools.draw_text(unit.position, text, Color(255, 255, 255))

    def choke_points(self, coordinates) -> Point2D:  # AW
        """Returns the appropriate choke point"""
        return Point2D(choke_point_dict[coordinates][0],
                       choke_point_dict[coordinates][1])

    # ---------- LOGIC ARGUMENTS ----------
    # Functions that provide simple values about its state

    # ZW
    def have_one(self, utid: Union[UNIT_TYPEID, UnitType]) -> bool:
        """Check if there exists at least one of these units in my_units."""
        if isinstance(utid, UNIT_TYPEID):
            for unit in self.get_my_units():
                if unit.unit_type.unit_typeid == utid and unit.is_completed:
                    return True
        elif isinstance(utid, UnitType):
            for unit in self.get_my_units():
                if unit.unit_type == utid and unit.is_completed:
                    return True
        return False

    def troops_full(self) -> bool:  # AW
        """Returns true if all troops are full"""
        for troop in defenders:
            if troop.wants_marines > 1:
                return False

        return True


# ========== END OF MY_AGENT ==========


if __name__ == "__main__":
    import cProfile

    pr = cProfile.Profile()
    pr.enable()
    MyAgent.bootstrap()
    pr.disable()
    # after your program ends
    pr.print_stats(sort="time")
