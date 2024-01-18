function isOverlap = BANOSoverlaps(bout1, bout2)
    % Helper function to check if two bouts overlap.
    isOverlap = bout1(2) >= bout2(1) && bout1(1) <= bout2(2);
end