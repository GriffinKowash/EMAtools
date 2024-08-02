import numpy as np

def create_graph(inp, conductor):
    """Takes in inp file and conductor name and returns a segment-connections mapping."""
    
    graph = {}
    
    # Loop through all junctions
    for i0 in inp.find_all('!JUNCTION AND NODE', exact=True):
        i1 = inp.find_next(i0, '', exact=True)
        
        # Find connecting segments
        segments = []
        for j in inp.find_all(conductor, start=i0, end=i1, verbose=False):
            name = inp.get(j).split()[0].split('_')[0]
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

    segment = segment.split('_')[0] #strip topology information

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
            name = inp.get(j).split()[0].split('_')[0]
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

    # Start ordering from arbitrary endpoint
    limb_ordered = []
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


def strip_topology(segments):
    """Removes topology suffix from segment names."""

    if not isinstance(segments, (list, tuple)):
        segments = [segments]

    segments = [segment.split('_')[0] for segment in segments]
    return segments


def find_cells_in_segment(segment, emin):
    """Finds the number of cells in a given segment."""
    segment = segment.split('_')[0] #strip topology information
    
    for i in emin.find_all('!MHARNESS SEGMENT'):
        if emin.get(i + 1).split()[0] == segment:
            i0 = i + 2
            i1 = emin.find_next(i0, '', exact=True)
            return i1 - i0
        
    return None


def find_array_midpoint(array):
    """Given an array of numbers, finds the index of the entry containing the floored midpoint of the sum."""
    
    midpoint = sum(array) // 2
    for i in range(len(array)):
        if sum(array[:i+1]) >= midpoint:
            return i
    
    return None


def find_terminating_node(x0, y0, z0, dir0, x1, y1, z1, dir1, mode='start'):
    """Identifies terminating node of cell (x0, y0, z0, dir0) based on neighbor."""

    # Find nodes in cells
    direction = {'X': np.array([1,0,0]), 'Y': np.array([0,1,0]), 'Z': np.array([0,0,1])}
    n00 = np.array((x0, y0, z0), dtype=np.int32)
    n01 = n00 + direction[dir0]
    n10 = np.array((x1, y1, z1), dtype=np.int32)
    n11 = n10 + direction[dir1]

    # Identify terminating node as node not shared with second cell
    term_node = None
    for test_node, other_node in zip((n00, n01), (n01, n00)):
        if np.all(test_node == n10) or np.all(test_node == n11):
            term_node = other_node
            break

    if term_node is None:
        print('!!! Could not find terminating node.')

    return term_node


def find_segment_endpoints(segment, emin):
    """Finds start/end meshes indices of an MHARNESS segment."""

    # Get start/end node and handle one-cell segments
    i_start = emin.find(segment, exact=True, separator='') + 1
    i_end = emin.find_next(i_start, '', exact=True) - 1

    if i_start == i_end:
        x0, y0, z0, dir0, _ = emin.get(i_start).split()
        start_node = np.array([x0, y0, z0], dtype=np.int32)
        direction = {'X': np.array([1,0,0]), 'Y': np.array([0,1,0]), 'Z': np.array([0,0,1])}
        end_node = start_node + direction[dir0]

    else:
        # Get first and second cells in segment and find start node
        i1 = i_start + 1
        x0, y0, z0, dir0, _ = emin.get(i_start).split()
        x1, y1, z1, dir1, _ = emin.get(i1).split()

        start_node = find_terminating_node(x0, y0, z0, dir0, x1, y1, z1, dir1)

        # Repeat to find end node
        i1 = i_end - 1
        x0, y0, z0, dir0, _ = emin.get(i_end).split()
        x1, y1, z1, dir1, _ = emin.get(i1).split()

        end_node = find_terminating_node(x0, y0, z0, dir0, x1, y1, z1, dir1)

    return start_node, end_node


