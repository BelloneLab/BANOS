%% BANOS Tutorial — MATLAB
% Behavior ANnOtation Score: ethological metrics for evaluating behavior annotations.
%
% This tutorial mirrors tutorial_python.ipynb exactly.
% Two sections:
%   Section 1 — Classic BANOS usage
%   Section 2 — Frame-based F1 vs BANOS: our approach and why it differs from CalMS21
%
% Dataset: CalMS21-derived, 10 recordings,
%          behaviors: attack, investigation, mount (dropping 'other')
%
% Requirements: MATLAB R2019b+
% Run from the project root OR from the demo/ directory.

clear; clc;

% Detect project root (works whether run from root or example/)
thisDir = fileparts(mfilename('fullpath'));
if exist(fullfile(thisDir, 'matlab'), 'dir')
    projectRoot = thisDir;
else
    projectRoot = fullfile(thisDir, '..');
end

% Add BANOS toolbox to path
run(fullfile(projectRoot, 'matlab', 'BANOS', 'setup.m'));
datasetDir = fullfile(projectRoot, 'data', 'dataset_human_vs_human');

BEHAVIORS = {'attack', 'investigation', 'mount'};

fprintf('BANOS MATLAB Tutorial\n');
fprintf('=====================\n\n');

%% =========================================================================
%% SECTION 1 — Classic BANOS Usage
%% =========================================================================

fprintf('--- Section 1: Classic BANOS Usage ---\n\n');

%% 1.1 Setup — already done above (addpath, BEHAVIORS, datasetDir)

%% 1.2 Single Recording -------------------------------------------------------
% Recording_1, behaviors event1/event2/event3 (dropping 'other')
%
% v0.2.0 absent-behavior rule:
%   - GT has no bouts AND machine predicts nothing -> all metrics = 1.0 (correct absence)
%   - GT has no bouts BUT machine predicts bouts   -> all metrics = 0.0 (false detection)

recDir    = fullfile(datasetDir, 'Recording_1');
predTable = readtable(fullfile(recDir, 'humanAnnotation_2.csv'));
gtTable   = readtable(fullfile(recDir, 'humanAnnotation_1.csv'));

% Keep only event1/event2/event3
predTable = predTable(:, BEHAVIORS);
gtTable   = gtTable(:, BEHAVIORS);

fprintf('Frames: %d  |  Behaviors: %s\n', height(predTable), strjoin(BEHAVIORS, ', '));
fprintf('GT bouts per behavior:\n');
for bi = 1:numel(BEHAVIORS)
    beh = BEHAVIORS{bi};
    col = gtTable.(beh);
    diffs = diff([0; col]);
    n_bouts = sum(diffs == 1);
    fprintf('  %s: %d bouts\n', beh, n_bouts);
end
fprintf('\n');

% Convert to BANOS cell array format (row 1 = headers, rows 2+ = binary data)
predHeaders = predTable.Properties.VariableNames;
gtHeaders   = gtTable.Properties.VariableNames;
pred1 = [predHeaders; num2cell(table2array(predTable))];
gt1   = [gtHeaders;   num2cell(table2array(gtTable))];

% Score single recording
metrics = BANOS_score(pred1, gt1);

fprintf('Per-behavior metrics -- Recording 1\n');
fprintf('%-10s  %9s  %7s  %9s  %6s  %8s  %6s\n', ...
    'Behavior', 'Precision', 'Recall', 'DA (F1)', 'SO', 'TP', 'IC');
fprintf('%s\n', repmat('-', 1, 68));
for bi = 1:numel(BEHAVIORS)
    beh = BEHAVIORS{bi};
    m = metrics.(beh);
    fprintf('%-10s  %9.4f  %7.4f  %9.4f  %6.4f  %8.4f  %6.4f\n', ...
        beh, m.precision, m.recall, m.f1_score, m.so, m.tp, m.ic);
end
fprintf('\n');

%% 1.3 Multi-Recording Batch --------------------------------------------------
% Pass struct of {recName: {pred, gt}} -> [groupMetrics, overallMetrics]

fprintf('Loading 10 recordings...\n');
allData = struct();
for n = 1:10
    recName = sprintf('Recording_%d', n);
    rDir    = fullfile(datasetDir, recName);

    pTable = readtable(fullfile(rDir, 'humanAnnotation_2.csv'));
    gTable = readtable(fullfile(rDir, 'humanAnnotation_1.csv'));

    % Drop 'other', keep only the 3 behaviors
    pTable = pTable(:, BEHAVIORS);
    gTable = gTable(:, BEHAVIORS);

    pH = pTable.Properties.VariableNames;
    gH = gTable.Properties.VariableNames;
    allData.(recName) = {[pH; num2cell(table2array(pTable))], ...
                         [gH; num2cell(table2array(gTable))]};
end

