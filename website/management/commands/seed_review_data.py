"""
Load realistic demo data for local review. Safe to run multiple times (slug-based upsert).

Usage:
  python manage.py seed_review_data
  python manage.py seed_review_data --wipe   # deletes seeded slugs first (see SEED_SLUGS)
"""

import hashlib
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from website.models import (
    Attraction,
    AttractionGalleryImage,
    BlogPost,
    CategoryGalleryImage,
    Destination,
    DestinationCategory,
    HomePageConfig,
    Lead,
    SitePage,
    SiteSettings,
    Testimonial,
    ThingToDo,
    ThingToDoGalleryImage,
    Tour,
    TourGalleryImage,
)

# Slugs owned by this seed (used with --wipe)
SEED_DEST_SLUGS = [
    "rome",
    "paris",
    "london",
    "venice",
    "florence",
    "barcelona",
    "amsterdam",
    "prague",
    "lisbon",
    "dublin",
]

SEED_BLOG_SLUGS = [
    "first-time-rome-7-day-itinerary",
    "paris-museum-pass-worth-it",
    "london-thames-walks",
    "venice-cicchetti-guide",
    "florence-duomo-without-lines",
    "barcelona-gaudi-beyond-sagrada",
    "italy-country-rail-guide",
    "europe-packing-light",
    "amsterdam-canal-photo-walk",
    "prague-castle-morning",
    "lisbon-tram-28-guide",
    "dublin-literary-pub-crawl",
    "rome-ostia-antica-day",
    "paris-versailles-audio",
    "london-hampton-court",
    "venice-murano-burano",
    "florence-pitti-boboli",
    "barcelona-montjuic-sunset",
    "food-wine-europe-introduction",
    "family-travel-museums",
    "photography-golden-hour-cities",
    "rainy-day-museum-routes",
    "train-sleepers-europe",
    "solo-travel-safety-tips",
    "christmas-markets-route",
    "summer-crowds-strategy",
    "accessible-travel-museums",
    "budget-eats-capital-cities",
    "night-photography-bridges",
    "tipping-guides-europe",
]

IMG = {
    "rome": "https://images.unsplash.com/photo-1552832230-c0197dd771b6?w=1200&q=80",
    "paris": "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=1200&q=80",
    "london": "https://images.unsplash.com/photo-1526129318478-62ed807ebdf9?w=1200&q=80",
    "venice": "https://images.unsplash.com/photo-1523906834658-6e24ef2386f9?w=1200&q=80",
    "florence": "https://images.unsplash.com/photo-1555993539-1732b0258235?w=1200&q=80",
    "barcelona": "https://images.unsplash.com/photo-1583422409516-2895a77efded?w=1200&q=80",
    "blog1": "https://images.unsplash.com/photo-1529154036614-a60975f5c760?w=1200&q=80",
    "blog2": "https://images.unsplash.com/photo-1499856871958-5b9627545d1a?w=1200&q=80",
    "blog3": "https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?w=1200&q=80",
    "blog4": "https://images.unsplash.com/photo-1476514525535-07fb3b4ae5f1?w=1200&q=80",
    "blog5": "https://images.unsplash.com/photo-1566073771259-6a8506099945?w=1200&q=80",
    "blog6": "https://images.unsplash.com/photo-1539037116277-4db20889f2d4?w=1200&q=80",
    "blog7": "https://images.unsplash.com/photo-1467269204594-9661b134dd2b?w=1200&q=80",
    "blog8": "https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=1200&q=80",
    "amsterdam": "https://images.unsplash.com/photo-1534351590666-13e3e96b5017?w=1200&q=80",
    "prague": "https://images.unsplash.com/photo-1541849546-216549ae216d?w=1200&q=80",
    "lisbon": "https://images.unsplash.com/photo-1585208798174-6cedd86e019a?w=1200&q=80",
    "dublin": "https://images.unsplash.com/photo-1590080876351-941da357a38c?w=1200&q=80",
    "t1": "https://images.unsplash.com/photo-1566127444979-b3d2b20e6d44?w=900&q=80",
    "t2": "https://images.unsplash.com/photo-1508672019048-805c876b67e2?w=900&q=80",
    "t3": "https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?w=900&q=80",
    "t4": "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=900&q=80",
    "t5": "https://images.unsplash.com/photo-1515542622106-78bda8ba0e5b?w=900&q=80",
    "t6": "https://images.unsplash.com/photo-1523906834658-6e24ef2386f9?w=900&q=80",
}

# Rotated across gallery rows (Unsplash — demo only)
GALLERY_POOL = [
    "https://images.unsplash.com/photo-1552832230-c0197dd771b6?w=800&q=80",
    "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=800&q=80",
    "https://images.unsplash.com/photo-1526129318478-62ed807ebdf9?w=800&q=80",
    "https://images.unsplash.com/photo-1523906834658-6e24ef2386f9?w=800&q=80",
    "https://images.unsplash.com/photo-1555993539-1732b0258235?w=800&q=80",
    "https://images.unsplash.com/photo-1583422409516-2895a77efded?w=800&q=80",
    "https://images.unsplash.com/photo-1534351590666-13e3e96b5017?w=800&q=80",
    "https://images.unsplash.com/photo-1541849546-216549ae216d?w=800&q=80",
    "https://images.unsplash.com/photo-1585208798174-6cedd86e019a?w=800&q=80",
    "https://images.unsplash.com/photo-1590080876351-941da357a38c?w=800&q=80",
    "https://images.unsplash.com/photo-1499856871958-5b9627545d1a?w=800&q=80",
    "https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?w=800&q=80",
    "https://images.unsplash.com/photo-1476514525535-07fb3b4ae5f1?w=800&q=80",
    "https://images.unsplash.com/photo-1566073771259-6a8506099945?w=800&q=80",
    "https://images.unsplash.com/photo-1539037116277-4db20889f2d4?w=800&q=80",
    "https://images.unsplash.com/photo-1467269204594-9661b134dd2b?w=800&q=80",
    "https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=800&q=80",
    "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=800&q=80",
    "https://images.unsplash.com/photo-1469474968028-56623f02e42e?w=800&q=80",
    "https://images.unsplash.com/photo-1508672019048-805c876b67e2?w=800&q=80",
]


