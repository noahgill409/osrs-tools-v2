from src.osrs_tools.character import *
from src.osrs_tools import analysis_tools
from src.osrs_tools.analysis_tools import ComparisonMode, DataMode

from itertools import product
import math
from tabulate import tabulate



def magic_shield_comparison(**kwargs):

	options = {
		'floatfmt': '.1f',
	}
	options.update(kwargs)

	lad = Player(name='lad')
	lad.boost(Overload.overload())
	lad.prayers.pray(Prayer.augury())

	lad.equipment.equip_basic_magic_gear(arcane=False, brimstone=False)
	lad.active_style = lad.equipment.equip(ring_of_endurance, Weapon.from_bb('sanguinesti staff'))

	equipment = [
		Equipment(shield=Gear.from_bb('arcane spirit shield')),
		Equipment(shield=book_of_the_dead)
	]

	olms = [OlmMageHand.from_de0(ps) for ps in range(15, 32, 8)]

	indices, axes, data_ary = analysis_tools.generic_comparison_better(
		players=lad,
		equipment=equipment,
		target=olms,
		comparison_mode=ComparisonMode.CARTESIAN,
		data_mode=DataMode.DPS,
	)

	row_axis = 4
	col_axis = 6

	data = data_ary[0, 0, 0, 0, :, 0, :]
	table_data = []

	for index, row in enumerate(data):
		row_with_label = [axes[row_axis][index]] + list(row)
		table_data.append(row_with_label)

	headers = [f'Olm Mage Hand ({ps:.0f})' for ps in range(15, 32, 8)]
	table = tabulate(table_data, headers=headers, floatfmt=options['floatfmt'])
	print(table)


def olm_estimate(**kwargs):

	options = {
		'floatfmt': '.1f',
		'thrall_dpt': 0.5,
		'scales': range(15, 56, 4),

	}
	options.update(kwargs)

	mage_lad = Player(name='mage_lad')
	mage_lad.boost(Overload.overload())
	mage_lad.prayers.pray(Prayer.augury())
	mage_lad.equipment.equip_basic_magic_gear(arcane=False, brimstone=False)
	mage_lad.active_style = mage_lad.equipment.equip(ring_of_endurance, book_of_the_dead,
	                                                 Weapon.from_bb('sanguinesti staff'))

	magic_olms = [OlmMageHand.from_de0(ps) for ps in options['scales']]

	indices, axes, data_ary = analysis_tools.generic_comparison_better(
		players=mage_lad,
		target=magic_olms,
		comparison_mode=ComparisonMode.PARALLEL,
		data_mode=DataMode.DPT,
	)

	data_ary = data_ary + options['thrall_dpt']
	magic_hp_per_phase = [olm.levels.hitpoints for olm in magic_olms]
	magic_ticks_per_phase = [mhpp / dpt for mhpp, dpt in zip(magic_hp_per_phase, data_ary)]
	specs_before_melee_starts = [int(np.round(2 + x/250)) for x in magic_ticks_per_phase]

	print(magic_ticks_per_phase)
	print(specs_before_melee_starts)

	defence_at_start_of_melee_phase = [0, 0, 0]

	melee_lad = Player(name='melee_lad')
	melee_lad.boost(Overload.overload())
	melee_lad.prayers.pray(Prayer.piety())
	melee_lad.equipment.equip_basic_melee_gear(berserker=False, torture=False)
	melee_lad.equipment.equip_torva_set()
	melee_lad.active_style = melee_lad.equipment.equip_lance(berserker=False)
	melee_lad.equipment.equip(amulet_of_fury, ring_of_endurance)

	melee_olms = [OlmMeleeHand.from_de0(ps) for ps in options['scales']]

	for olm, starting_def in zip(melee_olms, defence_at_start_of_melee_phase):
		olm.active_levels.defence = 0   # starting_def

	melee_indices, melee_axes, melee_data_ary = analysis_tools.generic_comparison_better(
		players=melee_lad,
		target=melee_olms,
		comparison_mode=ComparisonMode.PARALLEL,
		data_mode=DataMode.DPT
	)

	melee_data_ary = melee_data_ary + options['thrall_dpt']
	melee_hp_per_phase = [olm.levels.hitpoints for olm in melee_olms]
	melee_ticks_per_phase = [mhpp / dpt for mhpp, dpt in zip(melee_hp_per_phase, melee_data_ary)]

	ranger_lad = Player(name='ranger_lad')
	ranger_lad.boost(Overload.overload())
	ranger_lad.prayers.pray(Prayer.rigour())
	ranger_lad.equipment.equip_basic_ranged_gear(brimstone=False)
	ranger_lad.equipment.equip_arma_set(zaryte=True)
	ranger_lad.active_style = ranger_lad.equipment.equip_twisted_bow()

	olm_heads = [OlmHead.from_de0(ps) for ps in options['scales']]

	ranged_indices, ranged_axes, ranged_data_ary = analysis_tools.generic_comparison_better(
		players=ranger_lad,
		target=olm_heads,
		comparison_mode=ComparisonMode.PARALLEL,
		data_mode=DataMode.DPT
	)

	ranged_data_ary = ranged_data_ary + options['thrall_dpt']
	ranged_hp = [olm.levels.hitpoints for olm in olm_heads]
	ranged_ticks = [rhp / dpt for rhp, dpt in zip(ranged_hp, ranged_data_ary)]

	print(f'{magic_ticks_per_phase=}\n{melee_ticks_per_phase=}\n{ranged_ticks=}')

	magic_time_secs = [0.6*t * o.phases() for t, o in zip(magic_ticks_per_phase, magic_olms)]
	melee_time_secs = [0.6*t * o.phases() for t, o in zip(melee_ticks_per_phase, melee_olms)]
	total_time_secs = magic_time_secs[0] + melee_time_secs[0] + 0.6*ranged_ticks[0]

	print(f'{total_time_secs=}, {total_time_secs / 60}, {total_time_secs / 3600}')


