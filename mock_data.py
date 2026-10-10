"""
mock_data.py - Dynamic Routing, Telematics & Disruption Engine for TBS RoamAgent
SAMARTHA Hackathon Edition:
Features:
- Interactive Reverse Geocoding (Nominatim + Offline Landmark Fallback)
- Dynamic Bus Generation: generate_buses(source, destination) producing realistic
  Volvo, Sleeper, and Seater bus options between ANY two locations in India.
- Dynamic Smart Last-Mile Agent: Automatically pairs local transport (EV Auto / Bike)
  from the bus drop point to the exact map pin destination based on luggage and budget.
- Dynamic 45-Min Highway Delay Disruption Engine: Autonomously reschedules the local
  transit pickup time at zero extra charge with driver webhook synchronization.
"""

import re
import math
import random
from datetime import datetime, timedelta
from geopy.geocoders import Nominatim

# =========================================================================
# REVERSE GEOCODING & COORDINATE RESOLUTION
# =========================================================================

KNOWN_LANDMARKS = [
    ("Duvvada, Visakhapatnam", 17.7042, 83.1524),
    ("Visakhapatnam (RK Beach)", 17.7120, 83.3330),
    ("Gajuwaka, Visakhapatnam", 17.6900, 83.2100),
    ("Rushikonda Beach, Vizag", 17.7800, 83.3850),
    ("Simhachalam, Visakhapatnam", 17.7660, 83.2500),
    ("Anakapalle, Andhra Pradesh", 17.6890, 83.0030),
    ("Vizag RTC Complex Central", 17.7275, 83.3038),
    ("Kochi Vyttila Hub, Kerala", 9.9660, 76.3180),
    ("Ernakulam South, Kochi", 9.9680, 76.2920),
    ("Hyderabad Hitec City", 17.4470, 78.3760),
    ("Secunderabad Railway Hub", 17.4410, 78.5010),
    ("Nagole Metro Hub, Hyderabad", 17.3780, 78.5600),
    ("Vijayawada Benz Circle", 16.5000, 80.6400),
    ("Pandit Nehru Bus Station (PNBS)", 16.5100, 80.6200),
    ("Bengaluru Majestic Interchange", 12.9770, 77.5710),
    ("Whitefield Tech Park, Bengaluru", 12.9690, 77.7490),
    ("Chennai Koyambedu CMBT", 13.0690, 80.1910),
    ("T Nagar, Chennai", 13.0410, 80.2330),
    ("Tirupati Alipiri Gateway", 13.6500, 79.4000),
    ("Mumbai Dadar TT Circle", 19.0170, 72.8470),
    ("Pune Shivaji Nagar", 18.5310, 73.8440),
]

_geolocator = None

def get_geolocator():
    global _geolocator
    if _geolocator is None:
        try:
            _geolocator = Nominatim(user_agent="tbs_roamagent_hackathon_agent", timeout=3)
        except Exception:
            _geolocator = None
    return _geolocator

def reverse_geocode(lat, lng):
    """
    Resolves lat/lng to a clean, human-readable place name.
    1. Fast nearest-match check against high-accuracy landmarks (< 5km).
    2. Nominatim reverse geocode lookup (with timeout protection).
    3. Graceful fallback to nearest known region or formatted coordinate node.
    """
    # 1. Very close known landmark check (< 0.05 deg ~ 5km)
    best_dist = 999999.0
    best_name = None
    for name, k_lat, k_lng in KNOWN_LANDMARKS:
        dist = math.sqrt((lat - k_lat) ** 2 + (lng - k_lng) ** 2)
        if dist < best_dist:
            best_dist = dist
            best_name = name
    if best_dist < 0.05 and best_name:
        return best_name

    # 2. Try Nominatim Geocoder
    try:
        geo = get_geolocator()
        if geo:
            loc = geo.reverse((lat, lng), language="en", timeout=3)
            if loc and loc.raw and "address" in loc.raw:
                addr = loc.raw["address"]
                # Extract most relevant local name
                poi = addr.get("tourism") or addr.get("amenity") or addr.get("leisure") or addr.get("railway")
                suburb = addr.get("suburb") or addr.get("neighbourhood") or addr.get("residential") or addr.get("quarter")
                city = addr.get("city") or addr.get("town") or addr.get("village") or addr.get("municipality")
                district = addr.get("state_district") or addr.get("county")

                parts = []
                if poi:
                    parts.append(poi)
                if suburb and suburb not in parts:
                    parts.append(suburb)
                if city and city not in parts:
                    parts.append(city)
                elif district and district not in parts and len(parts) < 2:
                    parts.append(district)

                if parts:
                    return ", ".join(parts[:2])
    except Exception:
        pass

    # 3. Fallback: if within 30km of known landmark
    if best_dist < 0.35 and best_name:
        return best_name

    # 4. Fallback coordinate label
    return f"Transit Node ({lat:.2f}°N, {lng:.2f}°E)"