def segment_connects_at_start_node(segment, neighbor, emin):
    """Determines whether the connection between a segment and a neighbor occurs at the first mesh index.
    Required to ensure that the segment midpoint is calculated correctly."""

    # Strip topology information if needed
    segment = segment.split('_')[0]
    neighbor = neighbor.split('_')[0]

    # Get first and last mesh nodes of segment and neighbor
    segment_start, segment_end = find_segment_endpoints(segment, emin)
    neighbor_start, neighbor_end = find_segment_endpoints(neighbor, emin)

    print(f'\nChecking for connection from {neighbor} to start node of {segment}')
    #print('Segment start/end:', segment_start, segment_end)
    #print('Neighbor start/end:', neighbor_start, neighbor_end)

    if np.all(segment_start == neighbor_start) or np.all(segment_start == neighbor_end):
        return True

    elif np.all(segment_end == neighbor_start) or np.all(segment_end == neighbor_end):
        return False

    else:
        print('!!! Did not find incidence with start or end node.')
        return None


def find_limb_midpoint(limb, emin, verbose=False):
    """References ordered limb against emin file and finds segment and mesh index of midpoint."""
    
    # Find number of mesh cells in each segment
    cell_counts = []
    for segment in limb:
        l = find_cells_in_segment(segment, emin)
        cell_counts.append(l)
    
    # Find index of segment containing midpoint
    i_mid = find_array_midpoint(cell_counts)
    segment = limb[i_mid]

    # Find mesh index of midpoint on segment
    n_before = sum(cell_counts[:i_mid])
    n_mid = sum(cell_counts) // 2
    
    if i_mid >= 1:
        segment_before = limb[i_mid - 1]
        if segment_connects_at_start_node(segment, segment_before, emin):
            index = n_mid - n_before #+ 1
            if verbose:
                print(f'Segment {segment} connects to {segment_before} at start point--normal behavior.')
        else:
            n_after = sum(cell_counts[:i_mid + 1])
            index = n_after - n_mid + 1
            if verbose:
                print(f'Segment {segment} connects to {segment_before} at end point--reverse behavior.')
    else:
        index = n_mid - n_before + 1
    
    return segment, index
    

def probe_conductor_currents(conductor, inp, emin, verbose=False, timestep=None, endtime=None):
    """Places a current probe at the midpoint of each unbranching section of a conductor."""
    
    # Create a graph mapping each segment to all connected segments
    graph = create_graph(inp, conductor)

    # Create "limbs", or chains of continuously connected, unbranching segments
    limbs = create_limbs(inp, conductor, verbose)

    # Arrange limb segments in order of physical connectivity
    limbs = [order_limb(limb, graph, verbose) for limb in limbs]

    # Find midpoint mesh node for each limb
    midpoints = [find_limb_midpoint(limb, emin, verbose) for limb in limbs]
    
    # Place probes at limb midpoints
    if verbose:
        print('')
    for segment, index in midpoints:
        segment = restore_segment_topology(segment, conductor, inp)
        inp.probe_current(segment, conductor, index, timestep=timestep, end=endtime)
        if verbose:
            print(f'Conductor {conductor}: added current probe to segment {segment} at index {index}.')
    
    # Check input file
    if verbose:
        print('\n\n_____Displaying modified input file_____\n')
        inp.print_probes()
    

def format_segment_name(segment, conductor):
    """Temporary function to strip topology info from segment name if the conductor being probed
    is a shield. This should ultimately be replaced by a more comprehensive and informed
    strategy for dealing with topology tags."""

    conductor_split = conductor.split('___')

    if len(conductor_split) > 1:
        if 'S' in conductor_split[-1]:
            segment = segment.split('_')[0]

    return segment


def restore_segment_topology(segment, conductor, inp):
    """Recreates full segment name with topology information for a given conductor."""

    i_start = inp.find('Section 5: CABLE SEGMENT TOPOLOGY')
    i_stop = inp.find('Section 5.1: CABLE JUNCTION TOPOLOGY')

    indices = inp.find_all(segment, i_start, i_stop, exact=True, separator=('_', ' '))
    #print(f'found {len(indices)} occurrences of segment {segment}.')

    for i0 in indices:
        i1 = inp.find_next(i0, '', exact=True)

        if inp.find(conductor, start=i0+1, end=i1):
            print(f'found conductor {conductor}')
            segment = inp.get(i0).split()[0]
            break

    return segment