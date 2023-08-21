import panel as pn
import holoviews as hv
import config
import holoviews.operation.datashader as hd
import numpy as np
from plot_helpers import filter_points, hover_points

def make_hist_on_axis(dimension, points, num_bins=30):
    ### Make histogram function for a specified axis of a scatter plot
    def compute_hist(x_range, y_range):
        filtered_points = filter_points(points, x_range, y_range)
        hist = hv.operation.histogram(
            filtered_points, dimension=dimension, num_bins=num_bins, normed="height"
        )
        return hist

    return compute_hist



def make_hist(data, title, bins_range, log_y=True, plot_width=800):
    ### Make histogram from given count data
    count, bins = np.histogram(data, bins=bins_range)
    ylabel = "log(Count)" if log_y else "Count"
    np.seterr(divide="ignore")
    if log_y:
        count = np.log10(count)
        count[count == -np.inf] = 0
    histogram = hv.Histogram((count, bins)).opts(
        title=title, ylabel=ylabel, tools=["hover"]
    )
    histogram = histogram.opts(shared_axes=False, width=round(plot_width / 2))
    return histogram


def make_hist_panel(tsm, log_y):
    ### Make row of histograms for holoviews panel
    overall_site_hist = make_hist(
        tsm.sites_num_mutations,
        "Mutations per site",
        range(29),
        log_y=log_y,
        plot_width=config.PLOT_WIDTH,
    )
    overall_node_hist = make_hist(
        tsm.nodes_num_mutations,
        "Mutations per node",
        range(10),
        log_y=log_y,
        plot_width=config.PLOT_WIDTH,
    )
    return pn.Row(overall_site_hist, overall_node_hist)

def page(tsm):
    hv.extension("bokeh")
    plot_width = 1000
    log_y_checkbox = pn.widgets.Checkbox(
        name="Log y-axis of Mutations per site/node plots", value=False
    )

    points = tsm.mutations_df.hvplot.scatter(
        x="position",
        y="time",
        hover_cols=["position", "time", "mutation_node", "node_flag"],
    ).opts(width=plot_width, height=config.PLOT_HEIGHT)

    range_stream = hv.streams.RangeXY(source=points)
    streams = [range_stream]

    filtered = points.apply(filter_points, streams=streams)
    time_hist = hv.DynamicMap(
        make_hist_on_axis(dimension="time", points=points, num_bins=10), streams=streams
    )
    site_hist = hv.DynamicMap(
        make_hist_on_axis(dimension="position", points=points, num_bins=10),
        streams=streams,
    )
    hover = filtered.apply(hover_points)
    shaded = hd.datashade(filtered, width=400, height=400, streams=streams)

    main = (shaded * hover).opts(
        hv.opts.Points(tools=["hover"], alpha=0.1, hover_alpha=0.2, size=10)
    )

    hist_panel = pn.bind(make_hist_panel, log_y=log_y_checkbox, tsm=tsm)

    plot_options = pn.Column(
        pn.pane.Markdown("## Plot Options"),
        log_y_checkbox,
    )

    return pn.Column(main << time_hist << site_hist, hist_panel, plot_options)