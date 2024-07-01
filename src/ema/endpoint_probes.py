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


def filter_terminations_by_end(terminations, end=1):
    """Take in a list of terminations from "find_terminations" and return only those with the specified "end" value."""

    if end not in (1,2):
        raise ValueError(f'"end" argument may only be 1 or 2; {end} provided.')

    return [termination for termination in terminations if termination[2] == end]


def find_segment_endpoint_index(segment, endpoint, emin):
    """Returns mesh index of MHARNESS segment based on endpoint number (1 or 2)"""

    segment_root = segment.split('_')[0] #remove topology information if present

    if int(endpoint) == 1:
        index = 1
        return index
        
    elif int(endpoint) == 2:
        i0 = emin.find(segment_root, exact=True, separator='')
        i1 = emin.find_next(i0, '', exact=True)
        index = i1 - i0
        return index
        
    else:
        print(f'Unexpected value for segment endpoint: {end}.')
        return None


def restore_segment_topology(segment, conductor, inp):
    """Recreates full segment name with topology information for a given conductor."""

    i_start = inp.find('Section 5: CABLE SEGMENT TOPOLOGY')
    i_stop = inp.find('Section 5.1: CABLE JUNCTION TOPOLOGY')

    indices = inp.find_all(segment, i_start, i_stop, exact=True, separator=('_', ' '))
    print(f'found {len(indices)} occurrences of segment {segment}.')

    for i0 in indices:
        i1 = inp.find_next(i0, '', exact=True)

        if inp.find(conductor, start=i0+1, end=i1):
            print(f'found conductor {conductor}')
            segment = inp.get(i0).split()[0]
            break

    return segment