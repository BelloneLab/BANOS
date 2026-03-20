%% generate_matlab_fixtures.m
% Generates a single JSON reference file from the Matlab BANOS implementation,
% containing all 10 recordings in the same structure as golden_python_current.json.
%
% Output: tests/fixtures/golden_matlab_v020.json
%
% Run from the project root using any of:
%   matlab -batch "run('tests/fixtures/matlab/generate_matlab_fixtures.m')"
%   OR open in VS Code Matlab extension and click Run.

% Add BANOS Matlab functions to path
scriptDir = fileparts(mfilename('fullpath'));
addpath(fullfile(scriptDir, '..', '..', '..', 'matlab', 'BANOS'));

datasetDir = fullfile(scriptDir, '..', '..', '..', 'data', 'dataset_human_vs_human');
outFile    = fullfile(scriptDir, '..', 'golden_matlab_v020.json');

fprintf('Generating Matlab BANOS fixtures...\n');
fprintf('Dataset dir: %s\n', datasetDir);
fprintf('Output:      %s\n\n', outFile);

allResults = struct();

for n = 1:10
    recName = sprintf('Recording_%d', n);
    recDir  = fullfile(datasetDir, recName);

    predFile = fullfile(recDir, 'humanAnnotation_2.csv');
    gtFile   = fullfile(recDir, 'humanAnnotation_1.csv');

    if ~exist(predFile, 'file')
        fprintf('WARNING: %s not found, skipping\n', predFile);
        continue;
    end
    if ~exist(gtFile, 'file')
        fprintf('WARNING: GT file not found for %s, skipping\n', recName);
        continue;
    end

    % Load CSVs as tables, then convert to BANOS cell array format
    predTable = readtable(predFile);
    gtTable   = readtable(gtFile);

    predHeaders = predTable.Properties.VariableNames;
    gtHeaders   = gtTable.Properties.VariableNames;

    % BANOS Matlab format: row 1 = headers (strings), rows 2+ = binary data (numeric)
    predMatrix = [predHeaders; num2cell(table2array(predTable))];
    gtMatrix   = [gtHeaders;   num2cell(table2array(gtTable))];

    % Process this recording ALONE (critical: each recording processed independently)
    singleData.(recName) = {predMatrix, gtMatrix};

    [preprocessed, ~]  = BANOSpreprocessData(singleData);
    [fileMetrics]       = BANOScalculateBANOSForEachFile(preprocessed);
    [groupMetrics, overallMetrics] = BANOSaggregateMetrics(fileMetrics);

    % Store in combined result struct
    allResults.(recName).file_metrics    = fileMetrics.(recName);
    allResults.(recName).group_metrics   = groupMetrics;
    allResults.(recName).overall_metrics = overallMetrics;

    fprintf('Processed %s  (F1=%.4f, SO=%.4f, IC=%.4f)\n', ...
        recName, overallMetrics.f1_score, overallMetrics.so, overallMetrics.ic);

    % Reset for next recording
    clear singleData;
end

% Save all recordings as a single JSON (matches golden_python_current.json structure)
fid = fopen(outFile, 'w');
if fid == -1
    error('Cannot open output file: %s', outFile);
end
fprintf(fid, '%s', jsonencode(allResults));
fclose(fid);

fprintf('\nDone! Saved to: %s\n', outFile);
