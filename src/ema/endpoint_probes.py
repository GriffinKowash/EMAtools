def find_terminations(inp, conductors=None):
    """Return all terminations under "!BOUNDARY CONDITION" headers, optionally filtering by conductor name."""

    # Grab all termination definitions
    terminations = []
    indices = inp.find_all('!BOUNDARY CONDITION')
    
    for i in indices:
        if inp.get(i + 1) != '!!RESISTIVE':
            print(f'Skipping termination at line {Inp.itol(i)}; only resistive terminations are currently supported.')
            continue

        i0 = i + 2
        i1 = inp.find_next(i0, '', exact=True) - 1
        lines = inp.get(i0, i1)

        # Split into tuples of (segment, conductor, end, resistance) and add to full list
        terms = [line.split() for line in lines]
        terminations.extend(terms)
        
    # Filter by conductors, if specified
    if conductors is not None:
        if isinstance(conductors, str):
            conductors = [conductors]
        terminations = [(seg, cond, end, res) for seg, cond, end, res in terminations if cond in conductors]
        
    return terminations


def find_segment_endpoint_index(segment, endpoint, emin):
    """Returns mesh index of MHARNESS segment based on endpoint number (1 or 2)"""

    segment_root = segment.split('_')[0] #remove topology information if present

    if int(endpoint) == 1:
        index = 1
        return index
        
    elif int(endpoint) == 2:
        i0 = emin.find(segment_root, exact=True, separator='') + 1
        i1 = emin.find_next(i0, '', exact=True)
        index = i1 - i0
        return index
        
    else:
        print(f'Unexpected value for segment endpoint: {end}.')
        return None