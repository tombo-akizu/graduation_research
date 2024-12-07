#!/bin/zsh

if [ $# -ne 3 ]; then
    echo "Usage: dumpCoverageOnce.sh <pkg_name> <outdir> <index>"
    exit 1
fi

PKG=$1
OUT=$2
INDEX=$3
COVDIR="${OUT}/coverage${INDEX}"

adb shell am broadcast -a intent.END_COVERAGE

if [ ! -d $COVDIR ]; then
    mkdir $COVDIR
fi

adb pull "/sdcard/Android/data/${PKG}/files/coverage.ec" "${COVDIR}/coverage.ec"

if [ ! -d "./project/app/coverage" ]; then
    mkdir "./project/app/coverage"
fi

cp "${COVDIR}/coverage.ec" ./project/app/coverage/
cd ./project
./gradlew jacocoInstrumenterReport -q
cd ..
cp ./project/app/build/reports/jacoco/jacocoInstrumenterReport/jacocoInstrumenterReport.xml "${COVDIR}/coverage.xml"