# 概要
本プロジェクトは、多様なパスで対象メソッドを実行する、Androidアプリケーションの自動GUIテストツールを実装するものである。  
本ツールは、インストルメンタと自動GUIテスタの2つの機能を有する。
インストルメンタは、テスト対象アプリケーションに、テストされるのに必要な機能を埋め込むものである。
自動GUIテスタは、インストルメンタを適用したアプリケーションに対して、多様なパスで対象メソッドを実行するように、自動GUIテストを行う。

# セットアップ
## 前提
- Python
   - バージョン3.9で動作を確認。
   - `python --version` または`python3 --version` でバージョンが表示されること。
- Android Studio
   - ADB
      - `adb --version` でバージョンが表示されること。
   - Android Virtual Device
      - API 25で動作を確認。
   - ANDROID_HOME環境変数
      - `echo $ANDROID_HOME` でパスが表示されること。
      - 対象アプリケーションのビルドに必要。
- JDK
   - 対象アプリケーションのビルドに必要。

## セットアップ
1. 本プロジェクトをダウンロードする。
2. 本プロジェクトのルートに移動する。
3. Python仮想環境を作る。`python -m venv .venv` または`python3 -m venv .venv`。
4. 仮想環境に入る。  
   Win: `.venv/Scripts/activate`  
   Mac: `source .venv/bin/activate`
