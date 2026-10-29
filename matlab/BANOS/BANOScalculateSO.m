function [so, soTerms] = BANOScalculateSO(predBouts, gtBouts, varargin)
    % Calculates the Segment Overlap (SO) over the overlapping bout pairs.
    %
    % SO is the average tIoU of every overlapping (predicted, GT) bout pair.
    %
    % Arguments:
    % predBouts - Cell array of predicted bouts.
    % gtBouts - Cell array of ground truth bouts.
    % 'missed_bouts' - (name-value) how a GT bout that no predicted bout
    %                  overlaps is counted: 'exclude' (default) leaves it
    %                  out, 'zero' adds a term equal to 0.
    %
    % Returns:
    % so - The average of the terms, or NaN if there is no term.
    % soTerms - Row vector of the terms: the tIoU of each overlapping pair,
    %           GT bout by GT bout, and 0 for each missed GT bout with 'zero'.

    options = BANOSparseOptions(varargin, {'missed_bouts'});
    soTerms = [];
    for i = 1:length(gtBouts)
        found = false;
        for j = 1:length(predBouts)
            if BANOSoverlaps(predBouts{j}, gtBouts{i})
                soTerms(end + 1) = BANOScalculateTiou(predBouts{j}, gtBouts{i});
                found = true;
            end
        end
        if ~found && strcmp(options.missed_bouts, 'zero')
            soTerms(end + 1) = 0;
        end
    end
    % Return NaN if there is no term (matches Python behaviour).
    % NaN propagates correctly through BANOSaggregateMetrics (nanmean).
    if isempty(soTerms)
        so = NaN;
    else
        so = mean(soTerms);
    end
end
