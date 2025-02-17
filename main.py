import pandas as pd
import nfl_data_py as nfl
import plotly.express as px

def get_data(years):
    columns = [
        "game_id", "play_id", "drive", "drive_end_transition",
        "yardline_100", "game_date", "half_seconds_remaining",
        "game_half", "down", "ydstogo", "goal_to_go"
    ]
    raw_data = nfl.import_pbp_data(
        #years=[2019, 2020, 2021, 2022, 2023],
        years=years, #[2009, 2010, 2011, 2012, 2013]
        columns=columns
    )
    is_qualifying_first_down = (
        (raw_data.down == 1) &
        (raw_data.half_seconds_remaining > 120) &
        (raw_data.drive_end_transition.isin(["END_HALF", "END_GAME"]) == False) &
        (
            (raw_data.ydstogo == 10) |
            (raw_data.goal_to_go == 1)
        )
    )
    data = raw_data.loc[is_qualifying_first_down, columns]
    data.drive_end_transition = data.drive_end_transition.str.replace(
        "BLOCKED_PUNT,_DOWNS", "BLOCKED_PUNT"
    )
    data.drive_end_transition = data.drive_end_transition.str.replace(
        "BLOCKED_PUNT,_SAFETY", "BLOCKED_PUNT"
    )
    data.drive_end_transition = data.drive_end_transition.str.replace(
        "MISSED_FG", "BLOCKED_OR_MISSED_FG"
    )
    data.drive_end_transition = data.drive_end_transition.str.replace(
        "BLOCKED_FG", "BLOCKED_OR_MISSED_FG"
    )
    data.drive_end_transition = data.drive_end_transition.str.replace(
        "BLOCKED_OR_MISSED_FG,_DOWNS", "BLOCKED_OR_MISSED_FG"
    )
    data.drive_end_transition = data.drive_end_transition.str.replace(
        "FUMBLE", "TURNOVER"
    )
    data.drive_end_transition = data.drive_end_transition.str.replace(
        "INTERCEPTION", "TURNOVER"
    )
    data.drive_end_transition = data.drive_end_transition.str.replace(
        "TURNOVER,_SAFETY", "SAFETY"
    )
    return data

def do_analysis(raw_data):
    grouped_data = raw_data.groupby(["yardline_100", "drive_end_transition"], as_index=True).agg(
        num_plays_of_type=pd.NamedAgg(column="drive_end_transition", aggfunc="count")
    )
    # Adding in zeroes for all drive end types not present at a given yardline:
    grouped_data = grouped_data.unstack(fill_value=0).stack(future_stack=True).reset_index()
    num_plays_per_yardline = raw_data.groupby("yardline_100", as_index=False).agg(
        total_num_plays=pd.NamedAgg(column="drive_end_transition", aggfunc="count")
    )

    grouped_data = num_plays_per_yardline.merge(grouped_data, on="yardline_100", how="left")
    grouped_data["fraction_of_plays_at_yardline"] = (
            grouped_data.num_plays_of_type / grouped_data.total_num_plays
    )
    return grouped_data

def main():
    raw_data = get_data([2019, 2020, 2021, 2022, 2023])
    grouped_data = do_analysis(raw_data)

    fig = px.line(
        grouped_data,
        x="yardline_100", y="fraction_of_plays_at_yardline",
        color="drive_end_transition"
    )
    fig.write_html("2019-2023.html")
    grouped_data.to_csv("2019-2023.csv")

    raw_data = get_data([2009, 2010, 2011, 2012, 2013])
    grouped_data = do_analysis(raw_data)

    fig = px.line(
        grouped_data,
        x="yardline_100", y="fraction_of_plays_at_yardline",
        color="drive_end_transition"
    )
    fig.write_html("2009-2013.html")
    grouped_data.to_csv("2009-2013.csv")


if __name__ == "__main__":
    main()
