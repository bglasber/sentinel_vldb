import psycopg2 # type: ignore
import graphviz # type: ignore
import random
import numpy as np # type: ignore
import pyemd # type: ignore
import multiprocessing
import glob 
import pickle
import scipy.stats # type: ignore

from typing import List, Dict, Tuple, Set, Any, Iterable
from colorama import Fore, Style # type: ignore

class FileLocation:
    """A location in a file for a given event (filename,line_number)"""
    def __init__( self, fname: str, line_number: int ):
        self.fname = fname
        self.line_number = line_number
    def __repr__( self ) -> str:
        return "{}:{}".format( self.fname, self.line_number )
    def __eq__( self, obj ) -> bool:
        return isinstance( obj, FileLocation ) and self.line_number == obj.line_number and self.fname == obj.fname
    def __ne__( self, obj ) -> bool:
        return not self == obj
    def __hash__( self ) -> int:
        return hash( (self.fname, self.line_number) )

class EventRecord:
    def __init__( self, fname: str , ln: int, prob: float  ):
        self.event_loc = FileLocation( fname, ln )
        self.prob =  prob

    def get_id( self ):
        return self.event_loc.__repr__()
    def __repr__(self):
        return "<{}, Prob: {}>".format(self.get_id(), self.prob)

class TransitionRecord:
    """ A transition record between markov nodes. node == dest."""
    def __init__( self, dst: 'MarkovNode', prob: float, transition_time_cdf: List[Tuple[float,float]] ):
        self.dst = dst
        self.prob = prob
        self.transition_time_cdf = transition_time_cdf
        self.good_path = False
    def is_good_path( self ) -> bool:
        return self.good_path
    def set_good_path( self ):
        self.good_path = True
    def set_bad_path( self):
        self.good_path = False

class MarkovNode:
    """A Node in a MarkovGraph"""
    def __init__( self, node_id: int, fname: str, line: int ):
        self.node_id = node_id
        self.transitions = [] # type: List[TransitionRecord]
        self.event_loc = FileLocation( fname, line )
    
    def add_transition( self, dst: 'MarkovNode', prob: float, transition_time_cdf: List[Tuple[float,float]]):
        """ Add a transition from this node to dst with probability prob and transition_time_cdf"""
        tr = TransitionRecord( dst, prob, transition_time_cdf )
        self.transitions.append( tr )

    def get_transition( self, dst_name: str, dst_line: int ) -> 'MarkovNode':
        for transition in self.transitions:
            if transition.dst.event_loc.fname == dst_name and transition.dst.event_loc.line_number == dst_line:
                return transition.dst
        raise KeyError( "No such transition found: {}:{} from {}:{}".format( dst_name, dst_line, self.event_loc.fname, self.event_loc.line_number ) )
    
    def sample_transition_time( self, dst: 'MarkovNode' ) -> float:
        """ Sample a transition time from the current node to dst"""
        for tr in self.transitions:
            if dst != tr.dst:
                continue
            cdf_draw = random.random()
            if not tr.transition_time_cdf:
                print( "Unknown Transition!")
                return 0.0
            for pctl, val in tr.transition_time_cdf:
                if cdf_draw <= pctl:
                    return val
            return tr.transition_time_cdf[-1][1]
        raise KeyError( "Could not find transition for dst: {}".format( dst ) )
    
    def __str__( self ):
        return "MarkovNode-{}".format( self.node_id )
    
    def __repr__( self ):
        return "MarkovNode-{}".format( self.node_id )

    def get_key( self ):
        return self.event_loc.__repr__()
    
class MarkovGraph:
    """A graph of MarkovNodes"""
    def __init__( self, nodes: List[MarkovNode] ):
        self.node_map = {}
        for node in nodes:
            self.node_map[node.get_key()] = node
    def get_node( self, fname, line ) -> MarkovNode:
        return self.node_map[ FileLocation( fname, line ).__repr__() ]
    def __repr__( self ):
        return str(self.node_map)

def get_log_transitions( pg_conn, src_fname: str, src_line: int, run_id: int ) -> List[Tuple[str,int,float]]:
    """Get the transitions from event src_fname:src_line in run_id using the provided postgres connection"""
    cur = pg_conn.cursor()
    get_transition_probs_query = "SELECT log_next_fname, log_next_line, transition_probability FROM log_line_transitions WHERE log_initial_fname = %s AND log_initial_line = %s AND run_id = %s"

    cur.execute( get_transition_probs_query, ( src_fname, src_line, run_id ) )
    results = cur.fetchall()
    cur.close()
    return results

def get_log_transition_time( pg_conn, src_fname: str, src_line: int, dst_fname: str, dst_line: int, run_id: int ):
    """Get the transition times from event src_fname:src_line to dst_fname:dst_line in run_id using the provided postgres connection"""
    cur = pg_conn.cursor()
    get_cdf_query = "SELECT percentiles, percentile_values FROM transition_cdfs WHERE src_fname = %s and src_line = %s AND dst_fname = %s and dst_line = %s and run_id = %s"
    
    cur.execute( get_cdf_query, ( src_fname, src_line, dst_fname, dst_line, run_id ) )
    results = cur.fetchall()
    cur.close()
    return results

