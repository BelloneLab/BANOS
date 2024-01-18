"""
Behavior Annotation Score (BANOS) Calculation Library

This script calculates a set of metrics composing the Behavior Annotation Score (BANOS) for automatic annotations of behaviors in video data.
BANOS is a set of metrics designed to evaluate algorithmic annotations against a ground truth, integrating aspects of accuracy, overlap, temporal precision, and continuity of behavior annotations segments.


Metrics:
- Detection Accuracy (DA): Precision, Recall, and F1 score of segment of behavior (not frame)
  to assess the proportion of correctly identified positive segments out of all segments identified as positive (precision),
  the proportion of actual positive segments that were correctly identified (recall) and
  the harmonic mean of Precision and Recall, providing a balance between them (F1).
- Segment overlap (SO): Temporal Intersection over Union (tIoU) 
  to assess the overlap between the predicted segment and the ground truth segment.
- Temporal Precision (TP): Accuracy in predicting segment start and end times
  to assess the accuracy of the start and end times of predicted segments.
- Intra-segment Continuity (IC): Label continuity within each segment
  to assess the number of label switches within a segment.

The script includes functions for data preprocessing, segment identification, metric calculation, and aggregation of results across behaviors and files.

Usage:
- Input data should be in the form of a dictionary, with file names as keys and tuples of prediction and ground truth matrices as values.
- Run the script to preprocess the data, compute BANOS metrics for each behavior, and aggregate the results.

Example usage:
data_dict = {
    'file1': (pred_matrix1, gt_matrix1),
    'file2': (pred_matrix2, gt_matrix2),
    # Add more file entries as needed
}
preprocessed_data, dropped_info = preprocess_data(data_dict)
banos_metrics = calculate_banos_for_each_file(preprocessed_data)
group_metrics, overall_metrics = aggregate_metrics(banos_metrics)
print("Group Metrics:", group_metrics)
print("Overall Metrics:", overall_metrics)

Developed for use in ethological research and behavioral studies.

Reference:
This code is written by Benoit Girard and Giuseppe Chindemi.
It is part of the publication:
.............. (2024). [Title of the paper]. [Journal Name], [Volume(Issue)], [pages]. [DOI or URL]If you use this code in your research or project, please cite the above publication.
For inquiries, please contact the corresponding author.

"""

import pandas as pd

# Preprocessing functions
def preprocess_data(data_dict):
    """
    Preprocess the prediction and ground truth data in the provided dictionary.
    
    This includes replacing NaNs and missing values with zeros, dropping non-logical columns, 
    and ensuring that prediction and ground truth matrices have matching headers.
    
    Parameters:
    data_dict (dict): A dictionary with file names as keys and tuples of prediction and ground 
                      truth matrices as values.
    
    Returns:
    tuple: A tuple containing the processed data dictionary and information about dropped columns.
    """
    # Function implementation...
    dropped_columns_info = {}
    for file_name, (pred_matrix, gt_matrix) in data_dict.items():
        pred_matrix.fillna(0, inplace=True)
        gt_matrix.fillna(0, inplace=True)
        pred_matrix, pred_dropped = drop_non_logical_columns(pred_matrix)
        gt_matrix, gt_dropped = drop_non_logical_columns(gt_matrix)
        pred_matrix, gt_matrix, header_dropped = match_headers(pred_matrix, gt_matrix)
        data_dict[file_name] = (pred_matrix, gt_matrix)
        dropped_columns_info[file_name] = {
            'pred_dropped': pred_dropped,
            'gt_dropped': gt_dropped,
            'header_dropped': header_dropped
        }
    return data_dict, dropped_columns_info

def drop_non_logical_columns(matrix):
    """
    Drop columns from the matrix that do not contain logical values (0 or 1).
    
    Parameters:
    matrix (DataFrame): The DataFrame from which to drop non-logical columns.
    
    Returns:
    tuple: A tuple containing the modified matrix and a list of dropped columns.
    """
    # Function implementation...
    dropped_columns = [col for col in matrix if not is_logical_column(matrix[col])]
    return matrix.drop(columns=dropped_columns), dropped_columns

def is_logical_column(column):
    """
    Check if a DataFrame column contains only logical values (0s and 1s).

    This function is used in the preprocessing step to ensure that the data 
    used for calculating BANOS metrics consists only of logical values.

    Parameters:
    column (Series): A pandas Series representing a column from a DataFrame.

    Returns:
    bool: True if the column contains only 0s and 1s, False otherwise.
    """
    # Function implementation...
    return column.isin([0, 1]).all()

