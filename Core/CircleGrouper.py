from numpy import arcsin, sqrt, pi, float64
from pandas import concat, DataFrame


def cian_of_df(a, b_df, threshold):
    # CIAN: Common Intersecting Area Normalized
    # This a modified version of code to find the intersection area of two circles
    # Using linear algebra save a lot of time, and allows the code to scale as O(n)

    b_df = b_df.copy()
    b_df = b_df[["x", "y", "r"]]

    # Pass and rename variables into dataframe
    b_df["a_r"] = a["r"]
    b_df["a_x"] = a["x"]
    b_df["a_y"] = a["y"]
    b_df["b_r"] = b_df["r"]
    b_df["b_x"] = b_df["x"]
    b_df["b_y"] = b_df["y"]

    # Fix DataFrame types
    for col in b_df:
        b_df[col] = b_df[col].astype(float64)

    # Calculate distance
    b_df["d"] = sqrt(((b_df["a_x"] - b_df["b_x"]) ** 2) + ((b_df["a_y"] - b_df["b_y"]) ** 2))

    # Fetch circles that do not overlap at all
    no_overlap = b_df.loc[b_df["d"] > (b_df["a_r"] + b_df["b_r"])].index.tolist()
    b_df = b_df.drop(index=no_overlap)

    # Fetch circles that overlap completely
    complete_overlap = b_df.loc[b_df["d"] <= (b_df["a_r"] - b_df["b_r"]).abs()]
    b_df = b_df.drop(index=complete_overlap.index.tolist())

    # Gather indexes of circles that completely overlap and have a normalized common area above threshold
    complete_overlap_indexes = []
    if not complete_overlap.empty:
        complete_overlap["a_area"] = pi * (b_df["a_r"] ** 2)
        complete_overlap["b_area"] = pi * (b_df["b_r"] ** 2)
        complete_overlap["common_area_norm"] = complete_overlap[["a_area", "b_area"]].min(axis=1) / complete_overlap[
            ["a_area", "b_area"]].max(axis=1)
        complete_overlap_indexes = complete_overlap.loc[
            complete_overlap["common_area_norm"] >= threshold].index.tolist()

    above_threshold_index = []
    if not b_df.empty:
        b_df["d^2"] = b_df["d"] ** 2
        b_df["a_r^2"] = a["r"] ** 2
        b_df["b_r^2"] = b_df["r"] ** 2

        # Code block foundation can be found at
        # https://www.xarg.org/2016/07/calculate-the-intersection-area-of-two-circles/
        b_df["x_dist"] = (b_df["a_r^2"] - b_df["b_r^2"] + b_df["d^2"]) / (2 * b_df["d"])
        b_df["y_dist"] = sqrt(b_df["a_r^2"] - (b_df["x_dist"] ** 2))
        b_df["area_1"] = b_df["a_r^2"] * arcsin((b_df["y_dist"] / b_df["a_r"]).round(3).abs())
        b_df["area_2"] = b_df["b_r^2"] * arcsin((b_df["y_dist"] / b_df["b_r"]).round(3).abs())
        b_df["area_3"] = b_df["y_dist"] * (
                b_df["x_dist"] + sqrt(((b_df["x_dist"] ** 2) + b_df["b_r^2"] - b_df["a_r^2"]).round(3)))
        b_df["common_area"] = b_df["area_1"] + b_df["area_2"] - b_df["area_3"]

        # Normalize common area by max amount of common area possible
        b_df["common_area_norm"] = b_df["common_area"] / (pi * b_df[["a_r^2", "b_r^2"]].max(axis=1))

        # Get circles that are above the given threshold
        b_df.to_csv('dev.csv')
        above_threshold_index = b_df.loc[b_df["common_area_norm"] >= threshold].index.tolist()

    above_threshold_index.extend(complete_overlap_indexes)
    return above_threshold_index


def group_circles(circles: DataFrame, cian_threshold: float):
    # cian: Common Intersecting Area Normalized

    # Verify all circles have a radius larger than 0
    if len(circles.loc[circles["r"] <= 0]) > 0:
        raise ValueError("There were circles found to have a radius equal to or smaller than zero")

    grouping_df = circles.copy()

    list_of_groups = []
    while not grouping_df.empty:
        circle_a_index = grouping_df.head(1).index.tolist()[0]
        circle_a = grouping_df.loc[circle_a_index]
        grouping_df = grouping_df.drop(index=circle_a_index)

        grouping_indexes = cian_of_df(circle_a, grouping_df, cian_threshold)
        grouping_indexes.append(circle_a_index)
        list_of_groups.append(grouping_indexes)

        grouping_indexes = grouping_indexes.copy()
        grouping_indexes.remove(circle_a_index)
        grouping_df = grouping_df.drop(index=grouping_indexes)

    list_of_groups = list(zip(range(0, len(list_of_groups)), list_of_groups))
    circles["group"] = None
    for group in list_of_groups:
        group, indexes = group

        df_2 = circles.loc[indexes]
        df_2["group"] = group

        circles = circles.drop(index=indexes)
        circles = concat([circles, df_2])

    circles = circles.sort_values("group")

    if len(circles.loc[circles["group"].isna()]) > 0:
        raise Exception("Something Broke")

    return circles
