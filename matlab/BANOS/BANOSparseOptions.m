function options = BANOSparseOptions(args, names)
    % Reads and validates BANOS name-value options.
    %
    % Arguments:
    % args  - Cell array of name-value pairs, e.g. {'missed_bouts', 'zero'}.
    %         Names and values are case-insensitive.
    % names - Cell array of the option names the caller accepts.
    %
    % Returns:
    % options - Struct with one field per accepted name, holding the given
    %           value in lowercase, or the default value.
    %
    % Options and their values (the first value is the default):
    % 'matching'     - 'greedy', 'optimal'
    % 'missed_bouts' - 'exclude', 'zero'
    % 'aggregation'  - 'per_file', 'pooled'
    %
    % Errors:
    % BANOS:unknownOption      - a name the caller does not accept.
    % BANOS:missingOptionValue - a name without a value.
    % BANOS:invalidOption      - a value that is not allowed for its name.

    allowedValues = struct( ...
        'matching',     {{'greedy', 'optimal'}}, ...
        'missed_bouts', {{'exclude', 'zero'}}, ...
        'aggregation',  {{'per_file', 'pooled'}});

    options = struct();
    for k = 1:numel(names)
        values = allowedValues.(names{k});
        options.(names{k}) = values{1};
    end
    accepted = strjoin(strcat('''', names, ''''), ', ');

    for i = 1:2:numel(args)
        name = args{i};
        if ~(ischar(name) || (isstring(name) && isscalar(name)))
            error('BANOS:unknownOption', ...
                'Option names must be text. Accepted options: %s.', accepted);
        end
        name = lower(char(name));
        if ~any(strcmp(name, names))
            error('BANOS:unknownOption', ...
                'Unknown option ''%s''. Accepted options: %s.', name, accepted);
        end
        if i + 1 > numel(args)
            error('BANOS:missingOptionValue', 'Option ''%s'' requires a value.', name);
        end
        value = args{i + 1};
        allowed = allowedValues.(name);
        if ~(ischar(value) || (isstring(value) && isscalar(value))) ...
                || ~any(strcmpi(char(value), allowed))
            error('BANOS:invalidOption', 'Option ''%s'' must be %s.', ...
                name, strjoin(strcat('''', allowed, ''''), ' or '));
        end
        options.(name) = lower(char(value));
    end
end