def build_full_markov_graph( pg_conn, run_id: int ) -> MarkovGraph:
    """ Build a markov graph for run_id using the provided postgres connection"""
    get_all_nodes_query = """SELECT log_initial_fname, log_initial_line FROM log_line_transitions WHERE run_id = %s UNION SELECT log_next_fname, log_next_line FROM log_line_transitions WHERE run_id = %s"""
    
    nodes = [] # type: List[MarkovNode]
    cur = pg_conn.cursor()
    cur.execute( get_all_nodes_query, ( run_id, run_id ) )
    data = cur.fetchall() # type: List[Tuple[str,int]]
    cur.close()
    for entry in data:
        node = MarkovNode( hash(entry[0]) ^ hash(entry[1]), entry[0], entry[1] )
        nodes.append( node )
    
    for node in nodes:
        src_fname = node.event_loc.fname
        src_line = node.event_loc.line_number
        transitions = get_log_transitions( pg_conn, src_fname, src_line, run_id )
        for dst_name, dst_line, dst_prob in transitions:
            dst_node = node.get_transition( dst_name, dst_line )
            cdf_data = get_log_transition_time( pg_conn, node.event_loc.fname, node.event_loc.line_number, dst_node.event_loc.fname, dst_node.event_loc.line_number, run_id )
            if len(cdf_data) < 1:
                raise KeyError( "No transition for: {}:{} -> {}:{}".format( node.event_loc.fname, node.event_loc.line_number, dst_node.event_loc.fname, dst_node.event_loc.line_number) )
            else:
                cdf_data= cdf_data[0]
                node.add_transition( dst_node, dst_prob, list(zip(cdf_data[0],cdf_data[1])) )
            
    return MarkovGraph(nodes)

def bounded_dfs( node: MarkovNode, goal_nodes: List[MarkovNode], cur_prob=1., cut_off=1E-5, nodes_seen_so_far=[], allow_loops=True ) -> bool:

    if node in goal_nodes:
        return True
    
    if not allow_loops and node in nodes_seen_so_far:
        return False
    
    is_good_path = False
    
    for transition in node.transitions:
        
        next_prob = cur_prob * transition.prob
        if next_prob >= cut_off:
            result = bounded_dfs( transition.dst, goal_nodes, next_prob, cut_off, nodes_seen_so_far + [ node ], allow_loops )
            if result:
                # Mark the transition as a known good transition
                is_good_path = True
                transition.set_good_path()
            else:
                transition.set_bad_path()
    return is_good_path


def get_transition_node( valid_transitions: List[TransitionRecord] ) -> MarkovNode:
    """Given a set of valid transitions, determine which transition we will walk next
    according to their normalized probabilities."""
    prob = random.random()
    normalization_factor = 0.0
    for transition in valid_transitions:
        normalization_factor += transition.prob

    assert( normalization_factor <= 1.1 ) # to handle floating point error

    for transition in valid_transitions:
        adj_prob = transition.prob / normalization_factor
        if prob <= adj_prob:
            return transition.dst
        prob -= adj_prob
    raise ArithmeticError( "Ran out of normalized transition probabilities to walk! Normalization error?" )

def bounded_random_walk( start_node: MarkovNode, terminal_nodes: List[MarkovNode], num_walks=1.E6 ) -> Tuple[Dict[MarkovNode,int],Dict[MarkovNode,List[float]]]:
    """ Conduct num_walks bound random walks from the start_node to one of the terminal_nodes. Normalizes probabilities
    by pruning away paths that do not reach terminal nodes. Returns a tuple where the first item is a dictionary of the number times we've hit the terminal
    nodes and a dictionary representing the elapsed durations of how long it took to hit those terminal nodes (determined by MCMC)"""

    # Mark up the transitions so we have "railings" and know where we can go during our walk
    bounded_dfs( start_node, terminal_nodes, allow_loops=False )
    
    cur_walk = 0
    terminal_node_count = {} # type: Dict[MarkovNode, int]
    node_elapsed_times = {} # type: Dict[MarkovNode, List[float]]
    for tn in terminal_nodes:
        terminal_node_count[tn] = 0
        node_elapsed_times[tn] = []
        
    while cur_walk < num_walks:
        cur_node = start_node
        elapsed_ms = 0.
        while True:
            # TODO: prune this run out if the probably goes below a certain threshold --- its effectively zero
            # so might as well shortcut the results.
            # Problem is if the thing we prune out is a massive heavy hitter on run_time --- could inflate average!
            if cur_node in terminal_nodes:
                cur_walk += 1
                terminal_node_count[cur_node] += 1
                node_elapsed_times[cur_node].append( elapsed_ms )
                break
            # Get all the transitions we can take out of here
            valid_transitions = [ transition for transition in cur_node.transitions if transition.is_good_path() ]
            
            next_node = get_transition_node( valid_transitions )
            
            sampled_transition_time = cur_node.sample_transition_time( next_node )
            elapsed_ms += sampled_transition_time
            cur_node = next_node
            
    return terminal_node_count, node_elapsed_times

def depth_bounded_mcmc( start_node: MarkovNode, target_depth: int ) -> Tuple[Dict[MarkovNode, int], Dict[MarkovNode, List[float]]]:
    """Do bounded random walks MCMC with terminal nodes equal to the set of all possible nodes at depth k.
    If these nodes are also available at a higher depth, may terminate earlier (e.g. loops)"""
    def get_terminal_nodes_at_k_depth( cur_node: MarkovNode, nodes, cur_depth, target_depth ):
        if cur_depth == target_depth:
            nodes.add( cur_node )
            return
        next_nodes = [ t.dst for t in cur_node.transitions ] # type: List[MarkovNode]
        for nn in next_nodes:
            get_terminal_nodes_at_k_depth( nn, nodes, cur_depth+1, target_depth )

    nodes = set() # type: Set[MarkovNode]
    cur_depth = 0
    get_terminal_nodes_at_k_depth( start_node, nodes, 0, target_depth )
    counts, elapsed_time = bounded_random_walk( start_node, list(nodes) )
    return counts, elapsed_time
    
def compute_percentiles_from_mcmc_results( timer_results: Dict[MarkovNode, List[float]] ) -> Dict[MarkovNode, List[float]]:
    """ Compute percentiles from a dictionary of terminal nodes to elapsed times"""
    percentiles = np.arange( 5,100, 5 )
    percentile_results = {} # type: Dict[MarkovNode, List[float]]
    for node, times in timer_results.items():
        times_array = np.array( times )
        percentile_results[ node ] = np.percentile( times_array, percentiles )
    return percentile_results

