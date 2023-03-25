from bs4 import BeautifulSoup
import re
import sys
from datetime import datetime, timedelta
from pytz import timezone


def parse_station(soup):
    output = {}
    clock_span = soup.find(
        lambda tag: tag.name == "span"
        and tag.get("class") == ["d-block", "d-md-inline-block", "ml-md-3"]
    )
    output["reported_time"] = clock_span.text.strip()
    train_ol = soup.find(
        lambda tag: tag.name == "ol" and tag.get("class") == ["list-unstyled"]
    )
    if not train_ol:
        print("train_ol was missing, we fail")
        return output
    else:
        output["trains"] = []
        lis = train_ol.find_all("li", class_="border mb-3 rounded")
        if not lis:
            print("lis was a fucking failure")
            return output
        for li in lis:
            this_train = {}
            ps = li.find_all("p")
            # print(f"Destination: {ps[0].text}")
            this_train["destination"] = ps[0].text
            child_num = 0
            for child in ps[1].children:
                if child_num == 0:
                    # print(f"Line name: {child.text.strip()}")
                    this_train["line"] = child.text.strip()
                elif child_num == 1:
                    # print(f"Train name/number: {child.text.strip()}")
                    this_train["number"] = child.text.strip()
                else:
                    print(f"I didn't expect {child}")
                child_num += 1
            if len(ps) >= 3:
                # print(f"Status: {ps[2].text}")
                this_train["status"] = ps[2].text
            if len(ps) >= 4:
                # print(f"Track: {ps[3].text.strip()}")
                if this_train["status"] in ["BOARDING", "All Aboard"]:
                    this_field = "track"
                else:
                    this_field = "message"
                this_train[this_field] = ps[3].text.strip()
            # "d-flex flex-column ml-3 text-right"
            time_div = li.find(
                lambda tag: tag.name == "div"
                and tag.get("class") == ["d-flex", "flex-column", "ml-3", "text-right"]
            )

            strongs = time_div.find("strong")
            for strong in strongs:
                # print(f"Scheduled departure: {strong.text.strip()}")
                this_train["scheduled_departure"] = strong.text.strip()
            output["trains"].append(this_train)
    return output


def time_from_filename(filename):
    date_str = re.search("nyp-(.+)\.html", filename).group(1)
    return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S")


#  guessUTCTime :: UTCTime -> TimeZoneSeries -> Int -> Int -> UTCTime
#  -- If we have a 12-hour timestamp like "7:49" we need to know if it's AM or PM  -- and we need to know the day. If we know the time the page was retrieved we
#  -- can guess it from that. But that will be wrong if we retrieved the page at
#  -- 11:50 PM and saw something like "12:05".
#  guessUTCTime hint zone hour minute =
#    let local = utcToLocalTime' zone hint
#        day = localDay local
#        minTime = addUTCTime (-30 * 60) hint
#        candidateHours = if hour > 11 then [hour-12, hour] else [hour, hour+12]
#        makeCandidateTime cHour = localTimeToUTC' zone $ LocalTime day (TimeOfDay cHour minute 0)
#        candidateTimes = map makeCandidateTime candidateHours
#        isAcceptable t = t > minTime
#     in head $ filter isAcceptable candidateTimes


def guess_utc_time(hint: datetime, local_time: str) -> datetime:
    # local_time will be a string like "9:08"
    eastern = timezone("US/Eastern")
    utc = timezone("UTC")
    local_hint = utc.localize(hint).astimezone(eastern)
    # print(f"local_hint: {local_hint}")
    min_time = local_hint - timedelta(hours=8)
    # print(f"min_time: {min_time}")
    local_today = local_hint.date()
    # print(f"local_today: {local_today}")
    parsed_time = datetime.strptime(local_time, "%I:%M %p")
    # print(f"parsed_time: {parsed_time}")
    maybe_output = datetime.combine(local_today, parsed_time.time()).astimezone(utc)
    # print(f"maybe_output: {maybe_output}")
    if maybe_output >= min_time:
        return maybe_output
    else:
        local_tomorrow = local_today + timedelta(days=1)
        return datetime.combine(local_tomorrow, parsed_time.time()).astimezone(utc)


def fix_train_time(train, hint):
    # I hate that this is done as a mutation
    train["scheduled_departure"] = guess_utc_time(hint, train["scheduled_departure"])


def fix_station_times(station, hint):
    station["reported_time"] = guess_utc_time(hint, station["reported_time"])
    for train in station["trains"]:
        fix_train_time(train, hint)


def parse_station_file(filename):
    soup = BeautifulSoup(open(filename), "lxml")
    hint = time_from_filename(filename)
    station_dict = parse_station(soup)
    #    print(station_dict)
    fix_station_times(station_dict, hint)
    return station_dict


test_file = sys.argv[1]
print(parse_station_file(test_file))
