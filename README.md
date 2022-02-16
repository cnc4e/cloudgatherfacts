# CloudGatherFacts

## CloudGatherFacts とは
クラウド上のリソース情報を収集してJSONファイルに出力するツールです。  
また、収集したAWS構成データをデータベースに蓄積し、分析ツールから検索、分析できます。

### 対応するクラウド
現時点で AWS のみに対応しています。  

### 対応するリソース
CloudGatherFactsでは2通りの方法でAWSリソース情報を収集することができます。
1. AWSサービスのAPIでリソース情報を直接取得する
2. AWS Configサービスの「高度なクエリ」機能を実行する

それぞれ以下のリソース情報を収集できます。

### AWSサービスのAPIで直接取得可能
- VPC
- EC2
- EBS
- S3
- ELB
- IAM
- KMS
- SNS
- CloudTrail
- CloudWatch​​​​​​
- Route53
- EFS
- Lambda
- Backup
- DirectConnectGateway
- CloudWatch Logs
- RDS

### AWS Configの「高度なクエリ」機能で取得可能
AWS Configが対応するリソースに対応します。  
詳細は[​​​​​​​サポートされているリソースタイプ​​​​​​​](https://docs.aws.amazon.com/ja_jp/config/latest/developerguide/resource-config-reference.html)を参照してください。

## 動作環境
### OSに導入するもの
* Python 3.9 以上
### Pythonに導入するパッケージ
| パッケージ | バージョン |
| ------ | ---------  |
| PyYAML | 5.4.1 以上 |
| boto3  | 1.17.104 以上 |
| SQLAlchemy | 1.4.20 以上 |
| deepdiff | 5.5.0 以上 |

## 事前準備、設定
### AWSの情報収集に必要な権限
CloudGatherFactsを実行する際のAWSユーザには下記のIAMポリシーのアタッチが必要です。

#### 収集対象リソース毎に必要なIAMポリシー一覧
| サービス名 | type:で設定するリソース名 | ポリシー名               | 備考                         |
|-----------|-------------------------|-------------------------|--------------------------------|
| 共通       | -	                   | AmazonEC2ReadOnlyAccess | 実行時に必要                    |
| Backup     | Backups                 | AWSBackupFullAccess     | ReadOnlyポリシーなし         |
| CloudTrail | Trails                  | AWSCloudTrailReadOnlyAccess |                         |
| CloudWatch | MetricAlarms            | AmazonEC2ReadOnlyAccess |                             |
| CloudWatch | EventRules              | AmazonEventBridgeReadOnlyAccess |                     |
| CloudWatch | LogGroups               | CloudWatchLogsReadOnlyAccess    |                     |
| CloudWatch | MetricFilters           | CloudWatchLogsReadOnlyAccess    |                     |
| DirectConnectGateway | DirectConnectGateways | AWSDirectConnectReadOnlyAccess<br>AmazonEC2ReadOnlyAccess |              |
| EC2        | VPCs                    | AmazonEC2ReadOnlyAccess         |                     |
| EC2        | Subnets                 | AmazonEC2ReadOnlyAccess         |                     |
| EC2        | Reservations            | AmazonEC2ReadOnlyAccess<br>IAMReadOnlyAccess |                     |
| EC2        | SecurityGroups          | AmazonEC2ReadOnlyAccess         |                     |
| EC2        | Volumes                 | AmazonEC2ReadOnlyAccess         |                     |
| EC2        | NetworkInterfaces       | AmazonEC2ReadOnlyAccess         |                     |
| EC2        | RouteTables             | AmazonEC2ReadOnlyAccess         |                     |
| EC2        | NetworkAcls             | AmazonEC2ReadOnlyAccess         |                     |
| EC2        | InternetGateways        | AmazonEC2ReadOnlyAccess         |                     |
| EC2        | Addresses               | AmazonEC2ReadOnlyAccess         |                     |
| EC2        | NatGateways             | AmazonEC2ReadOnlyAccess         |                     |
| EC2        | DhcpOptions             | AmazonEC2ReadOnlyAccess         |                     |
| EFS        | FileSystems             | AmazonElasticFileSystemReadOnlyAccess |               |
| ELB        | LoadBalancers           | AmazonEC2ReadOnlyAccess         |                     |
| ELB        | TargetGroups            | AmazonEC2ReadOnlyAccess         |                     |
| IAM        | Users                   | IAMReadOnlyAccess               |                     |
| IAM        | Groups                  | IAMReadOnlyAccess               |                     |
| IAM        | Roles                   | IAMReadOnlyAccess               |                     |
| IAM        | Policies                | IAMReadOnlyAccess               |                     |
| KMS        | Keys                    | AWSKeyManagementServicePowerUser |                    |
| Lambda     | Functions               | AWSLambda_ReadOnlyAccess<br>AmazonEC2ReadOnlyAccess |                     |
| RDS        | DBInstances             | AmazonRDSReadOnlyAccess         |                     |
| RDS        | DBProxies               | AmazonRDSReadOnlyAccess<br>AmazonEC2ReadOnlyAccess |                     |
| RDS        | EventSubscriptions      | AmazonRDSReadOnlyAccess         |                     |
| Route53    | HostedZones             | AmazonRoute53ReadOnlyAccess     |                     |
| S3         | Buckets                 | AmazonS3ReadOnlyAccess          |                     |
| SNS        | Topics                  | AmazonSNSReadOnlyAccess         |                     |

#### AWSConfigクエリを使用する際に必要なIAMポリシー
| ポリシー名           | 説明                                                      |
|---------------------|----------------------------------------------------------|
| AWSConfigUserAccess | AWSConfig のクエリ実行権限<br>  ※AWSConfigクエリを使用する時のみ必要 |

### AWS認証情報の設定
以下の環境変数を追加します。  
AWS CLIのプロファイルに設定した認証情報を使用する場合は設定不要です。

| 環境変数名 | 設定内容 |
| ---- | --- |
| AWS_ACCESS_KEY_ID | AWSのアクセスキーID |
| AWS_SECRET_ACCESS_KEY | AWSのシークレットキー |
| AWS_DEFAULT_REGION | デフォルト利用するAWSのリージョン名（ap-northeast-1等）|
| AWS_SESSION_TOKEN | MFA認証を使用する際のセッショントークン（任意）|
| AWS_PROFILE | プロファイル名（AWS CLIの設定を流用することも可能）|

### 設定ファイルの編集
#### AWSConfig.yml
- CloudGatherFactsで取得対象とするAWSサービスは設定ファイル(AWSConfig.yml)に定義します。
- 設定ファイルはYAML形式で記載し、UTF-8の文字コードで保存してください。
```yaml
cloudtype: AWS
outputdir: SampleData
outputfile: AWS.json
resources:
  - type: Vpcs
    parameters:
      Filters: 
        - Name: tag:Owner
          Values: 
            - hogehoge
awsconfig:
  - name: Apis
    query: >-
      SELECT
        resourceId, configuration
      WHERE 
        resourceType = 'AWS::ApiGateway::RestApi'
```

##### 全般
- cloudtype: AWSを指定（固定）
- outputdir: JSONファイルを保存するフォルダ名を相対パス/絶対パスで記載​​​​​​​
- outputfile: 保存するJSONファイル名を記載
- resources: AWSサービスのAPIで直接取得するリソースを定義
  - 配下にリスト形式で記載します。
  - リストの数は任意です。
  - 詳細は「resources:要素」を参照
- awsconfig: AWS Configでの情報収集に利用する「高度なクエリ」を定義
  - 配下にリスト形式で記載します。
  - リストの数は任意です。
  - 詳細は「awsconfig:要素」を参照。

##### resources:要素
リストの要素には以下を記載します。
- type: 取得するリソースの名前
- parameters: リソースを取得するAWS APIのパラメータ
    - 特定の条件で結果を絞り込むフィルタなどを渡せます。

##### awsconfig:要素
リストの要素には以下を記載します。
- **name:** 出力するJSONでクエリ（query:）の実行結果をマージする際の要素名。
  - 任意の名前を指定できます。ただし、resources:要素のtype名(Vpcs等)を含め、他の要素名と重複しないようにしてください。
- **query:** AWS Configで実行可能な「高度なクエリ」を記載

## CloudGatherFacts の実行方法
### 実行例
* pythonコマンドで実行します。
* 正常終了後、事前設定したパス(デフォルトData/AWS.json)に収集結果が出力されます。
```shell-session
> python CloudGatherFacts.py AWSConfig.yml
[INFO] 実行を開始します。
[INFO] リソースの情報を収集しています: Vpcs (ap-southeast-1)
[INFO] リソースの情報を収集しています: Subnets (ap-southeast-1)
[INFO] リソースの情報を収集しています: SecurityGroups (ap-southeast-1)
[INFO] リソースの情報を収集しています: Reservations (ap-southeast-1)
[INFO] リソースの情報を収集しています: Volumes (ap-southeast-1)
・・・
[INFO] リソースの情報を収集しています: EventSubscriptions (ap-southeast-1)
[INFO] リソースの情報を収集しています: Apis (ap-southeast-1)
[INFO] 実行を完了しました。
```
### 実行時の引数
* 設定ファイル(AWSConfig.yml)の指定が必要です。
* --regionオプションで対象リージョンを指定できます。未指定時は「AWS認証情報の設定」での設定が使われます。
* --eventオプションを付けると収集結果をSQLiteデータベースにも格納できます。
```shell-session
> python CloudGatherFacts.py --help
usage: CloudGatherFacts.py [-h] [-R REGION] [-E EVENT] [-D] [-V] config

CloudGatherFacts - クラウド上のリソース情報を収集するツール

positional arguments:
  config                設定ファイル名

optional arguments:
  -h, --help            show this help message and exit
  -R REGION, --region REGION
                        リージョン名
  -E EVENT, --event EVENT
                        DB登録イベントのコメント
  -D, --debug           デバッグログを出力
  -V, --version         show program's version number and exit
```

## 構成管理機能
### 構成管理機能とは
CloudGatherFactsで収集したAWS構成データをデータベース(SQLite)に蓄積する機能です。  
構成管理機能により以下の様なことが実現できます。

- 様々な分析ツールから過去のAWS構成情報を検索、分析する
- 過去の2時点間のAWS構成の差分情報を取得する

### AWS構成データをDBに蓄積する
CloudGatherFactsで収集したAWS構成データをDB(SQLite)に蓄積する手順を説明します。

#### AWS環境​​​の準備（任意）
構成管理対象とするリソースをAWS環境に構築しておきます。

#### CloudGatherFactsの実行
CloudGatherFactsを実行してAWSの構成情報を収集します。

実行結果の構成情報はDBに1つの「イベント」データとして登録されます。用途に応じたタイミング（構成変更時のみ実行、毎日定刻にスケジュール実行）で実行してください。

- サンプル設定ファイル「AWSConfig.yml」にDB(SQLite)の設定「database:」を追記します。
```yaml
database:
    url: sqlite:///Data/test.db　　※SQLiteデータベースの接続文字列。
                                    ここではDataフォルダ内にtest.dbというファイル名で作成する。
```
- 「-E」オプションを付けてCloudGatherFactsを実行します。  
  - 「-E」オプションを付与しないと DB へデータ登録は行われません。
  - 「-E」オプションには登録イベントを識別しやすくする任意のコメントを指定できます。
```shell-session {linenos=false}
> python CloudGatherFacts.py AWSconfig.yml -E 'DBに登録するイベントのコメント'
```
- 実行が完了したら、収集したデータがDB(SQLite)に登録されます。​​​​​​

## DBに登録されたデータを確認
CloudGatherFactsで登録したデータを[DB Browser for SQLite](https://sqlitebrowser.org/)を使って確認します。  

1. インストールした DB Brower for SQLite をPCのプログラムメニュー等から起動します。
1. 「データベースを開く」からデータベースファイル(例: Dataフォルダのtest.db)を選択して開きます。
1. DB Browser for SQLite からDB(SQLite)を直接操作することができます。
    - データベース構造タブ：Event, AwsFacts のテーブル構造が確認できます
    - データ閲覧タブ：Event, AwsFacts テーブルのデータを参照できます
    - SQL実行タブ：Event, AwsFacts テーブルへの SQL を実行できます

## 分析ツールで分析する
CloudGatherFactsで収集したAWS構成データは同梱された分析用ツールで分析できます。

### 分析用ツールの概要
CloudGatherFactsで収集した構成データの分析を補助する独自ツールです。  
CloudGatherFactsに同梱され、以下の機能を提供します。
- sqlコマンド: 指定したSQLをDBに対して実行した結果を取得する。
- getコマンド: DBから指定したイベントIDのデータを取得する。
- diffコマンド: 指定した2つのイベントIDのデータを比較する。

#### sqlコマンド：DBへSQLを実行する
- 指定したSQLをDBに対して実行し、実行結果を取得します。
- 実行するSQLは、オプションで直接指定することも、SQLファイルを読み込んで実行することも可能です。
- 実行結果のファイル形式は CSV と JSON を選択できます。

##### 実行方法
```shell-session {linenos=false}
usage: FactAnalyze.exe sql [-h] [-Q QUERY] [-F FILE] [-J] [-C CONFIG] [-D] outdir
​
positional arguments:
  outdir                OUT: 結果出力フォルダ
​
optional arguments:
  -h, --help            show this help message and exit
  -Q QUERY, --query QUERY
                        IN: 実行するSQLクエリの文字列
  -F FILE, --file FILE  IN: 実行するSQLクエリが書かれたファイル
  -J, --json            JSONファイルとして出力
  -C CONFIG, --config CONFIG
                        設定ファイル名
  -D, --debug           デバッグログを出力
```

#### getコマンド：DBから構成データを取得する
- DBから指定したイベントIDのデータを取得します。
- 複数のイベントIDを指定することが可能です。
- 取得した複数イベントのデータを1つのJSONに統合して出力することも可能です。

##### 実行方法
```shell-session {linenos=false}
usage: FactAnalyze.exe get [-h] [-Q QUERY] [-M] [-C CONFIG] [-D] event outdir
​
positional arguments:
  event                 IN: 取得データのイベントID(カンマ区切りで複数指定可能)
  outdir                OUT: 結果出力フォルダ
​
optional arguments:
  -h, --help            show this help message and exit
  -Q QUERY, --query QUERY
                        抽出するJSONクエリ(JMESPath)
  -M, --merge           取得データを1つのJSONに統合
  -C CONFIG, --config CONFIG
                        設定ファイル名
  -D, --debug           デバッグログを出力
```

#### diffコマンド：2時点の構成差分を取得する
DBから指定した2つのイベントIDのデータを取得し、比較した差分情報を出力します。

##### 実行方法
```shell-session {linenos=false}
usage: FactAnalyze.exe diff [-h] [-Q QUERY] [-C CONFIG] [-D] event1 event2 outdir
​
positional arguments:
  event1                IN: 比較データ1 イベントID
  event2                IN: 比較データ1 イベントID
  outdir                OUT: 結果出力フォルダ
​
optional arguments:
  -h, --help            show this help message and exit
  -Q QUERY, --query QUERY
                        抽出するJSONクエリ(JMESPath)
  -C CONFIG, --config CONFIG
                        設定ファイル名
  -D, --debug           デバッグログを出力
```

### 設定ファイル
- 分析用ツールの設定を **AnalyzeConfig.yml** に定義できます。
- **diff: deepdiff:** ブロックではdiffの挙動を細かくカスタマイズできます。
- 指定できる設定項目は内部で使用している **DeepDiff** ライブラリに依存します。  
[DeepDiffのマニュアルページ​](https://zepworks.com/deepdiff/current/diff.html#module-deepdiff.diff)​​​​を参考に設定してください。
```yaml
database:                           # 参照するSQLiteデータベースの接続文字列
    url: sqlite:///Data/test.db         # ここではDataフォルダ内のtest.dbを指定
diff:                               # diffコマンドに関する設定
    outputfile: deepdiff.json           # 差分情報を出力する際のファイル名(JSON形式)
    deepdiff:                           # diffの挙動をカスタマイズする設定
        ignore_order: true                  # 比較する際に要素の順番を無視する
        verbose_level: 1                    # 比較するレベル
        exclude_paths:                      # 比較する際に除外する要素
            - root['NetworkInterfaces']
            - root['NetworkAcls']
```