def get_data_from_postgres( conn, run_id ) -> Tuple[Dict[str,EventRecord], Dict[str,Dict[str,float]]]:
    sql_stmt = "SELECT log_fname, log_line, log_probability FROM log_line_probabilities WHERE run_id = %s"
    cur = conn.cursor()
    cur.execute( sql_stmt, (run_id,) )
    rs = cur.fetchall()
    events = {} # type: Dict[str, EventRecord]
    for row in rs:
        fname, ln, count = row
        event = EventRecord( fname, ln, count )
        events[event.get_id()] = event
        
    sql_stmt = "SELECT log_initial_fname,log_initial_line, log_next_fname, log_next_line, transition_probability FROM log_line_transitions WHERE run_id = %s"
    cur = conn.cursor()
    cur.execute( sql_stmt, (run_id,) )
    rs = cur.fetchall()
    event_transitions = {} # type: Dict[str,Dict[str,float]]
    for row in rs:
        initial_fname, initial_line, next_fname, next_line, prob = row
        from_event_id = "{}:{}".format( initial_fname, initial_line )
        to_event_id = "{}:{}".format( next_fname, next_line )
        if not from_event_id in event_transitions:
            event_transitions[from_event_id] = {}
        event_transitions[from_event_id][to_event_id] = prob

    return events, event_transitions

class ProbDiffRecord:
    def __init__( self, diff_val: float, left_val: float, right_val: float, event_fname: str, event_line: int, is_left_greater: bool ):
        self.diff = diff_val
        self.left_val = left_val
        self.right_val = right_val
        self.event_fname = event_fname
        self.event_line = event_line
        self.is_left_greater = is_left_greater

class TransitionDiffRecord:
    def __init__( self, diff_val: float, left_val: float, right_val: float, src_fname: str, src_line: int, dst_fname: str, dst_line: int, is_left_greater: bool ):
        self.diff = diff_val
        self.left_val = left_val
        self.right_val = right_val
        self.src_fname = src_fname
        self.src_line = src_line
        self.dst_fname = dst_fname
        self.dst_line = dst_line
        self.is_left_greater = is_left_greater

def create_prob_diff_record( diff, left, right, event_fname, event_line, is_left_greater) -> ProbDiffRecord:
    pdr = ProbDiffRecord( diff, left, right, event_fname, event_line, is_left_greater )
    return pdr

def create_transition_diff_record( diff, left, right, event_1_fname, event_1_line, event_2_fname, event_2_line, is_left_greater ) -> TransitionDiffRecord:
    tdr = TransitionDiffRecord( diff, left, right, event_1_fname, event_1_line, event_2_fname, event_2_line, is_left_greater )
    return tdr

def do_calc_prob_diff( k: Any, events_1: Dict[Any, EventRecord], events_2: Dict[Any, EventRecord] ) -> ProbDiffRecord:
    
    # Compute the event probabilities for both runs
    event1_prob = 0.0
    event2_prob = 0.0
    event_fname = None
    event_ln = None
    if k in events_1:
        event1_prob = events_1[k].prob
        event_fname = events_1[k].event_loc.fname
        event_ln = events_1[k].event_loc.line_number
    if k in events_2:
        event2_prob = events_2[k].prob
        event_fname = events_2[k].event_loc.fname
        event_ln = events_2[k].event_loc.line_number
    
    min_prob = min( event1_prob, event2_prob )
    max_prob = max(event1_prob, event2_prob)
    is_left_greater = True if event1_prob > event2_prob else False

    # If both sides are greater than zero, it is straightforward to calculate the difference b/c there
    # are no divisions by zero.
    if min_prob > 0:
        ratio_diff = max_prob / min_prob
        return create_prob_diff_record( ratio_diff, event1_prob, event2_prob, event_fname, event_ln, is_left_greater)
    else:
        #ratio_diff = float("Inf")
        ratio_diff = 1.0
        return create_prob_diff_record( ratio_diff, event1_prob, event2_prob, event_fname, event_ln, is_left_greater)

def compute_prob_diff( events_1: Dict[Any, EventRecord], events_2: Dict[Any, EventRecord] ) -> List[ProbDiffRecord]:
    prob_diffs = [] # type: List[ProbDiffRecord]
    for k in set(events_1.keys()).union(events_2.keys()):
        p_diff = do_calc_prob_diff( k, events_1, events_2)
        prob_diffs.append( p_diff )
    prob_diffs.sort(key=lambda diff_record: diff_record.diff, reverse=True)
    return prob_diffs

