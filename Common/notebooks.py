"""

Copyright 2019, Institute for Systems Biology

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

"""

from google.cloud import bigquery
from google.cloud import storage
from google.cloud import exceptions
import shutil
import os
import requests
import copy
import urllib.parse as up
import time
import zipfile
import gzip
import threading
from json import loads as json_loads, dumps as json_dumps


def checkToken(aToken):
    """
    Used by pickColumns, below:
    """
    if ( aToken.find(';') >= 0 ):
        aList = aToken.split(';')
        aList.sort()
        newT = ''
        for bToken in aList:
            newT += bToken
            if ( len(newT) > 0 ): newT += ';'
        if ( newT[-1] == ';' ): newT = newT[:-1]
        return ( newT )

    elif ( aToken.find(',') >= 0 ):
        aList = aToken.split(',')
        aList.sort()
        newT = ''
        for bToken in aList:
            newT += bToken
            if ( len(newT) > 0 ): newT += ','
        if ( newT[-1] == ',' ): newT = newT[:-1]
        return ( newT )

    return ( aToken )

def pickColumns(tokenList):
    """
    Sheila's legacy pickColumns() Function
    For a list of tokens skip some and sort on others. Note that we do not do any pruning
    anymore. This function is retained for archival reasons.
    """

    ## original lists from Nov 2016 ...
    skipCols = [ 14, 17, 18, 21, 22, 23, 24, 26, 27, 29, 30, 43, 44, 57, 88, 89, 90, 91, 107 ]
    sortCols = [ 2, 28, 31 ]

    ## new lists from May 2017 ...
    skipCols = [ 17, 18, 21, 22, 23, 24, 25, 26, 27, 29, 30, 43, 44, 57, 88, 89, 90, 91, 96, 108 ]
    ## maybe we don't skip anything?
    skipCols = [ ]

    ## information that should be sorted for consistency, eg column #2 = Center,
    ## #14 = dbSNP_Val_Status, #28 = Validation_Method, #31 = Sequencer, #50 = Consequence, etc...
    sortCols = [ 2, 14, 28, 31, 50, 75, 85, 87, 109, 115, 116 ]
    ## new for June MAFs
    sortCols = [ 2, 14, 28, 31, 50, 51, 76, 86, 88, 110, 116, 117 ]
    ## new in Jan 2018 ... in some of the fields, the ORDER MATTERS!
    sortCols = [ ]

    newList = []

    for ii in range(len(tokenList)):
        if ii not in skipCols:
            if ii in sortCols:
                newList += [ checkToken(tokenList[ii]) ]
            else:
                newList += [ tokenList[ii] ]

    return newList

def write_MAFs(tumor, mutCalls, hdrPick, mutCallers, do_logging):
    """
    Sheila's function to write out MAFs for merging
    Original MAF table merged identical results from the different callers. This is the function
    to write out the results from the merged dictionaries.
    """
    with open("MAFLOG-WRITE-{}.txt".format(tumor), 'w') as log_file:
        outFilename = "mergeA." + tumor + ".maf"

        with open(outFilename, 'w') as fhOut:

            outLine = ''
            for aT in hdrPick:
                outLine += aT + '\t'
            fhOut.write("%s\n" % outLine[:-1])

            histCount = [0] * 10

            mutPrints = mutCalls.keys()
            log_file.write(" --> total # of mutPrints : {}\n".format(len(mutPrints)))

            for aPrint in mutPrints:

                if do_logging: log_file.write(" ")
                if do_logging: log_file.write(" looping over mutPrints ... {}\n".format(str(aPrint)))
                numCalls = len(mutCalls[aPrint])
                if do_logging: log_file.write("     numCalls = {}\n".format(numCalls))
                histCount[numCalls] += 1
                outLine = ''
                if (numCalls > 0):
                    if do_logging: log_file.write("     # of features = {}\n".format(len(mutCalls[aPrint][0])))
                    if do_logging: log_file.write("{}\n".format(str(mutCalls[aPrint][0])))

                    ## for each feature we want to see if the different callers
                    ## came up with different outputs ... so we create a vector
                    ## of all of the outputs [v], and a vector of only the unique
                    ## outputs [u]
                    for kk in range(len(mutCalls[aPrint][0])):
                        u = []
                        v = []
                        for ii in range(len(mutCalls[aPrint])):
                            if (mutCalls[aPrint][ii][kk] not in u):
                                u += [mutCalls[aPrint][ii][kk]]
                            v += [mutCalls[aPrint][ii][kk]]
                        if (len(u) > 1):
                            if do_logging: log_file.write(
                                "{} {} {} {}\n".format(str(kk), str(hdrPick[kk]), len(u), str(v)))

                        ## if we have nothing, then it's a blank field
                        if (len(v) == 0):
                            outLine += "\t"

                        ## if we only have one value, then just write that
                        elif (len(u) == 1 or len(v) == 1):
                            outLine += "%s\t" % v[0]

                        ## otherwise we need to write out the the values in the
                        ## order of the callers ...
                        else:
                            if do_logging: log_file.write(" looping over {}\n".format(mutCallers))
                            if do_logging: log_file.write("{}\n".format(str(u)))
                            if do_logging: log_file.write("{}\n".format(str(v)))
                            for c in mutCallers:
                                for ii in range(len(mutCalls[aPrint])):
                                    ## 3rd from the last feature is the 'caller'
                                    if (mutCalls[aPrint][ii][-3] == c):
                                        if do_logging: log_file.write("         found ! {}\n".format(str(c)))
                                        outLine += "%s|" % v[ii]
                            outLine = outLine[:-1] + "\t"
                    fhOut.write("%s\n" % outLine[:-1])

    return histCount


