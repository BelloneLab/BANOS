function tp = BANOScalculateTP(predBouts, gtBouts)
    % Calculates the Temporal Precision (TP) for each true positive bout.
    %
    % Arguments:
    % predBouts - Cell array of predicted bouts.
    % gtBouts - Cell array of ground truth bouts.
    %
    % Returns:
    % tp - The average TP for the true positive bouts.

    tpScores = [];
    for i = 1:length(gtBouts)
        for j = 1:length(predBouts)
            if BANOSoverlaps(predBouts{j}, gtBouts{i})
                startDiff = abs(predBouts{j}(1) - gtBouts{i}(1));
                endDiff = abs(predBouts{j}(2) - gtBouts{i}(2));
                tpScores(end + 1) = 1 / (1 + startDiff + endDiff);
            end
        end
    end
    % Return NaN if no overlapping bouts were found (matches Python behaviour).
    if isempty(tpScores)
        tp = NaN;
    else
        tp = mean(tpScores);
    end
end
