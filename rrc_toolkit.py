import argparse
from ue_mobility_controller import UEMobilityController
from rrc_trace_capture import RRCTraceCapture
from rrc_trace_analyzer import RRCTraceAnalyzer
from rrc_trace_visualizer import RRCTraceVisualizer


def main() -> None:
    parser = argparse.ArgumentParser(description="Unified entry point for mobility simulation and RRC tracing")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("mobility", help="Run UE mobility scenarios")
    subparsers.add_parser("capture", help="Capture RRC traces")
    subparsers.add_parser("analyze", help="Analyze captured traces")
    subparsers.add_parser("visualize", help="Visualize analysis results")

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
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
