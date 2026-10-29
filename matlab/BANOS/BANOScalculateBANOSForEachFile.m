function banosMetrics = BANOScalculateBANOSForEachFile(preprocessedData, varargin)
    % Calculates BANOS metrics for each behavior in each file.
    %
    % Arguments:
    % preprocessedData - A struct with preprocessed prediction and ground truth data.
    % 'missed_bouts' - (name-value) how SO, TP and IC count a GT bout that no
    %                  predicted bout overlaps: 'exclude' (default) or 'zero'
    %                  (see BANOScalculateSO).
    %
    % Returns:
    % banosMetrics - A struct containing BANOS metrics for each behavior in each file.

    options = BANOSparseOptions(varargin, {'missed_bouts'});
    fileNames = fieldnames(preprocessedData);
    banosMetrics = struct();

    for i = 1:length(fileNames)
        fileName = fileNames{i};
        extractMatrix = preprocessedData.(fileName);
        predMatrix = extractMatrix{1};
        gtMatrix = extractMatrix{2};
        behaviorMetrics = BANOScomputeBehaviorMetrics(predMatrix, gtMatrix, ...
            'missed_bouts', options.missed_bouts);
        banosMetrics.(fileName) = behaviorMetrics;
    end
end
