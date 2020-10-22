import os
import glob
import argparse

class FileEventSummary:
    def __init__( self, known_locs : list, event_count_map, event_transition_map ):

        # Known Locs
        self.known_locs = known_locs

        # Map from locs to counts
        self.event_count_map = event_count_map

        # Map from loc x loc to count 
        self.event_transition_map = event_transition_map

        self.msg_map = {}

    def untranslate( self, cur_key ):
        for k, translated_k in self.event_id_translation_map.items():
            if cur_key == translated_k:
                return k
        assert( False )

    def merge_in( self, other_summary ):

        # Merge in the event_ids we don't know about
        for known_loc in other_summary.known_locs:
            if known_loc not in self.known_locs:
                self.known_locs.append( known_loc )

        for loc in self.event_count_map.keys():
            if loc in other_summary.event_count_map.keys():
                self.event_count_map[loc] += other_summary.event_count_map[loc]

        for loc in other_summary.event_count_map.keys():
            if loc not in self.event_count_map.keys():
                self.event_count_map[loc] = other_summary.event_count_map[loc]


        for loc in self.event_transition_map.keys():
            if loc in other_summary.event_transition_map.keys():
                for loc2 in self.event_transition_map[loc].keys():
                    if loc2 in other_summary.event_transition_map[loc]:
                        self.event_transition_map[loc][loc2] += other_summary.event_transition_map[loc][loc2]

        for loc in other_summary.event_transition_map.keys():
            if loc not in self.event_transition_map:
                self.event_transition_map[loc] = other_summary.event_transition_map[loc]
            else:
                for loc2 in other_summary.event_transition_map[loc].keys():
                    if loc2 not in self.event_transition_map[loc]:
                        self.event_transition_map[loc][loc2] = other_summary.event_transition_map[loc][loc2]
                       

class FileLocation:
    def __init__( self, fname: str, line_number: int ):
        self.fname = fname
        self.line_number = line_number
    def __repr__( self ):
        return "{}:{}".format( self.fname, self.line_number )
    def __eq__( self, obj ):
        return isinstance( obj, FileLocation ) and self.line_number == obj.line_number and self.fname == obj.fname
    def __ne__( self, obj ):
        return not self == obj
    def __hash__( self ):
        return hash(self.fname) ^ hash(self.line_number)

def process_dump_lines( lines ):
    i = 0
    event_count_map = {}
    event_file_map = {}
    event_transition_map = {}
    while i < len(lines):
        # This is a transition line, break into transition processing
        if "->" in lines[i]:
            break
        # This is still an event count line
        left, right = lines[i].split("=")
        fname, line_number = left.split(":")
        loc = FileLocation( fname, int( line_number.strip() ) )
        identifier, count = right.lstrip().split(",")
        identifier = int( identifier )
        count = int( count.strip() )
        assert identifier not in event_file_map
        event_file_map[identifier] = loc
        event_count_map[loc] = count
        i += 1

    while i < len(lines):
        left, right = lines[i].split("->")
        left_id = int( left.strip() )
        transition, count = right.lstrip().split(":")
        transition_id = int( transition.lstrip() )
        count = int( count.lstrip() )

        left_loc = event_file_map[ left_id ]
        right_loc = event_file_map[ transition_id ]

        if left_loc not in event_transition_map:
            event_transition_map[left_loc] = {}
        
        event_transition_map[left_loc][right_loc] =  count

        i += 1

    return FileEventSummary( [ v for k,v in event_file_map.items() ], event_count_map, event_transition_map )
        
def read_single_im_dump( filename: str ):
    with open( filename, "r" ) as f:
        f_lines = f.readlines()
        f_event_summary = process_dump_lines( f_lines )
        return( f_event_summary )

def read_all_im_dumps( im_dir: str ):
    f_event_summary = FileEventSummary( [], {}, {} )
    for fname in glob.iglob( "{}/*.im.out*".format( im_dir ) ):
        next_f_event_summary = read_single_im_dump( fname )
        f_event_summary.merge_in( next_f_event_summary )
    return f_event_summary

def find( path: str, name: str ):
    for root, dirs, files in os.walk( path ):
        if name in files:
            return os.path.join( root, name )

def get_log_line_from_location( file_loc: FileLocation, postgres_src_dir: str ):
    return "macro, can't tell"

    #the_file = find( postgres_src_dir, file_loc.fname )
    #with open( the_file, "r" ) as f:
    #    # Enumerate to avoid materializing the file in memory
    #    lines = f.readlines()
    #    cur_ind = file_loc.line_number-1
    #    orig_ind = cur_ind
    #    base_line = lines[cur_ind]
    #    is_elog = True

        # Find the start of elog call
    #    while "elog" not in base_line and "ereport" not in base_line and "Logger.log" not in base_line:
    #        cur_ind -= 1
    #        base_line = lines[cur_ind]
#
#        is_elog = "elog" in base_line
        
        # Message is always the second arg
#        log_call = "".join( lines[cur_ind:orig_ind+1] )

        # Find first comma (end of first arg)
        #i = 0
        #while True:
        #    if ',' == log_call[i]:
        #        break
        #    i += 1
        #j = i+1

        # Find second comma (if more args left) or ); indicating end of call 
        #while True:
        #    if "," == log_call[j] or ( ")" == log_call[j] and ";" == log_call[j+1] ):
        #        break
        #    j += 1

        # Doesn't work with macros
        #the_message = log_call.lstrip().strip()
        #the_message = "\"" + the_message.split("\"")[1] + "\""
#        the_message = "macro, can't tell."

        #if not is_elog:
        #    the_message = the_message.split("(")[2]
        #    print( file_loc.fname, file_loc.line_number, the_message )
        #    the_message = the_message.split(")")[0]
#        return( the_message )

def get_log_lines_for_im_dumps( merged_summaries: FileEventSummary, postgres_src_dir: str ):
    msg_map = {}
    for loc in merged_summaries.known_locs:
        msg_map[loc] = get_log_line_from_location( loc, postgres_src_dir )
    merged_summaries.msg_map = msg_map

parser = argparse.ArgumentParser( "Read dumped postgres in memory tracing files and computes the transition graphs." )
parser.add_argument( "-p", action="store", dest="postgres_dir", default="/tmp/postgresql_source", help="sets the postgres source directory" )
parser.add_argument( "-d", action="store", dest="im_dir", default="/tmp", help="sets the directory in which in memory tracing files were dumped" )
parser.add_argument( "-m", action="store", dest="max_id", default=1000, help="sets the maximum RID value." )

args = parser.parse_args()
merged_summaries = read_all_im_dumps( args.im_dir )
get_log_lines_for_im_dumps( merged_summaries, args.postgres_dir )

for loc in merged_summaries.msg_map:
    print( loc, merged_summaries.msg_map[loc].strip(), merged_summaries.event_count_map[loc] )

print( "---" )

for loc in merged_summaries.event_transition_map:
    for loc2 in merged_summaries.event_transition_map[loc]:
        print( loc, loc2, merged_summaries.event_transition_map[loc][loc2] )

#print( merged_summaries.event_id_map['456'].fname, merged_summaries.event_id_map['456'].line_number )
