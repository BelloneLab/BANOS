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
%   'aggregation'   - how the metrics are combined: 'per_file' (default)
%                     scores each recording on its own, then averages;
%                     'pooled' scores each behavior once on the bout counts
%                     and terms of all recordings (see BANOSpoolComponents).
%                     The outputs have the same form in both modes.
%   Option names and values are case-insensitive. An unknown name or value,
%   or a name without a value, raises an error (BANOS:unknownOption,
%   BANOS:invalidOption, BANOS:missingOptionValue).
%
% NaN VALUES:
%   With 'per_file', a behavior with no ground-truth bouts in a recording
%   scores 1.0 on all metrics if nothing is predicted there and 0.0
%   otherwise; groupMetrics and overallMetrics average with nanmean.
%   With 'pooled', this 1.0/0.0 rule does not apply and overallMetrics
%   averages the pooled behaviors with nanmean.
%   A metric is NaN when it is undefined: precision when nothing is
%   predicted, recall when there is no GT bout (pooled), F1 when there is no
%   bout at all (pooled), SO, TP and IC when they have no term (no overlap,
%   or no found GT bout).
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
%           BANOSaggregateMetrics, BANOSpoolComponents, Contents

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
    options = BANOSparseOptions(varargin, {'matching', 'missed_bouts', 'aggregation'});
    pooled = strcmp(options.aggregation, 'pooled');

    if strcmp(options.matching, 'optimal')
        error('BANOS_score: optimal matching is not yet implemented in MATLAB. Use the Python package (banos.score(..., matching=''optimal'')).');
    end

    % --- Detect single vs multi-recording mode ----------------------------
    if isstruct(data)
        % Multi-recording: data is already a properly formatted struct
        [preprocessed, ~]          = BANOSpreprocessData(data);
        [fileMetrics, fileComponents] = BANOScalculateBANOSForEachFile(preprocessed, ...
            'missed_bouts', options.missed_bouts);
        if pooled
            [groupMetrics, overallMetrics] = BANOSpoolComponents(fileComponents);
        else
            [groupMetrics, overallMetrics] = BANOSaggregateMetrics(fileMetrics);
        end
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
        [fileMetrics, fileComponents] = BANOScalculateBANOSForEachFile(preprocessed, ...
            'missed_bouts', options.missed_bouts);
        if pooled
            varargout{1} = BANOSpoolComponents(fileComponents);
        else
            varargout{1} = fileMetrics.single_recording;
        end

    else
        error('BANOS_score: first argument must be a cell array (single recording) or a struct (multiple recordings).');
    end
end