class Command(BaseCommand):
    help = "Seed destinations, tours, blog posts, CMS pages, and sample lead for review."

    def add_arguments(self, parser):
        parser.add_argument(
            "--wipe",
            action="store_true",
            help="Remove blog posts and destinations (and dependents) with seeded slugs first.",
        )

    def handle(self, *args, **options):
        if options["wipe"]:
            self._wipe()
        with transaction.atomic():
            dest_map = self._seed_destinations()
            cat_map = self._seed_categories(dest_map)
            tour_map = self._seed_tours(dest_map, cat_map)
            att_map, thing_map = self._seed_attractions_things(dest_map)
            self._seed_blog(dest_map, tour_map, cat_map, att_map, thing_map)
            self._clear_seed_galleries()
            self._seed_galleries(cat_map, tour_map, att_map, thing_map)
            self._seed_testimonials(cat_map, tour_map, att_map, thing_map)
            self._seed_site_pages(dest_map, tour_map)
            self._seed_site_branding()
            self._seed_home_config()
            self._seed_sample_leads(dest_map)
        self.stdout.write(self.style.SUCCESS("Review data ready. Open /admin/ and the public site."))

    def _wipe(self):
        BlogPost.objects.filter(slug__in=SEED_BLOG_SLUGS).delete()
        Testimonial.objects.filter(author__endswith=" (seed)").delete()
        Destination.objects.filter(slug__in=SEED_DEST_SLUGS).delete()
        self.stdout.write("Wiped seeded destinations (cascaded), blog posts, and seed testimonials.")

    def _seed_destinations(self):
        rows = [
            {
                "slug": "rome",
                "name": "Rome",
                "summary": "Ancient ruins, Vatican City, and neighborhood trattorias — the Eternal City rewards slow walks and early starts.",
                "img": IMG["rome"],
                "home": True,
                "order": 1,
            },
            {
                "slug": "paris",
                "name": "Paris",
                "summary": "Art, café culture, and riverside sunsets. Perfect for first-timers and repeat visitors chasing hidden courtyards.",
                "img": IMG["paris"],
                "home": True,
                "order": 2,
            },
            {
                "slug": "london",
                "name": "London",
                "summary": "Royal history, world-class theatre, and markets from Borough to Columbia Road.",
                "img": IMG["london"],
                "home": True,
                "order": 3,
            },
            {
                "slug": "venice",
                "name": "Venice",
                "summary": "Canals, cicchetti bars, and islands beyond San Marco — see the lagoon before the crowds arrive.",
                "img": IMG["venice"],
                "home": True,
                "order": 4,
            },
            {
                "slug": "florence",
                "name": "Florence",
                "summary": "Renaissance masterpieces, Tuscan food, and hill towns a short train ride away.",
                "img": IMG["florence"],
                "home": True,
                "order": 5,
            },
            {
                "slug": "barcelona",
                "name": "Barcelona",
                "summary": "Gaudí architecture, Mediterranean beaches, and late-night tapas in Gràcia and El Born.",
                "img": IMG["barcelona"],
                "home": True,
                "order": 6,
            },
            {
                "slug": "amsterdam",
                "name": "Amsterdam",
                "summary": "Canal rings, world-class museums, and cycling culture — compact and endlessly photogenic.",
                "img": IMG["amsterdam"],
                "home": True,
                "order": 7,
            },
            {
                "slug": "prague",
                "name": "Prague",
                "summary": "Gothic spires, castle views, and cellar beer halls in the heart of Central Europe.",
                "img": IMG["prague"],
                "home": True,
                "order": 8,
            },
            {
                "slug": "lisbon",
                "name": "Lisbon",
                "summary": "Trams, tiles, Atlantic light, and custard tarts — hills worth climbing for the miradouros.",
                "img": IMG["lisbon"],
                "home": True,
                "order": 9,
            },
            {
                "slug": "dublin",
                "name": "Dublin",
                "summary": "Literary pubs, Georgian doors, and easy escapes to coast and Wicklow.",
                "img": IMG["dublin"],
                "home": True,
                "order": 10,
            },
        ]
        out = {}
        for r in rows:
            d, _ = Destination.objects.update_or_create(
                slug=r["slug"],
                defaults={
                    "name": r["name"],
                    "summary": r["summary"],
                    "listing_image_url": r["img"],
                    "show_on_homepage": r["home"],
                    "homepage_order": r["order"],
                },
            )
            out[r["slug"]] = d
        return out

    def _seed_categories(self, dest_map):
        """(name, slug, summary) — slug unique per destination"""
        spec = {
            "rome": [
                (
                    "Ancient Rome & Vatican",
                    "ancient-vatican",
                    "Colosseum, Forum, Palatine, and Vatican Museums — timed entries and historian guides.",
                ),
                (
                    "Food & Neighborhoods",
                    "food-neighborhoods",
                    "Trastevere, Testaccio, Prati — markets, trattorias, and aperitivo culture.",
                ),
                (
                    "Day Trips",
                    "day-trips",
                    "Ostia Antica, Tivoli, Castelli Romani — easy escapes by train or van.",
                ),
            ],
            "paris": [
                (
                    "Museums & Icons",
                    "museums-icons",
                    "Louvre, Orsay, Orangerie — skip-the-line routes and focused highlights.",
                ),
                (
                    "Seine & Districts",
                    "seine-districts",
                    "Île de la Cité, Marais, Montmartre — walks with local context.",
                ),
                (
                    "Food & Markets",
                    "food-markets",
                    "Marchés, boulangeries, wine bars — tastings and chef-led walks.",
                ),
            ],
            "london": [
                (
                    "Royal & Westminster",
                    "royal-westminster",
                    "Parliament, Westminster Abbey area, royal pageantry and timing tips.",
                ),
                (
                    "East End & Markets",
                    "east-end-markets",
                    "Borough, Spitalfields, street art — food and migration history.",
                ),
                (
                    "Literary & Thames",
                    "literary-thames",
                    "South Bank, Bloomsbury, riverside paths — stories and skyline views.",
                ),
            ],
            "venice": [
                (
                    "St. Mark's & Doge",
                    "st-marks-doge",
                    "Basilica, Doge's Palace, piazza logistics — beat the midday crush.",
                ),
                (
                    "Islands & Lagoon",
                    "islands-lagoon",
                    "Murano, Burano, Torcello — vaporetto and private boat options.",
                ),
                (
                    "Cicchetti & Wine",
                    "cicchetti-wine",
                    "Bacari near Rialto and beyond — stand-up culture done right.",
                ),
            ],
            "florence": [
                (
                    "Duomo & Museums",
                    "duomo-museums",
                    "Brunelleschi's dome, Uffizi, Accademia — tickets and dress codes.",
                ),
                (
                    "Tuscany Outings",
                    "tuscany-outings",
                    "Chianti, Siena, Pisa day trips — wine, hills, and medieval towns.",
                ),
                (
                    "Food & Artisan",
                    "food-artisan",
                    "Sant'Ambrogio, leather, gelato — hands-on and edible.",
                ),
            ],
            "barcelona": [
                (
                    "Gaudí & Modernisme",
                    "gaudi-modernisme",
                    "Sagrada Família, Batlló, Milà — timed slots and rooftop drama.",
                ),
                (
                    "Gothic Quarter & Sea",
                    "gothic-sea",
                    "Roman grid, cathedral, Barceloneta — old and new side by side.",
                ),
                (
                    "Tapas & Night",
                    "tapas-night",
                    "Pintxos crawl, vermut, late plates in Gràcia and Born.",
                ),
            ],
            "amsterdam": [
                (
                    "Canals & Museums",
                    "amsterdam-canals",
                    "Rijksmuseum, Van Gogh, canal cruises — tickets and quiet hours.",
                ),
                (
                    "Food & Markets",
                    "amsterdam-food",
                    "Albert Cuyp, Indonesian rijsttafel, brown cafés — multicultural bites.",
                ),
                (
                    "Day Trips",
                    "amsterdam-day-trips",
                    "Zaanse Schans, Haarlem, Utrecht — windmills and mercantile towns.",
                ),
            ],
            "prague": [
                (
                    "Castle & Old Town",
                    "prague-castle-town",
                    "Charles Bridge at dawn, castle complex, astronomical clock context.",
                ),
                (
                    "Beer & Culture",
                    "prague-beer",
                    "Historic halls, microbreweries, and Czech pub etiquette.",
                ),
                (
                    "Day Trips",
                    "prague-day-trips",
                    "Kutná Hora, Český Krumlov ideas — bone church and Bohemia beyond Prague.",
                ),
            ],
            "lisbon": [
                (
                    "Alfama & Tiles",
                    "lisbon-alfama",
                    "Tram 28, miradouros, azulejo workshops — hills with payoff views.",
                ),
                (
                    "Belém & River",
                    "lisbon-belem",
                    "Monastery, tower, pastéis de Belém — maritime golden age.",
                ),
                (
                    "Food & Fado",
                    "lisbon-food-fado",
                    "Petiscos, ginjinha, intimate fado houses — where locals listen.",
                ),
            ],
            "dublin": [
                (
                    "History & Literature",
                    "dublin-history-lit",
                    "Trinity, Book of Kells, Georgian squares — pages and pavement.",
                ),
                (
                    "Pubs & Music",
                    "dublin-pubs-music",
                    "Traditional sessions, whiskey stories, and pub architecture.",
                ),
                (
                    "Coast & Wicklow",
                    "dublin-coast",
                    "Howth cliff walk, Wicklow Mountains — green on the city's edge.",
                ),
            ],
        }
        cmap = {}
        for dslug, cats in spec.items():
            d = dest_map[dslug]
            cmap[dslug] = {}
            for name, cslug, summary in cats:
                c, _ = DestinationCategory.objects.update_or_create(
                    destination=d,
                    slug=cslug,
                    defaults={"name": name, "summary": summary},
                )
                cmap[dslug][cslug] = c
        return cmap

    @staticmethod
    def _tour_booking_defaults(tslug: str, dslug: str, cslug: str) -> dict:
        h = int(hashlib.md5(tslug.encode()).hexdigest()[:8], 16)
        currency = "EUR"
        price = Decimal(48 + (h % 118))
        if dslug == "london":
            currency = "GBP"
            price = Decimal(39 + (h % 85))
        elif dslug in ("amsterdam", "prague", "dublin"):
            currency = "EUR"
            price = Decimal(42 + (h % 95))
        rating = Decimal("4.2") + Decimal(min(7, h % 8)) * Decimal("0.1")
        if rating > Decimal("5"):
            rating = Decimal("5")
        reviews = 140 + (h % 3800)
        duration = Decimal("2") + Decimal((h % 20)) * Decimal("0.25")
        if any(
            x in cslug
            for x in (
                "food",
                "cicchetti",
                "tapas",
                "tasting",
                "crawl",
                "wine",
                "pub",
                "fado",
            )
        ):
            duration = max(duration, Decimal("3"))
        if "day-trips" in cslug or "day-trips" in tslug or "half-day" in tslug:
            duration = max(duration, Decimal("4.5"))
        group_sizes = (8, 10, 12, 14, 16, 20, 25)
        group_max = group_sizes[h % len(group_sizes)]
        langs_pool = (
            "English",
            "English, Italian",
            "English, Spanish",
            "English, French",
            "English, German",
            "English, Dutch",
            "English, Portuguese",
        )
        languages = langs_pool[h % len(langs_pool)]
        skip_keys = (
            "colosseum",
            "vatican",
            "louvre",
            "uffizi",
            "sagrada",
            "doges",
            "rijksmuseum",
            "book-kells",
            "tower-of-london",
            "accademia",
            "prague-castle",
            "evening-canal",
            "murano",
            "castle-complex",
            "zaanse",
            "kutna",
            "st-marks",
            "basilica",
        )
        skip_the_line = any(k in tslug for k in skip_keys)
        wheelchair = h % 10 == 0
        free_cancel = h % 19 != 0
        return {
            "price_from": price,
            "currency": currency,
            "rating_average": rating,
            "review_count": reviews,
            "duration_hours": duration.quantize(Decimal("0.01")),
            "group_size_max": group_max,
            "languages": languages,
            "free_cancellation": free_cancel,
            "skip_the_line": skip_the_line,
            "wheelchair_accessible": wheelchair,
        }

    def _seed_tours(self, dest_map, cat_map):
        tours_data = [
            # Rome
            (
                "rome",
                "ancient-vatican",
                "colosseum-forum-small-group",
                "Colosseum & Roman Forum — Small Group",
                "Skip-the-line entry with a historian guide. Includes arena floor where available.",
                "Meet near Colosseo metro. We enter through priority access, explore the amphitheatre levels, then walk the Via Sacra through the Forum to the Palatine. Your guide connects emperors, gladiators, and daily Roman life.\n\nDuration: 3 hours. Moderate walking. Headsets provided.",
                IMG["t1"],
            ),
            (
                "rome",
                "ancient-vatican",
                "vatican-museums-sistine",
                "Vatican Museums & Sistine Chapel",
                "Early-access option to beat peak crowds; full route with Michelangelo focus.",
                "Highlights: Pio-Clementino Museum, Gallery of Maps, Raphael Rooms, and the Sistine Chapel. We explain restoration stories and what to notice in the ceiling frescoes.\n\nDress code: shoulders and knees covered. No photography in the Sistine Chapel.",
                IMG["t2"],
            ),
            (
                "rome",
                "food-neighborhoods",
                "trastevere-food-evening",
                "Trastevere Evening Food Walk",
                "Fried artichokes, supplì, gelato, and natural wine in family-run spots.",
                "We visit 6–7 tasting stops over ~3 hours. Vegetarian options available on request. Small groups max 12.",
                IMG["t3"],
            ),
            # Paris
            (
                "paris",
                "museums-icons",
                "louvre-highlights",
                "Louvre Highlights — Guided",
                "Mona Lisa, Winged Victory, and French masters without getting lost.",
                "We use a curated 2-hour route: medieval foundations, Italian Renaissance, and Denon wing icons. After the tour you may stay inside independently.",
                IMG["t4"],
            ),
            (
                "paris",
                "seine-districts",
                "montmartre-walking",
                "Montmartre Walking Tour",
                "Sacré-Cœur, hidden vineyards, and the village streets behind the postcard view.",
                "Start at Abbesses metro, climb to the basilica terrace (free entry to church), then descend through Villa Léandre and artists' squares. Finish near the funicular with café recommendations.",
                IMG["t5"],
            ),
            # London
            (
                "london",
                "royal-westminster",
                "westminster-royal",
                "Westminster Royal Walking Tour",
                "Parliament, Westminster Abbey exterior, and Changing of the Guard timing tips.",
                "Route covers Parliament Square, Jewel Tower, St Margaret's, and best photo angles for Big Ben restoration wrap. Guard timing varies — we text the group the night before.",
                IMG["t6"],
            ),
            (
                "london",
                "east-end-markets",
                "borough-market-tasting",
                "Borough Market Tasting Tour",
                "British cheeses, street food, and the stories behind London's oldest food market.",
                "Eight tasting stops with dietary swaps. Includes Southwark Cathedral exterior and Thames path to Tate Modern if time allows. Wear comfortable shoes — cobbles are uneven.",
                IMG["t1"],
            ),
            # Venice
            (
                "venice",
                "st-marks-doge",
                "doges-palace-secret-itineraries",
                "Doge's Palace & Bridge of Sighs",
                "Skip-the-line palace interior with prisons and council chambers.",
                "See the Great Council hall, Bridge of Sighs crossing, and lead-roof prisons. Your guide explains the thousand-year republic in one coherent arc. Combine with an optional St Mark's Basilica add-on.",
                IMG["t2"],
            ),
            (
                "venice",
                "cicchetti-wine",
                "cicchetti-crawl-rialto",
                "Rialto Cicchetti Crawl",
                "Stand-up bites and ombra wine near the market — like locals.",
                "We visit five bacari between Rialto and San Polo. Learn to order ombra and spritz, try baccalà and polpette, and end with a digestivo. Not a seated dinner — pace yourself.",
                IMG["t3"],
            ),
            # Florence
            (
                "florence",
                "duomo-museums",
                "uffizi-highlights",
                "Uffizi Gallery Highlights",
                "Botticelli, Leonardo, and Michelangelo with priority entry.",
                "Timed entry through Door 3; 90-minute narrative through late Gothic to High Renaissance. Headsets for groups over 6. Optional add-on: Boboli Gardens same afternoon.",
                IMG["t4"],
            ),
            (
                "florence",
                "tuscany-outings",
                "chianti-half-day",
                "Chianti Villages Half-Day",
                "Two hill towns, olive oil tasting, and vineyard views.",
                "Van pickup near SMN station. Greve in Chianti market stop, second village for wine and oil flight, return by late afternoon. Minimum age 12 for wine tasting; juice alternative available.",
                IMG["t5"],
            ),
            # Barcelona
            (
                "barcelona",
                "gaudi-modernisme",
                "sagrada-familia-towers",
                "Sagrada Família with Tower Access",
                "Nativity façade, interior forest of columns, and tower climb when available.",
                "Tower slots subject to wind closures — we refund tower portion if cancelled. Interior visit covers Nativity passion portals and stained-glass light paths. Audio guide app included.",
                IMG["t6"],
            ),
            (
                "barcelona",
                "gothic-sea",
                "gothic-quarter-deep-dive",
                "Gothic Quarter Deep Dive",
                "Roman walls, Jewish quarter history, and cathedral cloister.",
                "Plaça del Rei, Temple of Augustus columns, El Call lanes, and Barcelona Cathedral cloister (entry ticket not always included — check season). Flat route, ~2 km.",
                IMG["t1"],
            ),
            (
                "rome",
                "day-trips",
                "ostia-antica-half-day",
                "Ostia Antica Half-Day",
                "Rome's ancient port — mosaics and apartment blocks without Pompeii crowds.",
                "Regional train from Piramide; 2.5 hours on site with an archaeologist. Good footwear; little shade in summer.",
                IMG["t2"],
            ),
            (
                "rome",
                "food-neighborhoods",
                "testaccio-market-morning",
                "Testaccio Market Morning",
                "Volpetti tasting counter, trapizzino, and coffee with locals.",
                "Small-group walk focused on Roman street food evolution. Saturday mornings busiest.",
                IMG["t3"],
            ),
            (
                "paris",
                "museums-icons",
                "orsay-impressionists",
                "Musée d'Orsay Impressionists",
                "Clock hall, Van Gogh, Monet — 90 minutes that hit the hits.",
                "Timed ticket bundle options with Rodin nearby. Not on Mondays when museum closed.",
                IMG["t4"],
            ),
            (
                "paris",
                "food-markets",
                "marais-chocolate-walk",
                "Marais Chocolate & Pastry",
                "Bean-to-bar stops and viennoiserie in the 3rd and 4th.",
                "Sweet-forward; savoury add-on available. Approx. 2 hours.",
                IMG["t5"],
            ),
            (
                "london",
                "royal-westminster",
                "tower-of-london-crowns",
                "Tower of London & Crown Jewels",
                "Yeoman stories, White Tower, and jewel house timing strategy.",
                "We book early slots to reduce jewel room wait. Not fully step-free.",
                IMG["t6"],
            ),
            (
                "london",
                "literary-thames",
                "south-bank-story-walk",
                "South Bank Story Walk",
                "Globe, Tate, street performers — narrative from Shakespeare to today.",
                "Flat 3 km; ends near Borough for optional lunch.",
                IMG["t1"],
            ),
            (
                "venice",
                "islands-lagoon",
                "murano-burano-morning",
                "Murano & Burano Morning",
                "Glass demo slot plus lace island photo stops.",
                "Vaporetto passes explained; private water taxi upgrade on request.",
                IMG["t2"],
            ),
            (
                "florence",
                "duomo-museums",
                "accademia-david-express",
                "Accademia David Express",
                "Michelangelo's David with priority entry and statue context.",
                "45–60 minutes inside; pairs well with our Uffizi same day.",
                IMG["t3"],
            ),
            (
                "florence",
                "food-artisan",
                "oltrarno-artisan-walk",
                "Oltrarno Artisan Walk",
                "Leather, gold leaf, and small botteghe away from the Duomo crush.",
                "Hands-on demo where schedules allow.",
                IMG["t4"],
            ),
            (
                "barcelona",
                "gaudi-modernisme",
                "casa-batllo-skip-line",
                "Casa Batlló Skip-the-Line",
                "Gaudí's dragon roof and modernist interiors with audio guide.",
                "Night sessions available seasonally; check facade lighting.",
                IMG["t5"],
            ),
            (
                "barcelona",
                "tapas-night",
                "el-born-tapas-crawl",
                "El Born Tapas Crawl",
                "Vermut, anchovies, croquetas — standing room only classics.",
                "Dietary notes welcome in advance.",
                IMG["t6"],
            ),
            (
                "amsterdam",
                "amsterdam-canals",
                "evening-canal-cruise",
                "Evening Canal Cruise",
                "Glass-top boat, bridges lit, commentary on Golden Age trade.",
                "Board near Centraal; blankets on chill nights.",
                IMG["amsterdam"],
            ),
            (
                "amsterdam",
                "amsterdam-canals",
                "rijksmuseum-highlights",
                "Rijksmuseum Highlights",
                "Night Watch, Vermeer room, ship models — 2-hour curator route.",
                "Timed tickets; museum busy Easter week.",
                IMG["t1"],
            ),
            (
                "amsterdam",
                "amsterdam-day-trips",
                "zaanse-schans-windmills",
                "Zaanse Schans Windmills",
                "Clogs, cheese barns, and working windmills north of Amsterdam.",
                "Half-day by coach; free time for photos.",
                IMG["t2"],
            ),
            (
                "prague",
                "prague-castle-town",
                "prague-castle-complex",
                "Prague Castle Complex",
                "St. Vitus, Old Royal Palace, Golden Lane — ticket strategy explained.",
                "Uphill start; midday bands optional. 3+ hours.",
                IMG["prague"],
            ),
            (
                "prague",
                "prague-beer",
                "historic-pub-crawl",
                "Historic Pub Crawl",
                "Cellars, pilsner lore, and Czech snacks with a local host.",
                "18+; pace yourself — portions are hearty.",
                IMG["t3"],
            ),
            (
                "prague",
                "prague-day-trips",
                "kutna-hora-bone-church",
                "Kutná Hora Bone Church Day",
                "Sedlec Ossuary and St. Barbara's cathedral by train.",
                "Full day; moderate walking in old town Kutná Hora.",
                IMG["t4"],
            ),
            (
                "lisbon",
                "lisbon-alfama",
                "tram-28-photo-walk",
                "Tram 28 Photo Walk",
                "Strategic stops for miradouros without riding the whole line twice.",
                "Early start recommended; trams can be crowded.",
                IMG["lisbon"],
            ),
            (
                "lisbon",
                "lisbon-belem",
                "belem-monuments-walk",
                "Belém Monuments Walk",
                "Tower, monastery exterior, pasteis queue strategy.",
                "Combined tickets where it saves time.",
                IMG["t5"],
            ),
            (
                "lisbon",
                "lisbon-food-fado",
                "alfama-fado-evening",
                "Alfama Fado Evening",
                "Intimate house with dinner option — respect the listening silence.",
                "Dress smart-casual; shows start on time.",
                IMG["t6"],
            ),
            (
                "dublin",
                "dublin-history-lit",
                "trinity-book-kells",
                "Trinity & Book of Kells",
                "Long Room library and illuminated manuscript context.",
                "Timed campus entry; bags restricted.",
                IMG["dublin"],
            ),
            (
                "dublin",
                "dublin-coast",
                "howth-cliff-walk",
                "Howth Cliff Walk",
                "Loop trail, harbour seafood, and Dublin Bay views.",
                "Weather-dependent; windproof layer advised.",
                IMG["t1"],
            ),
            (
                "dublin",
                "dublin-pubs-music",
                "temple-bar-music-crawl",
                "Traditional Music Pub Crawl",
                "Sessions away from only the tourist traps — quality over volume.",
                "Standing room; earplugs optional for tin whistles!",
                IMG["t2"],
            ),
        ]
        tmap = {}
        for row in tours_data:
            dslug, cslug, tslug, title, teaser, body, limg = row
            d = dest_map[dslug]
            cat = cat_map[dslug].get(cslug)
            booking = self._tour_booking_defaults(tslug, dslug, cslug)
            t, _ = Tour.objects.update_or_create(
                destination=d,
                slug=tslug,
                defaults={
                    "category": cat,
                    "name": title,
                    "teaser": teaser,
                    "body": body,
                    "listing_image_url": limg or "",
                    **booking,
                },
            )
            tmap[tslug] = t
        return tmap

    def _seed_attractions_things(self, dest_map):
        attr_spec = {
            "rome": [
                ("trevi-fountain", "Trevi Fountain", "Baroque masterpiece; early morning or late evening for thinner crowds."),
                ("pantheon", "Pantheon", "Best-preserved ancient temple; dome, oculus, and free entry to the church."),
                ("colosseum-exterior", "Colosseum (exterior arcades)", "Golden-hour photos from Via dei Fori Imperiali without a ticket."),
            ],
            "paris": [
                ("eiffel-tower", "Eiffel Tower", "Book summit or second floor ahead; sunset picnics on Champ de Mars."),
                ("louvre-pyramid", "Louvre Pyramid & Cour Napoléon", "Iconic entrance; arrive at opening for fewer people in frame."),
                ("sacre-coeur-terrace", "Sacré-Cœur terrace", "Free basilica entry; wide Paris views from the steps."),
            ],
            "london": [
                ("tower-bridge", "Tower Bridge", "Glass floor walkways; combine with Design Museum or St Katharine Docks."),
                ("british-museum-great-court", "British Museum Great Court", "Free entry; focus one gallery per visit to avoid overload."),
                ("westminster-abbey-exterior", "Westminster Abbey (exterior)", "Poets' Corner inside needs ticket — exterior Gothic detail is free to admire."),
            ],
            "venice": [
                ("st-marks-square", "Piazza San Marco", "Café orchestras cost a premium — stand in the middle for free acoustics."),
                ("rialto-bridge", "Rialto Bridge", "Market mornings on the San Polo side; sunset crowds on the bridge."),
                ("doge-palace-facade", "Doge's Palace façade", "Gothic pink stone and waterfront perspective before you go inside."),
            ],
            "florence": [
                ("duomo-complex", "Duomo complex (exterior)", "Baptistery doors, bell tower, and Brunelleschi's dome from Piazza del Duomo."),
                ("ponte-vecchio", "Ponte Vecchio", "Gold shops and Arno views; cross at dusk for softer light."),
                ("uffizi-exterior", "Uffizi & Loggia dei Lanzi", "Outdoor sculptures free to browse; timed tickets for the gallery."),
            ],
            "barcelona": [
                ("sagrada-familia-exterior", "Sagrada Família (exterior)", "Nativity façade detail without entering — still spectacular."),
                ("park-guell-terrace", "Park Güell", "Mosaic benches and city views; perimeter walks possible without a ticket slot."),
                ("barcelona-cathedral", "Barcelona Cathedral", "Gothic cloister with geese; dress modestly for entry."),
            ],
            "amsterdam": [
                ("rijksmuseum-building", "Rijksmuseum building", "Cuypers architecture and pond reflections — worth the approach walk."),
                ("anne-frank-area", "Anne Frank House area", "Book tickets weeks ahead; quiet Jordaan lanes nearby if you miss a slot."),
                ("canal-belt-facades", "Canal belt gables", "Herengracht to Prinsengracht — hook, neck, and step gables in one stroll."),
            ],
            "prague": [
                ("charles-bridge", "Charles Bridge", "Sculptures and musicians; dawn for mist, midnight for fewer tourists."),
                ("astronomical-clock", "Old Town Astronomical Clock", "Hourly show draws crowds — watch from the side streets."),
                ("prague-castle-gates", "Prague Castle gates", "Changing guard at noon; St. Vitus spires from Hradčany square."),
            ],
            "lisbon": [
                ("belem-tower", "Belém Tower", "Manueline stone lace; tide affects how close you get to the waterline."),
                ("alfama-miradouros", "Alfama miradouros", "Portas do Sol and Santa Luzia — tram noise vs postcard views."),
                ("comercio-arc", "Arco da Rua Augusta", "Elevator to the top for river and grid views (ticketed)."),
            ],
            "dublin": [
                ("trinity-college-front", "Trinity College front square", "Campus gates to Book of Kells — book a timed ticket."),
                ("ha-penny-bridge", "Ha'penny Bridge", "Pedestrian cast iron over the Liffey; quick crossing, big photo payoff."),
                ("guinness-storehouse-sky", "Guinness Storehouse Gravity Bar", "360° Dublin views with a pint — book ahead on weekends."),
            ],
        }
        thing_spec = {
            "rome": [
                ("aperitivo-prati", "Aperitivo in Prati", "Spritz culture near the Vatican — calmer than centro storico."),
                ("appian-bike", "Appian Way bike ride", "Rentals toward the aqueduct park; half-day with catacomb stops."),
                ("testaccio-market-lunch", "Testaccio market lunch", "Trapizzino, trippa, and natural wine in a local food hall."),
            ],
            "paris": [
                ("seine-cruise", "Evening Seine cruise", "Glass boats from Pont Neuf; illuminations after dark."),
                ("marais-gallery-hop", "Marais gallery afternoon", "Small contemporary spaces between cafés and vintage shops."),
                ("latin-quarter-jazz", "Latin Quarter jazz cellar", "Intimate sets in stone vaults — arrive early for a seat."),
            ],
            "london": [
                ("borough-breakfast", "Borough Market breakfast", "Coffee, bacon sandwiches, and doughnuts before the lunch rush."),
                ("thames-path-run", "Thames Path morning run", "Westminster to Tate Modern — flat, scenic, busy with commuters."),
                ("columbia-road-sunday", "Columbia Road flowers", "Sunday market — go early for stems and street musicians."),
            ],
            "venice": [
                ("vaporetto-grand-canal", "Vaporetto Grand Canal", "Line 1 slow boat — best cheap sightseeing seat in town."),
                ("burano-half-day", "Burano colour walk", "Lace shops and rainbow houses; ferry time built into the day."),
                ("spritz-campo", "Campo spritz hour", "Stand at a bar in Campo Santa Margherita with students and locals."),
            ],
            "florence": [
                ("oltrarno-apertivo", "Oltrarno aperitivo", "Piazza Santo Spirito benches and natural wine bars."),
                ("fiesole-sunset-bus", "Fiesole sunset bus", "Short ride uphill for Arno glow over the Duomo."),
                ("sant-ambrogio-market", "Sant'Ambrogio market morning", "Locals' produce hall — coffee and schiacciata at the counter."),
            ],
            "barcelona": [
                ("barceloneta-dip", "Barceloneta dip", "Urban beach swim June–September; showers and chiringuitos."),
                ("gracia-festivals", "Gràcia festival streets", "August block parties — each street competes in decorations."),
                ("montserrat-half-day", "Montserrat day idea", "Cog railway, boys' choir (schedule varies), mountain trails."),
            ],
            "amsterdam": [
                ("vondelpark-picnic", "Vondelpark picnic", "Open-air theatre in summer; rent a blanket spot by the pond."),
                ("nine-streets-shopping", "Nine Streets boutiques", "Compact indie shops between the main canals."),
                ("north-ferry-sunset", "NDSM ferry sunset", "Free ferry behind Centraal — waterfront cranes and skyline."),
            ],
            "prague": [
                ("petrin-tower-walk", "Petřín hill funicular", "Mini Eiffel views; forest paths down to Malá Strana."),
                ("beer-hall-reservation", "Historic beer hall dinner", "Long tables — reserve or arrive at opening for seats."),
                ("jazz-boat-prague", "Evening jazz cruise", "Vltava music boats — layer up on deck."),
            ],
            "lisbon": [
                ("pasteis-belem-queue", "Pastéis de Belém", "Takeaway line moves fast; sit inside for table service."),
                ("lx-factory-sunday", "LX Factory Sunday", "Street food, bookshops, and river walks in a converted industrial strip."),
                ("cascais-train", "Cascais train coastal", "Cheap seaside escape — last stop beaches west of the city."),
            ],
            "dublin": [
                ("literary-pub-crawl", "Literary pub crawl", "Joyce and Beckett haunts with live readings in select venues."),
                ("howth-cliff-walk", "Howth Cliff Path", "Loop trail and seafood chowder in the harbour."),
                ("phoenix-park-deer", "Phoenix Park deer spotting", "Morning light near the Papal Cross — keep a respectful distance."),
            ],
        }
        att_map = {s: {} for s in SEED_DEST_SLUGS}
        thing_map = {s: {} for s in SEED_DEST_SLUGS}
        for dslug in SEED_DEST_SLUGS:
            d = dest_map[dslug]
            for slug, name, summary in attr_spec[dslug]:
                a, _ = Attraction.objects.update_or_create(
                    destination=d,
                    slug=slug,
                    defaults={"name": name, "summary": summary},
                )
                att_map[dslug][slug] = a
            for slug, name, summary in thing_spec[dslug]:
                t, _ = ThingToDo.objects.update_or_create(
                    destination=d,
                    slug=slug,
                    defaults={"name": name, "summary": summary},
                )
                thing_map[dslug][slug] = t
        return att_map, thing_map

    def _clear_seed_galleries(self):
        CategoryGalleryImage.objects.filter(
            category__destination__slug__in=SEED_DEST_SLUGS
        ).delete()
        TourGalleryImage.objects.filter(tour__destination__slug__in=SEED_DEST_SLUGS).delete()
        AttractionGalleryImage.objects.filter(
            attraction__destination__slug__in=SEED_DEST_SLUGS
        ).delete()
        ThingToDoGalleryImage.objects.filter(
            thing_to_do__destination__slug__in=SEED_DEST_SLUGS
        ).delete()

    def _seed_galleries(self, cat_map, tour_map, att_map, thing_map):
        def pool_url(i):
            return GALLERY_POOL[i % len(GALLERY_POOL)]

        n = 0
        for dslug, cats in cat_map.items():
            for cslug, cat in cats.items():
                for k in range(3):
                    CategoryGalleryImage.objects.create(
                        category=cat,
                        image_url=pool_url(n),
                        alt_text=f"{cat.name} — gallery {k + 1}",
                        sort_order=k,
                    )
                    n += 1
        for tslug, tour in tour_map.items():
            for k in range(2):
                TourGalleryImage.objects.create(
                    tour=tour,
                    image_url=pool_url(n),
                    alt_text=f"{tour.name} — photo {k + 1}",
                    sort_order=k,
                )
                n += 1
        for dslug, by_slug in att_map.items():
            for aslug, att in by_slug.items():
                for k in range(2):
                    AttractionGalleryImage.objects.create(
                        attraction=att,
                        image_url=pool_url(n),
                        alt_text=f"{att.name} — {k + 1}",
                        sort_order=k,
                    )
                    n += 1
        for dslug, by_slug in thing_map.items():
            for tslug, thing in by_slug.items():
                for k in range(2):
                    ThingToDoGalleryImage.objects.create(
                        thing_to_do=thing,
                        image_url=pool_url(n),
                        alt_text=f"{thing.name} — {k + 1}",
                        sort_order=k,
                    )
                    n += 1

    def _seed_testimonials(self, cat_map, tour_map, att_map, thing_map):
        Testimonial.objects.filter(author__endswith=" (seed)").delete()
        quotes = [
            ("Our Colosseum guide made the Forum click — worth every euro.", "Maya K. (seed)", ["colosseum-forum-small-group"], [("rome", "ancient-vatican")], [("rome", "colosseum-exterior")], [("rome", "appian-bike")]),
            ("Louvre in two hours without feeling rushed — miracle.", "Jonas P. (seed)", ["louvre-highlights"], [("paris", "museums-icons")], [("paris", "louvre-pyramid")], [("paris", "seine-cruise")]),
            ("Westminster walk + guard timing text saved our morning.", "Claire D. (seed)", ["westminster-royal"], [("london", "royal-westminster")], [("london", "westminster-abbey-exterior")], [("london", "borough-breakfast")]),
            ("Cicchetti crawl was delicious chaos — exactly as promised.", "Elena V. (seed)", ["cicchetti-crawl-rialto"], [("venice", "cicchetti-wine")], [("venice", "rialto-bridge")], [("venice", "spritz-campo")]),
            ("Uffizi headset tour kept our teens engaged.", "Tom & Sue (seed)", ["uffizi-highlights"], [("florence", "duomo-museums")], [("florence", "uffizi-exterior")], [("florence", "oltrarno-apertivo")]),
            ("Sagrada tower slot worked; refund policy was fair when wind closed it.", "Ricardo M. (seed)", ["sagrada-familia-towers"], [("barcelona", "gaudi-modernisme")], [("barcelona", "sagrada-familia-exterior")], [("barcelona", "barceloneta-dip")]),
            ("Canal cruise at blue hour — photos I'll reprint.", "Ingrid S. (seed)", ["evening-canal-cruise"], [("amsterdam", "amsterdam-canals")], [("amsterdam", "canal-belt-facades")], [("amsterdam", "nine-streets-shopping")]),
            ("Castle complex ticket strategy alone paid for the guide.", "Petr N. (seed)", ["prague-castle-complex"], [("prague", "prague-castle-town")], [("prague", "prague-castle-gates")], [("prague", "beer-hall-reservation")]),
            ("Tram 28 tips saved us from riding in circles.", "Sofia L. (seed)", ["tram-28-photo-walk"], [("lisbon", "lisbon-alfama")], [("lisbon", "alfama-miradouros")], [("lisbon", "pasteis-belem-queue")]),
            ("Book of Kells slot + Howth same trip — perfect pacing.", "Brian O. (seed)", ["trinity-book-kells"], [("dublin", "dublin-history-lit")], [("dublin", "trinity-college-front")], [("dublin", "literary-pub-crawl")]),
            ("Small group, real historian, no shopping stops.", "Amélie R. (seed)", ["vatican-museums-sistine"], [("rome", "ancient-vatican")], [("rome", "pantheon")], []),
            ("Chianti half-day: kids got juice flights, we got the wine.", "Hannah W. (seed)", ["chianti-half-day"], [("florence", "tuscany-outings")], [("florence", "ponte-vecchio")], [("florence", "fiesole-sunset-bus")]),
            ("Murano demo + Burano colours — great photo day.", "Ken Y. (seed)", ["murano-burano-morning"], [("venice", "islands-lagoon")], [("venice", "st-marks-square")], [("venice", "burano-half-day")]),
            ("Orsay Impressionists tour nailed the hits in 90 min.", "Julie F. (seed)", ["orsay-impressionists"], [("paris", "museums-icons")], [("paris", "eiffel-tower")], []),
            ("Rijks highlights without museum fatigue — appreciated.", "Dirk V. (seed)", ["rijksmuseum-highlights"], [("amsterdam", "amsterdam-canals")], [("amsterdam", "rijksmuseum-building")], [("amsterdam", "vondelpark-picnic")]),
        ]
        for i, (quote, author, tour_slugs, cat_pairs, att_pairs, thing_pairs) in enumerate(quotes):
            t = Testimonial.objects.create(
                quote=quote,
                author=author,
                rating=5,
                sort_order=i,
                is_active=True,
            )
            for ts in tour_slugs:
                if ts in tour_map:
                    t.related_tours.add(tour_map[ts])
            for dslug, cslug in cat_pairs:
                c = cat_map.get(dslug, {}).get(cslug)
                if c:
                    t.related_categories.add(c)
            for dslug, aslug in att_pairs:
                a = att_map.get(dslug, {}).get(aslug)
                if a:
                    t.related_attractions.add(a)
            for dslug, tslug in thing_pairs:
                th = thing_map.get(dslug, {}).get(tslug)
                if th:
                    t.related_things_to_do.add(th)

    def _seed_blog(self, dest_map, tour_map, cat_map, att_map, thing_map):
        now = timezone.now()
        posts_spec = [
            {
                "slug": "first-time-rome-7-day-itinerary",
                "title": "First time in Rome: a sane 7-day itinerary",
                "scope": BlogPost.Scope.GENERAL,
                "country_slug": "",
                "city_slug": "",
                "excerpt": "How to layer Vatican, ancient sites, and neighborhood time without burning out.",
                "body": "Day 1: Arrive, evening in Trastevere.\nDay 2: Colosseum + Forum (book skip-the-line).\nDay 3: Vatican Museums; rest in Prati.\nDay 4: Borghese Gallery + Villa Borghese park.\nDay 5: Day trip to Ostia Antica or Tivoli.\nDay 6: Capitoline Museums + Jewish Ghetto food.\nDay 7: Last coffee near Pantheon, airport.\n\nBook timed entries 3–4 weeks ahead in peak season.",
                "img": IMG["blog1"],
                "dest_slugs": ["rome"],
                "tour_slugs": ["colosseum-forum-small-group"],
                "category_pairs": [("rome", "ancient-vatican"), ("rome", "food-neighborhoods")],
                "attraction_pairs": [("rome", "trevi-fountain"), ("rome", "pantheon")],
                "thing_pairs": [("rome", "aperitivo-prati"), ("rome", "testaccio-market-lunch")],
            },
            {
                "slug": "paris-museum-pass-worth-it",
                "title": "Is the Paris Museum Pass worth it in 2026?",
                "scope": BlogPost.Scope.CITY,
                "country_slug": "",
                "city_slug": "paris",
                "excerpt": "Break-even math for Louvre, Orsay, Arc, and Sainte-Chapelle.",
                "body": "If you visit 2 major museums plus one monument in 4 days, the pass usually pays off. It does not skip security lines — only ticket lines. Pair with timed Louvre entry.\n\nChildren often enter free at national museums; check official sites before buying passes for families.",
                "img": IMG["blog2"],
                "dest_slugs": ["paris"],
                "tour_slugs": ["louvre-highlights", "orsay-impressionists"],
                "category_pairs": [("paris", "museums-icons"), ("paris", "food-markets")],
                "attraction_pairs": [("paris", "louvre-pyramid"), ("paris", "eiffel-tower")],
                "thing_pairs": [("paris", "seine-cruise")],
            },
            {
                "slug": "london-thames-walks",
                "title": "Three Thames walks that beat the Tube",
                "scope": BlogPost.Scope.CITY,
                "country_slug": "",
                "city_slug": "london",
                "excerpt": "South Bank, Greenwich, and Little Venice — distances and pit stops.",
                "body": "South Bank: Westminster Bridge to Tate Modern (~2 km). Greenwich: cutty sark to observatory hill. Little Venice: canal path toward Camden.\n\nWear layers; weather shifts fast.",
                "img": IMG["blog3"],
                "dest_slugs": ["london"],
                "tour_slugs": ["westminster-royal", "south-bank-story-walk"],
                "category_pairs": [("london", "literary-thames"), ("london", "royal-westminster")],
                "attraction_pairs": [("london", "tower-bridge")],
                "thing_pairs": [("london", "borough-breakfast"), ("london", "thames-path-run")],
            },
            {
                "slug": "venice-cicchetti-guide",
                "title": "Cicchetti in Venice: what to order first",
                "scope": BlogPost.Scope.CITY,
                "country_slug": "",
                "city_slug": "venice",
                "excerpt": "Baccalà mantecato, sarde in saor, and the ombra ritual explained.",
                "body": "Stand at the bar; don't camp at tables without ordering drinks. One cicchetto + ombra (small wine) per stop is the classic rhythm. Cash still common in bacari.",
                "img": IMG["blog4"],
                "dest_slugs": ["venice"],
                "tour_slugs": ["cicchetti-crawl-rialto", "murano-burano-morning"],
                "category_pairs": [("venice", "cicchetti-wine"), ("venice", "islands-lagoon")],
                "attraction_pairs": [("venice", "rialto-bridge"), ("venice", "st-marks-square")],
                "thing_pairs": [("venice", "spritz-campo"), ("venice", "vaporetto-grand-canal")],
            },
            {
                "slug": "florence-duomo-without-lines",
                "title": "Florence Duomo complex: climbing Brunelleschi's dome",
                "scope": BlogPost.Scope.CITY,
                "country_slug": "",
                "city_slug": "florence",
                "excerpt": "Tickets, dress code, and how to combine baptistery and museum.",
                "body": "The Brunelleschi climb is 463 steps, narrow passages — not for severe claustrophobia. Book the combined Brunelleschi ticket early; time slots sell out.\n\nCombine with our Uffizi tour the same day if you love Renaissance depth.",
                "img": IMG["blog5"],
                "dest_slugs": ["florence"],
                "tour_slugs": ["uffizi-highlights", "accademia-david-express"],
                "category_pairs": [("florence", "duomo-museums")],
                "attraction_pairs": [("florence", "duomo-complex"), ("florence", "ponte-vecchio")],
                "thing_pairs": [("florence", "oltrarno-apertivo")],
            },
            {
                "slug": "barcelona-gaudi-beyond-sagrada",
                "title": "Beyond Sagrada Família: Casa Batlló vs Casa Milà",
                "scope": BlogPost.Scope.CITY,
                "country_slug": "",
                "city_slug": "barcelona",
                "excerpt": "Which modernist house fits your schedule and budget.",
                "body": "Casa Batlló: more whimsical facade and audio story. Casa Milà (La Pedrera): rooftop warrior chimneys. Both need timed tickets in summer.\n\nPark Güell requires a slot; free perimeter walking still possible.",
                "img": IMG["blog6"],
                "dest_slugs": ["barcelona"],
                "tour_slugs": ["sagrada-familia-towers", "casa-batllo-skip-line"],
                "category_pairs": [("barcelona", "gaudi-modernisme"), ("barcelona", "tapas-night")],
                "attraction_pairs": [("barcelona", "sagrada-familia-exterior"), ("barcelona", "park-guell-terrace")],
                "thing_pairs": [("barcelona", "barceloneta-dip")],
            },
            {
                "slug": "italy-country-rail-guide",
                "title": "Italy by train: Freccia, Italo, and regional tickets",
                "scope": BlogPost.Scope.COUNTRY,
                "country_slug": "italy",
                "city_slug": "",
                "excerpt": "When to buy high-speed vs when regional is enough.",
                "body": "Rome–Florence–Venice is ideal for Freccia or Italo if booked 2+ weeks ahead. Regional trains for Lucca, Orvieto, or Ravenna — no seat guarantee, validate paper tickets if any.\n\nLinks well with our Rome, Florence, and Venice destination hubs.",
                "img": IMG["blog7"],
                "dest_slugs": ["rome", "florence", "venice"],
                "tour_slugs": [],
                "category_pairs": [
                    ("rome", "day-trips"),
                    ("florence", "tuscany-outings"),
                    ("venice", "islands-lagoon"),
                ],
                "attraction_pairs": [],
                "thing_pairs": [],
            },
            {
                "slug": "europe-packing-light",
                "title": "Packing light for multi-city Europe trips",
                "scope": BlogPost.Scope.GENERAL,
                "country_slug": "",
                "city_slug": "",
                "excerpt": "One carry-on for Rome–Paris–London without laundry daily.",
                "body": "Layers, merino base, one smart jacket. Shoes you can walk 15k steps in. Universal USB-C charger. Scan PDFs of bookings offline.\n\nWe run small-group tours — small bags make security and vaporetto hops easier.",
                "img": IMG["blog8"],
                "dest_slugs": ["rome", "paris", "london"],
                "tour_slugs": [],
                "category_pairs": [],
                "attraction_pairs": [],
                "thing_pairs": [],
            },
            {
                "slug": "amsterdam-canal-photo-walk",
                "title": "Amsterdam canals: a photographer's loop",
                "scope": BlogPost.Scope.CITY,
                "country_slug": "",
                "city_slug": "amsterdam",
                "excerpt": "Golden angles on bridges, houseboats, and museumplein detours.",
                "body": "Start at Brouwersgracht, loop through Jordaan, end at Magere Brug after dark. Tripods are tolerated on bridges if you stay clear of bike lanes.",
                "img": IMG["blog1"],
                "dest_slugs": ["amsterdam"],
                "tour_slugs": ["evening-canal-cruise", "rijksmuseum-highlights"],
                "category_pairs": [("amsterdam", "amsterdam-canals")],
                "attraction_pairs": [("amsterdam", "canal-belt-facades")],
                "thing_pairs": [("amsterdam", "north-ferry-sunset")],
            },
            {
                "slug": "prague-castle-morning",
                "title": "Prague Castle before the tour buses",
                "scope": BlogPost.Scope.CITY,
                "country_slug": "",
                "city_slug": "prague",
                "excerpt": "Security lines, St. Vitus light, and Golden Lane pacing.",
                "body": "Arrive for opening security; do St. Vitus first while stained glass faces east. Save Golden Lane for last — it compresses fast.",
                "img": IMG["blog2"],
                "dest_slugs": ["prague"],
                "tour_slugs": ["prague-castle-complex"],
                "category_pairs": [("prague", "prague-castle-town")],
                "attraction_pairs": [("prague", "prague-castle-gates")],
                "thing_pairs": [("prague", "petrin-tower-walk")],
            },
            {
                "slug": "lisbon-tram-28-guide",
                "title": "Tram 28 without the bruises",
                "scope": BlogPost.Scope.CITY,
                "country_slug": "",
                "city_slug": "lisbon",
                "excerpt": "Pick-up stops, pickpocket habits, and better miradouro exits.",
                "body": "Board early in Graça or Estrela, not at the castle terminus. Standers pack tight — keep bags forward. Hop off at Portas do Sol for the classic Alfama view.",
                "img": IMG["blog3"],
                "dest_slugs": ["lisbon"],
                "tour_slugs": ["tram-28-photo-walk"],
                "category_pairs": [("lisbon", "lisbon-alfama")],
                "attraction_pairs": [("lisbon", "alfama-miradouros")],
                "thing_pairs": [("lisbon", "pasteis-belem-queue")],
            },
            {
                "slug": "dublin-literary-pub-crawl",
                "title": "Dublin literary pubs: reading the room",
                "scope": BlogPost.Scope.CITY,
                "country_slug": "",
                "city_slug": "dublin",
                "excerpt": "Sessions, stories, and where tourists thin out.",
                "body": "Temple Bar for energy, Portobello for quieter pints. Many venues are standing-room during trad sets — arrive when doors open if you want a stool.",
                "img": IMG["blog4"],
                "dest_slugs": ["dublin"],
                "tour_slugs": ["temple-bar-music-crawl"],
                "category_pairs": [("dublin", "dublin-pubs-music")],
                "attraction_pairs": [("dublin", "ha-penny-bridge")],
                "thing_pairs": [("dublin", "literary-pub-crawl")],
            },
            {
                "slug": "rome-ostia-antica-day",
                "title": "Ostia Antica vs Pompeii for a Rome base",
                "scope": BlogPost.Scope.CITY,
                "country_slug": "",
                "city_slug": "rome",
                "excerpt": "Half-day regional train, shade strategy, and what mosaics survive.",
                "body": "Ostia is flatter and closer than Pompeii — ideal with kids or jet lag. Bring water; tree cover is patchy. Pair with our half-day guided option.",
                "img": IMG["blog5"],
                "dest_slugs": ["rome"],
                "tour_slugs": ["ostia-antica-half-day"],
                "category_pairs": [("rome", "day-trips")],
                "attraction_pairs": [("rome", "colosseum-exterior")],
                "thing_pairs": [("rome", "appian-bike")],
            },
            {
                "slug": "paris-versailles-audio",
                "title": "Versailles day: audio vs guided trade-offs",
                "scope": BlogPost.Scope.CITY,
                "country_slug": "",
                "city_slug": "paris",
                "excerpt": "Train RER C, fountain show days, and garden bike rentals.",
                "body": "Audio suits independent pacing; guides win on crowd choreography in the State Apartments. Check fountain schedules before you commit to gardens-only tickets.",
                "img": IMG["blog6"],
                "dest_slugs": ["paris"],
                "tour_slugs": ["marais-chocolate-walk"],
                "category_pairs": [("paris", "seine-districts")],
                "attraction_pairs": [("paris", "sacre-coeur-terrace")],
                "thing_pairs": [("paris", "marais-gallery-hop")],
            },
            {
                "slug": "london-hampton-court",
                "title": "Hampton Court Palace in a morning",
                "scope": BlogPost.Scope.CITY,
                "country_slug": "",
                "city_slug": "london",
                "excerpt": "Train from Waterloo, maze timing, and Tudor kitchens smell-test.",
                "body": "Direct trains are quick; palace opens before the gardens fill. The maze is shorter than you remember — kitchens and tapestries reward dawdlers.",
                "img": IMG["blog7"],
                "dest_slugs": ["london"],
                "tour_slugs": ["tower-of-london-crowns"],
                "category_pairs": [("london", "royal-westminster")],
                "attraction_pairs": [("london", "british-museum-great-court")],
                "thing_pairs": [("london", "columbia-road-sunday")],
            },
            {
                "slug": "venice-murano-burano",
                "title": "Murano glass demos: what to book",
                "scope": BlogPost.Scope.CITY,
                "country_slug": "",
                "city_slug": "venice",
                "excerpt": "Factory visits, vaporetto math, and Burano light windows.",
                "body": "Morning glass demos have cooler furnaces and thinner crowds. Burano after lunch when colours pop in slanted light. Our lagoon tour strings both with transit explained.",
                "img": IMG["blog8"],
                "dest_slugs": ["venice"],
                "tour_slugs": ["murano-burano-morning"],
                "category_pairs": [("venice", "islands-lagoon")],
                "attraction_pairs": [("venice", "doge-palace-facade")],
                "thing_pairs": [("venice", "burano-half-day")],
            },
            {
                "slug": "florence-pitti-boboli",
                "title": "Pitti & Boboli: tickets that pair well",
                "scope": BlogPost.Scope.CITY,
                "country_slug": "",
                "city_slug": "florence",
                "excerpt": "Timed museums, uphill shortcuts, and café breaks.",
                "body": "Pitti museums are dense — Boboli gives your eyes green relief. Enter Boboli from Pitti courtyard; wear grippy shoes on gravel slopes.",
                "img": IMG["blog1"],
                "dest_slugs": ["florence"],
                "tour_slugs": ["chianti-half-day", "oltrarno-artisan-walk"],
                "category_pairs": [("florence", "food-artisan")],
                "attraction_pairs": [("florence", "uffizi-exterior")],
                "thing_pairs": [("florence", "sant-ambrogio-market")],
            },
            {
                "slug": "barcelona-montjuic-sunset",
                "title": "Montjuïc sunset without the cable-car queue",
                "scope": BlogPost.Scope.CITY,
                "country_slug": "",
                "city_slug": "barcelona",
                "excerpt": "Bus 150, castle viewpoints, and magic fountain nights.",
                "body": "Hike or bus to the castle terraces for port views. Magic fountain shows are seasonal — check city site before promising kids lights.",
                "img": IMG["blog2"],
                "dest_slugs": ["barcelona"],
                "tour_slugs": ["el-born-tapas-crawl"],
                "category_pairs": [("barcelona", "gothic-sea")],
                "attraction_pairs": [("barcelona", "barcelona-cathedral")],
                "thing_pairs": [("barcelona", "montserrat-half-day")],
            },
            {
                "slug": "food-wine-europe-introduction",
                "title": "How we think about food & wine tours",
                "scope": BlogPost.Scope.GENERAL,
                "country_slug": "",
                "city_slug": "",
                "excerpt": "Standing bites, seated tastings, and dietary notes we actually collect.",
                "body": "We label standing vs seated, approximate drink units, and flag shellfish-heavy routes. Vegetarian swaps exist on most city food walks — ask on booking.",
                "img": IMG["blog3"],
                "dest_slugs": ["rome", "paris", "barcelona", "lisbon"],
                "tour_slugs": ["trastevere-food-evening", "cicchetti-crawl-rialto"],
                "category_pairs": [("rome", "food-neighborhoods"), ("venice", "cicchetti-wine")],
                "attraction_pairs": [],
                "thing_pairs": [("lisbon", "pasteis-belem-queue")],
            },
            {
                "slug": "family-travel-museums",
                "title": "Museums with kids: realistic pacing",
                "scope": BlogPost.Scope.GENERAL,
                "country_slug": "",
                "city_slug": "",
                "excerpt": "90-minute ceilings, scavenger hunts, and when to bail for gelato.",
                "body": "Two timed entries per day beats one marathon. Audio tours for tweens, sticker books for younger kids. We note stroller access per listing.",
                "img": IMG["blog4"],
                "dest_slugs": ["london", "florence", "amsterdam"],
                "tour_slugs": [],
                "category_pairs": [("london", "royal-westminster")],
                "attraction_pairs": [("london", "british-museum-great-court")],
                "thing_pairs": [],
            },
            {
                "slug": "photography-golden-hour-cities",
                "title": "Golden hour in European cities",
                "scope": BlogPost.Scope.GENERAL,
                "country_slug": "",
                "city_slug": "",
                "excerpt": "Bridges, rivers, and rooftops that reward late light.",
                "body": "Rooftop bars need reservations; riverbanks are free. Shoot RAW if skies clip — stone facades hold shadow detail.",
                "img": IMG["blog5"],
                "dest_slugs": ["paris", "prague", "venice"],
                "tour_slugs": [],
                "category_pairs": [("prague", "prague-castle-town")],
                "attraction_pairs": [("prague", "charles-bridge")],
                "thing_pairs": [],
            },
            {
                "slug": "rainy-day-museum-routes",
                "title": "Rainy-day museum stacks we love",
                "scope": BlogPost.Scope.GENERAL,
                "country_slug": "",
                "city_slug": "",
                "excerpt": "Indoor-only days that still feel like a city walk.",
                "body": "Cluster museums near covered passages or food halls so breaks feel local. Pack a compact umbrella — cloakrooms hate golf umbrellas.",
                "img": IMG["blog6"],
                "dest_slugs": ["london", "amsterdam", "dublin"],
                "tour_slugs": ["rijksmuseum-highlights"],
                "category_pairs": [("amsterdam", "amsterdam-canals")],
                "attraction_pairs": [],
                "thing_pairs": [],
            },
            {
                "slug": "train-sleepers-europe",
                "title": "Night trains: couchettes vs sleepers",
                "scope": BlogPost.Scope.GENERAL,
                "country_slug": "",
                "city_slug": "",
                "excerpt": "Earplugs, door locks, and arrival shower strategy.",
                "body": "Couchettes save money; sleepers save sanity on 10h+ legs. Book gender compartments if that matters to your group; policies vary by carrier.",
                "img": IMG["blog7"],
                "dest_slugs": ["rome", "paris", "amsterdam", "prague"],
                "tour_slugs": [],
                "category_pairs": [],
                "attraction_pairs": [],
                "thing_pairs": [],
            },
            {
                "slug": "solo-travel-safety-tips",
                "title": "Solo travel in big European cities",
                "scope": BlogPost.Scope.GENERAL,
                "country_slug": "",
                "city_slug": "",
                "excerpt": "Scams, solo dining, and check-in habits that help.",
                "body": "Share live location with one person; keep a paper hotel card. Solo diners: bar seats and lunch specials beat awkward two-tops at 21:00.",
                "img": IMG["blog8"],
                "dest_slugs": ["london", "dublin"],
                "tour_slugs": [],
                "category_pairs": [],
                "attraction_pairs": [],
                "thing_pairs": [],
            },
            {
                "slug": "christmas-markets-route",
                "title": "Christmas markets: a sane multi-city route",
                "scope": BlogPost.Scope.GENERAL,
                "country_slug": "",
                "city_slug": "",
                "excerpt": "Prague, Vienna, Strasbourg pacing without mulled-wine burnout.",
                "body": "Two market nights per city max; alternate with museum or spa days. Cash still wins at wooden stalls.",
                "img": IMG["blog1"],
                "dest_slugs": ["prague", "paris"],
                "tour_slugs": ["historic-pub-crawl"],
                "category_pairs": [("prague", "prague-beer")],
                "attraction_pairs": [("prague", "astronomical-clock")],
                "thing_pairs": [],
            },
            {
                "slug": "summer-crowds-strategy",
                "title": "July crowds: tickets that actually help",
                "scope": BlogPost.Scope.GENERAL,
                "country_slug": "",
                "city_slug": "",
                "excerpt": "Opening slots, after-hours nights, and when to skip the icon.",
                "body": "First slot or last slot beats midday everywhere. Some sites run summer nights — fewer people, different light, worth the premium.",
                "img": IMG["blog2"],
                "dest_slugs": ["rome", "florence", "barcelona"],
                "tour_slugs": ["colosseum-forum-small-group", "sagrada-familia-towers"],
                "category_pairs": [("rome", "ancient-vatican")],
                "attraction_pairs": [],
                "thing_pairs": [],
            },
            {
                "slug": "accessible-travel-museums",
                "title": "Accessibility at museums and historic sites",
                "scope": BlogPost.Scope.GENERAL,
                "country_slug": "",
                "city_slug": "",
                "excerpt": "Lifts that exist, cobbles that don't, and questions to email ahead.",
                "body": "We publish step counts and lift availability where venues confirm. Email us mobility needs before booking — we re-verify seasonally.",
                "img": IMG["blog3"],
                "dest_slugs": ["london", "paris", "amsterdam"],
                "tour_slugs": [],
                "category_pairs": [],
                "attraction_pairs": [],
                "thing_pairs": [],
            },
            {
                "slug": "budget-eats-capital-cities",
                "title": "Capital cities on a food budget",
                "scope": BlogPost.Scope.GENERAL,
                "country_slug": "",
                "city_slug": "",
                "excerpt": "Markets, lunch menus, and grocery picnics that feel special.",
                "body": "Lunch formules beat dinner tariffs. Markets close early — plan picnics before 14:00 in much of southern Europe.",
                "img": IMG["blog4"],
                "dest_slugs": ["lisbon", "dublin", "prague"],
                "tour_slugs": [],
                "category_pairs": [("lisbon", "lisbon-food-fado")],
                "attraction_pairs": [],
                "thing_pairs": [("dublin", "howth-cliff-walk")],
            },
            {
                "slug": "night-photography-bridges",
                "title": "Bridges at blue hour",
                "scope": BlogPost.Scope.GENERAL,
                "country_slug": "",
                "city_slug": "",
                "excerpt": "Charles, Tower, and Amsterdam's skinny arches.",
                "body": "Tripod + 2s exposure cleans water reflections. Watch bike lanes on narrow bridges — shoot from the sidewalk inset.",
                "img": IMG["blog5"],
                "dest_slugs": ["prague", "london", "amsterdam"],
                "tour_slugs": ["evening-canal-cruise"],
                "category_pairs": [],
                "attraction_pairs": [("london", "tower-bridge"), ("amsterdam", "canal-belt-facades")],
                "thing_pairs": [],
            },
            {
                "slug": "tipping-guides-europe",
                "title": "Tipping on tours across Europe",
                "scope": BlogPost.Scope.GENERAL,
                "country_slug": "",
                "city_slug": "",
                "excerpt": "Where rounding up is enough vs where guides expect cash thanks.",
                "body": "Included gratuities are rare on walking tours. Card tips aren't always possible — small euro notes still king for guides.",
                "img": IMG["blog6"],
                "dest_slugs": ["rome", "paris", "london", "barcelona"],
                "tour_slugs": [],
                "category_pairs": [],
                "attraction_pairs": [],
                "thing_pairs": [],
            },
        ]
        for i, spec in enumerate(posts_spec):
            p, _ = BlogPost.objects.update_or_create(
                slug=spec["slug"],
                defaults={
                    "title": spec["title"],
                    "scope": spec["scope"],
                    "country_slug": spec["country_slug"],
                    "city_slug": spec["city_slug"],
                    "excerpt": spec["excerpt"],
                    "body": spec["body"],
                    "listing_image_url": spec["img"],
                    "published_at": now - timedelta(days=30 - i * 3),
                },
            )
            p.related_destinations.clear()
            for ds in spec["dest_slugs"]:
                if ds in dest_map:
                    p.related_destinations.add(dest_map[ds])
            p.related_tours.clear()
            for ts in spec["tour_slugs"]:
                if ts in tour_map:
                    p.related_tours.add(tour_map[ts])
            p.related_categories.clear()
            for dslug, cslug in spec.get("category_pairs", []):
                c = cat_map.get(dslug, {}).get(cslug)
                if c:
                    p.related_categories.add(c)
            p.related_attractions.clear()
            for dslug, aslug in spec.get("attraction_pairs", []):
                a = att_map.get(dslug, {}).get(aslug)
                if a:
                    p.related_attractions.add(a)
            p.related_things_to_do.clear()
            for dslug, tslug in spec.get("thing_pairs", []):
                th = thing_map.get(dslug, {}).get(tslug)
                if th:
                    p.related_things_to_do.add(th)

        # Related posts M2M (one chain)
        p1 = BlogPost.objects.get(slug="first-time-rome-7-day-itinerary")
        p2 = BlogPost.objects.get(slug="italy-country-rail-guide")
        p3 = BlogPost.objects.get(slug="europe-packing-light")
        p1.related_posts.clear()
        p1.related_posts.add(p2, p3)
        p_amsterdam = BlogPost.objects.filter(slug="amsterdam-canal-photo-walk").first()
        if p_amsterdam:
            p_amsterdam.related_posts.clear()
            p_amsterdam.related_posts.add(p1, p2)

    def _seed_site_pages(self, dest_map, tour_map):
        rome = dest_map["rome"]
        paris = dest_map["paris"]
        tour_col = tour_map.get("colosseum-forum-small-group")
        tour_louvre = tour_map.get("louvre-highlights")
        att = Attraction.objects.get(destination=rome, slug="trevi-fountain")
        thing = ThingToDo.objects.get(destination=rome, slug="aperitivo-prati")
        home = SitePage.objects.get(page_key=SitePage.PageKey.HOME)
        home.title = "Experience more"
        home.intro = (
            "Top-rated small-group tours for world-class wonders — skip lines, expert guides, "
            "and itineraries that respect your time."
        )
        home.body = (
            "We operate across ten European hubs — Rome, Paris, London, Venice, Florence, Barcelona, "
            "Amsterdam, Prague, Lisbon, and Dublin — with vetted local guides. "
            "Every listing includes what to wear, how long you'll walk, and honest crowd expectations."
        )
        home.show_lead_form = True
        home.save()
        home.featured_destinations.set([rome, paris])
        home.featured_blog_posts.set(
            BlogPost.objects.filter(slug__in=["first-time-rome-7-day-itinerary", "paris-museum-pass-worth-it"])
        )
        if tour_col and tour_louvre:
            home.featured_tours.set([tour_col, tour_louvre])
        home.featured_attractions.set([att])
        home.featured_things_to_do.set([thing])

        about = SitePage.objects.get(page_key=SitePage.PageKey.ABOUT)
        about.title = "About Traveler"
        about.intro = "We started as guides, not salespeople — that shapes every tour we list."
        about.body = (
            "Founded by former museum educators and city-licensed hosts, Traveler matches small groups with "
            "storytellers who live where they work.\n\n"
            "We cap most walks at 12 guests, publish real durations, and retrain staff on accessibility and "
            "inclusion yearly.\n\n"
            "Headquarters: remote-first team across EU & UK time zones. Partner DMCs in each destination."
        )
        about.save()
        about.featured_destinations.set([rome, dest_map["venice"]])

        contact = SitePage.objects.get(page_key=SitePage.PageKey.CONTACT)
        contact.title = "Contact us"
        contact.intro = "Trips, private groups, and partnerships — we reply within one business day."
        contact.body = (
            "Phone (UK): +44 20 7946 0958\n"
            "Email: hello@traveler.example\n"
            "Hours: Mon–Fri 09:00–18:00 GMT\n\n"
            "For urgent day-of-tour issues, use the emergency number on your confirmation PDF."
        )
        contact.save()

        faqs = SitePage.objects.get(page_key=SitePage.PageKey.FAQS)
        faqs.title = "Frequently asked questions"
        faqs.intro = "Booking, refunds, accessibility, and weather."
        faqs.body = (
            "Q: Can I cancel?\nA: Free cancellation up to 24h before most experiences; check your confirmation for exceptions.\n\n"
            "Q: Are tours wheelchair accessible?\nA: Many are partially accessible; email us with your mobility needs before booking.\n\n"
            "Q: What if it rains?\nA: Tours run unless authorities close sites; we issue vouchers if we cancel."
        )
        faqs.save()

        legal = SitePage.objects.get(page_key=SitePage.PageKey.LEGAL)
        legal.title = "Legal & privacy"
        legal.intro = "Terms of use, privacy policy summary, and imprint."
        legal.body = (
            "Operator: Traveler Demo Ltd (fictional entity for review data only).\n\n"
            "Privacy: We process booking data to fulfil contracts, send service emails, and improve our site. "
            "Analytics are anonymised where possible.\n\n"
            "Full policy PDF available on request — this seed text is not legal advice."
        )
        legal.save()

    def _seed_site_branding(self):
        s = SiteSettings.load()
        s.site_name = "Traveler Tours"
        s.search_placeholder = "Search destinations, tours, blog…"
        s.header_account_url = ""
        s.header_cart_url = ""
        s.header_locale_label = "EN · EUR"
        s.newsletter_title = "Get trip ideas weekly"
        s.newsletter_subtitle = "One email: new tours, seasonal tips, and member-only windows."
        s.newsletter_fine_print = "We never sell your address. Unsubscribe in one click."
        s.footer_payment_line = "Visa · Mastercard · Amex · PayPal · Apple Pay"
        s.press_bar_intro = "Featured in"
        s.copyright_holder = "Traveler Tours"
        s.save()

    def _seed_home_config(self):
        hc = HomePageConfig.load()
        hc.hero_kicker = "Small groups · Local experts"
        hc.hero_intro_fallback = (
            "Skip-the-line where it matters, hear the stories behind the stones, and leave with a sensible "
            "list of what to eat next."
        )
        hc.hero_cta_primary_label = "Browse destinations"
        hc.hero_cta_primary_link = "/destinations/"
        hc.hero_cta_secondary_label = "Talk to us"
        hc.hero_cta_secondary_link = "/contact/"
        hc.destinations_kicker = "Signature experiences"
        hc.destinations_title = "Where we're heading this season"
        hc.video_watch_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        hc.community_hashtag = "#TravelerTours"
        hc.community_follow_url = "https://www.instagram.com/"
        hc.testimonial_footer_note = "Average 4.9★ across Google, TripAdvisor, and post-tour surveys."
        hc.promise_section_subtitle = (
            "Fair pricing, clear meeting points, and guides who answer the weird questions — that's the deal."
        )
        hc.expert_body = (
            "You'll walk with art historians, chef-guides, and lifelong residents. We pay above living wage "
            "and run mystery-shopper quality checks twice a year."
        )
        hc.blog_section_subtitle = "Itineraries, honest reviews, and food you won't find on a postcard."
        hc.home_destinations_limit = 10
        hc.save()

    def _seed_sample_leads(self, dest_map):
        Lead.objects.update_or_create(
            email="review.demo@example.com",
            defaults={
                "name": "Alex Reviewer",
                "phone": "+1 415 555 0199",
                "message": "Interested in a private Colosseum + Forum for 6 people on June 12. Flexible on start time.",
                "destination_interest": dest_map["rome"],
                "source_page": "contact",
            },
        )
        Lead.objects.update_or_create(
            email="corporate.events@example.com",
            defaults={
                "name": "Jordan Lee",
                "phone": "",
                "message": "Company offsite 40 pax — need Paris full-day options with dinner recommendation.",
                "destination_interest": dest_map["paris"],
                "source_page": "home",
            },
        )
