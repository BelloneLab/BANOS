"""
Example of BANOS Analysis Python Script

Description:
This script processes annotation files using the Behavior Annotation Score (BANOS) Library.
It identifies pairs of human and machine annotations, compares them, calculates BANOS metrics, 
and visualizes the results in confusion matrices.

Assumptions:
- Annotation files should be in .csv format.
- Each set of human and machine annotations are expected to be stored in paired files within the same folders.
- Files should adhere to a specific format, accessible in the specified directory.

Dependencies:
- Python 3.x
- Required libraries: pandas, numpy, matplotlib, seaborn
- BANOS library files must be accessible in the script's directory or Python path.

Usage:
1. Run the script in a Python environment.
2. Input the required information when prompted:
    - Root directory for annotation files.
    - Patterns for identifying human and machine annotation files.
    - Header row details of the files.
3. The script will process the data and display the results.

Reference:
This code is written by Benoit Girard and Giuseppe Chindemi.
It is part of the publication:
[2024]. [Title of the paper]. [Journal Name], [Volume(Issue)], [pages]. [DOI or URL]
If you use this code in your research or project, please cite the above publication.
For inquiries, please contact the corresponding author.
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from BANOS import preprocess_data, calculate_banos_for_each_file, aggregate_metrics

    
def find_annotation_pairs(found_folders, root_dir, human_pattern, machine_pattern, header_row_name, header_row_total, annotation_ext='.csv'):
    # Function to find annotation pairs in given directory
    annotation_pairs = {}
    folders_with_multiple_files = []

    for folder in found_folders:
        folder_path = os.path.join(root_dir, folder)
        human_files = [f for f in os.listdir(folder_path) if f.endswith(annotation_ext) and human_pattern in f]
        machine_files = [f for f in os.listdir(folder_path) if f.endswith(annotation_ext) and machine_pattern in f]

        if len(human_files) > 1 or len(machine_files) > 1:
            folders_with_multiple_files.append(folder)
        elif human_files and machine_files:
            annotation_pairs[folder] = {
                'human_annotation': os.path.join(folder_path, human_files[0]),
                'machine_annotation': os.path.join(folder_path, machine_files[0]),
                'header_row_name': header_row_name,
                'header_row_total': header_row_total
            }

    return annotation_pairs, folders_with_multiple_files

def prepare_matrices(data_pairs):
    data_dict = {}

    for folder, files in data_pairs.items():
        header_row = files['header_row_name']
        num_header_rows = files['header_row_total']

        full_df = pd.read_csv(files['human_annotation'], header=None)
        column_names = full_df.iloc[header_row]
        human_annotation_df = full_df.drop(list(range(num_header_rows+1))).rename(columns=column_names)
        machine_annotation_df = pd.read_csv(files['machine_annotation'])

        human_annotation_df = human_annotation_df.loc[:, human_annotation_df.apply(lambda x: pd.to_numeric(x, errors='coerce').dropna().isin([0, 1]).all())]
        machine_annotation_df = machine_annotation_df.loc[:, machine_annotation_df.apply(lambda x: pd.to_numeric(x, errors='coerce').dropna().isin([0, 1]).all())]

        human_cols = human_annotation_df.columns
        machine_cols = machine_annotation_df.columns

        extended_machine_data = {}
        extended_human_data = {}

        for m_col in machine_cols:
            for h_col in human_cols:
                pair_name = f"{m_col}_vs_{h_col}"
                extended_machine_data[pair_name] = machine_annotation_df[m_col].astype(int)
                extended_human_data[pair_name] = human_annotation_df[h_col].astype(int)

        extended_machine_df = pd.DataFrame(extended_machine_data)
        extended_human_df = pd.DataFrame(extended_human_data)

        frame_index = np.arange(len(human_annotation_df))
        extended_machine_df.insert(0, 'frame_index', frame_index)
        extended_human_df.insert(0, 'frame_index', frame_index)

        data_dict[folder] = (extended_machine_df, extended_human_df)

    print("Data processing complete.")
    return data_dict


def plot_banos_metrics(group_metrics):
    # Extract unique machine and human motif names
    machine_motifs = sorted(set(key.split('_vs_')[0] for key in group_metrics.keys()))
    human_motifs = sorted(set(key.split('_vs_')[1] for key in group_metrics.keys()))

    # Initialize dictionaries to hold confusion matrices for each metric
    metric_matrices = {
        "precision": pd.DataFrame(0, index=machine_motifs, columns=human_motifs),
        "recall": pd.DataFrame(0, index=machine_motifs, columns=human_motifs),
        "f1_score": pd.DataFrame(0, index=machine_motifs, columns=human_motifs),
        "so": pd.DataFrame(0, index=machine_motifs, columns=human_motifs),
        "tp": pd.DataFrame(0, index=machine_motifs, columns=human_motifs),
        "ic": pd.DataFrame(0, index=machine_motifs, columns=human_motifs),
    }

    # Populate the matrices
    for pair, metrics in group_metrics.items():
        machine_motif, human_motif = pair.split('_vs_')
        for metric in metric_matrices.keys():
            metric_matrices[metric].loc[machine_motif, human_motif] = metrics[metric]

    # Plotting
    num_metrics = len(metric_matrices)
    grid_rows = int(np.ceil(num_metrics / 2))
    grid_cols = 2 if num_metrics > 1 else 1

    # Set up the grid layout
    fig, axs = plt.subplots(grid_rows, grid_cols, figsize=(12 * grid_cols, 10 * grid_rows))
    if grid_rows * grid_cols > 1:
        axs = axs.flatten()  # Flatten if more than one subplot

    for i, (metric, matrix) in enumerate(metric_matrices.items()):
        ax = axs[i] if num_metrics > 1 else axs
        sns.heatmap(matrix, annot=True, cmap='Blues', fmt=".2f", vmin=0, vmax=1, ax=ax)
        ax.set_title(f'{metric.capitalize()} Confusion Matrix')
        ax.set_xlabel('Human Annotated Motifs')
        ax.set_ylabel('Machine Annotated Motifs')
        ax.tick_params(axis='x', rotation=45)
        ax.tick_params(axis='y', rotation=0)

    plt.tight_layout()

    plt.show()
    
    
# User inputs
root_dir = input("Enter the root directory: ")
human_pattern = input("Enter the human annotation pattern: ")
machine_pattern = input("Enter the machine annotation pattern: ")
header_row_name = int(input("Enter the number of the header row name: ")) - 1
header_row_total = int(input("Enter the total number of header rows: ")) - 1

# List all folders in root directory
found_folders = [folder for folder in os.listdir(root_dir) if os.path.isdir(os.path.join(root_dir, folder))]

# Find annotation pairs
annotation_pairs, multiple_files_folders = find_annotation_pairs(found_folders, root_dir, human_pattern, machine_pattern, header_row_name, header_row_total)

if annotation_pairs:
    print("Folder, Human Annotation File and Machine Annotation File:")
    for folder, files in annotation_pairs.items():
        print(f"{folder}: Human - {files['human_annotation']}, Machine - {files['machine_annotation']}")
else:
    print("No matching files detected.")

if multiple_files_folders:
    print("\nFolders with Multiple Matching Files:")
    for folder in multiple_files_folders:
        print(folder)

# Process and display results
data_dict = prepare_matrices(annotation_pairs)

preprocessed_data, dropped_info = preprocess_data(data_dict)
banos_metrics = calculate_banos_for_each_file(preprocessed_data)
group_metrics, overall_metrics = aggregate_metrics(banos_metrics)

# Output
print("Group Metrics:", group_metrics)
print("Overall Metrics:", overall_metrics)
print("Behavior Annotation Score (BANOS) processing complete.")

# Plotting BANOS Metrics
plot_banos_metrics(group_metrics)
    