# =========================================================================
# HELPER TIME & CODE UTILITIES
# =========================================================================

def add_minutes_to_time_str(time_str, minutes=45):
    """Adds `minutes` to any time string like '06:00 AM' or '06:00 AM (Vizag RTC Complex)'."""
    match = re.search(r'(\d{1,2}):(\d{2})\s*(AM|PM)', str(time_str), re.IGNORECASE)
    if not match:
        return "07:00 AM"
    h, m, period = int(match.group(1)), int(match.group(2)), match.group(3).upper()
    if period == "PM" and h != 12:
        h += 12
    elif period == "AM" and h == 12:
        h = 0
    dt = datetime(2026, 1, 1, h, m) + timedelta(minutes=minutes)
    return dt.strftime("%I:%M %p")

def clean_code(name):
    """Produces clean 3-4 letter uppercase code from city or place name."""
    if not name:
        return "IND"
    # remove punctuation
    letters = re.sub(r'[^A-Za-z]', '', str(name)).upper()
    if len(letters) >= 3:
        return letters[:3]
    return (letters + "X")[:3]

def extract_primary_name(name):
    """Extracts base city or locality from a longer name like 'Duvvada, Visakhapatnam'."""
    if not name:
        return "Transit Destination"
    parts = [p.strip() for p in str(name).split(",") if p.strip()]
    if parts:
        # Check if first part contains parenthesis
        first = parts[0].split("(")[0].strip()
        return first if first else parts[0]
    return str(name)

# =========================================================================
# DYNAMIC BUS GENERATOR
# =========================================================================

def generate_buses(source, destination, budget=1500, luggage=2, comfort="Sleeper"):
    """
    Dynamically generates 3-4 realistic bus options (Volvo, Sleeper, Seater)
    with realistic ETA, timings, drop points, and prices between ANY two locations.
    """
    src_clean = extract_primary_name(source)
    dst_clean = extract_primary_name(destination)
    
    # Dynamic Drop Points in destination
    drop_points = [
        f"{dst_clean} Central RTC Complex",
        f"{dst_clean} Highway Bypass Bay",
        f"{dst_clean} Intermodal Transit Junction",
        f"{dst_clean} Express Toll Gateway"
    ]
    
    # Operators tailored dynamically
    operators_pool = [
        ("KSRTC SWIFT Deluxe Multi-Axle Volvo Sleeper", "Volvo Multi-Axle AC Sleeper", 1320, "04:30 PM", "06:00 AM", "13h 30m", "AC Lower Sleeper Berth LB-04", "🌟 Recommended Multi-Axle Sleeper", 4.8),
        ("VRL Logistics BharatBenz AC Sleeper", "BharatBenz Luxury AC Sleeper", 1250, "05:15 PM", "06:35 AM", "13h 20m", "AC Upper Sleeper Berth UB-08", "🛏️ Punctual Executive Sleeper", 4.7),
        ("IntrCity SmartBus Multi-Axle Semi-Sleeper", "Scania AC Semi-Sleeper", 950, "06:00 PM", "07:15 AM", "13h 15m", "Reclining Pushback Seat 14A", "💰 Value Budget Saver", 4.6),
        ("Express Line Air-Suspension Deluxe Seater", "Hi-Tech Air-Suspension Seater", 720, "07:30 PM", "07:45 AM", "12h 15m", "Window Seat 06B", "⚡ Rapid Non-Stop Transit", 4.5)
    ]

    # Adjust base price slightly around target budget if appropriate
    buses = []
    for idx, (op_name, b_type, base_cost, dep_time, arr_time, dur, berth, badge, rating) in enumerate(operators_pool):
        # Slightly modulate cost according to budget constraints if needed
        cost = base_cost
        if budget < 1000 and idx >= 2:
            cost = min(base_cost, budget - 80)
        
        bus_item = {
            "id": f"BUS-{clean_code(dst_clean)}-{idx+1:02d}",
            "operator": op_name,
            "bus_type": b_type,
            "source": source,
            "destination": destination,
            "departure": f"{dep_time} ({src_clean} Hub)",
            "departure_time": dep_time,
            "arrival": f"{arr_time} ({drop_points[idx % len(drop_points)]})",
            "arrival_time": arr_time,
            "arrival_point": drop_points[idx % len(drop_points)],
            "duration": dur,
            "berth": berth,
            "cost": cost,
            "rating": rating,
            "badge": badge,
            "telematics": "Live IoT GPS Tracking Active",
            "amenities": [
                f"Luggage Boot Space (Verified for {luggage} Bags)",
                "USB Charging Socket",
                "Personal AC Vent & Reading Light",
                "Blanket & Water Bottle"
            ]
        }
        buses.append(bus_item)

    return buses

