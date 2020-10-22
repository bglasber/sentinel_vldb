import glob
import math
import sys

def list_to_array_syntax( l ):
    """Convert a python list to PGSQL array syntax for insertion"""
    l_text = str(l)
    l_text = "'{" + l_text[1:-1] + "}'"
    return l_text


lines = []
with open( "out_lines.txt", "r" ) as f:
    lines = [ l.strip() for l in f.readlines() ]


total_event_count = 0
event_map = {}
line_number = 0
run_id = int(sys.argv[1])
# Phase 1: Get the frequency
while line_number < len( lines ):
    line = lines[ line_number ]
    if line == "---":
        line_number += 1
        break

    split_line = line.split(" ")
    event = split_line[0]
    freq = int(split_line[-1])
    event_msg = " ".join( split_line[1:-1] )

    total_event_count += freq
    event_map[ event ] = freq

    line_number += 1

sql_str = "INSERT INTO run_identifier VALUES ( {}, NOW() );".format( run_id )
print( sql_str )
sql_str = "INSERT INTO exp_iterations VALUES ( {}, 0 );".format( run_id )
print( sql_str )

for event, freq in event_map.items():
    event_prob = float(freq)/total_event_count
    sql_str = "INSERT INTO log_line_probabilities( run_id, iteration_number, log_fname, log_line, log_count, log_probability ) VALUES( {}, {}, {}, {}, {}, {} ) ON CONFLICT DO NOTHING;"
    event_file, event_line = event.split(":")
    formatted_sql_str = sql_str.format( run_id, 0, "'" + event_file + "'" , event_line, freq, event_prob )
    print( formatted_sql_str )
    

# Phase 2: Get the transitions
while line_number < len( lines ):
    line = lines[ line_number ]
    from_event, to_event, freq = line.split( " " )
    from_event_file, from_event_line = from_event.split(":")
    to_event_file, to_event_line = to_event.split(":")
    transition_prob = float(freq) / event_map[ from_event ]
    sql_str = "INSERT INTO log_line_transitions( run_id, iteration_number, log_initial_fname, log_initial_line, log_next_fname, log_next_line, transition_count, transition_probability ) VALUES( {}, {}, {}, {}, {}, {}, {}, {} ) ON CONFLICT DO NOTHING;"
    formatted_sql_str = sql_str.format( run_id, 0, "'" + from_event_file + "'", from_event_line, "'" + to_event_file + "'", to_event_line, freq, transition_prob )
    print( formatted_sql_str )

    line_number += 1


for fname in glob.glob("/tmp/*.ln"):
    lines = []
    with open( fname, "r" ) as f:
        lines = [ l.strip() for l in f.readlines() ]
    ptls = []
    vals = []
    for line in lines:
        ptl,val = line.split(",")
        ptls.append( float(ptl) )
        vals.append( math.exp(float(val)) )
    fname_chunks = fname.split("/")[-1]
    fname_chunks = fname_chunks.split("-")
    src_id = fname_chunks[2]
    src_fname, src_ln = src_id.split(":")
    src_fname = "'" + src_fname + "'"
    dst_id = fname_chunks[3]
    dst_fname, dst_ln = dst_id.split(":")
    dst_fname = "'" + dst_fname + "'"

    sql_stmt = "INSERT INTO transition_cdfs( run_id, iteration_number, src_fname, src_line, dst_fname, dst_line, percentiles, percentile_values ) VALUES( {}, {}, {}, {}, {}, {}, {}, {} );"

    formatted_sql_stmt = sql_stmt.format( run_id, 0, src_fname, src_ln, dst_fname, dst_ln, list_to_array_syntax( ptls ), list_to_array_syntax( vals ) )
    print( formatted_sql_stmt )