def read_MAFs(tumor_type, maf_list, program_prefix, extra_cols, col_count,
              do_logging, key_fields, first_token, file_info_func):
    """
    Sheila's function to read MAFs for merging.
    Original MAF table merged identical results from the different callers. This is the function to read
    in results and build merged dictionaries.
    """
    hdrPick = None
    mutCalls = {}
    with open("MAFLOG-READ-{}.txt".format(tumor_type), 'w') as log_file:

        for aFile in maf_list:
            file_info_list = file_info_func(aFile, program_prefix)
            if file_info_list[0] != (program_prefix + tumor_type):
                continue
            try:
                if do_logging: log_file.write(" Next file is <%s> \n" % aFile)
                toss_zip = False
                if aFile.endswith('.gz'):
                    dir_name = os.path.dirname(aFile)
                    use_file_name = aFile[:-3]
                    log_file.write("Uncompressing {}\n".format(aFile))
                    with gzip.open(aFile, "rb") as gzip_in:
                        with open(use_file_name, "wb") as uncomp_out:
                            shutil.copyfileobj(gzip_in, uncomp_out)
                    toss_zip = True
                else:
                    use_file_name = aFile

                log_file.write(" opening input file {}\n".format(use_file_name))
                log_file.write(" fileInfo : {}\n".format(str(file_info_list)))

                if os.path.isfile(use_file_name):
                    with open(use_file_name, 'r') as fh:
                        key_indices = []
                        for aLine in fh:
                            if aLine.startswith("#"):
                                continue
                            if aLine.startswith(first_token):
                                aLine = aLine.strip()
                                hdrTokens = aLine.split('\t')
                                if len(hdrTokens) != col_count:
                                    print("ERROR: incorrect number of header tokens! {} vs {}".format(col_count,
                                                                                                      len(hdrTokens)))
                                    print(hdrTokens)
                                    raise Exception()
                                    ## We no longer prune or sort columns, so assignment is now direct:
                                hdrPick = copy.copy(hdrTokens)
                                ## hdrPick = pickColumns ( hdrTokens )
                                ## since we're not skipping any columns, we should have 120 at this point
                                ## print " --> len(hdrPick) = ", len(hdrPick)
                                hdrPick += extra_cols
                                ## and 124 at this point ...
                                ## print " --> after adding a few more fields ... ", len(hdrPick)
                                for keef in key_fields:
                                    key_indices.append(hdrPick.index(keef))
                                continue

                            if hdrPick is None:
                                print("ERROR: Header row not found")
                                raise Exception()

                            aLine = aLine.strip()
                            tokenList = aLine.split('\t')
                            if len(tokenList) != len(hdrTokens):
                                print(
                                "ERROR: incorrect number of tokens! {} vs {}".format(len(tokenList), len(hdrTokens)))
                                raise Exception()

                            # This creates a key for a dictionary for each mutation belonging to a tumor sample:

                            mpl = [tokenList[x] for x in key_indices]
                            mutPrint = tuple(mpl)
                            if do_logging: log_file.write("{}\n".format(str(mutPrint)))

                            # list for each key:
                            if mutPrint not in mutCalls:
                                mutCalls[mutPrint] = []

                            ##infoList = pickColumns(tokenList) + file_info_list
                            ## Again, no longer pruning columns!
                            infoList = tokenList + file_info_list
                            if len(infoList) != len(hdrPick):
                                print(" ERROR: inconsistent number of tokens!")
                                raise Exception()

                            if do_logging: log_file.write(" --> infoList : {}\n".format(str(infoList)))
                            mutCalls[mutPrint] += [infoList]
                            if do_logging: log_file.write(
                                " --> len(mutCalls[mutPrint]) = {}\n".format(len(mutCalls[mutPrint])))

                        log_file.write(" --> done with this file ... {}\n".format(len(mutCalls)))
                else:
                    # If previous job died a nasty death, following finally statement may not get run, causing
                    # file manifest to hold onto a previously unzipped file that gets deleted. Catch that
                    # problem!
                    print('{} was not found'.format(use_file_name))
            finally:
                if toss_zip and os.path.isfile(use_file_name):
                    os.remove(use_file_name)

        log_file.write("\n")
        log_file.write(" DONE READING MAFs ... \n")
        log_file.write("\n")
    return mutCalls, hdrPick


