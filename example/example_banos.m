% Example of BANOS Analysis MATLAB Script
%
% Description:
% This script processes annotation files using the Behavior Annotation Score (BANOS) Library.
% It identifies pairs of human and machine annotations, compares them, calculates BANOS metrics, 
% and visualizes the results in confusion matrices.
%
% Assumptions:
% - Annotation files should be in .csv format.
% - Each set of human and machine annotations are expected to be stored in paired files within the same folders.
% - Files should adhere to a specific format, accessible in the specified directory.
%
% Dependencies:
% - MATLAB (R2020a or later recommended).
% - BANOS function files must be in the MATLAB path or current working directory.
%
% Usage:
% 1. Run the script in MATLAB.
% 2. Input required information when prompted:
%    - Root directory for annotation files.
%    - Patterns for identifying human and machine annotation files.
%    - Header row details of the files.
% 3. The script will process the data and display results.
%
% Reference:
% This code is written by Benoit Girard and Giuseppe Chindemi.
% It is part of the publication:
% .............. (2024). [Title of the paper]. [Journal Name], [Volume(Issue)], [pages]. [DOI or URL]
% If you use this code in your research or project, please cite the above publication.
% For inquiries, please contact the corresponding author.

% User inputs
root_dir = input('Enter the root directory: ', 's');
human_pattern = input('Enter the human annotation pattern: ', 's');
machine_pattern = input('Enter the machine annotation pattern: ', 's');
header_row_name = input('Enter the number of the header row name: ');
header_row_total = input('Enter the total number of header rows: ');

% List all folders in root directory
folders = dir(root_dir);
folders = folders([folders.isdir]);
found_folders = {folders.name};
found_folders = found_folders(~ismember(found_folders, {'.', '..'}));

% Find annotation pairs
[annotation_pairs, multiple_files_folders] = find_annotation_pairs(found_folders, root_dir, human_pattern, machine_pattern, header_row_name, header_row_total);

if ~isempty(annotation_pairs)
    disp("Folder, Human Annotation File and Machine Annotation File:");
    for n = 1:length(annotation_pairs)
        fprintf('Folder: %s: Human - %s, Machine - %s\n', annotation_pairs(n).folder, annotation_pairs(n).human_annotation, annotation_pairs(n).machine_annotation);
    end
else
    disp("No matching files detected.");
end

if ~isempty(multiple_files_folders)
    disp("\nFolders with Multiple Matching Files:");
    for i = 1:length(multiple_files_folders)
        fprintf('%s\n', multiple_files_folders{i});
    end
end

% Process and display results
data_dict = prepare_matrices(annotation_pairs);

[preprocessedData, droppedInfo] = BANOSpreprocessData(data_dict);
banosMetrics = BANOScalculateBANOSForEachFile(preprocessedData);
[groupMetrics, overallMetrics] = BANOSaggregateMetrics(banosMetrics);

% Output
disp('Group Metrics:');
disp(groupMetrics);
disp('Overall Metrics:');
disp(overallMetrics);
disp('Behavior Annotation Score (BANOS) processing complete.');

% Plotting BANOS Metrics
plot_banos_metrics(groupMetrics);


function [annotation_pairs, multiple_files_folders] = find_annotation_pairs(found_folders, root_dir, human_pattern, machine_pattern, header_row_name, header_row_total)
    % Function to find annotation pairs in given directory
    annotation_pairs = struct();
    multiple_files_folders = {};

    pair_count = 0;

    for i = 1:length(found_folders)
        folder = found_folders{i};
        folder_path = fullfile(root_dir, folder);
        human_files = dir(fullfile(folder_path, ['*' human_pattern '*.csv']));
        machine_files = dir(fullfile(folder_path, ['*' machine_pattern '*.csv']));

        if length(human_files) > 1 || length(machine_files) > 1
            multiple_files_folders{end+1} = folder;
        elseif ~isempty(human_files) && ~isempty(machine_files)
            pair_count = pair_count + 1;
            annotation_pairs(pair_count).folder = folder;
            annotation_pairs(pair_count).human_annotation = fullfile(folder_path, human_files(1).name);
            annotation_pairs(pair_count).machine_annotation = fullfile(folder_path, machine_files(1).name);
            annotation_pairs(pair_count).header_row_name = header_row_name;
            annotation_pairs(pair_count).header_row_total = header_row_total;
        end
    end
end



function data_dict = prepare_matrices(annotation_pairs)
    data_dict = struct();

    for i = 1:length(annotation_pairs)
        pair = annotation_pairs(i);
        human_data = readcell(pair.human_annotation);
        machine_data = readcell(pair.machine_annotation);

        % Determine the header row and remove unnecessary rows
        human_cols = human_data(pair.header_row_name,:);
        human_data = cell2mat(human_data(pair.header_row_total+1:end, :));

        % Filter columns with binary values
        machine_cols = machine_data(pair.header_row_name,:);
        machine_data = cell2mat(machine_data(pair.header_row_total+1:end, :));

        % Initialize tables for extended data
        extended_machine_data = {};
        extended_human_data = {};
        frame_index = num2cell(1:size(human_data,1))';
        extended_machine_data = cat(1, {'frame_index'}, frame_index);
        extended_human_data = cat(1, {'frame_index'}, frame_index);

        % Create extended data frames for each pair of columns
        for m_col = 1:length(machine_cols)
            for h_col = 1:length(human_cols)
                pair_name = strcat(machine_cols{m_col}, '_vs_', human_cols{h_col});
                extended_machine_data = cat(2,extended_machine_data,cat(1,{pair_name},num2cell(machine_data(:,m_col))));
                extended_human_data = cat(2,extended_human_data,cat(1,{pair_name},num2cell(human_data(:,h_col))));
            end
        end

        % Store in data dictionary
        data_dict.(char(pair.folder)) = {extended_human_data, extended_machine_data};
    end
end

function plot_banos_metrics(groupMetrics)
    % Extract unique machine and human motif names
    metricsFields = fieldnames(groupMetrics);
    machine_motifs = unique(cellfun(@(x) x{1}, regexp(metricsFields, '_vs_', 'split'), 'UniformOutput', false));
    human_motifs = unique(cellfun(@(x) x{2}, regexp(metricsFields, '_vs_', 'split'), 'UniformOutput', false));

    % Initialize confusion matrices for each metric
    metricNames = {'precision', 'recall', 'f1_score', 'so', 'tp', 'ic'};
    metricMatrices = struct();

    for i = 1:numel(metricNames)
        metric = metricNames{i};
        metricMatrices.(metric) = zeros(numel(machine_motifs), numel(human_motifs));
    end

    % Populate the matrices
    for i = 1:numel(metricsFields)
        motifPair = metricsFields{i};
        tokens = regexp(motifPair, '_vs_', 'split');
        machine_motif = tokens{1};
        human_motif = tokens{2};

        for j = 1:numel(metricNames)
            metric = metricNames{j};
            metricMatrices.(metric)(strcmp(machine_motifs, machine_motif), strcmp(human_motifs, human_motif)) = groupMetrics.(motifPair).(metric);
        end
    end

    % Plotting
    numMetrics = numel(metricNames);
    for i = 1:numMetrics
        metric = metricNames{i};
        matrix = metricMatrices.(metric);

        figure;
        heatmap(human_motifs, machine_motifs, matrix);
        title([metric ' Confusion Matrix']);
        xlabel('Human Annotated Motifs');
        ylabel('Machine Annotated Motifs');
    end
end



