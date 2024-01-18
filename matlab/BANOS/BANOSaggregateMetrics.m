function [groupMetrics, overallMetrics] = BANOSaggregateMetrics(fileMetrics)
    % Aggregates metrics at different levels: per behavior group and overall.
    %
    % Arguments:
    % fileMetrics - A struct containing BANOS metrics for each behavior in each file.
    %
    % Returns:
    % groupMetrics - Aggregated metrics for each behavior group.
    % overallMetrics - Overall aggregated metrics.

    groupMetrics = struct();
    overallMetrics = struct('precision', [], 'recall', [], 'f1_score', [], 'so', [], 'tp', [], 'ic', []);
    metricFields = fieldnames(overallMetrics);

    fileNames = fieldnames(fileMetrics);
    for i = 1:length(fileNames)
        behaviors = fieldnames(fileMetrics.(fileNames{i}));
        
        for j = 1:length(behaviors)
            behavior = behaviors{j};
            for k = 1:length(metricFields)
                field = metricFields{k};
                value = fileMetrics.(fileNames{i}).(behavior).(field);
                
                if ~isfield(groupMetrics, behavior)
                    for m = 1:length(metricFields)
                        groupMetrics.(behavior).(metricFields{m}) = [];
                    end
                end
                groupMetrics.(behavior).(field)(end + 1) = value;
                overallMetrics.(field)(end + 1) = value;
            end
        end
    end

    % Calculate averages
    for j = 1:length(metricFields)
        field = metricFields{j};
        for behavior = fieldnames(groupMetrics)'
            groupMetrics.(behavior{1}).(field) = nanmean(groupMetrics.(behavior{1}).(field));
        end
        overallMetrics.(field) = nanmean(overallMetrics.(field));
    end
end