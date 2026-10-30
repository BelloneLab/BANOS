function [ic, icTerms] = BANOScalculateIC(predSequence, gtBouts, varargin)
    % Calculates the Intra-bout Continuity (IC) over the found ground truth bouts.
    %
    % IC = 1 - (switches / boutLength) averaged over the found GT bouts, where
    % boutLength = end - start is the number of frame pairs of the bout.
    % A GT bout is found when at least one of its frames is predicted (value 1).
    % One-frame bouts (boutLength = 0) are always excluded from the average.
    % Returns NaN if there is no term (matches Python behaviour — the means
    % over recordings and behaviors leave NaN out).
    %
    % Arguments:
    % predSequence - The sequence of predictions (1-based index vector).
    % gtBouts - Cell array of ground truth bouts {[start, end], ...}.
    % 'missed_bouts' - (name-value) how a missed GT bout is counted:
    %                  'exclude' (default) leaves it out, 'zero' adds a term
    %                  equal to 0.
    %
    % Returns:
    % ic - The average of the terms, or NaN if undefined.
    % icTerms - Row vector of the terms, one per found GT bout longer than
    %           one frame, and 0 for each missed one with 'zero'.

    options = BANOSparseOptions(varargin, {'missed_bouts'});
    icTerms = [];
    for i = 1:length(gtBouts)
        boutLength = gtBouts{i}(2) - gtBouts{i}(1);
        if boutLength == 0
            continue;  % zero-length bout: no frame pair, no term
        end
        if any(predSequence(gtBouts{i}(1):gtBouts{i}(2)) == 1)
            switches = BANOScountSwitchesWithinBout(predSequence, gtBouts{i}(1), gtBouts{i}(2));
            icTerms(end + 1) = 1 - (switches / boutLength);
        elseif strcmp(options.missed_bouts, 'zero')
            icTerms(end + 1) = 0;  % missed bout
        end
    end

    if isempty(icTerms)
        ic = NaN;
    else
        ic = mean(icTerms);
    end
end
