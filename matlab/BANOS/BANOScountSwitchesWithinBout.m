function switches = BANOScountSwitchesWithinBout(pred_sequence, gt_start, gt_end)
    % Count the number of prediction switches within the span of a ground truth bout.
    %
    % Parameters:
    % pred_sequence: The sequence of prediction values (0s and 1s).
    % gt_start: The start index of the ground truth bout.
    % gt_end: The end index of the ground truth bout.
    %
    % Returns:
    % The number of switches (changes from 0 to 1 or 1 to 0) within the bout.
    switches = 0;
    for i = gt_start:gt_end-1
        if pred_sequence(i) ~= pred_sequence(i + 1)
            switches = switches + 1;
        end
    end
end
