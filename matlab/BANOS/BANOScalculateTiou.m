function tiou = BANOScalculateTiou(predBout, gtBout)
    % Helper function to calculate Temporal Intersection over Union (tIoU).
    intersectionStart = max(predBout(1), gtBout(1));
    intersectionEnd = min(predBout(2), gtBout(2));
    intersection = max(0, intersectionEnd - intersectionStart + 1);
    union = (predBout(2) - predBout(1) + 1) + (gtBout(2) - gtBout(1) + 1) - intersection;
    tiou = intersection / union;
end