def concat_all_merged_files(all_files, one_big_tsv):
    """
    Concatenate all Merged Files
    Gather up all merged files and glue them into one big one.
    """

    print("building {}".format(one_big_tsv))
    first = True
    header_id = None
    with open(one_big_tsv, 'w') as outfile:
        for filename in all_files:
            with open(filename, 'r') as readfile:
                for line in readfile:
                    if line.startswith('#'):
                        continue
                    split_line = line.split("\t")
                    if first:
                        header_id = split_line[0]
                        print("Header starts with {}".format(header_id))
                        first = False
                    if not line.startswith(header_id) or first:
                        outfile.write(line)

    print("finished building {}".format(one_big_tsv))
    return


def build_pull_list_with_bq(manifest_table, indexd_table, project, tmp_dataset, tmp_bq,
                            tmp_bucket, tmp_bucket_file, local_file, do_batch):
    """
    IndexD using BQ Tables
    GDC provides us a file that allows us to not have to pound the IndexD API; we build a BQ table.
    Use it to resolve URIs
    """
    #
    # If we are using bq to build a manifest, we can use that table to build the pull list too!
    #

    sql = pull_list_builder_sql(manifest_table, indexd_table)
    success = generic_bq_harness(sql, tmp_dataset, tmp_bq, do_batch, True)
    if not success:
        return False
    success = bq_to_bucket_tsv(tmp_bq, project, tmp_dataset, tmp_bucket, tmp_bucket_file, do_batch, False)
    if not success:
        return False
    bucket_to_local(tmp_bucket, tmp_bucket_file, local_file)
    return True

def pull_list_builder_sql(manifest_table, indexd_table):
    """
    Generates SQL for above function
    """
    return '''
    SELECT b.gs_url
    FROM `{0}` as a JOIN `{1}` as b ON a.id = b.id
    '''.format(manifest_table, indexd_table)


def get_the_bq_manifest(file_table, filter_dict, max_files, project, tmp_dataset, tmp_bq,
                        tmp_bucket, tmp_bucket_file, local_file, do_batch):
    """
    Build a Manifest File Using ISB-CGC File Tables. This duplicates the manifest file returned by
    GDC API, but uses the BQ file table as the data source.
    """

    sql = manifest_builder_sql(file_table, filter_dict, max_files)
    success = generic_bq_harness(sql, tmp_dataset, tmp_bq, do_batch, True)
    if not success:
        return False
    success = bq_to_bucket_tsv(tmp_bq, project, tmp_dataset, tmp_bucket, tmp_bucket_file, do_batch, True)
    if not success:
        return False
    bucket_to_local(tmp_bucket, tmp_bucket_file, local_file)
    return True


def manifest_builder_sql(file_table, filter_dict_list, max_files):
    """
    Generates SQL for above function
    """
    filter_list = []
    where_clause = "WHERE {} = '{}'"
    and_clause = "AND {} = '{}'"

    for filter in filter_dict_list:
        for key, val in filter.items():
            if len(filter_list) == 0:
                filter_list.append(where_clause.format(key, val))
            else:
                filter_list.append(and_clause.format(key, val))
    all_filters = ' '.join(filter_list)

    limit_clause = "" if max_files is None else "LIMIT {}".format(max_files)

    return '''
    SELECT file_gdc_id as id,
           file_name as filename,
           md5sum as md5,
           file_size as size,
           file_state as state
    FROM `{0}`
    {1} {2}
    '''.format(file_table, all_filters, limit_clause)


