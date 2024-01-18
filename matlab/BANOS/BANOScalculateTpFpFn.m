function [tp, fp, fn] = BANOScalculateTpFpFn(predBouts, gtBouts)
    % Calculates the number of true positives, false positives, and false negatives.
    %
    % Arguments:
    % predBouts - Cell array of predicted bouts.
    % gtBouts - Cell array of ground truth bouts.
    %
    % Returns:
    % tp - Count of True Positives.
    % fp - Count of False Positives.
    % fn - Count of False Negatives.

    matchedGtBouts = false(size(gtBouts));
    tp = 0;
    fp = 0;
    for i = 1:length(predBouts)
        foundMatch = false;
        for j = 1:length(gtBouts)
            if ~matchedGtBouts(j) && BANOSoverlaps(predBouts{i}, gtBouts{j})
                tp = tp + 1;
                matchedGtBouts(j) = true;
                foundMatch = true;
                break;
            end
        end
        if ~foundMatch
            fp = fp + 1;
        end
    end
    fn = length(gtBouts) - sum(matchedGtBouts);
end
