function varargout = BANOS_score(data, varargin)
% BANOS_score  High-level entry point for BANOS metrics (mirrors Python banos.score).
%
% SINGLE RECORDING:
%   metrics = BANOS_score(pred, gt)
%   metrics = BANOS_score(pred, gt, 'matching', 'greedy')
%
%   pred  - cell array: row 1 = behavior name strings, rows 2+ = binary data (0/1)
%   gt    - cell array: same format as pred
%   Returns a struct with per-behavior fields, each containing:
%     .precision, .recall, .f1_score, .so, .tp, .ic
%
% MULTI-RECORDING:
%   [groupMetrics, overallMetrics] = BANOS_score(dataStruct)
%   [groupMetrics, overallMetrics] = BANOS_score(dataStruct, 'matching', 'greedy')
%
%   dataStruct - struct where each field is a recording name and its value
%                is {pred_cell, gt_cell} (one pair per recording)
%   Returns groupMetrics (per-behavior average across recordings) and
%   overallMetrics (single average across all behaviors and recordings).
%
% NAME-VALUE OPTIONS:
%   'matching'      - 'greedy' (default). 'optimal' is not yet implemented in
%                     MATLAB; use the Python package for optimal matching.
%   'missed_bouts'  - how SO, TP and IC count a GT bout with no predicted
%                     frame inside it: 'exclude' (default) leaves it out of
%                     their averages, 'zero' adds a term equal to 0 to each.
%                     Precision, recall and F1 do not depend on it.
%   Option names and values are case-insensitive. An unknown name or value
%   raises an error (BANOS:unknownOption, BANOS:invalidOption).
%
% NaN VALUES:
%   A behavior with no ground-truth bouts returns NaN for all metrics.
%   NaN values are correctly excluded from group and overall averages
%   (via nanmean), so they do not bias results.
%
% EXAMPLE — single recording:
%   pred = [{'event1','event2'}; num2cell(predData)];
%   gt   = [{'event1','event2'}; num2cell(gtData)];
%   metrics = BANOS_score(pred, gt);
%   disp(metrics.event1.f1_score)
%
% EXAMPLE — multiple recordings:
%   allData.Recording_1 = {pred1, gt1};
%   allData.Recording_2 = {pred2, gt2};
%   [groupMet, overallMet] = BANOS_score(allData);
%   disp(overallMet.f1_score)
%
% See also: BANOSpreprocessData, BANOScalculateBANOSForEachFile,
%           BANOSaggregateMetrics, Contents

    % --- Parse name-value options ------------------------------------------
    % Single recording: the first cell array argument is the ground truth;
    % the remaining arguments are name-value options.
    gt = [];
    if iscell(data)
        gtIndex = find(cellfun(@iscell, varargin), 1);
        if ~isempty(gtIndex)
            gt = varargin{gtIndex};
            varargin(gtIndex) = [];
        end
    end
    options = BANOSparseOptions(varargin, {'matching', 'missed_bouts'});

    if strcmp(options.matching, 'optimal')
        error('BANOS_score: optimal matching is not yet implemented in MATLAB. Use the Python package (banos.score(..., matching=''optimal'')).');
    end

    % --- Detect single vs multi-recording mode ----------------------------
    if isstruct(data)
        % Multi-recording: data is already a properly formatted struct
        [preprocessed, ~]          = BANOSpreprocessData(data);
        fileMetrics                 = BANOScalculateBANOSForEachFile(preprocessed, ...
            'missed_bouts', options.missed_bouts);
        [groupMetrics, overallMetrics] = BANOSaggregateMetrics(fileMetrics);
        varargout{1} = groupMetrics;
        varargout{2} = overallMetrics;

    elseif iscell(data)
        % Single-recording: data = pred cell array, gt = first cell array in
        % varargin (taken out above, before the options were parsed)
        if isempty(gt)
            error('BANOS_score: single-recording mode requires two cell array arguments: BANOS_score(pred, gt).');
        end

        tmpData.single_recording = {data, gt};
        [preprocessed, ~] = BANOSpreprocessData(tmpData);
        fileMetrics       = BANOScalculateBANOSForEachFile(preprocessed, ...
            'missed_bouts', options.missed_bouts);
        varargout{1}      = fileMetrics.single_recording;

    else
        error('BANOS_score: first argument must be a cell array (single recording) or a struct (multiple recordings).');
    end
end