def bq_to_bucket_tsv(src_table, project, dataset, bucket_name, bucket_file, do_batch, do_header):
    """
    Get a BQ Result to a Bucket TSV file
    Export BQ table to a cloud bucket
    """
    client = bigquery.Client()
    destination_uri = "gs://{}/{}".format(bucket_name, bucket_file)
    dataset_ref = client.dataset(dataset, project=project)
    table_ref = dataset_ref.table(src_table)

    job_config = bigquery.ExtractJobConfig()
    if do_batch:
        job_config.priority = bigquery.QueryPriority.BATCH
    location = 'US'
    job_config.field_delimiter = '\t'
    job_config.print_header = do_header

    extract_job = client.extract_table(table_ref, destination_uri, location="US", job_config=job_config)

    # Query
    job_state = 'NOT_STARTED'
    while job_state != 'DONE':
        extract_job = client.get_job(extract_job.job_id, location=location)
        print('Job {} is currently in state {}'.format(extract_job.job_id, extract_job.state))
        job_state = extract_job.state
        time.sleep(5)
    print('Job {} is done with status'.format(extract_job.job_id))

    extract_job = client.get_job(extract_job.job_id, location=location)
    print('Job {} is done'.format(extract_job.job_id))
    if extract_job.error_result is not None:
        print('Error result!! {}'.format(extract_job.error_result))
        return False
    return True


def bucket_to_local(bucket_name, bucket_file, local_file):
    """
    Get a Bucket File to Local
    Export a cloud bucket file to the local filesystem
    No leading / in bucket_file name!!
    """
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(bucket_file)  # no leading / in blob name!!
    blob.download_to_filename(local_file)
    return

def build_manifest_filter(filter_dict_list):
    """
    Build a manifest filter using the list of filter items you can get from a GDC search
    """
    # Note the need to double up the "{{" to make the format command happy:
    filter_template = '''
    {{
        "op": "in",
        "content": {{
            "field": "{0}",
            "value": [
                "{1}"
            ]
        }}
    }}
    '''

    prefix = '''
    {
      "op": "and",
      "content": [

    '''
    suffix = '''
      ]
    }
    '''

    filter_list = []
    for kv_pair in filter_dict_list:
        for k, v in kv_pair.items():
            if len(filter_list) > 0:
                filter_list.append(',\n')
            filter_list.append(filter_template.format(k, v.rstrip('\n')))

    whole_filter = [prefix] + filter_list + [suffix]
    return ''.join(whole_filter)


def get_the_manifest(filter_string, api_url, manifest_file, max_files=None):
    """
    This function takes a JSON filter string and uses it to download a manifest from GDC
    """

    #
    # 1) When putting the size and "return_type" : "manifest" args inside a POST document, the result comes
    # back as JSON, not the manifest format.
    # 2) Putting the return type as parameter in the URL while doing a post with the filter just returns
    # every file they own (i.e. the filter in the POST doc is ignored, probably to be expected?).
    # 3) Thus, put the filter in a GET request.
    #

    num_files = max_files if max_files is not None else 100000
    request_url = '{}?filters={}&size={}&return_type=manifest'.format(api_url,
                                                                      up.quote(filter_string),
                                                                      num_files)

    resp = requests.request("GET", request_url)

    if resp.status_code == 200:
        mfile = manifest_file
        with open(mfile, mode='wb') as localfile:
            localfile.write(resp.content)
        print("Wrote out manifest file: {}".format(mfile))
        return True
    else:
        print()
        print("Request URL: {} ".format(request_url))
        print("Problem downloading manifest file. HTTP Status Code: {}".format(resp.status_code))
        print("HTTP content: {}".format(resp.content))
        return False


def create_clean_target(local_files_dir):
    """
    GDC download client builds a tree of files in directories. This routine clears the tree out if it exists.
    """

    if os.path.exists(local_files_dir):
        print("deleting {}".format(local_files_dir))
        try:
            shutil.rmtree(local_files_dir)
        except OSError as e:
            print("Error: %s - %s." % (e.filename, e.strerror))

        print("done {}".format(local_files_dir))

    if not os.path.exists(local_files_dir):
        os.makedirs(local_files_dir)


