<div align="center">

<p align="center">
<img src="https://gitlab.unige.ch/ben/behaviorannotationscore/-/raw/main/content/Logo_BANOS.png" width="20%">
</p>

# Behavior Annotation Score (BANOS)

[Home Page](https://gitlab.unige.ch/ben/behaviorannotationscore/-/tree/main?ref_type=heads) |
[Installation](#installation) |
[Example Usage](#example)

[![Downloads](https://static.pepy.tech/badge/cebra)](https://pepy.tech/project/cebra)
[![PyPI version](https://badge.fury.io/py/cebra.svg)](https://badge.fury.io/py/cebra)
[![View Private Cody Leaderboard on File Exchange](https://www.mathworks.com/matlabcentral/images/matlab-file-exchange.svg)](https://www.mathworks.com/matlabcentral/fileexchange/70197-private-cody-leaderboard)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

</div>


## Overview

This library is designed to calculate the Behavior Annotation Score (BANOS) for behavior annotations in video data, with implementation available in Python and Matlab.
BANOS is a set of metrics designed to evaluate algorithmic annotations against a ground truth, integrating aspects of accuracy, overlap, temporal precision, and continuity of behavior annotations segments, essential for researchers and practitioners in ethology and computer vision.

## Ethological Context and Key Concepts

### Background

In ethology (the science of animal behavior), the automatic annotation of behaviors from video data faces specific challenges for precise, contextually relevant annotations. Traditional metrics often focus on specific aspects of annotation performance, such as accuracy in a narrow sense, which may not fully encompass the ethological significance or practical applicability of an algorithm's output. There is a need for a more comprehensive metric framework that considers the diverse aspects of behavior annotation quality, providing a more complete picture of an algorithm's effectiveness in real-world scenarios.

### Introducing the Behavior Annotation Score (BANOS)

The BANOS is a set of metrics tailored for evaluating algorithmic behavior annotations against ground truths (typically human annotations), integrating multiple facets of accuracy to provide a comprehensive assessment.

## BANOS Metrics Formulas

<p align="center">
    <img src="https://gitlab.unige.ch/ben/behaviorannotationscore/-/raw/main/content/Schema_BANOS.png" width="364" height="224">
</p>

BANOS consists of the following metrics, each with specific formulas and offering disctinct perspective of an algorithm:

1. **Detection Accuracy (DA)**
   - Assess the accuracy of detecting behavioral segments with Precision, Recall and F1 score.
   - **Precision (P)**: TP/(TP+FP)
   - **Recall (R)**: TP/(TP+FN)
   - **F1 Score**: (2xPxR)/(P+R)

2. **Segment Overlap (SO)**
   - Assess the temporal overlap quality of for each annotated segment with temporal Intersection over Union (tIoU).
   - **Temporal Intersection over Union (tIoU)**: Intersection of Predicted and Ground Truth Segments/Union of Predicted and Ground Truth Segments

3. **Temporal Precision (TP)**
   - Asses the precision in predicting the start and end times of segments with the absolute differences between predicted and actual segment timings.
   - **Temporal Precision**: 1/(1 + Absolute Start Time Deviation + Absolute End Time Deviation)

4. **Intra-bout Continuity (IC)**
   - Assess the consistency of annotation within each segment by counting the number of annotation switches within a segment.
   - **Intra-bout Label Consistency**: 1 - (Number of Label Switches within Segment / Segment Length)

## Installation

Clone the repository or download the script into your project directory:

```bash
git clone https://github.com/your-repository/behavior-annotation-score.git
```

### Python Dependencies

- pandas: Install using `pip install pandas`.

### Python Dependencies

- MATLAB (No additional packages are required).

## Usage

### Python

Prepare your data as a dictionary where keys are file names, and values are tuples of prediction and ground truth DataFrames. Each DataFrame should have logical binary values with columns representing different behaviors.

#### Example

```python
# Loading data and using the library
import pandas as pd

data_dict = {
    'file1': (pd.read_csv('predictions_file1.csv'), pd.read_csv('groundtruth_file1.csv')),
    'file2': (pd.read_csv('predictions_file2.csv'), pd.read_csv('groundtruth_file2.csv')),
    # ... more files ...
}

preprocessed_data, dropped_info = preprocess_data(data_dict)
banos_metrics = calculate_banos_for_each_file(preprocessed_data)
group_metrics, overall_metrics = aggregate_metrics(banos_metrics)

print("Group Metrics:", group_metrics)
print("Overall Metrics:", overall_metrics)
```

### MATLAB

Prepare your data as a struct where fields are file names, and values are cell arrays containing two matrices: prediction and ground truth. Each matrix should have logical binary values with columns representing different behaviors.

#### Example

```matlab
% Loading data and using the library
dataDict = struct();
dataDict.file1 = {predMatrix1, gtMatrix1};
dataDict.file2 = {predMatrix2, gtMatrix2};
% ... more files ...

[preprocessedData, droppedInfo] = preprocessData(dataDict);
banosMetrics = calculateBANOSForEachFile(preprocessedData);
[groupMetrics, overallMetrics] = aggregateMetrics(banosMetrics);

fprintf('Group Metrics: %s\n', mat2str(groupMetrics));
fprintf('Overall Metrics: %s\n', mat2str(overallMetrics));

```

## Contributions and Support

For contributions or support, please open a pull request or issue in the GitHub repository.
