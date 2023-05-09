# Migrate from Cloud SQL to AlloyDB using DMS

This migration guideprovides instructions for migrating from the Cloud SQL databases (`accountsdb` + `ledgerdb`) to AlloyDB for PostgreSQL using the [Database Migration Service](https://cloud.google.com/database-migration). This guide closely follows the database [migration guide](https://cloud.google.com/database-migration/docs/postgresql-to-alloydb/configure-source-database#cloud-sql-postgresql).

## Prerequisites
Before proceeding with the migration, ensure that you have completed the set up for the Bank of Anthos on Cloud SQL project and have the required Kubernetes cluster, service accounts, Cloud SQL databases and backend deployments set up. If you have not, please click on the link to set up [Bank of Anthos on Cloud SQL](https://github.com/GoogleCloudPlatform/bank-of-anthos/tree/main/extras/cloudsql).

## How it works

The setup scripts provided in this guide will provision an AlloyDB instance in your Google Cloud Project and create two databases - one for the **accounts DB**, one for the **ledger DB**. These databases will replace the default Cloud SQL instance used in Bank of Anthos.

## Setup
Perform the following steps to set up AlloyDB and migrate from Cloud SQL to AlloyDB:

1. Open your Google Cloud project that contains your **Bank of Anthos on Cloud SQL** application.

2. **Set environment variables** that correspond to your project. Note that these variables are set to be the same as those used in the Bank of Anthos on Cloud SQL guide. Replace "my-project" with your Project id.
    ```
    export PROJECT_ID="my-project"

    export DB_REGION="us-east1"
    export ZONE="us-east1-b"
    export CLUSTER="my-cluster-name"
    export NAMESPACE="default"
    export GSA_NAME="boa-gsa"
    export INSTANCE_NAME='bank-of-anthos-db'

    export ALLOYDB_CLUSTER="alloydb-cluster"
    export ALLOYDB_INSTANCE="alloydb-instance"
    export ALLOYDB_REGION="us-east4"
    export VM_NAME="alloydb-client"
    ```

3. **Enable the Data Migration API and AlloyDB API**. 
Enable the Data Migration API and AlloyDB API by running the following commands:
    ```
    gcloud config set project $PROJECT_ID
    gcloud services enable datamigration.googleapis.com
    gcloud services enable alloydb.googleapis.com
    ```

4. **Grant your service account access to AlloyDB**. The Google Service Account (GSA) and Kubernetes Service Account (KSA) that were associated together in the Cloud SQL guide. Hence, we will use the same service accounts to grant access to AlloyDB.\
    Firstly, run the following command to get the credentials for your Kubernetes cluster:
    ```
    gcloud container clusters get-credentials $CLUSTER --zone $ZONE --project $PROJECT_ID
    ```
    Next, add a new IAM policy binding to your project, which grants the roles/alloydb.client role to your GSA, which is associated with your KSA. This effectively grants your cluster access to AlloyDB.
    ```
    gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member "serviceAccount:${GSA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role roles/alloydb.client
    ```

5. **Enable Private Services Access.** Since AlloyDB only allows private connections, you need enable Private IP for Cloud SQL to use Private Services Access. 
    1. Go to the [Cloud SQL console](https://console.cloud.google.com/sql/instances) and click into your instance.
    2. Click `Edit` on toolbar on top and scroll down to `Connections`.
    3. Enable `Private IP` under Instance IP assignment.
    4. Choose your network and click `Set Up Connection`.
    5. Click `Enable API` to enable Service Networking API.
    6. Create an IP range and click `Allocate a new IP range` and select `Use an automatically allocated IP range`.
    8. Click `Continue` and `Create Connection`. This will take a few minutes.


5. **Preparing the source database for migration.** Before migrating, you need to enable the pglogical flags and install the extension on each of your source databases, except for template0 and template1. You also need to grant privileges on the databases to the user that you will be using to connect to the source during the migration.
    1. Go to the [Cloud SQL console](https://console.cloud.google.com/sql/instances) and click into your instance.
    2. Click `Edit`, scroll down to `Flags` and add the following flags:
        * cloudsql.logical_decoding = On
        * cloudsql.enable_pglogical = On   
    4. Click `Save` then `Save and Restart`. Wait a few minutes for instance to update.
    5. Copy the instance's **Private IP address** and save it for Step 7.2.

6. **Configure your Cloud SQL databases**. After enabling the pglogical flags, you will need to install the extension on each of your source databases except for template0 and template1. You will also need to grant privileges on the databases to the user that you will be using to connect to the source during the migration. 
    1. Connect to your Cloud SQL instance from Cloud Shell.
        ```
        gcloud sql connect $INSTANCE_NAME --user=admin -d postgres
        ```
    2. In the psql terminal, run the following commands to grant privileges for user "admin" to each of your to-be-migrated databases (`accounts-db`, `ledger-db`, `postgres`).
        ```
        ALTER USER admin with REPLICATION;
        ```
        ```
        \c accounts-db;
        ```
        ```
        CREATE EXTENSION IF NOT EXISTS pglogical;
        GRANT USAGE on SCHEMA pglogical to PUBLIC;
        GRANT SELECT on ALL TABLES in SCHEMA pglogical to admin;
        GRANT USAGE ON SCHEMA public TO admin;
        GRANT ALL ON SCHEMA public TO admin;
        ```
        ```
        \c ledger-db;
        ```
        ```
        CREATE EXTENSION IF NOT EXISTS pglogical;
        GRANT USAGE on SCHEMA pglogical to PUBLIC;
        GRANT SELECT on ALL TABLES in SCHEMA pglogical to admin;
        GRANT USAGE ON SCHEMA public TO admin;
        GRANT ALL ON SCHEMA public TO admin;
        ```
        ```
        \c postgres;
        ```
        ```
        CREATE EXTENSION IF NOT EXISTS pglogical;
        GRANT SELECT on ALL TABLES in SCHEMA pglogical to admin;
        ```
        ```
        \q
        ```

7. **Create DMS Migration Job**. Go to the [Database Migration console](https://console.cloud.google.com/dbmigration/migrations) and **Create a migration job**.
    1. **Get started**
        * Set a name for your migration job
        * Source database engine = `Cloud SQL for PostgreSQL`
        * Destination database engine = `AlloyDB for PostgreSQL`
        * Destination region = `us-east4`
        * `Save and Continue`
    2. **Define your source** 
        * `Create a Connection Profile`
            1. Set Connection Profile name
            1. Cloud SQL instance = Select `bank-of-anthos-db` instance
            2. Hostname or IP address = `<Cloud_SQL_Private_IP_from_Step_5.5>`
            3. Port = `5432`
            4. Username = `admin`
            5. Password = `admin`
        * Encryption type = `None`
        * Connectivity method = `Not defined`
        * `Create`
        * `Save and Continue`
    3. **Create a destination**
        * Cluster ID = `alloydb-cluster`
        * Password = `admin`
        * Network = `default` or select your network
        * Instance ID = `alloydb-instance`
        * Machine = `2 vCPU, 16 GB`
        * `Save and Continue`
        * `Create Destination and Continue` and wait for AlloyDB cluster to be created.
    4. **Define connectivity method**
        * `Configure and continue`
    5. **Test and create migration job**
        * Review your migration details.
        * `Test Job`
        * `Create and Start Job`

8. **Review Migration Job**. 
    1. **Status** should be "Running CDC in progress".
    2. View migration job details. 
    3. **Replication Delay** should be zero at the time of promotion in order to avoid data loss.
    4. **Storage usage** reflects how many GB are currently being used by the destination AlloyDB for PostgreSQL isntance. This gives an indication of the migration process.

9. **Verify Migration Job**. 
    1. Go to the **[AlloyDB Console](https://console.cloud.google.com/alloydb/clusters)**.
    2. Copy the **Private IP Address** of your Primary Instance.
    3. In Cloud Shell, create a compute VM to act as an AlloyDB client.
        ```
        gcloud compute instances create $VM_NAME \
        --zone=$ZONE \
        --metadata=startup-script='#! /bin/bash
            apt-get update
            apt-get install -y postgresql-client'
        ```
    4. SSH into the instance.
        ```
        gcloud compute ssh $VM_NAME --zone=${ZONE}
        ```
    5. SSH into the instance with password "admin".
        ```
        psql -h <ALLOYDB_IP> -U postgres -d accounts-db
        ```
    6. Verify that all tables and data were migrated to AlloyDB. 
        List all databases - you should see `accounts-db`, `ledger-db`, `postgres`.
        ```
        \l
        ```
        Connect to the `accounts-db` and make sure the tables `contacts` and `users` exist.
        ```
        \c accounts-db
        \dt
        ```
        Check if the test data was inserted into the tables by running a SELECT query  to obtain number of rows.
        ```
        SELECT 'public.contacts' as table_name, COUNT(*) as row_count 
        FROM public.contacts
        UNION ALL
        SELECT 'public.users' as table_name, COUNT(*) as row_count 
        FROM public.users;
        ```
        Grant permissions to postgres user to modify the `users` and `contacts` table.
        ```
        GRANT ALL PRIVILEGES ON TABLE public.contacts TO postgres;
        GRANT ALL PRIVILEGES ON TABLE public.users TO postgres;
        ```
        Connect to the `ledger-db` to check the transaction table.
        ```
        \c ledger-db
        \dt
        ```
        Check if the test data was inserted into the tables by running a SELECT query to obtain number of rows.
        ```
        SELECT COUNT(*) FROM  public.transactions;
        ```
        Grant permissions to postgres user to modify the `transactions` table.
        ```
        GRANT ALL PRIVILEGES ON TABLE public.transactions TO postgres;
        ```

11. **Create a AlloyDB secret** in your GKE cluster. This gives your in-cluster AlloyDB client a username and password to access AlloyDB. (Note that the postgres/admin credentials are for demo use only and should never be used in a production environment.)
    ```
    export ALLOYDB_CONNECTION_NAME=$(gcloud alloydb instances describe $ALLOYDB_INSTANCE --cluster=$ALLOYDB_CLUSTER --region=$ALLOYDB_REGION --format="value(name)")
    echo $ALLOYDB_CONNECTION_NAME

    kubectl create secret -n $NAMESPACE generic alloydb-admin \
    --from-literal=username=postgres --from-literal=password=admin \
    --from-literal=connectionName=$ALLOYDB_CONNECTION_NAME
    ```

12. **Change connection properties in each of your services**. Each backend Deployment (`userservice`, `contacts`, `transactionhistory`, `balancereader`, and `ledgerwriter`) is configured with a [AlloyDB Auth Proxy](https://cloud.google.com/alloydb/docs/auth-proxy/overview) sidecar container. AlloyDB Auth Proxy provides a secure TLS connection between the backend GKE pods and your AlloyDB instance.

    This command will update the existing deployments to use the AlloyDB Auth Proxy and Connection URL instead of connecting to the Cloud SQL instance.
    ```
    kubectl apply -n $NAMESPACE -f ./kubernetes-manifests
    ```

13. Wait a few minutes for all the pods to be `RUNNING`. (Except for the two `populate-` Jobs. They should be marked `0/3 - Completed` when they finish successfully.)

    ```
    NAME                                  READY   STATUS      RESTARTS   AGE
    balancereader-d48c8d84c-j7ph7         2/2     Running     0          2m56s
    contacts-bbfdbb97f-vzxmv              2/2     Running     0          2m55s
    frontend-65c78dd78c-tsq26             1/1     Running     0          2m55s
    ledgerwriter-774b7bf7b9-jpz7l         2/2     Running     0          2m54s
    loadgenerator-f489d8858-q2n46         1/1     Running     0          2m54s
    populate-accounts-db-wrh4m            0/3     Completed   0          2m54s
    populate-ledger-db-422cr              0/3     Completed   0          2m53s
    transactionhistory-747476548c-j2zqx   2/2     Running     0          2m53s
    userservice-7f6df69544-nskdf          2/2     Running     0          2m53s
    ```

12. Access the Bank of Anthos frontend at the frontend service `EXTERNAL_IP`, then log in as `test-user` with the pre-populated credentials added to the AlloyDB-based `accounts-db`. You should see the pre-populated transaction data show up, from the AlloyDB-based `ledger-db`. You're done!

10. **Promote the Migration**. Go to the [Migration jobs console](https://console.cloud.google.com/dbmigration/migrations) and view your migration job details. The loss-less promotion process involves the following steps:
    1. Make sure to **stop all writes, running scripts and client connections** to the source database.
    2. Wait for **Replication Delay** to drop down near to zero.
    3. Once ready, go into your the Migration job details and click **PROMOTE**.
    4. Wait for the status to change from **"Promote in progress" to "Completed"**.
    5. The application is now connected to the AlloyDB for PostgreSQL instance.
    6. Your migration job and Cloud SQL instance can now be safely deleted.

**Congratulations!** You have successfully migrated your bank-of-anthos application from Cloud SQL to AlloyDB for PostgreSQL.
