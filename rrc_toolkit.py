import argparse
import os
import sys

ENHANCED_PATH = os.path.join(os.path.dirname(__file__), "srsRAN_5G", "srsRAN_5G")
if ENHANCED_PATH not in sys.path:
    sys.path.insert(0, ENHANCED_PATH)

from enhanced_ue_mobility_controller_v2 import main as mobility_main
from rrc_trace_capture import RRCTraceCapture
from enhanced_rrc_trace_analyzer import main as analyzer_main
from enhanced_visualization_dashboard import app as dashboard_app


def main() -> None:
    parser = argparse.ArgumentParser(description="Unified entry point for mobility simulation and RRC tracing")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("mobility", help="Run UE mobility scenarios")
    subparsers.add_parser("capture", help="Capture RRC traces")
    subparsers.add_parser("analyze", help="Analyze captured traces")
    subparsers.add_parser("visualize", help="Visualize analysis results")

    args = parser.parse_args()

    if args.command == "mobility":
        mobility_main()
    elif args.command == "capture":
        capture = RRCTraceCapture()
        capture.capture_all_traces()
    elif args.command == "analyze":
        analyzer_main()
    elif args.command == "visualize":
        dashboard_app.run_server(debug=False, host="0.0.0.0", port=8050)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
