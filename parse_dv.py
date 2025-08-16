import os
from bs4 import BeautifulSoup


def parse_departures(html_file_path):
    with open(html_file_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    departures = []
    # Each departure is in an <li> element with class "border mb-3 rounded"
    for departure_item in soup.select("li.border.mb-3.rounded"):
        try:
            # Extract destination from the first <strong> tag in media-body
            destination_elem = departure_item.select_one(".media-body strong")
            destination = (
                destination_elem.get_text(strip=True) if destination_elem else ""
            )

            # Extract route and train number from text that follows pattern "ROUTE Train NUMBER"
            train_text = departure_item.get_text()
            train = ""
            route = ""
            if "Train " in train_text:
                # Find the "Train " text
                train_keyword_start = train_text.find("Train ")

                # Look backward from "Train " to find the route (usually on the same line)
                text_before_train = train_text[:train_keyword_start].strip()
                # Get the last word before "Train " which should be the route
                route_words = text_before_train.split()
                if route_words:
                    route = route_words[-1].strip()

                # Extract train number after "Train "
                train_start = train_keyword_start + 6
                train_end = train_text.find("\n", train_start)
                if train_end == -1:
                    train_end = train_text.find(" ", train_start)
                if train_end > train_start:
                    train = train_text[train_start:train_end].strip()

            # Extract status from <strong> tags - look for status keywords
            status = ""
            strong_elements = departure_item.find_all("strong")
            for strong in strong_elements:
                text = strong.get_text(strip=True).upper()
                if text in [
                    "BOARDING",
                    "DEPARTING",
                    "ON TIME",
                    "DELAYED",
                    "ALL ABOARD",
                    "CANCELLED",
                ]:
                    status = text
                    break

            # Extract track number from text that follows "Track "
            track = ""
            if "Track " in train_text:
                track_start = train_text.find("Track ") + 6
                track_end = train_text.find("\n", track_start)
                if track_end == -1:
                    track_end = train_text.find(" ", track_start)
                if track_end > track_start:
                    track = train_text[track_start:track_end].strip()

            # Only add if we have at least train and destination
            if train and destination:
                departures.append(
                    {
                        "train": train,
                        "route": route,
                        "destination": destination,
                        "status": status,
                        "track": track,
                    }
                )
        except Exception as e:
            # Skip malformed entries
            continue

    return departures


if __name__ == "__main__":
    input_dir = os.path.join(os.path.dirname(__file__), "input")
    html_files = [f for f in os.listdir(input_dir) if f.endswith(".html")]
    if not html_files:
        print("No HTML files found in input directory.")
    else:
        for html_file in html_files:
            print(f"\n{'='*60}")
            print(f"Processing: {html_file}")
            print("=" * 60)

            html_file_path = os.path.join(input_dir, html_file)
            departures = parse_departures(html_file_path)

            # Filter for departing trains
            departing_trains = [
                dep
                for dep in departures
                if dep["status"].lower() in ["departing", "boarding", "all aboard"]
            ]

            print(f"Found {len(departures)} total departures")
            print(f"Found {len(departing_trains)} trains ready for departure")

            if departing_trains:
                print("\nTrains ready for departure:")
                for dep in departing_trains:
                    route_info = f" ({dep['route']})" if dep["route"] else ""
                    print(
                        f"  Train {dep['train']}{route_info} to {dep['destination']} - Track {dep['track']}"
                    )
            else:
                print("\nNo trains currently boarding/departing")
