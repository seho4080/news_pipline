import pendulum
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.operators.python import PythonOperator
from airflow.operators.email import EmailOperator
from scripts import move_daily_data, daily_psql_to_json
local_tz = pendulum.timezone("Asia/Seoul")

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    dag_id='spark_daily_report_dag',
    default_args=default_args,
    description='매일 새벽 1시에 Spark를 이용해 뉴스 리포트 생성',
    schedule_interval='0 1 * * *',
    start_date=datetime(2025, 5, 1, tzinfo=local_tz),
    catchup=False,
    tags=['daily', 'report', 'spark']
) as dag:
    # 하루 치 모아 놓은 데이터 전처리 -> PDF 만들기
    submit_spark_job = SparkSubmitOperator(
        task_id='spark_daily_report',
        application='/opt/airflow/dags/scripts/spark_daily_report.py',
        conn_id='spark-default',
        application_args=['--date', '{{ ds }}'],
        conf={
            "spark.master": "spark://spark-master:7077",
            "spark.hadoop.mapreduce.fileoutputcommitter.algorithm.version": "2",
            "spark.driver.extraJavaOptions": "-Duser.dir=/opt/bitnami/spark"
        },
        verbose=True,
    )
    # 하루치 사용한 JSON 파일 이동
    move_daily = PythonOperator(
        task_id = 'move_daily_data_task',
        python_callable = move_daily_data.move_file,
    )

    # 완료 알림
    notify_report_generated = BashOperator(
        task_id='notify_report_generated',
        bash_command='echo "리포트가 생성되었습니다: {{ ds }} 날짜의 이메일 보내기 "'
        
    )
    # 완성된 파일 이메일로 보내기 
    send_pdf_to_email =EmailOperator(
        task_id='send_email_task',  # 작업의 고유 ID
        to='tkrhktlqdjr1@gmail.com',  # 이메일 수신자 지정
        subject='airflow-test',  # 이메일 제목
        html_content='test_success',  # 이메일 본문 내용
        files=['/opt/airflow/reports/{{ ds }}_report.pdf']  # 예시 경로
    )

    submit_spark_job >> move_daily >> notify_report_generated >> send_pdf_to_email
