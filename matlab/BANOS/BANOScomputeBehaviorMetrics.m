function [behaviorMetrics, behaviorComponents] = BANOScomputeBehaviorMetrics(predMatrix, gtMatrix, varargin)
    % Computes metrics for each behavior in the prediction and ground truth matrices.
    %
    % A behavior with no GT bout scores 1.0 on all six metrics if nothing is
    % predicted (correct absence) and 0.0 otherwise (false detection).
    %
    % Name-value option:
    % 'missed_bouts' - how SO, TP and IC count a GT bout that no predicted
    %                  bout overlaps: 'exclude' (default) or 'zero'
    %                  (see BANOScalculateSO).
    %
    % Returns:
    % behaviorMetrics    - Struct with one field per behavior holding .precision,
    %                      .recall, .f1_score, .so, .tp and .ic.
    % behaviorComponents - Struct with one field per behavior holding what the
    %                      metrics are computed from: the bout counts .n_tp,
    %                      .n_fp, .n_fn and the terms .so_terms, .tp_terms,
    %                      .ic_terms averaged by SO, TP and IC. Summed over
    %                      files by BANOSpoolComponents.
    options = BANOSparseOptions(varargin, {'missed_bouts'});
    behaviorMetrics = struct();
    behaviorComponents = struct();

    for behavior = 1:size(predMatrix, 2)
        behaviorName = predMatrix{1,behavior};
        predSequence = cell2mat(predMatrix(2:end, behavior));
        predBouts = BANOSidentifyBouts(predSequence);
        gtBouts = BANOSidentifyBouts(cell2mat(gtMatrix(2:end, behavior)));

        [nTp, nFp, nFn] = BANOScalculateTpFpFn(predBouts, gtBouts);
        [so, soTerms] = BANOScalculateSO(predBouts, gtBouts, 'missed_bouts', options.missed_bouts);
        [tp, tpTerms] = BANOScalculateTP(predBouts, gtBouts, 'missed_bouts', options.missed_bouts);
        [ic, icTerms] = BANOScalculateIC(predSequence, gtBouts, 'missed_bouts', options.missed_bouts);
        behaviorComponents.(behaviorName) = struct('n_tp', nTp, 'n_fp', nFp, 'n_fn', nFn, ...
            'so_terms', soTerms, 'tp_terms', tpTerms, 'ic_terms', icTerms);

        if ~isempty(gtBouts)
            [precision, recall, f1] = BANOScalculatePrecisionRecallF1(nTp, nFp, nFn);
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
