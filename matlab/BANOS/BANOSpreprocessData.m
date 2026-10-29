function [processedData, droppedColumnsInfo] = BANOSpreprocessData(dataDict)
    % Preprocesses prediction and ground truth data for BANOS computation.
    %
    % Steps performed for each file:
    %   1. Check that pred and gt have the same number of frames (rows 2+),
    %      and at least one.
    %   2. Replace NaN values with 0.
    %   3. Drop columns whose values are not strictly binary (0/1).
    %   4. Retain only behavior columns whose names appear in BOTH pred and gt.
    %
    % Errors and warnings:
    %   BANOS:lengthMismatch (error) - pred and gt differ in number of frames.
    %   BANOS:noFrame        (error) - a file has no frame.
    %   BANOS:nanReplaced    (warning) - NaN values of a column replaced by 0.
    %   BANOS:columnDropped  (warning) - a column dropped (values other than
    %                        0 and 1, or missing or invalid on the other side).
    %   Each message names the file and the column.
    %
    % Arguments:
    %   dataDict - struct; each field is a recording name whose value is
    %              {predMatrix, gtMatrix} — cell arrays where row 1 contains
    %              behavior-name strings and rows 2+ contain binary (0/1) data.
    %
    % Returns:
    %   processedData      - struct with the same fields as dataDict, containing
    %                        the cleaned {predMatrix, gtMatrix} pairs.
    %   droppedColumnsInfo - struct with 'predDropped', 'gtDropped', and
    %                        'headerDropped' fields per file.

    fileNames = fieldnames(dataDict);
    processedData      = struct();
    droppedColumnsInfo = struct();

    for i = 1:length(fileNames)
        fileName    = fileNames{i};
        extractMatrix = dataDict.(fileName);
        predMatrix  = extractMatrix{1};
        gtMatrix    = extractMatrix{2};

        % --- Check the number of frames (rows 2+) ---
        nPredFrames = max(size(predMatrix, 1) - 1, 0);
        nGtFrames   = max(size(gtMatrix, 1) - 1, 0);
        if nPredFrames ~= nGtFrames
            error('BANOS:lengthMismatch', ...
                'File ''%s'': the prediction has %d frames but the ground truth has %d.', ...
                fileName, nPredFrames, nGtFrames);
        end
        if nPredFrames == 0
            error('BANOS:noFrame', 'File ''%s'' has no frame.', fileName);
        end

        % --- Separate headers (row 1) from data (rows 2+) ---
        predHeaders = predMatrix(1, :);
        gtHeaders   = gtMatrix(1, :);
        predData    = cell2mat(predMatrix(2:end, :));
        gtData      = cell2mat(gtMatrix(2:end, :));

        % --- Replace NaNs with zeros ---
        sides = {'prediction', 'ground truth'};
        nanCounts = {sum(isnan(predData), 1), sum(isnan(gtData), 1)};
        sideHeaders = {predHeaders, gtHeaders};
        for s = 1:2
            for k = find(nanCounts{s} > 0)
                warning('BANOS:nanReplaced', ...
                    'File ''%s'': %d NaN value(s) in %s column ''%s'' replaced by 0.', ...
                    fileName, nanCounts{s}(k), sides{s}, sideHeaders{s}{k});
            end
        end
        predData(isnan(predData)) = 0;
        gtData(isnan(gtData))     = 0;

        % --- Drop non-logical columns from data, track which indices ---
        [predData, predDropped] = BANOSdropNonLogicalColumns(predData);
        [gtData,   gtDropped]   = BANOSdropNonLogicalColumns(gtData);
        sideDropped = {predDropped, gtDropped};
        for s = 1:2
            for k = sideDropped{s}
                warning('BANOS:columnDropped', ...
                    'File ''%s'': %s column ''%s'' dropped (values other than 0 and 1).', ...
                    fileName, sides{s}, sideHeaders{s}{k});
            end
        end

        % Update header arrays to reflect dropped columns
        predKeepIdx = setdiff(1:length(predHeaders), predDropped);
        gtKeepIdx   = setdiff(1:length(gtHeaders),   gtDropped);
        predHeaders = predHeaders(predKeepIdx);
        gtHeaders   = gtHeaders(gtKeepIdx);

        % --- Warn about columns present on one side only ---
        oneSide = {setdiff(predHeaders, gtHeaders, 'stable'), setdiff(gtHeaders, predHeaders, 'stable')};
        for s = 1:2
            for k = 1:numel(oneSide{s})
                warning('BANOS:columnDropped', ...
                    'File ''%s'': %s column ''%s'' dropped (missing or invalid in the %s).', ...
                    fileName, sides{s}, oneSide{s}{k}, sides{3 - s});
            end
        end

        % --- Retain only columns present in both pred and gt ---
        commonHeaders = intersect(predHeaders, gtHeaders, 'stable');
        [~, predIdx]  = ismember(commonHeaders, predHeaders);
        [~, gtIdx]    = ismember(commonHeaders, gtHeaders);

        allHeaders     = union(predHeaders, gtHeaders);
        headerDropped  = setdiff(allHeaders, commonHeaders);

        predHeaders = predHeaders(predIdx);
        gtHeaders   = gtHeaders(gtIdx);
        predData    = predData(:, predIdx);
        gtData      = gtData(:, gtIdx);

        % --- Reassemble cell arrays with headers in row 1 ---
        predMatrix = cat(1, predHeaders, num2cell(predData));
        gtMatrix   = cat(1, gtHeaders,   num2cell(gtData));

        processedData.(fileName) = {predMatrix, gtMatrix};
        droppedColumnsInfo.(fileName) = struct( ...
            'predDropped',   predDropped, ...
            'gtDropped',     gtDropped, ...
            'headerDropped', {headerDropped});
    end
end
