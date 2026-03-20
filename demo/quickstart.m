%% BANOS Quickstart -- Score annotation files with one call.
%
% Demonstrates the high-level BANOS_score() API using the example dataset.
%
% Run from the project root:
%   matlab -batch "run('demo/quickstart.m')"
% Or open in MATLAB and click Run.

% Add BANOS to path
addpath(fullfile(fileparts(mfilename('fullpath')), '..', 'matlab', 'BANOS'));

DATASET = fullfile(fileparts(mfilename('fullpath')), '..', 'data', 'dataset_human_vs_human');


%% 1. Single recording ---------------------------------------------------

predTbl = readtable(fullfile(DATASET, 'Recording_1', 'humanAnnotation_2.csv'));
gtTbl   = readtable(fullfile(DATASET, 'Recording_1', 'humanAnnotation_1.csv'));

behaviors = {'attack', 'investigation', 'mount'};
predTbl = predTbl(:, behaviors);
gtTbl   = gtTbl(:, behaviors);

% BANOS Matlab format: row 1 = column headers, rows 2+ = binary data
pred = [predTbl.Properties.VariableNames; num2cell(table2array(predTbl))];
gt   = [gtTbl.Properties.VariableNames;   num2cell(table2array(gtTbl))];

metrics = BANOS_score(pred, gt);

fprintf('Per-behavior metrics -- Recording 1\n');
fprintf('%s\n', repmat('-', 1, 48));
behaviors = fieldnames(metrics);
for i = 1:numel(behaviors)
    beh = behaviors{i};
    m   = metrics.(beh);
    f1  = m.f1_score; so = m.so; ic = m.ic;
    fprintf('  %-12s  F1=%.3f  SO=%.3f  IC=%.3f\n', beh, f1, so, ic);
end
fprintf('\n');


%% 2. Multiple recordings ------------------------------------------------

data = struct();
for n = 1:10
    recDir   = fullfile(DATASET, sprintf('Recording_%d', n));
    predFile = fullfile(recDir, 'humanAnnotation_2.csv');
    gtFile   = fullfile(recDir, 'humanAnnotation_1.csv');
    if exist(predFile, 'file') && exist(gtFile, 'file')
        p = readtable(predFile);
        g = readtable(gtFile);
        p = p(:, behaviors);
        g = g(:, behaviors);
        recName = sprintf('Recording_%d', n);
        data.(recName) = { ...
            [p.Properties.VariableNames; num2cell(table2array(p))], ...
            [g.Properties.VariableNames; num2cell(table2array(g))]  ...
        };
    end
end

[~, overallMetrics] = BANOS_score(data);

fprintf('Overall metrics -- 10 recordings (nanmean across behaviors and recordings)\n');
fprintf('%s\n', repmat('-', 1, 48));
metricNames = fieldnames(overallMetrics);
for i = 1:numel(metricNames)
    name = metricNames{i};
    val  = overallMetrics.(name);
    if isnan(val)
        fprintf('  %-12s  NaN\n', name);
    else
        fprintf('  %-12s  %.4f\n', name, val);
    end
end
