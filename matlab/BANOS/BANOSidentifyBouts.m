function bouts = BANOSidentifyBouts(sequence)
    % Identifies continuous sequences (bouts) of 1s in a binary sequence.
    %
    % Arguments:
    % sequence - A binary vector representing predictions or ground truth.
    %
    % Returns:
    % bouts - A cell array with one [start, end] row vector per bout (1-based
    %         indices, both included).

    bouts = {};
    start = NaN;
    for i = 1:length(sequence)
        if sequence(i) == 1 && isnan(start)
            start = i;
        elseif sequence(i) == 0 && ~isnan(start)
            bouts{end + 1} = [start, i - 1];
            start = NaN;
        end
    end
    if ~isnan(start)
        bouts{end + 1} = [start, length(sequence)];
    end
end