def build_pull_list_with_indexd(manifest_file, indexd_max, indexd_url, local_file):
    """
    Generate a list of gs:// urls to pull down from a manifest, using indexD
    """

    # Parse the manifest file for uids, pull out other data too as a sanity check:

    manifest_vals = {}
    with open(manifest_file, 'r') as readfile:
        first = True
        for line in readfile:
            if first:
                first = False
                continue
            split_line = line.rstrip('\n').split("\t")
            manifest_vals[split_line[0]] = {
                'filename': split_line[1],
                'md5': split_line[2],
                'size': int(split_line[3])
            }

    # Use IndexD to map to Google bucket URIs. Batch up IndexD calls to reduce API load:

    print("Pulling {} files from buckets...".format(len(manifest_vals)))
    max_per_call = indexd_max
    indexd_results = {}
    num_full_calls = len(manifest_vals) // max_per_call  # Python 3: // is classic integer floor!
    num_final_call = len(manifest_vals) % max_per_call
    all_calls = num_full_calls + (1 if (num_final_call > 0) else 0)
    uuid_list = []
    call_count = 0
    for uuid in manifest_vals:
        uuid_list.append(uuid)
        list_len = len(uuid_list)
        is_last = (num_final_call > 0) and (call_count == num_full_calls)
        if list_len == max_per_call or (is_last and list_len == num_final_call):
            request_url = '{}{}'.format(indexd_url, ','.join(uuid_list))
            resp = requests.request("GET", request_url)
            call_count += 1
            print ("completed {} of {} calls to IndexD".format(call_count, all_calls))
            file_dict = json_loads(resp.text)
            for i in range(0, list_len):
                call_id = uuid_list[i]
                curr_record = file_dict['records'][i]
                curr_id = curr_record['did']
                manifest_record = manifest_vals[curr_id]
                indexd_results[curr_id] = curr_record
                if curr_record['did'] != curr_id or \
                                curr_record['hashes']['md5'] != manifest_record['md5'] or \
                                curr_record['size'] != manifest_record['size']:
                    raise Exception(
                        "Expected data mismatch! {} vs. {}".format(str(curr_record), str(manifest_record)))
            uuid_list.clear()

    # Create a list of URIs to pull, write to specified file:

    with open(local_file, mode='w') as pull_list_file:
        for uid, record in indexd_results.items():
            url_list = record['urls']
            gs_urls = [g for g in url_list if g.startswith('gs://')]
            if len(gs_urls) != 1:
                raise Exception("More than one gs:// URI! {}".format(str(gs_urls)))
            pull_list_file.write(gs_urls[0] + '\n')

    return


class BucketPuller(object):
    """Multithreaded  bucket puller"""
    def __init__(self, thread_count):
        self._lock = threading.Lock()
        self._threads = []
        self._total_files = 0
        self._read_files = 0
        self._thread_count = thread_count
        self._bar_bump = 0

    def __str__(self):
        return "BucketPuller"

    def reset(self):
        self._threads.clear()
        self._total_files = 0
        self._read_files = 0
        self._bar_bump = 0

    def pull_from_buckets(self, pull_list, local_files_dir):
        """
          List of all project IDs
        """
        self._total_files = len(pull_list)
        self._bar_bump = self._total_files // 100
        if self._bar_bump == 0:
            self._bar_bump = 1
        size = self._total_files // self._thread_count
        size = size if self._total_files % self._thread_count == 0 else size + 1
        chunks = [pull_list[pos:pos + size] for pos in range(0, self._total_files, size)]
        for i in range(0, self._thread_count):
            th = threading.Thread(target=self._pull_func, args=(chunks[i], local_files_dir))
            self._threads.append(th)

        for i in range(0, self._thread_count):
            self._threads[i].start()

        for i in range(0, self._thread_count):
            self._threads[i].join()

        print_progress_bar(self._read_files, self._total_files)
        return

    def _pull_func(self, pull_list, local_files_dir):
        storage_client = storage.Client()
        for url in pull_list:
            path_pieces = up.urlparse(url)
            dir_name = os.path.dirname(path_pieces.path)
            make_dir = "{}{}".format(local_files_dir, dir_name)
            os.makedirs(make_dir, exist_ok=True)
            bucket = storage_client.bucket(path_pieces.netloc)
            blob = bucket.blob(path_pieces.path[1:])  # drop leading / from blob name
            full_file = "{}{}".format(local_files_dir, path_pieces.path)
            blob.download_to_filename(full_file)
            self._bump_progress()

    def _bump_progress(self):

        with self._lock:
            self._read_files += 1
            if (self._read_files % self._bar_bump) == 0:
                print_progress_bar(self._read_files, self._total_files)


