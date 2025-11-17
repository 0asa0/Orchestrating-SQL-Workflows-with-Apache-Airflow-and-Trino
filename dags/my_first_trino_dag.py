import pendulum

from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from trino_operator import TrinoOperator

def print_command(**kwargs):
    task_instance = kwargs['task_instance']
    # Pull all rows returned by task3
    result = task_instance.xcom_pull(task_ids='task_3', key='return_value')
    if result:
        for row in result:
            print(row)
    else:
        print("No results found.")

with DAG(
    default_args={
        'depends_on_past': False
    },
    dag_id='akif_trino_scheduled_job',
    schedule_interval='*/2 * * * *',
    start_date=pendulum.datetime(2024, 11, 8, tz="Europe/Istanbul"),
    catchup=False,
    tags=['asa'],
) as dag:

    task1 = TrinoOperator(
        task_id='task_1',
        trino_conn_id='asa123456',
        sql="select count(*) from tpch.tiny.customer"
    )

    task2 = PythonOperator(
        task_id='print_command',
        python_callable=print_command,
        op_kwargs={'task_id': 'task_1'},  
        provide_context=True,
    )

    task3 = TrinoOperator(
        task_id='task_3',
        trino_conn_id='asa123456',
        sql="select * from tpch.tiny.nation"
    )

    task4 = PythonOperator(
        task_id='print_command2',
        python_callable=print_command,
        op_kwargs={'task_id': 'task_3'},  
        provide_context=True,
    )

    task5 = TrinoOperator(
      task_id='task_5',
      trino_conn_id='asa123456',
      sql="select * from tpch.tiny.customer"
      )

    task6 = TrinoOperator(
      task_id='task_6',
      trino_conn_id='asa123456',
      sql="set time zone 'America/Chicago'; select now(); set time zone 'UTC' ; select now()"
      )

    task1 >> task2 >> task3 >> task4 >> [task5, task6]
    
