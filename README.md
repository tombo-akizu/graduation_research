```
adb: error: failed to stat remote object '/sdcard/Android/data/com.serwylo.lexica/files/coverage.ec': No such file or directory
```
AVDのバージョンが問題だった。  
API 25で動作することを確認。  
API 34で本エラーが発生。  


```
cp: ./project/app/build/reports/jacoco/jacocoInstrumenterReport/jacocoInstrumenterReport.xml: No such file or directory
```
COSMOのカバレッジ集計用設定忘れが原因。  
COSMOによるインストルメント前に、COSMO/templates/jacoco-instrumenter-coverage.gradleを、本プロジェクトのtemplate/jacoco-instrumenter-coverage.gradleで置換する。  
変更点は以下の3つ。
- xmlファイルを出力するために、reportsのxml.enabledをtrueにする。何故か干渉するので、csv.enabledの行を削除する。
- kotlinソースファイルを網羅率計算に含めるために、includesに"**/tmp/kotlin-classes/**"を加える。
- 網羅率の保存先を指定するために、`dir: "/coverage"`とする。