def pull_from_buckets(pull_list, local_files_dir):
    """
    Run the "Download Client", which now justs hauls stuff out of the cloud buckets
    """

    # Parse the manifest file for uids, pull out other data too as a sanity check:

    num_files = len(pull_list)
    print("Begin {} bucket copies...".format(num_files))
    storage_client = storage.Client()
    copy_count = 0
    for url in pull_list:
        path_pieces = up.urlparse(url)
        dir_name = os.path.dirname(path_pieces.path)
        make_dir = "{}{}".format(local_files_dir, dir_name)
        os.makedirs(make_dir, exist_ok=True)
        bucket = storage_client.bucket(path_pieces.netloc)
        blob = bucket.blob(path_pieces.path[1:])  # drop leading / from blob name
        full_file = "{}{}".format(local_files_dir, path_pieces.path)
        blob.download_to_filename(full_file)
        copy_count += 1
        if (copy_count % 10) == 0:
            print_progress_bar(copy_count, num_files)
    print_progress_bar(num_files, num_files)

def build_file_list(local_files_dir):
    """
    Build the File List
    Using the tree of downloaded files, we build a file list. Note that we see the downloads
    (using the GDC download tool) bringing along logs and annotation.txt files, which we
    specifically omit.
    """
    print("building file list from {}".format(local_files_dir))
    all_files = []
    for path, dirs, files in os.walk(local_files_dir):
        if not path.endswith('logs'):
            for f in files:
                if f != 'annotations.txt':
                    if f.endswith('parcel'):
                        raise Exception
                    all_files.append('{}/{}'.format(path, f))

    print("done building file list from {}".format(local_files_dir))
    return all_files


def generic_bq_harness(sql, target_dataset, dest_table, do_batch, do_replace):
    """
    Handles all the boilerplate for running a BQ job
    """

    client = bigquery.Client()
    job_config = bigquery.QueryJobConfig()
    if do_batch:
        job_config.priority = bigquery.QueryPriority.BATCH
    if do_replace:
        job_config.write_disposition = "WRITE_TRUNCATE"

    target_ref = client.dataset(target_dataset).table(dest_table)
    job_config.destination = target_ref
    print(target_ref)
    location = 'US'

    # API request - starts the query
    query_job = client.query(sql, location=location, job_config=job_config)

    # Query
    job_state = 'NOT_STARTED'
    while job_state != 'DONE':
        query_job = client.get_job(query_job.job_id, location=location)
        print('Job {} is currently in state {}'.format(query_job.job_id, query_job.state))
        job_state = query_job.state
        print(query_job)
        time.sleep(5)
    print('Job {} is done with status'.format(query_job.job_id))

    query_job = client.get_job(query_job.job_id, location=location)
    print('Job {} is done'.format(query_job.job_id))
    if query_job.error_result is not None:
        print('Error result!! {}'.format(query_job.error_result))
        return False
    return True


def upload_to_bucket(target_tsv_bucket, target_tsv_file, local_tsv_file):
    """
    Upload to Google Bucket
    Large files have to be in a bucket for them to be ingested into Big Query. This does this.
    """
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(target_tsv_bucket)
    blob = bucket.blob(target_tsv_file)
    print(blob.name)
    blob.upload_from_filename(local_tsv_file)


def csv_to_bq(schema, csv_uri, dataset_id, targ_table, do_batch):
    client = bigquery.Client()

    dataset_ref = client.dataset(dataset_id)
    job_config = bigquery.LoadJobConfig()
    if do_batch:
        job_config.priority = bigquery.QueryPriority.BATCH

    schema_list = []
    for dict in schema:
        schema_list.append(bigquery.SchemaField(dict['name'], dict['type'].upper(),
                                                mode='NULLABLE', description=dict['description']))

    job_config.schema = schema_list
    job_config.skip_leading_rows = 1
    job_config.source_format = bigquery.SourceFormat.CSV
    job_config.write_disposition = bigquery.WriteDisposition.WRITE_TRUNCATE
    # Can make the "CSV" file a TSV file using this:
    job_config.field_delimiter = '\t'

    load_job = client.load_table_from_uri(
        csv_uri,
        dataset_ref.table(targ_table),
        job_config=job_config)  # API request
    print('Starting job {}'.format(load_job.job_id))

    location = 'US'
    job_state = 'NOT_STARTED'
    while job_state != 'DONE':
        load_job = client.get_job(load_job.job_id, location=location)
        print('Job {} is currently in state {}'.format(load_job.job_id, load_job.state))
        job_state = load_job.state
        time.sleep(5)
    print('Job {} is done with status'.format(load_job.job_id))

    load_job = client.get_job(load_job.job_id, location=location)
    print('Job {} is done'.format(load_job.job_id))
    if load_job.error_result is not None:
        print('Error result!! {}'.format(load_job.error_result))
        for err in load_job.errors:
            print(err)
        return False

    destination_table = client.get_table(dataset_ref.table(targ_table))
    print('Loaded {} rows.'.format(destination_table.num_rows))
    return True


