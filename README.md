# Interview Augusta Labs

## Requirements

`requirements.txt` was created using:

 ```shell
 pip list --format=freeze > requirements.txt
 ```
 and can be used to install the requirements to a pip enviroment using:
```shell
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
```

## Running

To run the app:
```shell
cd src
uvicorn fastapi_app:app --reload
```

## Requests

Some sample requests:

- List the last pt articles:
```shell
http://127.0.0.1:8000/wikipedia/list_last_pt_articles?total_limit=5
```

- Get the parsed last pt articles:
```shell
http://127.0.0.1:8000/wikipedia/get_last_pt_articles?total_limit=5&requests_per_second=2&processing_type=fast&verbose=true
```

- Get the results for a user query:
```shell
http://127.0.0.1:8000/user/query_results?query=Machine%20Learning&top_k=5&scrapping_total_limit=10
``` 

OR
```shell
http://127.0.0.1:8000/user/query_results?query=Hist%C3%B3ria&top_k=20&scrapping_total_limit=50
```

- Get refined search:
```shell
http://127.0.0.1:8000/user/query_refined?positive=Museo_Travesti_del_Per%C3%BA&negative=Estudos_transg%C3%AAnero&negative=One_of_Ours
```