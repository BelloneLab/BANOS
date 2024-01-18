function [predMatrix, gtMatrix, headerDropped] = BANOSmatchHeaders(predMatrix, gtMatrix)
    % Matches the headers (columns) of the prediction and ground truth matrices.
    %
    % Arguments:
    % predMatrix - The matrix containing the predicted behaviors.
    % gtMatrix - The matrix containing the ground truth behaviors.
    %
    % Returns:
    % predMatrix - The prediction matrix with matched headers.
    % gtMatrix - The ground truth matrix with matched headers.
    % headerDropped - Indices of headers that were dropped.

    commonHeaders = intersect(1:size(predMatrix, 2), 1:size(gtMatrix, 2));
    headerDropped = setdiff(1:size(predMatrix, 2), commonHeaders);
    predMatrix = predMatrix(:, commonHeaders);
    gtMatrix = gtMatrix(:, commonHeaders);
end