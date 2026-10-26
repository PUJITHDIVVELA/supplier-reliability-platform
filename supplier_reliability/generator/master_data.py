"""
Master Data Generation: Suppliers, Sites, and Contracts.
Provides realistic archetype distributions: Stable, Deteriorating, Quality-Prone, and Low-Volume.
"""
import random
from datetime import date, datetime, timedelta
from typing import List, Tuple, Dict

from supplier_reliability.models.entities import Supplier, Site, Contract
from supplier_reliability.models.enums import (
    SupplierTier,
    SupplierCategory,
    SupplierStatus,
    FinancialStabilityRating,
    FacilityType,
    SiteStatus,
    ContractType,
    ContractStatus,
)
from supplier_reliability.generator.id_generator import (
    format_supplier_id,
    format_site_id,
    format_contract_id,
)

COMPANY_PREFIXES = [
    "Apex", "Nova", "Titan", "Vanguard", "Precision", "Nexus", "Global", "Summit",
    "Pioneer", "Quantum", "Pacific", "Atlantic", "Omni", "Frontier", "Sterling",
    "Zenith", "Aero", "Micro", "Optima", "Synergy", "Hyperion", "Vertex", "Delta",
]

COMPANY_ROOTS = [
    "Silicon", "Dynamics", "Components", "Microtech", "Machining", "Systems",
    "Logistics", "Robotics", "Materials", "Industries", "Foundry", "Optics",
    "Fabrication", "Packaging", "Circuits", "Electro", "Advanced", "Semiconductor",
]

COMPANY_SUFFIXES = ["Corp", "Inc", "GmbH", "Ltd", "LLC", "S.A.", "Holdings", "Technologies"]

COUNTRIES = [
    ("United States", "US"), ("Germany", "DE"), ("Japan", "JP"),
    ("South Korea", "KR"), ("Taiwan", "TW"), ("Mexico", "MX"),
    ("Vietnam", "VN"), ("India", "IN"), ("Canada", "CA"), ("Netherlands", "NL")
]

CITIES_BY_COUNTRY = {
    "United States": ["Austin", "San Jose", "Detroit", "Phoenix", "Chicago"],
    "Germany": ["Munich", "Stuttgart", "Frankfurt", "Dusseldorf", "Hamburg"],
    "Japan": ["Tokyo", "Osaka", "Nagoya", "Yokohama", "Kyoto"],
    "South Korea": ["Seoul", "Suwon", "Busan", "Incheon", "Daejeon"],
    "Taiwan": ["Hsinchu", "Taipei", "Taichung", "Tainan", "Kaohsiung"],
    "Mexico": ["Monterrey", "Guadalajara", "Tijuana", "Queretaro", "Juarez"],
    "Vietnam": ["Ho Chi Minh City", "Hanoi", "Da Nang", "Hai Phong", "Bac Ninh"],
    "India": ["Bengaluru", "Chennai", "Pune", "Hyderabad", "Gurugram"],
    "Canada": ["Toronto", "Montreal", "Vancouver", "Calgary", "Waterloo"],
    "Netherlands": ["Eindhoven", "Amsterdam", "Rotterdam", "Utrecht", "Delft"]
}


