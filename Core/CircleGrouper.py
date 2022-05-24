from numpy import nan
from pandas import DataFrame


def group_circles(df: DataFrame, max_diff_rad: float = 0.05, max_dist: float = 0.5, sort_by_group: bool = True):

    """
    The goal of this function is take a DataFrame with the columns:

         x    y    r
    0  190   88  119
    1   30  183  190
    2    1  109  188
    3  163  141  199
    4   74  192  193
    5  154   32  184

    Then return a df with a new column with all the circles grouped by similarity, based on the thresholds given.
    Example is with max_diff_rad = 0.05 and max_dist = 0.5.

         x    y    r  group
    0  190   88  119      0
    1   30  183  190      1
    2    1  109  188      1
    4   74  192  193      1
    3  163  141  199      2
    5  154   32  184      3

    param df: Input pandas DataFrame.
    param max_diff_rad: The max difference of radii of circles. 1 means radius is twice as large.
    param max_dist: 0 is complete overlap, 1 is no overlap, 2 is two max radii apart.
    param sort_by_group: Weather or not to sort the final df by the group column.
    :return:
    """

    # Keep starting df in memory
    df_raw = df.copy()

    # Group Circles
    list_of_indexed_groups = []
    while not df.empty:

        # Grab first row in DataFrame, drop row from df
        base_row = df.iloc[0]
        base_index = base_row.name
        df = df.drop(index=base_index)

        # Add starting index to working group
        current_group = [base_index]

        # If there are no rows to compare, make base circle only circle in group
        if df.empty:
            list_of_indexed_groups.append(current_group)
            break

        # Grab properties of base circle
        x, y, r = base_row["x"], base_row["y"], base_row["r"]

        # Insert Base Properties as column in df
        df["base_x"] = x
        df["base_y"] = y
        df["base_r"] = r

        # Create column for min and max radius, comparing base r and actual r in row
        df["min_r"] = df[["r", "base_r"]].min(axis=1)
        df["max_r"] = df[["r", "base_r"]].max(axis=1)

        # Calculate the difference in radii
        df["diff_rad"] = (df["max_r"] - df["min_r"]) / ((df["max_r"] + df["min_r"]) / 2)

        # Calculate the distance of circles divided by max radius
        df["dist"] = (df["x"] - df["base_x"]) ** 2 + (df["y"] - df["base_y"]) ** 2
        df["dist"] = df["dist"] ** (1/2)
        df["dist"] = df["dist"] / df["max_r"]

        # Get part of df that are in the past parameters thresholds
        sub_df = df.loc[df["diff_rad"] <= max_diff_rad]
        sub_df = sub_df.loc[sub_df["dist"] <= max_dist]

        # If there are matches, add indexes to group and remove circles from df
        if not sub_df.empty:
            sub_df_index = sub_df.index.values.tolist()
            current_group.extend(sub_df_index)
            df = df.drop(index=sub_df_index)

        list_of_indexed_groups.append(current_group)

    # Set what group each circle is in by grouped index
    df = df_raw
    df["group"] = nan
    for i, working_group in enumerate(list_of_indexed_groups):
        for index in working_group:
            df.at[index, "group"] = i

    # Double check to make sure that all circles were grouped
    verify_df = df[df["group"].isna()]
    if not verify_df.empty:
        raise ValueError("There were circles that were not grouped")

    # Cast group column to int
    df["group"] = df["group"].astype(int)

    # If sort_by_group, then sort the df by the group column
    if sort_by_group:
        df = df.sort_values(by="group")

    return df