# =========================================================================
# DYNAMIC SMART LAST-MILE AGENT
# =========================================================================

def generate_dynamic_last_mile(selected_bus, destination, luggage=2, budget=1500, coords=None):
    """
    Dynamically generates local transport (EV Auto / Bike / Cab) from the Bus Drop Point
    to the exact Map Pin / Destination location based on luggage and budget inputs.
    """
    arrival_time = selected_bus.get("arrival_time", "06:00 AM")
    bus_drop_loc = selected_bus.get("arrival_point", f"{extract_primary_name(destination)} RTC Complex")
    
    # 15 minutes transfer buffer
    pickup_time = add_minutes_to_time_str(arrival_time, 15)
    # 25 minutes local run
    drop_time = add_minutes_to_time_str(pickup_time, 25)

    # Dynamic Vehicle & Fleet Selection
    if luggage >= 2:
        mode = "Smart Local EV Auto"
        driver_name = "Ramesh K. (4.9 ⭐)"
        vehicle_no = "AP39-TX-4402 (Green EV Auto)"
        cost = 80
        rationale = (
            f"Evaluated {luggage} heavy suitcases. Assigned Smart Local EV Auto equipped with "
            f"heavy luggage roof carrier and flat floorboard at {bus_drop_loc} for safe luggage transit."
        )
        amenities = ["Luggage Roof Carrier", "Flat Floorboard", "Zero-Wait Driver Standby"]
    elif luggage == 1 and budget <= 800:
        mode = "Rapido / EV Bike Taxi"
        driver_name = "Suresh M. (4.8 ⭐)"
        vehicle_no = "AP39-BY-1904 (EV Bike)"
        cost = 45
        rationale = (
            f"Light luggage ({luggage} bag) and budget cap detected. Dispatched nimble Rapido EV Bike Taxi "
            f"from {bus_drop_loc} directly to {destination} for rapid peak-hour transit."
        )
        amenities = ["Sanitized Helmet Provided", "Backpack Luggage Carrier", "Fast Commute"]
    else:
        mode = "Smart Local EV Auto"
        driver_name = "Ramesh K. (4.9 ⭐)"
        vehicle_no = "AP39-TX-4402 (Green EV Auto)"
        cost = 80
        rationale = (
            f"Pre-coordinated dedicated Smart Local EV Auto at {bus_drop_loc} Bay 4 directly to {destination}."
        )
        amenities = ["Luggage Storage", "Verified Driver", "Zero Surge Pricing"]

    total_fare = selected_bus.get("cost", 1320) + cost

    dest_display = destination
    if coords:
        dest_display = f"{destination} [{coords[0]:.3f}, {coords[1]:.3f}]"

    return {
        "mode": mode,
        "driver_name": driver_name,
        "vehicle_no": vehicle_no,
        "pickup_loc": bus_drop_loc,
        "pickup_time": pickup_time,
        "drop_loc": dest_display,
        "drop_time": drop_time,
        "cost": cost,
        "total_fare": total_fare,
        "rationale": rationale,
        "amenities": amenities,
        "status": "CONFIRMED & SYNCED"
    }

# =========================================================================
# DYNAMIC DISRUPTION RECOVERY ENGINE
# =========================================================================

