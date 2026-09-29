"""Illustrative Orlando-area market assumptions.

These numbers are practice defaults, not live market data. Swap this module for a
real data source (MLS/CoStar/Zillow export, county tax roll) when you move past
generated listings.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Neighborhood:
    name: str
    city: str
    zip: str
    rent1: float  # typical market rent, 1BR
    rent2: float  # typical market rent, 2BR
    cap: float  # typical market cap rate
    vac: float  # submarket vacancy


NEIGHBORHOODS = [
    Neighborhood("Parramore", "Orlando", "32805", 1080, 1320, 0.070, 0.08),
    Neighborhood("Holden Heights", "Orlando", "32839", 1100, 1350, 0.069, 0.08),
    Neighborhood("Pine Hills", "Orlando", "32808", 1120, 1380, 0.068, 0.075),
    Neighborhood("Azalea Park", "Orlando", "32807", 1220, 1470, 0.063, 0.065),
    Neighborhood("Semoran", "Orlando", "32822", 1260, 1520, 0.062, 0.06),
    Neighborhood("Kissimmee", "Kissimmee", "34741", 1250, 1500, 0.062, 0.065),
    Neighborhood("Sanford", "Sanford", "32771", 1230, 1480, 0.064, 0.065),
    Neighborhood("Conway", "Orlando", "32812", 1320, 1590, 0.059, 0.055),
    Neighborhood("Colonial Town", "Orlando", "32803", 1420, 1760, 0.055, 0.05),
    Neighborhood("College Park", "Orlando", "32804", 1460, 1820, 0.054, 0.05),
    Neighborhood("Mills 50", "Orlando", "32803", 1500, 1860, 0.053, 0.05),
    Neighborhood("Winter Park", "Winter Park", "32789", 1660, 2120, 0.050, 0.045),
    Neighborhood("Lake Nona", "Orlando", "32827", 1720, 2180, 0.051, 0.05),
]

# (label, rent as a function of the neighborhood, typical square feet)
UNIT_TYPES = [
    ("Studio", lambda nb: nb.rent1 * 0.82, 450),
    ("1BR/1BA", lambda nb: nb.rent1, 650),
    ("2BR/1BA", lambda nb: nb.rent2, 850),
    ("3BR/2BA", lambda nb: nb.rent2 * 1.22, 1100),
]

# condition class -> (rent as share of market low/high, rehab $/unit, repairs $/unit/yr)
CONDITIONS = {
    "A": ("Renovated", 0.97, 1.02, 0, 650),
    "B": ("Dated", 0.88, 0.96, 9000, 850),
    "C": ("Needs work", 0.78, 0.88, 17000, 1050),
    "D": ("Distressed", 0.68, 0.80, 28000, 1300),
}

STREETS = [
    "Orange Blossom Trl", "Colonial Dr", "Mills Ave", "Edgewater Dr", "Bumby Ave", "Semoran Blvd",
    "Kirkman Rd", "Pine Hills Rd", "Curry Ford Rd", "Conway Rd", "Aloma Ave", "Fairbanks Ave",
    "Michigan St", "Kaley Ave", "Robinson St", "Lake Underhill Rd", "Silver Star Rd", "Oak Ridge Rd",
    "Goldenrod Rd", "Narcoossee Rd", "Vine St", "French Ave", "Formosa Ave", "Corrine Dr",
]
NAME_A = [
    "The Palms", "Lakeview", "Cypress", "Magnolia", "Orange Grove", "Heron", "Live Oak", "Citrus",
    "Sunrise", "Pelican", "Spanish Moss", "Cattail", "Palmetto", "Egret", "Sabal", "Jasmine", "Bayside", "Osprey",
]
NAME_B = ["Apartments", "Flats", "Court", "Villas", "Terrace", "Commons", "Gardens", "Place", "Residences", "Quad"]
