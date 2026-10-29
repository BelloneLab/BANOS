function behaviorMetrics = BANOScomputeBehaviorMetrics(predMatrix, gtMatrix, varargin)
    % Computes metrics for each behavior in the prediction and ground truth matrices.
    %
    % Name-value option:
    % 'missed_bouts' - how SO, TP and IC count a GT bout that no predicted
    %                  bout overlaps: 'exclude' (default) or 'zero'
    %                  (see BANOScalculateSO).
    options = BANOSparseOptions(varargin, {'missed_bouts'});
    behaviorMetrics = struct();

    for behavior = 1:size(predMatrix, 2)
        behaviorName = predMatrix{1,behavior};
        predBouts = BANOSidentifyBouts(cell2mat(predMatrix(2:end, behavior)));
        gtBouts = BANOSidentifyBouts(cell2mat(gtMatrix(2:end, behavior)));

        if ~isempty(gtBouts)
            [tp, fp, fn] = BANOScalculateTpFpFn(predBouts, gtBouts);
            [precision, recall, f1] = BANOScalculatePrecisionRecallF1(tp, fp, fn);
            so = BANOScalculateSO(predBouts, gtBouts, 'missed_bouts', options.missed_bouts);
            tp = BANOScalculateTP(predBouts, gtBouts, 'missed_bouts', options.missed_bouts);
            ic = BANOScalculateIC(cell2mat(predMatrix(2:end, behavior)), gtBouts, ...
                'missed_bouts', options.missed_bouts);
        elseif isempty(predBouts)
            % Correct absence: system correctly detected nothing
            precision = 1.0; recall = 1.0; f1 = 1.0;
            so = 1.0; tp = 1.0; ic = 1.0;
        else
            % False detection: system predicted bouts that don't exist in GT
            precision = 0.0; recall = 0.0; f1 = 0.0;
            so = 0.0; tp = 0.0; ic = 0.0;
        end

        behaviorMetrics.(behaviorName) = struct('precision', precision, 'recall', recall, 'f1_score', f1, 'so', so, 'tp', tp, 'ic', ic);
    end
end
