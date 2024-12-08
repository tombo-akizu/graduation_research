# Objective
テスト対象アプリケーションの、ビルドに必要な情報を提供する。  

# General
## Gradle
gradleは、java系のビルドツールである。  
Groovy言語のスクリプトでタスクを定義しておき、タスクを実行することでビルドを行う。   
インストールしてパスを通しておけば、`gradle <task_name>`のようにしてビルドできる。   

gradlewは、gradle wrapperといい、gradleのインターフェイスである。  
実行ファイルとして、mac/linux用に`gradlew`が、win用に`gradlew.bat`が配布されている。  
`./gradlew <task_name>`として実行できる。  
`gradle/wrapper/gradle-wrapper.properties`で、使用するgradleのバージョンが指定されている。  
実行すると、コンピュータ上に使用するバージョンのgradleがない場合、自動的にそれがインストールされ、その後にタスクが実行される。  
私は、プロジェクト開発者が動作確認したバージョンのgradleでビルドができるため、gradlewを用いてビルドする方がよいと考えている。  

オープンソースAndroidプロジェクトには、gradlew及びgradleビルドスクリプトが含まれている場合がある。  

## General issue
### 1. ESET
環境: Mac  
gradle実行時に、次のエラーメッセージとともにビルドが失敗することがある。
```
* What went wrong:
Could not dispatch a message to the daemon.
```
セキュリティソフトESETが原因であり、  
システム設定 > 一般 > ログイン項目と機能拡張 > ネットワーク機能拡張 > ESET Network Access Protection  
をオフにすると成功する。  
ESETは、研究室貸与PCに最初にインストールするよう指示される。  
ビルド後は元に戻すこと。  
[参考資料](https://forum.eset.com/topic/41990-eset-block-gradle-after-latest-update/)  

### 2. No Android env
環境: Mac, Win  
gradle実行時に、次のエラーメッセージとともにビルドが失敗する。(Mac)
```
Error: ANDROID_HOME is not set and "android" command not in your PATH.
```
Winでは、次のエラーメッセージを確認した。  
```
* What went wrong:
Could not determine the dependencies of task ':app:compileDebugJavaWithJavac'.
> SDK location not found. Define a valid SDK location with an ANDROID_HOME environment variable or by setting the sdk.dir path in your project's local properties file at 'lexica_root\local.properties'.
```
ANDROID_HOME環境変数を設定する。  
Macなら、~/.zshrcに、次を追加する。
```
export ANDROID_HOME=~/Library/Android/sdk
export PATH=$PATH:$ANDROID_HOME/tools:$ANDROID_HOME/tools/bin:$ANDROID_HOME/platform-tools
```
Windowsなら、「環境変数を編集」アプリケーションから、ANDROID_HOME環境変数作成し、Android SDKのパスを代入する。  
私の環境では、`~/AppData/Local/Android/Sdk`だった。  
[参考資料](https://developer.android.com/tools/variables?hl=ja)

環境変数設定後は、シェルを再起動することを勧める。  

### 3. Last Resort
何らかのビルド問題がどうしても解決しない場合、`~/.gradle/caches`の中身を全て削除してから再ビルドすると、上手くいくことがある。  
私も数回、これで問題が解決したことがある。試してみてほしい。

# Lexica
README.mdに従って、次のコマンドでビルドする。COSMOを使用するために、デバッグビルドする。
```
./gradlew assembleDebug
```

## Issue of Lexica
### 1. InvocationTargetException
環境: Mac  
gradle実行時に、次のエラーメッセージとともにビルド失敗する。
```
* What went wrong:
Execution failed for task ':app:kaptDebugKotlin'.
> A failure occurred while executing org.jetbrains.kotlin.gradle.internal.KaptWithoutKotlincTask$KaptExecutionWorkAction
   > java.lang.reflect.InvocationTargetException (no error message)
```
app/build.gradleの、88, 89行目を、以下のように変更するとビルドできる。  
```
implementation 'androidx.room:room-runtime:2.2.6'
kapt 'androidx.room:room-compiler:2.2.6'
```
から、
```
implementation 'androidx.room:room-runtime:2.2.4'
kapt 'androidx.room:room-compiler:2.2.4'
```
に修正する。  
[参考資料](https://stackoverflow.com/questions/63649694/a-failure-occurred-while-executing-org-jetbrains-kotlin-gradle-internal-kaptexec)

## COSMO issue of Lexica
### 1. COSMO package error
環境: Mac, Win  
cli.py実行時に、次のエラーが発生する。
```
KeyError: 'package'
```
app/main/AndroidManifest.xml (COSMO実行後はAndroidManifest.xml.old)の2行目を、以下のように変更する。
```
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
```
から、
```
<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="com.serwylo.lexica">
```

### 2. Exported attribute
**本Issueを回避する操作を、README.mdのSetupに追加した。**  
環境: Mac, Win  
COSMO実行後、アプリケーションをビルドする際に、次のエラーとともにビルド失敗する。
```
* What went wrong:
Execution failed for task ':app:processDebugMainManifest'.
> Manifest merger failed : android:exported needs to be explicitly specified for element <receiver#com.serwylo.lexica.EndCoverageBroadcast>. Apps targeting Android 12 and higher are required to specify an explicit value for `android:exported` when the corresponding component has an intent filter defined. See https://developer.android.com/guide/topics/manifest/activity-element#exported for details.
```
エラーメッセージに従って、`app/src/main/AndroidManifest.xml` (oldではない)の6行目を、以下のように書き換える。
```
<receiver android:name=".EndCoverageBroadcast">
```
から
```
<receiver android:name=".EndCoverageBroadcast" android:exported="true">
```
とする。