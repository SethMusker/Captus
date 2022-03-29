#!/usr/bin/env python3
"""
Copyright 2020 Gentaro Shigita (gentaro.shigita@tum.de)
https://github.com/edgardomortiz/Captus

This file is part of Captus. Captus is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by the Free Software Foundation,
either version 3 of the License, or (at your option) any later version. Captus is distributed in
the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
details. You should have received a copy of the GNU General Public License along with Captus. If
not, see <http://www.gnu.org/licenses/>.
"""


import re
import time
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.colors import sample_colorscale
from plotly.subplots import make_subplots

from . import settings_assembly
from .misc import dim, elapsed_time, red

def normalize(l):
    if len(l) > 0:
        l_min = min(l)
        l_max = max(l)
        return [(i - l_min) / (l_max - l_min) for i in l] if l_max > l_min else 0.5
    else:
        return 0.5

def build_qc_report(out_dir, qc_extras_dir):
    start = time.time()

    ### Summary table ###
    df1 = pd.read_table(Path(qc_extras_dir, settings_assembly.QC_FILES["REBA"]))
    df2 = pd.read_table(Path(qc_extras_dir, settings_assembly.QC_FILES["PSQS"]))
    df3 = pd.read_table(Path(qc_extras_dir, settings_assembly.QC_FILES["SLEN"]))
    df4 = pd.read_table(Path(qc_extras_dir, settings_assembly.QC_FILES["PSGC"]))

    # Output reads/bases%
    df1["reads_passed_cleaning_%"] = df1["reads_passed_cleaning"] / df1["reads_input"] * 100
    df1["bases_passed_cleaning_%"] = df1["bases_passed_cleaning"] / df1["bases_input"] * 100
    # Mean read length%
    df3["length * count"] = df3["length"] * df3["count"]
    avg_read_len = (
        df3.groupby(["sample_name", "stage"])["length * count"].sum()
        / df3.groupby(["sample_name", "stage"])["count"].sum()
    )
    read_len_pct = avg_read_len.loc[:, "after"] / avg_read_len.loc[:, "before"] * 100
    # Q20, Q30 reads%
    q20 = (df2[df2["quality"] >= 20].groupby(["sample_name", "stage"])["count"].sum()
        / df2.groupby(["sample_name", "stage"])["count"].sum() * 100
    )
    q30 = (df2[df2["quality"] >= 30].groupby(["sample_name", "stage"])["count"].sum()
        / df2.groupby(["sample_name", "stage"])["count"].sum() * 100
    )
    # GC%
    df4["gc_content * count"] = df4["gc_content"] * df4["count"]
    gc = (df4.groupby(["sample_name", "stage"])["gc_content * count"].sum()
        / df4.groupby(["sample_name", "stage"])["count"].sum()
    )

    df = pd.DataFrame({
        "Sample": df1["sample"],
        "Input Reads": df1["reads_input"],
        "Input Bases": df1["bases_input"],
        "Output Reads": df1["reads_passed_cleaning"],
        "Output Reads%": df1["reads_passed_cleaning_%"],
        "Output Bases": df1["bases_passed_cleaning"],
        "Output Bases%": df1["bases_passed_cleaning_%"],
        "Mean Read Length%": read_len_pct.reset_index()[0],
        "≥Q20 Reads%": q20.xs("after", level="stage").reset_index()["count"],
        "≥Q30 Reads%": q30.xs("after", level="stage").reset_index()["count"],
        "GC%": gc.xs("after", level="stage").reset_index()[0],
    })

    sample_list = df["Sample"].unique()

    colorscale = [
        [0, "#F0D9E6"],
        [0.5, "#F5F5F5"],
        [1, "#BDE3D8"]
    ]
    figs = []
    fig = go.Figure()
    fig.add_trace(go.Table(
        header=dict(values=["<b>" + col + "</b>" for col in df.columns]),
        cells=dict(
            values=[df[col] for col in df.columns],
            fill_color=[
                "#F5F5F5",
                sample_colorscale(colorscale, normalize(df["Input Reads"].fillna(0))),
                sample_colorscale(colorscale, normalize(df["Input Bases"].fillna(0))),
                sample_colorscale(colorscale, normalize(df["Output Reads"].fillna(0))),
                sample_colorscale(colorscale, normalize(df["Output Reads%"].fillna(0))),
                sample_colorscale(colorscale, normalize(df["Output Bases"].fillna(0))),
                sample_colorscale(colorscale, normalize(df["Output Bases%"].fillna(0))),
                sample_colorscale(colorscale, normalize(df["Mean Read Length%"].fillna(0))),
                sample_colorscale(colorscale, normalize(df["≥Q20 Reads%"].fillna(0))),
                sample_colorscale(colorscale, normalize(df["≥Q30 Reads%"].fillna(0))),
                sample_colorscale(colorscale, normalize(df["GC%"].fillna(0))),
            ],
            format=[None, ",", ",", ",", ".2f", ",", ".2f"],
            align=["left", "right"],
            height=21,
        )
    ))

    buttons = []
    for col in df.columns:
        if col == "Sample":
            df.sort_values(by=col, inplace=True)
        else:
            df.sort_values(by=col, inplace=True, ascending=False)
        button = dict(label=col,
            method="restyle",
            args=[dict(
                cells=dict(values=[df[col] for col in df.columns],
                fill=dict(
                    color=[
                        "#F5F5F5",
                        sample_colorscale(colorscale, normalize(df["Input Reads"].fillna(0))),
                        sample_colorscale(colorscale, normalize(df["Input Bases"].fillna(0))),
                        sample_colorscale(colorscale, normalize(df["Output Reads"].fillna(0))),
                        sample_colorscale(colorscale, normalize(df["Output Reads%"].fillna(0))),
                        sample_colorscale(colorscale, normalize(df["Output Bases"].fillna(0))),
                        sample_colorscale(colorscale, normalize(df["Output Bases%"].fillna(0))),
                        sample_colorscale(colorscale, normalize(df["Mean Read Length%"].fillna(0))),
                        sample_colorscale(colorscale, normalize(df["≥Q20 Reads%"].fillna(0))),
                        sample_colorscale(colorscale, normalize(df["≥Q30 Reads%"].fillna(0))),
                        sample_colorscale(colorscale, normalize(df["GC%"].fillna(0))),
                    ]
                ),
                format=[None, ",", ",", ",", ".2f", ",", ".2f"],
                align=["left", "right"],
                height=21,
                )
            )]
        )
        buttons.append(button)

    updatemenus = [dict(
        buttons=buttons,
        type="dropdown",
        direction="down",
        pad=dict(t=10, b=10),
        x=1,
        xanchor="right",
        y=1,
        yanchor="bottom",
    )]

    annotations=[dict(
        text="<b>Sort by:</b>",
        x=1,
        xref="paper",
        xanchor="right",
        xshift=-160,
        y=1,
        yref="paper",
        yanchor="top",
        yshift=36,
        align="right",
        showarrow=False
    )]

    fig.update_layout(
        font_family="Arial",
        title_text=(
            "<b>Captus-assembly: Clean (Quality Control Report)<br>"
            "1. Summary Table</b><br>"
            "<sup>(Source: 03_qc_extras/"
            + ", ".join([
                settings_assembly.QC_FILES["REBA"],
                settings_assembly.QC_FILES["PSQS"],
                settings_assembly.QC_FILES["SLEN"],
                settings_assembly.QC_FILES["PSGC"],
            ])
            + ")</sup>"
        ),
        height=230 + 21 * len(sample_list) if len(sample_list) < 31 else None,
        updatemenus=updatemenus,
        annotations=annotations,
    )
    figs.append(fig)

    ### Stats on reads/bases ###
    df = pd.read_table(Path(qc_extras_dir, settings_assembly.QC_FILES["REBA"]),
                       usecols=[*range(0,3),4,5,7,8,10,11])

    df["reads_input_%"] = 100
    df["bases_input_%"] = 100
    df["reads_passed_round1_%"] = df["reads_passed_round1"] / df["reads_input"] * 100
    df["bases_passed_round1_%"] = df["bases_passed_round1"] / df["bases_input"] * 100
    df["reads_passed_round2_%"] = df["reads_passed_round2"] / df["reads_input"] * 100
    df["bases_passed_round2_%"] = df["bases_passed_round2"] / df["bases_input"] * 100
    df["reads_passed_cleaning_%"] = df["reads_passed_cleaning"] / df["reads_input"] * 100
    df["bases_passed_cleaning_%"] = df["bases_passed_cleaning"] / df["bases_input"] * 100

    var_suffix_list = ["_input", "_passed_round1", "_passed_round2", "_passed_cleaning"]
    legend_list = ["Input", "Round1", "Round2", "Cleaned"]
    colors = ["#CC79A7", "#E69F00", "#009E73", "#56B4E9"]

    fig = make_subplots(
        cols=2,
        # shared_yaxes=True,
        horizontal_spacing=0.02,
        subplot_titles=["Reads", "Bases"],
    )
    df.sort_values(
        by="bases_passed_cleaning",
        inplace=True,
    )
    for var, name, color in zip(var_suffix_list, legend_list, colors):
        # For reads
        fig.append_trace(
            go.Bar(
                x=df["reads" + var],
                y=df["sample"],
                orientation="h",
                marker_color=color,
                marker_line_color="rgb(8,8,8)",
                marker_line_width=0.25,
                legendgroup=name,
                name=name,
                customdata=df,
                hovertemplate="<b>%{y}</b><br>" +
                              "Count: <b>%{x:,} reads</b>",
            ),
            row=1,
            col=1
        )
        # For bases
        fig.append_trace(
            go.Bar(
                x=df["bases" + var],
                y=df["sample"],
                orientation="h",
                marker_color=color,
                marker_line_color="rgb(8,8,8)",
                marker_line_width=0.25,
                legendgroup=name,
                name=name,
                customdata=df,
                hovertemplate="<b>%{y}</b><br>" +
                              "Count: <b>%{x:,} bases</b>",
                showlegend=False,
            ),
            row=1,
            col=2
        )

    buttons = [
        dict(label="Count",
             method="update",
             args=[
                 dict(
                     x=[df["reads_input"],
                        df["bases_input"],
                        df["reads_passed_round1"],
                        df["bases_passed_round1"],
                        df["reads_passed_round2"],
                        df["bases_passed_round2"],
                        df["reads_passed_cleaning"],
                        df["bases_passed_cleaning"]],
                     y=[df["sample"]],
                     hovertemplate=["<b>%{y}</b><br>Count: <b>%{x:,} reads</b>",
                                    "<b>%{y}</b><br>Count: <b>%{x:,} bases</b>"] * 4,
                 ),
                 dict(
                     xaxis=dict(
                         title="Count",
                         domain=[0, 0.49],
                         ticks="outside",
                         gridcolor="rgb(64,64,64)",
                     ),
                     xaxis2=dict(
                         title="Count",
                         domain=[0.51, 1],
                         ticks="outside",
                         gridcolor="rgb(64,64,64)",
                     ),
                 )
             ]
        )
    ]
    df.sort_values(
        by="bases_passed_cleaning_%",
        inplace=True,
    )
    buttons.append(
        dict(label="Percentage",
             method="update",
             args=[
                 dict(
                     x=[df["reads_input_%"],
                        df["bases_input_%"],
                        df["reads_passed_round1_%"],
                        df["bases_passed_round1_%"],
                        df["reads_passed_round2_%"],
                        df["bases_passed_round2_%"],
                        df["reads_passed_cleaning_%"],
                        df["bases_passed_cleaning_%"]],
                     y=[df["sample"]],
                     hovertemplate=["<b>%{y}</b><br>Proportion: <b>%{x:.2f}%</b>"] * 8,
                 ),
                 dict(
                     xaxis=dict(
                         title="Proportion (%)",
                         range=[0, 100],
                         domain=[0, 0.49],
                         ticks="outside",
                         gridcolor="rgb(64,64,64)",
                     ),
                     xaxis2=dict(
                         title="Proportion (%)",
                         range=[0,100],
                         domain=[0.51, 1],
                         ticks="outside",
                         gridcolor="rgb(64,64,64)",
                     ),
                 )
             ]
        )
    )
    updatemenus = [
        dict(
            buttons=buttons,
            type="buttons",
            direction="right",
            pad={"t": 10, "b": 10},
            showactive=True,
            x=1,
            xanchor="right",
            y=1,
            yanchor="bottom",
        )
    ]

    fig.update_layout(
        font_family="Arial",
        title_text=(
            "<b>2. Stats on Reads/Bases</b><br>"
            "<sup>(Source: 03_qc_extras/"
            + settings_assembly.QC_FILES["REBA"]
            + ")</sup>"
        ),
        yaxis=dict(title="Sample"),
        yaxis2=dict(showticklabels=False),
        hoverlabel=dict(
            font_color="rgb(64,64,64)",
            bordercolor="rgb(64,64,64)",
        ),
        barmode="overlay",
        bargap=0,
        bargroupgap=0.1,
        legend_tracegroupgap=0,
        height=180 + 15 * len(sample_list),
        plot_bgcolor="rgb(8,8,8)",
        updatemenus=updatemenus,
    )
    fig.update_xaxes(
        title="Count",
        ticks="outside",
        gridcolor="rgb(64,64,64)",
        zeroline=False,
    )
    fig.update_yaxes(
        type="category",
        # categoryorder="category descending",
        ticks="outside",
        dtick=1,
        tickson="labels",
        gridcolor="rgb(8,8,8)",
    )
    figs.append(fig)

    ### Per Base Quality ###
    df = pd.read_table(Path(qc_extras_dir, settings_assembly.QC_FILES["PBSQ"]))
    df["stage"] = df["stage"].str.capitalize()

    # Covert Phred64 to Phred33
    if df["percentile_90"].max() > 42:
        phred64_sample_list = df.query("percentile_90 > 42")["sample_name"].unique()
        phred64_index = df[(df["sample_name"].isin(phred64_sample_list)) & (df["stage"] == "Before")].index
        df.iloc[phred64_index,4:] = df.iloc[phred64_index,4:] - 31
    
    var_list = [
        "mean",
        "percentile_90",
        "lower_quartile",
        "median",
        "upper_quartile",
        "percentile_10",
    ]
    var_lab_list = [
        "Mean",
        "90th Percentile",
        "75th Percentile",
        "50th Percentile",
        "25th Percentile",
        "10th Percentile",
    ]

    df_pivot = df.pivot_table(
        index=["sample_name", "stage"],
        columns=["read", "base"],
        values=var_list
    )
    df = df_pivot.stack(
        level=["read", "base"],
        dropna=False,
    ).reset_index()
    df.sort_values(
            by=["sample_name", "stage"],
            ascending=[True, False],
            inplace=True,
    )
    
    # For paired-end
    if "R2" in df["read"].to_list():
        df_R1 = df[df["read"] == "R1"]
        df_R2 = df[df["read"] == "R2"]
        fig = make_subplots(
            cols=2,
            shared_xaxes=True,
            shared_yaxes=True,
            horizontal_spacing=0.02,
            subplot_titles=["Read 1", "Read 2"],
        )
        # Read 1
        fig.append_trace(
            go.Heatmap(
                x=df_R1["base"],
                y=[df_R1["sample_name"], df_R1["stage"]],
                z=df_R1["mean"],
                customdata=df_R1,
                hovertemplate="<br>".join([
                    "<b>%{y}</b>",
                    "Position: <b>%{x} bp</b>",
                    "Mean: <b>%{customdata[5]:.0f}</b>",
                    "90<sub>th</sub> percentile: <b>%{customdata[8]}</b>",
                    "75<sub>th</sub> percentile: <b>%{customdata[4]}</b>",
                    "50<sub>th</sub> percentile: <b>%{customdata[6]}</b>",
                    "25<sub>th</sub> percentile: <b>%{customdata[9]}</b>",
                    "10<sub>th</sub> percentile: <b>%{customdata[7]}</b><extra></extra>",
                ]),
                coloraxis="coloraxis",
                hoverongaps=False,
                ygap=0.75,
            ),
            row=1,
            col=1,
        )
        # Read 2
        fig.append_trace(
            go.Heatmap(
                x=df_R2["base"],
                y=[df_R2["sample_name"], df_R2["stage"]],
                z=df_R2["mean"],
                customdata=df_R2,
                hovertemplate="<br>".join([
                    "<b>%{y}</b>",
                    "Position: <b>%{x} bp</b>",
                    "Mean: <b>%{customdata[5]:.0f}</b>",
                    "90<sub>th</sub> percentile: <b>%{customdata[8]}</b>",
                    "75<sub>th</sub> percentile: <b>%{customdata[4]}</b>",
                    "50<sub>th</sub> percentile: <b>%{customdata[6]}</b>",
                    "25<sub>th</sub> percentile: <b>%{customdata[9]}</b>",
                    "10<sub>th</sub> percentile: <b>%{customdata[7]}</b><extra></extra>",
                ]),
                coloraxis="coloraxis",
                hoverongaps=False,
                ygap=0.75,
            ),
            row=1,
            col=2,
        )

    # For single-end
    else:
        fig = go.Figure()
        fig.add_trace(
            go.Heatmap(
                x=df["base"],
                y=[df["sample_name"], df["stage"]],
                z=df["mean"],
                customdata=df,
                hovertemplate="<br>".join([
                    "<b>%{y}</b>",
                    "Position: <b>%{x} bp</b>",
                    "Mean: <b>%{customdata[5]:.0f}</b>",
                    "90<sub>th</sub> percentile: <b>%{customdata[8]}</b>",
                    "75<sub>th</sub> percentile: <b>%{customdata[4]}</b>",
                    "50<sub>th</sub> percentile: <b>%{customdata[6]}</b>",
                    "25<sub>th</sub> percentile: <b>%{customdata[9]}</b>",
                    "10<sub>th</sub> percentile: <b>%{customdata[7]}</b><extra></extra>",
                ]),
                coloraxis="coloraxis",
                hoverongaps=False,
                ygap=0.75,
            )
        )

    # Draw boundaries between samples
    y = 1.5
    while y < (len(sample_list) - 1) * 2:
        fig.add_hline(y=y, line_width=2, line_color="rgb(8,8,8)")
        y += 2

    buttons = []
    for var, lab in zip(var_list, var_lab_list):
        if "R2" in df["read"].to_list():
            z=[df_R1[var], df_R2[var]]
        else:
            z=[df[var]]
        button = dict(
            label=lab,
            method="restyle",
            args=[dict(z=z)]
        )
        buttons.append(button)

    updatemenus = [
        dict(
            buttons=buttons,
            type="dropdown",
            direction="down",
            pad=dict(t=10, b=10),
            x=1,
            xanchor="right",
            y=1,
            yanchor="bottom",
        )
    ]

    fig.update_layout(
        font_family="Arial",
        title_text=(
            "<b>3. Per Base Quality</b><br>"
            "<sup>(Source: 03_qc_extras/"
            + settings_assembly.QC_FILES["PBSQ"]
            + ")</sup>"
        ),
        plot_bgcolor="rgb(8,8,8)",
        yaxis=dict(title="Sample - Stage"),
        coloraxis=dict(
            colorscale="Spectral",
            cmin=0,
            cmax=42,
            colorbar=dict(
                title="Phred<br>Score",
                lenmode="pixels",
                len=200,
                outlinecolor="rgb(8,8,8)",
                outlinewidth=1,
                ticks="outside",
                yanchor="top" if len(sample_list) > 7 else "middle",
                y=1 if len(sample_list) > 7 else 0.5,
            )
        ),
        height=180 + 30 * len(sample_list),
        updatemenus=updatemenus,
    )
    fig.update_xaxes(
        title="Position (bp)",
        ticks="outside",
        tickson="labels",
        gridcolor="rgb(64,64,64)",
        zeroline=False,
    )
    fig.update_yaxes(
        showdividers=False,
        ticks="outside",
        dtick=1,
        tickson="labels",
        gridcolor="rgb(64,64,64)",
        autorange="reversed",
    )
    figs.append(fig)

    ### Per Read Quality ###
    df = pd.read_table(Path(qc_extras_dir, settings_assembly.QC_FILES["PSQS"]))
    df["stage"] = df["stage"].str.capitalize()

    # Convert Phred64 to Phred33
    if df["quality"].max() > 42:
        phred64_sample_list = df.query("quality > 42")["sample_name"].unique()
        phred64_index = df[(df["sample_name"].isin(phred64_sample_list)) & (df["stage"] == "Before")].index
        df.iloc[phred64_index,3] = df.iloc[phred64_index,3] - 31

    df_pivot = df.pivot(
        index=["sample_name", "read", "stage"], columns="quality", values="count"
    )
    col = 0
    while df_pivot.iloc[:,col].isnull().any() == True:
        df_pivot.iloc[:,col].fillna(0, inplace=True)
        col += 1
    df = df_pivot.reset_index().melt(
        id_vars=["sample_name", "read", "stage"],
        value_name="count",
    )
    df_grouped = df.groupby(["sample_name", "read", "stage"], as_index=False)["count"].sum()
    df_merged = pd.merge(df, df_grouped, on=["sample_name", "read", "stage"], how="outer")
    df_merged["freq"] = df_merged["count_x"] / df_merged["count_y"] * 100
    df_pivot = df_merged.pivot_table(
        index=["sample_name", "stage"],
        columns=["read", "quality"],
    )
    df = df_pivot.stack(
        level=["read", "quality"],
        dropna=False,
    ).reset_index()
    df.sort_values(
            by=["sample_name", "stage"],
            ascending=[True, False],
            inplace=True,
    )

    # For paired-end
    if "R2" in df["read"].to_list():
        df_R1 = df[df["read"] == "R1"]
        df_R2 = df[df["read"] == "R2"]
        fig = make_subplots(
            cols=2,
            shared_xaxes=True,
            shared_yaxes=True,
            horizontal_spacing=0.02,
            subplot_titles=["Read 1", "Read 2"],
        )
        # Read 1
        fig.add_trace(
            go.Heatmap(
                x=df_R1["quality"],
                y=[df_R1["sample_name"], df_R1["stage"]],
                z=df_R1["freq"],
                coloraxis="coloraxis",
                customdata=df_R1,
                hovertemplate="<b>%{y}</b><br>" +
                              "Mean Phred Score: <b>%{x}</b><br>" +
                              "Proportion: <b>%{z:.2f}%</b><br>" +
                              "Count: <b>%{customdata[4]:,.0f} reads</b><extra></extra>",
                hoverongaps=False,
                ygap=0.75,
            ),
            row=1,
            col=1,
        )
        # Read 2
        fig.add_trace(
            go.Heatmap(
                x=df_R2["quality"],
                y=[df_R2["sample_name"], df_R2["stage"]],
                z=df_R2["freq"],
                coloraxis="coloraxis",
                customdata=df_R2,
                hovertemplate="<b>%{y}</b><br>" +
                              "Mean Phred Score: <b>%{x}</b><br>" +
                              "Proportion: <b>%{z:.2f}%</b><br>" +
                              "Count: <b>%{customdata[4]:,.0f} reads</b><extra></extra>",
                hoverongaps=False,
                ygap=0.75,
            ),
            row=1,
            col=2,
        )

    # For single-end
    else:
        fig = go.Figure()
        fig.add_trace(
            go.Heatmap(
                x=df["quality"],
                y=[df["sample_name"], df["stage"]],
                z=df["freq"],
                coloraxis="coloraxis",
                customdata=df,
                hovertemplate="<b>%{y}</b><br>" +
                              "Mean Phred Score: <b>%{x}</b><br>" +
                              "Proportion: <b>%{z:.2f}%</b><br>" +
                              "Count: <b>%{customdata[4]:,.0f} reads</b><extra></extra>",
                hoverongaps=False,
                ygap=0.75,
            )
        )

    # Draw boundaries between samples
    y = 1.5
    while y < (len(sample_list) - 1) * 2:
        fig.add_hline(y=y, line_width=2, line_color="rgb(8,8,8)")
        y += 2

    fig.update_layout(
        font_family="Arial",
        title_text=(
            "<b>4. Per Read Quality</b><br>"
            "<sup>(Source: 03_qc_extras/"
            + settings_assembly.QC_FILES["PSQS"]
            + ")</sup>"
        ),
        yaxis=dict(title="Sample - Stage"),
        coloraxis=dict(
            colorscale="Spectral_r",
            colorbar=dict(
                title="Proportion",
                lenmode="pixels",
                len=200,
                outlinecolor="rgb(8,8,8)",
                outlinewidth=1,
                ticks="outside",
                ticksuffix="%",
                yanchor="top" if len(sample_list) > 7 else "middle",
                y=1 if len(sample_list) > 7 else 0.5,
            )
        ),
        height=180 + 30 * len(sample_list),
        plot_bgcolor="rgb(8,8,8)",
    )
    fig.update_xaxes(
        title="Phred Score",
        ticks="outside",
        matches="x",
        gridcolor="rgb(64,64,64)",
        zeroline=False,
        range=[df["quality"].min() - 0.5, df["quality"].max() + 0.5],
    )
    fig.update_yaxes(
        autorange="reversed",
        showdividers=False,
        ticks="outside",
        dtick=1,
        tickson="labels",
        gridcolor="rgb(64,64,64)",
    )
    figs.append(fig)

    ### Read Length Distribution ###
    df = pd.read_table(Path(qc_extras_dir, settings_assembly.QC_FILES["SLEN"]))
    df["stage"] = df["stage"].str.capitalize()
    df_pivot = df.pivot(
        index=["sample_name", "stage", "read"], columns="length", values="count"
    )
    # col = 0
    # while df_pivot.iloc[:,col].isnull().any() == True:
    #     df_pivot.iloc[:,col].fillna(0, inplace=True)
    #     col += 1

    df = df_pivot.reset_index().melt(
        id_vars=["sample_name", "read", "stage"],
        value_name="count"
    )
    df_grouped = df.groupby(["sample_name", "stage", "read"], as_index=False)["count"].sum()
    df_merged = pd.merge(df, df_grouped, on=["sample_name", "stage", "read"], how="outer")
    df_merged["freq"] = df_merged["count_x"] / df_merged["count_y"] * 100
    df_pivot = df_merged.pivot_table(
        index=["sample_name", "stage"],
        columns=["read", "length"],
    )
    df = df_pivot.stack(
        level=["read", "length"],
        dropna=False,
    ).reset_index()
    df.sort_values(
            by=["sample_name", "stage"],
            ascending=[True, False],
            inplace=True,
    )

    colorscale = [
        [0,     "#5E4FA2"],
        [0.002, "#3683BB"],
        [0.006, "#5DB7A9"],
        [0.01,  "#98D6A4"],
        [0.05,  "#D1EC9C"],
        [0.09,  "#F4FAAD"],
        [0.2,   "#FFF1A7"],
        [0.4,   "#FECE7C"],
        [0.6,   "#FB9C59"],
        [0.8,   "#EE6445"],
        [1.0,   "#D0384E"],
        # [1,    "#9E0142"],
    ]

    # For paired-end
    if "R2" in df["read"].to_list():
        df_R1 = df[df["read"] == "R1"]
        df_R2 = df[df["read"] == "R2"]
        fig = make_subplots(
            cols=2,
            shared_xaxes=True,
            shared_yaxes=True,
            horizontal_spacing=0.02,
            subplot_titles=["Read 1", "Read 2"],
        )
        # Read 1
        fig.add_trace(
            go.Heatmap(
                x=df_R1["length"],
                y=[df_R1["sample_name"], df_R1["stage"]],
                z=df_R1["freq"],
                coloraxis="coloraxis",
                customdata=df_R1,
                hovertemplate="<b>%{y}</b><br>" +
                              "Length: <b>%{x} bp</b><br>" +
                              "Proportion: <b>%{z:.2f}%</b><br>" +
                              "Count: <b>%{customdata[4]:,.0f} reads</b><extra></extra>",
                hoverongaps=False,
                ygap=2,
            ),
            row=1,
            col=1,
        )
        # Read 2
        fig.add_trace(
            go.Heatmap(
                x=df_R2["length"],
                y=[df_R2["sample_name"], df_R2["stage"]],
                z=df_R2["freq"],
                coloraxis="coloraxis",
                customdata=df_R2,
                hovertemplate="<b>%{y}</b><br>" +
                              "Length: <b>%{x} bp</b><br>" +
                              "Proportion: <b>%{z:.2f}%</b><br>" +
                              "Count: <b>%{customdata[4]:,.0f} reads</b><extra></extra>",
                hoverongaps=False,
                ygap=2,
            ),
            row=1,
            col=2,
        )

    # For single-end
    else:
        fig = go.Figure()
        fig.add_trace(
            go.Heatmap(
                x=df["length"],
                y=[df["sample_name"], df["stage"]],
                z=df["freq"],
                coloraxis="coloraxis",
                customdata=df,
                hovertemplate="<b>%{y}</b><br>" +
                              "Length: <b>%{x} bp</b><br>" +
                              "Proportion: <b>%{z:.2f}%</b><br>" +
                              "Count: <b>%{customdata[4]:,.0f} reads</b><extra></extra>",
                hoverongaps=False,
                ygap=2,
            )
        )

    # Draw boundaries between samples
    y = 1.5
    while y < (len(sample_list) - 1) * 2:
        fig.add_hline(y=y, line_width=2, line_color="rgb(8,8,8)")
        y += 2

    fig.update_layout(
        font_family="Arial",
        title_text=(
            "<b>5. Read Length Distribution</b><br>"
            "<sup>(Source: 03_qc_extras/"
            + settings_assembly.QC_FILES["SLEN"]
            + ")</sup>"
        ),
        yaxis=dict(title="Sample - Stage"),
        coloraxis=dict(
            colorscale=colorscale,
            colorbar=dict(
                title="Proportion",
                lenmode="pixels",
                len=200,
                outlinecolor="rgb(8,8,8)",
                outlinewidth=1,
                ticks="outside",
                ticksuffix="%",
                yanchor="top" if len(sample_list) > 7 else "middle",
                y=1 if len(sample_list) > 7 else 0.5,
            )
        ),
        height=180 + 30 * len(sample_list),
        plot_bgcolor="rgb(8,8,8)",
    )
    fig.update_xaxes(
        title="Read Length (bp)",
        matches="x",
        ticks="outside",
        tickson="labels",
        gridcolor="rgb(64,64,64)",
        zeroline=False,
    )
    fig.update_yaxes(
        autorange="reversed",
        showdividers=False,
        ticks="outside",
        dtick=1,
        tickson="labels",
        gridcolor="rgb(64,64,64)",
    )
    figs.append(fig)

    ### Per Base Nucleotide Content ###
    df = pd.read_table(Path(qc_extras_dir, settings_assembly.QC_FILES["PBSC"]))
    df["stage"] = df["stage"].str.capitalize()
    df_pivot = df.pivot(
        index=["sample_name", "stage"],
        columns=["read", "base"]
    ).reset_index()
    df = df_pivot.melt(
        id_vars=["sample_name", "stage"],
        var_name=["nuc", "read", "base"],
        value_name="pct",
    )
    order = {
        "A": 0,
        "T": 1,
        "G": 2,
        "C": 3,
    }
    df["nuc_order"] = df["nuc"].map(order)
    df.sort_values(
        by=["sample_name", "stage", "base", "nuc_order"],
        ascending=[True, False, True, True],
        inplace=True,
    )
    df["stage-nuc"] = df["stage"] + " - " + df["nuc"]

    # For paired-end
    if "R2" in df["read"].to_list():
        df_R1 = df[df["read"] == "R1"]
        df_R2 = df[df["read"] == "R2"]
        fig = make_subplots(
            cols=2,
            shared_xaxes=True,
            shared_yaxes=True,
            horizontal_spacing=0.02,
            subplot_titles=["Read 1", "Read 2"],
        )
        # Read 1
        fig.add_trace(
            go.Heatmap(
                x=df_R1["base"],
                y=[df_R1["sample_name"], df_R1["stage-nuc"]],
                z=df_R1["pct"],
                name="Read 1",
                coloraxis="coloraxis",
                hovertemplate="<b>%{y}</b><br>" +
                              "Position: <b>%{x} bp</b><br>" +
                              "Proportion: <b>%{z:.2f}%</b><extra></extra>",
                hoverongaps=False,
                ygap=0.25,
            ),
            row=1,
            col=1,
        )
        # Read 2
        fig.add_trace(
            go.Heatmap(
                x=df_R2["base"],
                y=[df_R2["sample_name"], df_R2["stage-nuc"]],
                z=df_R2["pct"],
                name="Read 2",
                coloraxis="coloraxis",
                hovertemplate="<b>%{y}</b><br>" +
                              "Position: <b>%{x} bp</b><br>" +
                              "Proportion: <b>%{z:.2f}%</b><extra></extra>",
                hoverongaps=False,
                ygap=0.25,
            ),
            row=1,
            col=2,
        )

    # For single-end
    else:
        fig = go.Figure()
        fig.add_trace(
            go.Heatmap(
                x=df["base"],
                y=[df["sample_name"], df["stage-nuc"]],
                z=df["pct"],
                coloraxis="coloraxis",
                hovertemplate="<b>%{y}</b><br>" +
                              "Position: <b>%{x} bp</b><br>" +
                              "Proportion: <b>%{z:.2f}%</b><extra></extra>",
                hoverongaps=False,
                ygap=0.25,
            )
        )

    # Draw boundaries between stages
    y = 3.5
    while y < (len(sample_list)) * 8:
        fig.add_hline(y=y, line_width=0.75, line_color="rgb(8,8,8)")
        y += 8

    # Draw boundaries between samples
    y = 7.5
    while y < (len(sample_list) - 1) * 8:
        fig.add_hline(y=y, line_width=2, line_color="rgb(8,8,8)")
        y += 8

    fig.update_layout(
        font_family="Arial",
        title_text=(
            "<b>6. Per Base Nucleotide Content</b><br>"
            "<sup>(Source: 03_qc_extras/"
            + settings_assembly.QC_FILES["PBSC"]
            + ")</sup>"
        ),
        yaxis=dict(title="Sample - Stage - Nucleotide"),
        coloraxis=dict(
            colorscale="Spectral_r",
            colorbar=dict(
                title="Proportion",
                lenmode="pixels",
                len=200,
                outlinecolor="rgb(8,8,8)",
                outlinewidth=1,
                ticks="outside",
                ticksuffix="%",
                yanchor="top" if len(sample_list) > 1 else "middle",
                y=1 if len(sample_list) > 1 else 0.5,
            )
        ),
        height=270 + 120 * len(sample_list),
        plot_bgcolor="rgb(8,8,8)",
    )
    fig.update_xaxes(
        title="Position (bp)",
        linecolor="black",
        ticks="outside",
        matches="x",
        gridcolor="rgb(64,64,64)",
        zeroline=False,
    )
    fig.update_yaxes(
        autorange="reversed",
        ticks="outside",
        dtick=1,
        tickson="labels",
        showdividers=False,
        gridcolor="rgb(64,64,64)",
    )
    figs.append(fig)

    ### Per Read GC Content ###
    df = pd.read_table(Path(qc_extras_dir, settings_assembly.QC_FILES["PSGC"]))
    df["stage"] = df["stage"].str.capitalize()
    df_grouped = df.groupby(["sample_name", "read", "stage"], as_index=False)["count"].sum()
    df_merged = pd.merge(df, df_grouped, on=["sample_name", "read", "stage"], how="outer")
    df_merged["freq"] = df_merged["count_x"] / df_merged["count_y"] * 100
    df = df_merged.drop(columns=["count_x", "count_y"])
    df_pivot = df.pivot(
        index=["sample_name", "stage"],
        columns=["read", "gc_content"],
        values="freq",
    ).reset_index()
    df = df_pivot.melt(
        id_vars=["sample_name", "stage"],
        value_name="freq",
    )
    df.sort_values(
        by=["sample_name", "stage"],
        ascending=[True, False],
        inplace=True,
    )
    # For paired-end
    if "R2" in df["read"].to_list():
        df_R1 = df[df["read"] == "R1"]
        df_R2 = df[df["read"] == "R2"]
        fig = make_subplots(
            cols=2,
            shared_yaxes=True,
            horizontal_spacing=0.02,
            subplot_titles=["Read 1", "Read 2"],
        )
        # Read 1
        fig.add_trace(
            go.Heatmap(
                x=df_R1["gc_content"],
                y=[df_R1["sample_name"], df_R1["stage"]],
                z=df_R1["freq"],
                coloraxis="coloraxis",
                hovertemplate="<b>%{y}</b><br>" +
                              "GC Content: <b>%{x}%</b><br>" +
                              "Proportion: <b>%{z:.2f}%</b><extra></extra>",
                hoverongaps=False,
                ygap=0.75,
            ),
            row=1,
            col=1,
        )
        # Read 2
        fig.add_trace(
            go.Heatmap(
                x=df_R2["gc_content"],
                y=[df_R2["sample_name"], df_R2["stage"]],
                z=df_R2["freq"],
                coloraxis="coloraxis",
                hovertemplate="<b>%{y}</b><br>" +
                              "GC Content: <b>%{x}%</b><br>" +
                              "Proportion: <b>%{z:.2f}%</b><extra></extra>",
                hoverongaps=False,
                ygap=0.75,
            ),
            row=1,
            col=2,
        )

    # For single-end
    else:
        fig = go.Figure()
        fig.add_trace(
            go.Heatmap(
                x=df["gc_content"],
                y=[df["sample_name"], df["stage"]],
                z=df["freq"],
                coloraxis="coloraxis",
                hovertemplate="<b>%{y}</b><br>" +
                              "GC Content: <b>%{x}%</b><br>" +
                              "Proportion: <b>%{z:.2f}%</b><extra></extra>",
                hoverongaps=False,
                ygap=0.75,
            )
        )

    # Draw boundaries between samples
    y = 1.5
    while y < (len(sample_list) - 1) * 2:
        fig.add_hline(y=y, line_width=2, line_color="rgb(8,8,8)")
        y += 2

    fig.update_layout(
        font_family="Arial",
        title_text=(
            "<b>7. Per Read GC Content</b><br>"
            "<sup>(Source: 03_qc_extras/"
            + settings_assembly.QC_FILES["PSGC"]
            + ")</sup>"
        ),
        yaxis=dict(title="Sample - Stage"),
        coloraxis=dict(
            colorscale="Spectral_r",
            colorbar=dict(
                title="Proportion",
                lenmode="pixels",
                len=200,
                outlinecolor="rgb(8,8,8)",
                outlinewidth=1,
                ticks="outside",
                ticksuffix="%",
                yanchor="top" if len(sample_list) > 7 else "middle",
                y=1 if len(sample_list) > 7 else 0.5,
            )
        ),
        height=180 + 30 * len(sample_list),
        plot_bgcolor="rgb(8,8,8)",
    )
    fig.update_xaxes(
        title="GC Content (%)",
        linecolor="black",
        ticks="outside",
        matches="x",
        gridcolor="rgb(64,64,64)",
        zeroline=False,
    )
    fig.update_yaxes(
        autorange="reversed",
        linecolor="black",
        ticks="outside",
        dtick=1,
        tickson="labels",
        showdividers=False,
        gridcolor="rgb(64,64,64)",
    )
    figs.append(fig)

    ### Sequence Duplication Level ###
    df = pd.read_table(Path(qc_extras_dir, settings_assembly.QC_FILES["SDUP"]),
                       usecols=[*range(0,4), 5])
    df["stage"] = df["stage"].str.capitalize()
    sample_list = df["sample_name"].unique()
    dup_lev_list = df["duplication_level"].unique()
    colors = {
        "1":     "#5e4fa2",
        "2":     "#4175b4",
        "3":     "#439bb5",
        "4":     "#66c2a5",
        "5":     "#94d4a4",
        "6":     "#bfe5a0",
        "7":     "#e6f598",
        "8":     "#f7fcb2",
        "9":     "#fff5ae",
        ">10":   "#fee08b",
        ">50":   "#fdbf6f",
        ">100":  "#fa9857",
        ">500":  "#f46d43",
        ">1k":   "#df4e4b",
        ">5k":   "#c32a4b",
        ">10k+": "#9e0142",
    }
    # For paired-end
    if "R2" in df["read"].to_list():
        fig = make_subplots(
            cols=2,
            shared_xaxes=True,
            shared_yaxes=True,
            horizontal_spacing=0.02,
            subplot_titles=["Read 1", "Read 2"],
        )
        df_R1 = df[df["read"] == "R1"]
        df_R2 = df[df["read"] == "R2"]
        for dup_lev in dup_lev_list:
            # Read 1
            data = df_R1[df_R1["duplication_level"] == dup_lev]
            fig.add_trace(
                go.Bar(
                    x=data["percentage_of_total"],
                    y=[data["sample_name"], data["stage"]],
                    name=dup_lev,
                    meta=[dup_lev],
                    legendgroup=dup_lev,
                    marker_color=colors[dup_lev],
                    marker_line_color="rgb(8,8,8)",
                    marker_line_width=0.25,
                    orientation="h",
                    hovertemplate="<b>%{y}</b><br>" +
                                  "Duplication Level: <b>%{meta[0]}</b><br>" +
                                  "Percentage: <b>%{x:.2f}%</b><extra></extra>",
                ),
                row=1,
                col=1,
            )
            # Read 2
            data = df_R2[df_R2["duplication_level"] == dup_lev]
            fig.add_trace(
                go.Bar(
                    x=data["percentage_of_total"],
                    y=[data["sample_name"], data["stage"]],
                    name=dup_lev,
                    meta=[dup_lev],
                    legendgroup=dup_lev,
                    marker_color=colors[dup_lev],
                    marker_line_color="rgb(8,8,8)",
                    marker_line_width=0.25,
                    showlegend=False,
                    orientation="h",
                    hovertemplate="<b>%{y}</b><br>" +
                                  "Duplication Level: <b>%{meta[0]}</b><br>" +
                                  "Percentage: <b>%{x:.2f}%</b><extra></extra>",
                ),
                row=1,
                col=2,
            )

    # For single-end
    else:
        fig = go.Figure()
        for dup_lev in dup_lev_list:
            data = df[df["duplication_level"] == dup_lev]
            fig.add_trace(
                go.Bar(
                    x=data["percentage_of_total"],
                    y=[data["sample_name"], data["stage"]],
                    name=dup_lev,
                    meta=[dup_lev],
                    legendgroup=dup_lev,
                    marker_color=colors[dup_lev],
                    marker_line_color="rgb(8,8,8)",
                    marker_line_width=0.25,
                    orientation="h",
                    hovertemplate="<b>%{y}</b><br>" +
                                  "Duplication Level: <b>%{meta[0]}</b><br>" +
                                  "Percentage: <b>%{x:.2f}%</b><extra></extra>",
                )
            )

    # Draw boundaries between samples
    y = 1.5
    while y < (len(sample_list) - 1) * 2:
        fig.add_hline(y=y, line_width=2, line_color="rgb(8,8,8)")
        y += 2

    fig.update_layout(
        font_family="Arial",
        title_text=(
            "<b>8. Sequence Duplication Level</b><br>"
            "<sup>(Source: 03_qc_extras/"
            + settings_assembly.QC_FILES["SDUP"]
            + ")</sup>"
        ),
        yaxis=dict(title="Sample - Stage"),
        barmode="stack",
        bargap=0,
        bargroupgap=0.0375,
        height=180 + 30 * len(sample_list),
        legend=dict(title="Duplication<br>Level", tracegroupgap=0),
        plot_bgcolor="rgb(8,8,8)",
    )
    fig.update_xaxes(
        title="Proportion (%)",
        ticks="outside",
        matches="x",
        range=[0, 100],
        zeroline=False,
        gridcolor="rgb(64,64,64)",
    )
    fig.update_yaxes(
        autorange="reversed",
        showdividers=False,
        ticks="outside",
        dtick=1,
        tickson="labels",
        gridcolor="rgb(64,64,64)",
    )
    figs.append(fig)

    ### Adapter Content ###
    df = pd.read_table(Path(qc_extras_dir, settings_assembly.QC_FILES["ADCO"]))
    df["stage"] = df["stage"].str.capitalize()
    df["Total adapter content"] = df.iloc[:,4:].sum(axis=1)
    df_pivot = df.pivot(
        index=["sample_name", "stage"],
        columns=["read", "position"],
    )
    df = df_pivot.stack(
        level=["read", "position"],
        dropna=False,
    ).reset_index()
    df.sort_values(
        by=["sample_name", "stage"],
        ascending=[True, False],
        inplace=True,
    )
    hover_info_list = []
    col_num = 4
    for col in df.columns[4:]:
        hover_info_list.append(col + ": <b>%{customdata[" + str(col_num) + "]:.2f}%</b>")
        col_num += 1
    hover_info_list.insert(0, "<b>%{y}</b><br>Position: <b>%{x} bp</b>")
    hovertemplate = "<br>".join(hover_info_list) + "<extra></extra>"

    # For paired-end
    if "R2" in df["read"].to_list():
        df_R1 = df[df["read"] == "R1"]
        df_R2 = df[df["read"] == "R2"]
        fig = make_subplots(
            cols=2,
            shared_xaxes=True,
            shared_yaxes=True,
            horizontal_spacing=0.02,
            subplot_titles=["Read 1", "Read 2"],
        )
        # Read 1
        fig.add_trace(
            go.Heatmap(
                x=df_R1["position"],
                y=[df_R1["sample_name"], df_R1["stage"]],
                z=df_R1["Total adapter content"],
                coloraxis="coloraxis",
                name="Read 1",
                customdata=df_R1,
                hovertemplate=hovertemplate,
                hoverongaps=False,
                ygap=0.75,
            ),
            row=1,
            col=1,
        )
        # Read 2
        fig.add_trace(
            go.Heatmap(
                x=df_R2["position"],
                y=[df_R2["sample_name"], df_R2["stage"]],
                z=df_R2["Total adapter content"],
                coloraxis="coloraxis",
                name="Read 2",
                customdata=df_R2,
                hovertemplate=hovertemplate,
                hoverongaps=False,
                ygap=0.75,
            ),
            row=1,
            col=2,
        )

    # For single-end
    else:
        fig = go.Figure()
        fig.add_trace(
            go.Heatmap(
                x=df["position"],
                y=[df["sample_name"], df["stage"]],
                z=df["Total adapter content"],
                coloraxis="coloraxis",
                customdata=df,
                hovertemplate=hovertemplate,
                hoverongaps=False,
                ygap=0.75,
            )
        )

    # Draw boundaries between samples
    y = 1.5
    while y < (len(sample_list) - 1) * 2:
        fig.add_hline(y=y, line_width=2, line_color="rgb(8,8,8)")
        y += 2

    fig.update_layout(
        font_family="Arial",
        title_text=(
            "<b>9. Adapter Content</b><br>"
            "<sup>(Source: 03_qc_extras/"
            + settings_assembly.QC_FILES["ADCO"]
            + ")</sup>"
        ),
        yaxis=dict(title="Sample - Stage"),
        coloraxis=dict(
            colorscale="Spectral_r",
            cmin=0 if max(df["Total adapter content"]) < 10 else None,
            cmax=10 if max(df["Total adapter content"]) < 10 else None,
            colorbar=dict(
                title="Proportion",
                lenmode="pixels",
                len=200,
                outlinecolor="rgb(8,8,8)",
                outlinewidth=1,
                ticks="outside",
                ticksuffix="%",
                yanchor="top" if len(sample_list) > 7 else "middle",
                y=1 if len(sample_list) > 7 else 0.5,
            )
        ),
        height=180 + 30 * len(sample_list),
        plot_bgcolor="rgb(8,8,8)",
    )
    fig.update_xaxes(
        title="Position (bp)",
        ticks="outside",
        matches="x",
        zeroline=False,
        gridcolor="rgb(64,64,64)",
    )
    fig.update_yaxes(
        autorange="reversed",
        ticks="outside",
        dtick=1,
        tickson="labels",
        showdividers=False,
        gridcolor="rgb(64,64,64)",
    )
    figs.append(fig)

    # Save plots in HTML
    config = dict(
        toImageButtonOptions=dict(
            format="svg",
        ),
        modeBarButtonsToAdd=[
            "v1hovermode",
            "hoverclosest",
            "hovercompare",
            "togglehover",
            "togglespikelines",
            "drawline",
            "drawopenpath",
            "drawclosedpath",
            "drawcircle",
            "drawrect",
            "eraseshape",
        ]
    )
    qc_html_report = Path(out_dir, "captus-assembly_clean.report.html")
    with open(qc_html_report, "w") as f:
        for fig in figs:
            f.write(
                fig.to_html(
                    full_html=False,
                    include_plotlyjs="cdn",
                    config=config
                )
            )
    if qc_html_report.exists() and qc_html_report.is_file():
        qc_html_msg = dim(f"Report generated in {elapsed_time(time.time() - start)}")
    else:
        qc_html_msg = red(f"Report not generated, verify your Python environment")

    return qc_html_report, qc_html_msg


