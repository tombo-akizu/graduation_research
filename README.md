# Setup
1. Setup COSMO.
   1. Clone [COSMO](https://github.com/H2SO4T/COSMO) in some directory with `git clone https://github.com/H2SO4T/COSMO.git`.
   2. Prepare a version of Python supported by COSMO. 3.8 has been confirmed.
   3. Prepare a target-app project in some directory.
   4. Modify COSMO's gradle setting with `cp <root_of_this_project>/template/jacoco-instrumenter-coverage.gradle <root_of_COSMO>/templates/jacoco-instrumenter-coverage.gradle`.
   5. Add "exported" attribute in instrumented "receiver" node of AndroidManifest.xml.
      1. Open `<root_of_COSMO>/source_instrumenter.py`
      2. Insert following line next to the 23'rd line. `receiver.set(ANDROID_NS + 'exported', 'true')`
   6. Setup COSMO venv.  
      win
      ```
      cd <root_of_COSMO>
      python -m venv .venv
      .venv/scripts/activate
      pip install -r requirements.txt
      ```
      mac  
      ```
      cd <root_of_COSMO>
      python3 -m venv .venv
      source .venv/bin/activate
      pip install -r requirements.txt
      ```
2. Instrument with COSMO.
   ```
   python cli.py <absolute_path_to_root_of_target_app>
   ```
3. Setup this tool.
   1. Create venv of this project and activate it.
   2. Install PyTorch for your environment from the [HP of PyTorch](https://pytorch.org/get-started/locally/).  
   3. `pip install -r requirements.txt` (Getting Ready).
4. Instrument with this tool.
   ```
   python src/run.py instrument --project_root <path_to_root_of_target_app>
   ```
5. Completed
   You can get instrumented apk file as `project/app/build/outputs/apk/debug/app-debug.apk`.

# Execution
1. Activate AVD (Android Virtual Device) using Android Studio.
2. `adb forward tcp:8080 tcp:8080`
3. `python src/run.py gui_tester --package <package_name> --apk_path <path_to_apk_file> --limit_hour <limit_hour> --target_method_id <target_method_id> --model <model_name>`
   - package_name: Such as "com.serwylo.lexica".
   - You can order limit_episode instead of limit_hour
   - You can know method_id by reading instrumented source code under `project/app/src`. It is given as argument of "callreport" method.
   - You can choose model_name from "4LP", "4LPWithPath", and "LSTM".

## Issues
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


何度も`empty batch`が表示される  
アプリケーションから、実行されたメソッドを受け取れていない。  
アプリケーションにネットワーク権限がないかもしれない。
AndroidManifest.xmlのmanifestの子ノードとして、以下を追加する。  
`<uses-permission android:name="android.permission.INTERNET" />`

エラーメッセージをわかりやすく
- AVDと繋がらない
- adb forward tcp:8080 tcp:8080
- アプリが元々インストールされている
- ソケット通信できない

インストルメントの権限拡大
- manifestのpackage属性
- receiverのexported属性
- uses-permission  
一旦保留して、他のアプリケーションの状態をみて決定する

method_idは環境によって変動するので注意
