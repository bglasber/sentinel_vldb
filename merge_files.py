import glob
import logging
import subprocess
import sys
import math
import numpy as np

def compute_flat_file_percentiles(l_files: list):
    all_percentiles = []
    all_ln_percentiles = []
    for filename in l_files:
        with open( filename, 'r' ) as f:
            for line in f:
                try:
                    all_percentiles.append( float(line.strip()) )
                    all_ln_percentiles.append( math.log( float(line.strip() ) ) )
                except:
                    print( "Problem with file: {}".format( filename ) )

    arr = np.array( all_percentiles )
    arr2 = np.array( all_ln_percentiles )
    percentiles = [ 5,10,15,20,25,30,35,40,45,50,55,60,65,70,75,80,85,90,95,99,99.9 ]
    percentiles_to_write = [ 0.05,0.1,0.15,0.2,0.25,0.3,0.35,0.4,0.45,0.5,0.55,0.6,0.65,0.7,0.75,0.8,0.85,0.9,0.95,0.99,0.999 ]
    try:
        ptl_values = np.percentile( arr, percentiles )
        ptl_ln_values = np.percentile( arr2, percentiles )

        f_name = l_files[0]
        if "/" in f_name:
            f_name = f_name.split("/")[-1]
        # event_flat_thing_thing
        f_name_all_str = '-'.join( f_name.split("-")[:4] ) + "-cdf-values.csv"

        with open(f_name_all_str, 'w+') as f:
            for i in range(len(ptl_values)):
                f.write( "{},{}\n".format( percentiles_to_write[i], ptl_values[i] ) )

        f_name_all_str = l_files[0].split("/")[-1]
        f_name_all_str = '-'.join( f_name_all_str.split("-")[:4] ) + "-cdf-values.csv.ln"

        with open(f_name_all_str, 'w+') as f:
            for i in range(len(ptl_ln_values)):
                f.write( "{},{}\n".format( percentiles_to_write[i], ptl_ln_values[i] ) )
    except Exception as e:
        print( "ERROR.")
        print( "Computing flat file percentiles over {} failed.".format(  l_files ) )
        print( all_percentiles )
        print( all_ln_percentiles )
        raise( e )
        

def merge_files(l_files: list, flat_files: list):
        assert False
        # TODO: handle flat file merge.
        with open(l_files[0], 'r') as f:
            N = int(float(f.readline().rstrip()))
            x_min = float(f.readline().rstrip())
            x_max = float(f.readline().rstrip())
            K1 = int(float(f.readline().rstrip()))
            moments = []
            log_moments = []
            for i in range(0, K1 + 1):
                moments.append(float(f.readline().rstrip()))
            log_x_min = float(f.readline().rstrip())
            log_x_max = float(f.readline().rstrip())
            K2 = int(float(f.readline().rstrip()))
            for i in range(0, K2 + 1):
                log_moments.append(float(f.readline().rstrip()))

        for filename in l_files[1:]:
            with open(filename, 'r') as f:
                N = N + int(float(f.readline().rstrip()))
                x_min = min(x_min, float(f.readline().rstrip()))
                x_max = max(x_max, float(f.readline().rstrip()))
                K1_tmp = int(float(f.readline().rstrip()))

                # TODO Maybe handle case where Ks are different for different sketch files
                if K1 != K1_tmp:
                    logging.error(filename + " and " + l_files[0] + " have different K1s")
                    raise ValueError(filename + " and " + l_files[0] + " have different K1s")

                for i in range(0, K1 + 1):
                    moments[i] += float(f.readline().rstrip())

                log_x_min = min(log_x_min, float(f.readline().rstrip()))
                log_x_max = max(log_x_max, float(f.readline().rstrip()))
                K2_tmp = int(float(f.readline().rstrip()))
                if K2 != K2_tmp:
                    logging.error(filename + " and " + l_files[0] + " have different K2s")
                    raise ValueError(filename + " and " + l_files[0] + " have different K2s")

                for i in range(0, K2 + 1):
                    log_moments[i] += float(f.readline().rstrip())

        for filename in flat_files:
            with open(filename, 'r') as f:
                for line in f:
                    value = float(line.strip())
                    N += 1
                    x_min = min(x_min, value)
                    x_max = max(x_max, value)
                    for i in range(0, 13):
                        tmp_value = value
                        tmp_value = math.pow( tmp_value, i )
                        moments[i] += tmp_value
                    log_value = math.log( value )
                    log_x_min = min( log_x_min, log_value )
                    log_x_max = max( log_x_max, log_value )
                    for i in range( 0, 13 ):
                        log_value = math.log( value )
                        log_value = math.pow( log_value, i )
                        log_moments[i] += log_value



        f_name = l_files[0]
        f_name_all = l_files[0].split('-')[:4]
        f_name_all.append('all')
        f_name_all_str = '-'.join(f_name_all)

        with open(f_name_all_str, 'w+') as f:
            f.write(str(N) + "\n")
            f.write(str('{}'.format(x_min)) + "\n")
            f.write(str('{}'.format(x_max)) + "\n")
            f.write(str(K1) + "\n")
            for i in range(0, K1+1):
                f.write(str('{}'.format(moments[i])) + "\n")
            f.write(str('{}'.format(log_x_min)) + "\n")
            f.write(str('{}'.format(log_x_max)) + "\n")
            f.write(str(K2) + "\n")
            for i in range(0, K2+1):
                f.write(str('{}'.format(log_moments[i])) + "\n")