def concat_all_files(all_files, one_big_tsv, program_prefix, extra_cols, file_info_func, split_more_func):
    """
    Concatenate all Files
    Gather up all files and glue them into one big one. The file name and path often include features
    that we want to add into the table. The provided file_info_func returns a list of elements from
    the file path, and the extra_cols list maps these to extra column names. Note if file is zipped,
    we unzip it, concat it, then toss the unzipped version.
    THIS VERSION OF THE FUNCTION USES THE FIRST LINE OF THE FIRST FILE TO BUILD THE HEADER LINE!
    """
    print("building {}".format(one_big_tsv))
    first = True
    header_id = None
    hdr_line = None
    with open(one_big_tsv, 'w') as outfile:
        for filename in all_files:
            toss_zip = False
            if filename.endswith('.zip'):
                dir_name = os.path.dirname(filename)
                print("Unzipping {}".format(filename))
                with zipfile.ZipFile(filename, "r") as zip_ref:
                    zip_ref.extractall(dir_name)
                use_file_name = filename[:-4]
                toss_zip = True
            elif filename.endswith('.gz'):
                dir_name = os.path.dirname(filename)
                use_file_name = filename[:-3]
                print("Uncompressing {}".format(filename))
                with gzip.open(filename, "rb") as gzip_in:
                    with open(use_file_name, "wb") as uncomp_out:
                        shutil.copyfileobj(gzip_in, uncomp_out)
                toss_zip = True
            else:
                use_file_name = filename
            if os.path.isfile(use_file_name):
                with open(use_file_name, 'r') as readfile:
                    file_info_list = file_info_func(use_file_name, program_prefix)
                    for line in readfile:
                        if line.startswith('#'):
                            continue
                        split_line = line.rstrip('\n').split("\t")
                        if first:
                            for col in extra_cols:
                                split_line.append(col)
                            header_id = split_line[0]
                            hdr_line = split_line
                            print("Header starts with {}".format(header_id))
                        else:
                            for i in range(len(extra_cols)):
                                split_line.append(file_info_list[i])
                        if not line.startswith(header_id) or first:
                            if split_more_func is not None:
                                split_line = split_more_func(split_line, hdr_line, first)
                            outfile.write('\t'.join(split_line))
                            outfile.write('\n')
                        first = False
            else:
                print('{} was not found'.format(use_file_name))

            if toss_zip and os.path.isfile(use_file_name):
                os.remove(use_file_name)

    return


def build_combined_schema(scraped, augmented, typing_tups, holding_list, holding_dict):
    """
    Merge schema descriptions (if any) and ISB-added descriptions with inferred type data
    """
    schema_list = []
    if scraped is not None:
        with open(scraped, mode='r') as scraped_hold_list:
            schema_list = json_loads(scraped_hold_list.read())

    with open(augmented, mode='r') as augment_list:
        augment_list = json_loads(augment_list.read())

    full_schema_dict = {}
    for elem in schema_list:
        full_schema_dict[elem['name']] = elem
    for elem in augment_list:
        full_schema_dict[elem['name']] = elem

    #
    # Need to create two things: A full schema dictionary to update the final
    # table, and a typed list for the initial TSV import:
    #

    typed_schema = []
    for tup in typing_tups:
        if tup[0] in full_schema_dict:
            use_type = tup[1]
            existing = full_schema_dict[tup[0]]
            existing['type'] = use_type
            typed_schema.append(existing)
        else:
            no_desc = {
                "name": tup[0],
                "type": tup[1],
                "description": "No description"
            }
            typed_schema.append(no_desc)
    with open(holding_list, mode='w') as schema_hold_list:
        schema_hold_list.write(json_dumps(typed_schema))

    with open(holding_dict, mode='w') as schema_hold_dict:
        schema_hold_dict.write(json_dumps(full_schema_dict))

    return True