def generate_master_data(
    num_suppliers: int,
    rng: random.Random,
    base_date: date = date(2026, 1, 1),
) -> Tuple[List[Supplier], List[Site], List[Contract], Dict[str, str]]:
    """
    Generates deterministic Supplier, Site, and Contract master data.
    Returns:
        (suppliers, sites, contracts, supplier_archetypes)
    """
    suppliers: List[Supplier] = []
    sites: List[Site] = []
    contracts: List[Contract] = []
    supplier_archetypes: Dict[str, str] = {}
    
    contract_counter = 1

    categories = list(SupplierCategory)
    tiers = [SupplierTier.TIER_1, SupplierTier.TIER_2, SupplierTier.TIER_3]
    tier_weights = [0.25, 0.45, 0.30]
    
    financial_ratings = [
        FinancialStabilityRating.AAA,
        FinancialStabilityRating.AA,
        FinancialStabilityRating.A,
        FinancialStabilityRating.BBB,
        FinancialStabilityRating.BB,
        FinancialStabilityRating.B,
        FinancialStabilityRating.CCC,
    ]
    fin_weights = [0.15, 0.25, 0.30, 0.18, 0.07, 0.03, 0.02]

    # Archetypes to fulfill Step 4:
    # 70% stable, 15% deteriorating lead times, 10% quality incidents, 5% low-volume/missing data
    archetype_choices = ["STABLE", "DETERIORATING", "QUALITY_PRONE", "LOW_VOLUME"]
    archetype_weights = [0.70, 0.15, 0.10, 0.05]

    for i in range(1, num_suppliers + 1):
        sup_id = format_supplier_id(i)
        
        # Archetype assignment
        archetype = rng.choices(archetype_choices, weights=archetype_weights, k=1)[0]
        supplier_archetypes[sup_id] = archetype

        # Distinct company name
        prefix = rng.choice(COMPANY_PREFIXES)
        root = rng.choice(COMPANY_ROOTS)
        suffix = rng.choice(COMPANY_SUFFIXES)
        comp_name = f"{prefix} {root} {suffix} #{i}"

        tier = rng.choices(tiers, weights=tier_weights, k=1)[0]
        category = rng.choice(categories)
        country_name, _ = rng.choice(COUNTRIES)
        founded_year = rng.randint(1975, 2021)
        fin_rating = rng.choices(financial_ratings, weights=fin_weights, k=1)[0]
        
        created_timestamp = datetime(
            founded_year if founded_year >= 2020 else 2022,
            rng.randint(1, 12),
            rng.randint(1, 28),
            rng.randint(8, 17),
            0,
            0
        )

        sup_status = SupplierStatus.ACTIVE
        if archetype == "DETERIORATING" and rng.random() < 0.2:
            sup_status = SupplierStatus.UNDER_REVIEW

        supplier = Supplier(
            supplier_id=sup_id,
            name=comp_name,
            tier=tier,
            category=category,
            status=sup_status,
            country=country_name,
            founded_year=founded_year,
            financial_stability_rating=fin_rating,
            created_at=created_timestamp,
        )
        suppliers.append(supplier)

        # Generate 1 to 3 sites per supplier
        num_sites = 1 if archetype == "LOW_VOLUME" else rng.choices([1, 2, 3], weights=[0.5, 0.35, 0.15], k=1)[0]
        city_list = CITIES_BY_COUNTRY.get(country_name, ["Central Hub"])

        for s_idx in range(1, num_sites + 1):
            site_id = format_site_id(sup_id, s_idx)
            city = rng.choice(city_list)
            facility_type = FacilityType.MANUFACTURING if s_idx == 1 else rng.choice([FacilityType.ASSEMBLY, FacilityType.WAREHOUSE_DEPOT])
            monthly_capacity = rng.randint(20000, 250000)
            
            # Utilization
            util_ratio = rng.uniform(0.60, 0.82)
            if archetype == "DETERIORATING":
                util_ratio = rng.uniform(0.88, 0.98) # Overloaded site
            elif archetype == "LOW_VOLUME":
                util_ratio = rng.uniform(0.15, 0.35) # Underutilized site
                
            utilized_capacity = int(monthly_capacity * util_ratio)
            iso_certified = False if (archetype == "QUALITY_PRONE" and rng.random() < 0.4) else (rng.random() < 0.92)
            
            site = Site(
                site_id=site_id,
                supplier_id=sup_id,
                site_name=f"{comp_name} - {city} Facility {s_idx}",
                country=country_name,
                city=city,
                address=f"{rng.randint(100, 9999)} Industrial Parkway, Suite {s_idx * 10}",
                facility_type=facility_type,
                monthly_capacity_units=monthly_capacity,
                utilized_capacity_units=utilized_capacity,
                iso_certified=iso_certified,
                status=SiteStatus.OPERATIONAL,
                created_at=created_timestamp,
            )
            sites.append(site)

        # Generate 1 to 2 Contracts per supplier
        num_contracts = 1 if archetype == "LOW_VOLUME" else (2 if rng.random() < 0.25 else 1)
        for c_idx in range(num_contracts):
            contract_id = format_contract_id(contract_counter)
            contract_counter += 1
            
            start_dt = base_date - timedelta(days=rng.randint(180, 540))
            end_dt = base_date + timedelta(days=rng.randint(180, 540))
            
            contract = Contract(
                contract_id=contract_id,
                supplier_id=sup_id,
                contract_type=rng.choice(list(ContractType)),
                start_date=start_dt,
                end_date=end_dt,
                agreed_sla_otd_pct=round(rng.uniform(94.0, 99.0), 1),
                agreed_defect_ppm_threshold=rng.choice([100, 250, 500, 1000]),
                unit_price_ceiling=round(rng.uniform(25.0, 650.0), 2),
                payment_terms=rng.choice(["Net 30", "Net 45", "Net 60"]),
                status=ContractStatus.ACTIVE,
            )
            contracts.append(contract)

    return suppliers, sites, contracts, supplier_archetypes