if __name__ == "__main__":

    # Here, we need to check if the files are "flat" or sketch files.
    # For each event -> event, if one of them is a sketch than we must take all other
    # flat files and merge them into the sketch.
    # If they are all flat, then we can just merge them all together to compute the percentiles, no need to
    # to use the sketch library
    # Output should be merged sketch files or percentile files.
    sketchList = None
    flatlist = None

    if len(sys.argv) < 2:
        print( "Not enough args to create_cdfs.sh!")
        print( "{} logdir".format( sys.argv[0] ) )
        sys.exit( 1 )

    sketchList = glob.glob("{}/event-sketch*".format( sys.argv[1] ) )
    flatList = glob.glob( "{}/event-flat*".format( sys.argv[1]) )
    d_sketches = {}
    d_flats = {}
    assert not sketchList

    #for f in sketchList:
    #    subprocess.run(["chmod", "+r", f])
    #    f_split = f.split('-')
    #    try:
    #        src_loc = f_split[2]
    #        dst_loc = f_split[3]
    #        if src_loc not in d_sketches:
    #            d_sketches[src_loc] = {}
#
#            if dst_loc not in d_sketches[src_loc]:
#                d_sketches[src_loc][dst_loc] = [f]
#            else:
#                d_sketches[src_loc][dst_loc].append( f )
#
#        except Exception as e:
#            logging.INFO(e)
#            continue

    for f in flatList:
        subprocess.run(["chmod", "+r", f])
        if "/" in f:
            f_name = f.split("/")[-1]
        else:
            fname = f

        f_split = f_name.split('-')
        try:
            src_loc = f_split[2]
            dst_loc = f_split[3]
            if src_loc not in d_flats:
                d_flats[src_loc] = {}

            if dst_loc not in d_flats[src_loc]:
                d_flats[src_loc][dst_loc] = [ f ]
            else:
                d_flats[src_loc][dst_loc].append( f )

        except Exception as e:
            logging.INFO(e)
            continue

    #for src_loc in d_sketches:
    #    for dst_loc in d_sketches[src_loc]:
    #        if src_loc in d_flats and dst_loc in d_flats[src_loc]:
    #            merge_files( d_sketches[src_loc][dst_loc], d_flats[src_loc][dst_loc] )
    #        else:
    #            merge_files( d_sketches[src_loc][dst_loc], [] )

    for src_loc in d_flats:
        for dst_loc in d_flats[src_loc]:
            if src_loc not in d_sketches or dst_loc not in d_sketches[src_loc]:
                compute_flat_file_percentiles( d_flats[src_loc][dst_loc] )
