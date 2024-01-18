function behaviorMetrics = BANOScomputeBehaviorMetrics(predMatrix, gtMatrix)
    % Computes metrics for each behavior in the prediction and ground truth matrices.
    behaviorMetrics = struct();

    for behavior = 1:size(predMatrix, 2)
        behaviorName = predMatrix{1,behavior};
        predBouts = BANOSidentifyBouts(cell2mat(predMatrix(2:end, behavior)));
        gtBouts = BANOSidentifyBouts(cell2mat(gtMatrix(2:end, behavior)));

        [tp, fp, fn] = BANOScalculateTpFpFn(predBouts, gtBouts);
        [precision, recall, f1] = BANOScalculatePrecisionRecallF1(tp, fp, fn);
        so = BANOScalculateSO(predBouts, gtBouts);
        tp = BANOScalculateTP(predBouts, gtBouts);
        ic = BANOScalculateIC(cell2mat(predMatrix(2:end, behavior)), gtBouts);

        behaviorMetrics.(behaviorName) = struct('precision', precision, 'recall', recall, 'f1_score', f1, 'so', so, 'tp', tp, 'ic', ic);
    end
end