def match_headers(pred_matrix, gt_matrix):
    """
    Match the headers of the prediction and ground truth matrices.

    This function ensures that both matrices have the same set of behavior columns
    before proceeding with the calculation of BANOS metrics.

    Parameters:
    pred_matrix (DataFrame): The DataFrame containing the predicted behaviors.
    gt_matrix (DataFrame): The DataFrame containing the ground truth behaviors.

    Returns:
    tuple: A tuple of two DataFrames (prediction and ground truth) with matching headers.
    """
    # Function implementation...
    common_headers = pred_matrix.columns.intersection(gt_matrix.columns)
    return pred_matrix[common_headers], gt_matrix[common_headers], list(set(pred_matrix.columns).symmetric_difference(gt_matrix.columns))

# Behavior identification and metrics calculation
def identify_bouts(sequence):
    """
    Identify continuous sequences (bouts) of 1s in a binary sequence.
    
    Parameters:
    sequence (list): A list of binary values representing predictions or ground truth.
    
    Returns:
    list of tuples: Each tuple contains the start and end indices of a continuous sequence (bout).
    """
    # Function implementation...
    bouts = []
    start = None
    for i, value in enumerate(sequence):
        if value == 1 and start is None:
            start = i
        elif value == 0 and start is not None:
            bouts.append((start, i - 1))
            start = None
    if start is not None:
        bouts.append((start, len(sequence) - 1))
    return bouts

def calculate_tp_fp_fn(pred_bouts, gt_bouts):
    """
    Calculate the number of true positives, false positives, and false negatives
    based on predicted and ground truth bouts.
    
    Parameters:
    pred_bouts (list of tuples): List of tuples representing predicted bouts.
    gt_bouts (list of tuples): List of tuples representing ground truth bouts.
    
    Returns:
    tuple: A tuple containing counts of true positives, false positives, and false negatives.
    """
    # Function implementation...
    true_positives = 0
    false_positives = 0
    matched_gt_bouts = set()
    for pred in pred_bouts:
        found_match = False
        for i, gt in enumerate(gt_bouts):
            if i not in matched_gt_bouts and pred[1] >= gt[0] and pred[0] <= gt[1]:
                true_positives += 1
                matched_gt_bouts.add(i)
                found_match = True
                break
        if not found_match:
            false_positives += 1
    false_negatives = len(gt_bouts) - len(matched_gt_bouts)
    return true_positives, false_positives, false_negatives

def calculate_precision_recall_f1(tp, fp, fn):
    """
    Calculate Precision, Recall, and F1 score.
    
    Parameters:
    tp (int): Count of True Positives.
    fp (int): Count of False Positives.
    fn (int): Count of False Negatives.
    
    Returns:
    tuple: A tuple containing the precision, recall, and F1 score.
    """
    # Function implementation...
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1_score = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    return precision, recall, f1_score

# Segment Overlap (SO)
def calculate_tiou(pred_bout, gt_bout):
    """
    Calculate the Temporal Intersection over Union (tIoU) for a predicted and ground truth bout.
    
    Parameters:
    pred_bout (tuple): The predicted bout as a tuple (start, end).
    gt_bout (tuple): The ground truth bout as a tuple (start, end).
    
    Returns:
    float: The tIoU score.
    """
    # Function implementation...
    intersection_start = max(pred_bout[0], gt_bout[0])
    intersection_end = min(pred_bout[1], gt_bout[1])
    intersection = max(intersection_end - intersection_start + 1, 0)
    union = (pred_bout[1] - pred_bout[0] + 1) + (gt_bout[1] - gt_bout[0] + 1) - intersection
    return intersection / union if union != 0 else 0

def calculate_so(pred_bouts, gt_bouts):
    """
    Calculate the Segment Overlap (SO) for each true positive bout.
    
    Parameters:
    pred_bouts (list of tuples): Predicted bouts.
    gt_bouts (list of tuples): Ground truth bouts.
    
    Returns:
    float: The average SO for the true positive bouts.
    """
    # Function implementation...
    tiou_scores = []
    for gt in gt_bouts:
        for pred in pred_bouts:
            if pred[1] >= gt[0] and pred[0] <= gt[1]:
                tiou_scores.append(calculate_tiou(pred, gt))
    return sum(tiou_scores) / len(tiou_scores) if tiou_scores else 0

# Temporal Precision (TP)
def calculate_tp(pred_bouts, gt_bouts):
    """
    Calculate the Temporal Precision (TP) for each true positive bout.
    
    Parameters:
    pred_bouts (list of tuples): Predicted bouts.
    gt_bouts (list of tuples): Ground truth bouts.
    
    Returns:
    float: The average TP for the true positive bouts.
    """
    # Function implementation...
    tp_scores = []
    for gt in gt_bouts:
        for pred in pred_bouts:
            if pred[1] >= gt[0] and pred[0] <= gt[1]:
                start_diff = abs(pred[0] - gt[0])
                end_diff = abs(pred[1] - gt[1])
                tp_scores.append(1 / (1 + start_diff + end_diff))
    return sum(tp_scores) / len(tp_scores) if tp_scores else 0

