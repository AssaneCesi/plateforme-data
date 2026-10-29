from datetime import datetime

from airflow.decorators import dag, task


@dag(
    dag_id="plateforme_donnees",
    schedule=None,
    start_date=datetime(2026, 11, 1),
    catchup=False,
)
def plateforme_donnees():

    @task
    def bonjour():
        print("Airflow fonctionne")

    @task
    def verifier_import():
        import plateforme
        print("Package trouvé :", plateforme.__file__)

    bonjour() >> verifier_import()


plateforme_donnees()