def compute_transition_diff( events_1: Dict[int, EventRecord], events_2: Dict[int, EventRecord], event_transitions1: Dict[int, Dict[int, float]], event_transitions2: Dict[int, Dict[int,float]] ) -> Tuple[float, List[TransitionDiffRecord], List[TransitionDiffRecord]]:
    agg_score = 0.
    score_diffs = []
    raw_transition_diffs = []
    for k in set(events_1).union(events_2):
        for k2 in set(events_1).union(events_2):
            events_1_prob = 0.0
            events_1_trans_prob = 0.0
            events_2_prob = 0.0
            events_2_trans_prob = 0.0
            if k in events_1:
                events_1_prob = events_1[k].prob
                if k in event_transitions1 and k2 in event_transitions1[k]:
                    events_1_trans_prob = event_transitions1[k][k2]
            if k in events_2:
                events_2_prob = events_2[k].prob
                if k in event_transitions2 and k2 in event_transitions2[k]:
                    events_2_trans_prob = event_transitions2[k][k2]
            events_1_score = events_1_prob * events_1_trans_prob
            events_2_score = events_2_prob * events_2_trans_prob
            is_left_greater = True if events_1_score > events_2_score else False
            difference = (events_1_score - events_2_score) ** 2
            agg_score += difference
            min_score = min(events_1_score, events_2_score)
            max_score = max(events_1_score, events_2_score)
            min_transition_score = min(events_1_trans_prob, events_2_trans_prob)
            max_transition_score = max(events_1_trans_prob, events_2_trans_prob)
            if min_score == 0.0:
                ratio_diff = float('Inf')
            else:
                ratio_diff = max_score / min_score
            if min_transition_score == 0.0:
                trans_ratio_diff = float('Inf')
            else:
                trans_ratio_diff = max_transition_score / min_transition_score
            
            fname_1 = events_1[k].event_loc.fname if k in events_1 else events_2[k].event_loc.fname
            line_1 = events_1[k].event_loc.line_number if k in events_1 else events_2[k].event_loc.line_number
            fname_2 = events_1[k2].event_loc.fname if k2 in events_1 else events_2[k2].event_loc.fname
            line_2 = events_1[k2].event_loc.line_number if k2 in events_1 else events_2[k2].event_loc.line_number
            
            score_diffs.append( create_transition_diff_record( ratio_diff, events_1_score, events_2_score, fname_1, line_1,
                                                              fname_2, line_2, is_left_greater ) )
            raw_transition_diffs.append( create_transition_diff_record( trans_ratio_diff, events_1_trans_prob, events_2_trans_prob,
                                                                       fname_1, line_1, fname_2, line_2, is_left_greater ))
    score_diffs.sort(key=lambda diff_record: diff_record.diff, reverse=True)
    raw_transition_diffs.sort(key=lambda diff_record: diff_record.diff, reverse=True)
    return agg_score, score_diffs, raw_transition_diffs
                
def compute_difference( events_1: Dict[int, EventRecord], event_t_1: Dict[int, Dict[int, float]], events_2: Dict[int, EventRecord], event_t_2: Dict[int, Dict[int, float]] ) -> Tuple[ float, List[ProbDiffRecord], List[TransitionDiffRecord], List[TransitionDiffRecord]]:
    
    prob_diffs = compute_prob_diff( events_1, events_2 )
    
    agg_score, score_diffs, raw_transition_diffs = compute_transition_diff( events_1, events_2, event_t_1, event_t_2 )
    
    # Prune out transitions that don't exist in one for the purposes of ranked list
    #prob_diffs = list(filter(lambda x: x[0] != float('Inf'), prob_diffs))

    raw_transition_diffs = list(filter(lambda diff_record: diff_record.diff != float('Inf'), raw_transition_diffs))
    score_diffs = list(filter(lambda diff_record: diff_record.diff != float('Inf'), score_diffs))
    return( agg_score, prob_diffs, raw_transition_diffs, score_diffs )

def pretty_print_differences( agg_score: float, prob_diffs: List[ProbDiffRecord], raw_transition_diffs: List[TransitionDiffRecord], score_diffs: List[TransitionDiffRecord], k=30):
    print( "Aggregate Difference: {}".format( agg_score ) )
    print( "="*60 )
    print( "Top {} Event Probability Differences:".format(k) )
    print( "{:<15}\t{:<15}\t{:<15}{:<20}".format("Ratio","Left Prob","Right Prob","Location") )
    print( "-"*60 )
    i = 0
    while i < k:
        if i == len(prob_diffs):
            break
        if prob_diffs[i].is_left_greater:
            print( Fore.BLUE + "{:<15f}\t{:<15f}\t{:<15f}\t{:<20}".format( 
                prob_diffs[i].diff, prob_diffs[i].left_val, prob_diffs[i].right_val,
                "{}:{}".format(prob_diffs[i].event_fname, prob_diffs[i].event_line)) + Style.RESET_ALL)
        else:
            print( Fore.RED + "{:<15f}\t{:<15f}\t{:<15f}\t{:<20}".format(
                prob_diffs[i].diff, prob_diffs[i].left_val, prob_diffs[i].right_val,
                "{}:{}".format(prob_diffs[i].event_fname, prob_diffs[i].event_line)) + Style.RESET_ALL)
        i += 1
    print( "="*60 )
    print( "Top {} Event Transition Differences:".format(k) )
    print( "{:<15}\t{:<15}\t{:<15}\t{:<20}".format("Ratio","Left Prob","Right Prob","Transition" ) )
    print( "-"*60 )
    i = 0
    while i < k:
        if i == len(raw_transition_diffs):
            break

        if raw_transition_diffs[i].is_left_greater:
            print( Fore.BLUE + "{:<15}\t{:<15}\t{:<15}\t{:<20}".format( raw_transition_diffs[i].diff, raw_transition_diffs[i].left_val,
                raw_transition_diffs[i].right_val, "{}:{} -> {}:{}".format( raw_transition_diffs[i].src_fname, raw_transition_diffs[i].src_line,
                raw_transition_diffs[i].dst_fname, raw_transition_diffs[i].dst_line)) + Style.RESET_ALL )
        else:
            print( Fore.RED + "{:<15}\t{:<15}\t{:<15}\t{:<20}".format( raw_transition_diffs[i].diff, raw_transition_diffs[i].left_val,
                raw_transition_diffs[i].right_val, "{}:{} -> {}:{}".format( raw_transition_diffs[i].src_fname, raw_transition_diffs[i].src_line, 
                raw_transition_diffs[i].dst_fname, raw_transition_diffs[i].dst_line)) + Style.RESET_ALL )
        i += 1