def build_assembly_report(out_dir, asm_stats_tsv):
    start = time.time()

    ### Table ###
    # Load datatable
    df = pd.read_table(asm_stats_tsv)

    df = df.reindex(
        columns=[
            "sample",
            "total_length",
            "n_contigs",
            "avg_length",
            "N50",
            "longest_contig",
            "shortest_contig",
            "pct_contigs_>=_1kbp",
            "GC_content",
            "avg_depth",
        ],
    )

    df.rename(
        columns={
            "sample": "Sample",
            "total_length": "Total Length (bp)",
            "n_contigs": "Number of Contigs",
            "avg_length": "Mean Length (bp)",
            "N50": "Contig N50 (bp)",
            "longest_contig": "Longest Contig (bp)",
            "shortest_contig": "Shortest Contig (bp)",
            "pct_contigs_>=_1kbp": "≥1kbp Contig (%)",
            "GC_content": "GC Content (%)",
            "avg_depth": "Mean Depth (x)",
        },
        inplace=True,
    )

    sample_list = df["Sample"].unique()

    colorscale = [
        [0, "#F0D9E6"],
        [0.5, "#F5F5F5"],
        [1, "#BDE3D8"]
    ]

    figs = []
    fig = go.Figure()
    fig.add_trace(
        go.Table(
            header=dict(values=["<b>" + col + "</b>" for col in df.columns]),
            cells=dict(
                values=[df[col] for col in df.columns],
                fill_color=[
                    "#F5F5F5",
                    sample_colorscale(colorscale, normalize(df["Total Length (bp)"])),
                    sample_colorscale(colorscale, normalize(df["Number of Contigs"])),
                    sample_colorscale(colorscale, normalize(df["Mean Length (bp)"])),
                    sample_colorscale(colorscale, normalize(df["Contig N50 (bp)"])),
                    sample_colorscale(colorscale, normalize(df["Longest Contig (bp)"])),
                    sample_colorscale(colorscale, normalize(df["Shortest Contig (bp)"])),
                    sample_colorscale(colorscale, normalize(df["≥1kbp Contig (%)"])),
                    sample_colorscale(colorscale, normalize(df["GC Content (%)"])),
                    sample_colorscale(colorscale, normalize(df["Mean Depth (x)"])),
                ],
                format=[None, ",", ",", ",", ",", ",", ",", ".2f"],
                align=["left", "right"],
                height=21,
            )
        )
    )

    buttons = []
    for col in df.columns:
        if col == "Sample":
            df.sort_values(by=col, inplace=True)
        else:
            df.sort_values(by=col, inplace=True, ascending=False)
        button = dict(
            label=col,
            method="restyle",
            args=[
                dict(
                cells=dict(
                    values=[df[col] for col in df.columns],
                fill=dict(
                    color=[
                        "#F5F5F5",
                        sample_colorscale(colorscale, normalize(df["Total Length (bp)"])),
                        sample_colorscale(colorscale, normalize(df["Number of Contigs"])),
                        sample_colorscale(colorscale, normalize(df["Mean Length (bp)"])),
                        sample_colorscale(colorscale, normalize(df["Contig N50 (bp)"])),
                        sample_colorscale(colorscale, normalize(df["Longest Contig (bp)"])),
                        sample_colorscale(colorscale, normalize(df["Shortest Contig (bp)"])),
                        sample_colorscale(colorscale, normalize(df["≥1kbp Contig (%)"])),
                        sample_colorscale(colorscale, normalize(df["GC Content (%)"])),
                        sample_colorscale(colorscale, normalize(df["Mean Depth (x)"])),
                    ]
                ),
                format=[None, ",", ",", ",", ",", ",", ",", ".2f"],
                align=["left", "right"],
                height=21,
                )
            )]
        )
        buttons.append(button)

    updatemenus = [dict(
        buttons=buttons,
        type="dropdown",
        direction="down",
        pad=dict(t=10, b=10),
        x=1,
        xanchor="right",
        y=1,
        yanchor="bottom",
    )]

    annotations=[dict(
        text="<b>Sort by:</b>",
        x=1,
        xref="paper",
        xanchor="right",
        xshift=-155,
        y=1,
        yref="paper",
        yanchor="top",
        yshift=36,
        align="right",
        showarrow=False
    )]

    fig.update_layout(
        font_family="Arial",
        title_text=(
            "<b>Captus-assembly: Assemble (<i>De Novo</i> Assembly Report)<br>"
            "1. Summary Table</b><br>"
            "<sup>(Source: "
            + str(asm_stats_tsv.name)
            + ")</sup>"
        ),
        height=230 + 21 * len(sample_list) if len(sample_list) < 31 else None,
        updatemenus=updatemenus,
        annotations=annotations,
    )
    figs.append(fig)

    ### Bar plot ###
    # Load datatable
    df = pd.read_table(asm_stats_tsv)

    # Variables available as drop-down menu
    var_list = [
        "total_length",
        "n_contigs",
        "avg_length",
        "median_length",
        "N50",
        "longest_contig",
        "shortest_contig",
        [
            "pct_contigs_>=_1kbp",
            "pct_contigs_>=_2kbp",
            "pct_contigs_>=_5kbp",
            "pct_contigs_>=_10kbp",
        ],
        [
            "pct_length_>=_1kbp",
            "pct_length_>=_2kbp",
            "pct_length_>=_5kbp",
            "pct_length_>=_10kbp",
        ],
        "GC_content",
        "avg_depth",
        [
            "pct_contigs_>=_1x",
            "pct_contigs_>=_2x",
            "pct_contigs_>=_5x",
            "pct_contigs_>=_10x",
        ],
    ]

    # Button labels
    button_lab_list = [
        "Total Length (bp)",
        "Number of Contigs",
        "Mean Length (bp)",
        "Median Length (bp)",
        "Contig N50 (bp)",
        "Longest Contig (bp)",
        "Shortest Contig (bp)",
        "Contig Breakdown by Length (%)",
        "Length Breakdown by Contig Length (%)",
        "GC Content (%)",
        "Mean Depth (x)",
        "Contig Breakdown by Depth (%)",
    ]

    # X axis labels
    xlab_list = [
        "Total Length",
        "Number of Contigs",
        "Mean Length",
        "Median Length",
        "Contig N50",
        "Longest Contig Length",
        "Shortest Contig Length",
        "Proportion of Contigs",
        "Proportion of Total Length",
        "GC Content",
        "Mean Depth",
        "Proportion of Contigs",
    ]

    colors = ["#56B4E9", "#009E73", "#E69F00", "#CC79A7"]

    # Create figure
    fig = go.Figure()
    df.sort_values(
        by=var_list[0],
        ascending=False,
        inplace=True,
    )

    for i in range(4):
        fig.add_trace(
            go.Bar(
                x=df[var_list[0]],
                y=df["sample"],
                orientation="h",
                visible=True if i == 0 else False,
                marker_color=colors[i],
                marker_line_color="rgb(8,8,8)",
                hovertemplate="<b>%{y}</b><br>" +
                              xlab_list[0] + ": <b>%{x:,} bp</b><extra></extra>"
            )
        )

    # Dropdown setting
    buttons = []
    for j, var in enumerate(var_list):
        if type(var_list[j]) == list:
            df["total"] = sum([
                df[var[0]],
                df[var[1]],
                df[var[2]],
                df[var[3]],
            ])
            df.sort_values(
                by="total",
                ascending=False,
                inplace=True,
            )
            x = [
                df[var[0]],
                df[var[1]],
                df[var[2]],
                df[var[3]],
            ]
            y = [df["sample"]] * 4
            name = [re.sub(".*_>=_", "≥ ", name) for name in var_list[j]]
            visible = [True] * 4
            hovertemplate = [
                "<b>%{y}</b><br>" +
                xlab_list[j] + ": <b>%{x:.2f}%</b>"
            ]
        else:
            df.sort_values(
                by=var,
                ascending=False,
                inplace=True,
            )
            x = [df[var], None, None, None]
            y = [df["sample"], None, None, None]
            name = []
            visible = [True, False, False, False]
            if var == "n_contigs":
                hovertemplate = [
                    "<b>%{y}</b><br>" +
                    xlab_list[j] + ": <b>%{x:,}</b><extra></extra>"
                ]
            elif var == "GC_content":
                hovertemplate = [
                    "<b>%{y}</b><br>" +
                    xlab_list[j] + ": <b>%{x:.2f}%</b><extra></extra>"
                ]
            elif var == "avg_depth":
                hovertemplate = [
                    "<b>%{y}</b><br>" +
                    xlab_list[j] + ": <b>%{x:.2f}x</b><extra></extra>"
                ]
            else:
                hovertemplate = [
                    "<b>%{y}</b><br>" +
                    xlab_list[j] + ": <b>%{x:,} bp</b><extra></extra>"
                ]

        button = dict(
            label=button_lab_list[j],
            method="restyle",
            args=[
                dict(
                    x=x,
                    y=y,
                    name=name,
                    visible=visible,
                    hovertemplate=hovertemplate
                ),
            ]
        )

        buttons.append(button)

    updatemenus = [
        dict(
            buttons=buttons,
            type="dropdown",
            direction="up",
            pad={"t": 30, "b": 10},
            showactive=True,
            x=0.5,
            xanchor="center",
            y=0,
            yanchor="top"
        )
    ]
    # Layout setting
    fig.update_layout(
        plot_bgcolor="rgb(8,8,8)",
        font_family="Arial",
        title_text=(
            "<b>2. Visual Stats</b><br>"
            "<sup>(Source: "
            + str(asm_stats_tsv.name)
            + ")</sup>"
        ),
        xaxis=dict(
            gridcolor="rgb(64,64,64)",
            ticks="outside",
            zeroline=False,
        ),
        yaxis=dict(
            title="Sample",
            type="category",
            autorange="reversed",
            showgrid=False,
            ticks="outside",
        ),
        hoverlabel=dict(
            font_color="rgb(64,64,64)",
            bordercolor="rgb(64,64,64)",
        ),
        barmode="overlay",
        # height=180 + 15 * len(sample_list),
        updatemenus=updatemenus,
    )
    figs.append(fig)

    # Save plot in HTML
    config = dict(
        toImageButtonOptions=dict(
            format="svg",
        ),
        modeBarButtonsToAdd=[
            "v1hovermode",
            "hoverclosest",
            "hovercompare",
            "togglehover",
            "togglespikelines",
            "drawline",
            "drawopenpath",
            "drawclosedpath",
            "drawcircle",
            "drawrect",
            "eraseshape",
        ]
    )
    asm_html_report = Path(out_dir, "captus-assembly_assemble.report.html")
    with open(asm_html_report, "w") as f:
        for fig in figs:
            f.write(
                fig.to_html(
                    full_html=False,
                    include_plotlyjs="cdn",
                    config=config
                )
            )
    if asm_html_report.exists() and asm_html_report.is_file():
        asm_html_msg = dim(f"Report generated in {elapsed_time(time.time() - start)}")
    else:
        asm_html_msg = red(f"Report not generated, verify your Python environment")

    return asm_html_report, asm_html_msg


