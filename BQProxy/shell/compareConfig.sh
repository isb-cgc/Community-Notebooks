#!/usr/bin/env bash

if [ "$#" -ne 1 ]; then
    echo "Must specify file to compare"
    exit
fi

CONFIG_PATH=$1

TMP_VERS=$(mktemp /tmp/vers.XXXXXXXXX)
TMP_SORT=$(mktemp /tmp/sort.XXXXXXXXX)
TMP_CURR=$(mktemp /tmp/curr.XXXXXXXXX)
TMP_LAST=$(mktemp /tmp/last.XXXXXXXXX)
TMP_DIFF=$(mktemp /tmp/diff.XXXXXXXXX)

cat < /dev/null > ${TMP_VERS}
VERS=`gsutil ls -a ${CONFIG_PATH}`
for VER in ${VERS}; do
  GEN=`echo ${VER} | sed s/.*#//`
  echo ${GEN} >> ${TMP_VERS}
done

VER_LEN=`cat ${TMP_VERS} | wc -l`

if (( ${VER_LEN} < 2 )); then
  echo "No diff: first version for " ${CONFIG_PATH}
  rm -f ${TMP_VERS} ${TMP_SORT} ${TMP_CURR} ${TMP_LAST} ${TMP_DIFF}
  exit
fi

cat ${TMP_VERS} | sort -n > ${TMP_SORT}
CURR=`tail -n 1 ${TMP_SORT}`
PENULT=`tail -n 2 ${TMP_SORT} | head -n 1`

(( CURR_SECS=(${CURR})/1000000 ))
(( PEN_SECS=(${PENULT})/1000000 ))

if [ ${OSTYPE} == 'darwin20' ]; then
    CURR_STR=`date -r ${CURR_SECS}`
    PEN_STR=`date -r ${PEN_SECS}`
else
    CURR_STR=`date -d @${CURR_SECS}`
    PEN_STR=`date -d @${PEN_SECS}`
fi

gsutil cp ${CONFIG_PATH}"#"${PENULT} ${TMP_LAST} > /dev/null 2>&1
gsutil cp ${CONFIG_PATH}"#"${CURR} ${TMP_CURR}  > /dev/null 2>&1

echo "Diff of previous (" ${PEN_STR} ") to current (" ${CURR_STR} ") for" ${CONFIG_PATH} ":"
diff ${TMP_LAST} ${TMP_CURR} > ${TMP_DIFF}

# The < and > mess up the tests:

while read -r LINE; do
    if [ ! -z `echo "${LINE}" | sed -e 's/<//' |  sed -e 's/>//' | grep -i "PASSWORD"` ]; then
        echo "PASSWORD REDACTED"
    elif [ ! -z `echo "${LINE}" | sed -e 's/<//' |  sed -e 's/>//' | grep -i "SECRET"` ]; then
        echo "SECRET REDACTED"
    elif [ ! -z `echo "${LINE}" | sed -e 's/<//' |  sed -e 's/>//' | grep -i "KEY"` ]; then
        echo "KEY REDACTED"
    elif [ ! -z `echo "${LINE}" | sed -e 's/<//' |  sed -e 's/>//' | grep -i "TOKEN"` ]; then
        echo "TOKEN REDACTED"
    else
        echo "${LINE}"
    fi
done < ${TMP_DIFF}

trap 'rm -f ${TMP_VERS} ${TMP_SORT} ${TMP_CURR} ${TMP_LAST} ${TMP_DIFF}' EXIT
