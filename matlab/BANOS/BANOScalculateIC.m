function ic = BANOScalculateIC(predSequence, gtBouts)
    % Calculates the Intra-bout Continuity (IC) for each ground truth bout.
    %
    % Arguments:
    % predSequence - The sequence of predictions.
    % gtBouts - Cell array of ground truth bouts.
    %
    % Returns:
    % ic - The average IC for the ground truth bouts.
    icScores = [];
    for i = 1:length(gtBouts)
        boutLength = gtBouts{i}(2) - gtBouts{i}(1);
        switches = BANOScountSwitchesWithinBout(predSequence, gtBouts{i}(1), gtBouts{i}(2));
        if boutLength > 0
            ic = 1 - (switches / boutLength);
        else
            ic = 0;        
        end
        icScores(end + 1) = ic;
    end
    if ~isempty(icScores)
        ic = nansum(icScores)./length(icScores);
    else
        ic = 0;
    end
    if isnan(ic)
        ic = 0;
    end
end

