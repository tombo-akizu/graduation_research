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

## Issue
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
環境: Mac
gradle実行時に、次のエラーメッセージとともにビルドが失敗する。
```
Error: ANDROID_HOME is not set and "android" command not in your PATH.
```
Android_HOME環境変数を設定する。  
Macなら、~/.zshrcに、次を追加する。
```
export ANDROID_HOME=~/Library/Android/sdk
export PATH=$PATH:$ANDROID_HOME/tools:$ANDROID_HOME/tools/bin:$ANDROID_HOME/platform-tools
```
Windowsなら、「環境変数を編集」アプリケーションから、ANDROID_HOME環境変数を設定する。  
[参考資料](https://developer.android.com/tools/variables?hl=ja)

# Lexica
README.mdに従って、次のコマンドでビルドする。COSMOを使用するために、デバッグビルドする。
```
./gradlew assembleDebug
```

## Issue
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

## COSMO issue
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
環境: Mac, Win
COSMO実行後、アプリケーションをビルドする際に、次のエラーとともにビルド失敗する。
```
* What went wrong:
Execution failed for task ':app:processDebugMainManifest'.
> Manifest merger failed : android:exported needs to be explicitly specified for element <receiver#com.serwylo.lexica.EndCoverageBroadcast>. Apps targeting Android 12 and higher are required to specify an explicit value for `android:exported` when the corresponding component has an intent filter defined. See https://developer.android.com/guide/topics/manifest/activity-element#exported for details.
```
`app/src/main/AndroidManifest.xml` (oldではない)の6行目を、以下のように書き換える。
```
<receiver android:name=".EndCoverageBroadcast">
```
から
```
<receiver android:name=".EndCoverageBroadcast" android:exported="true">
```
とする。