def typing_tups_to_schema_list(typing_tups, holding_list):
    #
    # Need to create a typed list for the initial TSV import:
    #

    typed_schema = []
    for tup in typing_tups:
        no_desc = {
            "name": tup[0],
            "type": tup[1],
            "description": "No description"
        }
        typed_schema.append(no_desc)
    with open(holding_list, mode='w') as schema_hold_list:
        schema_hold_list.write(json_dumps(typed_schema))

    return True

def update_schema(target_dataset, dest_table, schema_dict_loc):
    """
    Update the Schema of a Table
    Final derived table needs the schema descriptions to be installed.
    """

    with open(schema_dict_loc, mode='r') as schema_hold_dict:
        full_schema = json_loads(schema_hold_dict.read())

    client = bigquery.Client()
    table_ref = client.dataset(target_dataset).table(dest_table)
    table = client.get_table(table_ref)
    orig_schema = table.schema
    new_schema = []
    for old_sf in orig_schema:
        new_desc = full_schema[old_sf.name]['description']
        new_sf = bigquery.SchemaField(old_sf.name, old_sf.field_type, description=new_desc)
        new_schema.append(new_sf)
    table.schema = new_schema
    table = client.update_table(table, ["schema"])
    return True

def update_description(target_dataset, dest_table, desc):
    """
    Update the Description of a Table¶
    Final derived table needs a description
    """
    client = bigquery.Client()
    table_ref = client.dataset(target_dataset).table(dest_table)
    table = client.get_table(table_ref)
    table.description = desc
    table = client.update_table(table, ["description"])
    return True



def delete_table_bq_job(target_dataset, delete_table):
    client = bigquery.Client()
    table_ref = client.dataset(target_dataset).table(delete_table)
    try:
        client.delete_table(table_ref)
        print('Table {}:{} deleted'.format(target_dataset, delete_table))
    except exceptions.NotFound as ex:
        print('Table {}:{} was not present'.format(target_dataset, delete_table))

    return True


def confirm_google_vm():
    metadata_url = "http://metadata.google.internal/computeMetadata/v1/instance/id"
    meta_header = {"Metadata-Flavor": "Google"}

    try:
        resp = requests.request("GET", metadata_url, headers=meta_header)
    except Exception as ex:
        print("Not a Google VM: {}".format(ex))
        return False

    if resp.status_code == 200:
        return True
    else:
        print("Not a Google VM: {}".format(resp.status_code))
        return False


def print_progress_bar(iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█'):
    """
    Ripped from Stack Overflow.
    https://stackoverflow.com/questions/3173320/text-progress-bar-in-the-console
    H/T to Greenstick: https://stackoverflow.com/users/2206251/greenstick

    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end='\r')
    # Print New Line on Complete
    if iteration == total:
        print()
    return

def transfer_schema(target_dataset, dest_table, source_dataset, source_table):
    """
    Transfer description of schema from e.g. table to view

    Note, to get this working on a fresh Google VM, I do this:

    sudo apt-get install python3-venv
    python3 -m venv bqEnv
    source bqEnv/bin/activate
    python3 -m pip install google-api-python-client
    python3 -m pip install google-cloud-storage
    python3 -m pip install google-cloud-bigquery

    TDS = "view_data_set"
    DTAB = "view_name"
    SDS = "table_data_set"
    STAB = "table_name"
    transfer_schema(TDS, DTAB, SDS, STAB)

    """

    client = bigquery.Client()
    src_table_ref = client.dataset(source_dataset).table(source_table)
    trg_table_ref = client.dataset(target_dataset).table(dest_table)
    src_table = client.get_table(src_table_ref)
    trg_table = client.get_table(trg_table_ref)
    src_schema = src_table.schema
    trg_schema = []
    for src_sf in src_schema:
        trg_sf = bigquery.SchemaField(src_sf.name, src_sf.field_type, description=src_sf.description)
        trg_schema.append(trg_sf)
    trg_table.schema = trg_schema
    client.update_table(trg_table, ["schema"])
    return True

def list_schema(source_dataset, source_table):
    """
    List schema
    """

    client = bigquery.Client()
    src_table_ref = client.dataset(source_dataset).table(source_table)
    src_table = client.get_table(src_table_ref)
    src_schema = src_table.schema
    for src_sf in src_schema:
        print(src_sf.name, src_sf.field_type, src_sf.description)
    return True
