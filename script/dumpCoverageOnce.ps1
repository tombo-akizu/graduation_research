if ($args.Count -lt 3) {
    echo "Usage: dumpCoverageOnce.ps1 <pkg_name> <outdir> <index>"
    exit
}
$pkg = $args[0]
$out = $args[1]
$index = $args[2]
adb shell am broadcast -a intent.END_COVERAGE
if (-not (Test-Path "${out}/coverage${index}")) {
    mkdir "${out}/coverage${index}"
}
adb pull "/sdcard/Android/data/${pkg}/files/coverage.ec" "${out}/coverage${index}/coverage.ec"
if (-not (Test-Path "./project/app/coverage")) {
    mkdir "./project/app/coverage"
}
cp "${out}/coverage${index}/coverage.ec" ./project/app/coverage/
cd ./project
./gradlew jacocoInstrumenterReport -q
cd ..
cp ./project/app/build/reports/jacoco/jacocoInstrumenterReport/jacocoInstrumenterReport.xml "${out}/coverage${index}/coverage.xml"