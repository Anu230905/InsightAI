

import pandas as pd
import plotly.express as px


class VisualizationStudio:
    """Create interactive charts from uploaded datasets."""

    def __init__(self, df):
        self.df = df.copy()

    def get_numeric_columns(self):
        return self.df.select_dtypes(
            include="number"
        ).columns.tolist()

    def get_categorical_columns(self):
        return [
            column for column in self.df.columns
            if (
                pd.api.types.is_object_dtype(self.df[column])
                or isinstance(self.df[column].dtype, pd.CategoricalDtype)
            )
            and self.df[column].nunique(dropna=True) <= 100
        ]

    def create_chart(
        self,
        chart_type,
        x=None,
        y=None,
        aggregation="Sum",
        color=None
    ):
        """Create a Plotly chart based on the user's selections."""

        if self.df.empty:
            raise ValueError("The dataset is empty.")

        if x and x not in self.df.columns:
            raise ValueError("Selected X-axis column does not exist.")

        if y and y not in self.df.columns:
            raise ValueError("Selected Y-axis column does not exist.")

        if color and color not in self.df.columns:
            raise ValueError("Selected color column does not exist.")

        numeric_columns = self.get_numeric_columns()

        if chart_type == "Histogram":

            if not x or x not in numeric_columns:
                raise ValueError("Histogram requires a numeric column.")

            fig = px.histogram(
                self.df,
                x=x,
                title=f"Distribution of {x}",
                color=color if color != x else None
            )

        elif chart_type == "Box Plot":

            if not y or y not in numeric_columns:
                raise ValueError("Box plot requires a numeric Y-axis.")

            fig = px.box(
                self.df,
                x=x,
                y=y,
                color=color,
                title=f"Distribution of {y}"
            )

        elif chart_type == "Scatter Plot":

            if (
                not x or not y
                or x not in numeric_columns
                or y not in numeric_columns
            ):
                raise ValueError(
                    "Scatter plot requires two numeric columns."
                )

            fig = px.scatter(
                self.df,
                x=x,
                y=y,
                color=color,
                title=f"{y} vs {x}"
            )

        elif chart_type in ["Bar Chart", "Line Chart", "Pie Chart"]:

            if not x or not y:
                raise ValueError(
                    "Select both X-axis and Y-axis columns."
                )

            if y not in numeric_columns:
                raise ValueError(
                    "The Y-axis must be a numeric column."
                )

            if chart_type == "Pie Chart":
                if self.df[x].nunique(dropna=True) > 30:
                    raise ValueError(
                        "Pie charts work best with 30 or fewer categories."
                    )

            if aggregation == "Sum":
                operation = "sum"
            elif aggregation == "Average":
                operation = "mean"
            elif aggregation == "Count":
                operation = "count"
            elif aggregation == "Minimum":
                operation = "min"
            else:
                operation = "max"

            grouped = (
                self.df.groupby(x, dropna=False)[y]
                .agg(operation)
                .reset_index()
            )

            grouped.columns = [x, "Value"]

            if chart_type == "Bar Chart":

                fig = px.bar(
                    grouped,
                    x=x,
                    y="Value",
                    title=f"{aggregation} of {y} by {x}",
                    color=x if color == x else None
                )

            elif chart_type == "Line Chart":

                fig = px.line(
                    grouped,
                    x=x,
                    y="Value",
                    markers=True,
                    title=f"{aggregation} of {y} by {x}"
                )

            else:

                fig = px.pie(
                    grouped,
                    names=x,
                    values="Value",
                    title=f"{aggregation} of {y} by {x}"
                )

        else:
            raise ValueError("Unsupported chart type.")

        fig.update_layout(
            template="plotly_white",
            height=480,
            title_x=0.5,
            margin=dict(l=30, r=30, t=70, b=40)
        )

        return fig