def show_transition_graph( start_node: MarkovNode, depth=1, filter_function=lambda node, prob: True ):
    def remap_event_id( event_id ):
        return event_id.replace(":", "-")
    
    def build_transition_graph( graph: graphviz.Digraph, node: MarkovNode, depth, nodes_so_far: List[MarkovNode] ):
        if node in nodes_so_far:
            return
        
        nodes_so_far.append( node )
        graph.node( remap_event_id( node.get_key() ), node.get_key() )

        if depth != 0:
            for transition in node.transitions:
                if filter_function( transition.dst, transition.prob):
                    graph.node( remap_event_id( transition.dst.get_key() ), transition.dst.get_key() )
                    edge_label = "{:<5f}".format( transition.prob )
                    graph.edge( remap_event_id( node.get_key() ), remap_event_id( transition.dst.get_key() ), label=edge_label )
                    build_transition_graph( graph, transition.dst, depth-1, nodes_so_far )
    graph = graphviz.Digraph(comment="{} Event Transitions, Depth={}".format( start_node.get_key(), depth ) )
    build_transition_graph( graph, start_node, depth, [] )
    return graph

def show_mcmc_graph( start_event_id, events, event_transitions, target_depth, depth_bounded_mcmc_results ):
    def remap_event_id( event_id ):
        return event_id.replace(":", "-")

    def build_transition_graph( graph, event_id, events, event_transitions, mcmc_results, depth ):
        event = events[event_id]
        graph.node( remap_event_id( event_id ), event_id )
        transitions = event_transitions[ event_id ]
        if depth == 0:
            return
        for transition in transitions:
            graph.node( remap_event_id( transition ), transition )
            # 50th percentile
            edge_label = "{:<5f}".format( mcmc_results[ event_id ][ transition ][ 9 ] )
            graph.edge( remap_event_id( event_id ), remap_event_id( transition ), label=edge_label )
            build_transition_graph( graph, transition, events, event_transitions, mcmc_results, depth-1 )

    graph = graphviz.Digraph(comment="{} Event MCMC, Depth={}".format( start_event_id, target_depth ) )

    mcmc_dict = {}
    for key in depth_bounded_mcmc_results:
        ptls = depth_bounded_mcmc_results[ key ]
        dst_id = key.get_key()
        if not start_event_id in mcmc_dict:
            mcmc_dict[ start_event_id ] = {}
        mcmc_dict[ start_event_id ][ dst_id ] = ptls
    build_transition_graph( graph, start_event_id, events, event_transitions, mcmc_dict, target_depth )
    return graph

def generate_distance_matrix( percentile_vec ):
    """Compute the pairwise distance between every set of percentile "positions". Since the percentiles
    are not equally spread, some may be farther apart than others, which corresponds to more "distance" in terms of EMD"""
    grid1, grid2 = np.meshgrid( percentile_vec, percentile_vec )
    return np.abs( grid2 - grid1 )

def get_cdf( conn, src_fname: str, src_line: int, dst_fname: str, dst_line: int, run_id: int ):
    query = "SELECT percentile_values FROM transition_cdfs WHERE run_id = %s AND src_fname = %s AND src_line = %s AND dst_fname = %s AND dst_line = %s"
    cur = conn.cursor()
    cur.execute( query, (run_id, src_fname, src_line, dst_fname, dst_line) )
    results = cur.fetchall()
    return results

def do_emd( args ):
    src_fname, src_line, dst_fname, dst_line, cdf_vals1, cdf_vals2, dist_mat, normalize = args
    
    # Renormalize
    if normalize:
        max_val = max( cdf_vals1[-1], cdf_vals2[-1])
    else:
        max_val = 1.0
    cdf_vals1 = np.array( cdf_vals1 )/max_val
    cdf_vals2 = np.array( cdf_vals2 )/max_val
    
    # EMD
    emd_score = pyemd.emd( cdf_vals1, cdf_vals2, dist_mat )
    return (emd_score, src_fname, src_line, dst_fname, dst_line )


def get_emd_scores_for_transitions( conn, run_id1: int, run_id2: int, normalize=True, procs=1 ):
    percentiles = [0.05,
         0.1,
         0.15,
         0.2,
         0.25,
         0.3,
         0.35,
         0.4,
         0.45,
         0.5,
         0.55,
         0.6,
         0.65,
         0.7,
         0.75,
         0.8,
         0.85,
         0.9,
         0.95,
         0.99,
         0.999 ]
    dist_mat = generate_distance_matrix( percentiles )
    transition_cdf_query = """SELECT DISTINCT(src_fname, src_line, dst_fname, dst_line) FROM transition_cdfs,
        log_line_transitions, log_line_probabilities
        WHERE src_fname = log_initial_fname and src_line = log_initial_line and dst_fname = log_next_fname and dst_line = log_next_line
        and log_line_transitions.run_id = transition_cdfs.run_id and log_line_transitions.run_id = log_line_probabilities.run_id and 
        log_fname = src_fname and log_line = src_line and transition_count > 1000 and 
        (transition_cdfs.run_id = %s OR transition_cdfs.run_id = %s)"""
    cur = conn.cursor()
    cur.execute( transition_cdf_query, (run_id1, run_id2) )
    results = cur.fetchall()
    cur.close()

    proc_pool = multiprocessing.Pool( procs )
    all_args = []
    for result in results:
        field = result[0]
        
        # DB merges these fields together in distinct, need to split them out
        src_fname, src_line, dst_fname, dst_line = field.split(",")
        dst_line = dst_line[:-1] #Remove trailing commas
        src_fname = src_fname[1:] #Remove leading (
        
        # Get CDFs
        cdf_vals1 = get_cdf( conn, src_fname, int(src_line), dst_fname, int(dst_line), run_id1 )
        cdf_vals2 = get_cdf( conn, src_fname, int(src_line), dst_fname, int(dst_line), run_id2 )
        if not cdf_vals1 or not cdf_vals2:
            continue

        cdf_vals1 = cdf_vals1[0][0]
        cdf_vals2 = cdf_vals2[0][0]

        all_args.append( (src_fname, src_line, dst_fname, dst_line, cdf_vals1, cdf_vals2, dist_mat, normalize) )
    emd_scores = proc_pool.map( do_emd, all_args )
    return emd_scores