[groupMetrics, overallMetrics] = BANOS_score(allData);

fprintf('\nOverall metrics -- 10 recordings (nanmean across behaviors and recordings):\n');
fprintf('  Precision : %.4f\n', overallMetrics.precision);
fprintf('  Recall    : %.4f\n', overallMetrics.recall);
fprintf('  DA (F1)   : %.4f\n', overallMetrics.f1_score);
fprintf('  SO (tIoU) : %.4f\n', overallMetrics.so);
fprintf('  TP        : %.4f\n', overallMetrics.tp);
fprintf('  IC        : %.4f\n\n', overallMetrics.ic);

%% 1.4 Metric Explanations (printed summary) ----------------------------------

fprintf('Metric explanations:\n');
fprintf('  DA (F1) : Bout-level F1 -- did the system find the right bouts?\n');
fprintf('  SO      : Temporal IoU -- how well do detected bouts overlap GT?\n');
fprintf('  TP      : Boundary precision -- are bout start/end frames accurate?\n');
fprintf('  IC      : Intra-bout continuity -- is each detected bout clean?\n\n');
fprintf('Absent-behavior rule (v0.2.0):\n');
fprintf('  GT has no bouts AND machine predicts nothing -> all metrics = 1.0 (correct absence)\n');
fprintf('  GT has no bouts BUT machine predicts bouts   -> all metrics = 0.0 (false detection)\n\n');

%% =========================================================================
%% SECTION 2 — Frame-based F1 vs BANOS:
%%             Our approach and why it differs from CalMS21
%% =========================================================================

fprintf('--- Section 2: Frame-based F1 vs BANOS ---\n\n');

%% 2a. Frame-based F1: our implementation ------------------------------------
%
% Per-recording frame F1 for each behavior, then macro-average across behaviors,
% then mean across recordings.
%
% Absent-behavior scoring (explicit, matching Python implementation):
%   GT=0 bouts and machine=0 bouts -> 1.0 (correct absence)
%   GT=0 bouts and machine has bouts -> 0.0 (false detection)
%   Otherwise: standard precision/recall/F1

recNames = fieldnames(allData);
nRec = numel(recNames);
nBeh = numel(BEHAVIORS);

perRecF1 = zeros(nRec, 1);
for ri = 1:nRec
    recName = recNames{ri};
    rDir = fullfile(datasetDir, recName);

    pTable = readtable(fullfile(rDir, 'humanAnnotation_2.csv'));
    gTable = readtable(fullfile(rDir, 'humanAnnotation_1.csv'));
    pTable = pTable(:, BEHAVIORS);
    gTable = gTable(:, BEHAVIORS);

    f1s = zeros(nBeh, 1);
    for bi = 1:nBeh
        beh = BEHAVIORS{bi};
        p = table2array(pTable(:, beh));
        g = table2array(gTable(:, beh));
        f1s(bi) = local_frame_f1(p, g);
    end
    perRecF1(ri) = mean(f1s, 'omitnan');
end

framef1_overall = mean(perRecF1, 'omitnan');
fprintf('Frame-based F1 (our approach): %.3f\n', framef1_overall);  % Expected: ~0.791

%% 2b. BANOS metrics: same recordings, same behaviors ------------------------

banos_da = overallMetrics.f1_score;
banos_so = overallMetrics.so;
banos_tp = overallMetrics.tp;
banos_ic = overallMetrics.ic;

fprintf('BANOS DA (F1): %.3f\n', banos_da);
fprintf('BANOS SO:      %.3f\n', banos_so);
fprintf('BANOS TP:      %.3f\n', banos_tp);
fprintf('BANOS IC:      %.3f\n\n', banos_ic);

%% 2c. Side-by-side comparison -----------------------------------------------

fprintf('%-20s  %7s  %s\n', 'Metric', 'Value', 'What it captures');
fprintf('%s\n', repmat('-', 1, 70));
rows = {
    'Frame-based F1',  framef1_overall, 'Frame overlap; correct absence = 1';
    'BANOS DA (F1)',   banos_da,        'Bout-level detection (did system find right bouts?)';
    'BANOS SO',        banos_so,        'Temporal quality of overlapping bouts';
    'BANOS TP',        banos_tp,        'Boundary precision';
    'BANOS IC',        banos_ic,        'Label stability within detected bouts';
};
for ri = 1:size(rows, 1)
    fprintf('%-20s  %7.3f  %s\n', rows{ri,1}, rows{ri,2}, rows{ri,3});
end
fprintf('\n');

%% 2d. Why our approach differs from CalMS21 -- and why intentionally --------

