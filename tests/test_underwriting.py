import openpyxl
import pytest

from deal_desk import Property, UnitGroup, annual_debt_service, assumptions_from, generate_properties, underwrite
from deal_desk.excel import write_workbook


def fourplex():
    return Property(
        id="T-1", name="Test Fourplex", address="1 Test St", neighborhood="Conway", units=4,
        year_built=1985, sqft=3400, cond="B",
        mix=[UnitGroup("2BR/1BA", 4, 1400, 1600)],
        asking_price=600_000, taxes=10_000, insurance=5_000,
        util_water=250, util_trash=70, util_elec=80, other_monthly=100,
        repairs_per_unit=800, vacancy=0.05, market_cap=0.06, rehab_per_unit=10_000,
    )


def test_income_and_noi_by_hand():
    p = fourplex()
    r = underwrite(p, assumptions_from(p))
    assert r.gpr == 4 * 1400 * 12  # 67,200
    assert r.egi == pytest.approx(67_200 * 0.95 + 1_200)  # 65,040
    expected_opex = 10_000 + 5_000 + 400 * 12 + 800 * 4 + 0.08 * r.egi + 400 * 4 + 300 * 4
    assert r.opex == pytest.approx(expected_opex)
    assert r.noi == pytest.approx(r.egi - expected_opex)
    assert r.cap_rate == pytest.approx(r.noi / 600_000)


def test_debt_service_matches_excel_pmt():
    # =-PMT(0.07/12, 360, 450000)*12 = 35,926.33
    assert annual_debt_service(450_000, 0.07, 30) == pytest.approx(35_926.33, abs=0.05)
    assert annual_debt_service(0, 0.07, 30) == 0


def test_cash_needed():
    p = fourplex()
    r = underwrite(p, assumptions_from(p))
    # 25% down + 3% closing + 1% of loan + rehab + $1k/unit reserves
    assert r.cash_needed == pytest.approx(150_000 + 18_000 + 4_500 + 40_000 + 4_000)


def test_value_add_raises_noi():
    p = fourplex()
    r = underwrite(p, assumptions_from(p))
    assert r.stab_noi > r.noi
    assert r.equity_created == pytest.approx(r.stab_noi / 0.06 - r.all_in)


def test_generator_is_deterministic_and_plausible():
    a = generate_properties(200, seed=7)
    b = generate_properties(200, seed=7)
    assert [x.asking_price for x in a] == [x.asking_price for x in b]
    for p in a:
        assert sum(g.count for g in p.mix) == p.units
        assert 20_000 < p.asking_price / p.units < 600_000
        assert all(g.rent <= g.market * 1.03 for g in p.mix)


def test_excel_export_has_live_formulas(tmp_path):
    props = generate_properties(25, seed=1)
    path = write_workbook([(p, assumptions_from(p)) for p in props], str(tmp_path / "out.xlsx"))
    wb = openpyxl.load_workbook(path)
    ws = wb["Deals"]
    headers = [c.value for c in ws[1]]
    noi = ws.cell(row=2, column=headers.index("NOI") + 1).value
    assert isinstance(noi, str) and noi.startswith("=")
    assert ws.max_row == 26
    assert {"Summary", "Deals", "Rent Roll"} <= set(wb.sheetnames)
