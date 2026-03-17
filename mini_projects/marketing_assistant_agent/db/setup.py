import sqlite3
import random
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path(__file__).parent / "retail.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS categories (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            name     TEXT NOT NULL UNIQUE,
            slug     TEXT NOT NULL UNIQUE,
            icon     TEXT
        );

        CREATE TABLE IF NOT EXISTS products (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            sku             TEXT NOT NULL UNIQUE,
            name            TEXT NOT NULL,
            category_id     INTEGER REFERENCES categories(id),
            description     TEXT,
            price           REAL NOT NULL,
            cost            REAL NOT NULL,
            brand           TEXT,
            gender          TEXT CHECK(gender IN ('Men','Women','Unisex')),
            age_group       TEXT CHECK(age_group IN ('Kids','Teens','Adults','Seniors','All')),
            season          TEXT CHECK(season IN ('Spring','Summer','Autumn','Winter','All')),
            tags            TEXT,        -- comma-separated
            image_hint      TEXT,        -- description for AI image generation
            is_active       INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS inventory (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id      INTEGER NOT NULL REFERENCES products(id),
            quantity        INTEGER NOT NULL DEFAULT 0,
            reorder_level   INTEGER DEFAULT 10,
            warehouse       TEXT DEFAULT 'Main',
            last_updated    TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS sales (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id      INTEGER NOT NULL REFERENCES products(id),
            quantity        INTEGER NOT NULL,
            unit_price      REAL NOT NULL,
            sale_date       TEXT NOT NULL,
            channel         TEXT CHECK(channel IN ('In-Store','Online','Wholesale')),
            region          TEXT
        );

        CREATE TABLE IF NOT EXISTS campaigns (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT NOT NULL,
            product_id      INTEGER REFERENCES products(id),
            status          TEXT DEFAULT 'draft',
            trend_summary   TEXT,
            caption         TEXT,
            tagline         TEXT,
            quote           TEXT,
            image_path      TEXT,
            report_path     TEXT,
            created_at      TEXT DEFAULT (datetime('now')),
            filters_json    TEXT
        );
    """)
    conn.commit()


def seed_categories(conn):
    categories = [
        ("Sunglasses",  "sunglasses",  "🕶️"),
        ("Watches",     "watches",     "⌚"),
        ("Handbags",    "handbags",    "👜"),
        ("Shoes",       "shoes",       "👟"),
        ("Jewelry",     "jewelry",     "💍"),
        ("Scarves",     "scarves",     "🧣"),
        ("Hats",        "hats",        "🎩"),
        ("Belts",       "belts",       "👔"),
    ]
    conn.executemany(
        "INSERT OR IGNORE INTO categories (name, slug, icon) VALUES (?,?,?)",
        categories
    )
    conn.commit()


def seed_products(conn):
    products = [
        ("SG-001","Riviera Aviator Pro","Sunglasses","Classic gold aviator with mirrored lenses, UV400 protection",189.99,60,"RayWear","Unisex","Adults","Summer","aviator,gold,mirrored,summer,classic","A sleek aviator resting on sun-kissed sand beside ocean waves"),
        ("SG-002","Urban Shield Wraparound","Sunglasses","Full-coverage wraparound for sports & outdoors",149.99,45,"SpeedX","Men","Adults","Summer","sport,wraparound,outdoor,athletic","An athlete mid-sprint at golden hour wearing sleek black wraparound shades"),
        ("SG-003","Pastel Dream Cat-Eye","Sunglasses","Retro cat-eye with rose-tinted lenses, acetate frame",129.99,38,"LunaVision","Women","Adults","Spring","cat-eye,retro,pastel,feminine","A woman in a flower field wearing pastel pink cat-eye sunglasses"),
        ("SG-004","Nordic Minimal Round","Sunglasses","Thin titanium round frames, smoky lenses",219.99,72,"NordLens","Unisex","Adults","All","minimal,round,titanium,premium","Minimalist round sunglasses on a marble surface with botanical leaves"),
        ("SG-005","Kid Splash UV Shield","Sunglasses","Durable rubber frame for children, polarized",49.99,14,"TinyShade","Unisex","Kids","Summer","kids,polarized,durable,fun","Colorful kids' sunglasses on a beach towel with sandcastles"),
        ("SG-006","Sunset Gradient Butterfly","Sunglasses","Oversized butterfly frame with gradient orange lenses",159.99,48,"GlamLens","Women","Adults","Summer","oversized,butterfly,gradient,trendy","Bold butterfly sunglasses against a vibrant sunset sky"),
        ("SG-007","Heritage Tortoiseshell Square","Sunglasses","Classic acetate tortoiseshell, polarized UV400",174.99,55,"ClassiCo","Unisex","Adults","All","tortoiseshell,classic,polarized,heritage","Tortoiseshell sunglasses on a vintage newspaper beside an espresso"),
        ("SG-008","Cyberpunk Shield","Sunglasses","Futuristic one-piece shield lens, matte black frame",199.99,62,"FuturEdge","Unisex","Teens","Summer","cyberpunk,shield,futuristic,bold","Futuristic shield sunglasses in a neon-lit urban street at night"),

        ("WA-001","Chronos Elite Diver","Watches","300m water-resistant diver, sapphire crystal, automatic",499.99,155,"ChronosX","Men","Adults","All","diver,automatic,luxury,water-resistant","A luxury diver watch gleaming underwater with coral reef background"),
        ("WA-002","Bloom Floral Dial","Watches","Rose-gold case, floral enamel dial, quartz",249.99,75,"BelleTemps","Women","Adults","Spring","floral,rose-gold,feminine,elegant","Elegant rose-gold watch on a wrist beside blooming peonies"),
        ("WA-003","Solar Ranger Outdoor","Watches","Solar-powered, GPS, altimeter, for hikers",379.99,115,"TrailMaster","Unisex","Adults","All","solar,gps,outdoor,smart","Rugged solar watch worn on a mountain ridge at sunrise"),
        ("WA-004","Retro Neon Digital","Watches","80s-inspired LED display, bold neon case",89.99,25,"NeonTime","Unisex","Teens","Summer","retro,neon,digital,fun","Bright neon digital watch on a skateboard ramp"),

        ("HB-001","Milan Leather Tote","Handbags","Full-grain Italian leather tote, brass hardware",349.99,105,"MilanoLux","Women","Adults","All","leather,tote,luxury,italian","Premium leather tote on cobblestone streets in a European city"),
        ("HB-002","Canvas Weekender","Handbags","Waxed canvas weekend bag, unisex minimalist design",199.99,60,"WanderCo","Unisex","Adults","All","canvas,weekend,unisex,minimal","Canvas weekender bag at a train station, golden light"),
        ("HB-003","Neon Mini Crossbody","Handbags","Tiny crossbody in bold neon colors, gen-Z trend",79.99,22,"VibeCarry","Women","Teens","Summer","mini,crossbody,neon,trendy","Neon mini crossbody bag at a music festival"),

        ("SH-001","Cloud Runner Sneaker","Shoes","Ultra-light foam sole, breathable mesh, summer colourways",119.99,36,"AirStep","Unisex","Adults","Summer","sneaker,running,breathable,summer","White cloud-runner sneakers on a pastel background with flowers"),
        ("SH-002","Artisan Leather Loafer","Shoes","Hand-stitched leather loafer, cushioned insole",189.99,57,"CraftFoot","Men","Adults","All","loafer,leather,artisan,classic","Classic leather loafers on a wooden floor beside a briefcase"),
        ("SH-003","Boho Wedge Sandal","Shoes","Braided jute wedge sandal, ankle strap",89.99,26,"BohoStep","Women","Adults","Summer","sandal,wedge,boho,summer","Wedge sandals on beach boardwalk with ocean behind"),

        ("JW-001","Celestial Gold Pendant","Jewelry","14k gold crescent moon & star pendant, fine chain",299.99,88,"StarForge","Women","Adults","All","gold,celestial,pendant,luxury","Gold celestial pendant glowing under soft studio light"),
        ("JW-002","Ocean Pearl Bracelet","Jewelry","Freshwater pearl & silver charm bracelet",149.99,44,"SeaGems","Women","Adults","Summer","pearl,bracelet,ocean,summer","Pearl bracelet resting on a seashell at the beach"),
        ("JW-003","Minimal Stack Ring Set","Jewelry","Set of 5 stackable sterling silver rings",69.99,20,"ModRing","Unisex","Teens","All","rings,stack,minimal,silver","Stacked silver rings on elegant fingers against marble"),

        ("SC-001","Silk Bloom Scarf","Scarves","100% silk, floral print, hand-rolled edges",179.99,54,"SilkRoute","Women","Adults","Spring","silk,floral,luxury,spring","Silk scarf billowing in spring breeze beside cherry blossoms"),
        ("SC-002","Chunky Knit Wrap","Scarves","Oversized merino wool wrap, earthy tones",129.99,38,"WoolCraft","Unisex","Adults","Winter","wool,knit,wrap,cosy","Chunky knit scarf on a person walking in snowy woods"),

        ("HA-001","Panama Plantation Hat","Hats","Hand-woven toquilla straw panama, ribbon band",139.99,42,"PanamaReal","Unisex","Adults","Summer","panama,straw,summer,classic","Straw panama hat on a sun-drenched tropical terrace"),
        ("HA-002","Wool Felt Fedora","Hats","Classic wool felt fedora, grosgrain ribbon",109.99,33,"FeltCo","Unisex","Adults","Autumn","fedora,wool,classic,autumn","Wool fedora hat in a rustic autumn setting"),
        ("HA-003","Neon Bucket Hat","Hats","Lightweight neon bucket hat, festival favourite",39.99,11,"FestGear","Unisex","Teens","Summer","bucket,neon,festival,summer","Neon bucket hat at a sunny outdoor music festival"),

        ("BE-001","Heritage Leather Belt","Belts","Full-grain leather dress belt, solid brass buckle",99.99,30,"LeatherHouse","Men","Adults","All","leather,dress,heritage,classic","Classic leather belt beside a tailored suit jacket"),
        ("BE-002","Western Studded Belt","Belts","Distressed leather with turquoise stud detailing",119.99,36,"DustTrail","Unisex","Adults","All","western,studded,boho,statement","Studded western belt against a rustic denim backdrop"),
    ]

    cat_map = {r["name"]: r["id"] for r in conn.execute("SELECT id, name FROM categories").fetchall()}

    for p in products:
        sku, name, cat, desc, price, cost, brand, gender, age, season, tags, img_hint = p
        cat_id = cat_map.get(cat)
        conn.execute(
            """INSERT OR IGNORE INTO products
               (sku,name,category_id,description,price,cost,brand,gender,age_group,season,tags,image_hint)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (sku, name, cat_id, desc, price, cost, brand, gender, age, season, tags, img_hint)
        )
    conn.commit()


def seed_inventory(conn):
    products = conn.execute("SELECT id FROM products").fetchall()
    for p in products:
        qty = random.randint(5, 250)
        conn.execute(
            "INSERT OR IGNORE INTO inventory (product_id, quantity, reorder_level) VALUES (?,?,?)",
            (p["id"], qty, random.randint(5, 20))
        )
    conn.commit()


def seed_sales(conn):
    products = conn.execute("SELECT id, price FROM products").fetchall()
    channels = ["In-Store", "Online", "Wholesale"]
    regions = ["North", "South", "East", "West", "Central"]

    records = []
    for _ in range(800):
        p = random.choice(products)
        days_ago = random.randint(0, 365)
        sale_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        records.append((
            p["id"],
            random.randint(1, 12),
            round(p["price"] * random.uniform(0.85, 1.0), 2),
            sale_date,
            random.choice(channels),
            random.choice(regions),
        ))

    conn.executemany(
        "INSERT INTO sales (product_id, quantity, unit_price, sale_date, channel, region) VALUES (?,?,?,?,?,?)",
        records
    )
    conn.commit()


def initialize_db(force=False):
    if force and DB_PATH.exists():
        DB_PATH.unlink()
    conn = get_connection()
    create_tables(conn)
    seed_categories(conn)
    seed_products(conn)
    seed_inventory(conn)
    seed_sales(conn)
    conn.close()
    print(f"Database ready at {DB_PATH}")


if __name__ == "__main__":
    initialize_db(force=True)
