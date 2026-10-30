function [groupMetrics, overallMetrics] = BANOSpoolComponents(fileComponents)
    % Pools the metric components of all files and scores each behavior once.
    %
    % For each behavior, the TP, FP and FN counts are summed over the files and
    % give precision, recall and F1 (BANOScalculatePrecisionRecallF1); SO, TP
    % and IC are the means of all their terms over all files. A file without
    % the behavior adds its false bouts to FP and no SO, TP or IC term: the
    % 1.0/0.0 absent-behavior rule of the per-file metrics does not apply.
    % A behavior with no GT bout and no predicted bout in any file is NaN on
    % all six metrics.
    %
    % Arguments:
    % fileComponents - Struct with one field per file, each holding the
    %                  behavior components returned as second output by
    %                  BANOScalculateBANOSForEachFile.
    %
    % Returns:
    % groupMetrics - Pooled metrics for each behavior.
    % overallMetrics - Mean of the pooled metrics over the behaviors, NaN left
    %                  out (mean with 'omitnan').

    pooled = struct();
    fileNames = fieldnames(fileComponents);
    for i = 1:length(fileNames)
        components = fileComponents.(fileNames{i});
        behaviors = fieldnames(components);
        for j = 1:length(behaviors)
            behavior = behaviors{j};
            c = components.(behavior);
            if ~isfield(pooled, behavior)
                pooled.(behavior) = struct('n_tp', 0, 'n_fp', 0, 'n_fn', 0, ...
                    'so_terms', [], 'tp_terms', [], 'ic_terms', []);
            end
            p = pooled.(behavior);
            p.n_tp = p.n_tp + c.n_tp;
            p.n_fp = p.n_fp + c.n_fp;
            p.n_fn = p.n_fn + c.n_fn;
            p.so_terms = [p.so_terms, c.so_terms];
            p.tp_terms = [p.tp_terms, c.tp_terms];
            p.ic_terms = [p.ic_terms, c.ic_terms];
            pooled.(behavior) = p;
        end
    end

    groupMetrics = struct();
    overallMetrics = struct('precision', [], 'recall', [], 'f1_score', [], 'so', [], 'tp', [], 'ic', []);
    metricFields = fieldnames(overallMetrics);
    behaviors = fieldnames(pooled);
    for j = 1:length(behaviors)
        p = pooled.(behaviors{j});
        [precision, recall, f1] = BANOScalculatePrecisionRecallF1(p.n_tp, p.n_fp, p.n_fn);
        % Mean of each term list; NaN when a list is empty (no term)
        terms = {p.so_terms, p.tp_terms, p.ic_terms};
        termMeans = NaN(1, 3);
        for k = 1:3
            if ~isempty(terms{k})
                termMeans(k) = mean(terms{k});
            end
        end
        groupMetrics.(behaviors{j}) = struct('precision', precision, 'recall', recall, ...
            'f1_score', f1, 'so', termMeans(1), 'tp', termMeans(2), 'ic', termMeans(3));
        for k = 1:length(metricFields)
            overallMetrics.(metricFields{k})(end + 1) = groupMetrics.(behaviors{j}).(metricFields{k});
        end
    end

    for k = 1:length(metricFields)
        overallMetrics.(metricFields{k}) = mean(overallMetrics.(metricFields{k}), 'omitnan');
    end
end
