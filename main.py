"""
File is the body of the bot and handles bigger functions.
"""
from debug import *
from armies import *
from workplace import *


class MyAgent(ScaiBackbone):
    """
    A bot that uses IDABot to play and win StarCraft 2 matches.
    """

    # ---------- MAGIC METHODS ----------
    # Methods that are relevant for the class but already built in via Python.

    def __init__(self):
        """
        Initializes important values for MyAgent.
        """
        super().__init__()

        self.remember_these = []
        self.remember_mine = {}
        self.remember_enemies = []
        self.should_train_marines = []
        self.should_train_tanks = []
        self.should_develop_infantry = []
        self.should_develop_vehicle = []

    # ---------- FOUNDATION EVENTS ----------
    # These are events (functions) which are triggered by the IDABot.

    def on_game_start(self) -> None:
        """
        EVENT: Called on start up, triggered by IDABot.
        """
        super().on_game_start()

        # If bot should defened first base, then create a Troop
        # for that purpose.
        if DEFEND_FIRST_BASE:
            if self.side() == 'right':
                create_troop_defending(Point2D(114, 46))
            else:
                create_troop_defending(Point2D(38, 122))

        # Create a Workplace on start location.
        create_workplace(self.base_location_manager
                         .get_player_starting_base_location(PLAYER_SELF), self)

    def on_step(self) -> None:
        """
        EVENT: Called each cycle, triggered by IDABot.
        """
        super().on_step()

        # Call triggers and therefore all other Events that are triggered.
        self.trigger_events_for_all_units()
        self.trigger_events_for_my_units()

        # Print information relevant for developers.
        print_debug(self)

        # Try to train SCV if possible.
        self.train_scv()

        # Trigger on_step of all Workplaces and see if their under attack.
        for workplace in workplaces:
            if workplace.under_attack and not workplace.was_under_attack:
                defender = closest_troop(workplace.location.position)
                defender.defend_workplace(workplace, self)
            workplace.on_step(self)

        # Trigger on_step of all Troops and see if they're all satisfied.
        all_satisfied = True
        for troop in all_troops():
            troop.on_step(self)
            if not troop.satisfied:
                all_satisfied = False

        # Create an attacking Troop if fitting.
        if all_satisfied and len(workplaces) >= NUMB_BASES_BEFORE_ATTACKING:
            if self.side() == 'right':
                create_troop_attacking(Point2D(108, 55))
            else:
                create_troop_attacking(Point2D(46, 117))

        remove_terminated_troops()
        Troop.check_validity_enemy_structures(self)

        # For all units in queue to do something, see if they should do it
        if self.should_train_tanks:
            self.train_tank()
        if self.should_train_marines:
            self.train_marine()
        if self.should_develop_infantry:
            self.develop_infantry()
        if self.should_develop_vehicle:
            self.develop_vehicle()

        # If there isn't any scout, then let scout() fetch a new one
        if not scouts:
            self.scout()

    # ---------- LOCAL EVENTS ----------
    # These are events handling individual units in special states only.

    def on_new_my_unit(self, unit: Unit) -> None:
        """
        EVENT: Called each time a new completed unit that is owned by
        the bot is first noticed. Unfinished structures don't trigger
        this event.
        """

        # Remove buildings from Workplace targets and trigger
        # the relevant Event.
        if unit.unit_type.is_building:
            for workplace in workplaces:
                if workplace.has_build_target(unit):
                    workplace.on_building_completed(unit)
                    break

        # If Supply depot: lower it.
        if unit.unit_type.unit_typeid == UNIT_TYPEID.TERRAN_SUPPLYDEPOT:
            unit.ability(ABILITY_ID.MORPH_SUPPLYDEPOT_LOWER)

        # If Marine: Have it join a troop
        elif unit.unit_type.unit_typeid == UNIT_TYPEID.TERRAN_MARINE:
            troop = marine_seeks_troop(unit.position)
            if troop:
                troop.add(unit)

        # If Bunker: Have it join troop
        elif unit.unit_type.unit_typeid == UNIT_TYPEID.TERRAN_BUNKER:
            troop = bunker_seeks_troop(unit.position)
            if troop:
                troop.add(unit)

        # If Siegetank: Have it join troop
        elif unit.unit_type.unit_typeid in [UNIT_TYPEID.TERRAN_SIEGETANK,
                                            UNIT_TYPEID.TERRAN_SIEGETANKSIEGED]:
            troop = tank_seeks_troop(unit.position)
            if troop:
                troop.add(unit)

        # If SCV: Have it join closest workplace
        elif unit.unit_type.unit_typeid == UNIT_TYPEID.TERRAN_SCV:
            workplace = scv_seeks_workplace(unit.position)
            if workplace:
                workplace.add(unit)

        # If should add to a workplace: Then do so
        elif unit.unit_type.unit_typeid in \
                (refineries_TYPEIDS
                 + grounded_command_centers_TYPEIDS
                 + [UNIT_TYPEID.TERRAN_BARRACKS,
                    UNIT_TYPEID.TERRAN_ENGINEERINGBAY,
                    UNIT_TYPEID.TERRAN_ARMORY,
                    UNIT_TYPEID.TERRAN_FACTORY]):
            work = closest_workplace(unit.position)
            if work:
                work.add(unit)

        if len(workplaces) < MAX_EXPANSIONS:
            self.expansion()

        elif STRATEGY_FLUSH \
                and all(map(lambda troop: troop.satisfied, defenders)) \
                and attackers \
                and all(map(lambda work: work.has_enough_scvs, workplaces)):
            self.kill_em_all()

    def on_idle_my_unit(self, unit: Unit) -> None:
        """
        EVENT: Called each time a unit that is owned by the bot is idle.
        """

        # Trigger relevant Events in relevant groups.
        troop = find_unit_troop(unit)
        if troop:
            troop.on_idle(unit, self)
        work = find_unit_workplace(unit)
        if work:
            work.on_idle_my_unit(unit, self)

        # If they can develop then put them in line to do that.
        if unit.unit_type.unit_typeid == UNIT_TYPEID.TERRAN_ENGINEERINGBAY:
            self.should_develop_infantry.append(unit)
        elif unit.unit_type.unit_typeid == UNIT_TYPEID.TERRAN_ARMORY:
            self.should_develop_vehicle.append(unit)

        # Try to move scout by finding a new target.
        if unit in scouts:
            self.scout()

    def on_damaged_my_unit(self, unit: Unit) -> None:
        """
        EVENT: Called each time a unit that is owned by the bot has lost
        life (even if dead).
        """

        # Trigger relevant Events in relevant groups.
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
        """
        EVENT: Called each time a unit that is owned by the bot is killed.
        """

        # Try to remove unit from relevant groups.
        troop = find_unit_troop(unit)
        if troop:
            troop.remove(unit)

        work = find_unit_workplace(unit)
        if work:
            work.remove(unit)

        if unit in scouts:
            remove_scout(unit)

    # ---------- GLOBAL EVENTS ----------
    # These events are triggered by all units.

    def on_discover_unit(self, unit: Unit) -> None:
        """
        EVENT: Called when a unit is discovered. This means that unfinshed
        buildings are found here, as well as just constructed units.
        """

        # If relevant target for Miner or Gaser in Workplace, add it as that
        if unit.unit_type.unit_typeid in minerals_TYPEIDS \
                and unit.minerals_left_in_mineralfield > 0:
            for workplace in workplaces:
                if workplace.location.contains_position(unit.position):
                    workplace.add_mineral_field(unit)

        elif unit.unit_type.unit_typeid in geysers_TYPEIDS \
                and unit.gas_left_in_refinery > 0:
            for workplace in workplaces:
                if workplace.location.contains_position(unit.position):
                    workplace.add_geyser(unit)

        # Add relevant targets for attacking Troops as targets
        if unit.player == PLAYER_ENEMY and unit.unit_type.is_building:
            Troop.found_enemy_structure(unit, self)

    def on_lost_unit(self, unit: Unit) -> None:
        """
        EVENT: Called when a unit is lost, meaning that it isn't seen anymore
        or was destroyed. Units owned by the bot is triggered here as well.
        """

        # When mineral fields disappear, remove them from Workplaces.
        if unit.unit_type.unit_typeid in minerals_TYPEIDS:
            for workplace in workplaces:
                if unit in workplace.mineral_fields:
                    workplace.mineral_fields.remove(unit)
        # NOTE: Geysers can't truly disappear so they are not handled.

        if unit.player == PLAYER_ENEMY:
            # When a enemy structure is destroyed, remove it from
            # Troop targets.
            if not unit.is_alive and unit.unit_type.is_building \
                    and Troop.has_enemy_structure_as_target(unit):
                Troop.lost_enemy_structure(unit, self)

            # When a enemy unit is destroyed, if threatned a troop, then
            # remove it from there.
            for troop in all_troops():
                if unit in troop.foes_to_close:
                    troop.foes_to_close.remove(unit)

    # ---------- EVENT TRIGGERS ----------
    # Triggers all internal events.
    #
    # NOTE: This component is quite heavy for the process and is the
    # bottle neck of the program when it comes to efficiency, but it
    # lessens the load of all other functions significantly.

    remember_mine: Dict[Unit, int] = {}
    # Units owned by the bot and their remembered life.

    def trigger_events_for_my_units(self) -> None:
        """
        TRIGGER: Find units owned by the bot that has special conditions and
        activate relevant triggers for them.
        """
        temp_remember_these = self.remember_mine.copy()

        # Checks for new units
        for unit in self.get_my_units():
            # When a new unit is discovered, handle it properly
            if unit not in temp_remember_these:
                if unit.is_alive and unit.is_completed:
                    self.remember_mine[unit] = unit.hit_points
                    self.on_new_my_unit(unit)
            else:
                # Check if taken damage from last call and if so,
                # trigger relevant Event
                if unit.hit_points < temp_remember_these[unit]:
                    self.on_damaged_my_unit(unit)
                self.remember_mine[unit] = unit.hit_points

                # If unit is alive then acknowledge that it's truly found
                if unit.is_alive:
                    del temp_remember_these[unit]

                    if unit.is_idle:
                        self.on_idle_my_unit(unit)

        # For all units that weren't found, handle them if killed
        for remembered_unit in temp_remember_these:
            if not remembered_unit.is_alive:
                self.on_lost_my_unit(remembered_unit)
                del self.remember_mine[remembered_unit]

    remember_these: List[Unit]  # Remembered units (all).
    remember_enemies: List[Unit]  # Remembered units owned by an enemy.

    def trigger_events_for_all_units(self) -> None:
        """
        TRIGGER: Find all units with special conditions and activate
        triggers for them.
        """
        temp_remember_these = self.remember_these.copy()

        # Checks for new units
        for unit in self.get_all_units():
            if unit.is_cloaked:  # is_cloaked <=> Visible on the map
                if unit not in temp_remember_these:
                    # A new unit is discovered
                    if unit.is_alive:
                        self.remember_these.append(unit)
                        if unit.player == PLAYER_ENEMY:
                            self.remember_enemies.append(unit)
                        self.on_discover_unit(unit)

                else:
                    # A remembered unit is found
                    if unit.is_alive:
                        temp_remember_these.remove(unit)

        # For all remembered units that weren't found, handle them if lost
        for remembered_unit in temp_remember_these:
            if not (remembered_unit.is_alive
                    and remembered_unit.is_cloaked
                    and self.map_tools.is_visible(
                        round(remembered_unit.position.x),
                        round(remembered_unit.position.y))):

                self.on_lost_unit(remembered_unit)

                # Forget
                if remembered_unit in self.remember_enemies:
                    self.remember_enemies.remove(remembered_unit)
                self.remember_these.remove(remembered_unit)

    # ---------- TRAIN ----------
    # Functions that tries to train a unit or upgrade it.

    def train_scv(self) -> None:
        """
        Have a Command Center in queue train a SCV if needed.
        """
        scv_type = UnitType(UNIT_TYPEID.TERRAN_SCV, self)

        if can_afford(self, scv_type):
            ccs = get_my_type_units(self, grounded_command_centers_TYPEIDS)
            ccs = list(filter(lambda cc: cc.is_idle, ccs))

            for workplace in workplaces:
                # Stop try to train if no idle Command Center left.
                if not ccs:
                    break

                count_needed = workplace.wants_scvs
                # While there is a need and a Command Center in queue,
                # train SCV.
                while count_needed > 0 and ccs:
                    trainer = get_closest_unit(ccs, workplace.location.position)
                    trainer.train(scv_type)
                    count_needed -= 1
                    ccs.remove(trainer)

    def train_marine(self) -> None:
        """
        Have a Barrack in queue train a Marine if needed.
        """

        marine_type = UnitType(UNIT_TYPEID.TERRAN_MARINE, self)

        if can_afford(self, marine_type):
            barracks = self.should_train_marines

            not_promised_marine = len(list(filter(
                lambda b: b.is_constructing(marine_type), self.get_my_units())))

            for troop in all_troops():
                # Stop trying to train if no idle Barrack left.
                if not barracks:
                    break

                # Promises Marines to Troop (with overflow).
                count_needed = troop.wants_marines - not_promised_marine

                # While there is a need and a Barrack in queue, train Marine.
                while count_needed > 0 and barracks:
                    barrack = get_closest_unit(barracks, troop.target_pos)
                    barrack.train(marine_type)
                    count_needed -= 1
                    barracks.remove(barrack)

                # Lessen not promised Marines with how many of them that were
                # promised to this Troop.
                if not_promised_marine > 0:
                    not_promised_marine -= troop.wants_marines
                    if not_promised_marine < 0:
                        not_promised_marine = 0

        # Empty the queue.
        self.should_train_marines = []

    def train_tank(self) -> None:
        """
        Have a Factory with TechLab in queue train a SiegeTank if needed.
        """

        tank = UnitType(UNIT_TYPEID.TERRAN_SIEGETANK, self)

        if can_afford(self, tank):
            factories = self.should_train_tanks

            not_promised_tanks = len(list(filter(
                lambda b: b.is_constructing(tank), self.get_my_units())))

            for troop in all_troops():
                # Stop trying to train if no idle Factory left.
                if not factories:
                    break

                # Promises Tanks to Troop (with overflow).
                count_needed = troop.wants_tanks - not_promised_tanks

                # While there is a need and a Factory in queue, train Tank.
                while count_needed > 0 and factories:
                    factory = get_closest_unit(factories, troop.target_pos)
                    factory.train(tank)
                    factories.remove(factory)

                # Lessen not promised Tanks with how many of them that were
                # promised to this Troop.
                if not_promised_tanks > 0:
                    not_promised_tanks -= troop.wants_tanks
                    if not_promised_tanks < 0:
                        not_promised_tanks = 0

        # Empty the queue.
        self.should_train_tanks = []

    def develop_infantry(self) -> None:
        """
        Have EngineeringBays in queue develop infantry units.
        """

        if self.minerals >= 600 and self.gas >= 600 \
                and self.should_develop_infantry:

            # Have EngineeringBays try to develop something.
            for engineering_bay in self.should_develop_infantry:
                engineering_bay.research(UPGRADE_ID.TERRANINFANTRYWEAPONSLEVEL1)
                engineering_bay.research(UPGRADE_ID.TERRANINFANTRYARMORSLEVEL1)
                engineering_bay.research(UPGRADE_ID.TERRANINFANTRYWEAPONSLEVEL2)
                engineering_bay.research(UPGRADE_ID.TERRANINFANTRYARMORSLEVEL2)
                engineering_bay.research(UPGRADE_ID.TERRANINFANTRYWEAPONSLEVEL3)
                engineering_bay.research(UPGRADE_ID.TERRANINFANTRYARMORSLEVEL3)

        # Empty the queue.
        self.should_develop_infantry = []

    def develop_vehicle(self) -> None:
        """
        Have Armories in queue develop vehicles units.
        """

        if self.minerals >= 600 and self.gas >= 600 \
                and self.should_develop_vehicle:

            # Have Armories try to develop something.
            for armory in self.should_develop_vehicle:
                armory.research(UPGRADE_ID.TERRANVEHICLEANDSHIPARMORSLEVEL1)
                armory.research(UPGRADE_ID.TERRANVEHICLEANDSHIPARMORSLEVEL2)
                armory.research(UPGRADE_ID.TERRANVEHICLEANDSHIPARMORSLEVEL3)
                armory.research(UPGRADE_ID.TERRANVEHICLEWEAPONSLEVEL1)
                armory.research(UPGRADE_ID.TERRANVEHICLEWEAPONSLEVEL2)
                armory.research(UPGRADE_ID.TERRANVEHICLEWEAPONSLEVEL3)

        # Empty the queue.
        self.should_develop_vehicle = []

    # ---------- ORGANS ----------
    # Major impact functions that are important for the bot.

    def scout(self) -> None:
        """
        Finds suitable unit and have it scout all base locations.
        """

        # Gets and assign all base coordinates.
        if not all_base_chords:
            for cords in choke_point_dict:
                if cords not in [(26, 137), (125, 30)]:
                    all_base_chords.append(cords)

        # If there is no scout, then find and assign a new one.
        if not scouts:
            scout = workplaces[-1].get_scout()

            if scout:
                closest_base = get_closest([Point2D(chord[0], chord[1])
                                            for chord in all_base_chords],
                                           scout.position)
                scout.move(closest_base)

        # Have scout move to closest base if idle.
        if scouts and len(all_base_chords) > 0:
            scout = scouts[0]
            closest_base = get_closest([Point2D(chord[0], chord[1])
                                        for chord in all_base_chords],
                                       scout.position)
            real_base = get_closest([(base.position, base) for base in
                                     self.base_location_manager.base_locations],
                                    closest_base)

            # Move to closest base location. If there or idle, go to next site.
            if scout.is_idle and Troop.enemy_structures:

                # If scout reached target, remove it.
                if real_base.contains_position(closest_base) \
                        and real_base.contains_position(scout.position):

                    all_base_chords.remove((closest_base.x, closest_base.y))

                scout.move(closest_base)

            # If there are no enemy structures for Troop, see if any in
            # enemy start location.
            elif not Troop.enemy_structures:
                if self.side() == "right":
                    scout.move(Point2D(26, 137))
                else:
                    scout.move(Point2D(125, 30))

    def expansion(self) -> None:
        """
        Builds a new command center when needed.
        """
        command_center_type = UnitType(UNIT_TYPEID.TERRAN_COMMANDCENTER, self)
        location = self.base_location_manager.get_next_expansion(PLAYER_SELF). \
            depot_position

        if (self.troops_full() or not all_troops()) \
                and can_afford(self, command_center_type) \
                and not currently_building(self, command_center_type):

            workplace = closest_workplace(location)
            worker = workplace.get_suitable_worker_and_remove()

            # If found a worker, have it to be the first member of the
            # new Workplace and have it construct the Command Center.
            if worker:
                new_workplace = create_workplace(
                    self.base_location_manager.get_next_expansion(PLAYER_SELF),
                    self)
                new_workplace.add(worker)
                new_workplace.have_worker_construct(command_center_type,
                                                    location)

                point = self.choke_points((location.x, location.y))
                create_troop_defending(point)

    def kill_em_all(self) -> None:
        """
        Flush most of all units to a single troop and attack with it.
        """

        # Get suitable army to flush into.
        army = None
        for attacker in attackers:
            if not attacker.satisfied:
                army = attacker
                break

        if army:
            army.prohibit_refill = True

            self.send_chat("Going for the win!")

            # Fill troop with as many units as possible.
            for troop in defenders:
                if troop != army:
                    army.add(troop.flush_troop())

            for workplace in workplaces:
                army.add(workplace.flush_units())

    def try_to_scan(self, point: Point2D) -> None:
        """
        Look for an orbital command center and have it scan given position.
        """
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

    def side(self) -> str:
        """
        Return what side player spawns on as a String.
        """
        # NOTE: Since Point2D has problems with the comparison this compromise
        # is used instead.
        start_location = self.base_location_manager. \
            get_player_starting_base_location(PLAYER_SELF).position
        start_location_tuple = (start_location.x, start_location.y)

        if start_location_tuple == (127.750000, 28.500000):
            return 'right'
        else:
            return 'left'

    def choke_points(self, coordinates: Tuple[int, int]) -> Point2D:
        """
        Returns a appropriate choke point for a BaseLocation position
        which is provided in the form of a Tuple with x and y as elements.
        """
        return Point2D(choke_point_dict[coordinates][0],
                       choke_point_dict[coordinates][1])

    # ---------- LOGIC ARGUMENTS ----------
    # Functions that provide simple values about its state

    def have_one(self, utid: Union[UNIT_TYPEID, UnitType]) -> bool:
        """
        Returns whether a unit of the given type exists among the bots units.
        """
        if isinstance(utid, UNIT_TYPEID):
            for unit in self.get_my_units():
                if unit.unit_type.unit_typeid == utid and unit.is_completed:
                    return True
        elif isinstance(utid, UnitType):
            for unit in self.get_my_units():
                if unit.unit_type == utid and unit.is_completed:
                    return True
        return False

    def troops_full(self) -> bool:
        """
        Returns False if any defending troop is not full.
        """
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
    pr.print_stats(sort="time")
