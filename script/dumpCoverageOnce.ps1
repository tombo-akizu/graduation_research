if ($args.Count -lt 4) {
    echo "Usage: dumpCoverageOnce.ps1 <pkg_name> <outdir> <index> <path_to_project_root>"
    exit
}
$pkg = $args[0]
$out = $args[1]
$index = $args[2]
$project_root = $args[3]

adb shell am broadcast -a intent.END_COVERAGE
if (-not (Test-Path "${out}/coverage${index}")) {
    mkdir "${out}/coverage${index}"
}
adb pull "/sdcard/Android/data/${pkg}/files/coverage.ec" "${out}/coverage${index}/coverage.ec"
if (-not (Test-Path "${project_root}/app/coverage")) {
    mkdir "${project_root}/app/coverage"
}
cp "${out}/coverage${index}/coverage.ec" "${project_root}/app/coverage/"
Push-Location -Path ${project_root}
./gradlew jacocoInstrumenterReport -q
Pop-Location
cp "${project_root}/app/build/reports/jacoco/jacocoInstrumenterReport/jacocoInstrumenterReport.xml" "${out}/coverage${index}/coverage.xml"