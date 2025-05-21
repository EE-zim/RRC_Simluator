import pandas as pd
import argparse
from rrc_utils import parse_rrc_log, create_qa_dataset


def main() -> None:
    """Parse an RRC log and produce a QA parquet file."""
    parser = argparse.ArgumentParser(description="Extract RRC messages and build QA dataset")
    parser.add_argument("log_file", help="Path to the text log file")
    parser.add_argument("output_file", help="Path to output parquet file")
    args = parser.parse_args()

    log_file = args.log_file
    output_file = args.output_file
    
    print("Extracting RRC messages from log file...")
    messages = parse_rrc_log(log_file)
    
    if not messages:
        print("No RRC messages found in the log file.")
        # Create empty DataFrame with correct schema
        empty_df = pd.DataFrame(columns=["Q_Timestamp", "Q_Content", "A_Timestamp", "A_Content"])
        empty_df.to_parquet(output_file, index=False)
        print(f"Created empty parquet file: {output_file}")
        return
    
    print(f"Found {len(messages)} RRC messages.")
    
    # Create QA dataset
    print("Creating QA dataset...")
    qa_df = create_qa_dataset(messages)
    
    if qa_df.empty:
        print("No QA pairs could be formed from the extracted messages.")
        # Create empty DataFrame with correct schema
        empty_df = pd.DataFrame(columns=["Q_Timestamp", "Q_Content", "A_Timestamp", "A_Content"])
        empty_df.to_parquet(output_file, index=False)
        print(f"Created empty parquet file: {output_file}")
        return
    
    print(f"Created {len(qa_df)} QA pairs.")
    
    # Save to parquet
    print(f"Saving to {output_file}...")
    qa_df.to_parquet(output_file, index=False)
    
    print("Done!")
    print("\nDataFrame Info:")
    qa_df.info(verbose=True)
    print("\nFirst few rows:")
    print(qa_df.head())

if __name__ == "__main__":
    main()
