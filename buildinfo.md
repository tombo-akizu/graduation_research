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
## Issue
### 1. Package name
- AndroidManifestに、パッケージ名を加える
- AndroidManifestに、exported属性を加える
- Android Studioのターミナルで、READMEのコマンドを実行する
