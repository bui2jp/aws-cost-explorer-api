# aws-cost-explorer-api

lambda(python)で作成した AWS Cost Explorer API のサンプルです。

## env

```
$ python -VV
Python 3.13.1 (main, Jan  7 2025, 14:39:30) [GCC 9.4.0]
```

sam を利用

```
sam init \
  --name aws-cost-report \
  --package-type Image \
  --base-image amazon/python3.13-base \
  --app-template hello-world-lambda-image \
  --no-application-insights \
  --no-tracing
```

## local 実行
