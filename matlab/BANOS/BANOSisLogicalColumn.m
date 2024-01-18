function isLogical = BANOSisLogicalColumn(column)
    % Checks if a matrix column contains only logical values (0s and 1s).
    %
    % Arguments:
    % column - A column from a matrix.
    %
    % Returns:
    % isLogical - True if the column contains only 0s and 1s, False otherwise.

    isLogical = all(column == 0 | column == 1);
end