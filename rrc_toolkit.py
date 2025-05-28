import argparse
import subprocess
from ue_mobility_controller import UEMobilityController
from rrc_trace_capture import RRCTraceCapture
from rrc_trace_analyzer import RRCTraceAnalyzer
from rrc_trace_visualizer import RRCTraceVisualizer
from srsRAN_5G.srsRAN_5G import (
    enhanced_ue_mobility_controller_v2,
    enhanced_rrc_trace_analyzer,
    enhanced_performance_metrics_collector,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Unified entry point for mobility simulation and RRC tracing")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("mobility", help="Run UE mobility scenarios (legacy)")
    subparsers.add_parser("capture", help="Capture RRC traces")
    subparsers.add_parser("analyze", help="Analyze captured traces (legacy)")
    subparsers.add_parser("visualize", help="Visualize analysis results")
    subparsers.add_parser("mobility5g", help="Run enhanced 5G mobility simulation")
    subparsers.add_parser("analyze5g", help="Analyze traces with enhanced analyzer")
    subparsers.add_parser("metrics", help="Collect performance metrics")

    args = parser.parse_args()

    if args.command == "mobility":
        controller = UEMobilityController()
        controller.run_mobility_scenario()
    elif args.command == "capture":
        capture = RRCTraceCapture()
        capture.capture_all_traces()
    elif args.command == "analyze":
        analyzer = RRCTraceAnalyzer()
        analyzer.run_analysis()
    elif args.command == "visualize":
        visualizer = RRCTraceVisualizer()
        visualizer.run_visualization()
    elif args.command == "mobility5g":
        enhanced_ue_mobility_controller_v2.main()
    elif args.command == "analyze5g":
        enhanced_rrc_trace_analyzer.main()
    elif args.command == "metrics":
        enhanced_performance_metrics_collector.main()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
