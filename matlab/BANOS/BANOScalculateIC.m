function ic = BANOScalculateIC(predSequence, gtBouts)
    % Calculates the Intra-bout Continuity (IC) for each ground truth bout.
    %
    % IC = 1 - (switches / boutLength) averaged over the found GT bouts.
    % A GT bout is found when at least one of its frames is predicted (value 1).
    % Missed bouts and zero-length bouts are excluded from the average
    % (contribute NaN).
    % Returns NaN if gtBouts is empty or no found bout is longer than zero
    % (matches Python behaviour — NaN propagates through nanmean).
    %
    % Arguments:
    % predSequence - The sequence of predictions (1-based index vector).
    % gtBouts - Cell array of ground truth bouts {[start, end], ...}.
    %
    % Returns:
    % ic - The average IC across found GT bouts, or NaN if undefined.

    icScores = [];
    for i = 1:length(gtBouts)
        boutLength = gtBouts{i}(2) - gtBouts{i}(1);
        switches = BANOScountSwitchesWithinBout(predSequence, gtBouts{i}(1), gtBouts{i}(2));
        found = any(predSequence(gtBouts{i}(1):gtBouts{i}(2)) == 1);
        if boutLength > 0 && found
            icScores(end + 1) = 1 - (switches / boutLength);
        else
            icScores(end + 1) = NaN;  % zero-length or missed bout: excluded from mean
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