### Variable Order Stuff.
class VariableOrderTransition:
    """Variable Order Transition (s-k,...,s) - > s'"""
    def __init__( self, prior_events: List[FileLocation], next_event: FileLocation ):
        self.prior_events = prior_events
        self.next_event = next_event
    def __repr__( self ) -> str:
        return "({})->{}".format( ",".join([ str(ev) for ev in self.prior_events ]), self.next_event )
    def __eq__( self, obj ) -> bool:
        return isinstance( obj, VariableOrderTransition) and self.prior_events == obj.prior_events and self.next_event == obj.next_event
    def __ne__( self, obj ) -> bool:
        return not self == obj
    def __hash__( self ) -> int:
        return hash( (tuple(self.prior_events), self.next_event) )

class VariableOrderTransitionIndex:
    """An index from a tuple of prior events (s-k,...,s) to a list of transitions."""

    def __init__( self ):
        self.vot_prior_index = {} # type: Dict[Tuple[FileLocation, ...], List[VariableOrderTransition]]

    def add_transition( self, vo_transition: VariableOrderTransition ):
        key = tuple(vo_transition.prior_events)
        if not key in self.vot_prior_index:
            self.vot_prior_index[key] = []
        self.vot_prior_index[ key ].append( vo_transition )

    def find_all_transitions( self, prior_events: Tuple[FileLocation, ...] ) -> List[VariableOrderTransition]:
        key = prior_events
        while len(key) > 0:
            if key in self.vot_prior_index:
                return self.vot_prior_index[ key ]
            key = key[1:] # chop first element
        return []

    def is_in_index( self, event_sequence: Tuple[FileLocation, ...] ) -> bool:
        return event_sequence in self.vot_prior_index

def build_vot_prior_index( vo_transitions: Iterable[VariableOrderTransition] ) -> VariableOrderTransitionIndex:
    vot_index = VariableOrderTransitionIndex()
    for vo_transition in vo_transitions:
        vot_index.add_transition( vo_transition )
    return vot_index

def get_all_unique_vo_transitions( vo_transitions1 : Dict[VariableOrderTransition, int], vo_transitions2: Dict[VariableOrderTransition, int] ) -> Set[VariableOrderTransition]:
    unique_vo_transitions = set([]) # type: Set[VariableOrderTransition]
    matched_subtransition = set([]) # type: Set[VariableOrderTransition]
    transitions_without_matches = set([]) # type: Set[VariableOrderTransition]

    def get_all_unique_vo_transitions_sub( vo_transitions_i, vo_transitions_j, unique_vo_transitions, matched_subtransition, transitions_without_matches ):
        for vo_transition in vo_transitions_i:
            if vo_transition in vo_transitions_j:
                unique_vo_transitions.add( vo_transition )
            else:
                # This transition may not be present in vo_transitions_j because:
                # i) The transition never occurred in vo_transitions_j
                # ii) The transition occurred, but was reduced in vo_transitions_j but not in vo_transitions_i
                # iii) This is a reduced version of a transition that happened in vo_transitions_j
                # We want only the maximum length edition of this sequence.
                # To do so, compute subsets of this key and try to match them in vo_transitions_j.
                prior_events = vo_transition.prior_events[1:]
                while len(prior_events) > 0:
                    reduced_transition = VariableOrderTransition( prior_events, vo_transition.next_event )
                    if reduced_transition in vo_transitions_j:
                        # We matched on a reduced version, append the full version
                        unique_vo_transitions.add( vo_transition )
                        matched_subtransition.add( reduced_transition )
                        break
                    # Chop, go again
                    prior_events = prior_events[1:]

                # Didn't match on any subset. Either we are the subset, or this transition didn't happen in vo_transitions_j.
                # Need to handle second case where we should still add this transition (can check if someone matched us!)
                transitions_without_matches.add( vo_transition )

    get_all_unique_vo_transitions_sub( vo_transitions1, vo_transitions2, unique_vo_transitions, matched_subtransition, transitions_without_matches )
    get_all_unique_vo_transitions_sub( vo_transitions2, vo_transitions1, unique_vo_transitions, matched_subtransition, transitions_without_matches )

    for vo_transition in transitions_without_matches:
        if vo_transition not in matched_subtransition:
            unique_vo_transitions.add( vo_transition )

    return unique_vo_transitions

class VOTransitionDiffRecord:
    def __init__( self, transition: VariableOrderTransition, left_prob: float, right_prob: float, left_count_match: int, left_count_miss: int, right_count_match: int, right_count_miss: int ):
        self.transition = transition
        self.left_prob = left_prob
        self.right_prob = right_prob
        self.left_count = left_count_match
        self.right_count = right_count_match
        self.left_miss_count = left_count_miss
        self.right_miss_count = right_count_miss
        self.score = 0.
        self.stat = 10000
        if (left_prob > 0 and right_prob > 0) and left_prob != right_prob:
            self.score = max( left_prob / right_prob, right_prob / left_prob )

            # left_prob is mean, variance should be left_prob * (1-left_prob)
            left_std = np.sqrt( left_prob * (1-left_prob) )
            right_std = np.sqrt( right_prob * (1-right_prob) )

            tstat, pval = scipy.stats.ttest_ind_from_stats( left_prob, left_std, left_count_miss, right_prob, right_std, right_count_miss  )
            self.stat = pval

