#!/usr/bin/env python3

import sys
import psycopg2
import argparse
from sentinel_analysis import *

if __name__ == "__main__":
    parser = argparse.ArgumentParser( description='computes top differences between runs using sentinel' )
    parser.add_argument( '-k', type=int, action='store', help="""report top-k differences""", dest="topkcount", default=10 )
    parser.add_argument( '-r', type=str, action='store', help="""DB Host Name""", dest="dbhost", default="localhost" )
    parser.add_argument( '-d', type=str, action='store', help="""DB Name""", dest="dbname", default="sent_tmp" )
    parser.add_argument( '-u', type=str, action='store', help="""DB username""", dest="dbuser", default="postgres" )

    parser.add_argument( 'runid1', type=str, action='store', help="""First run"""  )
    parser.add_argument( 'runid2', type=str, action='store', help="""Second run""" )

    args = parser.parse_args()

    conn = psycopg2.connect( 'host={} user={} dbname={}'.format( args.dbhost, args.dbuser, args.dbname ) )

    events1, event_transitions1 = get_data_from_postgres( conn, args.runid1 )
    events2, event_transitions2 = get_data_from_postgres( conn, args.runid2 )

    agg_score, prob_diffs, raw_trans_diffs, score_diffs = compute_difference( events1, event_transitions1, events2, event_transitions2 )
    pretty_print_differences( agg_score, prob_diffs, raw_trans_diffs, score_diffs, args.topkcount )


    print( "\nTop EMD Differences:\n" )
    emd_scores = get_emd_scores_for_transitions( conn, args.runid1, args.runid2, normalize=False, procs=1 )
    emd_scores.sort( key=lambda x: x[0], reverse=True )
    for i in range( min( len(emd_scores), args.topkcount) ):
        print( emd_scores[i] )

    conn.close()