def build_extraction_report(out_dir, ext_stats_tsv):
    start = time.time()

    # Load datatable
    df = pd.read_table(
        ext_stats_tsv,
        low_memory=False,
        usecols=[*range(0,17)],
    )

    # Preprocess
    df_best = df[df["hit"] == 0].reset_index(drop=True).fillna("NaN")
    df_best["hit"] = df.groupby(["sample_name", "marker_type", "locus"], as_index=False).count()["hit"]
    df_best.loc[df_best["ref_type"] == "nucl", "ref_len_unit"] = "bp"
    df_best.loc[df_best["ref_type"] == "prot", "ref_len_unit"] = "aa"

    # Define variables
    marker_type = df_best["marker_type"].unique()
    if len(marker_type) > 1:
        marker_type = np.insert(marker_type, 0, "ALL")
    var_list = ["pct_recovered", "pct_identity", "hit", "score", "lwscore"]
    var_lab_list = [
        "Recovered Length (%)",
        "Identity (%)",
        "Total Hits (Copies)",
        "Score",
        "Length-weighted Score"
    ]
    colorscale = [
        [0.0, "rgb(94,79,162)"],
        [0.1, "rgb(50,136,189)"],
        [0.2, "rgb(102,194,165)"],
        [0.3, "rgb(171,221,164)"],
        [0.4, "rgb(230,245,152)"],
        [0.5, "rgb(255,255,191)"],
        [0.6, "rgb(254,224,139)"],
        [0.7, "rgb(253,174,97)"],
        [0.8, "rgb(244,109,67)"],
        [0.9, "rgb(213,62,79)"],
        [1.0, "rgb(158,1,66)"],
        [1.0, "rgb(255, 64, 255)"],
        [1.0, "rgb(255, 64, 255)"],
    ]
    colorscale2 = [
        [0.0, "rgb(94,79,162)"],
        [0.1, "rgb(50,136,189)"],
        [0.2, "rgb(102,194,165)"],
        [0.3, "rgb(171,221,164)"],
        [0.4, "rgb(230,245,152)"],
        [0.5, "rgb(255,255,191)"],
        [0.6, "rgb(254,224,139)"],
        [0.7, "rgb(253,174,97)"],
        [0.8, "rgb(244,109,67)"],
        [0.9, "rgb(213,62,79)"],
        [1.0, "rgb(158,1,66)"],
    ]
    # Dropdown for sorting
    buttons2 = [
        dict(
            label="None",
            method="relayout",
            args=[{
                "xaxis.categoryorder": "category ascending",
                "yaxis.categoryorder": "category descending",
            }],
        ),
        dict(
            label="Mean X",
            method="relayout",
            args=[{
                "xaxis.categoryorder": "mean descending",
                "yaxis.categoryorder": "category descending",
            }],
        ),
        dict(
            label="Mean Y",
            method="relayout",
            args=[{
                "xaxis.categoryorder": "category ascending",
                "yaxis.categoryorder": "mean ascending",
            }],
        ),
        dict(
            label="Mean Both",
            method="relayout",
            args=[{
                "xaxis.categoryorder": "mean descending",
                "yaxis.categoryorder": "mean ascending",
            }],
        ),
        dict(
            label="Total X",
            method="relayout",
            args=[{
                "xaxis.categoryorder": "total descending",
                "yaxis.categoryorder": "category descending",
            }],
        ),
        dict(
            label="Total Y",
            method="relayout",
            args=[{
                "xaxis.categoryorder": "category ascending",
                "yaxis.categoryorder": "total ascending",
            }],
        ),
        dict(
            label="Total Both",
            method="relayout",
            args=[{
                "xaxis.categoryorder": "total descending",
                "yaxis.categoryorder": "total ascending",
            }],
        ),
    ]

    # Make heatmap for each marker type
    figs = []
    for i, marker in enumerate(marker_type):
        if marker == "ALL":
            data = df_best
            data["marker_type - locus"] = data["marker_type"] + " - " + data["locus"].astype(str)
            x = data["marker_type - locus"]
        else:
            data = df_best[df_best["marker_type"] == marker]
            x = data["locus"]
        if data.size > 500000:
            customdata = None
            hovertemplate = "<br>".join([
                "Sample: <b>%{y}</b>",
                "Locus: <b>%{x}</b>",
                "Recovered length: <b>%{z:.2f}%</b><extra></extra>",
            ])
        else:
            customdata = data
            hovertemplate = "<br>".join([
                "Sample: <b>%{customdata[0]}</b>",
                "Marker type: <b>%{customdata[1]}</b>",
                "Locus: <b>%{customdata[2]}</b>",
                "Ref name: <b>%{customdata[3]}</b>",
                "Ref coords: <b>%{customdata[4]}</b>",
                "Ref type: <b>%{customdata[5]}</b>",
                "Ref len matched: <b>%{customdata[6]:,.0f} %{customdata[17]}</b>",
                "Total hits (copies): <b>%{customdata[7]}</b>",
                "Recovered length: <b>%{customdata[8]:.2f}%</b>",
                "Identity: <b>%{customdata[9]:.2f}%</b>",
                "Score: <b>%{customdata[10]:.3f}</b>",
                "Length-weighted score: <b>%{customdata[11]:.3f}</b>",
                "Hit length: <b>%{customdata[12]:,.0f} bp</b>",
                "CDS length: <b>%{customdata[13]:,.0f} bp</b>",
                "Intron length: <b>%{customdata[14]:,.0f} bp</b>",
                "Flanking length: <b>%{customdata[15]:,.0f} bp</b>",
                "Frameshift: <b>%{customdata[16]}</b><extra></extra>",
            ])
            
        fig = go.Figure()
        fig.add_trace(
            go.Heatmap(
                x=x,
                y=data["sample_name"],
                z=data[var_list[0]],
                zmin=data[var_list[0]].min(),
                zmax=data[var_list[0]].max() if data[var_list[0]].max() < 200 else 200,
                colorscale=colorscale2 if data[var_list[0]].max() < 200 else colorscale,
                colorbar=dict(
                    ticks="outside",
                    ticksuffix="%",
                    outlinecolor="rgb(8,8,8)",
                    outlinewidth=1,
                ),
                customdata=customdata,
                hovertemplate=hovertemplate,
                hoverongaps=False,
                xgap=0.5,
                ygap=0.5,
            )
        )

        # Dropdown for variables
        buttons1 = []
        for j, var in enumerate(var_list):
            if var == "pct_recovered":
                zmax = data[var].max() if data[var].max() < 200 else 200
                cmap = [colorscale2] if data[var].max() < 200 else [colorscale]
                if data.size > 500000:
                    hovertemplate = "<br>".join([
                        "Sample: <b>%{y}</b>",
                        "Locus: <b>%{x}</b>",
                        "Recovered length: <b>%{z:.2f}%</b><extra></extra>",
                    ])
            elif var == "pct_identity":
                zmax = data[var].max() if data[var].max() < 100 else 100
                cmap = [colorscale2] if data[var].max() <= 100 else [colorscale]
                if data.size > 500000:
                    hovertemplate = "<br>".join([
                        "Sample: <b>%{y}</b>",
                        "Locus: <b>%{x}</b>",
                        "Identity: <b>%{z:.2f}%</b><extra></extra>",
                    ])
            elif var == "hit":
                zmax = data[var].max() if data[var].max() < 50 else 50
                cmap = [colorscale2] if data[var].max() < 50 else [colorscale]
                if data.size > 500000:
                    hovertemplate = "<br>".join([
                        "Sample: <b>%{y}</b>",
                        "Locus: <b>%{x}</b>",
                        "Total hits (copies): <b>%{z}</b><extra></extra>",
                    ])
            elif var == "score":
                zmax = data[var].max() if data[var].max() < 2 else 2
                cmap = [colorscale2] if data[var].max() < 2 else [colorscale]
                if data.size > 500000:
                    hovertemplate = "<br>".join([
                        "Sample: <b>%{y}</b>",
                        "Locus: <b>%{x}</b>",
                        "Score: <b>%{z:.3f}</b><extra></extra>",
                    ])
            else:
                zmax = data[var].max() if data[var].max() < 2 else 2
                cmap = [colorscale2] if data[var].max() < 2 else [colorscale]
                if data.size > 500000:
                    hovertemplate = "<br>".join([
                        "Sample: <b>%{y}</b>",
                        "Locus: <b>%{x}</b>",
                        "Length-weighted score: <b>%{z:.3f}</b><extra></extra>",
                    ])
            button = dict(
                label=var_lab_list[j],
                method="restyle",
                args=[
                    {
                        "z": [data[var]],
                        "zmin": data[var].min(),
                        "zmax": zmax,
                        "colorscale": cmap,
                        "colorbar.ticksuffix": None if j > 1 else "%",
                        "hovertemplate": hovertemplate,
                    }
                ],
            )
            buttons1.append(button)

        updatemenus=[
            dict(
                buttons=buttons1,
                type="dropdown",
                direction="down",
                pad={"t": 10, "b": 10},
                showactive=True,
                x=0.5,
                xanchor="right",
                y=1,
                yanchor="bottom",
            ),
            dict(
                buttons=buttons2,
                type="dropdown",
                direction="down",
                pad={"t": 10, "b": 10},
                showactive=True,
                x=1,
                xanchor="right",
                y=1,
                yanchor="bottom",
            ),
        ]

        annotations = [
            dict(
                text="<b>Variable:</b>",
                x=0.5,
                xref="paper",
                xanchor="right",
                xshift=-165,
                y=1,
                yref="paper",
                yanchor="top",
                yshift=36,
                align="right",
                showarrow=False,
            ),
            dict(
                text="<b>Sort by Value:</b>",
                x=1,
                xref="paper",
                xanchor="right",
                xshift=-102,
                y=1,
                yref="paper",
                yanchor="top",
                yshift=36,
                align="right",
                showarrow=False,
            ),
        ]

        # Layout setting
        if i == 0:
            if len(marker_type) == 1:
                title = (
                        "<b>Captus-assembly: Extract (Marker Recovery Report)</b><br>"
                        "<sup>(Source: "
                        + str(ext_stats_tsv.name)
                        + ")</sup>"
                )
            else:
                title = (
                        "<b>Captus-assembly: Extract (Marker Recovery Report)<br>"
                        "1. Marker Type: "
                        + marker
                        + "</b><br><sup>(Source: "
                        + str(ext_stats_tsv.name)
                        + ")</sup>"
                )
        else:
            title = (
                "<b>"
                + str(i + 1)
                + ". Marker Type: "
                + marker
                + "</b><br><sup>(Source: "
                + str(ext_stats_tsv.name)
                + ")</sup>"
            )
        fig.update_layout(
            font_family="Arial",
            plot_bgcolor="rgb(8,8,8)",
            title=title,
            xaxis=dict(
                title="Marker type - Locus" if marker == "ALL" else "Locus",
                type="category",
                categoryorder="category ascending",
                gridcolor="rgb(64,64,64)",
                ticks="outside",
            ),
            yaxis=dict(
                title="Sample",
                type="category",
                categoryorder="category descending",
                gridcolor="rgb(64,64,64)",
                ticks="outside",
            ),
            annotations=annotations,
            updatemenus=updatemenus
        )
        figs.append(fig)

    # Save plot in HTML
    config = dict(
        scrollZoom=True,
        toImageButtonOptions=dict(
            format="svg",
        ),
        modeBarButtonsToAdd=[
            "v1hovermode",
            "hoverclosest",
            "hovercompare",
            "togglehover",
            "togglespikelines",
            "drawline",
            "drawopenpath",
            "drawclosedpath",
            "drawcircle",
            "drawrect",
            "eraseshape",
        ]
    )
    ext_html_report = Path(out_dir, "captus-assembly_extract.report.html")
    with open(ext_html_report, "w") as f:
        for fig in figs:
            f.write(
                fig.to_html(
                    full_html=False,
                    include_plotlyjs="cdn",
                    config=config
                )
            )
    if ext_html_report.exists() and ext_html_report.is_file():
        ext_html_msg = dim(f"Report generated in {elapsed_time(time.time() - start)}")
    else:
        ext_html_msg = red(f"Report not generated, verify your Python environment")

    return ext_html_report, ext_html_msg


