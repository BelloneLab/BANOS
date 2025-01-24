function [precision, recall, f1] = BANOScalculatePrecisionRecallF1(tp, fp, fn)
    % Calculates Precision, Recall, and F1 score at the bout level.
    %
    % Returns NaN (not 0) when the denominator is zero, matching Python behaviour.
    % NaN values propagate correctly through BANOSaggregateMetrics (nanmean).
    %
    % Arguments:
    % tp - Count of True Positives (matched bout pairs).
    % fp - Count of False Positives (predicted bouts with no GT match).
    % fn - Count of False Negatives (GT bouts with no pred match).
    %
    % Returns:
    % precision - TP / (TP + FP), or NaN if TP + FP = 0.
    % recall    - TP / (TP + FN), or NaN if TP + FN = 0.
    % f1        - Harmonic mean of precision and recall, or NaN if undefined.

    if (tp + fp) > 0
        precision = tp / (tp + fp);
    else
        precision = NaN;
    end

    if (tp + fn) > 0
        recall = tp / (tp + fn);
    else
        recall = NaN;
    end

    if ~isnan(precision) && ~isnan(recall) && (precision + recall) > 0
        f1 = 2 * precision * recall / (precision + recall);
    else
        f1 = NaN;
    end
end
