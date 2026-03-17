import argparse
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))


def seed():
    from db.setup import initialize_db
    initialize_db(force=True)
    print("Database seeded successfully.")


def launch_ui():
    import subprocess
    ui_path = ROOT / "app.py"
    subprocess.run(
        ["streamlit", "run", str(ui_path), "--server.headless", "false"],
        cwd=str(ROOT),
    )


def demo():
    from db import initialize_db, get_products
    from agents import run_campaign

    initialize_db()
    products = get_products(season="Summer", min_stock=1)
    if not products:
        print("No products found. Run --seed first.")
        return

    product = products[0]
    print(f"\nRunning demo campaign for: {product['name']}\n")

    filters = {
        "gender": "Unisex",
        "age_group": "Adults",
        "season": "Summer",
        "campaign_goal": "Brand Awareness",
        "tone": "Modern & Aspirational",
        "caption_style": "short and punchy",
    }

    def cb(step, data):
        prefix = {"phase": "▶", "start": "->", "done": "!"}.get(step, "  ")
        print(f"{prefix} {data}")

    result = run_campaign(product, filters, stream_callback=cb)
    print(f"\n>>>>>>Campaign complete!")
    print(f"   Quote   : {result.get('quote')}")
    print(f"   Tagline : {result.get('tagline')}")
    print(f"   Image   : {result.get('image_path')}")
    print(f"   Report  : {result.get('report_path')}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Retail Campaign Agent")
    parser.add_argument("--seed", action="store_true", help="Seed/reset the database")
    parser.add_argument("--ui",   action="store_true", help="Launch Streamlit UI")
    parser.add_argument("--demo", action="store_true", help="Run headless demo")
    args = parser.parse_args()

    if args.seed:
        seed()
    elif args.ui:
        launch_ui()
    elif args.demo:
        demo()
    else:
        print("Use --seed, --ui, or --demo. Run with --help for details.")