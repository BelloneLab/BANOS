function [matrix, droppedColumns] = BANOSdropNonLogicalColumns(matrix)
    % Drops columns from the matrix that do not contain logical values (0 or 1).
    %
    % Arguments:
    % matrix - The matrix from which to drop non-logical columns.
    %
    % Returns:
    % matrix - The modified matrix with only logical columns.
    % droppedColumns - A list of dropped column indices.

    logicalColumnIndices = arrayfun(@(colIndex) BANOSisLogicalColumn(matrix(:, colIndex)), 1:size(matrix, 2));
    droppedColumns = find(~logicalColumnIndices);
    matrix(:, ~logicalColumnIndices) = [];
end

