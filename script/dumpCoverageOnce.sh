#!/bin/zsh

if [ $# -ne 4 ]; then
    echo "Usage: dumpCoverageOnce.sh <pkg_name> <outdir> <index> <path_to_project_root>"
    exit 1
fi

PKG=$1
OUT=$2
INDEX=$3
PROJECT_ROOT=$4
COVDIR="${OUT}/coverage${INDEX}"
ORIGINAL_DIR=`pwd`

adb shell am broadcast -a intent.END_COVERAGE

if [ ! -d $COVDIR ]; then
    mkdir $COVDIR
fi

adb pull "/sdcard/Android/data/${PKG}/files/coverage.ec" "${COVDIR}/coverage.ec"

if [ ! -d "${PROJECT_ROOT}/app/coverage" ]; then
    mkdir "${PROJECT_ROOT}/app/coverage"
fi

cp "${COVDIR}/coverage.ec" ${PROJECT_ROOT}/app/coverage/
cd ${PROJECT_ROOT}
./gradlew jacocoInstrumenterReport -q
cd ${ORIGINAL_DIR}
cp ${PROJECT_ROOT}/app/build/reports/jacoco/jacocoInstrumenterReport/jacocoInstrumenterReport.xml "${COVDIR}/coverage.xml"