5. 自身の環境に適したPyTorchを、[PyTorchのHP](https://pytorch.org/get-started/locally/)のコマンドでインストールする。
6. 本ツールの依存ライブラリをインストールする。`pip install -r requirements.txt`

# 実行
## 簡易実行
インストルメント・ビルド済みのapkファイルを用いて、自動GUIテスタだけを実行できる。
1. `built_apps` から、テストしたいアプリケーションのpklファイルを、`instrument_data/instrument.pkl` として保存する。
2. 自動GUIテスタを実行する。
   ```
   python src/run.py gui_tester \
            --package <package_name> \
            --apk_path <path_to_apk_file_of_target_app> \
            --target_method_id <method_id> \
            --limit_hour <test_time(hour)>
   ```
   - package_nameは、"com.serwylo.lexica"などの、アプリケーション固有の名称.
   - limit_hourは、テストを行う時間。代わりに、limit_episodeとして、エピソード数を指定することもできる。
   - 現状、あるメソッドのmethod_idを知る方法は、`project/app/src` 以下のjavaファイルを直接読むしかない。メソッドの初めにcallReportメソッドの呼び出しが追加されており、その引数がそのメソッドのmethod_idである。
3. 出力を確認する。
   `result` 以下に保存される。詳細は「プロジェクト構成」の節を参照。

## インストルメンタ
1. 本プロジェクトのルートに移動する。
2. 仮想環境から出ていれば、入り直す。
3. 対象アプリケーションのプロジェクトを用意する。そのルートを`<path_to_root_of_target_app>` と記述する。
4. インストルメンタを実行する。
   ```
   python src/run.py instrument --project_root <path_to_root_of_target_app>
   ```

   `project` 以下に、対象アプリケーションのプロジェクトにインストルメントを行なったものが保存される。
5. 対象アプリケーションにネットワーク権限を付与する。
   `project/app/src/main/AndroidManifest.xml` を開き、`<manifest>` ブロック内に次の2行を記入する。
   ```
   <uses-permission android:name="android.permission.INTERNET" />
	<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
   ```

   *本来はこれもインストルメンタで行われるべきだが、実装していない。*
6. 対象アプリケーションをビルドする。
   `project` に移動し、次のコマンドを実行する。
   ```
   ./gradlew assembleDebug
   ```
   `project/app/build/outputs/apk/debug/app-debug.apk` として、対象アプリケーションが得られる。
   ビルドが上手くいかない場合、`buildinfo.md` を参照すると、助けになるかもしれない。

## 自動GUIテスタ
1. Android Studioを起動し、AVD (Android Virtual Device)を実行する。
2. AVDとのTCP通信用のポートを指定する。`adb forward tcp:8080 tcp:8080`
3. 自動GUIテスタを実行する。
   ```
   python src/run.py gui_tester \
            --package <package_name> \
            --apk_path <path_to_apk_file_of_target_app> \
            --target_method_id <method_id> \
            --limit_hour <test_time(hour)>
   ```
   - package_nameは、"com.serwylo.lexica"などの、アプリケーション固有の名称.
   - limit_hourは、テストを行う時間。代わりに、limit_episodeとして、エピソード数を指定することもできる。
   - 現状、あるメソッドのmethod_idを知る方法は、`project/app/src` 以下のjavaファイルを直接読むしかない。メソッドの初めにreportメソッドの呼び出しが追加されており、その引数がそのメソッドのmethod_idである。
4. 出力を確認する。
   `result` 以下に保存される。詳細は「プロジェクト構成」の節を参照。

# プロジェクト構成
- README.md: 本ファイル。
- buildinfo.md: 対象アプリケーションのビルドに関するトラブルシューティング。
- pyproject.toml: Pythonプロジェクトとしての設定ファイル。
- requirements.txt: 本プロジェクトの依存モジュールリスト。
- instrument_data
   - instrument.pkl: インストルメント時の情報を記録し、自動GUIテスタが読み込む。
- project: インストルメント済み対象アプリケーションのプロジェクトが置かれる。
- result:   自動GUIテストの出力が保管される。
   - crash_log: 検出されたクラッシュの記録。
   - explorer_loss.png, caller_loss.png: 誤差関数の値の遷移。
   - found_new_path.png: 新規パス発見数の、時間ごとのヒストグラム。
   - logcat.txt: AVDのログ。FATAL ERRORタグがついているログは、対象アプリケーションのクラッシュによるもの。
   - path.csv: 各ステップでの情報。
   - path.txt: パスの発見数。
   - Qtool.log: loggerのログ。
- template
   - CallReport.java:   インストルメントの際に、対象アプリケーションに組み込まれる。
- test:  本ツールのテストプログラム。
- src
   - run.py:   本ツールのエントリポイント。
   - instrument_data.py:   instrument.pklに保存するデータ構造。インストルメントのログの役割。
   - logger.py:   ログを出力する。
   - instrumenter:   インストルメンタを実装する。
      - run_instrumenter.py:  インストルメンタのエントリポイント。
      - add_file.py: 対象アプリケーションのプロジェクトに、template/CallReport.javaを加える。
      - instrument.py:  対象アプリケーションのメソッドの初めに、CallReport.reportの呼び出しを加える。
   - gui_tester:  自動GUIテスタを実装する。
      - run_gui_tester.py: 自動GUIテスタのエントリポイント。自動GUIテスタの全体的な流れがわかる。

      - agent.py: エージェントの親クラスを実装。ε-greedy法関連の実装のみが残っている。
      - multinet_agent.py: agent.pyのクラスの子クラス。DQNを用いて、行動を選択する。
      - models
         - explorer.py, caller.py:  2つのDQNのネットワーク構造を定義する。

      - experience.py: 状態・行動・実行されたメソッドの履歴やパスなど、テスト中に得られる情報を保存する。
      - multinet_experience.py: モデル交代条件を扱う。それぞれのモデルのReplayBufferを有する。
      - explorer_replay_buffer.py, caller_replay_buffer.py: それぞれのモデルのReplayBuffer。モデル訓練のための訓練データを保存・出力する。
      - path.py:  パスを管理するデータ構造。
      - state.py: 状態を管理するデータ構造。状態の通し番号の割り振りも行う。

      - env:   AVDとのやり取りを行う。
         - env.py: アプリケーションのインストール・アンインストールや、起動など。他所からのenvへのアクセスは、env.pyが受け付ける。
         - observer.py: AVDの画面の状況を、本ツールが扱えるように処理する。
         - executor.py: 本ツールが決定した行動を、AVDに渡す。
      - component.py:   AVDの画面上のGUI要素を扱うデータ構造。通し番号の割り振りも行う。

      - tcp_client.py:  AVDとTCP通信を行い、実行されたメソッドを取得する。
      - progress_manager.py:  テスト時間が指定された値に対してどれだけ経過したかを管理・表示する。
      - config.py:   定数置き場と化している。

      - report.py:   出力に必要な情報を保持し、出力を生成する。
      - log_reader.py:  logcatが出力する、 AVD上のログを処理する。

# ブランチ
graduation_research_experimentブランチは、卒論執筆時点の本プロジェクトのバックアップである。  
網羅率取得機能が半端に実装されており、提案手法には採用されなかったオプションが選択できる。  
buildinfo.mdには、網羅率取得ツールCOSMO向けにビルドする方法が含まれる。  
いずれも提案手法には含まれないものであるため、mainブランチからは削除されている。
