import re
import pandas as pd
from typing import List, Dict


def parse_rrc_log(log_file_path: str) -> List[Dict[str, str]]:
    """Parse a textual log and extract RRC messages with timestamp and direction."""
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
        if line.startswith("Frame") and "bytes" in line and i + 1 < len(lines):
            in_rrc_block = False
            current_content = []
            for j in range(i + 1, min(i + 10, len(lines))):
                if "Epoch Arrival Time:" in lines[j]:
                    timestamp_match = re.search(r"Epoch Arrival Time: (\d+\.\d+)", lines[j])
                    if timestamp_match:
                        current_timestamp = float(timestamp_match.group(1))
                        break
        elif "LTE Radio Resource Control (RRC) protocol" in line:
            in_rrc_block = True
            current_content = [line]
            for j in range(i + 1, min(i + 5, len(lines))):
                if any(x in lines[j] for x in ["UL-CCCH-Message", "UL-DCCH-Message", "UL_CCCH", "UL_DCCH"]):
                    current_direction = "UL"
                    break
                elif any(x in lines[j] for x in ["DL-CCCH-Message", "DL-DCCH-Message", "DL_CCCH", "DL_DCCH"]):
                    current_direction = "DL"
                    break
        elif in_rrc_block:
            current_content.append(line)
            if i + 1 < len(lines) and (lines[i + 1].strip() == "" or "No." in lines[i + 1] or "Frame" in lines[i + 1]):
                if current_timestamp is not None and current_direction is not None:
                    messages.append({
                        "timestamp": current_timestamp,
                        "direction": current_direction,
                        "content": "\n".join(current_content)
                    })
                in_rrc_block = False
        elif "LTE RRC" in line and "Info" in line:
            protocol_match = re.search(r"LTE RRC (UL|DL)_", line)
            if protocol_match:
                current_direction = protocol_match.group(1)
                j = i + 1
                while j < len(lines) and "LTE Radio Resource Control (RRC) protocol" not in lines[j]:
                    j += 1
                if j < len(lines):
                    i = j - 1
        i += 1

    if in_rrc_block and current_timestamp is not None and current_direction is not None:
        messages.append({
            "timestamp": current_timestamp,
            "direction": current_direction,
            "content": "\n".join(current_content)
        })

    return messages


def create_qa_dataset(messages: List[Dict[str, str]]) -> pd.DataFrame:
    """Group consecutive messages and create Q/A pairs."""
    if not messages:
        return pd.DataFrame(columns=["Q_Timestamp", "Q_Content", "A_Timestamp", "A_Content"])

    messages.sort(key=lambda x: x["timestamp"])
    grouped_messages = []
    current_group = {
        "timestamp": messages[0]["timestamp"],
        "direction": messages[0]["direction"],
        "content": [messages[0]["content"]]
    }

    for i in range(1, len(messages)):
        if messages[i]["direction"] == current_group["direction"]:
            current_group["content"].append(messages[i]["content"])
        else:
            current_group["content"] = "\n---\n".join(current_group["content"])
            grouped_messages.append(current_group)
            current_group = {
                "timestamp": messages[i]["timestamp"],
                "direction": messages[i]["direction"],
                "content": [messages[i]["content"]]
            }
    current_group["content"] = "\n---\n".join(current_group["content"])
    grouped_messages.append(current_group)

    qa_pairs = []
    i = 0
    while i < len(grouped_messages) - 1:
        if grouped_messages[i]["direction"] == "UL" and grouped_messages[i + 1]["direction"] == "DL":
            qa_pairs.append({
                "Q_Timestamp": grouped_messages[i]["timestamp"],
                "Q_Content": grouped_messages[i]["content"],
                "A_Timestamp": grouped_messages[i + 1]["timestamp"],
                "A_Content": grouped_messages[i + 1]["content"]
            })
            i += 2
        else:
            i += 1

    return pd.DataFrame(qa_pairs)
