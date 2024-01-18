function [processedData, droppedColumnsInfo] = BANOSpreprocessData(dataDict)
    % Preprocesses the prediction and ground truth data in the provided dictionary.
    % Replaces NaNs with zeros, drops non-logical columns, and ensures matching headers.
    %
    % Arguments:
    % dataDict - A struct with file names as fields containing tuples (prediction matrix, ground truth matrix).
    %
    % Returns:
    % processedData - A struct with the processed data.
    % droppedColumnsInfo - Information about dropped columns.

    fileNames = fieldnames(dataDict);
    processedData = struct();
    droppedColumnsInfo = struct();
    
    for i = 1:length(fileNames)
        fileName = fileNames{i};
        extractMatrix = dataDict.(fileName);
        gtMatrix = extractMatrix{1};
        predMatrix = extractMatrix{2};
        gtMatrixCol = gtMatrix(1,:);
        gtMatrix = cell2mat(gtMatrix(2:end,:));
        predMatrixCol = predMatrix(1,:);
        predMatrix = cell2mat(predMatrix(2:end,:));
        
        % Replace NaNs with zeros
        predMatrix(isnan(predMatrix)) = 0;
        gtMatrix(isnan(gtMatrix)) = 0;

        % Drop non-logical columns
        [predMatrix, predDropped] = BANOSdropNonLogicalColumns(predMatrix);
        [gtMatrix, gtDropped] = BANOSdropNonLogicalColumns(gtMatrix);

        % Ensure matching headers
        [predMatrix, gtMatrix, headerDropped] = BANOSmatchHeaders(predMatrix, gtMatrix);
        idx = find([1:length(predMatrixCol)] ~= predDropped);
        predMatrix = cat(1,predMatrixCol(idx),num2cell(predMatrix));
        idx = find([1:length(gtMatrixCol)] ~= gtDropped);
        gtMatrix = cat(1,gtMatrixCol(idx),num2cell(gtMatrix));
        
        % Update processed data and dropped columns info
        processedData.(fileName) = {gtMatrix,predMatrix};
        droppedColumnsInfo.(fileName) = struct('predDropped', predDropped, 'gtDropped', gtDropped, 'headerDropped', headerDropped);
    end
end