def olm_damage_estimate(**kwargs):
	options = {
		'floatfmt': '.1f',
		'scales': range(15, 32, 8),
	}
	options.update(kwargs)

	melee_lad = Player(name='melee_lad')
	melee_lad.boost(Overload.overload())
	melee_lad.prayers.pray(Prayer.piety())
	melee_lad.equipment.equip_basic_melee_gear(berserker=False, torture=False)
	melee_lad.equipment.equip_torva_set()
	melee_lad.active_style = melee_lad.equipment.equip_lance(avernic=False)
	melee_lad.equipment.equip(amulet_of_fury, ring_of_endurance)

	equipments = [Equipment(shield=x) for x in (avernic_defender, elysian_spirit_shield)]
	olms = [OlmHead.from_de0(ps) for ps in options['scales']]

	olm = OlmHead.from_de0(1)
	melee_lad.equipment.equip(avernic_defender)
	dam_1 = olm.damage_distribution(melee_lad)
	melee_lad.equipment.equip(elysian_spirit_shield)
	dam_2 = olm.damage_distribution(melee_lad)

	print(dam_1, dam_2)


def melee_hand_mean_defence(scale: int, total_specs: int, hammers_first: int, **kwargs):
	options = {
		'trials': 1e3,
	}
	options.update(kwargs)
	trials = int(options['trials'])

	lad_1 = Player(name='lad 1')
	lad_2 = Player(name='lad 2')
	lads = [lad_1, lad_2]

	for lad in lads:
		lad.boost(Overload.overload())
		lad.prayers.pray(Prayer.piety())

		lad.equipment.equip_basic_melee_gear(berserker=False, torture=False)
		lad.equipment.equip_torva_set()
		lad.equipment.equip(Gear.from_bb('amulet of fury'))

	lad_1.active_style = lad_1.equipment.equip_dwh(inquisitor_set=False, avernic=True, brimstone=False)
	lad_2.active_style = lad_2.equipment.equip(SpecialWeapon.from_bb('bandos godsword'))

	defence_data = np.empty(shape=(trials,), dtype=int)
	olm = OlmMeleeHand.from_de0(party_size=scale)

	defence_range = np.arange(0, olm.levels.defence + 1)
	dwh_p_ary = np.empty(shape=defence_range.shape, dtype=float)
	bgs_dam_ary = np.empty(shape=defence_range.shape, dtype=Damage)

	for index, defence in enumerate(defence_range):
		olm.active_levels.defence = defence
		dwh_p_ary[index] = lad_1.damage_distribution(olm, special_attack=True).chance_to_deal_positive_damage
		bgs_dam_ary[index] = lad_2.damage_distribution(olm, special_attack=True)

	for index in range(trials):
		olm.reset_stats()
		dwh_landed = 0

		for _ in range(total_specs):
			if dwh_landed < hammers_first:
				p = dwh_p_ary[olm.active_levels.defence]

				if np.random.random() < p:
					dwh_landed += 1
					olm.apply_dwh()
			else:
				bgs_dam: Damage = bgs_dam_ary[olm.active_levels.defence]
				olm.apply_bgs(bgs_dam.random()[0])

		defence_data[index] = olm.active_levels.defence

	return defence_data.mean()


def melee_hand_estimate(**kwargs):
	pass





if __name__ == '__main__':
	ring_of_endurance = Gear(
		name='ring of endurance',
		slot=GearSlots.ring,
		aggressive_bonus=AggressiveStats.no_bonus(),
		defensive_bonus=DefensiveStats.no_bonus(),
		prayer_bonus=0,
		combat_requirements=PlayerLevels.no_requirements()
	)

	book_of_the_dead = Gear(
		name='book of the dead',
		slot=GearSlots.shield,
		aggressive_bonus=AggressiveStats(magic=6),
		defensive_bonus=DefensiveStats.no_bonus(),
		prayer_bonus=3,
		combat_requirements=PlayerLevels.no_requirements()
	)

	elysian_spirit_shield = Gear.from_bb('elysian spirit shield')
	avernic_defender = Gear.from_bb('avernic defender')
	amulet_of_fury = Gear.from_bb('amulet of fury')

	# magic_shield_comparison(floatfmt='.2f')
	olm_estimate(scales=(31, ))
	# olm_damage_estimate(scales=(31, ))
