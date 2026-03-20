% SETUP  Add the BANOS toolbox to the MATLAB path.
%
% Run once per MATLAB session before using any BANOS function:
%   run('path/to/matlab/BANOS/setup.m')
%
% Or add to your startup.m for automatic loading:
%   addpath(genpath('/full/path/to/matlab/BANOS'));
%
% After running setup, verify the toolbox is on the path:
%   which BANOS_score

toolboxDir = fileparts(mfilename('fullpath'));
addpath(genpath(toolboxDir));
fprintf('BANOS toolbox added to path: %s\n', toolboxDir);
