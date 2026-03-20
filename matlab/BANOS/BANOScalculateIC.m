function ic = BANOScalculateIC(predSequence, gtBouts)
    % Calculates the Intra-bout Continuity (IC) for each ground truth bout.
    %
    % IC = 1 - (switches / boutLength) averaged over all GT bouts.
    % Zero-length bouts are excluded from the average (contribute NaN).
    % Returns NaN if gtBouts is empty or all bouts are zero-length
    % (matches Python behaviour — NaN propagates through nanmean).
    %
    % Arguments:
    % predSequence - The sequence of predictions (1-based index vector).
    % gtBouts - Cell array of ground truth bouts {[start, end], ...}.
    %
    % Returns:
    % ic - The average IC across GT bouts, or NaN if undefined.

    icScores = [];
    for i = 1:length(gtBouts)
        boutLength = gtBouts{i}(2) - gtBouts{i}(1);
        switches = BANOScountSwitchesWithinBout(predSequence, gtBouts{i}(1), gtBouts{i}(2));
        if boutLength > 0
            icScores(end + 1) = 1 - (switches / boutLength);
        else
            icScores(end + 1) = NaN;  % zero-length bout: undefined, excluded from mean
        end
    end

    % nanmean excludes NaN entries from both numerator and denominator,
    % matching Python's: sum(valid) / len(valid).
    % Returns NaN when icScores is empty or all values are NaN.
    if isempty(icScores)
        ic = NaN;
    else
        ic = nanmean(icScores);
    end
end
