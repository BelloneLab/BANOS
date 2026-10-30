function [tp, tpTerms] = BANOScalculateTP(predBouts, gtBouts, varargin)
    % Calculates the Temporal Precision (TP) over the overlapping bout pairs.
    %
    % TP is the average of 1 / (1 + |start deviation| + |end deviation|)
    % over every overlapping (predicted, GT) bout pair.
    %
    % Arguments:
    % predBouts - Cell array of predicted bouts.
    % gtBouts - Cell array of ground truth bouts.
    % 'missed_bouts' - (name-value) how a GT bout that no predicted bout
    %                  overlaps is counted: 'exclude' (default) leaves it
    %                  out, 'zero' adds a term equal to 0.
    %
    % Returns:
    % tp - The average of the terms, or NaN if there is no term.
    % tpTerms - Row vector of the terms, one per overlapping pair, GT bout
    %           by GT bout, and 0 for each missed GT bout with 'zero'.

    options = BANOSparseOptions(varargin, {'missed_bouts'});
    tpTerms = [];
    for i = 1:length(gtBouts)
        found = false;
        for j = 1:length(predBouts)
            if BANOSoverlaps(predBouts{j}, gtBouts{i})
                startDiff = abs(predBouts{j}(1) - gtBouts{i}(1));
                endDiff = abs(predBouts{j}(2) - gtBouts{i}(2));
                tpTerms(end + 1) = 1 / (1 + startDiff + endDiff);
                found = true;
            end
        end
        if ~found && strcmp(options.missed_bouts, 'zero')
            tpTerms(end + 1) = 0;
        end
    end
    % Return NaN if there is no term (matches Python behaviour).
    if isempty(tpTerms)
        tp = NaN;
    else
        tp = mean(tpTerms);
    end
end