fprintf('WHY OUR APPROACH DIFFERS FROM CALMS21:\n\n');
fprintf('CalMS21 official frame-based F1 (Task 1):\n');
fprintf('  - Pool all frames from all recordings -> one global F1 per behavior\n');
fprintf('  - No explicit absent-behavior handling\n');
fprintf('    (relies on pooling -- behaviors appear somewhere in the full dataset)\n');
fprintf('  - Macro-average across 3 behaviors (attack/investigation/mount)\n\n');
fprintf('Our approach differs in two ways:\n');
fprintf('  1. Per-recording then averaged: we treat each recording equally;\n');
fprintf('     CalMS21 weights by recording length. Per-recording aggregation\n');
fprintf('     preserves recording-level variability -- scientifically meaningful\n');
fprintf('     for ethological studies.\n\n');
fprintf('  2. Explicit absent-behavior scoring: we reward correct absence (score 1)\n');
fprintf('     and penalize false detection (score 0). CalMS21 implicitly handles\n');
fprintf('     this via pooling.\n\n');
fprintf('We do NOT align with CalMS21 pooled approach because BANOS quantifies\n');
fprintf('annotation quality per recording, not globally only.\n\n');
fprintf('For publications: state both the frame F1 methodology and BANOS metrics.\n\n');

%% 2e. Thought experiment -- the shifted annotator ---------------------------

fprintf('THOUGHT EXPERIMENT -- THE SHIFTED ANNOTATOR\n');
fprintf('%s\n', repmat('-', 1, 50));
fprintf('Synthetic 100-frame example: GT has 2 bouts at frames 20-29 and 60-69.\n\n');

N = 100;

% Ground truth
gt_s = zeros(N, 1);
gt_s(21:30) = 1;  % MATLAB 1-indexed: frames 20-29 -> indices 21-30
gt_s(61:70) = 1;

% Prediction A: identical to GT
pred_a = gt_s;

% Prediction B: shifted 15 frames forward (no frame overlap)
pred_b = zeros(N, 1);
pred_b(36:45) = 1;
pred_b(76:85) = 1;

% Prediction C: shifted 2 frames (small overlap)
pred_c = zeros(N, 1);
pred_c(23:32) = 1;
pred_c(63:72) = 1;

gt_cell  = [{'beh'}; num2cell(gt_s)];
labels = {'A (identical)', 'B (shift 15f)', 'C (shift 2f)'};
preds  = {pred_a, pred_b, pred_c};

fprintf('%-15s  %8s  %8s  %6s  %6s\n', 'Prediction', 'Frame F1', 'BANOS DA', 'SO', 'TP');
fprintf('%s\n', repmat('-', 1, 52));
for pi = 1:3
    p = preds{pi};
    ff1 = local_frame_f1(p, gt_s);
    pred_cell = [{'beh'}; num2cell(p)];
    b_m = BANOS_score(pred_cell, gt_cell);
    b = b_m.beh;
    fprintf('%-15s  %8.3f  %8.3f  %6.3f  %6.3f\n', ...
        labels{pi}, ff1, b.f1_score, b.so, b.tp);
end

fprintf('\nInterpretation:\n');
fprintf('  Frame F1 collapses to 0 for a 15-frame shift -- same as completely missing.\n');
fprintf('  BANOS DA = 1.0 for all predictions (both bouts are still detected).\n');
fprintf('  BANOS TP quantifies the temporal shift: large shift -> low TP.\n');
fprintf('  BANOS SO measures fractional temporal IoU of matched bouts.\n\n');
fprintf('Frame F1 says "shifted 15f is equally wrong as missing entirely".\n');
fprintf('BANOS tells you HOW the system is wrong -- and by how much.\n\n');

fprintf('Tutorial complete!\n');


%% =========================================================================
%% Local helper: frame-level F1 with explicit absent-behavior scoring
%% =========================================================================

function f1 = local_frame_f1(pred_col, gt_col)
    % Frame-level F1 with explicit absent-behavior scoring.
    %   GT=0 bouts and machine=0 bouts -> 1.0 (correct absence)
    %   GT=0 bouts and machine has bouts -> 0.0 (false detection)
    %   Otherwise: standard precision/recall/F1.
    if sum(gt_col) == 0 && sum(pred_col) == 0
        f1 = 1.0;
        return;
    end
    if sum(gt_col) == 0 && sum(pred_col) > 0
        f1 = 0.0;
        return;
    end
    tp_f = sum(pred_col == 1 & gt_col == 1);
    fp_f = sum(pred_col == 1 & gt_col == 0);
    fn_f = sum(pred_col == 0 & gt_col == 1);
    if (tp_f + fp_f) > 0
        prec = tp_f / (tp_f + fp_f);
    else
        prec = NaN;
    end
    if (tp_f + fn_f) > 0
        rec = tp_f / (tp_f + fn_f);
    else
        rec = NaN;
    end
    if ~isnan(prec) && ~isnan(rec) && (prec + rec) > 0
        f1 = 2 * prec * rec / (prec + rec);
    else
        f1 = NaN;
    end
end