def create_vot_diff_record( maximal_vo_transition: VariableOrderTransition, left_prob: float, right_prob: float, left_count_match: int, left_count_miss: int, right_count_match: int, right_count_miss: int ) -> VOTransitionDiffRecord:
    return VOTransitionDiffRecord( maximal_vo_transition, left_prob, right_prob, left_count_match, left_count_miss, right_count_match, right_count_miss )
    

def compute_vot_diff( vo_transitions1: Dict[VariableOrderTransition, int], vo_transitions2: Dict[VariableOrderTransition, int] ):

    vot_diff_records = []
    all_vo_transitions = get_all_unique_vo_transitions( vo_transitions1, vo_transitions2 )

    # A VariableOrderTransition consists of (s-k,...,s) -> s'.
    # We want to compare probabilities of making this particular transition (e.g. P(s'|s-k,...,s)), but we have only counts
    # Since P(s'|s-k,...s) = (s' from s-k,...s)/sum(anything from s-k,...,s), we need all VariableOrderTransition with the same prior events.
    # Let's build this index.
    vot_prior_event_index1 = build_vot_prior_index( vo_transitions1.keys() )
    vot_prior_event_index2 = build_vot_prior_index( vo_transitions2.keys() )

    for vo_transition in all_vo_transitions:
        # Suppose this transition is from (s-k,...,s)->s'. We need to obtain the 
        # the probability of this transition from both VariableOrderMarkovGraphs.
        # To do so, we need to find the count of moving from (s-k,...,s)->X for all
        # X, dividing that from the count of going from (s-k,...,s)->s'.

        # The problem is that either graph (or both) may not have (s-k,...,s) in it.
        # This could be because the transition's order has been reduced, or because the
        # the sequence (s-k,...,s) never occurred.

        # We know, however, that if (s-k,...,s)->X has been reduced to
        # (s-k-1,...,s)->X, it holds for all X. So, if we ever transitioned to s' from
        # (s-k,...,s)->s', then it would either show up at (s-k,...,s)->s' or as
        # (s-k-m,...,s)->s' for some m, and that the probability of (s-k-m,...,s)->s' is
        # the same as (s-k,...,s)->s'. So, search for (s-k,...s), (s-k-1,...,s), ... 
        # sequences until we find one, and use that to compute the transition probability to s',
        # which we know is the same.

        all_transitions_for_vom1 = vot_prior_event_index1.find_all_transitions( tuple(vo_transition.prior_events) )
        all_transitions_for_vom2 = vot_prior_event_index2.find_all_transitions( tuple(vo_transition.prior_events) )
        
        # We may have reduced the transition in one model, but not the other. Use the matching_transition we retrieved.
        tr_count_vom1 = 0
        this_tr_count_vom1 = 0
        have_match = False
        for matching_transition in all_transitions_for_vom1:
            assert matching_transition in vo_transitions1
            tr_count_vom1 += vo_transitions1[ matching_transition ]
            if matching_transition.next_event == vo_transition.next_event:
                this_tr_count_vom1 = vo_transitions1[ matching_transition ]
                have_match = True
        prob_tr_vom1 = 0.
        if len(all_transitions_for_vom1) > 0:
            prob_tr_vom1 = float( this_tr_count_vom1 ) / tr_count_vom1
            
        tr_count_vom2 = 0
        this_tr_count_vom2 = 0
        for matching_transition in all_transitions_for_vom2:
            assert matching_transition in vo_transitions2
            tr_count_vom2 += vo_transitions2[ matching_transition ]
            if matching_transition.next_event == vo_transition.next_event:
                this_tr_count_vom2 = vo_transitions2[ matching_transition ]
                have_match = True

        assert have_match

        prob_tr_vom2 = 0.
        if len(all_transitions_for_vom2) > 0:
            prob_tr_vom2 = float( this_tr_count_vom2 ) / tr_count_vom2

        # create vo_diff_record
        vot_diff_records.append( create_vot_diff_record( vo_transition, prob_tr_vom1, prob_tr_vom2, this_tr_count_vom1, tr_count_vom1, this_tr_count_vom2, tr_count_vom2 ) )

    return vot_diff_records

class InvalidModelException(Exception):
    pass

class VariableOrderMarkovGraph:
    """A Markov Graph where the transitions between nodes may rely on a variable number of previous nodes.
    A traditional MarkovGraph uses P(s'|s), but this Markov Graph is P(s'|s,s-1,s-2...s-k) AND k is variable depending on s'"""

    def __init__( self, events: Dict[FileLocation, EventRecord], transitions: Dict[VariableOrderTransition, int] ):
        self.events = events
        self.transitions = transitions

    def serialize( self ) -> bytes: 
        return pickle.dumps( self )

    @staticmethod
    def deserialize( data ):
        model = pickle.loads( data )
        model.check_valid_model()
        return model

    def diff( self, other_vom: 'VariableOrderMarkovGraph' ):
        prob_diff_records = compute_prob_diff( self.events, other_vom.events )
        vot_diff_records = compute_vot_diff( self.transitions, other_vom.transitions )
        return prob_diff_records, vot_diff_records

    def check_valid_model( self ):
        """Confirm that this variable order markov model is valid. That is,
        if it contains a transitions from (s_k,...,s), it does not contain transitions from
        (s_k-m,...s) for all m."""

        prior_vot_index = build_vot_prior_index( self.transitions )

        for transition in self.transitions.keys():
            prior_event_seq = transition.prior_events
            while len(prior_event_seq) > 1:
                prior_event_subseq = prior_event_seq[1:]
                if prior_vot_index.is_in_index( tuple(prior_event_subseq) ):
                    raise InvalidModelException( "{} in model, but so is {}".format( prior_event_subseq, transition.prior_events ) )
                prior_event_seq = prior_event_subseq

    def merge_in( self, other_vom: 'VariableOrderMarkovGraph' ):
        pass