# Intra-bout Continuity (IC)
def count_switches_within_bout(pred_sequence, gt_start, gt_end):
    """
    Count the number of prediction switches within the span of a ground truth bout.

    This function is used in the calculation of the Intra-bout Continuity (IC) 
    and counts the changes in the predicted sequence within a ground truth bout.

    Parameters:
    pred_sequence (list): The sequence of prediction values (0s and 1s).
    gt_start (int): The start index of the ground truth bout.
    gt_end (int): The end index of the ground truth bout.

    Returns:
    int: The number of switches (changes from 0 to 1 or 1 to 0) within the bout.
    """
    # Function implementation...
    switches = 0
    for i in range(gt_start, gt_end-1):
        if pred_sequence[i] != pred_sequence[i + 1]:
            switches += 1
    return switches

def calculate_ic(pred_sequence, gt_bouts):
    """
    Calculate the Intra-bout Continuity (IC) for each ground truth bout.
    
    Parameters:
    pred_sequence (list): The sequence of predictions.
    gt_bouts (list of tuples): Ground truth bouts.
    
    Returns:
    float: The average IC for the ground truth bouts.
    """
    # Function implementation...
    ic_scores = []
    for gt in gt_bouts:
        gt_length = gt[1] - gt[0]
        switches = count_switches_within_bout(pred_sequence, gt[0], gt[1])
        if gt_length > 0:
            ic = 1 - (switches / gt_length)
        else:
            ic = 0
        ic_scores.append(ic)
    return sum(ic_scores) / len(ic_scores) if ic_scores else 0

# Compute and aggregate metrics
def compute_behavior_metrics(pred_matrix, gt_matrix):
    """
    Compute metrics for each behavior in the prediction and ground truth matrices.
    
    Parameters:
    pred_matrix (DataFrame): Predicted behaviors matrix.
    gt_matrix (DataFrame): Ground truth behaviors matrix.
    
    Returns:
    dict: A dictionary of metrics for each behavior.
    """
    # Function implementation...
    metrics = {}
    for behavior in pred_matrix.columns:
        pred_bouts = identify_bouts(pred_matrix[behavior])
        gt_bouts = identify_bouts(gt_matrix[behavior])
        tp, fp, fn = calculate_tp_fp_fn(pred_bouts, gt_bouts)
        precision, recall, f1_score = calculate_precision_recall_f1(tp, fp, fn)
        so = calculate_so(pred_bouts, gt_bouts)
        tp = calculate_tp(pred_bouts, gt_bouts)
        ic = calculate_ic(pred_matrix[behavior], gt_bouts)
        metrics[behavior] = {
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score,
            'so': so,
            'tp': tp,
            'ic': ic
        }
    return metrics

def calculate_banos_for_each_file(preprocessed_data):
    """
    Calculate the Behavior Annotation Score (BANOS) metrics for each behavior in each file.

    This function processes preprocessed prediction and ground truth data for each file 
    and computes the BANOS metrics, including DA, SO, TP, and IC for each behavior.

    Parameters:
    preprocessed_data (dict): A dictionary with file names as keys, and tuples (prediction matrix, 
                              ground truth matrix) as values.

    Returns:
    dict: A dictionary with file names as keys and computed BANOS metrics for each behavior as values.
    """
    # Function implementation...
    file_metrics = {}
    for file_name, (pred_matrix, gt_matrix) in preprocessed_data.items():
        behavior_metrics = compute_behavior_metrics(pred_matrix, gt_matrix)
        file_metrics[file_name] = behavior_metrics
    return file_metrics

def aggregate_metrics(file_metrics):
    """
    Aggregate metrics at different levels: per behavior group and overall.
    
    Parameters:
    file_metrics (dict): Metrics for each behavior in each file.
    
    Returns:
    dict: Aggregated metrics.
    """
    # Function implementation...
    group_metrics = {}
    overall_metrics = {'precision': [], 'recall': [], 'f1_score': [], 'so': [], 'tp': [], 'ic': []}
    for file, behaviors in file_metrics.items():
        for behavior, metrics in behaviors.items():
            if behavior not in group_metrics:
                group_metrics[behavior] = {key: [] for key in metrics.keys()}
            for key, value in metrics.items():
                group_metrics[behavior][key].append(value)
                overall_metrics[key].append(value)
    for behavior, metrics in group_metrics.items():
        for key in metrics.keys():
            metrics[key] = sum(metrics[key]) / len(metrics[key])
    for key in overall_metrics.keys():
        overall_metrics[key] = sum(overall_metrics[key]) / len(overall_metrics[key])
    return group_metrics, overall_metrics


