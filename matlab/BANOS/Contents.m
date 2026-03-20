% BANOS  Behavior ANnOtation Score toolbox.
% Version 0.2.0  19-Mar-2026
%
% High-level entry point (mirrors Python banos.score):
%   BANOS_score                     - Score one or multiple annotation pairs.
%
% Pipeline functions:
%   BANOSpreprocessData             - Fill NaN, drop non-binary columns, align headers.
%   BANOScalculateBANOSForEachFile  - Compute metrics for each recording.
%   BANOSaggregateMetrics           - Average metrics across recordings (nanmean).
%   BANOScomputeBehaviorMetrics     - Per-behavior metric computation for one recording.
%
% Metric functions:
%   BANOScalculateIC                - Intra-bout Continuity (IC).
%   BANOScalculateSO                - Segment Overlap / temporal IoU (SO).
%   BANOScalculateTP                - Temporal Precision of bout boundaries (TP).
%   BANOScalculatePrecisionRecallF1 - Detection Accuracy: Precision, Recall, F1 (DA).
%   BANOScalculateTpFpFn            - Bout-level true/false positive/negative counts.
%   BANOScalculateTiou              - Temporal Intersection over Union for one bout pair.
%
% Utility functions:
%   BANOSidentifyBouts              - Find continuous runs of 1s in a binary sequence.
%   BANOScountSwitchesWithinBout    - Count label transitions within a GT bout span.
%   BANOSdropNonLogicalColumns      - Remove columns that are not binary (0/1).
%   BANOSisLogicalColumn            - Test whether a column contains only 0 and 1.
%   BANOSmatchHeaders               - Retain only common behavior columns in pred and GT.
%   BANOSoverlaps                   - Test whether two bout intervals overlap.
%
% Setup:
%   setup                           - Add this toolbox to the MATLAB path.
