function [predMatrix, gtMatrix, droppedHeaders] = BANOSmatchHeaders(predMatrix, gtMatrix)
% BANOSmatchHeaders Match headers of prediction and ground truth matrices.
%   Keeps only columns whose names appear in BOTH matrices.
%   Assumes row 1 of each matrix contains header strings.
%
% Parameters:
%   predMatrix - cell array with headers in row 1, binary data in rows 2+
%   gtMatrix   - cell array with headers in row 1, binary data in rows 2+
%
% Returns:
%   predMatrix     - filtered matrix with matching columns only
%   gtMatrix       - filtered matrix with matching columns only
%   droppedHeaders - cell array of header names present in only one matrix

predHeaders = predMatrix(1, :);
gtHeaders   = gtMatrix(1, :);

commonHeaders = intersect(predHeaders, gtHeaders);

[~, predIdx] = ismember(commonHeaders, predHeaders);
[~, gtIdx]   = ismember(commonHeaders, gtHeaders);

predMatrix = predMatrix(:, predIdx);
gtMatrix   = gtMatrix(:, gtIdx);

allHeaders     = union(predHeaders, gtHeaders);
droppedHeaders = setdiff(allHeaders, commonHeaders);
end