# This is redundant. I could just use VariableOrderMarkovModel now.
class FileEventSummary:
    """A summary of all the events (counts, transitions) that have occurred in one Sentinel output file."""
    def __init__( self, known_locs: List[ FileLocation ], event_count_map: Dict[FileLocation, int], event_transition_map: Dict[VariableOrderTransition, int] ):

        # Known Locs
        self.known_locs = known_locs

        # Map from locs to counts
        self.event_count_map = event_count_map

        # Map from (PriorEvents->Transition) -> Count
        self.event_transition_map = event_transition_map

        self.msg_map = {} # type: Dict[FileLocation, str]

    def untranslate( self, cur_key ):
        for k, translated_k in self.event_id_translation_map.items():
            if cur_key == translated_k:
                return k
        raise LookupError( "{} not found!".format( cur_key ) )

    def merge_count_dicts( self, out_dict: Dict[Any, int], other_dict: Dict[Any, int] ):
        """ Given two dictionaries that track counts over objects, sum them together in out_dict"""
        for k in out_dict.keys():
            if k in other_dict.keys():
                out_dict[k] += other_dict[k]
        
        for k in other_dict.keys():
            if not k in out_dict.keys():
                out_dict[k] = other_dict[k]

    def merge_in( self, other_summary: 'FileEventSummary' ):
        # Merge in the event_ids we don't know about
        for known_loc in other_summary.known_locs:
            if known_loc not in self.known_locs:
                self.known_locs.append( known_loc )
        
        self.merge_count_dicts( self.event_count_map, other_summary.event_count_map )
        self.merge_count_dicts( self.event_transition_map, other_summary.event_transition_map )

    def as_variable_order_markov_graph( self ) -> VariableOrderMarkovGraph:
        total_event_count = 0.
        for event_loc, count in self.event_count_map.items():
            total_event_count += count
        event_records = {} # type: Dict[FileLocation, EventRecord]
        for event_loc, count in self.event_count_map.items():
            record = EventRecord( event_loc.fname, event_loc.line_number, float(count)/total_event_count )
            event_records[ event_loc ] = record

        return VariableOrderMarkovGraph( event_records, self.event_transition_map )

def process_event_line( line, file_map: Dict[int, FileLocation], count_map: Dict[FileLocation,int] ):
    """Process a line like "pg.c:1 = 1, 10" and add the filelocation and count to the right maps"""
    left, right = line.split("=")
    fname, line_number = left.split(":")
    loc = FileLocation( fname, int( line_number.strip() ) )
    identifier, count = right.lstrip().split(",")
    identifier = int( identifier )
    count = int( count.strip() )
    assert identifier not in file_map
    file_map[identifier] = loc
    count_map[loc] = count

def process_transition_line( line, file_map: Dict[int,FileLocation], transition_map: Dict[VariableOrderTransition, int] ):
    """Process a line like "(1,2)->1: 2" and add the transition and count to the right maps"""
    left, right = line.split("->")
    
    # Skip over old transitions that we outputted.
    if not "(" in line:
        return

    prior_event_id_str = left.strip()
    prior_event_id_str = prior_event_id_str[1:-1] # chop off brackets
    prior_event_ids = [ int(prior_event_id) for prior_event_id in prior_event_id_str.split(",") ]

    transition, count = right.lstrip().split(":")
    transition_id = int( transition.lstrip() )
    count = int( count.lstrip() )

    prior_event_locs = [ file_map[ prior_event_id ] for prior_event_id in prior_event_ids ]
    right_loc = file_map[ transition_id ]

    transition = VariableOrderTransition( prior_event_locs, right_loc )
    transition_map[transition] = count

def process_dump_lines( lines )-> FileEventSummary:
    """ Read all the lines in a file and convert them into a FileEventSummary"""
    i = 0
    event_file_map = {} # type: Dict[int, FileLocation]
    event_count_map = {} # type: Dict[FileLocation, int]
    event_transition_map = {} # type: Dict[VariableOrderTransition, int]
    while i < len(lines):
        # This is a transition line, break into transition processing
        if "->" in lines[i]:
            break
        # This is still an event count line
        process_event_line( lines[i], event_file_map, event_count_map )
        i += 1

    while i < len(lines):
        process_transition_line( lines[i], event_file_map, event_transition_map )
        i += 1

    return FileEventSummary( [ v for k,v in event_file_map.items() ], event_count_map, event_transition_map )
        
def read_single_im_dump( filename: str ) -> FileEventSummary:
    with open( filename, "r" ) as f:
        f_lines = f.readlines()
        f_event_summary = process_dump_lines( f_lines )
        return( f_event_summary )

def read_all_im_dumps( im_dir: str ) -> FileEventSummary:
    f_event_summary = FileEventSummary( [], {}, {} )
    for fname in glob.iglob( "{}/*.im.out*".format( im_dir ) ):
        next_f_event_summary = read_single_im_dump( fname )

        # TODO: for debugging, can turn off if we want
        per_thread_vom = next_f_event_summary.as_variable_order_markov_graph()
        per_thread_vom.check_valid_model()

        f_event_summary.merge_in( next_f_event_summary )

        # TODO: for debugging, can turn off if we want
        merged_vom = f_event_summary.as_variable_order_markov_graph()
        merged_vom.check_valid_model()

    return f_event_summary

def get_log_line_from_location( file_loc: FileLocation, postgres_src_dir: str ) -> str:
    return "macro, can't tell"

def get_log_lines_for_im_dumps( merged_summaries: FileEventSummary, postgres_src_dir: str ):
    msg_map = {} # type: Dict[FileLocation, str]
    for loc in merged_summaries.known_locs:
        msg_map[loc] = get_log_line_from_location( loc, postgres_src_dir )
    merged_summaries.msg_map = msg_map
