import re
import pandas as pd
import sys
import os
import pyarrow as pa
import pyarrow.parquet as pq

# Function to parse the log file and extract RRC messages
def parse_rrc_log(log_file_path):
    messages = []
    current_timestamp = None
    current_direction = None
    current_content = []
    in_rrc_block = False
    
    try:
        with open(log_file_path, 'r') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading log file: {e}")
        return []
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Look for frame header with timestamp
        if line.startswith("Frame") and "bytes" in line and i+1 < len(lines):
            # Reset for new frame
            in_rrc_block = False
            current_content = []
            
            # Look for timestamp in the next few lines
            for j in range(i+1, min(i+10, len(lines))):
                if "Epoch Arrival Time:" in lines[j]:
                    timestamp_match = re.search(r"Epoch Arrival Time: (\d+\.\d+)", lines[j])
                    if timestamp_match:
                        current_timestamp = float(timestamp_match.group(1))
                        break
        
        # Look for RRC protocol line
        elif "LTE Radio Resource Control (RRC) protocol" in line:
            in_rrc_block = True
            current_content = [line]
            
            # Determine direction from the next few lines
            for j in range(i+1, min(i+5, len(lines))):
                if "UL-CCCH-Message" in lines[j] or "UL-DCCH-Message" in lines[j] or "UL_CCCH" in lines[j] or "UL_DCCH" in lines[j]:
                    current_direction = "UL"
                    break
                elif "DL-CCCH-Message" in lines[j] or "DL-DCCH-Message" in lines[j] or "DL_CCCH" in lines[j] or "DL_DCCH" in lines[j]:
                    current_direction = "DL"
                    break
        
        # If we're in an RRC block, collect content
        elif in_rrc_block:
            current_content.append(line)
            
            # Check if we've reached the end of the RRC block
            if i+1 < len(lines) and (lines[i+1].strip() == "" or "No." in lines[i+1] or "Frame" in lines[i+1]):
                if current_timestamp is not None and current_direction is not None:
                    messages.append({
                        "timestamp": current_timestamp,
                        "direction": current_direction,
                        "content": "\n".join(current_content)
                    })
                in_rrc_block = False
        
        # Look for protocol info line that might indicate RRC message
        elif "LTE RRC" in line and "Info" in line:
            protocol_match = re.search(r"LTE RRC (UL|DL)_", line)
            if protocol_match:
                current_direction = protocol_match.group(1)
                
                # Continue to next line to find RRC content
                j = i + 1
                while j < len(lines) and "LTE Radio Resource Control (RRC) protocol" not in lines[j]:
                    j += 1
                
                if j < len(lines):
                    # Found RRC block, will be processed in next iteration
                    i = j - 1  # -1 because we'll increment i at the end of the loop
        
        i += 1
    
    # Handle any remaining RRC block
    if in_rrc_block and current_timestamp is not None and current_direction is not None:
        messages.append({
            "timestamp": current_timestamp,
            "direction": current_direction,
            "content": "\n".join(current_content)
        })
    
    return messages

# Function to group consecutive messages and create QA pairs
def create_qa_dataset(messages):
    if not messages:
        return pd.DataFrame(columns=["Q_Timestamp", "Q_Content", "A_Timestamp", "A_Content"])
    
    # Sort messages by timestamp
    messages.sort(key=lambda x: x["timestamp"])
    
    # Group consecutive messages with same direction
    grouped_messages = []
    current_group = {
        "timestamp": messages[0]["timestamp"],
        "direction": messages[0]["direction"],
        "content": [messages[0]["content"]]
    }
    
    for i in range(1, len(messages)):
        if messages[i]["direction"] == current_group["direction"]:
            # Same direction, add to current group
            current_group["content"].append(messages[i]["content"])
        else:
            # Different direction, finalize current group and start new one
            current_group["content"] = "\n---\n".join(current_group["content"])
            grouped_messages.append(current_group)
            current_group = {
                "timestamp": messages[i]["timestamp"],
                "direction": messages[i]["direction"],
                "content": [messages[i]["content"]]
            }
    
    # Add the last group
    current_group["content"] = "\n---\n".join(current_group["content"])
    grouped_messages.append(current_group)
    
    # Create QA pairs (UL=Q, DL=A)
    qa_pairs = []
    i = 0
    while i < len(grouped_messages) - 1:
        if grouped_messages[i]["direction"] == "UL" and grouped_messages[i+1]["direction"] == "DL":
            qa_pairs.append({
                "Q_Timestamp": grouped_messages[i]["timestamp"],
                "Q_Content": grouped_messages[i]["content"],
                "A_Timestamp": grouped_messages[i+1]["timestamp"],
                "A_Content": grouped_messages[i+1]["content"]
            })
            i += 2  # Skip both messages in the pair
        else:
            i += 1  # Skip just this message
    
    return pd.DataFrame(qa_pairs)

# Main execution
def main():
    log_file = r"C:\Users\EEzim\Desktop\RRC\demo.txt"
    output_file = r"C:\Users\EEzim\Desktop\RRC\demo.parquet"
    
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
