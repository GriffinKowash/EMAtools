def create_graph(inp, conductor):
    """Takes in inp file and conductor name and returns a segment-connections mapping."""
    
    graph = {}
    
    # Loop through all junctions
    for i0 in inp.find_all('!JUNCTION AND NODE', exact=True):
        i1 = inp.find_next(i0, '', exact=True)
        
        # Find connecting segments
        segments = []
        for j in inp.find_all(conductor, start=i0, end=i1, verbose=False):
            name = inp.get(j).split()[0]#.split('_')[0]
            segments.append(name)
            
        # Add neighbors to graph for each segment
        for seg in segments:
            other_segs = [s for s in segments if s != seg]
            if seg in graph:
                graph[seg] += other_segs
            else:
                graph[seg] = other_segs
                
    # Remove any duplicate connections from graph
    for segment, connections in graph.items():
        graph[segment] = list(set(connections))
                              
    return graph


def find_conductors_and_segments(inp):
    """Takes in inp file and returns dictionary of conductor-segment mappings."""
    conductors = {}

    i_segments = inp.find_all('!SEGMENT')
    
    for i0 in i_segments:
        conductors = parse_segment(inp, i0, conductors)
        
    return conductors


def parse_segment(inp, i0, conductors):
    """Accepts inp file and index of segment and populates conductor-segment dictionary."""
    
    # Find end of segment definition
    i1 = inp.find_next(i0, '', exact=True)
        
    # Check segment type
    segment_type = inp.get(i0 + 1)
    if segment_type != '!!COMPLEX':
        print(f'Unsupported segment type at line {Inp.itol(i0+1)}: "{segment_type}"')

    # Read segment name and start/end junctions
    try:
        segment, start, end = inp.get(i0 + 2).split()
    except ValueError as exc:
        print(f'Failed to unpack line {Inp.itol(i0 + 2)}: {inp.get(i0 + 2)}')

    segment = segment#.split('_')[0] #strip topology information

    # Read conductors and add segment to dictionary
    for j in range(i0 + 3, i1):
        name = inp.get(j).split()[0]
        if name in conductors:
            conductors[name].append(segment)
        else:
            conductors[name] = [segment]
            
    return conductors


def find_limb_containing(segment, limbs):
    """Checks for presence of a segment in an existing limb."""
    
    for i, limb in enumerate(limbs):
        if segment in limb:
            return i
        
    return None
    

def add_limb(new_limb, limbs, verbose=False):
    """Takes in a proposed limb and combines with existing ones if appropriate."""
    i_merge = []
    
    for segment in new_limb:
        for i, limb in enumerate(limbs):
            if segment in limb:
                i_merge.append(i)
                if verbose:
                    print(f'\t\tAdding segment(s) {new_limb} to limb {i}.')
                #else:
                #    print(f'\t*** WARNING: found additional candidate limb {i} containing segment {segment} while integrating new limb.')
        

    # Create new limb if all segments are new
    if len(i_merge) == 0:
        if verbose:
            print(f'\t\tCreating new limb from segment(s) {new_limb}.')
        limbs.append(new_limb)
        
    # Combine with existing limbs otherwise
    else:
        # Create combined list of new limb and limbs to merge
        merged = [seg for i in i_merge for seg in limbs[i]]
        new_limb += merged
        new_limb = list(set(new_limb))
        
        # Remove merged limbs
        for i in sorted(i_merge, reverse=True):
            del limbs[i]
            
        # Add new, combined limb to list
        limbs.append(new_limb)
    
    return limbs
                

def create_limbs(inp, conductor, verbose=False):
    """Takes in inp file and conductor name and groups segments into 'limbs'."""
    
    limbs = []
    
     # Loop through all junctions
    for i0 in inp.find_all('!JUNCTION AND NODE', exact=True):
        junction = inp.get(i0 + 1).split('.')[0]
        i1 = inp.find_next(i0, '', exact=True)
        
        # Find connecting segments
        segments = []
        for j in inp.find_all(conductor, start=i0, end=i1, verbose=False):
            name = inp.get(j).split()[0]#.split('_')[0]
            segments.append(name)
            
        if len(segments) == 0:
            continue
            
        # Integrate new limbs from segments around junction
        else:
            if verbose:
                print(f'\nSegments connected to Junction {junction}: {segments}.')
            
            # 1-2 segments indicates a single limb
            if len(segments) <= 2:
                if verbose:
                    print(f'\tTreating segment(s) {segments} as single limb.')
                new_limbs = [segments]
                
            # 3+ segments indicates multiple branching limbs
            else:
                if verbose:
                    print(f'\tTreating segments {segments} as separate limbs.')
                new_limbs = [[segment] for segment in segments]

            for new_limb in new_limbs:
                limbs = add_limb(new_limb, limbs, verbose)
                
            if verbose:
                print(f'\nCurrent limb structure:')
                for limb in limbs:
                    print(f'\t{limb}')
            
    return limbs


