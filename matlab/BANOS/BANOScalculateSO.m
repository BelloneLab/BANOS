function so = BANOScalculateSO(predBouts, gtBouts)
    % Calculates the Segment Overlap (SO) for each true positive bout.
    %
    % Arguments:
    % predBouts - Cell array of predicted bouts.
    % gtBouts - Cell array of ground truth bouts.
    %
    % Returns:
    % so - The average SO for the true positive bouts.

    tiouScores = [];
    for i = 1:length(gtBouts)
        for j = 1:length(predBouts)
            if BANOSoverlaps(predBouts{j}, gtBouts{i})
                tiouScores(end + 1) = BANOScalculateTiou(predBouts{j}, gtBouts{i});
            end
        end
    end
    so = mean(tiouScores);
    if isnan(so)
        so = 0;
    end
end

