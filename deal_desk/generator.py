"""Generate realistic-looking (but fake) Orlando multifamily listings."""

import random
from dataclasses import dataclass, field

from .market import CONDITIONS, NAME_A, NAME_B, NEIGHBORHOODS, STREETS, UNIT_TYPES


@dataclass
class UnitGroup:
    type: str
    count: int
    rent: float  # current in-place rent / month
    market: float  # market rent / month


@dataclass
class Property:
    id: str
    name: str
    address: str
    neighborhood: str
    units: int
    year_built: int
    sqft: int
    cond: str
    mix: list[UnitGroup] = field(default_factory=list)
    asking_price: float = 0
    taxes: float = 0  # $/yr
    insurance: float = 0  # $/yr
    util_water: float = 0  # $/mo, owner-paid water/sewer
    util_trash: float = 0  # $/mo
    util_elec: float = 0  # $/mo, common-area electric
    other_monthly: float = 0  # laundry, parking, pet fees
    repairs_per_unit: float = 0  # $/unit/yr
    vacancy: float = 0.05
    market_cap: float = 0.06
    rehab_per_unit: float = 0
    days_on_market: int = 0

    @property
    def monthly_rent(self) -> float:
        return sum(g.count * g.rent for g in self.mix)


def _round(v: float, step: float) -> float:
    return round(v / step) * step


def generate_property(rng: random.Random, id_num: int) -> Property:
    between = rng.uniform
    nb = rng.choice(NEIGHBORHOODS)

    roll = rng.random()
    if roll < 0.35:
        units = rng.choice([2, 3, 4])
    elif roll < 0.7:
        units = rng.choice([5, 6, 8, 10, 12])
    elif roll < 0.92:
        units = rng.choice([14, 16, 20, 24])
    else:
        units = rng.choice([30, 36, 48])

    year_built = int(between(1955, 2019))
    cond_roll = rng.random() + (0.35 if year_built > 2005 else -0.15 if year_built < 1975 else 0)
    cond = "A" if cond_roll > 0.85 else "B" if cond_roll > 0.45 else "C" if cond_roll > 0.15 else "D"
    _, loss_lo, loss_hi, rehab, repairs = CONDITIONS[cond]

    weights = [0.05, 0.35, 0.5, 0.1] if units <= 4 else [0.1, 0.45, 0.4, 0.05]
    counts = [0, 0, 0, 0]
    for _ in range(units):
        counts[rng.choices(range(4), weights)[0]] += 1

    mix, sqft = [], 0
    for (label, rent_fn, sf), c in zip(UNIT_TYPES, counts):
        if not c:
            continue
        market = _round(rent_fn(nb) * between(0.96, 1.04), 5)
        rent = _round(market * between(loss_lo, loss_hi), 5)
        mix.append(UnitGroup(label, c, rent, market))
        sqft += c * sf

    other = _round(units * between(8, 22), 5)
    water = _round(units * between(52, 78), 5)
    trash = _round(units * between(14, 24), 5)
    elec = _round(80 + units * between(8, 18), 5)
    insurance = _round(units * between(900, 1500) * (1.2 if year_built < 1980 else 1), 50)
    repairs_per_unit = _round(repairs * between(0.9, 1.1), 25)

    # back into an asking price from a rough seller NOI at a cap that's sometimes rich, sometimes cheap
    # brokers price partly on pro-forma rents, so under-rented buildings aren't free money
    pro_forma = between(0.3, 0.9)
    gpr = sum(g.count * (g.rent + (g.market - g.rent) * pro_forma) for g in mix) * 12
    rough_egi = gpr * (1 - nb.vac) + other * 12
    rough_opex = (rough_egi * 0.08 + insurance + (water + trash + elec) * 12
                  + repairs_per_unit * units + 700 * units + 0.018 * gpr * 5.5)
    seller_noi = max(rough_egi - rough_opex, rough_egi * 0.3)
    cap_mult = between(1.25, 1.45) if rng.random() < 0.08 else between(0.82, 1.18)  # ~8% motivated sellers
    asking = _round(seller_noi / (nb.cap * cap_mult), 5000)
    taxes = _round(asking * between(0.0145, 0.0185), 50)

    if units <= 4:
        kind = {2: "Duplex", 3: "Triplex", 4: "Fourplex"}[units]
        name = f"{kind} on {rng.choice(STREETS).split()[0]}"
    else:
        name = f"{rng.choice(NAME_A)} {rng.choice(NAME_B)}"
    address = f"{int(between(100, 9800))} {rng.choice(STREETS)}, {nb.city}, FL {nb.zip}"

    return Property(
        id=f"OMF-{id_num:05d}", name=name, address=address, neighborhood=nb.name, units=units,
        year_built=year_built, sqft=sqft, cond=cond, mix=mix, asking_price=asking, taxes=taxes,
        insurance=insurance, util_water=water, util_trash=trash, util_elec=elec, other_monthly=other,
        repairs_per_unit=repairs_per_unit, vacancy=nb.vac, market_cap=nb.cap, rehab_per_unit=rehab,
        days_on_market=int(between(2, 140)),
    )


def generate_properties(n: int, seed: int = 42) -> list[Property]:
    rng = random.Random(seed)
    return [generate_property(rng, i + 1) for i in range(n)]