def find_limb_endpoints(limb, graph, verbose=False):
    """Finds terminating segments for a limb."""
    
    endpoints = []
    if verbose:
        print('')
    
    for segment in limb:
        connections = [connection for connection in graph[segment] if connection in limb]
        if len(connections) == 1:
            endpoints.append(segment)
            if verbose:
                print(f'Identified terminating segment {segment}.')
                
    return endpoints


def order_limb(limb, graph, verbose=False):
    """Orders segments within a limb by connectivity."""
    
    # If length is one, no need to order
    if len(limb) == 1:
        return limb
    
    limb_ordered = []
    
    # Start at arbitrary endpoint
    endpoints = find_limb_endpoints(limb, graph, verbose)
    if len(endpoints) == 0:
        print(f'\t*** WARNING: No endpoints detected for limb: {limb}.')
    active = endpoints[0]
    limb_ordered.append(active)
    if verbose:
        print(f'\nOrdering limb starting from segment {active}.')
    
    # Find next connected segment not already in ordered limb
    for i in range(len(limb) - 1):
        connected = graph[active]
        for segment in connected:
            if segment in limb and segment not in limb_ordered:
                if verbose:
                    print(f'\tConnecting {active} to {segment}.')
                limb_ordered.append(segment)
                active = segment
                break
                
    return limb_ordered


def find_segment_length(segment, emin):
    """Finds the number of mesh nodes in a given segment."""
    segment = segment.split('_')[0] #strip topology information
    
    for i in emin.find_all('!MHARNESS SEGMENT'):
        if emin.get(i + 1).split()[0] == segment:
            i0 = i + 2
            i1 = emin.find_next(i0, '', exact=True)
            return i1 - i0
        
    return None


def find_array_midpoint(array):
    """Given an array of numbers, finds the index of the entry containing the midpoint of the sum."""
    
    midpoint = sum(array) / 2
    for i in range(len(array)):
        if sum(array[:i+1]) >= midpoint:
            return i
    
    return None
    

def find_limb_midpoint(limb, emin):
    """References ordered limb against emin file and finds segment and mesh index of midpoint."""
    
    # Find number of mesh cells in each segment
    lengths = []
    for segment in limb:
        l = find_segment_length(segment, emin)
        lengths.append(l)
    
    # Find index of segment containing midpoint
    i_mid = find_array_midpoint(lengths)
    segment = limb[i_mid]
    
    # Find mesh index of midpoint on segment
    n_before = sum(lengths[:i_mid])
    n_mid = sum(lengths) // 2
    index = n_mid - n_before + 1  #mesh nodes are 1-indexed
    
    return segment, index
    

def probe_conductor_currents(conductor, inp, emin, verbose=False):
    """Places a current probe at the midpoint of each unbranching section of a conductor."""
    
    # Create a graph mapping each segment to all connected segments
    graph = create_graph(inp, conductor)

    # Create "limbs", or chains of continuously connected, unbranching segments
    limbs = create_limbs(inp, conductor, verbose)

    # Arrange limb segments in order of physical connectivity
    limbs = [order_limb(limb, graph, verbose) for limb in limbs]

    # Find midpoint mesh node for each limb
    midpoints = [find_limb_midpoint(limb, emin) for limb in limbs]
    
    # Place probes at limb midpoints
    if verbose:
        print('')
    for segment, index in midpoints:
        inp.probe_current(segment, conductor, index)
        if verbose:
            print(f'Conductor {conductor}: added current probe to segment {segment} at index {index}.')
    
    # Check input file
    if verbose:
        print('\n\n_____Displaying modified input file_____\n')
        inp.print_probes()
    

