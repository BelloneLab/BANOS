
function [precision, recall, f1] = BANOScalculatePrecisionRecallF1(tp, fp, fn)
    % Calculates Precision, Recall, and F1 score.
    %
    % Arguments:
    % tp - Count of True Positives.
    % fp - Count of False Positives.
    % fn - Count of False Negatives.
    %
    % Returns:
    % precision - The precision score.
    % recall - The recall score.
    % f1 - The F1 score.

    precision = tp / (tp + fp);
    recall = tp / (tp + fn);
    f1 = 2 * (precision * recall) / (precision + recall);
    if isnan(precision)
        precision = 0;
    end
    if isnan(recall)
        recall = 0;
    end
    if isnan(f1)
        f1 = 0;
    end
end