function banosMetrics = BANOScalculateBANOSForEachFile(preprocessedData)
    % Calculates BANOS metrics for each behavior in each file.
    %
    % Arguments:
    % preprocessedData - A struct with preprocessed prediction and ground truth data.
    %
    % Returns:
    % banosMetrics - A struct containing BANOS metrics for each behavior in each file.

    fileNames = fieldnames(preprocessedData);
    banosMetrics = struct();

    for i = 1:length(fileNames)
        fileName = fileNames{i};
        extractMatrix = preprocessedData.(fileName);
        predMatrix = extractMatrix{1};
        gtMatrix = extractMatrix{2};
        behaviorMetrics = BANOScomputeBehaviorMetrics(predMatrix, gtMatrix);
        banosMetrics.(fileName) = behaviorMetrics;
    end
end