def build_alignment_report(out_dir, aln_stats_tsv):
    start = time.time()

    df = pd.read_table(aln_stats_tsv)
    df["stage"] = df["trimmed"].astype(str).str.cat([df["paralog_filter"], df["no_refs"].astype(str)], sep="-")
    df.loc[df["format"] == "AA", "aln_len_unit"] = "aa"
    df.loc[df["format"] != "AA", "aln_len_unit"] = "bp"
    marker_type_list = df["marker_type"].unique()

    color_dict = {
        "AA": "#CC79A7",
        "NT": "#56B4E9",
        "GE": "#E69F00",
        "GF": "#009E73",
        "MA": "#CC79A7",
        "MF": "#009E73",
    }

    stage_dict = {
        "False-unfiltered-False": "02_aligned_untrimmed/ <br>01_unfiltered -",
        "False-fast-False": "02_aligned_untrimmed/ <br>02_fast -",
        "False-careful-False": "02_aligned_untrimmed/ <br>03_careful -",
        "False-unfiltered-True": "02_aligned_untrimmed/ <br>04_unfiltered_no_refs -",
        "False-fast-True": "02_aligned_untrimmed/ <br>05_fast_no_refs -",
        "False-careful-True": "02_aligned_untrimmed/ <br>06_careful_no_refs -",
        "True-unfiltered-False": "03_aligned_trimmed/ <br>01_unfiltered -",
        "True-fast-False": "03_aligned_trimmed/ <br>02_fast -",
        "True-careful-False": "03_aligned_trimmed/ <br>03_careful -",
        "True-unfiltered-True": "03_aligned_trimmed/ <br>04_unfiltered_no_refs -",
        "True-fast-True": "03_aligned_trimmed/ <br>05_fast_no_refs -",
        "True-careful-True": "03_aligned_trimmed/ <br>06_careful_no_refs -",
    }

    var_dict = {
        "Sequences": "seqs",
        "Samples": "samples",
        "Sequences per Sample": "avg_copies",
        "Alignment Length": "sites",
        "Informative Sites": "informative",
        "Informativeness (%)": "informativeness",
        "Uninformative Sites": "uninformative",
        "Constant Sites": "constant",
        "Singleton Sites": "singleton",
        "Patterns": "patterns",
        "Mean Pairwise Identity (%)": "avg_pid",
        "Missingness (%)": "missingness",
    }

    figs = []
    fig = go.Figure()
    for j, marker_type in enumerate(marker_type_list):
        data = df[df["marker_type"] == marker_type]
        fmt_list = list(reversed(data["format"].unique()))
        for i, fmt in enumerate(fmt_list):
            fig.add_trace(
                go.Violin(
                    x=data[data["format"] == fmt][list(var_dict.values())[3]],
                    y=data[data["format"] == fmt]["stage"].map(stage_dict),
                    name=fmt,
                    line=dict(
                        color=color_dict[fmt],
                    ),
                    spanmode="hard",
                    meanline_visible=True,
                    hoverinfo="x",
                    visible=True if j == 0 else False,
                    orientation="h",
                    side="negative",
                    width=1.9,
                    points=False,
                )
            )
        if j == 0:
            false_list = [[False] * len(fmt_list)]
        else:
            false_list += [[False] * len(fmt_list)]

    buttons = []
    for j, marker_type in enumerate(marker_type_list):
        data = df[df["marker_type"] == marker_type]
        fmt_list = data["format"].unique()
        visible = list(false_list)
        visible[j] = [True] * len(fmt_list)
        visible = sum(visible, [])
        button = dict(
            label=marker_type,
            method="restyle",
            args=[
                dict(
                    visible=visible,
                )
            ]
        )
        buttons.append(button)

    buttonsX = []
    for lab, var in var_dict.items():
        x_list = []
        for j, marker_type in enumerate(marker_type_list):
            data = df[df["marker_type"] == marker_type]
            fmt_list = list(reversed(data["format"].unique()))
            for i, fmt in enumerate(fmt_list):
                x = data[data["format"] == fmt][var]
                x_list.append(x)
        buttonX = dict(
            label=lab,
            method="restyle",
            args=[
                dict(
                    x=x_list,
                ),
            ]
        )
        buttonsX.append(buttonX)

    updatemenus = [
        dict(
            buttons=buttonsX,
            type="dropdown",
            direction="up",
            pad={"t": 30, "b": 10},
            active=3,
            showactive=True,
            x=0.5,
            xanchor="center",
            y=0,
            yanchor="top"
        ),
    ]
    if len(marker_type_list) > 1:
        updatemenus.append(
            dict(
                buttons=buttons,
                type="dropdown",
                direction="down",
                pad={"t": 10, "b": 10},
                showactive=True,
                x=1,
                xanchor="right",
                y=1,
                yanchor="bottom"
            )
        )

    annotations = [
        dict(
            text="<b>Marker Type:</b>",
            x=1,
            xref="paper",
            xanchor="right",
            xshift=-70,
            y=1,
            yref="paper",
            yanchor="top",
            yshift=36,
            align="right",
            showarrow=False,
        ),
    ]

    fig.update_layout(
        font_family="Arial",
        plot_bgcolor="rgb(8,8,8)",
        title=(
            "<b>Captus-assembly: Align (Alignment/Trimming Report)<br>"
            + "1. Stats Comparison at Each Processing Step"
            + "</b><br><sup>(Source: "
            + str(aln_stats_tsv.name)
            + ")</sup>"
        ),
        xaxis=dict(
            showgrid=True,
            gridcolor="rgb(64,64,64)",
            ticks="outside",
            rangemode="nonnegative",
            zeroline=False,
        ),
        yaxis=dict(
            title="Processing Step",
            showgrid=False,
            # ticks="outside",
            ticklabelposition="outside top",
            zeroline=False,
            autorange="reversed",
        ),
        hoverlabel=dict(
                font_color="rgb(64,64,64)",
                bordercolor="rgb(64,64,64)",
            ),
        legend=dict(
            title=dict(
                text="<b>Format</b>",
                side="top",
            ),
            traceorder="reversed+grouped",
        ),
        annotations=annotations if len(marker_type_list) > 1 else None,
        updatemenus=updatemenus,
    )
    figs.append(fig)

    stage_dict = {
        "False-unfiltered-False": "02_aligned_untrimmed/<br>01_unfiltered",
        "False-fast-False": "02_aligned_untrimmed/<br>02_fast",
        "False-careful-False": "02_aligned_untrimmed/<br>03_careful",
        "False-unfiltered-True": "02_aligned_untrimmed/<br>04_unfiltered_no_refs",
        "False-fast-True": "02_aligned_untrimmed/<br>05_fast_no_refs",
        "False-careful-True": "02_aligned_untrimmed/<br>06_careful_no_refs",
        "True-unfiltered-False": "03_aligned_trimmed/<br>01_unfiltered",
        "True-fast-False": "03_aligned_trimmed/<br>02_fast",
        "True-careful-False": "03_aligned_trimmed/<br>03_careful",
        "True-unfiltered-True": "03_aligned_trimmed/<br>04_unfiltered_no_refs",
        "True-fast-True": "03_aligned_trimmed/<br>05_fast_no_refs",
        "True-careful-True": "03_aligned_trimmed/<br>06_careful_no_refs",
    }

    hovertemplate = "<br>".join([
            "Locus: <b>%{customdata[6]}</b>",
            "Marker type: <b>%{customdata[4]}</b>",
            "Sequences: <b>%{customdata[7]:,.0f}</b>",
            "Samples: <b>%{customdata[8]:,.0f}</b>",
            "Sequences per sample: <b>%{customdata[9]:.2f}</b>",
            "Alignment length: <b>%{customdata[10]:,.0f} %{customdata[20]}</b>",
            "Informative sites: <b>%{customdata[11]:,.0f}</b>",
            "Informativeness: <b>%{customdata[12]:.2f}%</b>",
            "Uninformative sites: <b>%{customdata[13]:,.0f}</b>",
            "Constant sites: <b>%{customdata[14]:,.0f}</b>",
            "Singleton sites: <b>%{customdata[15]:,.0f}</b>",
            "Patterns: <b>%{customdata[16]:,.0f}</b>",
            "Mean pairwise identity: <b>%{customdata[17]:.2f}%</b>",
            "Missingness: <b>%{customdata[18]:.2f}%</b>",
    ])

    for j, marker_type in enumerate(marker_type_list):
        data = df[df["marker_type"] == marker_type]
        stage_list = data["stage"].unique()
        fmt_list = list(reversed(data["format"].unique()))
        fig = go.Figure()
        buttons_stage = []
        for i, stage in enumerate(stage_list):
            for fmt in fmt_list:
                d = data[(data["stage"] == stage) & (data["format"] == fmt)]
                fig.add_trace(
                    go.Histogram2dContour(
                        x=d[list(var_dict.values())[3]],
                        y=d[list(var_dict.values())[4]],
                        contours_coloring="fill",
                        colorscale=[
                            [0, "rgba(8,8,8,0)"],
                            [1, color_dict[fmt]],
                        ],
                        opacity=0.5,
                        showscale=False,
                        line_width=0.1,
                        visible=True if i == 0 else False,
                        hoverinfo="skip",
                        legendgroup=fmt,
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=d[list(var_dict.values())[3]],
                        y=d[list(var_dict.values())[4]],
                        name=fmt,
                        mode="markers",
                        visible=True if i == 0 else False,
                        legendgroup=fmt,
                        customdata=d,
                        hovertemplate=hovertemplate,
                        marker=dict(
                            size=8,
                            color=color_dict[fmt],
                            opacity=0.7,
                            line=dict(
                                # color="white",
                                width=1,
                            )
                        ),
                    )
                )
                fig.add_trace(
                    go.Histogram(
                        x=d[list(var_dict.values())[3]],
                        yaxis="y2",
                        name=fmt,
                        bingroup=stage + "_x",
                        marker=dict(
                            color=color_dict[fmt],
                            opacity=0.5,
                            line=dict(
                                color="rgb(8,8,8)",
                                width=1,
                            ),
                        ),
                        visible=True if i == 0 else False,
                        legendgroup=fmt,
                        showlegend=False,
                    )
                )
                fig.add_trace(
                    go.Histogram(
                        y=d[list(var_dict.values())[4]],
                        xaxis="x2",
                        name=fmt,
                        bingroup=stage + "_y",
                        marker=dict(
                            color=color_dict[fmt],
                            opacity=0.5,
                            line=dict(
                                color="rgb(8,8,8)",
                                width=1,
                            ),
                        ),
                        visible=True if i == 0 else False,
                        legendgroup=fmt,
                        showlegend=False,
                    )
                )
            visible = [[False] * len(fmt_list) * 4] * len(stage_list)
            visible[i] = [True] * len(fmt_list) * 4
            visible = sum(visible, [])
            button_stage = dict(
                label=stage_dict[stage],
                method="restyle",
                args=[
                    dict(
                        visible=visible
                    )
                ]
            )
            buttons_stage.append(button_stage)

        buttonsX, buttonsY = [], []
        for lab, var in var_dict.items():
            x_list, y_list = [], []
            for stage in stage_list:
                for fmt in fmt_list:
                    d = data[(data["stage"] == stage) & (data["format"] == fmt)]
                    x = [
                        d[var],
                        d[var],
                        d[var],
                        None,
                    ]
                    y = [
                        d[var],
                        d[var],
                        None,
                        d[var],
                    ]
                    x_list += x
                    y_list += y
            buttonX = dict(
                label=lab,
                method="update",
                args=[
                    dict(
                        x=x_list,
                    ),
                ]
            )
            buttonY = dict(
                label=lab,
                method="update",
                args=[
                    dict(
                        y=y_list,
                    ),
                ]
            )
            buttonsX.append(buttonX)
            buttonsY.append(buttonY)

        updatemenus = [
            dict(
                buttons=buttons_stage,
                type="dropdown",
                direction="down",
                pad={"t": 10, "b": 10},
                showactive=True,
                x=0.9,
                xanchor="right",
                y=1,
                yanchor="bottom"
            ),
            dict(
                buttons=buttonsX,
                type="dropdown",
                direction="up",
                pad={"t": 30, "b": 10},
                active=3,
                showactive=True,
                x=0.45,
                xanchor="center",
                y=0,
                yanchor="top"
            ),
            dict(
                buttons=buttonsY,
                type="dropdown",
                direction="down",
                pad={"t": 10, "b": 10, "r": 40},
                active=4,
                showactive=True,
                x=0,
                xanchor="right",
                y=0.425,
                yanchor="middle"
            ),
        ]

        annotations = [
            dict(
                text="<b>Processing Step:</b>",
                x=0.9,
                xref="paper",
                xanchor="right",
                xshift=-175,
                y=1,
                yref="paper",
                yanchor="top",
                yshift=36,
                align="right",
                showarrow=False,
            ),
        ]

        if j == 0:
            if len(marker_type_list) == 1:
                title = (
                    "<b>2. Bivariate Relationships and Distributions</b><br>"
                    + "<sup>(Source: "
                    + str(aln_stats_tsv.name)
                    + ")</sup>"
                )
            else:
                title = (
                    "<b>2. Bivariate Relationships and Distributions<br>"
                    + "Marker Type: "
                    + marker_type
                    + "</b><br><sup>(Source: "
                    + str(aln_stats_tsv.name)
                    + ")</sup>"
                )
        else:
            title = (
                "<b>Marker Type: "
                + marker_type
                + "</b><br><sup>(Source: "
                + str(aln_stats_tsv.name)
                + ")</sup>"
            )
        fig.update_layout(
            font_family="Arial",
            plot_bgcolor="rgb(8,8,8)",
            title=title,
            xaxis=dict(
                showgrid=True,
                gridcolor="rgb(64,64,64)",
                ticks="outside",
                domain=[0,0.9],
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor="rgb(64,64,64)",
                ticks="outside",
                domain=[0,0.9],
            ),
            xaxis2=dict(
                title="Count",
                gridcolor="rgb(64,64,64)",
                ticks="outside",
                zeroline=True,
                domain=[0.9,1],
            ),
            yaxis2=dict(
                title="Count",
                gridcolor="rgb(64,64,64)",
                ticks="outside",
                zeroline=True,
                domain=[0.9,1],
            ),
            hoverlabel=dict(
                font_color="rgb(64,64,64)",
                bordercolor="rgb(64,64,64)",
            ),
            legend=dict(
                title=dict(
                    text="<b>Format</b>",
                    side="top",
                ),
                traceorder="reversed",
            ),
            barmode="overlay",
            annotations=annotations,
            updatemenus=updatemenus,
        )
        figs.append(fig)
    
    # Save plot in html
    aln_html_report = Path(out_dir, "captus-assembly_align.report.html")
    with open(aln_html_report, "w") as f:
        for i, fig in enumerate(figs):
            f.write(
                fig.to_html(
                    full_html=False,
                    include_plotlyjs="cdn",
                    config=dict(
                        scrollZoom=False if i == 0 else True,
                        toImageButtonOptions=dict(
                            format="svg",
                        ),
                        modeBarButtonsToAdd=[
                            "v1hovermode",
                            "hoverclosest",
                            "hovercompare",
                            "togglehover",
                            "togglespikelines",
                            "drawline",
                            "drawopenpath",
                            "drawclosedpath",
                            "drawcircle",
                            "drawrect",
                            "eraseshape",
                        ]
                    ),
                )
            )
    if aln_html_report.exists() and aln_html_report.is_file():
        aln_html_msg = dim(f"Report generated in {elapsed_time(time.time() - start)}")
    else:
        aln_html_msg = red(f"Report not generated, verify your Python environment")

    return aln_html_report, aln_html_msg
