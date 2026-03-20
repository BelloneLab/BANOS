function [processedData, droppedColumnsInfo] = BANOSpreprocessData(dataDict)
    % Preprocesses prediction and ground truth data for BANOS computation.
    %
    % Steps performed for each file:
    %   1. Replace NaN values with 0.
    %   2. Drop columns whose values are not strictly binary (0/1).
    %   3. Retain only behavior columns whose names appear in BOTH pred and gt.
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

        % --- Separate headers (row 1) from data (rows 2+) ---
        predHeaders = predMatrix(1, :);
        gtHeaders   = gtMatrix(1, :);
        predData    = cell2mat(predMatrix(2:end, :));
        gtData      = cell2mat(gtMatrix(2:end, :));

        % --- Replace NaNs with zeros ---
        predData(isnan(predData)) = 0;
        gtData(isnan(gtData))     = 0;

        % --- Drop non-logical columns from data, track which indices ---
        [predData, predDropped] = BANOSdropNonLogicalColumns(predData);
        [gtData,   gtDropped]   = BANOSdropNonLogicalColumns(gtData);

        % Update header arrays to reflect dropped columns
        predKeepIdx = setdiff(1:length(predHeaders), predDropped);
        gtKeepIdx   = setdiff(1:length(gtHeaders),   gtDropped);
        predHeaders = predHeaders(predKeepIdx);
        gtHeaders   = gtHeaders(gtKeepIdx);

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