def generate_dynamic_disruption_recovery(selected_bus, last_mile, origin, destination, delay_minutes=45):
    """
    Autonomously reschedules the dynamic last-mile booking when an intercity highway delay occurs.
    - Intercity bus arrival shifts by delay_minutes.
    - Last-mile auto pickup shifts by delay_minutes automatically at ZERO extra charge.
    - Generates dynamic PNR, dispatch code, OTP, and updated visual timeline.
    """
    orig_clean = extract_primary_name(origin)
    dest_clean = extract_primary_name(destination)

    bus_arr_orig = selected_bus.get("arrival_time", "06:00 AM")
    auto_pick_orig = last_mile.get("pickup_time", "06:15 AM")
    auto_drop_orig = last_mile.get("drop_time", "06:40 AM")

    # Delayed times
    delayed_bus_arr = add_minutes_to_time_str(bus_arr_orig, delay_minutes)
    rescheduled_pickup = add_minutes_to_time_str(auto_pick_orig, delay_minutes)
    rescheduled_drop = add_minutes_to_time_str(auto_drop_orig, delay_minutes)

    pnr = f"TBS-{clean_code(orig_clean)}-{clean_code(dest_clean)}-V99"
    auto_code = f"AUTO-DISPATCH-{clean_code(dest_clean)}-EV42"
    otp = "5821"

    highlight = (
        f"Local {last_mile.get('mode', 'EV Auto')} pickup rescheduled automatically from "
        f"{auto_pick_orig} to {rescheduled_pickup} at zero extra charge!"
    )
    webhook_confirm = (
        f"Autonomous telematics webhook confirmed driver {last_mile.get('driver_name', 'Ramesh K.')} "
        f"will hold standby at {last_mile.get('pickup_loc')} until {rescheduled_pickup} with zero waiting penalty!"
    )

    timeline_steps = [
        {"node": origin, "time": selected_bus.get("departure_time", "04:30 PM"), "type": "origin"},
        {"transit": f"🚍 {selected_bus.get('operator', 'Intercity Bus')} (+{delay_minutes}m Highway Delay)", "duration": "Telematics Sync"},
        {"node": last_mile.get("pickup_loc"), "time": delayed_bus_arr, "type": "transfer"},
        {"transit": f"🛺 {last_mile.get('mode', 'EV Auto')} (Rescheduled)", "duration": "Zero Waiting Penalty"},
        {"node": destination, "time": rescheduled_drop, "type": "destination"}
    ]

    return {
        "pnr": pnr,
        "auto_dispatch_code": auto_code,
        "auto_otp": otp,
        "driver_name": last_mile.get("driver_name", "Ramesh K. (4.9 ⭐)"),
        "vehicle_no": last_mile.get("vehicle_no", "AP39-TX-4402"),
        "original_bus_arrival": bus_arr_orig,
        "delayed_bus_arrival": delayed_bus_arr,
        "original_auto_pickup": auto_pick_orig,
        "rescheduled_auto_pickup": rescheduled_pickup,
        "rescheduled_arrival": rescheduled_drop,
        "reschedule_highlight_en": highlight,
        "webhook_confirmation": webhook_confirm,
        "timeline_steps": timeline_steps,
        "delay_minutes": delay_minutes,
        "total_fare": last_mile.get("total_fare", 1400)
    }

# =========================================================================
# QUERY PARSING & FALLBACK COMPATIBILITY
# =========================================================================

def parse_travel_query(query_str):
    """Extracts origin, destination, deadline, budget, luggage from free-text string."""
    text = (query_str or "").strip()
    origin = "Kerala (Kochi)"
    dest = "Visakhapatnam (RK Beach)"
    
    # Check 'from X to Y' pattern
    match = re.search(r"from\s+([^,]+?)\s+to\s+([^,.\n]+)", text, re.IGNORECASE)
    if match:
        origin = match.group(1).strip()
        dest = match.group(2).strip()

    # Extract budget
    budget = 1500
    b_match = re.search(r"(?:under|below|budget|within|₹|rs\.?)\s*(\d{3,5})", text, re.IGNORECASE)
    if b_match:
        budget = int(b_match.group(1))

    # Extract luggage
    luggage = 2
    l_match = re.search(r"(\d)\s*(?:heavy\s*)?(?:bags|suitcases|luggage)", text, re.IGNORECASE)
    if l_match:
        luggage = int(l_match.group(1))

    # Extract deadline
    deadline = "09:00 AM"
    d_match = re.search(r"(?:by|before)\s*(\d{1,2}(?::\d{2})?\s*(?:AM|PM)?)", text, re.IGNORECASE)
    if d_match:
        deadline = d_match.group(1).upper()

    return {
        "origin": origin,
        "destination": dest,
        "budget": budget,
        "luggage": luggage,
        "deadline": deadline
    }

def resolve_city_profile(city_name):
    """Graceful city resolver for backwards compatibility."""
    return {
        "canonical": str(city_name),
        "gateways": [f"{city_name} Central Bay", f"{city_name} Bypass Gateway"],
        "terminals": [f"{city_name} Main Hub", f"{city_name} RTC Complex"],
        "has_metro": False,
        "metro_name": f"{city_name} Smart EV Auto Feeder"
    }
